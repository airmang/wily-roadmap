# Stage 29 Board Polish Stack Lift Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lift Wily Board's existing Next.js frontend onto Tailwind, shadcn/ui, Framer Motion, TanStack Query, next-themes, date-fns, sanitized markdown, and OpenAPI-generated types without changing backend API behavior.

**Architecture:** The roadmap marketplace repo owns Wily stage state, but code changes for this stage happen in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`. Keep the FastAPI API read-only and use the current Next.js App Router frontend as the integration surface. Build a serial foundation first, then split independent frontend lanes by non-overlapping write scopes and integrate with one final build/browser pass.

**Tech Stack:** FastAPI, pytest, Next.js 15 App Router, React 19, TypeScript, npm package-lock, Tailwind CSS, shadcn/ui/Radix, Framer Motion, TanStack Query, next-themes, date-fns, react-markdown, rehype-sanitize, openapi-typescript.

---

## Current State

- Roadmap repo: `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`
- Implementation repo: `/Users/wilycastle/Code/projects/wily-plugin/wily-board`
- Important constraint: `/Users/wilycastle/Code/projects/wily-plugin/wily-board` is already dirty from Stage 28 readonly cutover. Do not revert or restage those changes.
- Package manager: use `npm`, not `pnpm`; `frontend/package-lock.json` is the current lockfile.
- Existing frontend has raw CSS tokens in `frontend/app/globals.css`, hand-rolled `.chip`, `.icon-button`, `.dialog-overlay`, and `router.refresh()` in `frontend/components/live-refresh.tsx`.
- Existing backend already exposes `/openapi.json` through FastAPI defaults and read-only JSON APIs under `/api/*`.

## Dependency Graph

- Serial foundation: `29-1` must land first.
- Parallel after foundation:
  - Lane A: `29-4` TanStack Query + SSE invalidation.
  - Lane B: `29-5` next-themes + date-fns + markdown + OpenAPI types.
- Integration after Lane A/B: `29-2` shadcn primitive migration. This depends on the UI component scaffold and benefits from theme/query providers already existing.
- Final polish: `29-3` Framer Motion transitions. This depends on shadcn migration because the rail/dialog surfaces should be stable before animation.

## Parallelization Rules

- Only dispatch parallel workers after Task 2 completes and commits.
- Parallel workers must be told: this is a shared repo with existing dirty Stage 28 changes; do not revert or clean unrelated files.
- Parallel write scopes:
  - Lane A owns `frontend/components/live-refresh.tsx`, `frontend/components/query-provider.tsx`, `frontend/lib/client-api.ts`, `frontend/lib/query-keys.ts`, and minimal provider wiring in `frontend/app/layout.tsx`.
  - Lane B owns `frontend/components/theme-provider.tsx`, `frontend/components/theme-toggle.tsx`, `frontend/lib/format.ts`, `frontend/lib/api-types.ts`, `frontend/scripts/`, and `frontend/components/phase-markdown.tsx`.
  - Integration owner owns `frontend/components/ui/*`, `frontend/components/local-desk.tsx`, `frontend/components/repo-switcher.tsx`, `frontend/components/desk.tsx`, `frontend/components/repo-list.tsx`, `frontend/components/phase-list.tsx`, and `frontend/app/globals.css`.
- If two lanes both need `frontend/app/layout.tsx`, make the smallest provider wrapper changes and let the integration owner reconcile the wrapper order.

---

## Task 1: Preflight and Baseline

**Files:**
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package.json`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/live-refresh.tsx`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/local-desk.tsx`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-switcher.tsx`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/phase-list.tsx`

- [ ] **Step 1: Confirm dirty state before touching files**

Run:
```bash
git -C /Users/wilycastle/Code/projects/wily-plugin/wily-board status --short
```

Expected: Stage 28 dirty files may be present. Treat them as user-owned baseline.

- [ ] **Step 2: Run current frontend checks**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: record pass/fail. If failures are unrelated to s29, note them before implementation and keep going only if the failure does not block dependency installation.

- [ ] **Step 3: Run current backend checks**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest
```

Expected: record pass/fail. s29 should not require backend API signature changes.

---

## Task 2: `29-1` Tailwind + shadcn/ui Foundation

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package.json`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package-lock.json`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/tailwind.config.ts`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/postcss.config.mjs`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components.json`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/utils.ts`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/ui/button.tsx`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/ui/badge.tsx`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/ui/dialog.tsx`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/ui/sheet.tsx`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/ui/tooltip.tsx`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/ui/alert.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`

- [ ] **Step 1: Install foundation dependencies**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm install tailwindcss postcss autoprefixer tailwindcss-animate class-variance-authority clsx tailwind-merge @radix-ui/react-dialog @radix-ui/react-slot @radix-ui/react-tooltip
```

Expected: `package.json` and `package-lock.json` gain the Tailwind/shadcn/Radix foundation packages.

- [ ] **Step 2: Add Tailwind config with Wily tokens**

Create `frontend/tailwind.config.ts` with the Wily CSS variables mapped to Tailwind token names:
```ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      borderRadius: {
        lg: "var(--wb-radius)",
        md: "calc(var(--wb-radius) - 2px)",
        sm: "calc(var(--wb-radius) - 4px)",
      },
      colors: {
        bg: "rgb(var(--wb-bg) / <alpha-value>)",
        surface: "rgb(var(--wb-surface) / <alpha-value>)",
        "surface-2": "rgb(var(--wb-surface-2) / <alpha-value>)",
        border: "rgb(var(--wb-border) / <alpha-value>)",
        text: "rgb(var(--wb-text) / <alpha-value>)",
        "text-muted": "rgb(var(--wb-text-muted) / <alpha-value>)",
        accent: "rgb(var(--wb-accent) / <alpha-value>)",
        status: {
          done: "rgb(var(--wb-status-done) / <alpha-value>)",
          prog: "rgb(var(--wb-status-prog) / <alpha-value>)",
          review: "rgb(var(--wb-status-review) / <alpha-value>)",
          ready: "rgb(var(--wb-status-ready) / <alpha-value>)",
          blocked: "rgb(var(--wb-status-blocked) / <alpha-value>)",
          pending: "rgb(var(--wb-status-pending) / <alpha-value>)",
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
```

- [ ] **Step 3: Add PostCSS config**

Create `frontend/postcss.config.mjs`:
```js
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

export default config;
```

- [ ] **Step 4: Add shadcn component registry config**

Create `frontend/components.json`:
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "app/globals.css",
    "baseColor": "zinc",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide"
}
```

- [ ] **Step 5: Add shadcn utility helper**

Create `frontend/lib/utils.ts`:
```ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 6: Generate or add shadcn primitives**

Preferred command:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npx shadcn@latest add button badge dialog sheet tooltip alert
```

Expected: `frontend/components/ui/*` contains local component source, not an opaque component package.

- [ ] **Step 7: Keep globals as token + compatibility layer**

Modify `frontend/app/globals.css` to start with:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Keep the existing `:root` and `[data-theme="dark"]` variable blocks. Keep existing `.app-shell`, `.workspace`, `.stage-node`, `.phase-row`, `.chip`, and `.icon-button` compatibility classes until Task 5 migrates call sites.

- [ ] **Step 8: Verify foundation**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: both pass; existing screens render without requiring call-site rewrites.

- [ ] **Step 9: Commit foundation**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
git add frontend/package.json frontend/package-lock.json frontend/tailwind.config.ts frontend/postcss.config.mjs frontend/components.json frontend/lib/utils.ts frontend/components/ui frontend/app/globals.css
git commit -m "feat(board): add Tailwind and shadcn foundation"
```

Expected: commit succeeds only if Stage 28 dirty changes are intentionally included or already committed. If unrelated dirty files remain, do not commit them accidentally.

---

## Task 3A: Parallel Lane A - `29-4` TanStack Query + SSE Invalidation

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package.json`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package-lock.json`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/query-provider.tsx`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/query-keys.ts`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/client-api.ts`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/live-refresh.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/layout.tsx`

- [ ] **Step 1: Install TanStack Query**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm install @tanstack/react-query
```

- [ ] **Step 2: Add query keys**

Create `frontend/lib/query-keys.ts`:
```ts
export const queryKeys = {
  repos: ["repos"] as const,
  desk: ["desk"] as const,
  repoDesk: (owner: string, name: string) => ["repo", owner, name, "desk"] as const,
  repo: (owner: string, name: string) => ["repo", owner, name] as const,
  phase: (owner: string, name: string, stageId: string, phaseId: string) =>
    ["repo", owner, name, "stage", stageId, "phase", phaseId] as const,
};
```

- [ ] **Step 3: Add client fetch helper for browser queries**

Create `frontend/lib/client-api.ts`:
```ts
import type { DeskPayload, PhaseDetail, RepoDetail, RepoGroups } from "./types";

async function clientFetch<T>(path: string): Promise<T> {
  const response = await fetch(path, { credentials: "include" });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return (await response.json()) as T;
}

export function fetchRepoGroups() {
  return clientFetch<RepoGroups>("/api/repos");
}

export function fetchDesk(path = "/api/desk") {
  return clientFetch<DeskPayload>(path);
}

export function fetchRepoDetail(owner: string, name: string) {
  return clientFetch<RepoDetail>(`/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`);
}

export function fetchPhaseDetail(owner: string, name: string, stageId: string, phaseId: string) {
  return clientFetch<PhaseDetail>(
    `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/stages/${encodeURIComponent(stageId)}/phases/${encodeURIComponent(phaseId)}`,
  );
}
```

- [ ] **Step 4: Add QueryClient provider**

Create `frontend/components/query-provider.tsx`:
```tsx
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 15_000,
            refetchOnWindowFocus: true,
            retry: 1,
          },
        },
      }),
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
```

- [ ] **Step 5: Convert SSE to key-based invalidation**

Modify `frontend/components/live-refresh.tsx` so it no longer imports `useRouter`. It should use `useQueryClient()` and invalidate specific keys:
```tsx
"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { toast } from "sonner";

import { queryKeys } from "@/lib/query-keys";

type LiveEventPayload = {
  repo?: {
    owner?: string;
    name?: string;
    full_name?: string;
  };
};

function invalidateRepoPayload(queryClient: ReturnType<typeof useQueryClient>, payload: LiveEventPayload) {
  queryClient.invalidateQueries({ queryKey: queryKeys.desk });
  queryClient.invalidateQueries({ queryKey: queryKeys.repos });
  const owner = payload.repo?.owner;
  const name = payload.repo?.name;
  if (owner && name) {
    queryClient.invalidateQueries({ queryKey: queryKeys.repo(owner, name) });
    queryClient.invalidateQueries({ queryKey: queryKeys.repoDesk(owner, name) });
  }
}

export function LiveRefresh({ enabled }: { enabled: boolean }) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!enabled) return;

    const source = new EventSource("/api/sse/live");
    source.addEventListener("live_item.updated", (event) => {
      invalidateRepoPayload(queryClient, JSON.parse(event.data) as LiveEventPayload);
    });
    source.addEventListener("live_item.cleared", (event) => {
      invalidateRepoPayload(queryClient, JSON.parse(event.data) as LiveEventPayload);
    });
    source.addEventListener("durable.synced", () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.desk });
      queryClient.invalidateQueries({ queryKey: queryKeys.repos });
      queryClient.invalidateQueries({ queryKey: ["repo"] });
    });
    source.addEventListener("open", () => {
      toast.dismiss("live-disconnected");
    });
    source.addEventListener("error", () => {
      toast("Live updates disconnected - retrying", { id: "live-disconnected" });
    });
    return () => source.close();
  }, [enabled, queryClient]);

  return null;
}
```

- [ ] **Step 6: Wrap layout with QueryProvider**

Modify `frontend/app/layout.tsx` so `LiveRefresh` is rendered inside `QueryProvider`:
```tsx
<body>
  <QueryProvider>
    <Header />
    <LiveRefresh enabled={liveRefreshEnabled} />
    {children}
    <Toaster position="bottom-right" />
  </QueryProvider>
</body>
```

- [ ] **Step 7: Verify no route refresh remains**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
rg -n "router\\.refresh|useRouter" frontend/components/live-refresh.tsx frontend
cd frontend
npm run lint
npm run build
```

Expected: no `router.refresh` reference in `live-refresh.tsx`; lint and build pass.

---

## Task 3B: Parallel Lane B - `29-5` Themes, Dates, Markdown, OpenAPI Types

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package.json`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package-lock.json`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/theme-provider.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/theme-toggle.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/layout.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/format.ts`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/phase-markdown.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/phase-list.tsx`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/api-types.ts`

- [ ] **Step 1: Install dependencies**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm install next-themes date-fns react-markdown rehype-sanitize
npm install --save-dev openapi-typescript
```

- [ ] **Step 2: Add next-themes provider**

Create `frontend/components/theme-provider.tsx`:
```tsx
"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider attribute="data-theme" defaultTheme="system" enableSystem disableTransitionOnChange>
      {children}
    </NextThemesProvider>
  );
}
```

- [ ] **Step 3: Replace manual theme toggle**

Modify `frontend/components/theme-toggle.tsx`:
```tsx
"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const isDark = mounted && resolvedTheme === "dark";
  return (
    <Button
      variant="ghost"
      size="icon"
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label="Toggle theme"
    >
      {isDark ? <Sun size={18} /> : <Moon size={18} />}
    </Button>
  );
}
```

- [ ] **Step 4: Wrap layout with ThemeProvider**

Modify `frontend/app/layout.tsx` so `ThemeProvider` wraps the visible app inside `<body>`. If Task 3A already added `QueryProvider`, use:
```tsx
<body>
  <ThemeProvider>
    <QueryProvider>
      <Header />
      <LiveRefresh enabled={liveRefreshEnabled} />
      {children}
      <Toaster position="bottom-right" />
    </QueryProvider>
  </ThemeProvider>
</body>
```

- [ ] **Step 5: Replace relative time helper with date-fns Korean locale**

Modify `frontend/lib/format.ts`:
```ts
import { ko } from "date-fns/locale";
import { formatDistanceToNow } from "date-fns";

export function statusLabel(status: string) {
  return status.replaceAll("_", " ");
}

export function relativeTime(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return formatDistanceToNow(date, { locale: ko, addSuffix: true });
}
```

- [ ] **Step 6: Add sanitized markdown renderer**

Create `frontend/components/phase-markdown.tsx`:
```tsx
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

export function PhaseMarkdown({ children }: { children: string }) {
  return (
    <div className="phase-markdown">
      <ReactMarkdown rehypePlugins={[rehypeSanitize]}>{children}</ReactMarkdown>
    </div>
  );
}
```

Modify `frontend/components/phase-list.tsx`:
```tsx
import { PhaseMarkdown } from "./phase-markdown";
```

Replace:
```tsx
{phase.task ? <p className="phase-task">{phase.task}</p> : null}
```

With:
```tsx
{phase.task ? <PhaseMarkdown>{phase.task}</PhaseMarkdown> : null}
```

- [ ] **Step 7: Add OpenAPI type generation script**

Modify `frontend/package.json` scripts:
```json
"types:generate": "openapi-typescript http://127.0.0.1:8000/openapi.json -o lib/api-types.ts",
"types:check": "npm run types:generate && git diff --exit-code -- lib/api-types.ts"
```

- [ ] **Step 8: Generate initial API types**

Run backend in one shell:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

Run generation in another shell:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run types:generate
```

Expected: `frontend/lib/api-types.ts` is created from FastAPI OpenAPI.

- [ ] **Step 9: Verify lane**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: lint and build pass; no custom localStorage theme code remains in `theme-toggle.tsx`.

---

## Task 4: Merge Parallel Lanes

**Files:**
- Review: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/layout.tsx`
- Review: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package.json`
- Review: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package-lock.json`

- [ ] **Step 1: Reconcile provider nesting**

Ensure `layout.tsx` has one wrapper stack in this order:
```tsx
<ThemeProvider>
  <QueryProvider>
    <Header />
    <LiveRefresh enabled={liveRefreshEnabled} />
    {children}
    <Toaster position="bottom-right" />
  </QueryProvider>
</ThemeProvider>
```

- [ ] **Step 2: Verify all foundation and parallel dependencies are present**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm ls @tanstack/react-query next-themes date-fns react-markdown rehype-sanitize openapi-typescript tailwindcss @radix-ui/react-dialog
```

Expected: all packages resolve.

- [ ] **Step 3: Build before UI migration**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: pass.

---

## Task 5: `29-2` shadcn Primitive Migration

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-switcher.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/local-desk.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/desk.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-list.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/phase-list.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/repos/[owner]/[name]/page.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`

- [ ] **Step 1: Replace repo switcher overlay with shadcn Dialog shell**

In `repo-switcher.tsx`, remove the manual `<div className="dialog-overlay" />` and wrap `Command` with the generated `Dialog` primitives. Keep `cmdk` list behavior and `CommandPalette` public API unchanged.

- [ ] **Step 2: Replace icon buttons with shadcn Button**

In `repo-switcher.tsx`, `local-desk.tsx`, `repo-list.tsx`, and `theme-toggle.tsx`, use:
```tsx
<Button variant="ghost" size="icon" type="button" aria-label="...">
  <Icon size={16} />
</Button>
```

Expected: `.icon-button` call sites disappear except compatibility CSS if still used by older pages.

- [ ] **Step 3: Replace chips with Badge**

In `desk.tsx`, `repo-list.tsx`, `local-desk.tsx`, `phase-list.tsx`, and repo page attention rows, replace static `<span className="chip">` with:
```tsx
<Badge variant="secondary">...</Badge>
```

Use `variant="outline"` for metadata such as visibility, dependency lists, and draft labels.

- [ ] **Step 4: Convert Local Desk rail to Sheet-backed surface**

In `local-desk.tsx`, keep `LocalDesk({ repo, desk })` unchanged. Use `Sheet`, `SheetContent`, and `SheetTrigger` for mobile/bottom behavior while retaining desktop `<aside>` for the width-aware rail. Persist `wily.board.railCollapsed` exactly as today.

- [ ] **Step 5: Add Tooltip for pin controls**

Wrap pin buttons in `TooltipProvider`, `Tooltip`, `TooltipTrigger`, and `TooltipContent` with labels `"Pin repo"` and `"Unpin repo"` based on current state.

- [ ] **Step 6: Convert Attention block to Alert**

In repo page attention block, use generated `Alert` for the section body, preserving the existing `detail.attention.map` data and no new backend fields.

- [ ] **Step 7: Trim compatibility CSS**

In `globals.css`, remove `.dialog-overlay`, `.command-dialog` overlay styles that shadcn now owns. Keep layout-specific classes such as `.app-shell`, `.workspace`, `.react-flow-shell`, `.stage-node`, `.phase-row`, and `.phase-markdown`.

- [ ] **Step 8: Verify accessibility and build**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
rg -n "dialog-overlay|className=\\\"chip\\\"|className=\\\"icon-button\\\"" frontend
cd frontend
npm run lint
npm run build
```

Expected: no manual dialog overlay; no direct `.chip`/`.icon-button` usage in migrated components; lint and build pass.

---

## Task 6: `29-3` Framer Motion Transitions

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package.json`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package-lock.json`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/local-desk.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/stage-map.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/desk.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`

- [ ] **Step 1: Install Framer Motion**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm install framer-motion
```

- [ ] **Step 2: Animate Local Desk width with reduced-motion guard**

In `local-desk.tsx`, import `motion` and `useReducedMotion` from `framer-motion`. Replace desktop `<aside>` with:
```tsx
<motion.aside
  className="rail"
  animate={{ width: collapsed ? 56 : 320 }}
  transition={{ duration: prefersReducedMotion ? 0 : 0.2, ease: "easeOut" }}
>
```

Keep mobile Sheet behavior from Task 5.

- [ ] **Step 3: Add MY DESK staggered entry**

In `desk.tsx`, use `motion.ul` and `motion.li` for non-empty `DeskList`. Duration must be `0` when `useReducedMotion()` returns true and `0.18` otherwise.

- [ ] **Step 4: Animate stage nodes and Done blob transitions**

In `stage-map.tsx`, pass stable node IDs and wrap the `StageNode` content with `motion.div layout`. Use reduced-motion duration `0`; otherwise duration `0.18`. Do not replace react-flow layout or add DAG features reserved for s30.

- [ ] **Step 5: Add global reduced motion reset**

Append to `globals.css`:
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.001ms !important;
  }
}
```

- [ ] **Step 6: Verify animation path**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: pass. Browser verification must also toggle reduced motion in DevTools and confirm rail/opening transitions stop.

---

## Task 7: Full Verification

**Files:**
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/.next`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/tests`

- [ ] **Step 1: Run backend tests**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest
```

Expected: all tests pass or only pre-existing Stage 28 failures remain with notes.

- [ ] **Step 2: Run frontend checks**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: pass.

- [ ] **Step 3: Verify no forbidden readonly regressions**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
rg -n "Open PR|/actions/phase/status|new_status|toggle_status|router\\.refresh\\(\\)" app frontend tests
```

Expected: no active UI/backend mutation references and no `router.refresh()` in SSE refresh path.

- [ ] **Step 4: Browser smoke**

Run backend:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

Run frontend:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run dev
```

Open `http://127.0.0.1:3000/me` and a repo workspace. Verify:
- dark/light toggle does not flash after reload;
- repo switcher opens with keyboard and closes with Escape;
- Local Desk rail collapses/expands and persists;
- phase task markdown renders bold, links, and code blocks;
- SSE disconnect toast still appears if backend is stopped;
- mobile width shows the Local Desk bottom Sheet path.

---

## Commit Plan

- Commit 1: `feat(board): add Tailwind and shadcn foundation` (`29-1`)
- Commit 2A: `feat(board): use query invalidation for live updates` (`29-4`)
- Commit 2B: `feat(board): add themes markdown dates and generated api types` (`29-5`)
- Commit 3: `feat(board): migrate board controls to shadcn primitives` (`29-2`)
- Commit 4: `feat(board): add reduced-motion aware transitions` (`29-3`)

Do not commit roadmap `.wily` status changes until the corresponding Wily phase is actually completed through the normal `$wily-start` / `$wily-complete` flow.

## Self-Review

- Spec coverage: covers s29 scope for Tailwind/shadcn, shadcn primitive migration, Framer Motion, reduced motion, TanStack Query SSE invalidation, next-themes, date-fns Korean relative time, sanitized markdown, and OpenAPI type generation.
- Explicit non-scope preserved: no new s30 Headline/Attention component redesign, no DAG layout replacement, no mobile fallback redesign beyond shadcn Sheet wiring for existing Local Desk behavior, no backend API signature changes.
- Parallel safety: only `29-4` and `29-5` run in parallel after `29-1`; `29-2` and `29-3` remain serial integration tasks because they touch shared visual components.
