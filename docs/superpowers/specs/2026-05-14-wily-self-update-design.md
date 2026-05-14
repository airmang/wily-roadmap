# Wily Self-Update Design

**Date:** 2026-05-14

**Status:** approved for implementation planning

**Goal:** Let users who first received Wily as a zip install upgrade to a managed install that can update itself from the canonical GitHub repository.

---

## Decision

Wily should support an explicit self-update command:

```text
./wily update
$wily-update
```

The update path is GitHub-backed and approval-first. Wily does not update in the background and does not contact remotes unless the user invokes the update command.

The current zip distribution remains useful as a bootstrap package. A new zip can be shared once, and that package should include the update command so future upgrades can happen through GitHub instead of repeated manual zip delivery.

Canonical source:

```text
https://github.com/airmang/wily-roadmap
```

Canonical local version:

```text
.codex-plugin/plugin.json -> version
```

Keep `.claude-plugin/plugin.json` in sync when it exists.

---

## User Experience

For a git-managed install, `./wily update` should:

1. Read the current version from `.codex-plugin/plugin.json`.
2. Confirm the plugin root is a git repository.
3. Confirm the repository remote points to the expected Wily repository, or clearly report the detected remote.
4. Fetch remote metadata.
5. Compare the local `HEAD` and remote default branch.
6. Print current version, local commit, remote commit, and a compact summary of pending commits when available.
7. Ask for explicit approval before changing files.
8. Run a fast-forward-only update.
9. Print the new version and next verification suggestion.

For a zip install without `.git`, `./wily update` should not try to patch files in place. It should explain that the install is zip-based and offer a managed-install migration path:

```text
./wily update --migrate
```

The migration path should clone the canonical repository into a sibling managed directory, then tell the user which directory to use or copy into their Codex plugin cache. It must not delete or overwrite the existing zip directory automatically.

---

## Command Surface

Add a Wily command skill:

```text
skills/wily-update/SKILL.md
commands/wily-update.md
```

Add CLI support:

```text
python3 <plugin-root>/scripts/wily.py update
python3 <plugin-root>/scripts/wily.py update --check
python3 <plugin-root>/scripts/wily.py update --migrate
python3 <plugin-root>/scripts/wily.py update --yes
```

`--check` is read-only and prints whether an update appears available.

`--migrate` is for zip installs and creates a managed clone without deleting the current install.

`--yes` skips the interactive confirmation only after the user explicitly includes the flag.

The repo-local launcher should route `./wily update` to the same script command.

---

## Safety Policy

The update command must stay local-first and approval-first:

- No background checks.
- No automatic updates during unrelated Wily commands.
- No destructive cleanup of zip installs.
- No non-fast-forward pulls.
- No merge commits.
- No writes outside the managed install except the explicitly requested migration target.
- No global shell, PATH, hook, app, or MCP integration changes.

If the working tree has local changes, the command should refuse to update by default and explain that the user should commit, stash, or use a fresh managed clone. This protects local edits inside a shared plugin checkout.

If the remote cannot be reached, the command should fail with a clear network-oriented message and leave files untouched.

---

## Versioning

The implementation should treat `.codex-plugin/plugin.json` as the source of truth for plugin version display.

When releasing a Wily update:

- bump `.codex-plugin/plugin.json`
- bump `.claude-plugin/plugin.json` when present
- commit the change
- push to the canonical repository
- optionally create a zip bootstrap package for first-time users

Git tags are useful but not required for the first version of self-update. The first implementation can compare commits and display manifest versions. Tags can be added later if release automation needs stricter version ordering.

---

## Error Handling

Expected states:

- **Already current:** print current version and commit, exit cleanly.
- **Update available:** show pending commit summary and require approval unless `--yes` is present.
- **Zip install:** explain migration and exit without changing files unless `--migrate` is present.
- **Dirty tree:** refuse to update and list changed paths compactly.
- **Unexpected remote:** warn and require explicit confirmation before using it.
- **Fetch/pull failure:** preserve current files and print the failed command context.

---

## Testing

Add focused tests around deterministic command behavior:

- manifest exposes `$wily-update`
- `wily.py update --check` detects non-git zip installs without changing files
- dirty git working tree refuses update
- already-current git checkout reports cleanly
- migration command builds the expected clone command without deleting the source install

Tests should avoid real network access by injecting command runners or using local bare repositories.

---

## Documentation

Update README with two installation paths:

1. Zip bootstrap install for first-time sharing.
2. Managed GitHub install for ongoing updates.

Document the normal update command:

```bash
./wily update
```

Also document that users who already received a zip should install the new bootstrap zip once, then use the update command afterward.
