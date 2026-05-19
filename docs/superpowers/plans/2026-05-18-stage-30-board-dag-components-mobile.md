# Stage 30 Board DAG Components Mobile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Wily Board repo workspace polish by replacing the current zigzag React Flow layout with dependency-aware DAG layout, adding the missing Headline and Attention surfaces, improving mobile behavior, and polishing repo switcher/pin ordering.

**Architecture:** The roadmap marketplace repo owns Stage state, but implementation happens in `/Users/wilycastle/Code/projects/wily-plugin/wily-board`. Keep the Board API read-only, consume existing `RepoDetail`, `Stage`, `DeskPayload`, and `RepoGroups` shapes, and confine UI changes to the Next.js frontend. Parallelize only where write scopes do not overlap.

**Tech Stack:** Next.js 15 App Router, React 19, TypeScript, React Flow, Framer Motion, shadcn/ui, Radix Progress, cmdk, lucide-react, Tailwind/CSS tokens, npm.

---

## Current State

- Roadmap stage: `.wily/stages/s30-board-dag-components-mobile/stage.yaml`
- Implementation repo: `/Users/wilycastle/Code/projects/wily-plugin/wily-board`
- Wily Board worktree is already dirty from earlier stages. Do not revert or clean unrelated changes.
- Existing `frontend/components/stage-map.tsx` uses `position: { x: index * 250, y: index % 2 === 0 ? 40 : 160 }`.
- Existing `frontend/components/repo-workspace.tsx` already renders a simple headline and inline Attention list, but Stage 30 wants those as deliberate components and with the specified progress/Alert behavior.
- Existing `frontend/components/local-desk.tsx` already has a mobile bar plus shadcn `Sheet`, but Stage 30 needs the rail fully hidden below 600px and the bottom sheet to be the mobile rail fallback.
- Existing `frontend/components/repo-list.tsx` already pins within each visibility group.
- Existing `frontend/components/repo-switcher.tsx` currently flattens repos and does not group Shared/Personal, order by recent, or show pinned status.
- Carryover dependency correction: `@dagrejs/dagre` is required for Stage 30 and should be present before implementation. `@tremor/react` is not used because the current Tremor package has a React 18 peer dependency while Wily Board is on React 19; use the local shadcn-style `Progress` primitive backed by `@radix-ui/react-progress` for the Headline instead of forcing an incompatible dependency.

## Dependency Graph

- Serial preflight: `30-0` must run first to confirm baseline, dependency gap, and current test status.
- First parallel wave after preflight:
  - Lane A: `30-1` DAG layout. Owns `stage-map.tsx` and DAG-specific CSS.
  - Lane B: `30-2` Headline plus `30-3` Attention. Owns new repo workspace components and minimal `repo-workspace.tsx` integration.
  - Lane C: `30-5` repo switcher and pin polish. Owns repo sorting/local storage helpers, `repo-switcher.tsx`, and `repo-list.tsx`.
- Final integration wave:
  - Lane D: `30-4` mobile fallback depends on Lane A because the mobile stage list should reuse the final stage ordering/collapsed-done logic. It also touches `local-desk.tsx` and mobile CSS, so run it after Lane A and after any CSS-heavy Lane B changes are merged.
- Final serial verification runs after all lanes merge.

## Parallelization Rules

- Workers are not alone in the codebase. They must not revert edits made by other workers or clean unrelated dirty files.
- Do not split `30-2` and `30-3` into separate workers; both need `repo-workspace.tsx` and shared section styling.
- Do not run `30-4` in parallel with `30-1`; both need `stage-map.tsx`.
- Keep dependency changes serial before dispatching frontend lanes so every worker sees the same lockfile.
- Prefer new focused components over growing `repo-workspace.tsx`:
  - `frontend/components/repo-headline.tsx`
  - `frontend/components/repo-attention.tsx`
  - optional `frontend/lib/repo-ordering.ts`

---

## Task 1: `30-0` Preflight And Dependency Decision

**Files:**
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package.json`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/package-lock.json`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/stage-map.tsx`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-workspace.tsx`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/local-desk.tsx`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-switcher.tsx`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-list.tsx`
- Read: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/ui/progress.tsx`

- [ ] **Step 1: Confirm dirty baseline**

Run:
```bash
git -C /Users/wilycastle/Code/projects/wily-plugin/wily-board status --short
```

Expected: existing dirty Stage 28/29 files may be present. Record the output in the phase notes; do not revert anything.

- [ ] **Step 2: Check required package availability**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm ls @xyflow/react framer-motion cmdk @radix-ui/react-dialog @radix-ui/react-tooltip @radix-ui/react-progress @dagrejs/dagre --depth=0
```

Expected: React Flow/shadcn/cmdk, `@radix-ui/react-progress`, and `@dagrejs/dagre` packages exist.

Confirm Tremor remains absent unless its React 19 peer dependency support changes:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
node -e "const p=require('./package.json'); console.log(p.dependencies['@tremor/react'] || 'absent')"
```

Expected: `absent`.

If `@dagrejs/dagre` or `@radix-ui/react-progress` is missing, install it before worker dispatch:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm install @dagrejs/dagre @radix-ui/react-progress
```

- [ ] **Step 3: Run baseline checks**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: record pass/fail. If failures are unrelated to Stage 30, capture them before proceeding.

---

## Task 2: `30-1` React Flow Dagre Layout

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/stage-map.tsx`
- Modify only if needed: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`

- [ ] **Step 1: Preserve Done prefix behavior**

Keep the current contiguous done-prefix collapse behavior, including the synthetic `done-prefix` node and edge from `done-prefix` to the next visible stage. Do not expand this task into clickable Done blob behavior unless already available in the current UI; Stage 30 acceptance only requires preserving the existing Done blob behavior.

- [ ] **Step 2: Replace index zigzag with dependency-aware layout**

Implement a layout helper shaped like:
```ts
const NODE_WIDTH = 220;
const NODE_HEIGHT = 118;

function layoutStages(stages: Stage[]): { nodes: Node<NodeData>[]; edges: Edge[] } {
  const visibleStages = collapseDonePrefix(stages);
  const edges = buildEdges(stages, visibleStages);
  return applyDagreLayout(visibleStages, edges);
}
```

If using `@dagrejs/dagre`, set `rankdir: "LR"`, `nodesep: 48`, `ranksep: 72`, and subtract half node width/height because dagre returns centered coordinates.

- [ ] **Step 3: Keep live and status affordances**

Do not remove `motion.div`, `Badge`, status CSS classes, `MiniMap`, `Controls`, `Background`, or animated edges for in-progress targets. Add live chip rendering only if the existing `Stage` payload already gives enough information without API changes.

- [ ] **Step 4: Verify**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: pass or only known unrelated baseline failures.

---

## Task 3: `30-2` Headline And `30-3` Attention Components

**Files:**
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-headline.tsx`
- Create: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-attention.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-workspace.tsx`
- Use: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/ui/progress.tsx`
- Modify only if needed: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`

- [ ] **Step 1: Extract Headline**

Create `RepoHeadline` with props:
```ts
import type { ApiRepo, DeskPayload } from "@/lib/types";

export function RepoHeadline({ repo, desk }: { repo: ApiRepo; desk: DeskPayload }) {
  const total = repo.stage_total || 0;
  const left = Math.max(0, total - repo.stage_done);
  const active = desk.working_now[0];
  return (
    <section className="headline" aria-label="Repository progress">
      {/* render repo.full_name, done/total stages, left count, visibility, progress */}
      {/* render active phase summary below only when active exists */}
    </section>
  );
}
```

Use the local `Progress` component from `@/components/ui/progress`. Do not add `@tremor/react` while it has a React 18 peer dependency.

- [ ] **Step 2: Extract Attention**

Create `RepoAttention` with props:
```ts
import type { RepoDetail } from "@/lib/types";

type AttentionItem = RepoDetail["attention"][number];

export function RepoAttention({ items }: { items: AttentionItem[] }) {
  if (!items.length) return null;
  return (
    <section className="workspace-panel" aria-label="Attention">
      {/* shadcn Alert rows grouped visually for blocked and needs_review items */}
    </section>
  );
}
```

Keep it render-only. Do not add mutating actions.

- [ ] **Step 3: Integrate into RepoWorkspace**

In `repo-workspace.tsx`, replace the inline headline block with `<RepoHeadline repo={detail.repo} desk={detail.desk} />` and replace the inline Attention section with `<RepoAttention items={detail.attention} />`.

- [ ] **Step 4: Verify**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: pass or only known unrelated baseline failures.

---

## Task 4: `30-5` Repo Switcher And Pin Polish

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/storage.ts`
- Create optional: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/lib/repo-ordering.ts`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-switcher.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-list.tsx`

- [ ] **Step 1: Add recent repo storage helpers**

Extend storage helpers without changing existing pinned storage key:
```ts
const RECENT_KEY = "wily.board.recentRepos";

export function getRecentRepos() {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY) ?? "[]") as string[];
  } catch {
    return [];
  }
}

export function rememberRecentRepo(fullName: string) {
  const next = [fullName, ...getRecentRepos().filter((name) => name !== fullName)].slice(0, 8);
  localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  return next;
}
```

- [ ] **Step 2: Centralize ordering**

Add or inline a deterministic comparator:
```ts
export function sortRepos(repos: ApiRepo[], pins: Set<string>, recent: string[] = []) {
  const recentRank = new Map(recent.map((name, index) => [name, index]));
  return [...repos].sort((a, b) => {
    const pinDiff = Number(pins.has(b.full_name)) - Number(pins.has(a.full_name));
    if (pinDiff) return pinDiff;
    const aRecent = recentRank.get(a.full_name);
    const bRecent = recentRank.get(b.full_name);
    if (aRecent !== undefined || bRecent !== undefined) {
      return (aRecent ?? 999) - (bRecent ?? 999);
    }
    return a.full_name.localeCompare(b.full_name);
  });
}
```

- [ ] **Step 3: Update RepoSwitcher**

Keep `CommandPalette` public behavior. When opened, keep shared and personal arrays separate, render grouped headings, show a filled `Star` for pinned repos, and call `rememberRecentRepo(repo.full_name)` before navigation.

- [ ] **Step 4: Reuse ordering in Hub repo lists**

Update `RepoGroup` to use the shared ordering helper with pins and no recent override unless product wants recent ordering on the Hub too. Preserve current pinned-first behavior.

- [ ] **Step 5: Verify**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: pass or only known unrelated baseline failures.

---

## Task 5: `30-4` Mobile Fallback

**Files:**
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/stage-map.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/local-desk.tsx`
- Modify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/app/globals.css`

- [ ] **Step 1: Add vertical mobile stage list**

In `stage-map.tsx`, render a sibling list that uses the same visible stage sequence as the DAG layout:
```tsx
<ol className="mobile-stage-list" aria-label="Stages">
  {visibleStages.map((stage) => (
    <li key={stage.stage_id} className={`mobile-stage-row status-${stage.status}`}>
      <span className="dot" aria-hidden="true" />
      <span className="mono">{stage.stage_id === "done-prefix" ? "Done" : stage.stage_id}</span>
      <span>{stage.title}</span>
      <Badge variant="outline">{stage.phase_done}/{stage.phase_count || 0}</Badge>
    </li>
  ))}
</ol>
```

Desktop should still render React Flow. Mobile below 600px should hide the canvas and show this list.

- [ ] **Step 2: Tighten mobile rail fallback**

Keep the existing `Sheet` in `local-desk.tsx`, but ensure `SheetContent` opens from the bottom on mobile if the local shadcn `SheetContent` supports `side="bottom"`. The trigger should be a sticky top badge/button with working and next counts. Desktop rail behavior must remain unchanged.

- [ ] **Step 3: Add mobile CSS**

In `globals.css`, keep `.react-flow-shell { display: none; }` under `max-width: 600px`, add `.mobile-stage-list` display rules, keep `.rail { display: none; }`, and make `.mobile-live-bar` sticky enough to remain useful without covering the topbar.

- [ ] **Step 4: Verify**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: pass or only known unrelated baseline failures.

---

## Task 6: Final Integration And Visual Verification

**Files:**
- Read/verify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/stage-map.tsx`
- Read/verify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-workspace.tsx`
- Read/verify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/local-desk.tsx`
- Read/verify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-switcher.tsx`
- Read/verify: `/Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend/components/repo-list.tsx`

- [ ] **Step 1: Run full frontend checks**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board/frontend
npm run lint
npm run build
```

Expected: pass.

- [ ] **Step 2: Run backend/API checks if package or API assumptions changed**

Run:
```bash
cd /Users/wilycastle/Code/projects/wily-plugin/wily-board
uv run pytest
```

Expected: pass, especially readonly and API route tests.

- [ ] **Step 3: Browser verification**

Start the local services according to the current Board dev workflow, then verify:

- Desktop repo workspace shows dependency-shaped DAG, Headline, Attention only when data exists, and desktop rail.
- iPhone SE width around 375px hides React Flow, shows vertical stage list, and opens local desk through a bottom sheet.
- Repo switcher groups Shared/Personal, recent repos rise to the top inside their group, and pinned repos show a star.
- Hub repo lists keep pinned repos at the top of each visibility group.

- [ ] **Step 4: Record Wily evidence**

Record verification evidence in the active Stage 30 phase notes or session artifacts before marking any phase complete.

## Recommended Execution Order

1. Run `30-0` serially.
2. If `@dagrejs/dagre` or `@radix-ui/react-progress` is missing, install it serially.
3. Dispatch Lane A `30-1`, Lane B `30-2+30-3`, and Lane C `30-5` in parallel.
4. Merge/review those lanes.
5. Run Lane D `30-4`.
6. Run final integration and browser verification.

## Self-Review

- Spec coverage: DAG dagre/layout, Headline, Attention, mobile fallback, repo switcher grouping/recent/pin, and Hub pin ordering are each covered.
- Placeholder scan: no unfinished-marker steps remain.
- Type consistency: plan uses existing exported `ApiRepo`, `DeskPayload`, `RepoDetail`, and `Stage` frontend types.
