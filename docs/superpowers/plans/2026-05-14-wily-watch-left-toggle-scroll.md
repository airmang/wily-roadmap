# Wily Watch Left Toggle Scroll Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `$wily-watch` toggle completed-stage folding only on left-click, and make expanded completed-stage content scroll with the mouse wheel.

**Architecture:** Keep mouse input handling in `scripts/wily.py` and rendering in `scripts/wily_watch_ui.py`. Extend the existing SGR mouse parser to preserve button code, add explicit scroll actions, then pass a clamped scroll offset into the watch renderer.

**Tech Stack:** Python stdlib CLI, `unittest`, existing Wily ASCII/Rich renderer.

---

## File Structure

- Modify `scripts/wily.py`: parse SGR mouse button codes, return explicit actions (`toggle_done`, `scroll_up`, `scroll_down`, etc.), and maintain scroll offset in `watch_here_interactive`.
- Modify `scripts/wily_watch_ui.py`: add scroll offset support to `_body_lines()` and `render_watch()`, plus a pure clamp helper for tests.
- Modify `tests/test_wily_cli.py`: replace current "any press toggles when expanded" contract with left-click-only and wheel action tests.
- Modify `tests/test_wily_watch_ui.py`: add renderer scroll/clamp tests and adjust footer wording expectations.
- Modify `skills/wily-watch/SKILL.md`: document left-click toggle and wheel scrolling.

## Task 1: Mouse Parser And Action Contract

**Files:**
- Modify: `scripts/wily.py`
- Test: `tests/test_wily_cli.py`

- [ ] **Step 1: Write failing parser/action tests**

Replace the current `WatchInputTest` mouse tests in `tests/test_wily_cli.py` with explicit button-code behavior:

```python
    def test_left_mouse_press_on_body_toggles_done(self) -> None:
        self.assertEqual(
            wily.watch_action_from_input("\x1b[<0;12;4M", summary_row=4, body_rows=1),
            "toggle_done",
        )
        self.assertEqual(
            wily.watch_action_from_input("\x1b[<0;12;6M", summary_row=4, body_rows=3),
            "toggle_done",
        )

    def test_non_left_mouse_presses_do_not_toggle_done(self) -> None:
        self.assertIsNone(wily.watch_action_from_input("\x1b[<1;12;4M", summary_row=4, body_rows=1))
        self.assertIsNone(wily.watch_action_from_input("\x1b[<2;12;4M", summary_row=4, body_rows=1))

    def test_sgr_mouse_release_or_outside_body_is_ignored(self) -> None:
        self.assertIsNone(wily.watch_action_from_input("\x1b[<0;12;4m", summary_row=4, body_rows=1))
        self.assertIsNone(wily.watch_action_from_input("\x1b[<0;12;8M", summary_row=4, body_rows=2))

    def test_expanded_done_only_left_click_on_body_toggles(self) -> None:
        self.assertEqual(
            wily.watch_action_from_input("\x1b[<0;12;4M", summary_row=4, body_rows=2, expand_done=True),
            "toggle_done",
        )
        self.assertIsNone(
            wily.watch_action_from_input("\x1b[<0;12;22M", summary_row=4, body_rows=2, expand_done=True)
        )
        self.assertIsNone(
            wily.watch_action_from_input("\x1b[<2;12;4M", summary_row=4, body_rows=2, expand_done=True)
        )

    def test_mouse_wheel_returns_scroll_actions(self) -> None:
        self.assertEqual(wily.watch_action_from_input("\x1b[<64;12;4M", expand_done=True), "scroll_up")
        self.assertEqual(wily.watch_action_from_input("\x1b[<65;12;4M", expand_done=True), "scroll_down")
        self.assertIsNone(wily.watch_action_from_input("\x1b[<64;12;4M", expand_done=False))

    def test_parse_sgr_mouse_event_includes_button_code(self) -> None:
        self.assertEqual(wily.parse_watch_mouse_event("\x1b[<0;9;12M"), (0, 9, 12, True))
        self.assertEqual(wily.parse_watch_mouse_event("\x1b[<2;9;12M"), (2, 9, 12, True))
        self.assertEqual(wily.parse_watch_mouse_event("\x1b[<64;9;12M"), (64, 9, 12, True))
        self.assertEqual(wily.parse_watch_mouse_event("\x1b[<0;9;12m"), (0, 9, 12, False))
        self.assertIsNone(wily.parse_watch_mouse_event("not mouse"))
```

- [ ] **Step 2: Run the focused failing tests**

Run:

```bash
python3 -m unittest tests.test_wily_cli.WatchInputTest
```

Expected: failures showing `parse_watch_mouse_event()` still returns a 3-tuple and expanded mouse presses still toggle too broadly.

- [ ] **Step 3: Implement the mouse contract**

In `scripts/wily.py`, add constants near the existing watch constants:

```python
WATCH_MOUSE_LEFT = 0
WATCH_MOUSE_WHEEL_UP = 64
WATCH_MOUSE_WHEEL_DOWN = 65
```

Change `parse_watch_mouse_event()` to preserve the button code:

```python
def parse_watch_mouse_event(data: str) -> tuple[int, int, int, bool] | None:
    match = WATCH_MOUSE_RE.search(data)
    if not match:
        return None
    button, x, y, kind = match.groups()
    return int(button), int(x), int(y), kind == "M"
```

Change the mouse branch of `watch_action_from_input()` to:

```python
    mouse = parse_watch_mouse_event(data)
    if not mouse:
        return None
    button, _x, y, pressed = mouse
    if not pressed:
        return None
    if button == WATCH_MOUSE_WHEEL_UP:
        return "scroll_up" if expand_done else None
    if button == WATCH_MOUSE_WHEEL_DOWN:
        return "scroll_down" if expand_done else None
    if button != WATCH_MOUSE_LEFT:
        return None

    end_row = summary_row + max(0, body_rows)
    if summary_row <= y < end_row:
        return "toggle_done"
    return None
```

- [ ] **Step 4: Verify parser/action tests pass**

Run:

```bash
python3 -m unittest tests.test_wily_cli.WatchInputTest
```

Expected: `OK`.

## Task 2: Renderer Scroll Offset

**Files:**
- Modify: `scripts/wily_watch_ui.py`
- Test: `tests/test_wily_watch_ui.py`

- [ ] **Step 1: Write failing renderer tests**

Add these tests to the existing watch UI render test class in `tests/test_wily_watch_ui.py`:

```python
    def test_scroll_offset_clamps_to_body_length(self) -> None:
        self.assertEqual(wily_watch_ui.clamp_scroll_offset(0, total_rows=10, visible_rows=4), 0)
        self.assertEqual(wily_watch_ui.clamp_scroll_offset(3, total_rows=10, visible_rows=4), 3)
        self.assertEqual(wily_watch_ui.clamp_scroll_offset(99, total_rows=10, visible_rows=4), 6)
        self.assertEqual(wily_watch_ui.clamp_scroll_offset(-3, total_rows=10, visible_rows=4), 0)
        self.assertEqual(wily_watch_ui.clamp_scroll_offset(5, total_rows=3, visible_rows=4), 0)

    def test_render_expanded_done_stages_scrolls_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._make(Path(tmp), self.FAN_YAML)
            top = wily_watch_ui.render_watch(
                Path(tmp),
                interval=2.0,
                rich=False,
                size=(70, 8),
                expand_done=True,
                interactive=True,
                scroll_offset=0,
            )
            scrolled = wily_watch_ui.render_watch(
                Path(tmp),
                interval=2.0,
                rich=False,
                size=(70, 8),
                expand_done=True,
                interactive=True,
                scroll_offset=2,
            )
            self.assertIn("Settle Korean response-style update", top)
            self.assertNotIn("Settle Korean response-style update", scrolled)
            self.assertIn("Korean stage-based DAG status output", scrolled)
            self.assertIn("left-click/d collapse done", scrolled)
```

- [ ] **Step 2: Run failing renderer tests**

Run:

```bash
python3 -m unittest tests.test_wily_watch_ui
```

Expected: failures because `clamp_scroll_offset()` and `scroll_offset` do not exist yet.

- [ ] **Step 3: Add clamp helper and scroll slicing**

In `scripts/wily_watch_ui.py`, add a helper near `_body_lines()`:

```python
def clamp_scroll_offset(offset: int, *, total_rows: int, visible_rows: int) -> int:
    max_offset = max(0, total_rows - max(1, visible_rows))
    return min(max(0, offset), max_offset)
```

Update `_body_lines()` signature and apply scroll slicing after collapse logic is skipped for expanded done stages:

```python
def _body_lines(
    view: _RoadmapView,
    *,
    width: int,
    max_rows: int | None,
    ascii_: bool,
    expand_done: bool = False,
    scroll_offset: int = 0,
) -> list[Line]:
```

Before `return lines` at the end of `_body_lines()`, add:

```python
    if expand_done and max_rows is not None and len(lines) > max_rows:
        offset = clamp_scroll_offset(scroll_offset, total_rows=len(lines), visible_rows=max_rows)
        return lines[offset : offset + max_rows]
```

Update `render_watch()` to accept and pass the offset:

```python
def render_watch(
    root: Path,
    *,
    interval: float,
    rich: bool,
    size: tuple[int, int] | None = None,
    expand_done: bool = False,
    interactive: bool = False,
    scroll_offset: int = 0,
) -> str:
```

```python
    body = _body_lines(
        view,
        width=cols,
        max_rows=max_rows,
        ascii_=ascii_,
        expand_done=expand_done,
        scroll_offset=scroll_offset,
    )
```

- [ ] **Step 4: Update footer wording**

Change `_footer_line()` interactive wording in `scripts/wily_watch_ui.py`:

```python
    if interactive:
        toggle = "left-click/d collapse done" if expand_done else "left-click/d expand done"
        scroll = f"{sep}wheel scroll" if expand_done else ""
        text = f" {toggle}{scroll}{sep}r refresh{sep}q quit{sep}git: {_git_state(root, ascii_)}{sep}{root.name}"
```

Update existing footer expectations in `tests/test_wily_watch_ui.py` from `click/d ...` to `left-click/d ...`, and assert expanded footer includes `wheel scroll`.

- [ ] **Step 5: Verify renderer tests pass**

Run:

```bash
python3 -m unittest tests.test_wily_watch_ui
```

Expected: `OK`.

## Task 3: Interactive Loop Scroll State

**Files:**
- Modify: `scripts/wily.py`
- Modify: `scripts/wily_watch_ui.py`
- Test: `tests/test_wily_cli.py`

- [ ] **Step 1: Write focused state helper tests**

Add pure helper tests to `WatchInputTest` in `tests/test_wily_cli.py`:

```python
    def test_apply_watch_scroll_action_updates_offset(self) -> None:
        self.assertEqual(wily.apply_watch_scroll_action(0, "scroll_down", max_offset=3), 1)
        self.assertEqual(wily.apply_watch_scroll_action(3, "scroll_down", max_offset=3), 3)
        self.assertEqual(wily.apply_watch_scroll_action(2, "scroll_up", max_offset=3), 1)
        self.assertEqual(wily.apply_watch_scroll_action(0, "scroll_up", max_offset=3), 0)
        self.assertEqual(wily.apply_watch_scroll_action(2, "refresh", max_offset=3), 2)
```

- [ ] **Step 2: Run failing helper tests**

Run:

```bash
python3 -m unittest tests.test_wily_cli.WatchInputTest
```

Expected: failure because `apply_watch_scroll_action()` does not exist.

- [ ] **Step 3: Add body-count helper in renderer**

In `scripts/wily_watch_ui.py`, add a helper after `_body_lines()`:

```python
def rendered_body_row_count(
    root: Path,
    *,
    width: int,
    rich: bool,
    expand_done: bool,
) -> int:
    view = _load(root)
    return len(
        _body_lines(
            view,
            width=width,
            max_rows=None,
            ascii_=not rich,
            expand_done=expand_done,
        )
    )
```

- [ ] **Step 4: Add scroll state helper in CLI**

In `scripts/wily.py`, add:

```python
def apply_watch_scroll_action(current: int, action: str | None, *, max_offset: int) -> int:
    if action == "scroll_down":
        return min(max_offset, current + 1)
    if action == "scroll_up":
        return max(0, current - 1)
    return min(max(0, current), max_offset)
```

- [ ] **Step 5: Pass scroll offset through watch output**

Update `watch_output()` signature in `scripts/wily.py`:

```python
def watch_output(
    root: Path,
    interval: float = 2.0,
    ui: str = "auto",
    *,
    expand_done: bool = False,
    interactive: bool = False,
    show_rich_hint: bool = True,
    scroll_offset: int = 0,
) -> str:
```

Pass it into `wily_watch_ui.render_watch()`:

```python
        scroll_offset=scroll_offset,
```

- [ ] **Step 6: Maintain scroll offset in `watch_here_interactive()`**

In `watch_here_interactive()`, initialize `scroll_offset = 0` and compute body/visible rows before rendering:

```python
    scroll_offset = 0
```

Inside the loop, before `watch_output()`:

```python
            terminal_size = shutil.get_terminal_size((80, 24))
            use_rich = ui != "ascii" and rich_available()
            visible_body_rows = max(1, terminal_size.lines - wily_watch_ui.CHROME_ROWS)
            total_body_rows = wily_watch_ui.rendered_body_row_count(
                root,
                width=terminal_size.columns,
                rich=use_rich,
                expand_done=current_expand_done,
            )
            max_scroll_offset = max(0, total_body_rows - visible_body_rows) if current_expand_done else 0
            scroll_offset = apply_watch_scroll_action(scroll_offset, None, max_offset=max_scroll_offset)
```

Pass the offset to `watch_output()`:

```python
                scroll_offset=scroll_offset,
```

After action handling:

```python
            if action == "toggle_done":
                current_expand_done = not current_expand_done
                scroll_offset = 0
            if action in {"scroll_up", "scroll_down"}:
                scroll_offset = apply_watch_scroll_action(scroll_offset, action, max_offset=max_scroll_offset)
            if action in {"toggle_done", "refresh", "scroll_up", "scroll_down"}:
                continue
```

- [ ] **Step 7: Verify focused CLI tests pass**

Run:

```bash
python3 -m unittest tests.test_wily_cli.WatchInputTest
```

Expected: `OK`.

## Task 4: Documentation And Full Verification

**Files:**
- Modify: `skills/wily-watch/SKILL.md`
- Test: `tests/test_wily_command_skills.py`

- [ ] **Step 1: Update live skill guidance**

In `skills/wily-watch/SKILL.md`, replace the interactive behavior bullet with:

```markdown
- In an interactive TTY pane, left-click the collapsed done-stage summary or visible done-stage body row, or press `d`, to expand/collapse completed stages. When completed stages are expanded and the body is taller than the pane, use the mouse wheel to scroll. Press `r` to refresh immediately and `q` or Ctrl-C to quit.
```

- [ ] **Step 2: Update skill text test if needed**

If `tests/test_wily_command_skills.py` asserts the old wording, update the assertion to include:

```python
self.assertIn("left-click the collapsed done-stage summary", text)
self.assertIn("mouse wheel to scroll", text)
```

- [ ] **Step 3: Run focused verification**

Run:

```bash
python3 -m unittest tests.test_wily_cli tests.test_wily_watch_ui tests.test_wily_command_skills
python3 -m py_compile scripts/wily.py scripts/wily_watch_ui.py
```

Expected: all tests pass and both files compile.

- [ ] **Step 4: Manual smoke check**

Run in an interactive terminal:

```bash
./wily watch --here --ui ascii
```

Expected: left click toggles completed-stage folding; right/middle clicks do nothing; when expanded, mouse wheel scrolls the body.

## Self-Review

- Spec coverage: left-click-only toggle is covered by Task 1; wheel action handling is covered by Task 1 and Task 3; renderer scroll/clamp is covered by Task 2; docs and verification are covered by Task 4.
- Placeholder scan: no placeholder markers, generic "add tests", or undefined behavior remains.
- Type consistency: mouse events are consistently `(button, x, y, pressed)`; actions are string literals already used by `watch_here_interactive`; renderer offset is consistently named `scroll_offset`.
