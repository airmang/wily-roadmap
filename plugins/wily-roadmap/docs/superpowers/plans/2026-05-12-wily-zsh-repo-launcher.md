# Wily Zsh Repo Launcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a simple repo-local zsh command for running Wily status and watch commands without typing `python3 scripts/wily.py`.

**Architecture:** Add a checked-in root `./wily` zsh wrapper that delegates to the existing deterministic Python CLI without changing shell startup files or PATH. The wrapper resolves the repository script path from its own location but leaves the current working directory unchanged, so Wily continues to operate on the caller's current repo. Document the zsh usage in a short root `README.md` and lock the contract with CLI and documentation tests.

**Tech Stack:** zsh wrapper script, Python standard library `unittest`, Markdown documentation, existing `scripts/wily.py` CLI.

---

## File Structure

- Create: `wily` - repo-local zsh wrapper; executes `scripts/wily.py` with all arguments.
- Create: `README.md` - concise repo-local usage for zsh users, including `./wily status` and `./wily watch`.
- Modify: `tests/test_wily_cli.py` - add launcher behavior tests proving the wrapper delegates from the caller's current directory and passes watch arguments through.
- Modify: `tests/test_wily_command_skills.py` - add documentation contract tests for the zsh launcher and local-first boundary.
- Modify: `.wily/phases/06-3-zsh-repo-launcher/plan.md` - point the phase at this detailed plan.

## Task 1: Lock Launcher Behavior With Failing Tests

**Files:**
- Modify: `tests/test_wily_cli.py`
- Modify: `tests/test_wily_command_skills.py`

- [ ] **Step 1: Add imports and launcher constants**

In `tests/test_wily_cli.py`, add `import shutil` beside the existing imports:

```python
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
```

After `SCRIPT = ROOT / "scripts" / "wily.py"`, add:

```python
LAUNCHER = ROOT / "wily"
ZSH = shutil.which("zsh")
```

- [ ] **Step 2: Add a helper for running the launcher**

Inside `WilyCliTest`, after `run_wily_with_env`, add:

```python
    def run_launcher(
        self,
        project: Path,
        *args: str,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if ZSH is None:
            self.skipTest("zsh is not installed")
        return subprocess.run(
            [ZSH, str(LAUNCHER), *args],
            cwd=project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={**os.environ, **(env or {})},
        )
```

- [ ] **Step 3: Add a failing test that `./wily status` delegates from the caller cwd**

Add this method near the other status/watch tests:

```python
    def test_repo_launcher_status_delegates_from_current_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'goal: "Launcher smoke"',
                        'phases:',
                        '  - id: "01"',
                        '    title: "Launcher phase"',
                        '    path: "phases/01-launcher-phase"',
                        '    status: "ready"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_launcher(project, "status", env={"COLUMNS": "80", "LINES": "30"})

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wily Roadmap", result.stdout)
            self.assertIn("Launcher phase", result.stdout)
            self.assertNotIn(str(ROOT / ".wily"), result.stdout)
```

- [ ] **Step 4: Add a failing test that watch arguments pass through**

Add this method after the status launcher test:

```python
    def test_repo_launcher_watch_passes_arguments_to_wily_py(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.create_state(project)
            (project / ".wily" / "roadmap.yaml").write_text(
                "\n".join(
                    [
                        'roadmap_version: 1',
                        'phases:',
                        '  - id: "01"',
                        '    title: "Watch through launcher"',
                        '    path: "phases/01-watch-through-launcher"',
                        '    status: "ready"',
                        '    depends_on: []',
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_launcher(
                project,
                "watch",
                "--once",
                "--ui",
                "ascii",
                env={"COLUMNS": "80", "LINES": "30"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wily Roadmap", result.stdout)
            self.assertIn("Watch through launcher", result.stdout)
            self.assertNotIn("Rich UI is not installed", result.stdout)
```

- [ ] **Step 5: Add a failing test for wrapper safety**

Add this method after the launcher behavior tests:

```python
    def test_repo_launcher_is_zsh_and_local_first(self) -> None:
        text = LAUNCHER.read_text(encoding="utf-8")

        self.assertTrue(text.startswith("#!/usr/bin/env zsh"))
        self.assertIn('exec python3 "$repo_root/scripts/wily.py" "$@"', text)
        for forbidden in ("git push", "gh pr", ".zshrc", ".zprofile", "curl ", "rm -rf"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)
```

- [ ] **Step 6: Add a failing documentation contract test**

In `tests/test_wily_command_skills.py`, add this method near the manifest/documentation tests:

```python
    def test_readme_documents_repo_local_zsh_launcher(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("zsh", readme)
        self.assertIn("./wily status", readme)
        self.assertIn("./wily watch", readme)
        self.assertIn("does not modify shell startup files", readme)
        self.assertIn("local-first", readme)
```

- [ ] **Step 7: Run the focused tests and confirm they fail for the intended reason**

Run:

```bash
python3 -m unittest tests.test_wily_cli tests.test_wily_command_skills
```

Expected: FAIL because `wily` and `README.md` do not exist yet.

## Task 2: Add The Repo-Local Zsh Wrapper

**Files:**
- Create: `wily`

- [ ] **Step 1: Create `wily`**

Create root file `wily` with:

```zsh
#!/usr/bin/env zsh
set -euo pipefail

launcher_path=${0:A}
repo_root=${launcher_path:h}

exec python3 "$repo_root/scripts/wily.py" "$@"
```

- [ ] **Step 2: Make the wrapper executable**

Run:

```bash
chmod +x wily
```

Expected: exits 0.

- [ ] **Step 3: Run the wrapper safety test**

Run:

```bash
python3 -m unittest tests.test_wily_cli.WilyCliTest.test_repo_launcher_is_zsh_and_local_first
```

Expected: PASS.

- [ ] **Step 4: Run the wrapper behavior tests**

Run:

```bash
python3 -m unittest \
  tests.test_wily_cli.WilyCliTest.test_repo_launcher_status_delegates_from_current_directory \
  tests.test_wily_cli.WilyCliTest.test_repo_launcher_watch_passes_arguments_to_wily_py
```

Expected: PASS.

## Task 3: Document Zsh Usage

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create concise README usage**

Create `README.md` with:

````markdown
# Wily Roadmap

Wily is a local-first roadmap workflow plugin for agentic coding sessions.

## Repo-Local Zsh Command

From the repository root, run Wily with the checked-in zsh launcher:

```bash
./wily status
./wily next
./wily watch
./wily watch --once --ui ascii
```

The launcher delegates to `scripts/wily.py` and keeps the current working directory as the target repository. It does not modify shell startup files, install aliases, touch PATH, contact remotes, or perform destructive actions by itself.

Use `python3 scripts/wily.py <command>` when a Python-only invocation is preferred.

Wily behavior stays local-first: remote or destructive work requires explicit user approval.
````

- [ ] **Step 2: Run the README documentation test**

Run:

```bash
python3 -m unittest tests.test_wily_command_skills.WilyCommandSkillsTest.test_readme_documents_repo_local_zsh_launcher
```

Expected: PASS.

## Task 4: Manual Zsh Smoke Test

**Files:**
- No file edits.

- [ ] **Step 1: Run status through the wrapper from the repository root**

Run:

```bash
zsh ./wily status
```

Expected: exits 0 and prints a `Wily Roadmap` pane for the current repository.

- [ ] **Step 2: Run watch preview through the wrapper from the repository root**

Run:

```bash
zsh ./wily watch --once --ui ascii
```

Expected: exits 0 and prints a `Wily Roadmap` pane without opening tmux.

- [ ] **Step 3: Confirm no shell startup files are touched**

Run:

```bash
rg -n "\\.zshrc|\\.zprofile|PATH|alias wily|git push|gh pr|curl |rm -rf" wily README.md tests/test_wily_cli.py tests/test_wily_command_skills.py
```

Expected: only README explanatory text may mention `PATH`; no file should instruct editing shell startup files or running remote/destructive commands.

## Task 5: Phase Plan Pointer And Final Verification

**Files:**
- Modify: `.wily/phases/06-3-zsh-repo-launcher/plan.md`

- [ ] **Step 1: Point the phase plan at this detailed plan**

Replace `.wily/phases/06-3-zsh-repo-launcher/plan.md` with:

```markdown
# Implementation Plan

Detailed plan: `docs/superpowers/plans/2026-05-12-wily-zsh-repo-launcher.md`

## Summary

- Add a checked-in root `./wily` zsh wrapper that delegates to `scripts/wily.py`.
- Keep the current working directory as the target repository.
- Document `./wily status` and `./wily watch` usage without modifying shell startup files or PATH.
- Add focused tests for wrapper behavior, safety boundaries, and documentation.
```

- [ ] **Step 2: Run required phase verification**

Run:

```bash
python3 -m unittest tests.test_wily_cli tests.test_wily_command_skills
python3 -m unittest discover
```

Expected: all commands exit 0.

- [ ] **Step 3: Review changed files before completion**

Run:

```bash
git diff -- wily README.md tests/test_wily_cli.py tests/test_wily_command_skills.py docs/superpowers/plans/2026-05-12-wily-zsh-repo-launcher.md
```

Expected: changes are limited to the wrapper, README, focused tests, and the implementation plan.

## Self-Review

- Spec coverage: The plan provides a repo-root zsh command, documents zsh usage, keeps behavior local-first, avoids shell startup/PATH mutation, and adds tests for wrapper behavior plus documented command paths.
- Placeholder scan: No task relies on unspecified implementation details.
- Type and naming consistency: The launcher path is consistently `ROOT / "wily"`, helper name is `run_launcher`, and the command examples use `./wily`.
