# Batch Migrate Wily V2 Verification

Evidence will be appended during the migration loop.

Explicitly forbidden command:

- `--prune-legacy` is not to be run.

## Summary

Full command evidence:

- `agent-handoffs/batch-migrate-wily-v2-run.log`
- `agent-handoffs/batch-migrate-wily-v2-summary.tsv`
- `agent-handoffs/batch-migrate-wily-v2-corrected-candidates.tsv`

Correction:

- The original run treated every `.wily/roadmap.yaml` path as a candidate, including nested test fixtures.
- S27 remediation corrects the discovery contract: `*/tests/fixtures/**`, `*/fixtures/**`, dependency/cache directories, and test data are excluded from "all local repo" candidates.
- The historical fixture rows below remain recorded as evidence of the bug, but they are invalidated as batch-migration repo candidates.
- S27 remediation restored the mutated fixture source directories after this bug was found, so `mixed-legacy` and `v1-only` remain valid migration test inputs.

Recorded migration results:

| Candidate | Result | Verification |
| --- | --- | --- |
| `/Users/wilycastle/Code/projects/DIVE-2` | migrated | dry-run/apply/status/next/diff-check all exit 0 |
| `/Users/wilycastle/Code/projects/Digit` | migrated | dry-run/apply/status/next/diff-check all exit 0 |
| `/Users/wilycastle/Code/projects/hwpx` | skipped | `git status --short` exit 128: not a git repository |
| `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap` | migrated | dry-run/apply/status/next/diff-check all exit 0 |
| `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/fixtures/migration/already-v2` | already v2 | dry-run/status/next/diff-check exit 0; apply skipped because schema was already v2 |
| `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/fixtures/migration/mixed-legacy` | migrated | dry-run/apply/status/next/diff-check all exit 0 |
| `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/fixtures/migration/v1-only` | migrated | dry-run/apply/status/next/diff-check all exit 0 |

Corrected candidate set:

| Candidate | Result | Verification |
| --- | --- | --- |
| `/Users/wilycastle/Code/projects/DIVE-2` | migrated | original dry-run/apply/status/next/diff-check all exit 0 |
| `/Users/wilycastle/Code/projects/Digit` | migrated | original dry-run/apply/status/next/diff-check all exit 0 |
| `/Users/wilycastle/Code/projects/hwpx` | skipped | original `git status --short` exit 128; not usable as a git repository for required procedure |
| `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap` | migrated | original dry-run/apply/status/next/diff-check all exit 0 |

Invalidated fixture candidates:

- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/fixtures/migration/already-v2`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/fixtures/migration/mixed-legacy`
- `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap/plugins/wily-roadmap/tests/fixtures/migration/v1-only`

Corrected discovery command evidence:

- `find /Users/wilycastle/Code/projects -path '*/.wily/roadmap.yaml' -print | sort` found 7 raw paths.
- After excluding `*/tests/fixtures/**`, the corrected non-fixture set is 4 candidates: DIVE-2, Digit, hwpx, and wily-roadmap.

Fresh final checks:

- `git diff --check` in `/Users/wilycastle/Code/projects/DIVE-2`: exit 0.
- `git diff --check` in `/Users/wilycastle/Code/projects/Digit`: exit 0.
- `git diff --check` in `/Users/wilycastle/Code/projects/wily-plugin/wily-roadmap`: exit 0.
- Fixture integrity check: Roadmap full unittest suite passed after fixture restoration, including migration CLI coverage.
- Schema check: all migrated/already-v2 candidates declare `roadmap_schema: wily-roadmap-v2`.
- Run log check: no `--prune-legacy` invocation found.
