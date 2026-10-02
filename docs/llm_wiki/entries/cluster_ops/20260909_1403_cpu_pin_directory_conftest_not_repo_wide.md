---
id: 20260909_1403_cpu_pin_directory_conftest_not_repo_wide
date: 2026-09-09
time: "14:03"
folder: cluster_ops
tags: [decision, learned_lesson, tradeoff, testing]
summary: "The CPU backend for tests/env is pinned by a directory conftest, not a repo-wide setting: a repo-wide pin would make test_gpu_buffer.py silently skip its 7 GPU tests with a false 'No CUDA device available', and a pytest marker cannot work at all because markers resolve after module import."
related: ["20260909_1402_parity_gates_green_without_comparing"]
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

# Pin the CPU backend per directory, never repo-wide — the repo-wide pin buys green by hiding GPU tests

## Key conclusion

`JAX_PLATFORMS` must be set before JAX first *initialises* a backend, not before it is
imported — which rules out both of the obvious fixes. A per-module
`os.environ.setdefault` is a no-op once any earlier-collected module has initialised one,
and a pytest marker is structurally too late because markers resolve after the module is
imported. A directory `conftest.py` is imported before any test module in that directory,
so it is the earliest hook that is still scoped. The repo-wide pin works but pays for it
in a way that is invisible in a green run, so it was rejected.

## Evidence, measurements, facts

- **Why not repo-wide.** `tests/algorithms/dreamer_srl/test_gpu_buffer.py` computes
  `_CUDA = _cuda_available()` at **import time** via `jax.devices("gpu")`, and gates 7 tests
  behind `@_requires_cuda`. Under a repo-wide CPU pin that call raises, `_CUDA` is False, and
  those 7 tests **skip** with the reason `"No CUDA device available"` — false on this
  two-RTX-4090 box, and indistinguishable from a pass in the summary line. The cost of the
  repo-wide pin is therefore lost coverage, not the "slows every GPU-capable test" that the
  handover note claimed.
- **Why not a marker.** Markers are resolved during collection, after the module object is
  built; by then the module's imports have already run and a backend may already exist.
  The handover listed marker-scoping as the *preferred* option; it cannot work.
- **Why a directory conftest is early enough.** pytest imports `tests/env/conftest.py`
  before any module in `tests/env/`, which is before any of them import JAX.
- **Scale of the underlying gap.** Only 9 of 35 modules in `tests/env/` pinned the backend
  (8 of the 9 arrived with the temperature work), and three fixture-consuming parity modules
  pinned it nowhere. There is no repo-level `conftest.py`, and `pyproject.toml`'s
  `[tool.pytest.ini_options]` sets only `markers`.
- **Verified both directions.** `pytest tests/env/test_unified_parity.py` (previously
  unpinned) → **34 passed / 323 skipped / 0 failed**. Forcing `JAX_PLATFORMS=cuda` → the
  conftest raises once at collection with a message naming the cause and the fix, replacing
  what was **146 failed / 359 passed / 905 skipped** of opaque float mismatches.
- **Machine context.** A full CPU sweep aborted twice inside XLA `backend_compile_and_load`
  under load (`Fatal Python error: Aborted`) — a compiler crash, not a test failure. Load
  was 12–15 throughout, from sensor-ladder training runs still alive from 2026-08-27. Run
  one file at a time on a loaded box.

## Decisions and actions

- Added `tests/env/conftest.py` (commit `bd22429d`): sets the pin, then asserts
  `jax.default_backend() == "cpu"` and raises with the cause and the fix if not. The
  assertion is the more valuable half — it converts a mass of unexplained failures into one
  legible error.
- Established the two-invocation convention for a full green run, rather than a repo-wide pin:
  `JAX_PLATFORMS=cpu pytest tests/env/` and `pytest tests/ --ignore=tests/env`.
- Recorded both rejected alternatives, with reasons, in the Known Bugs registry row so the
  decision is not silently re-litigated.

## Open questions and follow-ups

- The conftest fixes the *effect* (wrong backend in `tests/env/`) rather than the *cause*
  (26 of 35 modules never pinned). If a fixture-backed byte-identity test is ever added
  outside `tests/env/`, it inherits the original gap and nothing will catch it.

## References

- `tests/env/conftest.py` — carries the full rationale in its module docstring.
- Registry: `docs/develop/active/issues/KNOWN_BUGS.md`, Fixed cluster "test-gate hygiene" (2026-09-09).
- Commits: `bd22429d` (conftest), `73a19a31` (registry row closed).
- Related: [[20260909_1402_parity_gates_green_without_comparing]] — the sibling gate defect
  the same session fixed.
- Raw conversation: synced via `./sync-agent-data.sh claude push`. To read on another node:
  `./sync-agent-data.sh claude pull`, then either `claude --resume 75d00862-fedd-4393-8200-a49d666c3a30`
  or `python scripts/claude/claude_jsonl_to_md.py <jsonl> /tmp/<id>.md`.

<!-- BACKLINKS — auto-generated by scripts/regen_wiki_graph.py; do not edit -->
## Backlinks
- [[20260909_1402_parity_gates_green_without_comparing]] (env_entities, 2026-09-09) — Two of the environment's byte-identity gates were reporting success without comp
- [[20260909_1404_verify_handover_claims_against_code]] (subagent_engineering, 2026-09-09) — A handover note written by the session that did the work was wrong about the cod
<!-- END BACKLINKS -->
