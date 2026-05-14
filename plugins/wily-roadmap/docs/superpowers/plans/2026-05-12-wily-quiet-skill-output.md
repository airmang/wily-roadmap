# Wily Quiet Skill Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Wily command skills produce concise user-facing responses that do not repeat internal helper commands or procedural chatter.

**Architecture:** Keep helper command invocation documented for agents, but label it as internal execution rather than user-facing output. Centralize shared response rules in one workflow reference, then give each command skill a short command-specific response contract. Add document tests that lock the quiet-output contract without requiring brittle exact wording.

**Tech Stack:** Markdown skill files, Codex plugin discovery-compatible skill layout, Python standard library `unittest`, `rg`.

---

## File Structure

- `skills/wily-workflow/references/response-style.md` - new shared policy for quiet user-facing Wily responses.
- `skills/wily-workflow/SKILL.md` - routing-level pointer to the shared response-style reference.
- `skills/wily-init/SKILL.md` - state-changing init contract: goal/status, files created or updated, next question or next action.
- `skills/wily-start/SKILL.md` - state-changing start contract: phase started, session path, immediate next action, then stop.
- `skills/wily-retry/SKILL.md` - state-changing retry contract: new attempt created, session path, scoped next action.
- `skills/wily-complete/SKILL.md` - state-changing complete contract: phase completed, verification/session status, next ready phase when available.
- `skills/wily-block/SKILL.md` - state-changing block contract: phase blocked, blocker reason, what approval/input is needed.
- `skills/wily-replan/SKILL.md` - state-changing replan contract: roadmap version/revision path, changed future phases, next review action.
- `skills/wily-status/SKILL.md` - read-only visual status contract: show pane output, avoid extra prose around it.
- `skills/wily-watch/SKILL.md` - read-only watch contract: report pane opened or fallback command only when the user must run it manually.
- `skills/wily-next/SKILL.md` - read-only next-phase contract: show phase id/title, dependency state, phase path, and start command as the user action.
- `tests/test_wily_command_skills.py` - document-level tests for quiet response contracts and internal command separation.
- `.wily/phases/06-1-quiet-skill-output/plan.md` - pointer to this implementation plan.

## Task 1: Capture The Current Response Guidance Baseline

**Files:**
- Read: `skills/wily-*/SKILL.md`
- Read: `skills/wily-workflow/SKILL.md`
- Read: `tests/test_wily_command_skills.py`

- [ ] **Step 1: List response and command sections**

Run:

```bash
rg -n '^## (Command|First Move|Report|Behavior|Required Before Running|When To Use|Rules|Boundaries|Response Style)' skills/wily-* -g 'SKILL.md'
```

Expected: every command skill has either `## Command` or `## First Move`, and most command skills have only a single Korean-announcement bullet under `## Response Style`.

- [ ] **Step 2: List helper command code blocks**

Run:

```bash
rg -n 'python3 <plugin-root>/scripts/wily.py|```bash' skills/wily-* -g 'SKILL.md'
```

Expected: helper command examples are present in command skills for agent execution. These examples must remain available to the agent, but the plan will mark them internal and forbid repeating them in normal final responses.

- [ ] **Step 3: Group duplicate response guidance**

Record this grouping before editing:

```text
Shared across command skills:
- Use Korean when announcing Wily plugin or skill usage for Korean-speaking users.
- Internal helper commands are documented in skill files.

Missing shared contract:
- Do not echo internal helper commands in normal final responses.
- Keep state-changing command responses to result, path or artifact, next action or blocker.
- Keep read-only command responses to requested output or concise answer.
- Preserve safety-critical approval-first warnings.

Command-specific output:
- wily-start and wily-retry need session path plus next action.
- wily-status needs the Wily Roadmap pane verbatim.
- wily-watch needs pane-opened/fallback status.
- wily-next needs concise next phase data and the user-facing start action.
- wily-block needs the blocker reason and unblock requirement.
- wily-complete needs completion result and verification/session status.
- wily-replan needs revision result and changed future-phase summary.
- wily-init needs goal/state result and the next question when no goal exists.
```

## Task 2: Add Failing Tests For Quiet Response Contracts

**Files:**
- Modify: `tests/test_wily_command_skills.py`

- [ ] **Step 1: Add response contract constants**

Add these constants after `COMMANDS`:

```python
MUTATING_COMMANDS = {"wily-init", "wily-start", "wily-complete", "wily-block", "wily-retry", "wily-replan"}
READONLY_COMMANDS = {"wily-status", "wily-watch", "wily-next"}
QUIET_RESPONSE_PHRASE = "Do not echo internal helper commands in normal user-facing responses."
```

- [ ] **Step 2: Add a test that every command separates internal execution from user response**

Add this test method to `WilyCommandSkillsTest`:

```python
    def test_command_skills_mark_helper_commands_as_internal(self) -> None:
        for command, helper in COMMANDS.items():
            with self.subTest(command=command):
                text = self.skill_text(command)
                self.assertIn("## Internal Command", text)
                self.assertIn(helper, text)
                self.assertIn(QUIET_RESPONSE_PHRASE, text)
```

- [ ] **Step 3: Add a test for state-changing response shape**

Add this test method:

```python
    def test_state_changing_commands_report_only_result_artifact_and_next_action(self) -> None:
        required = (
            "Report only the result, the relevant path or artifact, and the next action or blocker.",
            "Keep safety-critical approval requirements when they apply.",
        )
        for command in MUTATING_COMMANDS:
            with self.subTest(command=command):
                text = self.skill_text(command)
                for phrase in required:
                    self.assertIn(phrase, text)
```

- [ ] **Step 4: Add a test for read-only response shape**

Add this test method:

```python
    def test_readonly_commands_keep_output_concise(self) -> None:
        required = (
            "Report only the requested roadmap output or concise answer.",
            "Avoid procedural narration before or after the result.",
        )
        for command in READONLY_COMMANDS:
            with self.subTest(command=command):
                text = self.skill_text(command)
                for phrase in required:
                    self.assertIn(phrase, text)
```

- [ ] **Step 5: Keep the helper-command coverage compatible with the rename**

Leave `test_command_skills_reference_helper_commands` in place. It should still pass after `## Command` is renamed to `## Internal Command` because the helper command text remains in each skill.

- [ ] **Step 6: Run the focused tests and confirm failure**

Run:

```bash
python3 -m unittest tests.test_wily_command_skills
```

Expected: failures mention missing `## Internal Command`, missing quiet response phrase, and missing concise response contract phrases.

## Task 3: Centralize Shared Quiet Response Policy

**Files:**
- Create: `skills/wily-workflow/references/response-style.md`
- Modify: `skills/wily-workflow/SKILL.md`

- [ ] **Step 1: Create the shared response-style reference**

Create `skills/wily-workflow/references/response-style.md` with:

```markdown
# Response Style

Wily command skills distinguish internal execution from user-facing output.

## Shared Rules

- Do not echo internal helper commands in normal user-facing responses.
- Do not describe routine procedure such as reading files, running helper scripts, or checking generated context unless that detail changes the user's next decision.
- Use Korean when the user is speaking Korean, while keeping file paths, command names, status values, and machine-facing markers in English.
- Keep safety-critical approval requirements when they apply.
- If a command cannot complete, report the blocker and the smallest required user decision or approval.

## State-Changing Commands

- Report only the result, the relevant path or artifact, and the next action or blocker.
- Include changed roadmap/session state only when it helps the user decide what to do next.
- Do not continue into implementation after session-bookkeeping commands unless the user explicitly asks in a separate message.

## Read-Only Commands

- Report only the requested roadmap output or concise answer.
- Avoid procedural narration before or after the result.
- Show manual fallback commands only when the user must run them outside the agent.
```

- [ ] **Step 2: Link the reference from workflow skill**

In `skills/wily-workflow/SKILL.md`, add this line under `Read detailed policy only when needed:`:

```markdown
- Quiet user-facing responses: `references/response-style.md`
```

- [ ] **Step 3: Tighten workflow-level response style**

Replace the workflow `## Response Style` bullets with:

```markdown
- Be direct and concrete.
- Lead with current state, next action, and blockers.
- Do not echo internal helper commands in normal user-facing responses.
- Use Korean when the user is speaking Korean, but keep file content and machine-facing markers in English.
```

## Task 4: Update Command Skills To Use Internal Commands And Concise Contracts

**Files:**
- Modify: `skills/wily-init/SKILL.md`
- Modify: `skills/wily-status/SKILL.md`
- Modify: `skills/wily-watch/SKILL.md`
- Modify: `skills/wily-next/SKILL.md`
- Modify: `skills/wily-start/SKILL.md`
- Modify: `skills/wily-retry/SKILL.md`
- Modify: `skills/wily-complete/SKILL.md`
- Modify: `skills/wily-block/SKILL.md`
- Modify: `skills/wily-replan/SKILL.md`

- [ ] **Step 1: Rename helper command sections**

For every command skill with `## Command`, rename that heading to:

```markdown
## Internal Command
```

For `skills/wily-init/SKILL.md`, keep `## First Move`, but change step 4 from:

```markdown
4. Ensure local state exists with:
```

to:

```markdown
4. Ensure local state exists with this internal helper command:
```

- [ ] **Step 2: Add shared quiet-output bullets to every command skill response section**

Every `skills/wily-*/SKILL.md` command skill must include these bullets under `## Response Style`:

```markdown
- When announcing Wily plugin or skill usage, use Korean if the user is speaking Korean.
- Do not echo internal helper commands in normal user-facing responses.
```

- [ ] **Step 3: Add state-changing contract bullets**

Add these bullets to `wily-init`, `wily-start`, `wily-retry`, `wily-complete`, `wily-block`, and `wily-replan`:

```markdown
- Report only the result, the relevant path or artifact, and the next action or blocker.
- Keep safety-critical approval requirements when they apply.
```

- [ ] **Step 4: Add read-only contract bullets**

Add these bullets to `wily-status`, `wily-watch`, and `wily-next`:

```markdown
- Report only the requested roadmap output or concise answer.
- Avoid procedural narration before or after the result.
```

- [ ] **Step 5: Add command-specific response bullets**

Use these command-specific additions:

```markdown
<!-- skills/wily-start/SKILL.md -->
- For a successful start, include the phase id, `Session:` path, and one immediate next action, then stop.

<!-- skills/wily-retry/SKILL.md -->
- For a successful retry, include the phase id, new attempt/session path, and scoped next action.

<!-- skills/wily-complete/SKILL.md -->
- For a successful complete, include the phase id, completion result, and verification/session status.

<!-- skills/wily-block/SKILL.md -->
- For a block, include the phase id, blocker reason, and the smallest unblock requirement.

<!-- skills/wily-replan/SKILL.md -->
- For a successful replan, include the new roadmap version or revision path and the next review action.

<!-- skills/wily-init/SKILL.md -->
- If no goal is available, ask only for the intended final outcome after reporting baseline state.

<!-- skills/wily-status/SKILL.md -->
- Include the `Wily Roadmap` pane output verbatim in the user response.

<!-- skills/wily-watch/SKILL.md -->
- If the pane opens, report that it opened and how to stop it; show fallback commands only when tmux is unavailable.

<!-- skills/wily-next/SKILL.md -->
- Include only the next phase id/title, dependency status, phase path, plan availability, and `$wily-start <phase-id>` as the user-facing next action.
```

Remove the HTML comments while applying the bullets; they are only labels for this plan.

## Task 5: Rebalance Wily Next Context Guidance

**Files:**
- Modify: `skills/wily-next/SKILL.md`
- Modify if needed: `skills/wily-workflow/SKILL.md`

- [ ] **Step 1: Keep full context available but not mandatory in the final response**

In `skills/wily-next/SKILL.md`, replace this report list:

```markdown
- next executable phase, including `pending` phases whose dependencies are `done`
- dependency status
- phase definition
- planner adapter
- prompt
- verification
- handoff context
- whether an optional `plan.md` already exists
```

with:

```markdown
- next executable phase id and title
- dependency status
- phase path
- whether an optional `plan.md` already exists
- one sentence naming the immediate user action
```

- [ ] **Step 2: Preserve planner adapter boundary**

Keep this existing rule unchanged:

```markdown
Do not invoke the planner adapter while handling `$wily-next`; it is context for a later implementation step.
```

- [ ] **Step 3: Add path-first access to full context**

Add this sentence under the report list:

```markdown
Do not paste the full phase context unless the user asks for details; provide the phase path so it can be inspected when needed.
```

## Task 6: Verify Tests And Manual Output Contracts

**Files:**
- Read: `tests/test_wily_command_skills.py`
- Read: `skills/wily-*/SKILL.md`
- Read: `skills/wily-workflow/references/response-style.md`

- [ ] **Step 1: Run focused command-skill tests**

Run:

```bash
python3 -m unittest tests.test_wily_command_skills
```

Expected: all tests pass.

- [ ] **Step 2: Run full unittest discovery**

Run:

```bash
python3 -m unittest discover
```

Expected: all tests pass.

- [ ] **Step 3: Inspect final response sections**

Run:

```bash
rg -n '## Response Style|Do not echo internal helper commands|Report only|Avoid procedural narration|Session:' skills/wily-* -g 'SKILL.md'
```

Expected: every command skill has the quiet response phrase; mutating skills have result/path/next-action wording; read-only skills have concise-output wording.

- [ ] **Step 4: Confirm internal commands are still discoverable**

Run:

```bash
rg -n '## Internal Command|python3 <plugin-root>/scripts/wily.py' skills/wily-* -g 'SKILL.md'
```

Expected: every command skill still documents the helper command for agent execution, but the heading says `Internal Command` where applicable.

## Task 7: Update The Wily Phase Plan Pointer

**Files:**
- Modify: `.wily/phases/06-1-quiet-skill-output/plan.md`
- Modify if implementation proceeds: `.wily/sessions/2026-05-12-091127-phase-06-1-attempt-1/changed-files.md`
- Modify if implementation proceeds: `.wily/sessions/2026-05-12-091127-phase-06-1-attempt-1/verification.md`
- Modify if implementation proceeds: `.wily/sessions/2026-05-12-091127-phase-06-1-attempt-1/result.md`

- [ ] **Step 1: Replace the phase placeholder with a pointer**

Set `.wily/phases/06-1-quiet-skill-output/plan.md` to:

```markdown
# Implementation Plan

Detailed plan: `docs/superpowers/plans/2026-05-12-wily-quiet-skill-output.md`

Summary:
- Separate internal helper commands from user-facing responses.
- Add a shared quiet response policy reference.
- Give each command skill a concise response contract.
- Add tests that lock the quiet-output contract.
```

- [ ] **Step 2: During implementation, update session artifacts**

After code and documentation edits, record changed files and verification results in the current session files listed above. Do not mark the phase complete until verification has run or the reason it could not run is recorded.

## Self-Review

- Spec coverage: the plan covers concise command skill response guidance, state-changing result/path/next-action output, read-only concise output, safety-critical approval retention, and tests for response contracts.
- Placeholder scan: the plan contains concrete file paths, exact commands, expected outcomes, and exact Markdown/Python snippets.
- Type and naming consistency: the tests use existing `COMMANDS`, `skill_text`, and `WilyCommandSkillsTest` names from `tests/test_wily_command_skills.py`.
