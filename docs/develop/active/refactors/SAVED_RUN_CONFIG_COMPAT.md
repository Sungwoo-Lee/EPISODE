---
title: "Re-loading archived runs: a read-only compatibility layer for saved run configs"
topic: refactors
status: active
created: 2026-09-09
last_updated: 2026-09-09
---

# Re-loading archived runs: a read-only compatibility layer for saved run configs

> **Status**: PLANNED
> **Opened**: 2026-09-09
> **Related**: [[KNOWN_BUGS]] (row "Mandatory config keys keep landing without migrating the archive", row "A run's saved config file carries a stale second copy of the seed and episode budget") · [[IMPLEMENTATION_PLAN]] (thermal) finding F9 · `src/models/modulation_compat.py` and `tests/models/test_modulation_compat.py` (the presence-shaped precedent) · `scripts/eval/traj_collect/collect_trajectories.py` `apply_sensor_compat` (the absence-shaped precedent)

---

## Context

Every training run writes a frozen copy of its own settings next to its checkpoints, and every offline analysis tool rebuilds the simulated world from **that frozen copy** rather than from the maintained settings files — which is correct, because the frozen copy is what the run actually trained with. The problem is that the world-builder refuses to run unless certain settings are spelled out explicitly, and the list of settings it demands has grown over time. A run finished in July cannot know about a switch invented in September, so its frozen copy does not mention it, and the world-builder stops with an error instead of rebuilding the run's world. No analysis of that run is possible.

The immediate trigger was the body-temperature ("thermal") system, whose on/off switch became a required setting on 2026-09-09. That switch blocks the 32-run grid comparing where a neuromodulatory signal is injected into the network (16 runs using Monte-Carlo returns, 16 using normalised advantage estimates, all trained 2026-09-07) — the substrate for the representational analyses already published under `results/analysis/nmn_representation/`, and for more analyses expected on the same runs.

**The headline finding of this investigation is that the body-temperature switch is not the problem; it is the fifth instance of the problem.** Measured, not estimated: of the 477 frozen run-configs currently on disk, **only 17 can be rebuilt at the current code**. Four earlier required settings — three about vision, one about smell — already block hundreds of runs, and they have been blocking them silently since August, because nobody tried to re-analyse those runs. A fix that only teaches the tools about the temperature switch would restore 120 runs and leave 340 broken, and the sixth key would be discovered exactly the same way: by someone hitting it.

This plan therefore proposes **one small read-only compatibility layer**, applied only where a *frozen run copy* is read and never where a *maintained settings file* is read, that supplies each historically-added setting at the value which reproduces the behaviour the run actually had. It keeps the strict "no silent defaults" guarantee fully intact on the live path — that guarantee is what makes a typo in a settings file fail loudly instead of training the wrong experiment — and it pins that asymmetry with a named test, exactly as the existing neuromodulation compatibility shim does. It also proposes the piece that stops the next recurrence: a handful of tiny era-representative frozen configs committed as test fixtures, so the day someone makes a sixth setting mandatory, the test suite goes red instead of an analysis six weeks later.

---

## Analysis

### A1 — The reproducer

```
python -c "
import yaml
from src.utils.config import Config
from src.environment.config_loader import load_env_params
p='results/JAX_RecurrentPPO/20260907-045531_rppo_nmnsite_t1none_s42/models/config.yaml'
load_env_params(Config(yaml.safe_load(open(p))))"
```

```
ValueError: Strict Config: Configuration key 'thermal.enabled' is required but missing.
  src/environment/config_loader.py:1476  _thermal_on = bool(config.get_mandatory('thermal.enabled'))
  src/utils/config.py:74
```

### A2 — The measured blast radius (this is the finding that changes the plan)

A cascading sweep over every `results/*/*/models/config.yaml` (477 files): try `load_env_params`; on a *missing mandatory key* error, inject that key's value from `configs/environment/default.yaml`; retry; record the chain. Working file: `tmp/20260909_saved_cfg_cascade.txt`.

| Frozen configs | Chain of missing mandatory keys, in the order the loader hits them | Era |
|---:|---|---|
| 17 | *(none — rebuilds cleanly at HEAD)* | 2026-09-09 onward |
| 120 | `thermal.enabled` | 2026-08-26 → 2026-09-07 (includes all 32 target runs) |
| 6 | `sensory.visual_value_mode` → `sensory.visual_occlusion_enabled` → `thermal.enabled` | 2026-08-26, same day, pre-merge |
| 184 | `sensory.visual_value_mode` → `sensory.olfactory_grid_range` → `sensory.visual_blur_enabled` → `sensory.visual_occlusion_enabled` → `thermal.enabled` | 2026-05-28 → 2026-08-16 |
| 150 | the same five keys, **then** a non-missing-key error | 2026-04-20 → 2026-05-21 |

Per-key totals — the number of frozen run-configs each key alone is enough to block:

| Key | Blocks | Made mandatory by | Date |
|---|---:|---|---|
| `thermal.enabled` | 460 | `dd3b5dfa` (thermal Stage 1) | 2026-09-09 |
| `sensory.visual_value_mode` | 340 | `9771e98c` (visual value mode + occlusion) | 2026-08-26 |
| `sensory.visual_occlusion_enabled` | 340 | `9771e98c` | 2026-08-26 |
| `sensory.olfactory_grid_range` | 334 | `0949ddb2` rename + `4a5fcd44` validation | 2026-08-26 |
| `sensory.visual_blur_enabled` | 334 | `0e8a4ef8` (directional olfaction + point spread) | 2026-08-21 |

The 150-run tail fails on something structurally different and **out of scope for this plan**: 130 raise on `environment.predator_enabled` (a key *removed* in v2.0, guarded at `config_loader.py:1738`) and 20 on `Resource: missing required key 'properties_std'` (a schema *rename*, `config_loader.py:711`). Supplying a missing key cannot fix a removed key or a renamed schema; those need a translation, which is `modulation_compat`'s shape, and they should be their own plan if anyone ever needs those April/May runs.

A sixth key, `sensory.injury_observable` (mandatory since `980fa09b`, 2026-04-30, read at `config_loader.py:2072`), is absent from 40 frozen configs — but all 40 are inside that 150-run tail and fail earlier on `predator_enabled` / `properties_std`, so supplying it changes nothing. Deliberately excluded; recorded here so a later reader does not think it was missed.

**Recovery arithmetic.** Supplying the five keys takes the archive from **17 / 477 rebuildable (3.6 %)** to **327 / 477 (69 %)**, and covers **32 / 32** of the runs that prompted this plan.

### A3 — Is this the same shape as `modulation_compat`? No, and the difference is the whole design

`src/models/modulation_compat.py` fires on a **positive signature**: the archived config *contains* the obsolete flat `temp_clip` key, which is a fact no current config can produce, so the shim can translate it with no risk of touching anything else. Its own docstring draws the boundary this plan must not cross:

> "It is also not a general defaulting layer: it fires only on the specific legacy shape (flat `temp_clip` present), and a saved config that is merely missing a mandatory key still fails loudly."

A missing `thermal.enabled` **is** "merely missing a mandatory key". So the honest answer to "follow the established pattern" is: yes, follow an established pattern — but the *other* one. The project already has a second, absence-shaped precedent, in `scripts/eval/traj_collect/collect_trajectories.py:333` (`apply_sensor_compat` + `PRE_V31_SENSOR_DEFAULTS` / `PRE_V32_SENSOR_DEFAULTS`), which solves precisely this problem for the four sensory keys. Its three properties are the ones this plan generalises:

1. Values chosen to reproduce the *pre-feature* behaviour, each justified against a specific trace-time branch in `sensor.py` — not "sensible defaults".
2. **Verified, not asserted**: replaying 25 real episodes (5,298 steps) through today's code against observations the old code wrote gave a max difference of 2.4e-07 across all 27 channels (`scripts/analysis/supplementary/parity.py`).
3. A refusal guard: if the config already sets any key the shim would supply, it raises rather than overwriting.

Its weakness is that it lives inside one script. `eval_rollout.py`, `scripts/analysis/nmn/replay.py` and `scripts/analysis/trajectory_glm.py` have no access to it, which is why those tools cannot replay a pre-2026-08-26 run **at all** today.

### A4 — Every call site that reads a frozen run config (found, not guessed)

Enumerated from `grep -rn "load_env_params\|config.yaml" --include=*.py src scripts`. Two groups.

**Group 1 — rebuild the world from a frozen config (broken today; the shim's insertion points):**

| # | Site | Line | How the frozen config gets in |
|---|---|---|---|
| 1 | `scripts/eval/eval_rollout.py` | `959` (`load_env_config`), `1007` (`load_env_params`) | `--config` commonly points at `<run>/models/config.yaml`; `_resolve_continual_stage_config` (line 677) may redirect to a per-stage copy under the same checkpoint root. **May also be a live file** — needs the same live/saved discrimination the modulation shim does at line 1063 (`agent_config_source`). |
| 2 | `scripts/eval/traj_collect/collect_trajectories.py` | `699` (read), `727` (`load_env_params`) | Always `<run>/models/config.yaml`; refuses anything else. Already has the opt-in sensory shim at `713`–`723`. |
| 3 | `scripts/analysis/nmn/replay.py` | `82`–`84` | `<models_dir>/config.yaml`. Always saved. **This is the site the 32 target runs' analyses go through.** |
| 4 | `scripts/analysis/trajectory_glm.py` | `54` | `f"{run}/models/config.yaml"`. Always saved. |
| 5 | `scripts/analysis/supplementary/parity.py` | `26`, `31` | `RUN + '/models/config.yaml'`. Always saved. |

**Group 2 — read a frozen config as a plain dictionary, never build the world (unaffected; listed so the developer does not touch them):** `scripts/analysis/nmn/ckpt_io.py:129` (`run_config`), `scripts/analysis/hiding_drivers.py:346`, `scripts/analysis/context_dependence.py:475`, `scripts/analysis/figures/_common.py:136`, `scripts/analysis/ladder/_ladder.py:144`, `scripts/analysis/supplementary/{prox_full,allarms_glm,armpain,modeleffect}.py`, `src/utils/trajectory_store.py:824` (error text only).

`src/utils/evaluation_core.py` does **not** call `load_env_params`; it receives already-built params. Not a site.

### A5 — What a pre-thermal run's rebuilt world should be, verified rather than repeated

The claim under test: `thermal.enabled: false` is sufficient, and nothing else in the temperature block is read when the gate is off.

**Verified at load time.** `config_loader.py:1476` reads the gate; `1477`–`1591` is the `if _thermal_on:` arm where all ~20 sub-keys are read via `get_mandatory`; `1592`–`1629` is the `else:` arm, which assigns every one of them an inert literal and calls `get_mandatory` zero times. The load-time structural check `_check_thermal_structure` (defined `530`, called `2019`) sits inside `if _thermal_on:`. The only thermal-adjacent code that runs unconditionally is `_read_temperature` (`336`), which reads per-entity heat declarations with a plain `entry.get('temperature', 0.0)` — a genuine "this entity is not a heat source" default, not a `get_mandatory` — and returns `(0.0, 0.0, 0.0)` for every entity in a pre-thermal config.

**Verified at run time.** Every consumer is behind a *static* Python branch on `params.thermal_enabled`, so a thermal-off config traces the identical computation graph — and therefore draws the identical random numbers — that pre-thermal code did: `core.py:77` (homeostatic drive), `247`, `854`, `913`, `1773`; `sensor.py:485` (thermoception channel) and `541` (observation width); `state.py:95`. `config_loader.py:1596`–`1600` explains why the two placement constraints must be `0` in the off-arm for exactly this reason. Both renderers reach for the field through `getattr(params, 'thermal_enabled', False)` (`renderer.py:630`, `renderer_v2.py:307`), so drawing an old recording is already handled.

**Verified empirically, and this already exists.** `tests/env/test_thermal_parity.py` replays a fixed 100-step episode from seed 0 for 34 fixtured configs against pre-thermal reference captures and requires exact equality on reward, both drives, `state.key`, termination reason, entity positions and every observation slice but one (a documented ≤1-ulp exemption on sampled properties, with a derived Olfaction tolerance). That test **is** the instrument for "thermal-off equals pre-thermal", it is committed, and it is green. This plan does not need to build a new one; it needs to cite this one and add a per-key equivalence test (§Checkpoint 4).

**Confirmed measurement:** injecting only `thermal.enabled: false` into all 16 `nmnsite` frozen configs and all 16 `nmngaenorm` frozen configs makes `load_env_params` succeed on 32 / 32.

### A6 — Is the substitution ambiguous? Measured: no, on this population

The reason `apply_sensor_compat` is opt-in is the fear of reinterpreting a run that genuinely used the feature. On frozen run-configs that fear is checkable, and it was checked:

- A frozen config is written by the trainer **after** `load_env_params` has already succeeded. At any commit where a key is mandatory, a run that reached checkpoint-save time necessarily had the key. So on this population, absence of a key means "trained before the key existed" — it cannot mean "the author forgot it", which is what the mandatory-key rule protects against on the live path.
- Measured: `thermal:` block present in 33 frozen configs, absent in 460. No frozen config has a `thermal:` block without `enabled`.
- The one real hazard was the rename `olfactory_sensor_range` → `olfactory_grid_range` (`0949ddb2`): a config carrying the *old* spelling with a real non-zero value would be silently reinterpreted as `0`. Measured across all 477 frozen configs: **zero** carry the old spelling. Hazard empirically absent — but the plan still adds a guard for it (§Checkpoint 3) rather than relying on the measurement staying true.

### A7 — Option B (pinned-commit analysis policy): assessed, not workable

*Policy:* analyse pre-thermal runs at the commit they were trained at; no shim, no code change.

Honest assessment — three failures, the third decisive:

1. **Back-porting is per-script and permanent.** `scripts/analysis/nmn/` is nine modules at HEAD and growing; every new analysis would have to be authored against, or copied back to, a September-7 tree. The standing project rule is the opposite ("build eval/analysis tooling run-agnostic — analysis questions arrive after development").
2. **The mechanics are hazardous here.** A pinned checkout rewrites `src/`, `configs/` and `scripts/` under any live training run reading them (CLAUDE.md git-safety rule). Doing it properly means a `git worktree` per era plus discipline about which tree an analyst is in — and `results/` is a NAS path shared across trees, so a mis-targeted write lands in the same archive.
3. **It cannot express a cross-era comparison, and it fails silently when it tries.** The archive spans five eras. There is no commit at which a pre-2026-08-21 run and a post-2026-09-09 run both rebuild. Worse than the error: at a pre-v3.2 commit, a *later* run's frozen config still loads, because the loader ignores keys it does not ask for — so a run that actually trained with `visual_value_mode: clamp` and line-of-sight occlusion is replayed by code that has neither, and produces plausible, wrong observations with no error. A policy whose failure mode is silent wrong numbers is worse than the current loud one.

**Verdict: reject as a policy.** Keep it as the documented escape hatch for the 150 pre-v2.0 runs, where no shim exists and the alternative is nothing.

### A8 — Option C (back-fill the frozen configs on disk): assessed, reject

*Policy:* write the missing keys into the 460 files under `results/`.

1. **Irreversible on unbacked data.** `results/` is gitignored, has no history, and was destroyed once in this project (recovery required re-training). A 460-file in-place rewrite has no undo and no diff to review.
2. **It rewrites the provenance record of a finished run.** The frozen config is the evidence of what the run trained with. Editing it makes the archive assert that a July run declared a September setting — the "verify actual state, not a re-derivation" rule points the other way.
3. **It silently invalidates provenance already recorded elsewhere.** `collect_trajectories.py:391` stores `train_config_mtime` and `build_manifest` stores `env_fp = env_fingerprint(cfg)` into every trajectory store's manifest as guarded fields. Touching the files changes the mtime and, for any key the fingerprint covers, the fingerprint — retroactively breaking stores that were correct.
4. **It walks into an open design question.** A recorded bug (2026-09-04) notes every frozen config carries a *duplicate stale* `training.seed` / `training.episodes` block permanently reading 42 / 100, and that pair still needs a wire-or-remove decision. Any tool that rewrites these files has to decide what to do with it. Scope grows from "add one key" to "own the file format".
5. **It is the same treadmill with write side-effects.** The sixth mandatory key requires re-running it over an archive that keeps growing.
6. **It does not even finish the job** — the 150 pre-v2.0 runs stay broken.

A softer variant — write a *sidecar* `models/config_compat.yaml` rather than editing the original — avoids (1)–(3) but is strictly worse than Option A: it is Option A with a disk cache that can go stale against the compat table. **Reject.**

### A9 — Relationship to the recorded bug

`KNOWN_BUGS.md` already carries "Mandatory config keys keep landing without migrating the archive", re-measured 2026-09-09: 68 of 141 stand-alone **authored** configs under `configs/` fail to load, and the standing user decision there is **lazy migration** — fix one when a run next needs it. Two things follow, and the developer must not blur them:

- That row's population is `configs/` (files a human wrote and can edit). **This plan's population is `results/` (files a finished run wrote and nobody should edit).** Same root cause, different object, opposite correct remedy: you migrate an authored config, you shim a frozen one.
- **This plan does not touch `configs/` and does not perform any bulk migration.** The lazy-migration decision stands untouched.

---

## Implementation Plan

### Design

One new module, `src/environment/saved_config_compat.py`, holding a single table and a single function. Placed in `src/environment/` rather than `scripts/` because five call sites across three directories need it, and because it belongs next to the loader whose contract it complements.

```
        LIVE PATH (unchanged, still hard-errors)
        configs/**.yaml ──► load_env_config ──► load_env_params ──► ValueError on any missing mandatory key

        SAVED PATH (new)
        results/<algo>/<run>/models/config.yaml
                │
                ├─ apply_saved_config_compat(cfg, source=<path>)   # in memory; nothing written to disk
                │     • refuses if source resolves under configs/           (structural live-path guard)
                │     • refuses if a key it would supply is already present (already a later-era run)
                │     • refuses if a parent block is present without its gate key (the typo case)
                │     • prints one INFO line naming every key supplied
                │
                └─► load_env_params ──► EnvParams
```

Four decisions and why:

- **Absence-shaped, not presence-shaped.** Generalises `apply_sensor_compat` (§A3), not `modulation_compat`. `modulation_compat` stays exactly as it is — it solves a different problem (a *translated* key) at the same boundary, and the two compose.
- **Automatic at the saved boundary, not behind a per-tool flag.** This is the one place the plan departs from `apply_sensor_compat`, and it is the decision most worth arguing about. An opt-in flag that must be passed for 96 % of the archive is not a safety mechanism; it becomes reflex, and a reflexive flag looks deliberate in a command log while carrying no thought. The ambiguity that justified opt-in (§A6) is measured to be absent on this population, and the three refusal guards catch it structurally if it ever appears. **If the reviewer or the user disagrees, the fallback is a single `--legacy-config-compat` flag threaded through all five sites; the module is identical either way, so this is a late-binding decision.**
- **Never a fallback default.** The module supplies keys *only* when handed a path outside `configs/`, refuses when the key is already present, and refuses when a block is present but its gate key is not. `config.get('thermal.enabled', False)` remains forbidden everywhere.
- **Loud.** One INFO line per invocation naming every key supplied and the source path, in the style of `modulation_compat`'s. A substitution nobody can see in a log is a substitution nobody can audit.

**Staging.** Stage 1 unblocks the 32 target runs and is independently shippable. Stage 2 absorbs the sensory keys and the remaining call sites. Stage 3 is the recurrence guard. If the reviewer wants to cut scope, cut Stage 2 — not Stage 3.

### File Changes

#### NEW — `src/environment/saved_config_compat.py`

Module docstring must state, in the `modulation_compat` register: what it does, what it deliberately does not do (soften the live path), and that it writes nothing to disk.

```python
"""Read-only compatibility layer for SAVED run configs (archived-run re-analysis).
... (see modulation_compat.py for the register; state the live-path asymmetry explicitly)
"""
from pathlib import Path

# Each entry: dotted key -> (value that reproduces the pre-feature behaviour,
#                            commit that made it mandatory, one-line justification).
# A value here is a CLAIM ABOUT WHAT THE OLD CODE DID and must name the branch
# that makes it true. Do not add an entry without one.
_ERA_KEYS = {
    # Stage 1
    "thermal.enabled": (
        False, "dd3b5dfa",
        "gate; config_loader.py:1592 else-arm reads no other thermal key, and every "
        "runtime consumer sits behind a static `if params.thermal_enabled:` "
        "(core.py:77/247/854/913/1773, sensor.py:485/541). Parity instrument: "
        "tests/env/test_thermal_parity.py"),
    # Stage 2 — moved verbatim from collect_trajectories.PRE_V31/V32_SENSOR_DEFAULTS
    "sensory.visual_value_mode":        ("sum",  "9771e98c", "original per-cell accumulation"),
    "sensory.visual_occlusion_enabled": (False,  "9771e98c", "static branch in sensor.py"),
    "sensory.olfactory_grid_range":     (0,      "0949ddb2", "0 = original single-point sample"),
    "sensory.visual_blur_enabled":      (False,  "0e8a4ef8", "blur knobs conditional-mandatory since 35a26452"),
}

# A block whose gate key is missing but whose block EXISTS is the typo case the
# mandatory-key rule exists to catch. Never supply into one.
_GATE_KEYS = {"thermal": "enabled"}

# Renamed predecessors: if the OLD spelling is present, the run predates the
# rename and its real value must not be silently replaced by the era default.
_RENAMED_FROM = {"sensory.olfactory_grid_range": "sensory.olfactory_sensor_range"}


def apply_saved_config_compat(cfg: dict, *, source: str) -> list[str]:
    """Supply era keys a frozen run config predates. In memory only.

    Raises if `source` resolves under `configs/` (the live path must keep
    hard-erroring), if a key it would supply is already present, if a gated
    block is present without its gate key, or if a renamed predecessor spelling
    is present. Returns the sorted list of keys supplied.
    """
```

Behavioural requirements the developer must implement exactly:

1. Resolve `source`; if it is under the repo's `configs/` directory, raise `ValueError` naming the path — the live path is structurally excluded, not excluded by convention.
2. For each key in `_ERA_KEYS`: if already present in `cfg`, skip it silently (a later-era run legitimately sets it). If **any** key in a group is present while others are missing, that is fine — keys are independent.
3. If a gated block exists but its gate key does not (`thermal:` present, `thermal.enabled` absent), raise — do not supply.
4. If a renamed predecessor spelling is present, raise with the old and new names.
5. Print one INFO line listing every key supplied, its value, and `source`.
6. Mutate a **copy** if the caller passes one; the docstring must say which. (Recommendation: mutate `cfg` in place and return the key list, matching `apply_sensor_compat`'s contract, since two of the five call sites need the patched dict for fingerprinting.)

#### Stage 1 — `scripts/analysis/nmn/replay.py` (lines 82–84)

```python
# BEFORE:
    cfg_path = os.path.join(models_dir, "config.yaml")
    cfg = Config.load_yaml(cfg_path)
    env_params = load_env_params(cfg)

# AFTER:
    from src.environment.saved_config_compat import apply_saved_config_compat
    cfg_path = os.path.join(models_dir, "config.yaml")
    _raw = yaml.safe_load(open(cfg_path))
    apply_saved_config_compat(_raw, source=cfg_path)
    cfg = Config(_raw)
    env_params = load_env_params(cfg)
```

`Config.load_yaml` must be replaced by an explicit `yaml.safe_load` + `Config(...)` so the shim can see the dict. Add `import yaml` at module scope if absent.

#### Stage 1 — `scripts/analysis/trajectory_glm.py` (line 54)

```python
# BEFORE:
    p = load_env_params(Config(yaml.safe_load(open(f"{run}/models/config.yaml"))))

# AFTER:
    _cfg_path = f"{run}/models/config.yaml"
    _raw = yaml.safe_load(open(_cfg_path))
    apply_saved_config_compat(_raw, source=_cfg_path)
    p = load_env_params(Config(_raw))
```

#### Stage 2 — `scripts/eval/traj_collect/collect_trajectories.py` (lines 296–347, 713–726)

- Delete `PRE_V31_SENSOR_DEFAULTS`, `PRE_V32_SENSOR_DEFAULTS` and `apply_sensor_compat`; their content moves into `_ERA_KEYS` **verbatim, comments included** — those comments carry the parity evidence and must not be lost.
- Call `apply_saved_config_compat(cfg, source=str(cfg_path))` immediately after `cfg = yaml.safe_load(f)` at line 700, i.e. **before** `assert_scene_unambiguous` and **before** `env_fingerprint(cfg)`, preserving the existing ordering property that the manifest's `env_fp` reflects the config actually used.
- Keep `--assume-pre-v31-sensors` / `--assume-pre-v32-sensors` as accepted no-op flags that print a deprecation line ("now applied automatically for saved run configs"). Recorded invocations exist in `docs/experiments/active/trajectory_factors/nmn_film_vs_unmodulated.md:233`; silently removing them breaks a documented command.
- Thread `pre_v31_sensor_keys=` in `build_manifest` (line 356) from the shim's return value so the manifest keeps recording which keys were supplied. Rename the parameter only if the developer also updates `tests/test_trajectory_collection.py`.

#### Stage 2 — `scripts/eval/eval_rollout.py` (lines 949–1007)

This is the only site that may receive **either** a live or a saved config, so it needs discrimination — the same asymmetry `modulation_compat` already gets right at line 1063 via `agent_config_source`.

```python
# In _resolve_entry, after config_path_i is determined (line 958) and BEFORE
# load_env_config at line 959:
#   - resolve config_path_i
#   - saved := it lies under the checkpoint root (ckpt_root / "config.yaml", or a
#     per-stage sibling produced by _resolve_continual_stage_config)
#   - if saved: read the YAML, apply_saved_config_compat(..., source=config_path_i),
#     and build the Config from the patched dict
#   - else: today's load_env_config(config_path_i) unchanged
```

The developer must preserve `load_env_config`'s `extends:` handling on the live branch. A frozen run config is a fully-resolved flat dump and carries no `extends:` (confirmed: the `extends:`-ignoring bug is a *fixed* bug, `22c73ba`), so the saved branch does not need it — but the developer must assert that rather than assume it, by checking `"extends" not in raw` on the saved branch and raising if present.

#### Stage 2 — `scripts/analysis/supplementary/parity.py` (lines 26–31)

Same edit shape as `trajectory_glm.py`. Note in the commit message that this script is itself the parity evidence for the v3.1 sensory values; changing it must not change what it measures.

#### Stage 3 — NEW `tests/fixtures/saved_config_eras/*.yaml` (4 files, ~9.5 KB each)

Copy one real frozen config per era, renamed to describe the era, with a `README.md` naming the source run and its training date:

| Fixture | Source run | Era it represents |
|---|---|---|
| `era_2026-08-16_pre_v32.yaml` | a `20260816-*_rppo_restpremNH_*` run | needs all five keys |
| `era_2026-08-26_mid_v32.yaml` | `20260826-144838_sens_D_vision_blur_n114g3` | needs three keys |
| `era_2026-09-07_pre_thermal.yaml` | `20260907-045531_rppo_nmnsite_t1none_s42` | needs `thermal.enabled` only |
| `era_2026-09-09_current.yaml` | `20260909-023638_rppo_olfmc_t1none_s42` | needs nothing |

These are committed because `results/` is gitignored — without them the recurrence guard cannot run in CI.

#### Stage 3 — NEW `tests/environment/test_saved_config_compat.py`

Named tests, mirroring `tests/models/test_modulation_compat.py`'s structure and its file-level docstring explaining the asymmetry:

| Test | Asserts |
|---|---|
| `test_live_config_missing_thermal_enabled_still_hard_errors` | `load_env_params` on `configs/environment/default.yaml` with `thermal.enabled` deleted raises `ValueError` matching `thermal.enabled`. **This is the direct analogue of `test_live_config_with_temp_clip_still_hard_errors` and is the test that pins the guarantee.** |
| `test_compat_refuses_a_source_path_under_configs` | `apply_saved_config_compat(cfg, source="configs/environment/default.yaml")` raises. The structural live-path guard. |
| `test_saved_config_with_thermal_block_but_no_enabled_key_still_hard_errors` | A dict with `thermal: {sigma: 0.7}` and no `enabled` raises — the typo case stays loud. |
| `test_saved_config_that_already_sets_a_key_is_left_alone` | A config with `thermal.enabled: true` is not overwritten and is not reported as supplied. |
| `test_renamed_predecessor_spelling_is_refused` | `sensory.olfactory_sensor_range` present raises, naming both spellings. |
| `test_supplied_thermal_off_equals_an_explicit_thermal_off_config` | `EnvParams` built from (pre-thermal fixture + shim) is field-by-field equal to `EnvParams` built from (same fixture + literal `thermal: {enabled: false}`). Proves the shim adds nothing beyond the key. |
| `test_every_era_fixture_loads` | Each of the four fixtures rebuilds via shim + `load_env_params`. **This is the recurrence guard**: the next mandatory key turns this red at CI time. |
| `test_era_fixture_from_the_current_era_needs_no_keys` | The 2026-09-09 fixture has an empty supplied-key list — proves the earlier fixtures are failing for era reasons, not because the shim always fires. |

Every one of the first five must **fail on pre-fix code by not existing**; `test_every_era_fixture_loads` must fail on pre-fix code because `apply_saved_config_compat` is absent — the developer must record, in the Implementation Report, the pre-fix failure of a temporary variant that calls `load_env_params` directly on the pre-thermal fixture (this is the test that reproduces the reported bug).

#### `docs/environment/CONFIG_GUIDE.md`

Add a short subsection "Reading a finished run's frozen config" under the authoring section: the live/saved asymmetry, the module that implements it, and the rule that a new mandatory key requires an `_ERA_KEYS` entry **and** a new era fixture in the same commit. Required by that guide's Maintenance Contract because this changes how configs are loaded, though not the schema.

#### `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`

Listed because four files under `scripts/` gain a new dependency on `src/environment/saved_config_compat.py`. No file under `scripts/` is added, moved, renamed or deleted, so this is an edge update, not a structural one.

#### `docs/environment/CONFIG_CRITICAL_SETTINGS.md` — **no change required**

Stated explicitly so a reviewer does not have to work it out: this plan alters no value of any registry setting. It changes only what happens when a *frozen* config omits a key. No dated change-log entry is due.

---

## Checkpoints

Verify **during** implementation, in order:

- [ ] **CP1 — Reproduce before fixing.** Run the §A1 command; confirm the `thermal.enabled` `ValueError`. Paste it into the Implementation Report.
- [ ] **CP2 — Stage 1 unblocks all 32 target runs, not just one.** Loop `load_env_params` through the shim over all 16 `*_rppo_nmnsite_*` and 16 `*_rppo_nmngaenorm_*` frozen configs; expect 32 / 32 and exactly one supplied key (`thermal.enabled`) each.
- [ ] **CP3 — The live guarantee is intact.** `pytest tests/environment/test_saved_config_compat.py -k "hard_errors or refuses" -v` green, and `pytest tests/models/test_modulation_compat.py` still green (the two shims must compose).
- [ ] **CP4 — The substitution changes nothing but the key.** `test_supplied_thermal_off_equals_an_explicit_thermal_off_config` green, and `pytest tests/env/test_thermal_parity.py` still green — the pre-existing instrument for "thermal-off equals pre-thermal" must not have moved.
- [ ] **CP5 — Archive-wide count, measured not assumed.** Re-run the §A2 cascading sweep with the shim in place. Expect **327 / 477** frozen configs rebuilding and **150** still failing on `predator_enabled` / `properties_std`. Any other number means the table is wrong; report it rather than adjusting the table to match.
- [ ] **CP6 — The 150 still fail loudly.** Confirm the remaining failures are the two legacy-schema errors and are unchanged in message — the shim must not have turned a loud failure into a quiet one.
- [ ] **CP7 — Fingerprint ordering preserved.** In `collect_trajectories.py`, confirm the shim runs before `env_fingerprint(cfg)` and that `build_manifest` still records the supplied keys. `pytest tests/test_trajectory_collection.py` green.
- [ ] **CP8 — Nothing written to disk.** Record `md5sum` of the 32 target frozen configs before and after the full test run; they must be identical. This is the one property the whole design rests on.
- [ ] **CP9 — Speed.** This is a load-time-only change on a path that runs once per analysis invocation and never inside a training step; no training-loop code is touched. State that in the Implementation Report **with the diff as evidence** (no file under `src/algorithms/` or `src/models/` modified). If the diff does touch a training path, a before/after speed measurement is required instead.
- [ ] **CP10 — Full suite.** `pytest tests/env tests/environment tests/models -q` green.

---

## Implementation Report

> **Implemented by**: [agent/person]
> **Date**: [date]

<!-- Filled by the implementing agent. Must include: the CP1 pre-fix error text; the CP5 measured
     327/150 split; the CP8 md5 comparison; and the CP9 speed justification with its evidence. -->

## Verification Report

> **Verified by**: [agent/person]
> **Date**: [date]

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**: [one-line summary]

---

## Open questions for the reviewer

1. **Automatic vs. opt-in** (§Design, decision 2). Recommended automatic; the fallback is one `--legacy-config-compat` flag threaded through five sites. This is the decision most likely to be contested and is cheap to reverse.
2. **Stage 2 scope.** Absorbing the four sensory keys is what takes the fix from 120 runs to 327. It is also the part that edits a working script (`collect_trajectories.py`). Cutting it is defensible; cutting Stage 3 is not.
3. **Bug registry.** Once this lands, `bug-curator` should record the `results/`-population instance (distinct from the recorded `configs/` row), plus the two unrecorded legacy breakages `environment.predator_enabled` and `Resource: properties_std`.
