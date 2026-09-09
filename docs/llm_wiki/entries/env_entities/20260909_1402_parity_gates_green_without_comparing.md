---
id: 20260909_1402_parity_gates_green_without_comparing
date: 2026-09-09
time: "14:02"
folder: env_entities
tags: [meta, learned_lesson, testing, config]
summary: "Two of the environment's byte-identity gates were reporting success without comparing anything — one skipped for three months after its config moved, the other compared GPU floats against CPU-captured fixtures — and a replay proved no regression slipped through either."
related: ["20260909_1403_cpu_pin_directory_conftest_not_repo_wide", "20260909_1404_verify_handover_claims_against_code"]
session_origin: claude_code
session_label: "thermal handover follow-up (v4.0)"
importance: high
status: settled
valid_until: null
confidence: high
supersedes: []
raw_source: claude_data/.claude/projects/-media-nas01-projects-Interoceptive-AI-grid-world-pain/75d00862-fedd-4393-8200-a49d666c3a30.jsonl
raw_completeness: full
---

# Two env byte-parity gates reported green while comparing nothing

## Key conclusion

A skipped test is indistinguishable from a passing one in pytest's summary line, and
two of the environment's byte-identity gates exploited that for months without anyone
noticing. Neither had let a real regression through — verified, not assumed — so both
were test hygiene rather than investigations. The transferable lesson is that a parity
gate needs to fail loudly on *its own* preconditions (missing config, missing fixture,
wrong backend), because every one of those conditions otherwise renders it silently inert.

## Evidence, measurements, facts

- **Gate 1 — `tests/env/test_extero_noc_parity.py`, dark for three months.** It pinned its
  reference config at `configs/experiment/hypervigilance/01-interoNocicept_sameProp.yaml`;
  commit `4e975fb8` (2026-06-17) moved that file under
  `configs/environment/experiment/archive/hypervigilance/` and nothing repointed it. The
  `params` fixture called `pytest.skip()` on a missing config, so the module reported
  **3 skipped, 0 run** and read as green.
- **Same file, second and sharper defect: it re-baselined itself.** The fixture loader was
  `if gen or not os.path.exists(FIXTURE_PATH): _generate_fixture(...)`, so a *missing*
  reference was silently recaptured from today's code on today's backend and then compared
  against itself. That always passes. `tests/env/test_visual_parity.py:162` carries the
  same branch but calls `pytest.fail` on a missing config — the pattern the extero module needed.
- **No regression had slipped through — measured, not reasoned.** Replaying the gate's own
  1000-step episode on CPU against the committed pre-move fixture
  (`tests/env/fixtures/extero_noc_parity_ref.npz`) is **byte-identical**, and
  `params.animal_is_damaging` is exactly `[True, False, False]` — one damaging predator,
  two neutral rabbits — so the B2 property the gate protects held throughout.
- **It was blind across a real edit to its own subject.** Commit `90d687fe` (2026-06-22,
  five days after the config moved) added `& state.animal_active` to the damaging mask in
  `sense_extero_nociception`. That edit is behaviour-preserving when all animals are active,
  which is why parity holds — but nobody could have known that at the time, and `90d687fe`'s
  own commit message reports "34 passed / 133 skipped" with this gate among the skips.
- **Gate 2 — the whole `tests/env/` directory, wrong backend.** Every byte-identity fixture
  in the repo was captured on CPU, but only **9 of 35** modules pinned the backend, and three
  fixture-consuming parity modules pinned it nowhere (`test_unified_parity.py`,
  `test_visual_parity.py`, `test_extero_noc_parity.py`) — so on a GPU box they compared GPU
  floats against CPU fixtures **even when run alone**. A whole-directory run measured
  **146 failed / 359 passed / 905 skipped**, with nothing naming the backend as the cause.
- **Nothing in the suite asserted the backend.** The one assertion carrying that message
  (`parity fixture must run on CPU, got 'gpu'`) lives in
  `scripts/verification/capture_sensor_baseline.py:20`, not in any test.

## Decisions and actions

- Repointed `_PARITY_CFG`; a missing config now calls `pytest.fail`, not `pytest.skip`,
  because the skip is precisely how this went dark. A missing fixture now fails too;
  `--gen-fixtures` still re-baselines deliberately. Commit `c4f53ca8`. Now 3 passed.
- Added `tests/env/conftest.py` to pin and assert the CPU backend — see
  [[20260909_1403_cpu_pin_directory_conftest_not_repo_wide]] for why that shape and not another.
- Both rows filed and then closed in the Known Bugs registry (`82d2c12b`, `73a19a31`),
  with the verified-clean replay recorded so nobody re-opens the three dark months later.

## Open questions and follow-ups

- The self-rebaselining branch (`if not exists: regenerate`) was only fixed in the extero
  module. Whether any other fixture-backed test in the repo carries the same shape has not
  been swept — `test_visual_parity.py` was checked and is safe.
- Five sibling rows from the same filing remain open; `scripts/analysis/ladder/lad03_how_it_ends.py`
  (hardcoded three termination outcomes, no share-sum guard) is the one most likely to bite
  a real analysis first.

## References

- Registry rows: `docs/develop/active/issues/KNOWN_BUGS.md`, Fixed cluster
  "test-gate hygiene: two parity gates were reporting green without running (2026-09-09)".
- Entry point for the wider handover: `docs/develop/active/thermal/HANDOVER.md`.
- Commits: `c4f53ca8` (gate fix), `bd22429d` (backend pin), `82d2c12b` / `73a19a31` (registry).
- Related: [[20260909_1403_cpu_pin_directory_conftest_not_repo_wide]] ·
  [[20260909_1404_verify_handover_claims_against_code]]
- Raw conversation: synced via `./sync-agent-data.sh claude push`. To read on another node:
  `./sync-agent-data.sh claude pull`, then either `claude --resume 75d00862-fedd-4393-8200-a49d666c3a30`
  or `python scripts/claude/claude_jsonl_to_md.py <jsonl> /tmp/<id>.md`.

<!-- BACKLINKS — auto-generated by scripts/regen_wiki_graph.py; do not edit -->
## Backlinks
- [[20260909_1403_cpu_pin_directory_conftest_not_repo_wide]] (cluster_ops, 2026-09-09) — The CPU backend for tests/env is pinned by a directory conftest, not a repo-wide
- [[20260909_1404_verify_handover_claims_against_code]] (subagent_engineering, 2026-09-09) — A handover note written by the session that did the work was wrong about the cod
<!-- END BACKLINKS -->
