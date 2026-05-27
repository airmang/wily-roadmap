import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { Type } from "typebox";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { Text } from "@earendil-works/pi-tui";

const extensionDir = dirname(fileURLToPath(import.meta.url));
const pluginRoot = dirname(extensionDir);
const wilyScript = join(pluginRoot, "scripts", "wily.py");

const COMMANDS = [
	"agent",
	"block",
	"claim",
	"cp",
	"done",
	"go",
	"init",
	"land",
	"next",
	"replan",
	"status",
	"watch",
	"workspace",
] as const;

type WilyCommand = (typeof COMMANDS)[number];

type RunOptions = {
	cwd: string;
	command: WilyCommand;
	args?: string[];
	signal?: AbortSignal;
	timeout?: number;
};

const COMMAND_SET = new Set<string>(COMMANDS);
const DEFAULT_TIMEOUT_MS = 120_000;

function normalizeCommand(input: string): WilyCommand | undefined {
	const normalized = input.trim().replace(/^\$?wily[-\s]/, "");
	if (COMMAND_SET.has(normalized)) return normalized as WilyCommand;
	return undefined;
}

function defaultArgs(command: WilyCommand, args: string[]): string[] {
	if (args.length > 0) return args;
	if (command === "watch") return ["--once"];
	if (command === "workspace") return ["status"];
	if (command === "agent") return ["check"];
	return args;
}

function parseArgs(input: string): string[] {
	const args: string[] = [];
	let current = "";
	let quote: '"' | "'" | undefined;
	let escaped = false;

	for (const ch of input) {
		if (escaped) {
			current += ch;
			escaped = false;
			continue;
		}
		if (ch === "\\") {
			escaped = true;
			continue;
		}
		if (quote) {
			if (ch === quote) quote = undefined;
			else current += ch;
			continue;
		}
		if (ch === '"' || ch === "'") {
			quote = ch;
			continue;
		}
		if (/\s/.test(ch)) {
			if (current.length > 0) {
				args.push(current);
				current = "";
			}
			continue;
		}
		current += ch;
	}

	if (escaped) current += "\\";
	if (current.length > 0) args.push(current);
	return args;
}

function formatInvocation(command: WilyCommand, args: string[]): string {
	return ["wily", command, ...args].join(" ");
}

function truncateOutput(output: string, maxChars = 48_000): string {
	if (output.length <= maxChars) return output;
	return `${output.slice(0, maxChars)}\n\n[Output truncated by wily-roadmap pi extension: ${output.length - maxChars} characters omitted.]`;
}

function hasWilyProject(cwd: string): boolean {
	return existsSync(join(cwd, ".wily", "tasks.yaml")) || existsSync(join(cwd, ".wily", "coordination.yaml"));
}

function requiresApprovalForTool(command: WilyCommand, args: string[]): boolean {
	if (["claim", "block", "cp", "done", "init", "land", "replan"].includes(command)) return true;
	if (command === "workspace") {
		const action = args[0] ?? "status";
		return !["status", "next", "watch", "show-config"].includes(action);
	}
	if (command === "agent") {
		const action = args[0] ?? "check";
		return !["check", "status"].includes(action);
	}
	return false;
}

async function runWily(pi: ExtensionAPI, options: RunOptions) {
	const args = defaultArgs(options.command, options.args ?? []);
	const result = await pi.exec("python3", [wilyScript, options.command, ...args], {
		cwd: options.cwd,
		signal: options.signal,
		timeout: options.timeout ?? DEFAULT_TIMEOUT_MS,
	});

	const output = truncateOutput([result.stdout, result.stderr].filter(Boolean).join("\n"));
	return {
		...result,
		args,
		invocation: formatInvocation(options.command, args),
		output: output || `(no output; exit code ${result.code})`,
	};
}

function renderWilyMessage(message: { content?: unknown; details?: any }, _options: unknown, theme: any) {
	const code = message.details?.code;
	const titleColor = code === 0 ? "success" : code === undefined ? "accent" : "warning";
	const title = theme.fg(titleColor, theme.bold("Wily Roadmap"));
	const invocation = message.details?.invocation ? ` ${theme.fg("muted", message.details.invocation)}` : "";
	return new Text(`${title}${invocation}\n${String(message.content ?? "")}`, 0, 0);
}

async function displayRun(pi: ExtensionAPI, ctx: ExtensionContext, command: WilyCommand, rawArgs: string[]) {
	const result = await runWily(pi, {
		cwd: ctx.cwd,
		command,
		args: rawArgs,
		signal: ctx.signal,
	});

	if (!ctx.hasUI) {
		console.log(result.output);
	}

	pi.sendMessage({
		customType: "wily-roadmap",
		content: result.output,
		display: true,
		details: {
			code: result.code,
			invocation: result.invocation,
			cwd: ctx.cwd,
		},
	});
}

export default function wilyRoadmapExtension(pi: ExtensionAPI) {
	pi.registerMessageRenderer("wily-roadmap", renderWilyMessage);

	pi.on("session_start", (_event, ctx) => {
		ctx.ui.setStatus("wily-roadmap", hasWilyProject(ctx.cwd) ? "wily" : undefined);
	});

	pi.on("input", async (event, ctx) => {
		if (event.source === "extension") return { action: "continue" as const };
		const match = event.text.trim().match(/^\$(wily[-\w]*)(?:\s+(.*))?$/);
		if (!match) return { action: "continue" as const };

		const command = normalizeCommand(match[1] ?? "");
		if (!command) return { action: "continue" as const };

		await displayRun(pi, ctx, command, parseArgs(match[2] ?? ""));
		return { action: "handled" as const };
	});

	pi.registerCommand("wily", {
		description: "Run a Wily Roadmap command in this project",
		getArgumentCompletions: (prefix) => {
			const first = prefix.trimStart().split(/\s+/)[0] ?? "";
			const filtered = COMMANDS.filter((command) => command.startsWith(first));
			return filtered.map((command) => ({ value: command, label: command }));
		},
		handler: async (args, ctx) => {
			const [commandToken, ...rest] = parseArgs(args);
			const command = normalizeCommand(commandToken ?? "status");
			if (!command) {
				ctx.ui.notify(`Unknown Wily command: ${commandToken}`, "error");
				return;
			}
			await displayRun(pi, ctx, command, rest);
		},
	});

	for (const command of COMMANDS) {
		pi.registerCommand(`wily-${command}`, {
			description: `Run wily ${command}`,
			handler: async (args, ctx) => {
				await displayRun(pi, ctx, command, parseArgs(args));
			},
		});
	}

	pi.registerTool({
		name: "wily_cli",
		label: "Wily CLI",
		description:
			"Run the bundled Wily Roadmap CLI against the current project. Output is truncated to about 48KB. Use read-only commands like status, next, go, watch, and workspace status for task context; ask for approval before state-changing or remote/daemon actions.",
		promptSnippet: "Run Wily Roadmap task commands against the current project",
		promptGuidelines: [
			"Use wily_cli for Wily Roadmap task state instead of guessing from .wily files.",
			"wily_cli state-changing commands require explicit user approval; do not use them for remote or destructive actions unless the user asked for that action.",
		],
		parameters: Type.Object({
			command: Type.String({
				description: `Wily command. One of: ${COMMANDS.join(", ")}. The leading wily- or wily prefix is optional.`,
			}),
			args: Type.Optional(Type.Array(Type.String(), { description: "Command arguments as argv tokens, without shell quoting." })),
		}),
		prepareArguments(args) {
			if (!args || typeof args !== "object") return args;
			const input = args as { command?: unknown; args?: unknown; arguments?: unknown };
			if (Array.isArray(input.args) || !Array.isArray(input.arguments)) return args;
			return { ...input, args: input.arguments };
		},
		async execute(_toolCallId, params, signal, _onUpdate, ctx) {
			const command = normalizeCommand(params.command);
			if (!command) {
				return {
					content: [{ type: "text", text: `Unknown Wily command: ${params.command}. Expected one of: ${COMMANDS.join(", ")}` }],
					details: { ok: false },
				};
			}

			const args = params.args ?? [];
			if (requiresApprovalForTool(command, args)) {
				if (!ctx.hasUI) {
					return {
						content: [
							{
								type: "text",
								text: `Refusing to run approval-required command without an interactive UI: ${formatInvocation(command, args)}`,
							},
						],
						details: { ok: false, requiresApproval: true },
					};
				}
				const ok = await ctx.ui.confirm(
					"Wily Roadmap approval",
					`Allow this Wily command in ${ctx.cwd}?\n\n${formatInvocation(command, args)}`,
				);
				if (!ok) {
					return {
						content: [{ type: "text", text: `User denied: ${formatInvocation(command, args)}` }],
						details: { ok: false, denied: true },
					};
				}
			}

			const result = await runWily(pi, { cwd: ctx.cwd, command, args, signal });
			return {
				content: [{ type: "text", text: result.output }],
				details: {
					ok: result.code === 0,
					code: result.code,
					invocation: result.invocation,
					cwd: ctx.cwd,
				},
			};
		},
	});
}
