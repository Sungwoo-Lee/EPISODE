---
title: "Separate Warming and Cooling Speeds for Body Temperature"
topic: sensors
status: active
created: 2026-09-17
last_updated: 2026-09-17
aliases: [warming_cooling_rate_scales]
---

# Separate Warming and Cooling Speeds for Body Temperature

> **Status**: IMPLEMENTED, verification pending (2026-09-17). Plan approved at Revision 2 (`plan-reviewer` SOUND). The pre-change fixture is committed (`068d791e`); the code, config, test and doc change is an uncommitted working tree under parallel review by `senior-developer`, `code-reviewer`, `math-reviewer` and `env-config-reviewer`. Commit 2 has not been made.
> **Opened**: 2026-09-17
> **Related**: [[thermal_implementation_plan]] (Stage 2, the body recurrence this changes) · [[thermal_handover]] · [OPEN_WORK_HANDOFF.md item E1](../issues/OPEN_WORK_HANDOFF.md) (reviewing every temperature setting together; this plan is **not** that review) · [[body_temperature_observation]] · [SAVED_RUN_CONFIG_COMPAT.md](../refactors/SAVED_RUN_CONFIG_COMPAT.md)

---

## Context

In the campfire world the agent has a body temperature. Each step it drifts toward the temperature of the cell it stands on, physiology pulls it partly back toward a comfortable 0°, and it dies if it leaves the band from −15 to +15. **The body warms and cools at the same speed.** The user set behavioural targets from what the agent has to do:

- **Away from a fire, about 80–110 steps.** Starting comfortable and standing in the far cold, the body should take that long to fall to −15. That matches the 100-step hunger clock, so a trip to forage, dodge predators and heal is possible.
- **Rewarming from near-death in 10 steps or fewer.** Predators strike within 1–3 steps of arriving, so a slow rewarm next to the fire leaves the agent a sitting target.
- **The fire cell itself kills by step 2–3, and the first step on it is survivable.** Anything slower is warming, not pain.

A search of about 120,000 combinations of the settings that exist today found **no** setting that meets the "away" and "rewarm" targets together. One speed cannot be slow for cooling and fast for warming at once.

**This plan adds two settings: a warming speed and a cooling speed.** Each multiplies the body's whole per-step temperature change: the warming one when the temperature is rising, the cooling one when it is falling. Where the body finally settles in any cell does not move, and neither does the load-time check built on those settling points. Both settings ship at 1.0, which reproduces today's environment exactly. Choosing values that meet the targets is a separate follow-up.

Warming faster than cooling is documented in real animals (see §A4), but the ratio the targets probably need is a deliberate modelling choice. It is also a documented departure from EVAAA, the reference environment this one was adapted from, which uses a single rate.

---

## Approval

The user pre-approved this plan before sleeping (2026-09-17) and asked that the development pipeline run to completion. A clean, independent `plan-reviewer` pass stands in for the approval gate.

- `plan-reviewer` verdict: **SOUND**, on the Revision 2 pass (2026-09-17), after SOUND WITH CONCERNS on the original draft and on Revision 1. Each concern was confirmed resolved by a fresh `plan-reviewer` pass against the plan text, never by the author. Signed results are appended below under the three `Feedback from plan-reviewer` headings.
- `math-reviewer` verdict: **no Critical finding**. All seven claims VERIFIED by derivation and numerics, and all 21 quoted durations reproduced exactly. Its two 🟡 items (the D3 rationale, and evaluating the fire target at range corners) were folded into Revision 1 as M2 and D19. The equations did not change across revisions, so no re-run was needed.
- Approved for implementation by: the user's overnight pre-approval, with the clean `plan-reviewer` pass standing in for the approval gate, recorded by top-level Claude.
- Documentation correction after approval: the helper bullet's "every test except T01 loads through this helper" was narrowed to match D20. `plan-reviewer` ruled this a wording fix that changes no test or prediction and does not reopen the plan.

---

## Decisions made unattended

Nobody was available to ask, so each call below was settled conservatively. The reasoning is recorded so the user can overturn any of them on waking.

| # | Decision | Why |
|---|---|---|
| **D1** | **Key names: `thermal.warming_rate_scale` and `thermal.cooling_rate_scale`.** `EnvParams` fields are `thermal_warming_rate_scale` and `thermal_cooling_rate_scale`. | `_rate` already marks per-step quantities in this block (`metabolic_coupling_rate`). `_scale` says the value is a dimensionless multiplier, not a new coefficient; a `k_` prefix would wrongly suggest a new physical term. A bare `thermal.warming_scale` was rejected because the block already has a different "scale" in play (the thermal drive-axis scale in E1(b)), and a bare name could be read as scaling the drive or the field. |
| **D2** | **Both scales are static `EnvParams` fields (`pytree_node=False`). The gate is computed inline from the two values: `if params.thermal_warming_rate_scale == 1.0 and params.thermal_cooling_rate_scale == 1.0:`.** No separate stored boolean. | This follows `body.recovery_in_bush_multiplier` (static float, inline `!= 1.0` gate, commit `761f427f`). A separate traced value plus a stored boolean gate could get out of sync: a `params.replace(thermal_warming_rate_scale=3.0)` that forgot the boolean would be silently ignored. Deriving the gate from the values makes that impossible. The loader applies `float()`, so YAML `1` and `1.0` both compare equal to `1.0`. Static fields add no graph inputs, so the 1.0/1.0 graph keeps exactly today's inputs. **Cost:** changing a scale recompiles, and one batch cannot mix scale values across environments. Both hold already for every static field, and the scales are per-config constants. |
| **D3** | **The metabolic-coupling drain is NOT scaled.** It stays `rate * abs(k_loss * (T - temperature_setpoint))` using the pre-step temperature. The code comments and `05_body_homeostasis.md` are updated to say so. *(Reason corrected in Revision 1; the decision is unchanged.)* | **Why.** The thermal field is built once at reset (`core.py:1821`), so a body resting in one cell recomputes the same `d` every step. At a settled equilibrium the sign of `d` is **fixed by float rounding**: usually frozen at the direction the body arrived from, occasionally alternating every step. Both reviewers measured this independently. `plan-reviewer` found 0 sign flips over 6 cases × 2000 settled float32 steps; the body stalls at −8.0000029 with `d > 0` when it arrives from below, and at −7.9999843 with `d < 0` from above. `math-reviewer` ran 1,072 random legal settings × 20,000 steps: the sign stayed frozen at the arrival direction in 97.3% of them, and alternated every two steps from rounding in 2.7%. The defence term `k_loss*(T - setpoint)` is not zero at that settled point. **A bill scaled by the sign of `d` would therefore be path-dependent or jittery**: two settled bodies 1.6e-5° apart could pay bills that differ by the full warming/cooling ratio, forever, depending only on how they got there. The unscaled bill is a continuous function of body state and has neither problem. Two further reasons: the feature is off in every live config, and E1(a) already queues the drain's calibration for the whole-block review. **D3 is defensible but not the only defensible choice.** Two alternatives are recorded for E1(a). **(i) Time-dilation reading** (`math-reviewer`): the scaled update is forward Euler with step length `h = s`, and under that reading a bill consistent with elapsed time is `s·rate·abs(k_loss·(T − setpoint))`. D3's unscaled bill is then a *per-decision* cost, not a *per-degree-moved* cost, and the two coincide only at `s = 1`. **Consequence under D3:** a full rewarm costs *less* total nutrition the larger the warming scale, because it takes fewer steps. **(ii) Continuous scaled formulation** (`plan-reviewer`): scale the bill by the direction of the *defence* term, `sign(setpoint − T)`, using the warming scale when the defence pushes the body up and the cooling scale when it pushes down. The bill is zero at the setpoint, so the switch is harmless and there is no path dependence. **Known cost of D3:** with unequal scales the claim "the charge on step t pays for exactly the defence performed on step t" becomes approximate while the body is moving. The comment is amended to say so. T11 pins the decision. |
| **D4** | **Scales must be strictly > 0, written `if not (scale > 0.0): raise`.** Warming covers `d > 0`; **cooling covers `d <= 0`, including `d == 0`.** | A scale of 0 freezes the body in that direction forever: at `cooling_rate_scale: 0` a warmed body never cools, and the equilibrium is never reached from above. A negative scale reverses the direction and diverges. The negated comparison also rejects a YAML `.nan`, which a plain `scale <= 0.0` would let through. At `d == 0` the branch makes no numerical difference to temperature, because `s * 0 == 0`; T09 pins that. Under D3 it makes no difference to the drain either. |
| **D5** | **The existing check `k_exchange + k_loss <= 1` stays exactly as it is. A per-scale check is added next to it:** `if not (scale * (k_exchange + k_loss) <= 1.0): raise`, run once per key, each naming its own key. | The unscaled check keeps `k_exchange` and `k_loss` meaning "fraction of the gap closed per step", which is their documented meaning. Relaxing it would be a separate scope decision. *(Revision 1 note: the unscaled check is redundant with the per-scale checks whenever `max(warming, cooling) >= 1`, and it is not implied when both scales are below 1. It is kept for the documented meaning of `k_exchange` / `k_loss`, not for stability.)* The per-scale bound is the one that actually prevents overshoot (§A2). `k_exchange` is one global scalar, not per-cell (§A5.1), so no maximum over cells is needed. **Consequence for the follow-up search:** its space is `k_exchange + k_loss <= 1` and `scale * (k_exchange + k_loss) <= 1` for each scale. |
| **D6** | **Configs: the keys are written inline at `1.0 / 1.0` in `configs/environment/default.yaml` and in the two archived thermal-on standalone worlds. They are NOT written into `basic/05-campfire_thermal_10x10.yaml` or `basic/06-sensory_noise_10x10.yaml`.** | Level 05's own `thermal:` block contains only `enabled: true`; it takes every body constant (`k_exchange`, `k_loss`, …) from `default.yaml`, and level 06 extends level 05. Writing the two scales only into 05 would make them the lone body constants spelled out there. They resolve to 1.0/1.0 through the trainer's loader, and Checkpoint CP3 verifies that on the resolved config. `default.yaml` needs the keys anyway, because `tests/env/test_thermal_validation.py` switches `enabled` on inside `default.yaml`'s own dictionary. The two archived worlds need them because eight test modules and one fixture generator load them as raw, thermal-on configs (§A5.3). The ~70 archived **thermal-off** configs with a `thermal:` block are not touched, because a conditional key is never read when `enabled` is false. |
| **D7** | **`docs/develop/active/thermal/temperature_system_plan/sim.py` and its vendored copy `tests/env/thermal_sandbox_oracle.py` are not modified.** The new tests carry their own two-rate NumPy oracle. | `sim.py` is the design record for the single-rate body, and the vendored oracle is meant to mirror it verbatim. Adding scales there would change a historical artefact and couple the existing Stage 2 tests to this change. The follow-up target search will need its own two-rate recurrence; §F1 gives it. |
| **D8** | **A new byte-identity fixture is added, captured from the pre-change code.** A new generator script under `scripts/fixtures/` produces it, so `SCRIPTS_DEPENDENCY_MAP.md` gets a row. | Measured: the only existing thermal-on fixture, `thermal_on_coupling_off.npz`, has **0 warming steps** in 300 (273 cooling, 27 flat; the agent dies around step 16 and freezes). It therefore **cannot detect a mistake in the warming half of the gate**. The new fixture holds four rollouts: warming, cooling, and each again with coupling on. Following the `761f427f` precedent, a pre/post jaxpr hash of the whole `jax_step` is also required (CP5). |
| **D9** | **The scales are not added to the curriculum modality fingerprint** (`_modality_fingerprint` in `train.py` / `dreamer_srl_main.py`). | That fingerprint guards what observation dimensions *mean*. The scales change dynamics, not observations, and the fingerprint already skips continuous floats on purpose (see `dreamer_srl_main.py:838-848`). |
| **D10** | **`scripts/claude/regen_dev_index.py` was not run.** `docs/develop/INDEX.md` currently holds another session's staged, uncommitted work. The frontmatter `topic` is `sensors`, matching the sibling docs in `thermal/`; `thermal` is not in `VALID_TOPICS`. | Regenerating the index now would rewrite a file another session is mid-way through committing. Whoever commits `INDEX.md` next picks this doc up. |
| **D11** | **The comment deriving the Body Temperature noise clip in `default.yaml` (`clip_min/max: ±100`) is not edited.** | Checked: under the D5 bound one step can never pass the equilibrium (§A2), so the worst terminal overshoot jumps to at most `T*`. On the calibrated fire `T*` is +51 to +65 (world −22 to −28), which is under 100. The clip cannot bind at shipped geometry for any legal scale. The comment's one-step formula is written for scale 1.0 and is flagged for the follow-up (§F2) instead of edited here. |
| **D12** | **`docs/environment/05_body_homeostasis.md` is updated**, although it is not one of the three Maintenance-Contract docs. | It is the doc that states the recurrence, the time constant and the drain formula. All three would go stale. |
| **D13** | **Two commits.** (1) The generator, the pre-change fixture and the dependency-map row. (2) Everything else, so the registry change-log entry lands in the same commit as the `default.yaml` key, as the registry protocol requires. | A separate first commit makes it visible in history that the evidence came before the change. |
| **D14** | **Stop condition checked, and none found.** All six settled requirements were checked against the code, and none is factually false. One finding (§A3) bears on the **follow-up**, not on this plan: at today's other settings, the "away" time still depends strongly on the per-episode world temperature, whatever cooling scale is chosen. | Recorded so the follow-up search does not assume the two keys alone are enough. |
| **D15** | **(Revision 1, M1) The shared test helper `_params(d)` checks the two new `EnvParams` fields on every load:** if `d["thermal"]["enabled"]` it asserts both fields equal the dict's values; otherwise it asserts both equal `1.0`. **T01 does not use it** and loads through a plain `load_env_params(Config(d))`. **T04, T05, T11 and T14 gain a check that the scale was actually applied.** | Without these, T04, T05, T09, T11 and T14 would **pass** on pre-change code: each checks a property that also holds when the scales are ignored, and none reads a new field. Under the original "any other outcome is a stop" rule that would halt the night on a false alarm. The helper check fails loudly pre-change (`AttributeError`) and afterwards catches a loader that drops or rewrites a value. T01 is kept free of it because T01's pre-change job is the opposite: to **pass** and show the fixture matches the code it came from. |
| **D16** | **(Revision 1, M3) Foreign-edit attribution rule for CP7.** Record `git diff -- src/environment/dashboard \| sha1sum` at Step 0 and Step 6. If test counts change **only** in `test_thermal_rendering.py` and/or `test_dashboard_layout.py` **and** that hash changed, the change is attributed to the renderer session and reported, not treated as a stop. Any other count change is still a stop. The A5.6 foreign-edit check is also re-run on `config_loader.py`, `state.py` and `core.py` immediately before Step 4. | Both files import `src/environment/dashboard/*`, which carries the renderer session's uncommitted edits (`episode.py`, `painters.py`), and that session is active tonight. `core.py` imports no dashboard code, so those edits cannot reach `jax_step` or any byte-identity gate. The rule is narrow on purpose: it excuses only the two files that can see the foreign code, and only when the foreign code demonstrably moved. |
| **D17** | **(Revision 1) The revision commit includes `plan-reviewer`'s signed `## Feedback from plan-reviewer` block, which was appended to this doc uncommitted and is kept verbatim.** | It is review evidence for this plan and belongs in the doc's history. Leaving it unstaged risks losing it. It is not rewritten. |
| **D18** | **(Revision 1, L3) `test_backward_compat_configs.py` and `test_maintained_worlds_bush_blocks_animals.py` are added to the pre-change test list.** | Both glob the maintained and archived worlds, including the thermal-on ones, and both are cheap. |
| **D19** | **(Revision 1, math-reviewer) The target search's fire check must be done at the corners of the sampled ranges, and §A3 is amended to say so.** | At warming scale 2, the first step onto the fire is survivable at world −25 / ratio 12 (body 13.08), and barely so at −28 / 12 (14.64). It is lethal at −25 / 13 (15.83) and at −28 / 13 (17.73); all four values were re-computed here. The midpoint example in §A3 therefore misses the "first step survivable" target in part of the sampled world. This is not a defect of this plan, whose §A3 is illustrative, but the follow-up must not repeat it. |
| **D20** | **(Revision 2) Sub-cases that expect `load_env_params` to raise call it directly (`load_env_params(Config(d))`), not through `_params`. This narrows D15's "every test except T01 loads through this helper" and the same sentence in the test-helper bullet: those two sentences now mean every *successful* load outside T01. Keys a test removes are removed with `pop(key, None)`, never `del`.** The rows D15 and the helper bullet were left unedited because revision round 2 is limited to the T12/T13 rows and their CP2 entries. **This decision governs where they differ.** | `pytest.raises(ValueError)` does not catch the `AttributeError` that the helper's field read raises on pre-change code, so a raise-expecting sub-case wrapped in `_params` fails with the wrong exception type and trips CP2's stop rule. On a load that must fail, the field check is meaningless anyway. `del` on a key that does not exist until Step 3 raises `KeyError` before any loader runs. Both defects, and both fixes, were reproduced by running the T12 and T13 bodies against the current, still pre-change tree (`tmp/20260917_rev2_trace_t12_t13.py`). |
| **D21** | **(Implementation) The `SCRIPTS_DEPENDENCY_MAP.md` footer's dated "Last updated" line was extended** with the new generator, in addition to the planned row. | That file records every addition in its footer; skipping it would leave the footer claiming 2026-09-15. Same file, same commit as the row. |
| **D22** | **(Implementation) T02 counts `select_n` / `gt` equations recursively, including nested sub-jaxprs, not over the top-level `jaxpr.jaxpr.eqns` only.** | Probed before writing the test (JAX 0.9.0.1): `jnp.where` traces as a nested `jit[name=_where]` equation whose body holds the `select_n`, so a top-level count would never see the new select and T02 would fail post-change for a reason unrelated to the gate. The recursive count is what "strictly more `select_n` equations" means. |
| **D23** | **(Implementation, D16) A content hash of the dashboard code was recorded in addition to the diff hash.** | Between Step 0 and Step 1 the renderer session committed its dashboard edits (`fe341d7d`), so `git diff -- src/environment/dashboard \| sha1sum` moved from `12ee6249…` to `da39a3ee…` (empty diff) with no code change. The diff hash alone would have counted as "changed" for D16. `cat src/environment/dashboard/*.py \| sha1sum` = `316cd303…` was recorded before and after Step 6 and did not change. As it turned out, no test count changed, so D16 was never invoked. |
| **D24** | **(Implementation) The fixture generator asserts that `src` was really imported from `--src-root`.** | The fixture is only evidence if its source is the pre-change tree; a stray `src` on `sys.path` would silently record the working tree instead. Cheap, and it fired no false alarm. |
| **D25** | **(Implementation) Speed probe = `vmap(64)` × `lax.scan(500)` of `jax_step` on the archived campfire world, 7 repetitions after one warm-up; at Step 6 the (1.0, 1.0) and (3.0, 0.3) configurations alternate within each repetition.** | The plan fixed the world, repetitions and statistics but not the harness. Scanning keeps Python dispatch out of the measurement. Step 0 has no alternation partner, because pre-change code has no scale fields. Script: `tmp/20260917_014500_speed.py`. |
| **D26** | **(Implementation) T07's all-three-terms case uses cell −10, `k_exchange` 0.04, `k_loss` 0.01, `k_metabolic` 0.3, setpoint 2.0, scales (2.0, 0.5), and starts −12 (warming) and +12 (cooling).** | The plan left the values open. These make all three terms non-zero and exercise both branches against the hand formula. |
| **D27** | **(Implementation) T14 calls `jax.clear_caches()` before counting compiles (the `test_no_recompile.py` pattern), and T01 also asserts the fixture's exact key set, dtypes and shapes.** | Without clearing, "count is 1 after step 1" would depend on test order. The extra T01 checks stop a fixture with a missing or re-typed array from passing by comparing less. |
| **D28** | **(Implementation) `_update_body_trace` carries only `body_temp` through `lax.scan`, not the whole state.** | `update_body`'s body-temperature output depends only on `body_temp`, the fixed field, the cell and params, so this is equivalent to `state.replace(body_temp=new_bt)` each step and far cheaper to trace. |
| **D29** | **(Implementation) The registry change-log entry's "Commit" field names the fixture commit `068d791e` and says the code/config/doc change is the plan's second commit, made after review.** | Commit 2 is deliberately not made by the developer tonight; the reviewers see the dirty tree first. Whoever commits should replace that phrase with the SHA if wanted. |
| **D30** | **(Fix round 1) The two archived worlds now carry different, per-file loader lists, not "nine modules and two generators" on both.** | Recounted with `git grep` plus the untracked new test. `campfire_world.yaml` is loaded from a raw `Config` by **nine** test modules (the original eight plus `test_thermal_rate_scales`) and **two** generators. `campfire_world_body_temp_hidden.yaml` is loaded **only** by `test_body_temperature_observation.py`; its "eight test modules" comment, copied from the plan's template at Step 3, was wrong from the start. Two further `git grep` hits load neither world: `scripts/eval/make_render_fixture_recordings.py` names it in a provenance string ("copied as text, never loaded"), and `test_dashboard_layout.py` only in a test-function name. Lists replace counts, so the next addition cannot make a number stale. |
| **D31** | **(Fix round 1) The committed generator was not modified, and the provenance pin lives only in T01, as a module-level `PRE_CHANGE_SHA` constant.** | `code-reviewer` marked a generator-side pin optional; commit 1 stays as it is. A named constant makes the pinned commit visible at the top of the test file, next to the duplicated scenario table. |
| **D32** | **(Fix round 1) YAML booleans are still accepted by `float()` for the two scales (`true` → 1.0).** | `code-reviewer` Low. The behaviour is inherited from every `thermal.k_*` read (plan-reviewer L2), so rejecting it in two keys only would make the block inconsistent. A whole-block concern for OPEN_WORK_HANDOFF E1. |
| **D33** | **(Fix round 1) `test_backward_compat_configs.py` was not edited.** | `env-config-reviewer` found it skips every layered maintained world, including both live thermal-on worlds, on a pre-existing key. That blind spot predates this change; the coordinator routed it to `bug-curator`. |
| **D34** | **(Fix round 1) In the `02_config_schema.md` "Body-block validation" table the two new rows go after `k_loss` and before `k_metabolic`, so the recurrence rows stay contiguous, and the sentence below says "The first eight".** | Counted rows 1–8: `temperature_setpoint`, `min_temperature`, `max_temperature`, `k_exchange`, `k_loss`, `warming_rate_scale`, `cooling_rate_scale`, `k_metabolic`. The coupling rows follow. **Noticed, not touched:** the next sentence, "From Stage 4 the first two also enter the reward", predates this change and is imprecise. The first two rows are `temperature_setpoint` and `min_temperature`, but the drive uses `temperature_setpoint` and `max_temperature`. It is left for the doc's owner. |
| **D35** | **(Fix round 1) The absence of executable changes in `core.py` was shown against a reconstructed pre-round file, not against HEAD.** | `git diff -U0 HEAD -- core.py` necessarily includes the reviewed Step-5 gate code, so it cannot show *this round* is comment-only. The pre-round file was rebuilt by removing exactly the two inserted comment blocks; it differs from HEAD by 55 lines (= Step 5's 49 insertions + 6 deletions), and differs from the current file by comment lines only. |

---

## Analysis

### A1. What exists today

`src/environment/core.py::update_body` (lines 286–317 at HEAD `663cbd72`), inside a static `if params.thermal_enabled:`:

```python
cell_temp = state.thermal_field[new_agent_pos[0], new_agent_pos[1]]
new_body_temp = (
    state.body_temp
    + params.thermal_k_exchange * (cell_temp - state.body_temp)
    + params.thermal_k_metabolic
    - params.thermal_k_loss * (state.body_temp - params.temperature_setpoint)
)
```

`k_exchange`, `k_loss` and `k_metabolic` are **traced** scalar `EnvParams` fields (`state.py:393-395`). The metabolic-coupling drain sits earlier in the same function (`core.py:192-196`), behind the **static** field `thermal_metabolic_coupling` (`state.py:411`, `pytree_node=False`). It reads the pre-step `state.body_temp`.

The stability check is at `config_loader.py:1553-1558`: `if _th_k_exchange + _th_k_loss > 1.0: raise ValueError(...)`. It is inside `if _thermal_on:`, with each rate validated `>= 0` just above.

### A2. The change, and why every settling point survives it

Write `K = k_exchange + k_loss` and let `T*` be the body's settling temperature in the current cell:

$$
T^{*} = \frac{k_{ex}\,T_{field} + k_{loss}\,T_{set} + k_{met}}{K}
$$

The per-step change is linear in `T`:

$$
d(T) = k_{ex}(T_{field} - T) + k_{met} - k_{loss}(T - T_{set}) = K\,(T^{*} - T)
$$

The new update is `T ← T + s·d`, with `s = warming_rate_scale` if `d > 0` and `cooling_rate_scale` otherwise.

- **Fixed points are unchanged.** `s·d = 0` exactly when `d = 0`, because `s > 0` (D4), and `d = 0` exactly when `T = T*`, because `K > 0`. So there is one settling temperature per cell, with no dependence on the path taken, and it is today's `T*`.
- **With `s·K <= 1` the approach cannot overshoot.** Let the error be `e = T − T*`. The update gives `e_next = (1 − s·K)·e`, and `0 <= 1 − s·K < 1`. The sign of `e` therefore never flips while the agent stays in one cell, so the same scale applies on every step. **The path is exactly today's single-rate recurrence with rate `s·K` in place of `K`.** This is why D5's bound matters beyond "no oscillation". The loader's structure check (`02_config_schema.md` §"load-time structure check") relies on "the approach to `T*` is monotone", and that stays true. Between `s·K = 1` and `s·K = 2` the body would cross `T*` and flip scale on each step. It would still converge, but the monotone claim would be false.
- **Time to reach a threshold** `T_th` from `T0`, in a fixed cell, is the first `n` with `(1 − s·K)^n <= (T_th − T*)/(T0 − T*)`. Only `s·K` enters it, which is why one key per direction is enough to set speed.
- **`K = 0` (both rates zero)** has no fixed point today: the body drifts by `k_met` per step. After the change it drifts by `s·k_met`. The structure check already skips this case (`config_loader.py:650`), and nothing new is needed.

**What "warming" means, stated plainly for the docs.** The scale follows the direction of *this step's* change, not whether the body is above or below the setpoint or colder than its cell. A body at −2 in a −10 cell has `T* = −8` and is cooling, even though it is below the comfortable 0°. A body at +12 standing on the fire is warming, **so a warming scale above 1 also makes the fire kill faster**. Likewise, a body overheated to +14 that steps back to the ring (`T* = +8.09`) cools at the cooling speed. The follow-up search must account for both effects.

**`_thermal_equilibrium`, `_thermal_radial_equilibria` and `_thermal_structure_verdict` (`config_loader.py:428-527`) stay unmodified.** They compute fixed points only, and fixed points are unchanged. Measured at HEAD at the calibrated midpoint (world −25, fire ratio 12, sigma 0.7, 10×10), the settling temperatures are **+57.93 on the fire, +8.09 on the ring, −19.68 three cells out**. None of these depends on either scale. The plan tests this property (T04, T05) rather than asserting it.

### A3. Why two keys are needed, and a caveat for the follow-up (illustrative, not a tuning)

The following computations use today's `K = 0.05` and the loader's own `_thermal_radial_equilibria`. "Far cold" means a uniform cell at the world baseline, `T* = 0.8 × world`.

| World baseline | Rewarm −14 → 0 on the ring, s=1 | s=2 | Away 0 → −15 in far cold, s=1 | s=0.3 | s=0.2 | Fire kill from ring, s=1 | s=2 |
|---|---|---|---|---|---|---|---|
| −22 | 22 steps | 11 | 38 | 127 | 191 | step 4 | step 2 |
| −25 | 20 | **10** | 28 | **92** | 138 | step 3 | step 2 |
| −28 | 19 | 9 | 22 | 74 | 111 | step 3 | step 2 |

At world −25 a warming scale near 2 and a cooling scale near 0.3 meet all three targets, a ratio of about 6. That fits the user's "probably around 4–6×".

**Revision 1: that example fails the fire target elsewhere in the sampled world.** The environment samples the world baseline in [−28, −22] and the fire ratio in [11, 13]. At warming scale 2 the first step from the ring onto the fire leaves the body at 13.08 (world −25, ratio 12), 14.64 (−28 / 12, only 0.36° from death), **15.83 (−25 / 13, dead on step 1)** and **17.73 (−28 / 13, dead on step 1)**. At the other end, −22 / 11, the fire takes until step 3 at scale 2 and more than 3 steps at scale 1. These values were re-computed from `_thermal_radial_equilibria` at each corner. **The follow-up target search must evaluate the fire target, like the structure check does, at the corners of both sampled ranges and not at the midpoint** (D19, F1).

**Caveat, for the follow-up and not this plan (D14).** At any fixed cooling scale the away time still varies by about 1.7× across the −28 to −22 range the environment samples per episode (127 vs 74 steps at s=0.3). The target band 80–110 is only 1.375× wide. The cause is the gap between far-field `T*` and the −15 death line: only 2.6° at world −22. A cooling scale stretches time but cannot fix that sensitivity. **The spread already exists at scale 1** (38 vs 22 steps at −22 / −28): it is the gap between the far-field settling temperature and the death line, which no speed multiplier changes. The follow-up search will likely have to move `k_loss` or the world baseline as well. The two keys are necessary but may not be sufficient.

Working file: this was computed inline during planning. The numbers above are reproducible from `_thermal_radial_equilibria(12*abs(w), w, 0.7, 3, 10, 10, 0.04, 0.01, 0.0, 0.0)` together with the recurrence `T ← T + s·K·(T* − T)`.

### A4. Ecology, and the deviation from EVAAA

**Plausible in kind.** Heating faster than cooling is well documented in ectotherms: reptiles use cardiovascular control (heart-rate and blood-flow changes) to heat faster than they cool. In endotherms, vasodilation versus vasoconstriction and insulation make heat gain and heat loss asymmetric. **The ratio the targets probably need, about 4–6×, is at or beyond the commonly reported range, so it is a deliberate model choice and not a biological measurement.** The user asked whether the asymmetry is ecologically reasonable and accepted this reading.

**The literature figures in this paragraph have NOT been verified.** They are the user's and the session's recollection. `research-postdoc` should check them against primary sources before any paper claim relies on them.

**Deviation from EVAAA, checked in the vendored source.** EVAAA updates body temperature with one coefficient on the summed relative surround temperature: `resourceLevels[2] += changeBody_0 * surroundTemp * Time.fixedDeltaTime + …` (`vendor/evaaa/evaaa_unity/Assets/Scripts/Agent/InteroceptiveAgent.cs:860-878`). There is no sign-dependent rate. This change is a deliberate departure, and the registry change-log entry records it (File Changes, `CONFIG_CRITICAL_SETTINGS.md`).

### A5. Re-verification of the repo, and how each item was checked

**A5.1 Code shape.**
- `update_body`, the drain and the recurrence were read at `core.py:124-317`. Its only caller is `jax_step` at `core.py:878`, found by `git grep "update_body("` over `src/ tests/ scripts/`; `tests/env/test_recovery_in_bush.py:208` traces it directly.
- The stability check was read at `config_loader.py:1553`: the form is `k_exchange + k_loss > 1.0 → raise`, so the allowed region is `<= 1`. **The check has no test**: `git grep` over `tests/` for its message text and for `<= 1` found nothing thermal. T13 therefore also covers the existing check.
- The `thermal_metabolic_coupling` gate is a **static `EnvParams` field**, not a closure (`state.py:411`), used as a Python `if` at `core.py:192`.
- The conditional-mandatory pattern from `feaa3f1b` was read at `config_loader.py:1593-1606`: `get_mandatory` inside `if _thermal_on:`, with inert sentinels in the `else:` branch (`1616-1651`).
- **`k_exchange` is one global scalar.** `EnvParams.thermal_k_exchange: float` (`state.py:393`). `git grep thermal_k_exchange` over `src/` finds one reader, `core.py:303`, and no per-cell array exists.
- **The loader does not reject unknown keys.** Checked in three ways. `Config` (`src/utils/config.py:25-100`) is a plain dict wrapper with `get`/`get_mandatory` and no schema. `load_env_config` (`config_loader.py:78`) only resolves `extends:`. `git grep -i -E "unknown key|unrecognized|unexpected key|allowed_keys|KNOWN_KEYS|extra key"` over `src/` found no key whitelist. **So configs can gain the keys before the loader reads them without breaking any load** (edit order, Step 3).
- There is **one `EnvParams(` constructor**, `config_loader.py:2171` (`git grep "EnvParams("`), so no other code builds `EnvParams` and would break on new required fields.

**A5.2 Every thermal-on config, by sweep.** Two independent methods:
1. **Text grep**: `git grep -A3 -E "^thermal:" -- configs/ | grep "enabled: *true"` found 3 files: `archive/thermal/campfire_world.yaml`, `archive/thermal/campfire_world_body_temp_hidden.yaml`, `basic/05-campfire_thermal_10x10.yaml`.
2. **Trainer loader sweep**: every tracked `configs/environment/**/*.yaml` (335 files, from `git ls-files`) went through `load_env_config` (resolves `extends:`) and then `load_env_params`. Script: Appendix B. It found **4 thermal-on configs**: the three above plus **`basic/06-sensory_noise_10x10.yaml`**, which is thermal-on only through `extends:` and which the text grep cannot see. A second run over the 24 files in `configs/continual/` and `configs/verification/` found **none**.

| Config | Kind | Loads at HEAD | Migration |
|---|---|---|---|
| `configs/environment/experiment/archive/thermal/campfire_world.yaml` | standalone | yes | keys inline (D6) |
| `configs/environment/experiment/archive/thermal/campfire_world_body_temp_hidden.yaml` | standalone | yes | keys inline (D6) |
| `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml` | layered (→ 04 → … → `default`) | yes | inherits from `default.yaml` (D6); resolved value checked in CP3 |
| `configs/environment/experiment/basic/06-sensory_noise_10x10.yaml` | layered (→ 05) | yes | inherits from `default.yaml` (D6); resolved value checked in CP3 |
| `configs/environment/default.yaml` | standalone, **thermal-off** | yes | keys inline, because tests switch `enabled` on in its dict (`test_thermal_validation.py:217-219`) |

**Load counts at HEAD, 2026-09-17** (Appendix B; "standalone" = no `extends:` key):
- tracked env configs: 335;
- standalone: 118, of which **27 load**;
- layered: 217, of which **211 load**.

These differ from the 2026-09-16 registry figures (265 standalone with 38 loading; 217 layered with 210 loading) because the **population** differs, a difference `plan-reviewer` fully accounted for. The registry figure covers the **whole `configs/` tree**: `git ls-files 'configs/*.yaml'` gives 483, and 483 − 217 layered = 266 ≈ 265. Appendix B covers **`configs/environment/` only** (335 files). **The before/after comparison must use Appendix B on both sides.** Expected delta: **zero**.

**A5.3 The archived-config trap from `761f427f`.** The new keys are conditional, so only **thermal-on** configs can fail to load. The trap still bites here, because the archived campfire world is thermal-on and these modules load it from a raw `Config`, found by `git grep "campfire_world"` over `tests/ scripts/ src/`:
- `test_body_temperature_observation.py` (both archived worlds)
- `test_metabolic_coupling.py`
- `test_thermal_body.py`
- `test_thermal_field.py`
- `test_thermal_rendering.py`
- `test_thermal_reward_gate.py`
- `test_thermal_validation.py`
- `test_thermoception.py`
- `scripts/fixtures/generate_metabolic_coupling_fixture.py`

That is 8 test modules and 1 script. Without D6's two archived edits, every one of them would die at load. The parity collectors (`test_unified_parity.py`, `test_thermal_parity.py`, `test_thermal_reward_gate.py`) glob all of `configs/environment/experiment/**`. **No** parity fixture belongs to a thermal-on config (all 34 + 12 + 12 fixture slugs listed by `git ls-files tests/env/fixtures/`), so thermal-off archived configs are unaffected.

**A5.4 Every other reader of the thermal keys.** `git grep -n -E "k_exchange|k_loss"` over `src/ scripts/ tests/ configs/` gave 112 lines (`tmp/20260917_thermal_rates_grep.txt`).
- **Outside configs:** `config_loader.py` (read, validate, fixed-point helpers), `core.py` (recurrence, drain), `state.py` (fields).
- **Tests:** `test_metabolic_coupling.py`, `test_thermal_body.py` and `test_thermal_validation.py` (closed forms at scale 1.0, still valid), and `thermal_sandbox_oracle.py` (vendored single-rate oracle, D7).
- **`scripts/`:** none.
- **Design-doc copies of the recurrence:** `temperature_system_plan/sim.py`, `build_page.py` and `figK_budget.py`. These are design artefacts and are not modified (D7).
- **Test helpers building thermal dicts inline:** `test_thermal_validation.py::_MUST_LOAD` and `test_thermal_body.py::_uniform_field_config`. Both start from `default.yaml` or the archived campfire world, so they gain the keys from D6's edits.
- **Other `EnvParams` thermal readers** (`git grep` for `temperature_setpoint` etc.): the renderer and dashboard read `temperature_setpoint` only. **No renderer file is touched.**

**A5.5 Every byte-identity fixture.** From `git ls-files tests/env/fixtures/`:

| Fixture family | Files | Thermal | Checked by |
|---|---|---|---|
| `metabolic_coupling/thermal_on_coupling_off.npz` | 1 | **ON**, coupling off, **0 warming steps** (measured) | `test_metabolic_coupling.py::test_off_by_default_is_a_provable_noop` |
| `metabolic_coupling/` coupling-**on** fixtures | **0: none exist** | — | — |
| `thermal_parity/*.npz` | 12 | off | `test_thermal_parity.py` |
| `parity/*.npz` | 34 | off | `test_unified_parity.py` |
| `visual_parity/*.npz` + `visual_parity_ref.npz` | 12 + 1 | off | `test_visual_parity.py` |
| `extero_noc_parity_ref.npz` | 1 | off | `test_extero_noc_parity.py` |
| **new** `thermal_rate_scales/single_rate_rollouts.npz` | 1 | **ON**, warming and cooling, coupling on and off | new `test_thermal_rate_scales.py` (D8) |

**All of them were captured on CPU.** `tests/env/conftest.py` pins `JAX_PLATFORMS=cpu` and raises if JAX came up on another backend. Every run in this plan therefore goes **one file per process** under `JAX_PLATFORMS=cpu`, which also avoids the XLA core dump on whole-directory runs.

**A5.6 Foreign edits.** Commands: `git status --porcelain --` over every path in File Changes, plus `git diff --cached --name-only`, each wrapped in `timeout` with retries. **None of the files this plan changes carries another session's edits.** Unrelated files that are dirty: `docs/develop/INDEX.md` (staged), `docs/develop/active/refactors/SAVED_RUN_CONFIG_COMPAT.md` (staged) and `docs/develop/active/meta/artifact_format_bugs.md` (unstaged). HEAD moved from `976c0024` to `663cbd72` during planning, so other sessions are committing. **The developer repeats this check immediately before each commit** (CP10).

### A6. Known-context rows (from `bug-curator`)

- **No registry row covers `update_body`, `body_temp`, static `EnvParams` fields or coupling accounting.** This is new ground, so the tests carry the burden: fixture identity (T01), jaxpr identity (CP5) and gate structure (T02).
- **Reset is not bit-identical across compilations.** That row is scoped to `animal_property_sampled` at reset, one float32 ULP. This plan's static gate keeps the 1.0/1.0 graph literally unchanged, so no new divergence can come from here. `jax_reset` is not edited. The new fixture compares `body_temp` and `nutrition`, not sampled animal properties, and the uniform-field worlds contain no animals.
- **OPEN_WORK_HANDOFF E1** (review the whole `thermal:` block together). **This change does not resolve E1.** Interaction: E1(a)'s drain calibration now also has to consider D3, the drain being unscaled while the body moves at `s·K`. D3 records the two alternative readings E1(a) should weigh: time-dilation (bill × `s`) and the defence-direction switch. Neither the scale values nor anything E1 lists is tuned here.
- **Mandatory-key migration drift** (open, deliberately deferred). The keys are conditional, so thermal-off loads cannot change. Before/after counts are recorded with Appendix B (A5.2, CP3).
- **Saved run configs stop loading once a key becomes mandatory** (open, remedy in `SAVED_RUN_CONFIG_COMPAT`). Checked 2026-09-17: `results/*/*/models/config.yaml` = **503 files, 0 with `thermal.enabled: true`**, 0 read errors (`tmp/20260917_saved_cfg_thermal.py`). The 77 saved configs using `extends:` date from June–July, before thermal existed. **No saved run is affected.** Trajectory-store fingerprints are also unaffected: `collect_trajectories.py:704` hashes the run's *frozen* config, not the live `default.yaml`.

### A7. Checked and ruled out

- **Curriculum modality fingerprint:** not affected (D9).
- **Body Temperature observation clip ±100:** cannot bind at calibrated geometry (D11).
- **Trajectory-store `env_fp`:** frozen-config hash (A6).
- **Parameter stacking across environments:** `git grep` for stacking `EnvParams` over `src/` found none. Static fields already include `thermal_metabolic_coupling` and `recovery_in_bush_multiplier`, so this adds no new constraint.
- **Dtype drift:** `jnp.where(pred, py_float, py_float)` yields a weak float32, and multiplied by the float32 change it stays float32. If it widened, `jax_step` would retrace on the next step; T14 catches that.

---

## Implementation Plan

### Design

1. Two conditional-mandatory keys under `thermal:`, read with `get_mandatory` **inside** `if _thermal_on:`, cast with `float()`, validated `> 0` and `scale * (k_exchange + k_loss) <= 1` per key. The inert value when thermal is off is `1.0` / `1.0`.
2. Two static `EnvParams` fields.
3. In `update_body`, a static Python gate. At 1.0/1.0 the four existing lines are kept **character for character**. Otherwise the per-step change `d` is computed once and scaled by `jnp.where(d > 0.0, warming, cooling)`.
4. The drain is unchanged in code and gains a comment (D3).
5. Configs at 1.0/1.0 (D6), tests, and docs.

### Edit order (the tree is shared; live configs must load between steps)

| Step | What | Loads in between? |
|---|---|---|
| **0** | **Read-only baseline.** Record the HEAD SHA. Run the pre-change test list (below). Run Appendix B and record counts. Record `jax_step` jaxpr SHA-1s (CP5) for `default.yaml`, the archived `campfire_world.yaml` and `basic/05-campfire_thermal_10x10.yaml`. Time `jax_step` on the campfire world (speed baseline). Record `timeout 120 git diff -- src/environment/dashboard | sha1sum` (D16). | untouched |
| **1** | Write `scripts/fixtures/generate_thermal_rate_scale_fixture.py`. `git worktree add --detach /tmp/gwp_prescale_baseline <Step-0 SHA>`. Run the generator with `--src-root /tmp/gwp_prescale_baseline`. `git worktree remove /tmp/gwp_prescale_baseline`. Add the `SCRIPTS_DEPENDENCY_MAP.md` row. **Commit 1.** | untouched (new files only) |
| **2** | Write `tests/env/test_thermal_rate_scales.py`. Run it against the unchanged code and record per-test pass/fail (CP2). Do not commit. | untouched |
| **3** | Add the keys to `default.yaml` and the two archived thermal-on worlds. Re-run Appendix B: counts must be identical to Step 0. | **yes**: the loader ignores unknown keys (A5.1) |
| **4** | **First** re-run the foreign-edit check (`timeout 120 git diff -- src/environment/config_loader.py src/environment/state.py src/environment/core.py` and `timeout 120 git diff --cached --name-only`). Any hunk that is not this plan's is a stop (D16). Then apply the `config_loader.py` edit and the `state.py` edit **back-to-back, with nothing run in between**. | A process that *starts* in the seconds between the two edits fails loudly with a `TypeError` on `EnvParams(...)`. No silent wrong behaviour is possible, and a restart fixes it. There is no zero-window order without adding a default value, which the no-fallback rule forbids. |
| **5** | Edit `core.py`. Re-take the CP5 jaxpr SHA-1s: they must equal Step 0. Run T01 and the pre-change test list. | yes |
| **6** | Run the new test file (all pass) and the pre-change list (identical to Step 0, under the D16 attribution rule). Record the dashboard diff hash again. Take the speed measurement. | yes |
| **7** | Docs: `CONFIG_GUIDE.md`, `02_config_schema.md`, `CONFIG_CRITICAL_SETTINGS.md`, `05_body_homeostasis.md`. Update this doc's Implementation Report. | yes |
| **8** | Foreign-edit check (CP10), then **commit 2** with an explicit pathspec. | yes |

### Pre-change test list (Step 0; recorded again at Step 6)

Run each in its own process, and record `passed / failed / skipped / errors` for each:

```bash
cd /media/nas01/projects/Interoceptive-AI/grid_world_pain
for f in test_thermal_body test_thermal_validation test_thermal_field test_thermoception \
         test_thermal_reward_gate test_thermal_rendering test_body_temperature_observation \
         test_metabolic_coupling test_thermal_parity test_unified_parity test_visual_parity \
         test_extero_noc_parity test_recovery_in_bush test_no_recompile test_dashboard_layout \
         test_config_layer_silent_failures_20260723 test_backward_compat_configs \
         test_maintained_worlds_bush_blocks_animals; do
  echo "== $f"
  JAX_PLATFORMS=cpu timeout 3600 /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
      -m pytest "tests/env/$f.py" -q -p no:cacheprovider 2>&1 | tail -3
done
```

Why these files:
- **Thermal suite and archived-world loaders:** the first 8.
- **Every byte-identity gate:** `metabolic_coupling`, `thermal_parity`, `unified_parity`, `visual_parity`, `extero_noc_parity`.
- **The other static-gate graph test on `update_body`:** `recovery_in_bush`.
- **Recompile behaviour:** `no_recompile`.
- **Loaders of level 05:** `dashboard_layout`, `config_layer_silent_failures`.
- **Globs over maintained and archived worlds, including thermal-on ones:** `backward_compat_configs`, `maintained_worlds_bush_blocks_animals` (D18).

**Foreign-code exposure (D16):** `test_thermal_rendering` and `test_dashboard_layout` import `src/environment/dashboard/*`, which carries another session's uncommitted edits.

`test_thermal_rendering.py` is *run* only. Renderer files are not edited.

**Retry rule (EMFILE).** If a run dies with `OSError: [Errno 24] Too many open files`, or a git command fails the same way, wait 5 s and retry, up to 5 times, before calling it broken. Wrap git in `timeout 120`. Never kill the `bfs` processes, and never delete `.git/index.lock`.

### File Changes

#### `scripts/fixtures/generate_thermal_rate_scale_fixture.py` (new)

Model it on `scripts/fixtures/generate_metabolic_coupling_fixture.py`: CPU pin before any JAX import, the `--src-root` import mechanism and `_provenance_sha` stamping. Differences from that script:
- **`--src-root` is required** (argparse `required=True`, no default), so re-baselining from the working tree takes a deliberate act.
- It builds four uniform-field worlds from `<src-root>/configs/environment/experiment/archive/thermal/campfire_world.yaml`. The transformation is copied verbatim from `tests/env/test_thermal_body.py::_uniform_field_config` (lines 58–87): `use_object_sources=False`, `use_random_spots=False`, `default_temp=[c, c]`, `entities=[]`, only campfire obstacles, only food resources, `max_steps=500`, `body.metabolic_cost=0.0`.

| Scenario | Cell temp | Start body temp | Coupling | What it exercises |
|---|---|---|---|---|
| `warm_off` | +10.0 | −14.0 | off | warming only (`T* = +8`) |
| `cool_off` | −10.0 | +14.0 | off | cooling only (`T* = −8`) |
| `warm_on` | +10.0 | −14.0 | `metabolic_coupling: true`, `metabolic_coupling_rate: 1.0` | warming, drain changes sign when crossing 0 |
| `cool_on` | −10.0 | +14.0 | same | cooling, drain changes sign when crossing 0 |

For each scenario:
1. `state = jax_reset(params, PRNGKey(0))`, then `state = state.replace(body_temp=jnp.asarray(T0, dtype=state.body_temp.dtype))`.
2. Take 150 steps of action `4` (REST) through `jax_step`.
3. Record `"<name>.body_temp"` `[151]`, `"<name>.nutrition"` `[151]`, `"<name>.done"` `[150]`, `"<name>.termination_reason"` `[150]` and `"<name>.ate_food"` `[150]`.
4. Record `_provenance_sha`, the `git rev-parse HEAD` of `--src-root`.

**Non-vacuity asserts in the generator:**
- `warm_*` has ≥ 100 strictly positive `np.diff(body_temp)`.
- `cool_*` has ≥ 100 strictly negative diffs.
- No `done` in any scenario.
- `ate_food` is False on every step of every scenario. If the uniform world lets a resting agent eat (food kept by the copied transformation), change the scenario world **before capture**, in both the generator and the test, so the agent cannot touch food. Settle this at Step 1; after capture the fixture is frozen.
- `nutrition[-1]` of each `*_on` is lower than its `*_off` twin by > 1.0.

The scenario table, `SEED = 0`, `N_STEPS = 150` and `REST = 4` are duplicated in the test, and each file's docstring says so (the `generate_metabolic_coupling_fixture.py` precedent).

Output: `tests/env/fixtures/thermal_rate_scales/single_rate_rollouts.npz`.

#### `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (around line 216)

Add a row directly below `generate_metabolic_coupling_fixture.py`, in the same style:
- Caller: "named in the docstring of `tests/env/test_thermal_rate_scales.py` only (not invoked)."
- Added 2026-09-17 by [[warming_cooling_rate_scales]]. Hand-run once with `--src-root` (required) pointed at a worktree of the pre-change tip.
- Writes `tests/env/fixtures/thermal_rate_scales/single_rate_rollouts.npz`.
- Its scenario table, SEED, N_STEPS and REST are duplicated in the test: change one, change the other.
- Imports `src/utils/config.py`, `src/environment/config_loader.py` and `src/environment/core.py` (`jax_reset`, `jax_step`).
- Kind: HAND. Depth: already at `scripts/fixtures/` depth.

#### `configs/environment/default.yaml` (thermal block, between `k_metabolic: 0.0` at line 328 and `metabolic_coupling: false` at line 329)

```yaml
  k_metabolic: 0.0
  # Separate warming and cooling SPEEDS. Each step the body's temperature would
  # change by  d = k_exchange*(T_field - T) + k_metabolic - k_loss*(T - temperature_setpoint);
  # the change actually applied is  scale*d, with warming_rate_scale when d > 0
  # (temperature rising this step) and cooling_rate_scale otherwise. Scaling the
  # WHOLE step leaves every settling temperature exactly where it was; only how
  # fast the body gets there changes. "Warming" follows the direction of the step,
  # so a warming scale above 1 also makes the fire burn faster.
  # 1.0 / 1.0 is exactly the single-rate body (the scaled branch is not compiled).
  # Equal values other than 1.0 are NOT today's behaviour: 0.5 / 0.5 halves both.
  # Validated: each > 0, and each * (k_exchange + k_loss) <= 1 (else a step
  # overshoots its settling point). A deliberate deviation from EVAAA, whose body
  # uses one rate. Read ONLY when enabled is true.
  warming_rate_scale: 1.0
  cooling_rate_scale: 1.0
  metabolic_coupling: false
```

#### `configs/environment/experiment/archive/thermal/campfire_world.yaml` (after `k_metabolic: 0.0`, line 350)
#### `configs/environment/experiment/archive/thermal/campfire_world_body_temp_hidden.yaml` (after `k_metabolic: 0.0`, line 361)

Both files get the same two lines, preceded by this comment (the `761f427f` convention):

```yaml
  # NOT a migration of the archive. This world is thermal-ON and is loaded from a
  # raw Config by eight test modules (thermal_body, thermal_field, thermal_rendering,
  # thermal_reward_gate, thermal_validation, thermoception, body_temperature_observation,
  # metabolic_coupling) and by scripts/fixtures/generate_metabolic_coupling_fixture.py;
  # `warming_rate_scale` / `cooling_rate_scale` are mandatory whenever thermal is on,
  # so without these lines those modules die at config load. 1.0 / 1.0 is the
  # single-rate body, byte-identical to before the keys existed.
  warming_rate_scale: 1.0
  cooling_rate_scale: 1.0
```

#### `src/environment/config_loader.py`

**(a) Read and validate.** Insert after the stability check (line 1558) and before `# ── Metabolic coupling (Stage 5)` (line 1560):

```python
        # ── Warming / cooling speed ───────────────────────────────────────
        # The body's per-step change  d = k_ex*(T_field - T) + k_met
        # - k_loss*(T - setpoint)  is applied as  scale*d, with the warming scale
        # when d > 0 and the cooling scale otherwise (d == 0 -> cooling; s*0 == 0
        # either way). Scaling the whole step leaves every fixed point unchanged,
        # which is why `_thermal_equilibrium` / `_thermal_structure_verdict` take
        # no scale. Conditional-mandatory under `thermal.enabled`, no fallback.
        # Plan: docs/develop/active/thermal/WARMING_COOLING_RATE_SCALES.md
        #
        # float() BEFORE the static gate in core.update_body compares against 1.0,
        # so YAML `1` and `1.0` trace the same graph.
        _th_warming_scale = float(config.get_mandatory('thermal.warming_rate_scale'))
        _th_cooling_scale = float(config.get_mandatory('thermal.cooling_rate_scale'))
        for _key, _scale, _direction in (
                ('thermal.warming_rate_scale', _th_warming_scale, 'warming'),
                ('thermal.cooling_rate_scale', _th_cooling_scale, 'cooling')):
            # Written as `not (x > 0)` so a YAML .nan is refused too.
            if not (_scale > 0.0):
                raise ValueError(
                    f"{_key} must be > 0 (it multiplies the body's per-step "
                    f"temperature change while {_direction}; 0 would freeze the body "
                    f"in that direction and a negative value would reverse it), "
                    f"got {_scale}.")
            if not (_scale * (_th_k_exchange + _th_k_loss) <= 1.0):
                raise ValueError(
                    f"{_key} * (thermal.k_exchange + thermal.k_loss) must be <= 1 "
                    f"({_scale} * ({_th_k_exchange} + {_th_k_loss}) = "
                    f"{_scale * (_th_k_exchange + _th_k_loss)}); above 1 a "
                    f"{_direction} step overshoots the body's settling temperature "
                    f"and the approach stops being monotone, which the load-time "
                    f"structure check relies on.")
```

**(b) Inert values when thermal is off.** In the `else:` branch, directly after `_th_k_exchange, _th_k_loss, _th_k_metabolic = 0.0, 0.0, 0.0` (line 1630):

```python
        # Warming / cooling speed, inert. 1.0 / 1.0 is the value at which
        # `update_body`'s static gate traces the single-rate lines verbatim; it is
        # never read on a thermal-off config anyway (the whole body block sits
        # behind `if params.thermal_enabled:`).
        _th_warming_scale, _th_cooling_scale = 1.0, 1.0
```

**(c) Pass to `EnvParams`.** Directly after `thermal_k_metabolic=_th_k_metabolic,` (line 2332):

```python
        thermal_warming_rate_scale=_th_warming_scale,
        thermal_cooling_rate_scale=_th_cooling_scale,
```

No other loader change. `_thermal_equilibrium`, `_thermal_single_fire_field`, `_thermal_radial_equilibria`, `_thermal_structure_verdict` and `_check_thermal_structure` (`config_loader.py:428-707`) and their call at line ~2059 **stay unmodified** (§A2).

#### `src/environment/state.py` (after `thermal_k_metabolic: float`, line 395)

```python
    # Warming / cooling speed. The recurrence's per-step change d is applied as
    # scale*d: `thermal_warming_rate_scale` when d > 0, `thermal_cooling_rate_scale`
    # otherwise. STATIC (pytree_node=False), like `recovery_in_bush_multiplier`:
    # `core.update_body` gates on `== 1.0` for both at trace time, so at 1.0 / 1.0
    # the scaled branch contributes no operation to the graph and the body update
    # is the single-rate lines verbatim. The gate is derived from the two values
    # themselves (no separate bool), so a `.replace()` of either scale can never
    # be silently ignored. Not part of the curriculum modality fingerprint: they
    # change dynamics, not what an observation dimension means. Inert 1.0 when
    # `thermal_enabled` is False.
    thermal_warming_rate_scale: float = struct.field(pytree_node=False)
    thermal_cooling_rate_scale: float = struct.field(pytree_node=False)
```

Before inserting, confirm that the neighbouring field block has no default values. Fields without defaults may not follow fields with them, and the thermal block has none today (`state.py:353-431`).

#### `src/environment/core.py`

**(a) Body recurrence** (`core.py:299-306`).

BEFORE:
```python
    if params.thermal_enabled:
        cell_temp = state.thermal_field[new_agent_pos[0], new_agent_pos[1]]
        new_body_temp = (
            state.body_temp
            + params.thermal_k_exchange * (cell_temp - state.body_temp)
            + params.thermal_k_metabolic
            - params.thermal_k_loss * (state.body_temp - params.temperature_setpoint)
        )
```

AFTER:
```python
    if params.thermal_enabled:
        cell_temp = state.thermal_field[new_agent_pos[0], new_agent_pos[1]]
        # Warming / cooling speed. STATIC gate on two static floats (cast with
        # float() at load, so YAML `1` == 1.0). At 1.0 / 1.0 the four lines below
        # are character-for-character the single-rate code and the scaled branch
        # does not exist in the traced graph, so bit-parity with every run that
        # predates the keys is a property of the source (same discipline as the
        # Stage 5 drain and recovery_in_bush_multiplier). Equal values other than
        # 1.0 take the scaled branch: 0.5 / 0.5 is a uniform slow-down.
        if (params.thermal_warming_rate_scale == 1.0
                and params.thermal_cooling_rate_scale == 1.0):
            new_body_temp = (
                state.body_temp
                + params.thermal_k_exchange * (cell_temp - state.body_temp)
                + params.thermal_k_metabolic
                - params.thermal_k_loss * (state.body_temp - params.temperature_setpoint)
            )
        else:
            # Scale the WHOLE per-step change, never one term of it. d is linear
            # in T with d == 0 exactly at the cell's fixed point T*, so scaling d
            # leaves T* where it was: one settling temperature per cell, reached
            # from above or below. Scaling k_exchange alone would move T* by the
            # direction of arrival. The branch follows the sign of THIS step's
            # change (d > 0 warming, else cooling; at d == 0, s*0 == 0 either way),
            # not the body's position relative to the setpoint or the cell.
            body_temp_change = (
                params.thermal_k_exchange * (cell_temp - state.body_temp)
                + params.thermal_k_metabolic
                - params.thermal_k_loss * (state.body_temp - params.temperature_setpoint)
            )
            rate_scale = jnp.where(body_temp_change > 0.0,
                                   params.thermal_warming_rate_scale,
                                   params.thermal_cooling_rate_scale)
            new_body_temp = state.body_temp + rate_scale * body_temp_change
```

The rest of the block (the `thermal_death` computation and the `done` fold) is unchanged. Also add, directly after the existing formula comment at `core.py:287-289`, one line: `#   (applied as scale*d with a warming / cooling scale — see below)`.

**(b) Drain comment** (`core.py:182-186`). The code does not change. Extend the "`state.body_temp` is the PRE-step temperature" paragraph with:

```python
        # NOT scaled by thermal.warming_rate_scale / cooling_rate_scale (plan D3).
        # Those scales follow the SIGN of the body's net step d. The field is fixed
        # within an episode, so a body settled in one cell recomputes the same d
        # every step, and at the settled point the sign of d is set by float
        # rounding: usually frozen at the direction the body arrived from,
        # occasionally alternating. The defence term k_loss*(T - setpoint) is not
        # zero there, so a bill scaled by that sign would be path-dependent or
        # jittery: two settled bodies 1.6e-5 degrees apart could pay bills that
        # differ by the full warming/cooling ratio, depending only on history.
        # This bill is instead a continuous function of body state: a per-step
        # (per-decision) cost, which equals a per-degree-moved cost only at
        # 1.0 / 1.0. Defensible, not the only defensible choice: the alternatives
        # (bill x scale, or a switch on the defence direction sign(setpoint - T))
        # are recorded for OPEN_WORK_HANDOFF E1(a) in the plan.
        # Pinned by tests/env/test_thermal_rate_scales.py.
```

#### `tests/env/fixtures/thermal_rate_scales/single_rate_rollouts.npz` (new; produced by Step 1, never regenerated from the working tree)

#### `tests/env/test_thermal_rate_scales.py` (new)

Header:
- Module docstring: plain-language purpose, the generator's name, and the "do not regenerate from the working tree" warning.
- `import os; os.environ.setdefault("JAX_PLATFORMS", "cpu")`, belt-and-braces with the conftest.
- `jax.config.update("jax_log_compiles", True)`, needed by T14 and harmless alone in its process.

Helpers:
- `_campfire_dict()`, which loads the live archived world.
- `_uniform(cell, **thermal_overrides)`, the same transformation as the generator plus overrides.
- `_params(d)`: `p = load_env_params(Config(d))`. **Read `w, c = p.thermal_warming_rate_scale, p.thermal_cooling_rate_scale` first**, before touching the dict, so pre-change the failure is the predicted `AttributeError` and not a `KeyError` from a dict that has no keys yet. Then, if `d["thermal"]["enabled"]`, assert `p.thermal_warming_rate_scale == float(d["thermal"]["warming_rate_scale"])` and the same for cooling; otherwise assert both are `1.0`. Also assert both are `float`. Return `p`. **Every successful load outside T01 goes through this helper** (D15); sub-cases that expect a load to raise call `load_env_params(Config(d))` directly (D20). T01 uses `_params_raw(d) = load_env_params(Config(d))`, whose docstring says why.
- `_rest_rollout(params, T0, n)`, which mirrors the generator.
- `_update_body_trace(params, T0, cell_pos, n)`, which iterates `update_body` directly: `state = state.replace(body_temp=new_bt)`, info `{"ate_food": False, "damage": 0.0, "rested": True}` as in `test_recovery_in_bush.py:213-221`, jitted over a `lax.scan`. This isolates the recurrence from episode termination, so equilibria past the death line (the fire) can be reached.
- `_oracle(cell, T0, k_ex, k_loss, k_met, setpoint, ws, cs, n)`: **a two-rate NumPy float64 recurrence written from this plan's equation, importing nothing from `src/`.** `d = k_ex*(cell - T) + k_met - k_loss*(T - setpoint)`; `T = T + (ws if d > 0 else cs) * d`.
- `_closed_form_T_star(...) = (k_ex*Tf + k_loss*set + k_met) / (k_ex + k_loss)`, written inline, **not** imported from `config_loader`.

Tests. Each reference is independent of the code under test.

| ID | Name | Requirement covered | Reference and assertion |
|---|---|---|---|
| **T01** | `test_single_rate_is_byte_identical_to_pre_change_fixture` | every fixture byte-identical at 1.0/1.0 | Load with `_params_raw` (D15). Rebuild the four scenarios from the live configs, which now carry 1.0/1.0, and compare with `np.array_equal` on every array in the pre-change `.npz`. No tolerance. On failure, report max \|diff\| and `_provenance_sha`. Also assert the fixture is non-vacuous (the same asserts as the generator), so the gate cannot pass by comparing nothing. |
| **T02** | `test_gate_is_off_at_one_and_on_just_above_one` | gate off at 1.0/1.0, on at 1.0/1.0000001 | `jax.make_jaxpr(lambda p: update_body(state, info, p, pos))(params)` on the campfire world at (1.0, 1.0), at YAML ints (1, 1), and at (1.0, 1.0000001), (1.0000001, 1.0) and (0.5, 0.5). Assert: `str(jaxpr)` at (1.0, 1.0) **equals** that at (1, 1). Each of the other three **differs** from it and has strictly more `select_n` equations and at least as many `gt` equations (counted over `jaxpr.jaxpr.eqns` by `eqn.primitive.name`). The loaded params' `thermal_warming_rate_scale` has type `float` in every case. |
| **T03** | `test_equal_non_unit_scales_are_not_todays_behaviour` | 0.5/0.5 differs | The `warm_off` and `cool_off` scenarios at (0.5, 0.5). Assert the trajectory differs from the fixture by > 1e-2 at some step, and matches `_oracle(..., 0.5, 0.5)` with `atol=2e-4` (the Stage 2 precedent tolerance). |
| **T04** | `test_equilibrium_unchanged_from_above_and_below_ring_and_fire` | equilibria unchanged, from above and below, ring and fire | Use the campfire world at `PRNGKey(0)`. Fire cell = `argmax(state.thermal_field)`. Ring cell = an in-bounds Manhattan-1 neighbour. For scale pairs (1.0, 1.0), (3.0, 0.3), (0.3, 3.0), and body starts above and below (ring: `T*−22` / `T*+14`; fire: `T*−40` / `T*+15`), run `_update_body_trace` for 4000 steps. Assert: final value within 2e-3 of `_closed_form_T_star(field value at that cell)`; above-start and below-start finals agree within 2e-3; each scaled final agrees with the (1.0, 1.0) final within 2e-3; **no step crosses `T*`** (the sign of `T_t − T*` is constant until \|e\| < 2e-3). **Discriminator (D15):** for each scaled pair and start, the scaled trajectory differs from the (1.0, 1.0) trajectory from the same start by > 1e-2 at some step, so the scale was applied. Log the four `T*` values; at `PRNGKey(0)` they need not equal the midpoint-corner numbers +57.93 / +8.09. |
| **T05** | `test_equilibrium_unchanged_at_extreme_ratio_and_general_fixed_point` | extreme ratio; nonzero `k_metabolic` and setpoint | Uniform cell −10 with `k_metabolic: 0.3`, `temperature_setpoint: 5.0` (inside [−15, 15]) and scales (20.0, 0.2), then (0.2, 20.0). That is ratio 100, with `20*0.05 = 1.0` on the stability boundary, so the fast side converges in one step. Starts at `T*±12`, 4000 steps. The same four assertions as T04, plus T04's discriminator: each scaled trajectory differs from the (1.0, 1.0) trajectory from the same start by > 1e-2 at some step. **Float32 note for the developer:** the slow side at `s·K = 0.01` stalls within about 2e-4 of `T*` from rounding, which is why the tolerance is 2e-3. Do not pick 0.05 for the slow side: at `s·K = 0.0025` the stall (~8e-4) reaches the tolerance. |
| **T06** | `test_whole_step_scaled_with_zero_exchange` | whole step scaled, `k_exchange = 0` | Uniform cell −10, `k_exchange: 0.0`, `k_loss: 0.05`, setpoint 0, scales (1.0, 0.5), `T0 = +10`, one `update_body` step. Expect **9.75**, which is `10 + 0.5*(−0.5)`. Assert it is not 9.5, the value if only `k_exchange` were scaled, which is also today's value. |
| **T07** | `test_whole_step_scaled_with_metabolic_heat` | whole step scaled, `k_metabolic` nonzero | Uniform cell 0, `k_exchange: 0.0`, `k_loss: 0.05`, `k_metabolic: 0.3`, setpoint 0, scales (2.0, 1.0), `T0 = 0`. One step gives **0.6**, not 0.3. Also run a case with all three terms non-zero against the hand formula, `atol=1e-5`. |
| **T08** | `test_scale_is_chosen_by_sign_of_the_step` | correct scale by sign | Uniform cell −10 (`T* = −8`), scales (3.0, 0.5). `T0 = −14` (below `T*`, warming): expect **−13.1**, and the wrong branch would give −13.85. `T0 = −2` (**below the setpoint and above the cell, yet cooling** because it is above `T*`): expect **−2.15**, and the wrong branch would give −2.9. `T0 = +14` (cooling): hand value. Each at `atol=1e-5`. |
| **T09** | `test_zero_step_stays_put` | `d == 0` branch stated | Uniform cell −8, `k_exchange: 0.5`, `k_loss: 0.5`, setpoint 0, scales (1.0, 0.5), `T0 = −4`. Here `d = −2 + 2 = 0` exactly in float32, so the next value is **exactly** −4.0. |
| **T10** | `test_scaled_rollouts_match_two_rate_oracle` | whole-trajectory reference | All four fixture scenarios at (3.0, 0.3): `body_temp` matches `_oracle` at `atol=2e-4`. Assert it differs from the fixture (non-vacuous). |
| **T11** | `test_metabolic_drain_is_not_scaled` | pins D3 | The `warm_on` and `cool_on` scenarios at (3.0, 0.3). From the **recorded** `body_temp[t]`, compute `expected_nutrition[t+1] = clip(nutrition[t] − rate·abs(k_loss·(body_temp[t] − setpoint)), 0, max_nutrition)`, with `metabolic_cost = 0`. First assert `info["ate_food"]` is False on every step, so the formula applies. Then assert a match at `atol=1e-4`. **Discrimination:** also compute the scaled-drain alternative and assert the recorded series is > 1e-2 away from it at some step. **Scales applied (D15):** assert the recorded `body_temp` differs from the fixture's matching `*_on` series by > 1e-2 at some step, as T10 does. |
| **T12** | `test_conditional_mandatory` | thermal-off loads without keys; thermal-on missing either raises | **Order inside the function: (a), (b), (c), (d).** (a) The `default.yaml` dict (`enabled: false`) with both keys removed via `d["thermal"].pop(key, None)`, **never `del`**, because at Step 2 the keys do not exist yet and `del` would raise `KeyError`. It loads through `_params`, and the loaded fields are `1.0` (the helper's thermal-off branch). (b) The campfire dict with `warming_rate_scale` removed via `pop(key, None)`: `with pytest.raises(ValueError) as exc: load_env_params(Config(d))`, **called directly, not through `_params`** (D20). The message contains `thermal.warming_rate_scale`. (c) The same for `cooling_rate_scale`, removed the same way and also calling the loader directly. The message contains `thermal.cooling_rate_scale`. (d) YAML `1` (int) for both keys loads through `_params` as `float` `1.0`. *(Revision 2: `pop` in (a)–(c); (b) and (c) call the loader directly.)* |
| **T13** | `test_stability_and_positivity_checks_fire_per_key` | stability check per scale; also covers the untested existing check | All sub-cases use a uniform cell, where the structure check is skipped. **Every sub-case that expects a raise calls `load_env_params(Config(d))` directly inside `with pytest.raises(ValueError) as exc:`, never through `_params`** (D20): the raise *is* the assertion, and the helper's field read on a load that must fail would only let an `AttributeError` escape `pytest.raises` on pre-change code. **Order inside the function (Revision 2):** (1) `k_exchange: 0.25`, `k_loss: 0.25` (so `K = 0.5` exactly), warming 2.001 with cooling 1.0: raises, and the message names `thermal.warming_rate_scale` and not `cooling`. (2) The mirror: cooling 2.001 with warming 1.0 raises, naming `thermal.cooling_rate_scale` and not `warming`. (3) For each key, 0.0, −1.0 and `float('nan')`, with the other scale at 1.0: each raises with that key named. (4) The existing check: `k_exchange: 0.6`, `k_loss: 0.6` raises with `thermal.k_exchange + thermal.k_loss must be <= 1`, even at scales (0.5, 0.5), confirming D5 kept it. (5) **Last**, the boundary: `K = 0.5` with warming 2.0 and cooling 1.0 **loads through `_params`**, since `2.0*0.5 == 1.0` is on the boundary, and the helper confirms the loaded values. |
| **T14** | `test_jitted_episode_unequal_scales_no_nan_no_recompile` | jitted episode runs, no NaN, no per-step recompile | The archived campfire world at (3.0, 0.3), `PRNGKey(0)`, and the `ACTIONS` sequence from `test_metabolic_coupling.py` (300 steps) through `jax_step`, inside the log-capture counter pattern of `tests/env/test_no_recompile.py:199-230` (copy the class; do not import from another test module). Assert: count is 1 after step 1 and still 1 after step 300; every `state.body_temp` is finite and float32; `thermal_field` is finite. **Discriminator (D15):** the same 300 actions at (1.0, 1.0) from the same key give a `body_temp` series that differs from the (3.0, 0.3) series by > 1e-2 at some step. The (1.0, 1.0) run happens **outside** the compile-counter context, because it is a different static configuration and compiles once on its own. |

**Non-vacuity requirement (CP2), rewritten in Revision 1 with one prediction per test.** At Step 2 the new test file is run against the unchanged code, with the Step-3 config keys **not yet added**. The developer records each test's outcome **and the exception type or assertion that fired**, and compares it with this table:

| Test | Predicted pre-change outcome | Why |
|---|---|---|
| T01 | **PASS** | `_params_raw` reads no new field; the fixture *is* this code. **If T01 fails, stop:** the fixture does not match its source. |
| T02 | FAIL, `AttributeError` (`thermal_warming_rate_scale`) from `_params` | The helper reads the new field. Underneath, all five jaxprs would be identical. |
| T03 | FAIL, `AttributeError` from `_params` | Underneath, 0.5/0.5 would equal the fixture. |
| T04 | FAIL, `AttributeError` from `_params` | Underneath, the equilibrium assertions would **pass** and only the D15 discriminator would fail. |
| T05 | FAIL, `AttributeError` from `_params` | Same as T04. |
| T06 | FAIL, `AttributeError` from `_params` | Underneath, the value would be 9.5, not 9.75. |
| T07 | FAIL, `AttributeError` from `_params` | Underneath, 0.3, not 0.6. |
| T08 | FAIL, `AttributeError` from `_params` | Underneath, the unscaled values (−13.7, −2.3). |
| T09 | FAIL, `AttributeError` from `_params` | **The helper is the only reason it fails**: `d == 0` stays put with or without the feature. That is expected, not a vacuity defect. T09 documents the branch; it does not discriminate it. |
| T10 | FAIL, `AttributeError` from `_params` | Underneath, the trajectory would equal the fixture, not the oracle. |
| T11 | FAIL, `AttributeError` from `_params` | Underneath, the drain formula would **pass** and only the D15 "body_temp differs from fixture" check would fail. |
| T12 | FAIL, `AttributeError: 'EnvParams' object has no attribute 'thermal_warming_rate_scale'`, from `_params` in part (a) | *(Revision 2; traced on the pre-change tree.)* (a) runs first. `pop(key, None)` is a no-op because the keys don't exist yet, so there is no `KeyError`. The pre-change loader loads the thermal-off dict, and the helper's first field read raises `AttributeError`. Underneath, (b) and (c) call the loader directly inside `pytest.raises` and fail with `Failed: DID NOT RAISE <class 'ValueError'>`; (d) fails with `AttributeError`. With the old `del`, (a) raised `KeyError: 'warming_rate_scale'` instead. |
| T13 | FAIL, `Failed: DID NOT RAISE <class 'ValueError'>` from sub-case (1) | *(Revision 2; traced on the pre-change tree.)* Sub-case (1) calls the loader directly. The pre-change loader has no scale reads or checks, and the uniform dict passes its existing checks (`K = 0.5 <= 1`, structure check skipped), so the load succeeds and `pytest.raises` reports `DID NOT RAISE`. Nothing reads a new field before that point, so no `AttributeError` can come first. Sub-cases (2) and (3) would also give `DID NOT RAISE`, (4) passes pre-change, and (5), through `_params`, would give `AttributeError`. That is why (5) is last. Had the raise cases gone through `_params`, the first failure would be `AttributeError` in any order: the old wording's defect, reproduced. |
| T14 | FAIL, `AttributeError` from `_params` | Underneath, the episode is finite with one compile, and only the D15 discriminator would fail. |

**Stop rule:** a mismatch in pass/fail, or a different exception type from the one predicted, is a stop-and-report. The one exception: if a test predicted to fail on `AttributeError` instead fails earlier on a config-loading error that names a **different** key, record it and investigate. That is a foreign or config problem, not a vacuity finding.

#### `docs/environment/CONFIG_GUIDE.md` §3.9

- **YAML example** (lines 283–300): after `k_metabolic: 0.0`, add `warming_rate_scale: 1.0   # multiplies the per-step change while the body warms` and `cooling_rate_scale: 1.0   # … while it cools; 1.0 / 1.0 = single-rate body`.
- **New bullet** after the `k_loss` bullet (which ends at line ~363): **"`warming_rate_scale` / `cooling_rate_scale` change speed, never where the body settles."** Content:
  - the `scale·d` rule and the sign semantics, including "warming also speeds the fire";
  - that 1.0/1.0 is byte-identical and not even compiled;
  - that equal non-1.0 values are a uniform slow-down, not today's behaviour;
  - the per-scale `<= 1` bound and why (monotone approach, which the structure check relies on);
  - that the drain is not scaled (D3);
  - the EVAAA deviation;
  - a link to this plan.
- Change "Six things that bite" to "Seven things that bite".
- **Validation paragraph** (line ~372): after "`k_exchange` and `k_loss` each `>= 0` and summing to `<= 1`", add ", `warming_rate_scale` and `cooling_rate_scale` each `> 0` with `scale · (k_exchange + k_loss) <= 1` per key".

#### `docs/environment/02_config_schema.md`

- **`thermal:` keys table** (lines 66–80): add two rows after `food_min_fire_distance`:
  - `` `warming_rate_scale` `` \| `thermal_warming_rate_scale` \| **yes** \| `> 0`; `× (k_exchange + k_loss) <= 1` \| multiplies the body's per-step temperature change when it is positive; 1.0 = single-rate. Conditional-mandatory under `enabled`
  - the mirror row for `cooling_rate_scale` ("… when it is zero or negative").
- **Conditional-mandatory list** (lines 1275–1279): add `thermal.warming_rate_scale` and `thermal.cooling_rate_scale`.
- **Structure-check section** (after the `T*` formula paragraph, line ~209): add one sentence. "The two rate scales do not enter this check: they multiply the whole per-step change, so the fixed point is the same, and the per-scale `<= 1` bound keeps the approach monotone."

#### `docs/environment/CONFIG_CRITICAL_SETTINGS.md`

- **Registry row** (after the `thermal.k_loss` row, line 22):
  - Setting: `` `thermal.warming_rate_scale` / `thermal.cooling_rate_scale` ``
  - Value: **1.0 / 1.0**
  - Set in: `default.yaml`
  - Meaning:
    - Separate warming and cooling speeds. Each multiplies the body's whole per-step change `d` (warming when `d > 0`, cooling otherwise), so every settling temperature is unchanged and only the time to reach it moves.
    - **1.0 / 1.0 is byte-identical to the single-rate body.** Equal values other than 1.0 are a uniform slow-down and **not** today's behaviour.
    - "Warming" follows the step's direction, so a warming scale above 1 also makes the fire kill sooner.
    - Validated `> 0` and `scale·(k_exchange + k_loss) <= 1` per key.
    - A documented deviation from EVAAA (single rate).
    - The ecological literature figures are unverified; `research-postdoc` should check them before any paper claim.
    - Read only when `thermal.enabled`.
- **Change-log entry** (the newest entry, inserted above the current first entry at line 36). Title: **2026-09-17 — new conditional-mandatory keys `thermal.warming_rate_scale` and `thermal.cooling_rate_scale`, shipped at 1.0 / 1.0 (separate warming and cooling speeds)**. Body:
  - **Reason:** the user's targets (away 80–110 steps, rewarm ≤10, fire death by step 2–3) were infeasible together across ~120,000 single-rate configs.
  - **Design:** scaling the whole step (not `k_exchange`) keeps every equilibrium. The static gate makes 1.0/1.0 graph-identical: jaxpr SHA-1s before/after, and the pre-change fixture byte-identical.
  - **EVAAA deviation**, citing `InteroceptiveAgent.cs:860-878`.
  - **Ecology:** plausible in kind; the ratio is a model choice; literature unverified.
  - **Migration:** `default.yaml` plus two archived thermal-on worlds; 05/06 inherit.
  - **Before/after load counts** from Appendix B, **naming the population**: "tracked `configs/environment/**/*.yaml`, standalone = no `extends:` key". State that this differs from the 2026-09-16 entry's whole-`configs/` population (L1), so nobody compares the two.
  - **Saved runs affected:** 0 of 503.
  - **Drain not scaled** (D3), with the corrected reason: path dependence or jitter at settled equilibria. Say it is defensible but not the only choice, and name both alternatives deferred to E1(a).
  - **Commit** and **blast radius:** none at shipped values.

#### `docs/environment/05_body_homeostasis.md` ("Body Temperature (thermal)", lines ~494–565)

- **After the recurrence equation:** a short paragraph and a display equation, `T_{t+1} = T_t + s \, d_t`, with `s` = warming scale if `d_t > 0` else cooling scale. Then add both keys to the constants table.
- **"Tug-of-war" section:**
  - one sentence that the fixed point is unchanged by the scales;
  - replace "The gap to the fixed point shrinks by a factor `(1 − k_exchange − k_loss)` per step" with "… by `(1 − s·(k_exchange + k_loss))` per step, with `s` the scale for the direction of travel; the time constant is `1/(s·(k_exchange + k_loss))`, 20 steps at 1.0";
  - the "warming also speeds the fire" sentence.
- **"Metabolic coupling" section, after "Which `T`.":** a paragraph titled "Not scaled by the warming / cooling speeds", carrying D3's corrected reasoning in plain language:
  - within an episode the field is fixed, so at a settled body temperature the direction of the step is set by rounding, usually frozen at the arrival direction and occasionally alternating;
  - a bill scaled by that direction would be path-dependent or jittery;
  - the unscaled bill is a continuous per-step cost, equal to a per-degree-moved cost only at 1.0 / 1.0;
  - under it, a faster rewarm costs less total nutrition;
  - it is defensible but not the only choice: name the time-dilation reading (bill × scale) and the defence-direction switch (`sign(setpoint − T)`), both deferred to E1(a).

#### `docs/develop/active/issues/OPEN_WORK_HANDOFF.md` (E1, append one line; cross-link in the other direction)

At the end of the E1 bullet: `  - 2026-09-17: [[warming_cooling_rate_scales]] adds two speed multipliers to the thermal block (shipped 1.0/1.0). It does not resolve E1; note that the metabolic drain is deliberately left unscaled while the body moves at scale·rate (that plan's D3), which E1(a)'s calibration should take into account.`

**The senior-developer adds this line when the plan is approved, not the developer.** It is listed here only so the verifier checks it.

**Not changed:**
- `docs/develop/INDEX.md` (D10).
- Renderer / dashboard files.
- `basic/05-*`, `basic/06-*` (D6).
- `sim.py` and `thermal_sandbox_oracle.py` (D7).
- `test_metabolic_coupling.py`, `test_thermal_body.py` and `test_thermal_validation.py`: they are unchanged and must pass unchanged.
- `config_loader.py:428-707`, the fixed-point helpers (§A2).

---

## Checkpoints

- [x] **CP1: Step-0 baseline recorded.** Record the HEAD SHA; the dashboard foreign-diff hash (D16); the pre-change test table (per-file passed/failed/skipped/errors); Appendix B counts; the three jaxpr SHA-1s; and the `jax_step` timing on the campfire world at 1.0/1.0 (≥ 5 alternating repetitions of ≥ 500 steps after one warm-up; report the median and spread, per the `761f427f` lesson that 3 repetitions misled). *Done: HEAD `1b5d1ed5`; dashboard diff `12ee6249…`; all 18 files green (table in the Implementation Report); 118/27 and 217/211; three SHA-1s; 30,126 SPS median.*
- [x] **CP2: new tests behave as predicted before the change.** The Step-2 outcomes **and exception types** match the per-test table in the non-vacuity requirement (Revision 1). **If T01 fails at Step 2, stop:** the fixture does not match the code it came from. *Done: all 14 match, T01 PASS, T13 `DID NOT RAISE` at (1), the rest `AttributeError` from `_params` (T12 in part (a)).*
- [x] **CP3: config migration is load-neutral.** After Step 3 and again after Step 5, Appendix B gives the **same** standalone and layered load counts as Step 0, and the same 4 thermal-on configs. For each of the 4, `load_env_config(path).get('thermal.warming_rate_scale')` and `...cooling_rate_scale` equal `1.0` (resolved, through the trainer's loader). After Step 4, `load_env_params` gives `float` 1.0 for both fields on all 4. *Done: identical per-file counts at Steps 3 and 5; all 4 resolve and load as float 1.0 / 1.0.*
- [x] **CP4: dtype.** After Step 5, on the campfire world at (3.0, 0.3), `jax_step`'s returned `state.body_temp.dtype == float32` and `weak_type` is unchanged from the input state. *Done: float32, `weak_type` False in and out.*
- [x] **CP5: the graph at 1.0/1.0 is literally today's.** For each config, `hashlib.sha1(str(jax.make_jaxpr(jax_step)(state, 0, params)).encode()).hexdigest()` after Step 5 **equals** the Step-0 value. Pass `params` as an **argument**, not a closure, and take `state = jax_reset(params, PRNGKey(0))`. The configs: `default.yaml` (thermal-off), the archived `campfire_world.yaml` and `basic/05-campfire_thermal_10x10.yaml` (thermal-on, the latter through `load_env_config`). **Contrast case, on the two thermal-on configs only** (a thermal-off config traces no body block, so its hash cannot move): with `thermal_warming_rate_scale=3.0` via `params.replace`, the hash **differs**. Otherwise the probe proves nothing. *Done: all three equal Step 0; the contrast differs on both thermal-on configs.*
- [x] **CP6: byte-identity gates.** At Step 6, `test_metabolic_coupling.py`, `test_thermal_parity.py`, `test_unified_parity.py`, `test_visual_parity.py` and `test_extero_noc_parity.py` give pass/skip counts **identical** to Step 0, each run alone under `JAX_PLATFORMS=cpu`. No `.npz` other than the new one appears in `git status`. *Done: identical counts; `git status -- tests/env/fixtures/` clean (the new fixture is committed in `068d791e`).*
- [x] **CP7: the whole pre-change list is unchanged.** Every file's Step-6 counts equal Step 0. A difference is a stop-and-report, never a fixture regeneration. **The one exception (D16):** if the only differences are in `test_thermal_rendering.py` and/or `test_dashboard_layout.py` **and** the dashboard foreign-diff hash changed between Step 0 and Step 6, record it as attributed to the renderer session and continue. *Done: all 18 files identical; D16 not invoked (see D23).*
- [x] **CP8: the new test file is fully green.** 14 tests passed, 0 skipped. A skip counts as a failure here (the parity-gates lesson from the wiki). *Done: 14 passed, 0 skipped.*
- [x] **CP9: speed.** Timing at 1.0/1.0 is within noise of CP1. Given CP5's identical graph, any real delta means the measurement is broken, not the code. Report gate-on (3.0, 0.3) versus gate-off for information only. *Done: 29,893 vs 30,126 SPS (−0.8%, inside the ~3% spread); gate-on 30,070.*
- [ ] **CP10: foreign edits.** Immediately before Step 4 (on `config_loader.py`, `state.py`, `core.py`; D16) and immediately before each commit, run `timeout 120 git diff -- <file>` for every file in File Changes and `timeout 120 git diff --cached --name-only`. Every hunk must be this plan's. Commit with `git commit -F msg -- <paths>`. Never `git add -A`. *Partly done: checked before Step 4 and before commit 1 (clean). The pre-commit-2 check belongs to whoever makes commit 2.*
- [ ] **CP11: docs.** `CONFIG_CRITICAL_SETTINGS.md` has both the registry row and the dated change-log entry, **in the same commit as the `default.yaml` edit**. `CONFIG_GUIDE.md`, `02_config_schema.md`, `05_body_homeostasis.md` and `SCRIPTS_DEPENDENCY_MAP.md` are updated as specified. *Docs done (row plus change-log entry written); "same commit as `default.yaml`" is pending commit 2.*

---

## Follow-ups (not stages of this plan)

- **F1: target re-search with the new keys.** The user runs this after this lands, without editing configs. The two-rate recurrence to use is `d = k_ex*(Tf − T) + k_met − k_loss*(T − set)`, `T ← T + (ws if d > 0 else cs)·d`, with the legal region `k_ex + k_loss <= 1` and `ws·K <= 1`, `cs·K <= 1` (D5). **Read §A3 first:** at today's other settings the away time varies about 1.7× across the sampled world range at any fixed cooling scale. That spread **already exists at scale 1** (38 vs 22 steps at −22 / −28). It is the gap between the far-field settling temperature and the −15 line, which no speed multiplier changes, so the feature is necessary but **not sufficient** across the sampled range, and the search will likely also need `k_loss` or the world baseline to move. **Evaluate the fire target (and the other targets) at the corners of both sampled ranges, world [−28, −22] × fire ratio [11, 13], not at the midpoint** (D19): at warming scale 2 the first fire step is lethal at −25 / 13 and −28 / 13. Remember that the warming scale also speeds fire death, and the cooling scale also slows recovery from overheating.
- **F2:** after F1 picks values, re-check the Body Temperature noise clip derivation comment in `default.yaml` (D11) against the chosen fire geometry.
- **F3: `research-postdoc`** should verify the ecological rate-asymmetry figures (§A4) before any paper claim.
- **F4: E1** (whole-block review) should account for the unscaled drain (D3) and choose among the three readings D3 records: unscaled (current), time-dilation (bill × scale, under which a rewarm's total cost does not fall as the warming scale rises), and the defence-direction switch (`sign(setpoint − T)`).
- *(Noticed, not touched:)* `CONFIG_GUIDE.md` §3.9 still says to put campfire worlds under `configs/environment/experiment/thermal/`, a path that `f3161dcc` archived. Doc drift for whoever next edits that section.

---

## Appendix B: config load sweep (run at Step 0, Step 3 and Step 5)

Save as `tmp/<YYYYMMDD_HHMMSS>_thermal_sweep.py` and run with the conda interpreter. The planning run is `tmp/20260917_thermal_sweep.py`, with output `tmp/20260917_thermal_sweep.json`. The file list comes from `git ls-files 'configs/*.yaml' > tmp/<ts>_all_config_yamls.txt`.

```python
import os, sys, json, time, yaml
os.environ["CUDA_VISIBLE_DEVICES"] = ""; os.environ["JAX_PLATFORMS"] = "cpu"
ROOT = "/media/nas01/projects/Interoceptive-AI/grid_world_pain"
sys.path.insert(0, ROOT); os.chdir(ROOT)
from src.environment.config_loader import load_env_config, load_env_params
LIST = sys.argv[1]                                  # the git ls-files output
paths = [l.strip() for l in open(LIST) if l.strip().startswith("configs/environment/")]
out = []
for p in paths:
    rec = {"path": p}
    for _ in range(5):                              # EMFILE retry
        try: raw = yaml.safe_load(open(p)) or {}; break
        except OSError: time.sleep(2)
    rec["layered"] = isinstance(raw, dict) and "extends" in raw
    try:
        cfg = load_env_config(p)                    # the TRAINER's loader, resolves extends:
        rec["thermal_enabled"] = bool(cfg.get("thermal.enabled"))
        rec["warming"] = cfg.get("thermal.warming_rate_scale")
        rec["cooling"] = cfg.get("thermal.cooling_rate_scale")
    except Exception as e:
        rec["resolve_err"] = repr(e)[:200]; out.append(rec); continue
    try:
        load_env_params(cfg); rec["params_ok"] = True
    except Exception as e:
        rec["params_ok"] = False; rec["params_err"] = repr(e)[:300]
    out.append(rec)
json.dump(out, open(sys.argv[2], "w"), indent=1)
for kind, flag in (("standalone", False), ("layered", True)):
    sub = [r for r in out if r["layered"] is flag]
    print(kind, len(sub), "load OK", sum(r.get("params_ok", False) for r in sub))
for r in out:
    if r.get("thermal_enabled"):
        print("THERMAL-ON", r["path"], r.get("warming"), r.get("cooling"), r.get("params_ok"))
```

Planning-time result (HEAD `663cbd72`): 335 env configs. Standalone: 118, of which 27 load. Layered: 217, of which 211 load. Thermal-on: the 4 listed in §A5.2, all loading.

---

## Implementation Report

> **Implemented by**: developer
> **Date**: 2026-09-17 (unattended overnight run)

**Status: Steps 0–7 done; commit 1 made (`068d791e`); Steps 2–7 left as a dirty, uncommitted tree for review (commit 2 not made, by instruction).** No stop condition fired. Working file: `tmp/20260917_thermal_rate_asymmetry_work.md`.

#### What was implemented, file by file

| File | Change |
|---|---|
| `scripts/fixtures/generate_thermal_rate_scale_fixture.py` (new, **commit 1**) | As specified, plus the import-origin assert (D24). |
| `tests/env/fixtures/thermal_rate_scales/single_rate_rollouts.npz` (new, **commit 1**) | Captured from a worktree of `1b5d1ed5`. warm: −14 → +7.99; cool: +14 → −7.99; `*_on` nutrition 100 → 89.953. All non-vacuity asserts passed, including `ate_food` False on every step (no world change was needed). sha1 `22888b4d…`. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (**commit 1**) | Row plus footer (D21). |
| `tests/env/test_thermal_rate_scales.py` (new) | T01–T14 as specified; D20 applied; D22, D26–D28. |
| `configs/environment/default.yaml`, both archived campfire worlds | Keys at 1.0 / 1.0 with the specified comments (D6). |
| `src/environment/config_loader.py` | (a) read and validate, (b) inert 1.0 / 1.0, (c) pass to `EnvParams`: verbatim from File Changes. |
| `src/environment/state.py` | Two static fields, verbatim. |
| `src/environment/core.py` | Gate and scaled branch verbatim, the one-line formula note, and the D3 drain comment verbatim. |
| `docs/environment/CONFIG_GUIDE.md`, `02_config_schema.md`, `05_body_homeostasis.md`, `CONFIG_CRITICAL_SETTINGS.md` | As specified (YAML example, bullet, "Seven things", validation clause; table rows, conditional-mandatory list, structure-check sentence; equation, table rows, tug-of-war, drain paragraph; registry row and change-log entry). |

#### Step 0 / Step 6 test tables (one file per process, `JAX_PLATFORMS=cpu`)

| File | Step 0 | Step 6 |
|---|---|---|
| test_thermal_body | 5 passed | 5 passed |
| test_thermal_validation | 34 passed | 34 passed |
| test_thermal_field | 9 passed | 9 passed |
| test_thermoception | 14 passed | 14 passed |
| test_thermal_reward_gate | 18 passed | 18 passed |
| test_thermal_rendering | 16 passed | 16 passed |
| test_body_temperature_observation | 15 passed | 15 passed |
| test_metabolic_coupling | 11 passed | 11 passed |
| test_thermal_parity | 12 passed, 21 skipped | 12 passed, 21 skipped |
| test_unified_parity | 34 passed, 325 skipped | 34 passed, 325 skipped |
| test_visual_parity | 8 passed | 8 passed |
| test_extero_noc_parity | 3 passed | 3 passed |
| test_recovery_in_bush | 7 passed | 7 passed |
| test_no_recompile | 3 passed | 3 passed |
| test_dashboard_layout | 104 passed | 104 passed |
| test_config_layer_silent_failures_20260723 | 5 passed, 1 warning | 5 passed, 1 warning |
| test_backward_compat_configs | 12 passed, 21 skipped | 12 passed, 21 skipped |
| test_maintained_worlds_bush_blocks_animals | 11 passed | 11 passed |
| **test_thermal_rate_scales (new)** | 1 passed, 13 failed (Step 2, pre-change) | **14 passed, 0 skipped** |

No core dump in any run. Logs: `tmp/20260917_prechange_step{0,6}_*.log`, `tmp/20260917_step2_cp2.log`, `tmp/20260917_step6_newtests.log`.

#### CP2: pre-change outcome vs prediction

| Test | Predicted | Actual |
|---|---|---|
| T01 | PASS | PASS |
| T02–T11, T14 | FAIL, `AttributeError` from `_params` | FAIL, `AttributeError: 'EnvParams' object has no attribute 'thermal_warming_rate_scale'` at `_params` |
| T12 | FAIL, `AttributeError` from `_params` in (a) | same, at part (a) |
| T13 | FAIL, `DID NOT RAISE` at sub-case (1) | same, at sub-case (1) |

#### Appendix B load sweep (`tmp/20260917_012800_sweep_step{0,3,5}.json`)

| | Step 0 | Step 3 | Step 5 |
|---|---|---|---|
| standalone (loads) | 118 (27) | 118 (27) | 118 (27) |
| layered (loads) | 217 (211) | 217 (211) | 217 (211) |
| thermal-on | 4, scales absent | 4, all 1.0 / 1.0 | 4, all 1.0 / 1.0 |

Per-file load status was identical across all three sweeps. At Step 5, `load_env_params` gives `float` 1.0 for both fields on all 4 thermal-on configs, including 05 and 06 through `extends:`.

#### CP5: `jax_step` jaxpr SHA-1 (params as argument, `PRNGKey(0)`; deterministic across two Step-0 processes)

| Config | Step 0 | Step 5 | Contrast, warming 3.0 |
|---|---|---|---|
| `default.yaml` (thermal off) | `a3a2f04f596a52e65380079ed5c3614958609e7a` | identical | n/a |
| archived `campfire_world.yaml` | `ef1b0a1f1be6d9fa6913a69044f6d84949bcbf84` | identical | `cc7b8cd8…` (differs) |
| `basic/05-campfire_thermal_10x10.yaml` | `188186e9bbead1279f7f1cc68c80df7f6a1578d5` | identical | `5139bf41…` (differs) |

#### Byte-identity fixtures

T01 is byte-identical to the new pre-change fixture. `metabolic_coupling`, `thermal_parity`, `unified_parity`, `visual_parity` and `extero_noc_parity` all have counts identical to Step 0. `git status -- tests/env/fixtures/` is clean; the only new fixture is the one in `068d791e`, and no fixture was regenerated.

#### Speed (CP9): `tmp/20260917_014500_speed.py`, vmap 64 × scan 500, 7 repetitions, CPU (D25)

| | Median SPS | Min–max | Spread |
|---|---|---|---|
| Step 0 (pre-change) | 30,126 | 29,797–30,770 | 3.2% |
| Step 6, 1.0 / 1.0 | 29,893 | 29,460–30,296 | 2.8% |
| Step 6, 3.0 / 0.3 (gate on) | 30,070 | 29,720–30,725 | 3.3% |

1.0 / 1.0 is −0.8% vs Step 0, inside the spread, and the graph is identical (CP5), so this is noise. Other sessions kept the load average at 2–7 throughout.

#### Commits and HEAD movement

- **Commit 1: `068d791e`** (generator, fixture, dependency-map row). A first attempt staged nothing, because zsh did not word-split a `$P` variable; it was retried with literal paths. The foreign staged files stayed staged and uncommitted.
- HEAD moved three times during the run, all from other sessions, and none touched `update_body`, the loader, `state.py` or any config: `fe341d7d` (renderer: dashboard, render audit), `d0531a5e` (imperativism docs), and later `02a14322`.

#### Deviations and notes for the verifier

- No deviation from File Changes in code or configs. Test-construction choices are recorded as D22 and D26–D28.
- `core.py`: D3 says the drain comment is "amended to say" that "charge on step t pays for the defence on step t" becomes approximate while moving. The File Changes comment text, used verbatim, carries this as "a per-step (per-decision) cost, which equals a per-degree-moved cost only at 1.0 / 1.0", and does not edit the older sentence above it. Flagged in case the verifier wants the older sentence qualified.
- The plan's status banner (line 12) still reads "PLANNED, Revision 1"; the banner is `senior-developer`'s to update.
- Not done here, by design: commit 2; the CP10 check before commit 2; `OPEN_WORK_HANDOFF.md` E1 line (senior-developer); `INDEX.md` regeneration (D10).

#### Fix round 1 (2026-09-17, after verification: senior-developer PASS; no Critical/Moderate code findings)

Comment, doc and test changes only. **No executable line in `src/` changed.** The tree is still uncommitted.

| # | File | Change |
|---|---|---|
| 1 | `src/environment/core.py` (drain comment), `docs/environment/05_body_homeostasis.md` ("Which `T`") | "pays for the defence performed on step t" now says this holds exactly at 1.0 / 1.0. At other scales the applied defence is `scale × k_loss·(T − setpoint)`, and the bill is a per-decision charge for the defence effort; points to the D3 note. |
| 2 | `docs/environment/02_config_schema.md` | Body-block validation table gains `warming_rate_scale` / `cooling_rate_scale` rows (`> 0`, NaN rejected; `scale × (k_exchange + k_loss) <= 1`, per key, error names the key). "The first six" → "The first eight" (rows counted, D34). |
| 3 | both archived campfire worlds | Loader comments corrected to per-file lists (D30). |
| 4 | `configs/environment/default.yaml` | "makes the fire burn faster" → "makes the fire kill sooner". |
| 5 | `src/environment/core.py` (gate comment) | Added: bit-identity holds only when BOTH scales are 1.0; with only one side at 1.0, that side still takes the scaled branch and rounds differently in the last bits. |
| 6 | `tests/env/test_thermal_rate_scales.py` | T01 asserts `_provenance_sha == PRE_CHANGE_SHA` (`1b5d1ed5…`), with a comment on why it is pinned. Checked that it fires: with the constant set to a wrong SHA, T01 raises `AssertionError` naming both SHAs. |

Not done, as decisions: D31 (generator untouched), D32 (YAML booleans), D33 (backward-compat test).

**Verification (actual output):**
- **`core.py`, this round only (D35):** `diff -U0` pre-round → current shows two hunks. `@@ -184 +184,5 @@` rewrites one comment line into five comment lines; `@@ -324,0 +329,3 @@` adds three comment lines. Non-comment changed lines: **0**.
- **Tests, one file per process, CPU:** `test_thermal_rate_scales` **14 passed** (T01 passing with the pin); `test_metabolic_coupling` **11 passed**; `test_thermal_body` **5 passed**; `test_thermal_validation` **34 passed**; `test_thermal_parity` **12 passed, 21 skipped**. Also `test_body_temperature_observation` **15 passed**, the only loader of the hidden world whose comment changed.
- **`jax_step` jaxpr SHA-1 at 1.0 / 1.0**, Step-0 harness: `default` `a3a2f04f596a52e65380079ed5c3614958609e7a`, archived campfire `ef1b0a1f1be6d9fa6913a69044f6d84949bcbf84`, `basic/05` `188186e9bbead1279f7f1cc68c80df7f6a1578d5`. All identical to Step 0.
- Both edited archived worlds and `default.yaml` still load through `load_env_params`, at float 1.0 / 1.0.
- `git status -- tests/env/fixtures/`: clean.

## Verification Report

> **Verified by**: senior-developer
> **Date**: 2026-09-17 (unattended; uncommitted tree, nothing staged, committed or stashed by the verifier)

**Verdict: PASS.** The built change matches the approved plan. At the shipped 1.0 / 1.0 the environment is provably unchanged, and this was re-derived independently rather than taken from the report. Nothing blocks commit 2. There are two conditions on how commit 2 is made (V1, V2), and one comment fix is recommended (V3).

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| `src/environment/config_loader.py` | +39: read/validate, inert 1.0/1.0, `EnvParams` kwargs | ✅ | Matches File Changes (a)(b)(c) verbatim. There are three hunks only (≈1557, ≈1628, ≈2330). `_thermal_equilibrium`, `_thermal_radial_equilibria`, `_thermal_structure_verdict` and `_check_thermal_structure` have no hunk. |
| `src/environment/state.py` | +12: two static fields | ✅ | Verbatim; placed after `thermal_k_metabolic`, no default values. |
| `src/environment/core.py` | +55/−6: gate, scaled branch, formula note, D3 drain comment | ✅ | Verbatim. See V3 on the older drain sentence. |
| `configs/environment/default.yaml` + 2 archived campfire worlds | +14 / +9 / +9 | ✅ | Verbatim. `basic/05` and `basic/06` untouched (D6). |
| `tests/env/test_thermal_rate_scales.py` (untracked) | T01–T14 | ✅ | Rows match the plan, with D20 and D22/D26–D28 applied. T01 reads the committed `.npz` via `_params_raw`; T12/T13 raise-cases call the loader directly. |
| `docs/environment/CONFIG_GUIDE.md`, `02_config_schema.md`, `05_body_homeostasis.md`, `CONFIG_CRITICAL_SETTINGS.md` | as specified | ✅ | Every hunk belongs to this plan. The registry has both the row and the dated change-log entry, which covers the EVAAA deviation, names the load-count population, and records 0 of 503 saved runs affected. Anchor `#metabolic-coupling-thermal` resolves. |
| `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` | row + footer (commit `068d791e`) | ✅ | Row at line 217, footer at line 279 (D21). |
| `docs/diary/2026-09-17.md` | one developer row | ⚠️ | The developer's row is correct, but the file also carries **uncommitted rows from two other sessions** (`14318db1` renderer rows, `f431d3` progress report and notes). See V1. |
| this plan doc | D21–D29, checkpoints, Implementation Report | ✅ | No foreign hunks. The verifier updated the status banner and wrote this report. |
| `docs/develop/active/issues/OPEN_WORK_HANDOFF.md` | E1 cross-link line (verifier's own edit) | ✅ | The file had no foreign hunks and was not staged before the edit. The line was appended verbatim from File Changes and `last_updated` was bumped. |
| Out of scope, not touched | renderer / dashboard, fixtures, `sim.py`, the vendored oracle, `INDEX.md` | ✅ | `git status -- tests/env/fixtures/ src/environment/dashboard/` is empty. Every other dirty path (the nmn figures and scripts, recovery_in_bush figures, `artifact_format_bugs.md`, the staged `INDEX.md` and `SAVED_RUN_CONFIG_COMPAT.md`, diaries 09-14 and 09-16) belongs to other sessions. |

**Independent re-derivations (not taken from the Implementation Report).** Script: `tmp/20260917_verify_rate_scales_probe.py`.
- **Fixture provenance, from the pre-change source itself.** `git archive 1b5d1ed5 src configs` was exported to `/tmp`, and the generator's own `rollouts()` was called in memory against that export, with nothing written to the repo. **All 20 arrays equal the committed `.npz` exactly** (dtype and `np.array_equal`), and `_provenance_sha` = `1b5d1ed5…`. So T01 compares against evidence of the pre-change code, not against something computed afterwards.
- **jaxpr SHA-1 of `jax_step`, pre-change export vs live tree.** `default.yaml` gave `a3a2f04f…` on both; the archived campfire world `ef1b0a1f…` on both; `basic/05` `188186e9…` on both. The contrast at warming 3.0 gives `cc7b8cd8…` / `5139bf41…`, which differ. All six values equal the developer's CP5 table.
- **The live levels through the trainer's loader** (`load_env_config` → `load_env_params`). Both `basic/05-campfire_thermal_10x10.yaml` and `basic/06-sensory_noise_10x10.yaml` are thermal-on and resolve to `warming=1.0 (float)`, `cooling=1.0 (float)`; so do `default.yaml` and the archived world.
- **Tests, one file per process, `JAX_PLATFORMS=cpu`** (log `tmp/20260917_015409_verify_rate_scales_tests.log`, no EMFILE retries needed). `test_thermal_rate_scales` 14 passed; `test_metabolic_coupling` 11; `test_thermal_body` 5; `test_thermal_validation` 34; `test_thermal_parity` 12 passed / 21 skipped; `test_unified_parity` 34 / 325; `test_backward_compat_configs` 12 / 21. **All seven are identical to the Step-0 and Step-6 columns.**
- **D16/D23 attribution.** `git diff 1b5d1ed5 fe341d7d -- src/environment/dashboard | sha1sum` = `12ee6249446786d0…`, exactly the Step-0 working-tree diff hash. The dashboard content the Step-0 tests ran against is therefore byte-for-byte what `fe341d7d` committed. No commit since then touches the dashboard, the current diff is empty (`da39a3ee…` is the SHA-1 of empty input), and the content hash is still `316cd303…`. The diff-hash move was a commit and not a code change, no test count changed, and D16 was never invoked, so nothing was misattributed.

**Speed:** ✅ no regression. 1.0 / 1.0 ran 29,893 vs 30,126 SPS (−0.8%) against a 2.8–3.2% run-to-run spread, on the same harness, world and CPU, with 7 repetitions after warm-up. The graph is identical by jaxpr SHA-1, so no real delta is possible. Gate-on (3.0 / 0.3) ran at 30,070 SPS.

**Blocking findings:** none.

**Non-blocking findings / conditions on commit 2:**
- **V1: leave the diary out of commit 2's pathspec.** `docs/diary/2026-09-17.md` holds other sessions' uncommitted rows. Committing it under this plan's message would sweep their work. Commit it separately, or let its owners do so.
- **V2: CP10 and CP11 stay open until commit 2.** Re-run the foreign-edit check immediately before committing, because other sessions keep moving HEAD. The `CONFIG_CRITICAL_SETTINGS.md` change-log entry must land in the same commit as `default.yaml`. Suggested pathspec: the 3 source files, 3 configs, the new test, the 4 `docs/environment/` files, this plan doc and `OPEN_WORK_HANDOFF.md`. Do not include `INDEX.md` (D10) or any diary.
- **V3: qualify one older sentence (recommended, `developer`).** D3 promised to amend the comment. File Changes gave no text for it, so the new paragraph qualifies the sentence only indirectly, 3 lines later. With unequal scales the defence actually applied on a step is `s·k_loss·(T − setpoint)`, not the billed `k_loss·(T − setpoint)`. The *timing* claim stays true; the *amount* claim does not.
  - `src/environment/core.py` lines 183–184, drain comment. The sentence "So the nutrition charged on step t pays for the defence performed on step t." (it wraps across two comment lines) becomes "So the nutrition charged on step t is billed on the same T as the defence performed on step t; the amount equals that defence exactly only at warming/cooling scales 1.0 / 1.0 (see the D3 paragraph below)." Re-wrap the comment lines to fit.
  - `docs/environment/05_body_homeostasis.md` lines 565–567, the "**Which `T`.**" paragraph directly above the new "Not scaled" paragraph. The clause "so the nutrition charged on step `t` pays for the defence performed on step `t`" gets the same qualifier.
  - Comments and prose only: no jaxpr, fixture or test can move.
- **V4 (informational).** D15 and the helper bullet still read "every test except T01". D20 governs; the test file's `_params` docstring already says "every SUCCESSFUL load". No action.

**Conclusion**: PASS. The code, configs, tests and docs match the approved plan with no unplanned scope. Byte-identity at 1.0 / 1.0 was re-proven from the pre-change source: the fixture was regenerated from a `1b5d1ed5` export, and the jaxpr hashes match before and after. Commit 2 may proceed under V1 and V2; V3 is a one-line comment clarification best folded into the same commit.

---

## Feedback from plan-reviewer

**Verdict: SOUND WITH CONCERNS** (2026-09-17, adversarial pre-implementation pass; no 🔴 Critical, so no `docs/reviews/` file). All six settled requirements are met as written; no stop condition. Three 🟡 items must be resolved in the plan text/tests before Step 2 runs, because two of them would halt an unattended run and one would commit a wrong rationale. Full table, assumption list and cost-of-being-wrong are in the review transcript; the actionable items are:

- **🟡 M1 — CP2's prediction is wrong for T04, T05, T09, T11 and T14.** Each asserts a property that also holds when the scales are silently ignored (equilibria unchanged; `d == 0` stays put; drain unscaled is *today's* behaviour; a jitted episode at ignored scales is finite with one compile), and none reads a new `EnvParams` field, so none raises `AttributeError` pre-change. They will **pass** at Step 2 and the "any other outcome is a stop-and-report" rule halts the night. Fix: (a) the shared `_params()` helper asserts both loaded fields equal the dict values (loud pre-change, useful post-change); (b) T04/T05/T14 add a discriminator that the scale was applied at all (the scaled trajectory differs from the 1.0/1.0 trajectory by > 1e-2 at some step); (c) T11 asserts the recorded `body_temp` differs from the fixture's `*_on` series, as T10 does; (d) restate the CP2 table per test with the expected failure mode.
- **🟡 M2 — D3's stated reason is factually wrong; the decision stands.** The field is built once at reset (`core.py:1821`), so a settled body in a fixed cell recomputes the identical `d` every step: its sign is **constant**, not noise. Float32 simulation (six cases, 2000 settled steps each): 0 sign flips; the stall side is fixed by the arrival direction (−8.0000029 with `d > 0` from below, −7.9999843 with `d < 0` from above). The correct argument: a scaled bill would be a step function of arrival history — two settled bodies 1.6e-5° apart paying bills that differ by the full ratio, forever. Discontinuous and path-dependent, not jittering. A continuous scaled formulation also exists (scale the bill by the direction of the *defence* term, `sign(setpoint − T)`, which vanishes at the setpoint); name it as the alternative deferred to E1(a). Reword D3, the `core.py` drain comment, the `05_body_homeostasis.md` paragraph and the registry entry. No code change.
- **🟡 M3 — CP7 false-stop from the renderer session.** `test_thermal_rendering` and `test_dashboard_layout` import `src/environment/dashboard/*`, which currently carries that session's uncommitted edits (`episode.py`, `painters.py`), and the session is active tonight. Record `git diff -- src/environment/dashboard | sha1sum` at Steps 0 and 6; a count change confined to those two files with a changed foreign hash is attributed and reported, anything else remains a stop. Also re-run the A5.6 foreign-edit check on `core.py` / `config_loader.py` / `state.py` immediately before Step 4, not only before the commit.
- **🟢 L1 — §A5.2 count discrepancy explained:** `git ls-files 'configs/*.yaml'` = 483; 483 − 217 layered = 266 ≈ the registry's 265, so the 2026-09-16 figure is the whole `configs/` tree and Appendix B is `configs/environment/` only (335). Say so in the change-log entry rather than "not reproducible". Same script both sides → no masking.
- **🟢 L2** — YAML `true` is accepted as 1.0 (`float(True)`); `1e0` / `1.0e0` parse as strings in PyYAML and `float()` rescues them; `.nan`/`.inf`/`0`/negatives are refused. Same property as the existing `k_*` reads; no action.
- **🟢 L3** — `test_backward_compat_configs.py` and `test_maintained_worlds_bush_blocks_animals.py` also load thermal-on worlds and are cheap; add to the pre-change list.

Verified, not assumed: fixture capture is pre-change twice over (worktree of the Step-0 SHA; generator imports `src` only after `sys.path.insert(0, src_root)`; run before any edit; `core.py` imports no dashboard code, so the foreign edits cannot reach `jax_step`); the existing fixture has 0 warming steps (0 up / 273 down / 27 flat); hand values T06–T08 recomputed; `20·(0.04+0.01) == 1.0` in float64 and `1 − 20K = 5.96e-8 > 0` in float32, so T05's boundary case is safe; campfire nutrition scale (100) survives 150 steps at rate 1.0; loader has no key whitelist; one `EnvParams(` constructor; no `.replace(thermal_` sweeps; frozen `environment__default.yaml` is thermal-off. §A3's 1.7× spread already exists at scale 1 (38 vs 22 steps) — a tuning matter for F1, not a defect in the motivation.

Reviewed by: plan-reviewer

---

## Revision 1

> **Date**: 2026-09-17 · **Author**: senior-developer · **Trigger**: `plan-reviewer` (SOUND WITH CONCERNS; signed block above, kept verbatim) and `math-reviewer` (sound, two moderate items). Neither found a Critical issue or a stop condition. Every item below was edited **in place** in the section named; this list is the index. None of these concerns is marked resolved here. A fresh `plan-reviewer` pass decides that.

| Item | Source | What changed | Where |
|---|---|---|---|
| **M1**: CP2 would have halted on a false alarm | plan-reviewer | (a) `_params()` asserts both loaded scale fields equal the dict values (1.0 when thermal is off), and T01 uses a plain loader instead; (b) T04, T05 and T14 gain a check that the scaled trajectory differs from the 1.0/1.0 one by > 1e-2; (c) T11 asserts `body_temp` differs from the fixture's `*_on` series; (d) the CP2 prediction is now a per-test table with the expected exception type, including T09 failing **only** through the helper, and T13's sub-case order pinned so its first failure is the predicted one. | D15; test helpers; T01, T04, T05, T11, T14; "Non-vacuity requirement (CP2)"; CP2 |
| **M2**: D3's reason was wrong; the decision stands | plan-reviewer and math-reviewer, independently | "The sign of `d` is float noise" was false: the field is fixed per episode, so at a settled point the sign is set by rounding, frozen at the arrival direction in 97.3% of cases and alternating every two steps in 2.7%. The corrected argument is that a scaled bill would be **path-dependent or jittery**. D3 now says it is defensible but not the only choice, and records both alternatives for E1(a): the time-dilation reading (bill × `s`; under D3 a faster rewarm costs less total nutrition) and the defence-direction switch (`sign(setpoint − T)`). | D3; `core.py` drain comment in File Changes; `05_body_homeostasis.md` instructions; registry change-log instructions; A6 (E1); F4 |
| **M3**: foreign edits could move two test counts | plan-reviewer | Record the dashboard foreign-diff hash at Steps 0 and 6. A count change confined to `test_thermal_rendering` / `test_dashboard_layout` **with** a changed hash is attributed and reported; anything else is still a stop. The foreign-edit check is re-run on `config_loader.py`, `state.py` and `core.py` immediately before Step 4. | D16; edit order Steps 0, 4, 6; pre-change list note; CP1, CP7, CP10 |
| **Fire target at range corners** | math-reviewer | Re-computed at all nine corners. At warming scale 2 the first fire step is survivable at −25 / 12 (13.08), marginal at −28 / 12 (14.64), and lethal at −25 / 13 (15.83) and −28 / 13 (17.73). §A3 and F1 now require the target search to evaluate at the corners of both sampled ranges. | D19; §A3; F1 |
| **Away-time spread exists at scale 1** | coordinator, from plan-reviewer (i) | Recorded that the ~1.7× spread is already present at scale 1 (38 vs 22 steps), so the feature is necessary but not sufficient across the sampled range, and this is a tuning matter. | §A3; F1 |
| **L1**: load-count population | plan-reviewer | Explained: the 2026-09-16 figure covers the whole `configs/` tree (483 − 217 = 266 ≈ 265); Appendix B covers `configs/environment/` only (335). The change-log entry must name its population. | §A5.2; change-log instructions |
| **L3**: two more pre-change tests | plan-reviewer | Added `test_backward_compat_configs.py` and `test_maintained_worlds_bush_blocks_animals.py`. Both exist and glob the thermal-on worlds. | D18; pre-change list |
| **L2**: YAML spellings | plan-reviewer | Verified correct by the reviewer; no change. | — |
| **D5 wording** | coordinator, relaying math-reviewer | Recorded that the unscaled `K <= 1` check is redundant when `max(scales) >= 1` and not implied when both scales are below 1. D5's stated reason stays the documented *meaning* of `k_exchange` / `k_loss`. | D5 |
| **Reviewer feedback block** | — | Committed with this revision, unmodified. | D17 |

**Not changed by this revision:** the key names, the gate design, the edit order apart from the Step 0/4/6 additions, the File Changes for `config_loader.py`, `state.py`, the configs and the fixture generator, and every test's reference value.

---

## Feedback from plan-reviewer — Revision 1 pass

**Verdict: SOUND WITH CONCERNS** (2026-09-17, fresh independent pass on `e5a0d0ac`; standing in for the approval gate). The exit condition is met against the text itself: M1(a)–(d), M2 at all three sites (D3, the `core.py` drain comment, the `05_body_homeostasis.md` instruction; and the registry instruction), M3's two recording steps (D16 at Steps 0/6, CP7; the code-file check before Step 4, CP10), and the per-test CP2 table listing T04/T05/T09/T11/T14 with their discriminators. No reference value moved: T04 and T05 changed by insertion only, T11/T13/T14 are identical up to their appended sentences, and T03, T06–T10 and T12 are untouched by the diff. My earlier signed block is byte-identical to what I appended (sha1 `1ef134fa0ba3810072ceca524000d76927f065e9` on both). The `_params()` "read the fields first" reasoning is correct: at Step 2 the configs carry no keys yet, so a dict read would raise `KeyError` before the predicted `AttributeError`.

**One concern remains, in exactly the class the revision addressed — two CP2 predictions are still false alarms under the revision's own rules:**

- **🟡 R1 — T13's prediction contradicts the helper rule.** D15 says every test except T01 loads through `_params`. Inside `with pytest.raises(ValueError): _params(d)`, pre-change code loads successfully and the helper's first field read raises `AttributeError`; `pytest.raises(ValueError)` does not catch it, so T13's first failure is `AttributeError`, not the predicted `DID NOT RAISE` — whatever the sub-case order. Fix (one sentence in T13): the raise-expecting sub-cases (2.001, 0.0, −1.0, nan, and the existing-`K` case) call `load_env_params(Config(d))` directly, because the raise *is* the assertion and the helper's field check is meaningless on a load that must fail; only the boundary "2.0 loads" sub-case goes through `_params`, and it is ordered after them. Then the prediction `DID NOT RAISE` holds.
- **🟡 R2 — T12(a) "both keys deleted" raises `KeyError` at Step 2.** `default.yaml` has no scale keys until Step 3, so a `del d["thermal"]["warming_rate_scale"]` raises `KeyError` before `_params` is reached; the table predicts `AttributeError`, and the new stop rule treats a different exception type as a stop. Fix (three words): "deleted with `pop(key, None)`". Same wording for (b) and (c), which are moot at Step 2 but should not depend on order.

Everything else in the coordinator's list checks out; D19's corner values are `math-reviewer`'s domain and are consistent with a one-step hand check at −25 / 12 (ring 8.09 → 13.07 at scale 2). What flips this to SOUND: R1 and R2 applied to the T13 and T12 rows. No other section needs to change, and the next pass needs only to read those two rows.

Reviewed by: plan-reviewer

---

## Revision 2

> **Date**: 2026-09-17 · **Author**: senior-developer · **Trigger**: `plan-reviewer`'s Revision 1 pass (SOUND WITH CONCERNS; signed block above, kept verbatim), findings R1 and R2. Final revision round. **Scope kept surgical:** only the T12 and T13 rows, their two CP2 entries, and one new decision (D20). Nothing is marked resolved here.

| Finding | What changed | Pre-change first failure, traced |
|---|---|---|
| **R1**: T13's prediction was wrong | Sub-cases (1)–(4), which expect a raise, call `load_env_params(Config(d))` directly inside `pytest.raises(ValueError)`. The boundary "2.0 loads" sub-case (5) goes through `_params` and is ordered **last**. | `Failed: DID NOT RAISE <class 'ValueError'>` from sub-case (1). The old wording (`_params` inside `pytest.raises`) was reproduced giving `AttributeError`. |
| **R2**: T12's key deletion | (a)–(c) remove keys with `pop(key, None)`, never `del`. (b) and (c) also call the loader directly (the R1 logic applied to T12). Order (a)–(d) stated. | `AttributeError: 'EnvParams' object has no attribute 'thermal_warming_rate_scale'`, from `_params` in (a). The old `del` was reproduced giving `KeyError: 'warming_rate_scale'`. |

**How the predictions were derived.** I did not reword them. The specified T12 and T13 bodies, with the helper exactly as the plan defines it (fields read first), were **run against the current tree**, which is still exactly the pre-change code: no scale keys in any config, and no scale fields or reads in the loader. Script: `tmp/20260917_rev2_trace_t12_t13.py`. Output, first exception per body:

```
T12 as revised                     -> AttributeError: 'EnvParams' object has no attribute 'thermal_warming_rate_scale'
T12(b) alone                       -> Failed: DID NOT RAISE <class 'ValueError'>
T12(d) alone                       -> AttributeError: 'EnvParams' object has no attribute 'thermal_warming_rate_scale'
T12 old `del`                      -> KeyError: 'warming_rate_scale'
T13 as revised                     -> Failed: DID NOT RAISE <class 'ValueError'>
T13 old: _params inside raises     -> AttributeError: 'EnvParams' object has no attribute 'thermal_warming_rate_scale'
T13 existing-K case alone          -> PASSED
T13 boundary 2.0 alone             -> AttributeError: 'EnvParams' object has no attribute 'thermal_warming_rate_scale'
```

**Post-change behaviour of the same bodies, checked by reading the planned loader code, not run:**
- T12(b): the loader reads `warming_rate_scale` first, so a missing key raises `ValueError` naming it.
- T12(c): warming reads fine, and the missing cooling key raises naming `thermal.cooling_rate_scale`.
- T13(1)–(2): positivity passes, and the stability message is built from that key alone.
- T13(3): `not (nan > 0)` raises.
- T13(5): `2.0 * 0.5 == 1.0` passes the `<= 1` check.

**Known wording inconsistency, deliberately not edited:** D15 and the test-helper bullet still say "every test except T01 loads through this helper". **D20 governs:** raise-expecting sub-cases call the loader directly.

---

## Feedback from plan-reviewer — Revision 2 pass

**Verdict: SOUND** (2026-09-17, fresh independent pass on `b6375c53`; standing in for the approval gate). Implementation may start.

- **R1 (T13) resolved in the text.** Sub-cases (1)–(4) call `load_env_params(Config(d))` directly inside `pytest.raises(ValueError)`; the boundary "2.0 loads" case (5) is the only one through `_params` and is last. Predicted first pre-change failure `DID NOT RAISE` is correct: the pre-change loader has no scale reads, the uniform dict passes its existing checks (`K = 0.5`, structure check skipped), and nothing reads a new field before that point.
- **R2 (T12) resolved in the text.** (a)–(c) use `pop(key, None)`; (b) and (c) call the loader directly; order (a)–(d) is stated. Predicted first pre-change failure `AttributeError` from `_params` in (a) is correct.
- **The trace is real evidence, not a look-alike.** `tmp/20260917_rev2_trace_t12_t13.py` defines `_params` exactly as the plan does (both fields read first), `_uniform` as the plan's transformation, runs T12(a) and T13(1)–(2) as specified, and imports the working copy, which is still the pre-change code (no scale reads in `config_loader.py`, no scale keys under `configs/`). Its output matches the CP2 table line for line, and the two old wordings reproduce the two defects (`KeyError`, `AttributeError`). Post-change behaviour of the same bodies is read, not run; CP8 covers that after Step 5.
- **The stale D15 / helper-bullet sentence is not misleading and is non-blocking.** The developer implements from the T12/T13 rows, which state the exception in-line and cite D20; D20 declares precedence; and a mis-implementation would surface at Step 2 as a CP2 mismatch (stop-and-report), never silently. Recommend the one-line edit ("every *successful* load outside T01") as a documentation correction — it changes no test or prediction, so it does not reopen the plan.
- **Both earlier blocks unaltered:** first block sha1 `1ef134fa0ba3810072ceca524000d76927f065e9`; the Revision 1 pass block appears in the `e5a0d0ac..b6375c53` diff verbatim.
- **Diff scope confirmed surgical:** D20, the T12/T13 rows, their two CP2 entries, the Revision 2 section. No reference value, loader/state/config/generator section, or other test row changed.

Reviewed by: plan-reviewer

---

## Follow-up — target search with the new speed settings (2026-09-17, after commit `d4c30a2a`)

**Plain-language summary.** With the two new settings in place, the user's three targets can be met,
but only if the world stops varying as much from episode to episode as it does now. The settings
themselves were never the whole answer; the per-episode randomness in world temperature and fire
strength is what blocks a robust result. **No config was changed.** These are candidates for the
user to choose from.

**Method.** Every candidate was checked at the four corners of the sampled ranges and at their centre,
never the midpoint alone (D19). Radial temperatures come from the loader's own blur
(`_thermal_single_fire_field`) and validity from `_thermal_structure_verdict`. Durations come from the
discrete recurrence, which `math-reviewer` verified equals the closed form and which the committed
code implements (T04-T09). Grid: warming 1-15, cooling 0.1-1.0, `k_loss` 0.005 / 0.01 / 0.02,
`k_exchange` 0.04, sigma 0.7, stability `scale*(k_exchange + k_loss) <= 1` enforced. The scripts are
`tmp/20260917_target_search_scales.py` and `tmp/20260917_target_search_ring.py`. **Not yet run through
the live environment**: a candidate the user picks should get a short thermal-on rollout before training.

**Correction to the confirmed pain definition.** The pain target was confirmed as "starting from
comfortable (0)". An agent almost never enters the fire from 0: it steps on from the ring next to
the fire, already near +8. Every robust candidate under the confirmed definition **killed on step 1
when entered from the ring**. The search below therefore requires pain from **both** entries, which
is what the user's rule ("the first step must be survivable") actually means.

| Finding | Result |
|---|---|
| Shipped sampled ranges (world -28..-22, fire ratio 11..13) | **0** robust configs |
| Why the world range alone blocks it | at any fixed cooling speed, away time differs 1.72x between world -28 and -22; the target band 80-110 is only 1.375x wide |
| Fire ratio kept at 11..13, any world width > 0 | **0** robust configs |
| Fire ratio fixed at 12, world +/-1 | **14** robust configs |
| Fire ratio fixed at 12, world +/-0.5 | **49** robust configs |

**Why fire-ratio variation is fatal.** Fast rewarm and a survivable first step from the ring pull the
**same** warming speed in opposite directions. At the shipped centre: warming 1 -> rewarm 20 steps, step
1 from the ring +10.6; warming 2 -> rewarm 10, step 1 +13.1; warming 3 -> rewarm 7, step 1 **+15.6
(dead)**. The usable window is roughly warming 2-2.5. A hotter fire (ratio 13) pushes the first step
past +15 inside that window, so a per-fire ratio range cannot be tolerated.

**Candidates for the user (none applied):**

| World range | Fire ratio | `k_loss` | Warming | Cooling | Away | Rewarm | Pain from 0 / from ring |
|---|---|---|---|---|---|---|---|
| -31..-29 | 12 fixed | 0.02 | 2 | 0.25 | 86-99 | <=9 | <=3 / <=2 |
| -35.5..-34.5 | 12 fixed | 0.02 | 1.5 | 0.2 | 84-88 | <=10 | <=3 / <=2 |

**Costs the user should weigh before choosing:**
- **Both candidates double `k_loss`** (0.01 -> 0.02). That moves every settling temperature, which
  changes the map's geography: the ring's temperature, how much of the map is survivable, and the
  radial profile the design page was tuned on. The speed settings alone left the map untouched; this
  does not.
- **Both need a colder world** (-30 or -35 against today's -25) and a **much narrower** per-episode
  range (+/-1 or +/-0.5 against +/-3), plus a fixed fire strength. That removes most of the
  episode-to-episode variation in the thermal world.
- **Warming 1.5-2 against cooling 0.2-0.25 is a 6-10x asymmetry**, beyond the 4-6x estimated earlier
  and further past the commonly reported physiological range. Worth `research-postdoc`'s literature
  check before a paper claim.
- These are feasible points on a coarse grid, not optima.
