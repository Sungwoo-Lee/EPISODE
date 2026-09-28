---
title: "Continual worlds: does the modulator help an agent move between worlds whose body rules never change?"
topic: continual_worlds
status: active
created: 2026-09-28
last_updated: 2026-09-28
phase: continual / A-B-A-B structure (user framing 2026-09-28)
wandb_tag: "rppo_cw_*"
---

# Continual worlds: an A-B-A-B test of the modulator with a stationary body

> **Status (2026-09-28, Revision 1a):** pilots 1–18 **running** since 13:16; an interim read-out
> failed three worlds (Danger, Fog, Harsh) for both agents, so their softened versions are configured
> and six re-pilot runs (rows 31–36) are **planned, not launched** (see the Revision 1a box below).
> *Revision 1 status, kept for the record:* DESIGNED, configs written and loader-validated, **nothing
> launched**. The next step is the three **pilots** (section 3.6, 18 runs), which are ready to
> launch once `env-config-reviewer` has passed the changed worlds and the parent has assigned nodes.
> The main runs wait for the pilots: their stage lengths are computed from Pilot 1 by a rule fixed
> in advance (3.3), and they branch from Pilot 1's Forage runs (3.4).
> **Related:** level-05 factorial (source of the two pre-trained agents) [[LEVEL05_BODY_INTERACTIONS]] ·
> larger / less observable worlds and their search times [[STUDY_PLAN]] (context exploration) ·
> the May continual probe this design replicates at scale [[NMN_CONTINUAL_DOUBLE_RETURN_PROBE]] ·
> balance logging [[BALANCE_METRICS_TRAINING_LOGGING]] · curriculum lessons in the LLM wiki
> (`curriculum_learning`: plasticity loss, negative transfer).

> **Revision 1 (2026-09-28)** — resolves the plan-reviewer's findings F1–F9 (bottom of this doc) and
> the user's decisions ("follow your recommendations"):
> - **Decisions taken:** the no-code workaround for the animal-count trainer bug is accepted (no
>   per-predator distance curves); Fog = sight blurred 3× plus smell/sight noise; Winter fire heat
>   factor 10; Famine = 1–2 food items regrowing after 30 steps; **Forage is trained once per agent
>   and the three sequences branch from it** (3.4).
> - **Pilots replaced (F1):** Pilot 1 = each new world once from the Home agent, both agents (12
>   runs); Pilot 2 = two short A-B-A-B pipeline shakedowns, both agents (4 runs); Pilot 3 = the
>   Nursery world from scratch, both agents, with a pass criterion (2 runs). New schedule files for
>   Pilot 2. Manifest rewritten (section 4).
> - **Rules pre-registered:** plateau and stage length, with a fallback and a 3 M cap (F2, 3.3);
>   recovery counted in episodes **and** environment steps, both must agree (F3, 5.1); noise yardstick
>   is a floor plus the within-visit checkpoint spread (F4, 5.5); forgetting evaluation at 2,000
>   episodes per cell with a non-overlapping-CI rule (F5, 5.3); the May probe cited and this study
>   positioned as its replication at scale (F6, sections 1–2); verdict wording "one initialisation
>   pair, three world-pairs" (F7); project interpreter in commands (F8); entropy windows cut on the
>   iteration stream (F9).
> - **Entity counts re-derived per cell (coordinator, figure build):** the 15 × 15 worlds had copied
>   some counts from the brief without scaling by area, so Danger was *less* dangerous per cell than
>   Home. Every count is now set against Home's density per cell (3.2, new density table). Changed:
>   Danger hunters 2–3 → **5–7**, ambushers 6–12 → **14–27**, bushes 8–12 → **18–27**; Famine and
>   Winter hunters 0–1 → **0–2**; Fog hunters 1–2 → **2–5**; Harsh hunters 1–2 → **2–5**, bushes 2–4 →
>   **5–9**. Loads, observation width, 1,000-reset placement and schedule builds re-run (6.1).

> **Revision 1a (2026-09-28, evening) — three worlds proved too hard; each gets its one softening
> step and a re-pilot.** Pilots 1–18 were launched at 13:16 (manifest rows 1–18). An **interim**
> read-out (runs still training, so every number below is **provisional until the runs end**) shows
> that in three of the new worlds **neither** agent survives long enough to pass the pre-registered
> survivable rule (3.6: survival over the last 200,000 episodes at least half of the agent's own
> Home level, i.e. ≥ 124.9 steps for the ordinary agent and ≥ 126.7 for the modulated one):
>
> | World | Ordinary agent (last 200k, steps) | Modulated agent | Curve | Verdict | The one pre-named softening step (3.6) |
> |---|---|---|---|---|---|
> | Danger | 76.8 | 76.8 | flat | both fail | hunting predators 5–7 → **3–5** per episode |
> | Fog | 92.2 | 92.0 | flat | both fail | perceptual noise halved: smell σ 0.3 → **0.15**, sight σ 0.2 → **0.1** (smell range 3 and the 3× sight blur unchanged) |
> | Harsh | 82.6 | 82.1 | flat | both fail | food items 1–2 → **2–4** per episode |
>
> The runs were 1.2–1.8 M of 3 M episodes in, with under 2 h left, and none of the curves was still
> rising. Because both agents fail, 3.6 applies its rule: soften **once** by the pre-named step and
> re-pilot; if the softened world fails again it is dropped and the user chooses its replacement.
> The softened worlds are new files next to the originals (`*_soft_15x15.yaml`, 4.1); each `extends:`
> its original and changes only that one step, so the body (level 05) and the 58-number observation
> are unchanged (check C11, 6.1). The six re-pilot runs are **Pilot 1s**, manifest rows **31–36**,
> planned, not launched. If the original run's final read-out (after it ends) reverses a verdict, the
> matching re-pilot rows are cancelled rather than run.
>
> Other interim Pilot 1 / Pilot 3 read-outs, recorded here, **nothing changed**:
> - **Forage** carries the pre-registered **"too easy to be a distinct world"** flag: both agents
>   reach ≈ 475 of the 500-step episode cap (ordinary 475.0, modulated 474.0). This is expected for
>   the deliberately safe first stage, was shown to the user, and Forage is not changed.
> - **Winter, modulated agent is borderline**: 138.1 steps against its 126.7 line (ordinary 154.3);
>   it passes today, but by a margin small enough that the final read-out must confirm it.
> - **Famine** passes for both agents (205.4 / 202.7).
> - **Pilot 3 (Nursery from scratch) passes provisionally** on every pre-registered row for both
>   agents (survival 375.0 / 359.5 ≥ 200; bites 64.9 / 60.8 ≥ 15; eat ratio, hide ratio, time warm
>   and thermal late-death share all inside their thresholds; no collapse).
>
> Source: `scripts/analysis/studies/continual_worlds/pilot_readout.py` → 
> `results/analysis/continual_worlds/pilot_readout.json` (full print
> `tmp/20260928_pilot_readout_run2.log`).

## 1. Question

Our agents live in a grid world and must keep three body quantities in range: how fed they are,
how injured they are, and how warm they are. Two agents are compared throughout: an **ordinary**
recurrent agent, and the same agent with a **modulator** (a small side network that reads the
senses and rescales the main network's layers, loosely modelled on how neuromodulators such as
noradrenaline retune the brain). In a single fixed world the modulator gives at most a small
survival edge.

The literature on neuromodulation says its main pay-off should appear when the **world keeps
changing and old worlds come back**. The project already has one small positive result of this
kind: in May, a probe alternated a hunting predator with a harmless one (active, passive, active,
passive, active), and the modulated agent survived about 107–132 steps longer on the returns to the
hunting world. That probe was tiny (1,500-episode stages, one seed, one kind of change). This
experiment asks whether the result **holds at scale and across several kinds of world change**.

One strict rule: **the body never changes.** Hunger, injury, healing, body temperature and what the
agent feels from inside its body obey identical rules in every world. Only the outside world
changes: grid size, how far smells carry, how many hunters there are and how persistent they are,
how scarce food is, how cold it is, how noisy the senses are. So the body's signals mean the same
thing everywhere and can act as a stable reference for the modulator.

Each agent starts from its already-trained self (10 million episodes in the standard campfire
world, "Home"), learns a large safe foraging world once ("Forage"), then alternates between two
harsher worlds A and B four times (A, B, A, B). Three A/B pairs: **dangerous vs. scarce food**,
**foggy vs. dangerous**, **winter vs. scarce food**. The measure is **survival steps** per episode;
the question is whether the modulated agent's **dips on switching are smaller, its recoveries
faster, and its returns better** than the ordinary agent's. With one starting pair of agents, a
positive result says "this initialisation pair, in three world-pairs", not "the modulator"; fresh
seeds (3.5) are the route to the general claim.

## 2. Hypotheses and predicted outcomes (pre-registered)

Plain names first; the symbols are only shorthand used in the tables below.

- **Smaller dip (H-dip).** On each switch into a world, the modulated agent's survival falls less
  below that world's reference level than the ordinary agent's does.
- **Faster recovery (H-rec).** After each switch, the modulated agent needs less training to climb
  back to 90 % of the reference level — counted **both** in episodes and in environment steps (5.1);
  the vote counts only if both units agree.
- **Better return (H-ret).** On the second visit to a world, the modulated agent gains more (or
  loses less) relative to its first visit than the ordinary agent does. "Second visit better than
  first" means something was kept, not relearned.
- **Less forgetting (H-forget).** Tested without training: a checkpoint taken at the end of a stage,
  played in the *other* worlds of its sequence, keeps more of its earlier survival for the modulated
  agent (forgetting matrix, 5.3).

**Relation to the May probe (replication targets).** The May double-return probe
([[NMN_CONTINUAL_DOUBLE_RETURN_PROBE]]) found the modulated agent ahead on the **returns** and
forgetting less, and found that "how deep is the dip" was an ill-posed measure there — the
difference lived in **how fast** survival came back, not in the first-window depth. H-ret and
H-forget are therefore this study's **replication targets**, and H-rec is expected to carry more
signal than H-dip. The May probe also measured ±4.4 steps of seed-to-seed noise on a harder world;
that number is reported next to every difference here (5.5).

**What would support the modulator (in advance):** in at least **2 of the 3 sequences**, the
modulated-minus-ordinary difference has the favourable sign on **at least 3 of the 4 switch
measures** (dip, recovery, return, forgetting) **and** at least one of those differences is beyond
noise (5.5 for dip / recovery / return, 5.3 for forgetting). The three sequences share one starting
pair of agents (same weights, optimizer state and random key) and share worlds (P1 and P3 both use
Famine, P1 and P2 both use Danger), so they are **not** three independent votes: a support verdict
is worded **"one initialisation pair, three world-pairs"**. Predicted shape: the difference is small
or absent on the first visit to A and B and appears on the **returns** (stages 4 and 5).

**What would refute it (in advance):** in at least 2 of the 3 sequences, the differences have mixed
or unfavourable signs, or all lie inside noise. A **null** is also recorded if both agents show no
dip at all (failure mode 7.2).

**Not claimed either way:** any mechanism, and anything about the modulator in general beyond this
initialisation pair.

## 3. Experimental design

### 3.1 The stationary body (identical in every stage, = today's level 05)

Every concept world `extends:` the level-05 campfire world and overrides **only** external keys.
Verified on the live loader (6.1, check C2): all 8 world configs resolve to the **same** body,
thermal-body, interoception and reward parameters as level 05 (the only differing fields are the
per-entity arrays whose length changes with the counts, grid size, smell range, ambient and fire
settings, and Fog's external noise table).

| Body item | Value (level 05) | Keys (inherited, never overridden) |
|---|---|---|
| Nutrition | range 0–200, setpoint 100, metabolic cost 1/step, eating cost 1, **food energy per bite 6** (fixed), death at 0 and at 200 (overeating) | `body.max_nutrition`, `satiation_setpoint`, `metabolic_cost`, `eating_nutrition_cost`, `food_nutrition_gain`, `overeating_death` |
| Injury | max 100, healing only when resting, base rate 0.2, no acceleration, **bush healing ×25** (fixed), hits spread over 3 steps | `max_injury`, `recovery_base_rate`, `recovery_accel_rate`, `recovery_in_bush_multiplier`, `injury_smoothing_duration` |
| Body temperature | exchange 0.04, loss 0.02, warming ×2, cooling ×0.25, death below −15 or above +15 | `thermal.k_exchange`, `k_loss`, `warming_rate_scale`, `cooling_rate_scale`, `min/max_temperature` |
| Body rules B2–B5 / A1 | all off (as level 05) | `healing_nutrition_cost 0`, `healing_nutrition_dependence false`, `thermal.healing_*_sensitivity 0`, `injury_heat_exchange_gain 0` |
| Random start body | nutrition 0–200, injury 0–100, body temp −10…+5 | `random_start_*`, `start_*_low/high` |
| Interoception | satiation exact, felt injury through the 12-step alpha kernel (τ 3), body temperature exact; injury and nutrition not directly observed | `interoceptive_*`, `injury_observable false`, `nutrition_observable false`, `thermal.body_temp_observable true` |
| Reward | drive reduction, death penalty 100 | `use_homeostatic_reward`, `death_penalty` |
| Episode | max 500 steps | `environment.max_steps` |
| Agent | γ 0.95 and every other agent setting unchanged (the pre-trained agents' own configs) | agent YAMLs (4.1) |

### 3.2 The concept worlds (external only)

All worlds keep the **58-number observation**: senses are never removed, only their range, blur or
noise changes; temperature sensing is always on. Within every A ↔ B pair both worlds are 15 × 15, so
grid size changes once (Forage → A) and never on the alternation being measured; the agents have no
absolute-position sensor (`location_sensor: false`), so grid size is not a direct cue either.

**Per-cell density rule (Revision 1).** Home (level 05, 100 cells) is the reference. Every count
is set so the concept's pressure holds **per cell**: a count the concept brief gave in Home-grid
terms is scaled by area (×2.25 at 15 × 15, ×4 at 20 × 20, round half up; the context-exploration
generator's rule), and anything the concept does not name is at Home's density. Three things are
deliberately **not** scaled because scarcity *is* the concept: Forage's food (a sparse, large world
to search), Famine's and Harsh's food (1–2 items, user decision), and Winter's single fire. Rabbits
stay 0–5 in every main-run world (5 slots, needed by the trainer-bug workaround, 6.2 B1).

**Counts** (range per episode):

| Concept | Grid | Smell | Food (items, bites, regrow) | Hunting predators | Ambushers | Bushes | Fires | Rocks | Rabbits | Ambient | Other |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Nursery** (fresh pre-training only) | 10 | 20 | 4–6, 12, 0 | exactly 1; moves every 3rd step; notices at 3–4 cells; hit 15–45 | 0–2 | 8–12 (may sit by fires) | 2–3 | 6–12 | 0–2 | ≈ −30 | |
| **Home** (reference) | 10 | 20 | 1–4, 12, 0 | 0–2 | 2–12 | 4–10 | 1–3 | 6–12 | 0–2 | ≈ −30 | level 05 unchanged |
| **Forage** | 20 | 5 | 4–8, 12, 0 | none | 0–2 | 16–40 | 4–12 | 24–48 | 0–5 | ≈ −30 | |
| **Danger** | 15 | 5 | 2–9, 12, 0 | **5–7**; notice at 5–9 cells (L05 1–7); stamina 100–200 (L05 30–150); lose-interest 2.0 (L05 1.5); hit 15–120 | **14–27** | 18–27 | 2–7 | 14–27 | 0–5 | ≈ −30 | |
| **Famine** | 15 | 5 | **1–2**, 12, **30 steps** | 0–2 | 5–27 | 9–23 | 2–7 | 14–27 | 0–5 | ≈ −30 | |
| **Winter** | 15 | 5 | 2–9, 12, 0 | 0–2 | 5–27 | 9–23, **none within 3 cells of the fire** | **exactly 1**, heat factor 10 | 14–27 | 0–5 | **≈ −40** | |
| **Fog** | 15 | **3** | 2–9, 12, 0 | 2–5 | 5–27 | 9–23 | 2–7 | 14–27 | 0–5 | ≈ −30 | sight blurred 3×; noise on smell σ 0.3, sight σ 0.2 |
| **Harsh** (later, P5) | 15 | 8 | **1–2**, 12, 0 | 2–5 | 5–27 | **5–9** | 2–7 | 14–27 | 0–5 | **≈ −35** | |

**Per-cell density** — mean number placed per 100 cells, measured on 1,000 real resets per world
(6.1 C3); in brackets, the ratio to Home where the concept departs from it on purpose:

| Concept | Food | Hunters | Ambushers | Bushes (shelter) | Fires (heat) | Rocks | Rabbits | Intended pressure |
|---|---|---|---|---|---|---|---|---|
| Home | 2.46 | 0.98 | 7.24 | 7.01 | 2.01 | 8.98 | 1.01 | reference |
| Nursery | 4.99 (2×) | 1.00 (slow, short-sighted) | 1.02 (0.14×) | 9.97 (1.4×) | 2.49 | 8.98 | 1.01 | easier than Home everywhere |
| Forage | 1.51 (0.6×, by design) | 0 | 0.26 (0.04×) | 7.03 | 2.00 | 9.10 | 0.62 | safe; food sparse in a big world |
| Danger | 2.44 | **2.66 (2.7×)** | **9.16 (1.3×)** | 10.03 (1.4×) | 2.00 | 9.00 | 1.08 | many more, longer-chasing hunters and more ambushers per cell |
| Famine | **0.66 (0.27×)**, slow regrowth | 0.44 (0.45×) | 7.01 | 7.06 | 2.00 | 9.00 | 1.08 | food scarce; threat below Home so hunger dominates |
| Winter | 2.44 | 0.44 (0.45×) | 7.01 | 7.06 | **0.44 (0.22×)**, none beside a bush | 9.00 | 1.08 | cold; one heat source; threat below Home |
| Fog | 2.44 | 1.55 (1.6×) | 7.01 | 7.06 | 2.00 | 9.00 | 1.08 | short noisy senses; threat slightly above Home |
| Harsh | **0.66 (0.27×)** | 1.55 (1.6×) | 7.01 | **3.10 (0.44×)** | 2.00 | 9.00 | 1.08 | cold, hungry, exposed and hunted at once |

Config keys per concept (all under `environment:` unless stated): `height`/`width`;
`sensory.sensor_radius`; food `count_low/high`, `max_consumption`, `regeneration_delay`; hunting
predator entry (`class: predator`) `count_low/high`, `move_interval`, `detection_range`,
`max_stamina`, `lose_interest_multiplier`, `damage` — absent in Forage; ambusher (`hiding_predator`
resource) `count_low/high`; `campfire` / `rock` / `bush` `count_low/high` and `area`; campfire
`temperature_ratio` (Winter only); `thermal.default_temp` (Winter [−41, −39], Harsh [−36, −34]);
`thermal.bush_min_fire_distance` 3 (Winter only); Fog adds `sensory.visual_blur_radial_scale` 1.5 and
a `perceptual_noise` block (enabled, every modality `mode: constant`, σ 0 except olfaction 0.3 and
visual 0.2). Search time to the nearest food (context-exploration Part 3 reset study, mean steps):
15 × 15 at density with smell 5 ≈ 9.7; 1–2 items at smell 5 ≈ 51; at smell 8 ≈ 23; smell 3 with
density food ≈ 20.5.

**Three departures from the brief, each forced by a measured constraint (all accepted by the user):**

1. **Fog cannot have vision range 1.** Vision range changes the observation width (58 → 50) and the
   trainer's curriculum check refuses such a schedule (`obs_dim` and the modality fingerprint, which
   includes `visual_sensor_range`). Fog instead blurs sight along each line of sight three times more
   than level 05 (`visual_blur_radial_scale` 0.5 → 1.5; continuous, not fingerprinted), plus noise on
   smell and sight. Noise uses `constant` mode, not level 06's injury-scaled mode, because noise that
   grows with injury would be a body rule.
2. **Winter's fire heat factor is 10, not level 05's 11.** A fire is `ratio × |ambient|` hot. At −40
   with ratio 11 the first step from the warm ring onto the fire reached **+15.65** on 1,000 real
   resets — instant death. At 10 the worst case is **+11.73** and only the 4 cells beside the fire are
   survivable to stand in (level 05: ≈ 16 cells). Tested: 11 → 15.65, 10 → 11.73, 9.5 → 9.78,
   9 → 7.83, 8.25 → 4.90.
3. **Famine has no edge band.** A spawn area is a single rectangle; a band along all four walls
   needs several food entries with independent counts, which would allow episodes with no food. The
   fallback is used: 1–2 items anywhere, regrowing 30 steps after being eaten out (level 05:
   instantly).

**A known risk, stated in advance:** in context-exploration Part 4, agents trained **from scratch**
on 15 × 15 or 20 × 20 worlds with 1–2 food items never learned to eat within 2 M episodes. Famine
and Harsh sit exactly there. Our agents start already able to eat; Pilot 1 decides whether that
carries over. Danger at 2.7× Home's hunter density with long chases may be too hard; Pilot 1 decides
that too, with a pre-named softening step (3.6).

### 3.3 Sequences and the stage-length rule (pre-registered)

| Sequence | Stage 1 | 2 (A) | 3 (B) | 4 (A again) | 5 (B again) | Now / later |
|---|---|---|---|---|---|---|
| **P1** Danger ↔ Famine | Forage | Danger | Famine | Danger | Famine | after pilots |
| **P2** Fog ↔ Danger | Forage | Fog | Danger | Fog | Danger | after pilots |
| **P3** Winter ↔ Famine | Forage | Winter | Famine | Winter | Famine | after pilots |
| P4 Famine ↔ Danger (P1 reversed: order control) | Forage | Famine | Danger | Famine | Danger | later |
| P5 Harsh ↔ Forage | Forage | Harsh | Forage | Harsh | Forage | later |

The pre-trained agent's 10 M episodes in Home **are** the Home stage. Home still appears in the
forgetting matrix (the pre-trained checkpoint is row 0).

**Plateau (defined on each Pilot 1 run, per agent, per world).** Survival is `Episode/Steps_mean`.
For every logged episode row at episode *e* (counted from the switch into the world), the trailing
mean is the mean survival over episodes (*e* − 200,000, *e*], weighting each row by the episodes it
covers (Δ `Episode/Number`). The run's **best window** is the largest trailing mean anywhere in the
pilot. **Time to plateau `T`** = the first *e* at which the trailing mean is within 5 % of the best
window (≥ 0.95 × best). `T` is reported in **episodes** and in **environment steps** (the sum of
Δ episodes × `Episode/Steps_mean` from the switch to *e*).

**Stage length (per concept X, same for both agents):**
`L_X = min(3,000,000, max(1,000,000, 1.5 × max(T_X,ordinary, T_X,modulated)))`, rounded up to a
multiple of 100,000, in episodes (the trainer's boundaries are episode counts; the environment-step
equivalent is reported for every stage, F3). Every visit to X lasts `L_X`, so first visit and return
are always the same length and both agents see the same schedule.
- **Why 1.5 × the slower agent:** the reference level `R_X` (5.1) is the last 200,000 episodes of
  the first visit; it must sit after both agents have levelled off, with margin.
- **Why a 1 M floor:** below it, the 200,000-episode reference window and the recovery window
  overlap.
- **Why a 3 M cap:** 5 stages × 3 M is the most a run can take and stay inside ~3 GPU-days on
  15 × 15 (throughput measured by Pilot 1; level 05 10 M took 19.4 h on 10 × 10).
- **Fallback — no plateau by the pilot's end.** If `T_X` falls in the last 500,000 episodes of a
  pilot (still climbing when the pilot ended), X is marked **"not plateaued"**: `L_X` = the 3 M cap,
  and every return measure in X carries the note "below plateau". It is not extended past the cap.
  If X also fails the survivable rule (3.6), the softening step applies instead.
- **Caveat carried forward:** the pilots switch **Home → X**; the main runs switch Forage → A and
  A ↔ B. Only the plateau time and the survivability verdict transfer from the pilots; the pilots'
  dips are *not* the main runs' dips.

The schedule files for P1–P3 are regenerated from the `L_X` values once Pilot 1 is analysed; the
2 M-per-stage boundaries in them today are **placeholders** and are marked PROVISIONAL in the files.

### 3.4 Starting agents, branching, and the shared-start confound

| Agent | Pre-trained run (level-05 factorial, all-rules-off world) | Final checkpoint | Agent config |
|---|---|---|---|
| Ordinary | `results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42` | episode 10,000,046 | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml` |
| Modulated (FiLM at encoder, RNN, actor, critic) | `results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42` | episode 10,000,021 | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml` |

Their final Home survival (factorial §7): 249.8 (ordinary) and 253.4 (modulated) steps.

**Branching (user decision).** Forage is trained **once per agent**, and it is Pilot 1's Forage run
(runs 1–2): same checkpoint, same world, same key, so it *is* the main runs' stage 1. Once `L_Forage`
is known, the branch point is the first checkpoint of that run at or after episode counter
`B0 = 10,000,000 + L_Forage` (checkpoints every 100,000; `L` is a multiple of 100,000, so it is the
checkpoint of the iteration that crossed `B0`). Because the trainer restores the **latest** checkpoint
in a directory, the step directory is copied (read-only copy, nothing moved or deleted) with the run's
`config.yaml` into `results/JAX_RecurrentPPO/cw_branchpoint_forage_<agent>_s42/models/`; each of the
three sequences then loads it with `--load-checkpoint`. The restored counter is ≥ `B0`, so each branch
starts directly in stage 2 (A); the Forage stage stays in the schedule file because the trainer sizes
its per-animal logging buffers from stage 0 before the restore, which is what keeps the workaround
for the animal-count bug valid (6.2 B1). Verified: a copied single step directory is what the
checkpoint manager returns as the latest step (6.1 C10).

**Confound (stated):** all three branches of an agent start from the **same weights, optimizer
state and random key**, so P1–P3 are not three independent replicates of the agent comparison, and
the ordinary and modulated agents differ in initialisation, capacity and seed as well as in the
modulator (factorial plan-review finding A2). Hence the "one initialisation pair, three world-pairs"
wording (section 2) and the fresh-seed pre-training (3.5). Branching removes the three near-duplicate
Forage copies, and with them the old noise yardstick (a); nothing is lost (5.5).

### 3.5 Fresh pre-training for the replicated version (2 more seeds per agent)

For each agent and seeds **43** and **44**: **Nursery for 2,000,000 episodes, then Home until the
episode counter reaches 10,000,000** (8 M Home episodes), as **two consecutive single-world runs**
(Nursery leg, then a Home leg that loads the Nursery leg's final checkpoint), because Nursery has one
hunting-predator slot and Home two, and that roster change crashes the continual trainer (6.2 B1;
smoke run S-B). **The seed-43 Nursery legs are Pilot 3** (runs 17–18): if Pilot 3 passes they
continue as production legs; if it fails they are not used and the user decides how to change
Nursery.

- **Nursery 2 M:** the curriculum study found easy levels learned within ~0.2 M episodes and that long
  over-training on easy levels hurt later learning (plasticity loss); 2 M is ample for the basics
  without lingering.
- **Home to 10 M total:** the fresh seeds get the same total experience and episode counter as the
  seed-42 pair. They later need their own Forage run to the same `B0` before branching.
- **Competence gate (pre-registered):** a fresh Home leg counts as competent when, over its last
  200,000 episodes, mean survival is **≥ 95 % of the same agent type's seed-42 Home level** (ordinary
  ≥ 237.3, modulated ≥ 240.7) **and** it rose < 5 % over its last fifth. If it fails at 10 M, it is
  reported, not extended silently.

### 3.6 Pilots (before any main run)

All pilots: `wandb-job-type` = `pilot`; both agents; checkpoints every 100,000 episodes; balance
metrics (`Episode/Bal_*`) are logged by the current trainer (the pre-trained runs predate them).

**Pilot 1 — one new world each, from the Home agent (12 runs; also the main runs' Forage stage).**
Each pre-trained agent is loaded from its Home checkpoint and trained in one new world only:
Forage for 4,000,000 episodes (counter to 14,000,000), Danger, Famine, Winter, Fog and Harsh for
3,000,000 each (counter to 13,000,000). Runs go to full length (the plateau rule needs the whole
curve; Forage must pass `B0`); a run is stopped early only under failure mode 7.1. It measures, per
world and per agent: the Home → X zero-shot dip (first 20,000 episodes vs. Home level), the time to
plateau `T` (3.3), the survivability verdict, and throughput (iterations/s, recorded in the manifest).

*Survivable rule (per world, on each agent's last 200,000 pilot episodes):*
1. mean survival ≥ **50 % of that agent's Home level** (ordinary ≥ 124.9, modulated ≥ 126.7 steps), and
2. mean `Episode/FoodEaten` ≥ **1.0** bite per episode (the from-scratch failure mode was ≈ 0.02).

A world passes if **both** agents pass. If exactly one agent fails, that is reported to the user as
a finding before any main run (not softened automatically). If both fail, the world is softened
**once** by its pre-named step and re-piloted; if it fails again it is dropped and its sequence
replaced by the user:

| Concept | One softening step if it fails |
|---|---|
| Forage | food 4–8 → 6–12 |
| Danger | hunting predators 5–7 → 3–5 (still 1.8× Home per cell) |
| Famine | regrow delay 30 → 10 steps |
| Winter | ambient −40 → −35 (fire heat factor re-checked for the first-step target) |
| Fog | noise σ halved (smell 0.15, sight 0.1) |
| Harsh | food 1–2 → 2–4 |

A world that passes with both agents ≥ 95 % of Home **and** a Home → X dip < 5 % is flagged **"too
easy to be a distinct world"** and shown to the user; it is not changed automatically.

**Pilot 2 — pipeline shakedown, NOT evidence (4 runs).** Pilot 2a: Home (pre-trained) → Forage →
Danger → Famine → Danger → Famine; Pilot 2b: Home → Forage → Fog → Danger → Fog → Danger; 1,000,000
episodes per stage, both agents. It exercises, on GPU and the real checkpoints: four stage switches
with changing grid size and animal counts, the checkpoint cadence at stage ends, `stage/index` rows,
and the forgetting-matrix sweep on a real continual run (the sweep's per-condition `--config`
bypasses `eval_rollout`'s refusal of a continual run's stage-0 `config.yaml`; tested here once).
1 M per stage is below the within-world plateau, so **its dips, recoveries and returns are not read
as evidence** for or against the modulator and are not pooled with the main runs. *Pass:* every run
completes all five stages with a `[STAGE]` line per switch, no traceback, 10 checkpoints per stage,
and the forgetting sweep produces a full matrix for one run.

**Pilot 3 — Nursery from scratch (2 runs; the seed-43 Nursery legs of 3.5).** Both agents, seed 43,
2,000,000 episodes. *Pass criterion (pre-registered), per agent, on the leg's last 200,000 episodes:*

| Skill | Measure (WandB key) | Threshold |
|---|---|---|
| Survives | mean `Episode/Steps_mean` | ≥ 200 steps (Home-trained agents: ≈ 250 in the harder Home) |
| Eats | mean `Episode/FoodEaten` and `Episode/Bal_EatRatio` (eating share when hungry ÷ when fed) | ≥ 15 bites per episode **and** ratio ≥ 2 |
| Hides when hurt | `Episode/Bal_HideRatio_True` (bush share when truly injured ÷ when not) | ≥ 2 |
| Warms | `Episode/Bal_TimeWarm` (share of steps on a warm cell) and `Episode/Bal_LateDeath_Thermal` (cold/heat share of late deaths) | ≥ 0.10 **and** ≤ 0.25 |
| Does not collapse | 200,000-episode trailing survival after the first window that meets all rows above | never below 0.8 × that window's value |

"Within N episodes" is N = 2,000,000; the first 200,000-episode window meeting all rows is reported as
the time to competence. Pass = all rows met on the last window. Fail → the leg is not used for
production and the user chooses (soften Nursery, or pre-train in Home alone).

## 4. Launch Manifest

All rows: `wandb-group` = `continual_worlds`. Tag = wandb-name. Scheme:
`rppo_cw_<cell>_<agent>_s<seed>`, agent ∈ {`t1none` ordinary, `t16quad` modulated}. Seed 42 rows load
the pre-trained pair; `--seed 42` is passed for the record, the restored key governs. Node / GPU are
assigned by the parent (candidate nodes 106–112, 102, 113; pack node-first).

**Launch order:** pilots (runs 1–18, all at once) → pilot verdicts, `L_X` computed, P1–P3 schedules
regenerated, branch-point copies made, user go → branches (19–24) and seed-44 Nursery legs (25–26) →
Home legs (27–30) after their Nursery leg ends (27–28 only if Pilot 3 passed).

| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|-----|--------|------|--------------------|-------------|----------------|------|------|-----|-------------|--------------|----------|
| 1 | running | Pilot 1 Forage (= main stage 1) | `rppo_cw_pilot1_forage_t1none_s42` | continual_worlds | pilot | 42 | 106 | cuda:0 | 2026-09-28T13:16:42 | `6sf68was` | `logs/20260928_131642.log` |
| 2 | running | Pilot 1 Forage (= main stage 1) | `rppo_cw_pilot1_forage_t16quad_s42` | continual_worlds | pilot | 42 | 106 | cuda:1 | 2026-09-28T13:16:46 | `e78og819` | `logs/20260928_131646.log` |
| 3 | running | Pilot 1 Danger | `rppo_cw_pilot1_danger_t1none_s42` | continual_worlds | pilot | 42 | 107 | cuda:0 | 2026-09-28T13:16:50 | `7e8rr45p` | `logs/20260928_131650.log` |
| 4 | running | Pilot 1 Danger | `rppo_cw_pilot1_danger_t16quad_s42` | continual_worlds | pilot | 42 | 107 | cuda:1 | 2026-09-28T13:16:53 | `gwkhnlpl` | `logs/20260928_131653.log` |
| 5 | running | Pilot 1 Famine | `rppo_cw_pilot1_famine_t1none_s42` | continual_worlds | pilot | 42 | 108 | cuda:0 | 2026-09-28T13:16:56 | `p0ev5nbw` | `logs/20260928_131656.log` |
| 6 | running | Pilot 1 Famine | `rppo_cw_pilot1_famine_t16quad_s42` | continual_worlds | pilot | 42 | 108 | cuda:1 | 2026-09-28T13:17:00 | `lf5tquew` | `logs/20260928_131700.log` |
| 7 | running | Pilot 1 Winter | `rppo_cw_pilot1_winter_t1none_s42` | continual_worlds | pilot | 42 | 109 | cuda:0 | 2026-09-28T13:17:04 | `s85qrj65` | `logs/20260928_131704.log` |
| 8 | running | Pilot 1 Winter | `rppo_cw_pilot1_winter_t16quad_s42` | continual_worlds | pilot | 42 | 109 | cuda:1 | 2026-09-28T13:17:07 | `4bapjjog` | `logs/20260928_131707.log` |
| 9 | running | Pilot 1 Fog | `rppo_cw_pilot1_fog_t1none_s42` | continual_worlds | pilot | 42 | 110 | cuda:0 | 2026-09-28T13:17:11 | `nealqwms` | `logs/20260928_131711.log` |
| 10 | running | Pilot 1 Fog | `rppo_cw_pilot1_fog_t16quad_s42` | continual_worlds | pilot | 42 | 110 | cuda:1 | 2026-09-28T13:17:14 | `4rkcrqzp` | `logs/20260928_131714.log` |
| 11 | running | Pilot 1 Harsh | `rppo_cw_pilot1_harsh_t1none_s42` | continual_worlds | pilot | 42 | 111 | cuda:0 | 2026-09-28T13:17:18 | `cssu3qc3` | `logs/20260928_131718.log` |
| 12 | running | Pilot 1 Harsh | `rppo_cw_pilot1_harsh_t16quad_s42` | continual_worlds | pilot | 42 | 111 | cuda:1 | 2026-09-28T13:17:22 | `xbpq1y9s` | `logs/20260928_131722.log` |
| 13 | running | Pilot 2a shakedown | `rppo_cw_pilot2a_t1none_s42` | continual_worlds | pilot | 42 | 112 | cuda:0 | 2026-09-28T13:17:26 | `tdpz3ju7` | `logs/20260928_131726.log` |
| 14 | running | Pilot 2a shakedown | `rppo_cw_pilot2a_t16quad_s42` | continual_worlds | pilot | 42 | 112 | cuda:1 | 2026-09-28T13:17:30 | `si97t2j5` | `logs/20260928_131730.log` |
| 15 | running | Pilot 2b shakedown | `rppo_cw_pilot2b_t1none_s42` | continual_worlds | pilot | 42 | 113 | cuda:0 | 2026-09-28T13:17:34 | `rygfw76a` | `logs/20260928_131734.log` |
| 16 | running | Pilot 2b shakedown | `rppo_cw_pilot2b_t16quad_s42` | continual_worlds | pilot | 42 | 113 | cuda:1 | 2026-09-28T13:17:38 | `zjsdfoyq` | `logs/20260928_131738.log` |
| 17 | running | Pilot 3 Nursery (= seed-43 leg) | `rppo_cw_nursery_t1none_s43` | continual_worlds | pilot | 43 | 102 | cuda:0 | 2026-09-28T13:17:41 | `98tm6jxe` | `logs/20260928_131741.log` |
| 18 | running | Pilot 3 Nursery (= seed-43 leg) | `rppo_cw_nursery_t16quad_s43` | continual_worlds | pilot | 43 | 102 | cuda:1 | 2026-09-28T13:17:45 | `q3ni07j6` | `logs/20260928_131745.log` |
| 19 | planned (after pilots) | P1 branch, ordinary | `rppo_cw_p1_t1none_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| 20 | planned (after pilots) | P1 branch, modulated | `rppo_cw_p1_t16quad_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| 21 | planned (after pilots) | P2 branch, ordinary | `rppo_cw_p2_t1none_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| 22 | planned (after pilots) | P2 branch, modulated | `rppo_cw_p2_t16quad_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| 23 | planned (after pilots) | P3 branch, ordinary | `rppo_cw_p3_t1none_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| 24 | planned (after pilots) | P3 branch, modulated | `rppo_cw_p3_t16quad_s42` | continual_worlds | prod | 42 | — | — | — | — | — |
| 25 | planned (after pilots) | Nursery leg | `rppo_cw_nursery_t1none_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 26 | planned (after pilots) | Nursery leg | `rppo_cw_nursery_t16quad_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 27 | planned (after 17, if Pilot 3 passes) | Home leg | `rppo_cw_home_t1none_s43` | continual_worlds | prod | 43 | — | — | — | — | — |
| 28 | planned (after 18, if Pilot 3 passes) | Home leg | `rppo_cw_home_t16quad_s43` | continual_worlds | prod | 43 | — | — | — | — | — |
| 29 | planned (after 25) | Home leg | `rppo_cw_home_t1none_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 30 | planned (after 26) | Home leg | `rppo_cw_home_t16quad_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 31 | running | Pilot 1s Danger-soft | `rppo_cw_pilot1s_danger_soft_t1none_s42` | continual_worlds | pilot | 42 | 101 | cuda:0 | 2026-09-28T16:20:23 | `ww9ck47l` | `logs/20260928_162023.log` |
| 32 | running | Pilot 1s Danger-soft | `rppo_cw_pilot1s_danger_soft_t16quad_s42` | continual_worlds | pilot | 42 | 101 | cuda:1 | 2026-09-28T16:20:24 | `kgvn98p5` | `logs/20260928_162024.log` |
| 33 | running | Pilot 1s Fog-soft | `rppo_cw_pilot1s_fog_soft_t1none_s42` | continual_worlds | pilot | 42 | 104 | cuda:0 | 2026-09-28T16:28:58 | `ruudv8i6` | `logs/20260928_162858.log` (shared with row 34; clean copy `wandb/run-20260928_162915-ruudv8i6/files/output.log`) |
| 34 | running | Pilot 1s Fog-soft | `rppo_cw_pilot1s_fog_soft_t16quad_s42` | continual_worlds | pilot | 42 | 104 | cuda:1 | 2026-09-28T16:28:58 | `il157bos` | `logs/20260928_162858.log` (shared with row 33; clean copy `wandb/run-20260928_162915-il157bos/files/output.log`) |
| 35 | running | Pilot 1s Harsh-soft | `rppo_cw_pilot1s_harsh_soft_t1none_s42` | continual_worlds | pilot | 42 | 103 | cuda:0 | 2026-09-28T16:20:25 | `dxkzhykp` | `logs/20260928_162025.log` |
| 36 | running | Pilot 1s Harsh-soft | `rppo_cw_pilot1s_harsh_soft_t16quad_s42` | continual_worlds | pilot | 42 | 103 | cuda:1 | 2026-09-28T16:20:26 | `hjktbwln` | `logs/20260928_162026.log` |

Rows 31–36 (Revision 1a) are judged by the same survivable rule and plateau rule as Pilot 1 (3.6,
3.3) and, if they pass, their `T` replaces the failed original's in the `L_X` computation for P1–P3.

**Compute (rough, to be replaced by Pilot 1's measured throughput):** level 05 ran 10 M episodes in
19.4 h on 10 × 10. Assuming 15 × 15 / 20 × 20 are 1.3–2× slower: Pilot 1 ≈ 8–12 h per 3 M run and
≈ 14–24 h for Forage 4 M; Pilot 2 ≈ 13–20 h per run; Pilot 3 ≈ 4 h. 18 GPUs, one run each.

### 4.1 Configs to Produce

`CW` = `configs/environment/experiment/continual_worlds/`; `CS` = `configs/continual/continual_worlds/`.
`T1` = `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml`, `T16` =
`.../nmngaenorm_t16quad_ALL.yaml` (unchanged; the pre-trained agents' own configs). `CK_O` / `CK_M` =
the ordinary / modulated pre-trained `models/` directories (3.4). `BP_O` / `BP_M` =
`results/JAX_RecurrentPPO/cw_branchpoint_forage_{t1none,t16quad}_s42/models` (made after Pilot 1, 3.4).

| Run | Env config (single world) or stage dir + schedule | Agent | Starts from | `--episodes` |
|-----|---|---|---|---|
| 1, 2 | `CW/forage_20x20.yaml` | T1, T16 | `CK_O`, `CK_M` | 14000000 |
| 3, 4 | `CW/danger_15x15.yaml` | T1, T16 | `CK_O`, `CK_M` | 13000000 |
| 5, 6 | `CW/famine_15x15.yaml` | T1, T16 | `CK_O`, `CK_M` | 13000000 |
| 7, 8 | `CW/winter_15x15.yaml` | T1, T16 | `CK_O`, `CK_M` | 13000000 |
| 9, 10 | `CW/fog_15x15.yaml` | T1, T16 | `CK_O`, `CK_M` | 13000000 |
| 11, 12 | `CW/harsh_15x15.yaml` | T1, T16 | `CK_O`, `CK_M` | 13000000 |
| 13, 14 | `CS/pilot2a_danger_famine_stages/` + `CS/pilot2a_danger_famine.yaml` (boundaries 11 M … 15 M) | T1, T16 | `CK_O`, `CK_M` | none (schedule) |
| 15, 16 | `CS/pilot2b_fog_danger_stages/` + `CS/pilot2b_fog_danger.yaml` (boundaries 11 M … 15 M) | T1, T16 | `CK_O`, `CK_M` | none (schedule) |
| 17, 18 | `CW/nursery_10x10.yaml` | T1, T16 | scratch | 2000000 |
| 19, 20 | `CS/p1_danger_famine_stages/` + `CS/p1_danger_famine.yaml` (**regenerated after Pilot 1**) | T1, T16 | `BP_O`, `BP_M` | none |
| 21, 22 | `CS/p2_fog_danger_stages/` + `CS/p2_fog_danger.yaml` (regenerated) | T1, T16 | `BP_O`, `BP_M` | none |
| 23, 24 | `CS/p3_winter_famine_stages/` + `CS/p3_winter_famine.yaml` (regenerated) | T1, T16 | `BP_O`, `BP_M` | none |
| 25, 26 | `CW/nursery_10x10.yaml` | T1, T16 | scratch | 2000000 |
| 27–30 | `CW/home_10x10.yaml` | as its Nursery leg | its Nursery leg's `models/` | 10000000 |
| 31, 32 | `CW/danger_soft_15x15.yaml` (Revision 1a) | T1, T16 | `CK_O`, `CK_M` | 13000000 |
| 33, 34 | `CW/fog_soft_15x15.yaml` (Revision 1a) | T1, T16 | `CK_O`, `CK_M` | 13000000 |
| 35, 36 | `CW/harsh_soft_15x15.yaml` (Revision 1a) | T1, T16 | `CK_O`, `CK_M` | 13000000 |

Rows 31–36 use exactly the flags of rows 3–12 (the Pilot 1 command in 4.2 with the world file and
tag swapped): `--load-checkpoint` the same pre-trained `CK_O` / `CK_M`, `--episodes 13000000
--checkpoint-frequency 100000 --seed 42`, `--wandb-group continual_worlds --wandb-job-type pilot`.

Each stage file is a one-line `extends:` of its concept file, so every visit to a concept is the
identical world. Checkpoints every 100,000 episodes everywhere (schedules set it per stage; single-
world runs pass `--checkpoint-frequency 100000`); the rPPO train config keeps all checkpoints.

### 4.2 Launch commands (for `training-runner`, via `run_command.py`, after the user's go)

`PY=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python`, run from the repo root. `--episodes`
is refused in continual mode (the schedule's last boundary is the budget); `--log-interval` is ignored
by these configs, so it is not passed.

```bash
# Pilot 1 (run 3 shown; runs 1-12 change world file, agent config, checkpoint dir, --episodes, tag)
$PY train.py --config configs/environment/experiment/continual_worlds/danger_15x15.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
  --episodes 13000000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
  --tag rppo_cw_pilot1_danger_t1none_s42 --wandb-name rppo_cw_pilot1_danger_t1none_s42 \
  --wandb-group continual_worlds --wandb-job-type pilot

# Pilot 2 (run 14 shown; 2b swaps in pilot2b_fog_danger)
$PY train.py --configs-dir configs/continual/continual_worlds/pilot2a_danger_famine_stages \
  --continual-schedule configs/continual/continual_worlds/pilot2a_danger_famine.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
  --load-checkpoint results/JAX_RecurrentPPO/20260927-053059_rppo_l05body_w0000_t16quad_s42/models \
  --seed 42 --device cuda:0 --tag rppo_cw_pilot2a_t16quad_s42 --wandb-name rppo_cw_pilot2a_t16quad_s42 \
  --wandb-group continual_worlds --wandb-job-type pilot

# Pilot 3 (run 17 shown; run 18 uses the T16 agent config and tag)
$PY train.py --config configs/environment/experiment/continual_worlds/nursery_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --episodes 2000000 --checkpoint-frequency 100000 --seed 43 --device cuda:0 \
  --tag rppo_cw_nursery_t1none_s43 --wandb-name rppo_cw_nursery_t1none_s43 \
  --wandb-group continual_worlds --wandb-job-type pilot

# Branch (run 20 shown; after Pilot 1 analysis, schedule regeneration and the branch-point copy)
$PY train.py --configs-dir configs/continual/continual_worlds/p1_danger_famine_stages \
  --continual-schedule configs/continual/continual_worlds/p1_danger_famine.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
  --load-checkpoint results/JAX_RecurrentPPO/cw_branchpoint_forage_t16quad_s42/models \
  --seed 42 --device cuda:0 --tag rppo_cw_p1_t16quad_s42 --wandb-name rppo_cw_p1_t16quad_s42 \
  --wandb-group continual_worlds --wandb-job-type prod

# Home leg (run 27 shown; after run 17 has finished and passed)
$PY train.py --config configs/environment/experiment/continual_worlds/home_10x10.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --load-checkpoint results/JAX_RecurrentPPO/<run-17 dir>/models \
  --episodes 10000000 --checkpoint-frequency 100000 --seed 43 --device cuda:0 \
  --tag rppo_cw_home_t1none_s43 --wandb-name rppo_cw_home_t1none_s43 \
  --wandb-group continual_worlds --wandb-job-type prod
```

## 5. Analysis plan (pre-specified)

Survival steps per episode is the only performance measure. Reward is not used for any verdict.
Curves are read from each run's WandB episode rows (`Episode/Number`, `Episode/Steps_mean`,
`Episode/_window_n`, `stage/index`) over the whole run, never from end-of-training snapshots alone.

### 5.1 Reference level and the three switch measures

For each world X in a sequence, its **reference level** `R_X` = mean survival over the **last 200,000
episodes of X's first visit**. For every switch into a visit v of X:

- **Dip** = 1 − (mean survival over the first 20,000 episodes of visit v) / `R_X`.
- **Recovery** = training after the switch until the 20,000-episode running mean first reaches
  **0.9 × `R_X`**, reported in **two units**: episodes, and environment steps (sum of Δ episodes ×
  `Episode/Steps_mean` from the switch). Censored at `L_X` if never reached ("not recovered"). The
  trainer updates once per fixed block of environment steps, so an agent that survives longer gets
  more updates per episode; counting in episodes alone would favour whichever agent already survives
  longer. **The H-rec vote counts only if the modulated-minus-ordinary difference has the favourable
  sign in both units.** The number of training iterations per stage is reported for every run.
- **Return** (visits 4 and 5 only) = (mean over the last 200,000 episodes of the return visit) − `R_X`,
  plus the change in dip and recovery from first visit to return.
- The previous stage's end level (its last 200,000 episodes) is reported next to every switch.

The first rows after a switch are partial windows (the trainer clears its rolling window at a switch);
rows are weighted by `Episode/_window_n` and rows under 1,000 episodes are skipped.

### 5.2 Modulator comparison

For every switch measure, the **modulated-minus-ordinary difference** (dip and recovery: negative
favours the modulator; return: positive). Reported per switch (4 per sequence), per sequence and
pooled across the 3 sequences, always next to the noise yardstick (5.5). The support / refute rule is
section 2's.

### 5.3 Forgetting matrix (no training)

Checkpoints: the pre-trained start (row 0), the Forage branch point (row 1, shared by the three
branches of an agent) and the **stage-end checkpoint** of stages 2–5 (the first checkpoint at or after
each boundary; saved at the end of the iteration that crossed it, before the world switches). Each is
evaluated on **all eight concept worlds** for **2,000 episodes** with the eval sweep driver
(`scripts/eval/dwell_sweep/run_sweep.py`, `probe: configs/environment/experiment/continual_worlds`,
`conditions:` the eight file stems, `algo: rppo`, **`episodes: 2000` set explicitly** — the key's
default is 30). Entries: mean survival steps with 95 % CI (≈ ±5 steps at 2,000 episodes for a
per-episode SD of 100–150). **Forgetting of world X at stage k** = survival on X at the end of X's
latest visit − survival on X at the end of stage k, with its CI from the two cells' standard errors.
**H-forget "beyond noise"** = the modulated and ordinary forgetting values' 95 % CIs do not overlap.
The sweep spec is written after the branches exist; Pilot 2 tests it once on a real continual run.

### 5.4 Plasticity and balance (logged; descriptive)

- **Policy entropy** (`loss/entropy`) is on the **iteration** stream, not the episode rows; its stage
  windows are cut by `stage/index` on that stream, and "first / last 200,000 episodes of a stage" is
  mapped to iterations through the episode counter logged alongside. A decline in recovery speed
  over stages together with falling entropy is read as plasticity loss.
- **Balance metrics** logged per episode (time shares in bush / on warm cell / eating, need-driven
  ratios, cause-of-death shares; [[BALANCE_METRICS_TRAINING_LOGGING]]) per stage, first vs. last
  200,000 episodes, first visit vs. return. Descriptive only.
- The modulated-minus-ordinary difference is reported for entropy and the balance shares.

### 5.5 Noise yardstick (a floor, not an estimate)

With one starting pair, noise cannot be measured properly; two stand-ins are used and the verdict
says so:

- **(b) Seed floor:** the level-05 factorial's seed SD of survival (1.5 steps at ≈ 250), i.e. ≈ 2.1
  steps for a difference of two single runs. It was measured in Home, not in these worlds, so it is a
  **floor**.
- **(c) Within-visit checkpoint spread:** for each agent and visit, the SD of the non-overlapping
  200,000-episode window means over the visit's post-plateau part (from `T_X` to the end of the
  visit); for a difference, √2 × the larger of the two agents' SDs.

A modulated-minus-ordinary difference counts as "beyond noise" only if it exceeds **2 × the larger of
(b) and (c)** in that world's survival units. The May probe's ±4.4-step seed spread is printed next to
every difference for scale. The old yardstick (a) (three near-duplicate Forage copies) no longer
exists after branching and is dropped.

### 5.6 Temporal evolution

Every figure is a curve over training episodes (and, for recovery, environment steps) with stage
boundaries marked: survival (20,000-episode running mean), entropy, balance shares, both agents on one
axis per sequence. Pilot 1 figures show all six worlds' Home → X curves with `T` marked.

## 6. Pre-launch checks

### 6.1 Verified (2026-09-28, read-only, project interpreter, CPU)

| # | Check | Result |
|---|---|---|
| C1 | All 8 world configs load through `load_env_config` → `load_env_params` (the trainer's path) | pass (re-run after Revision 1) |
| C2 | Observation width 58 on every world (real `ParallelEnv.reset`); body / thermal-body / interoception / reward fields identical to level 05 | pass (re-run after Revision 1): every differing field is external — per-entity arrays, grid, smell range, ambient and fire settings, Fog's noise table and blur |
| C3 | 1,000 real resets per world: every placed type spans its allowed area to within 1 cell; nothing at (0,0) where excluded; every drawn fire inside its inset and ≥ 4 from other fires; **mean placed = mean drawn for every type** | pass on all 8 (re-run after Revision 1), e.g. Danger hunters 5.98, ambushers 20.62, bushes 22.57; Winter fires 1.00. Per-cell table in 3.2 is from this run |
| C4 | Thermal: every reset has ≥ 1 survivable cell; worst first step from the warm ring onto a fire < +15 | pass before Revision 1 (worst +12.4; Winter 11.73 at factor 10). Revision 1 changed no fire count, heat factor or ambient, so the thermal field is unchanged by construction |
| C5 | Hunting-predator / rabbit slot counts per world | Home 2/2, Nursery 1/2, Forage 0/5, **Danger 7/5, Famine 2/5, Winter 2/5, Fog 5/5, Harsh 5/5** (Revision 1) |
| C6 | Pre-trained checkpoints exist and are final | ordinary 10,000,046; modulated 10,000,021 |
| C7 | The two stale stage tests (Known Bugs row "8-wide vision") | still fail as recorded (hand-off in 6.2) |
| C8 | All five schedules (P1–P3 provisional, Pilot 2a/2b) built by `train._build_continual_schedule` itself | pass: 5 stages each; Pilot 2 boundaries `[11M … 15M]`, P1–P3 `[12M … 20M]` (placeholders); restored counters 10,000,046 / 10,000,021 map to stage 0; a counter just past the first boundary maps to stage 1; every stage resolves to its concept world with width 58 and the expected hunter slots (Forage 0 first in every schedule) |
| C9 | Smoke runs before Revision 1 | S-A (ordinary checkpoint through six grid-size / roster / noise switches) pass; S-B (Nursery → Home as one continual run) crashes as Known Bug A2 predicts → two-leg pre-training; S-C (modulated checkpoint, Forage → Danger) pass. Pilot 2 repeats S-A's path on GPU with the Revision 1 counts |
| C10 | Branch-point mechanism: one step directory copied with `config.yaml` into a fresh `models/` dir | the checkpoint manager returns that step as the latest (tested on step 9,800,027 of the ordinary pre-trained run in scratch space) |
| C11 | Revision 1a softened worlds: each loaded through `load_env_config` → `load_env_params` next to its original and every `EnvParams` field compared | pass. **Fog-soft:** 1 of 208 fields differs, `noise_sigmas` (smell 0.3 → 0.15, sight 0.2 → 0.1). **Danger-soft:** only `animal_count_low/high` (hunters [5, 7] → [3, 5]); every other differing field is a per-slot array or index that is 2 slots shorter (12 → 10), with per-entry values identical. **Harsh-soft:** only `res_count_low/high` (food [1, 2] → [2, 4]); the rest are per-slot arrays 2 slots longer (29 → 31), per-entry values identical. No body, thermal, interoception or reward field differs. Observation width 58 on all six (real `ParallelEnv.reset`) |

### 6.2 Blockers and hand-offs

- **B1 — roster-size change between stages (Known Bugs A2) — workaround accepted by the user.** The
  trainer sizes its per-animal distance buffers from stage 0 and never resizes them. Every
  continual run here (Pilot 2, the branches) has Forage (no hunting predator, 5 rabbit slots) as stage
  0 and 5 rabbit slots in every stage, so per-predator distance logging is off and nothing crashes.
  Cost: no per-predator distance curves. Pilot 1 and Pilot 3 are single-world runs and unaffected.
- **B2 — pilots not yet run.** No branch launches before Pilot 1 is analysed, `L_X` computed and the
  P1–P3 schedule files regenerated and re-built (C8 repeated).
- **Hand-off to `developer` (via `senior-developer`):** fix the two stale continual tests (C7). Until
  fixed, the continual stage-switch and resume paths have no passing regression test; the smoke runs
  and Pilot 2 are this design's substitute.
- **Known and accepted:** Known Bugs B5 (a resumed single-world run pairs restored recurrent memory
  with fresh worlds for its first window) affects the first rows of the Pilot 1 runs and Home legs.

### 6.3 Still to check at launch (`training-runner` / `env-config-reviewer`)

- `env-config-reviewer` pre-flight on the five changed worlds and the two new Pilot 2 schedules.
- Live GPU state (diary + `pgrep`, not only `nvidia-smi`) and NAS mount on each node.
- First stage switch of each continual run: `[STAGE] 0:01_forage -> 1:02_...` and no traceback; for
  a branch, the `[RESUME]` line naming stage 1.
- Before the branches: repeat C8 on the regenerated schedules and C10 on the real branch-point copy;
  the smoke path S-A is re-run on the launch node if HEAD has moved since Pilot 2.

## 7. Failure-mode catalog (decided in advance)

| # | Outcome | Reading |
|---|---|---|
| 7.1 | NaN / value explosion in one run | that run is invalid, relaunched once from its last good checkpoint; not evidence about the modulator |
| 7.2 | Neither agent dips at any switch (dip < 5 % everywhere) | the worlds are not distinct enough; null for this design, not for the hypothesis |
| 7.3 | A world is never recovered (censored) for both agents | its switch measures are reported but excluded from the support / refute count |
| 7.4 | Only one agent collapses in a world (survival < 0.6 × its `R_X` for the whole visit) | reported and marked; the verdict is computed with and without that sequence |
| 7.5 | Late stages learn more slowly for both agents | plasticity loss, recorded as a result (5.4); not a design flaw |
| 7.6 | Differences all within the noise yardstick | null for this screen; the fresh-seed replication decides |
| 7.7 | A stage switch crashes | run invalid; resume from its last checkpoint after the fix |
| 7.8 | A Pilot 1 world has not plateaued by the pilot's end | `L_X` = 3 M cap, returns in X marked "below plateau" (3.3) |
| 7.9 | Recovery favours the modulator in episodes but not in environment steps (or the reverse) | the H-rec vote is not counted for that switch (5.1) |
| 7.10 | Pilot 3 fails | the seed-43 Nursery leg is not used; user decides Nursery's fate before runs 25–30 |

## 8. Metrics requested (optional, for the user)

| Metric | Why now | Where it'd live | Cost |
|---|---|---|---|
| Per-stage modulator activity (mean and spread of the FiLM scale and shift per site, per stage) | the "why" behind any H-dip / H-ret effect | `train.py` rPPO logging, `mod_info` already returned by the train step | cheap |
| Per-predator distance curves across roster changes | lost under B1's workaround | `train.py` continual stage switch (A2 fix) | cheap |
| Cumulative environment steps on the episode rows | makes F3's step-unit recovery exact rather than reconstructed | `train.py` `_emit_episode_row` (`global_step`) | cheap |

If accepted, route through `feature-workflow` before launch; none blocks the pilots.

## 9. Decisions (all taken 2026-09-28; user: "follow your recommendations")

1. B1: no-code workaround accepted (no per-predator distance curves).
2. Fog: 3× blur + smell/sight noise accepted in place of vision range 1.
3. Winter: fire heat factor 10 accepted.
4. Famine: 1–2 items, regrowing after 30 steps, anywhere, accepted.
5. Forage once per agent, sequences branch from it (3.4).
6. Pilots: the three-pilot set of 3.6.

## 10. Results

*(blank until the runs finish)*

## 11. Conclusions

*(blank until the runs finish)*

## Feedback from plan-reviewer

**Verdict: SOUND WITH CONCERNS** (2026-09-28, reviewed against commit `95b34d01`, before any launch).
The A-B-A-B design is measurable in survival steps only, its refutation rule is written down in
advance, its configs resolve through the trainer's own loader, and the stage-switch path was
exercised end to end by real smoke runs. What is not ready is the **pilot phase as committed**:
the manifest names six ordinary-only 1 M-episode pilots (§3.6, §4 rows 1–6), while the pilots
the user asked to launch now are (Pilot 1) a single switch from the Home agent into each of the
six new worlds for **both** agents, up to 3–4 M episodes, to measure the dip, the time to level off
and survival; (Pilot 2) short 1 M-per-stage A-B-A-B runs of P1 and P2 for both agents; and
(Pilot 3) Nursery from scratch for both agents. None of those is in the doc, no schedule file
exists for Pilot 2, and the rule that turns "time to level off" into a stage length is not yet
written down. That is doc-and-config work (an hour, `experiment-designer`), not a flaw in the
science, but launching from the manifest as it stands would launch the wrong pilots. No Critical
finding: no `docs/reviews/` file is written.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### Findings

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| F1 | 🟡 | §3.6, §4 rows 1–6, §4.1 | The committed pilots (ordinary only, 1 M, `--episodes 11000000`) are not the pilots requested. Pilot 1 needs 12 rows (both agents; `--episodes 13000000`–`14000000` on the restored counter), Pilot 2 needs two new schedule files with boundaries `[11M, 12M, 13M, 14M, 15M]` and their stage folders (4 rows), Pilot 3 is manifest rows 13 and 15 as written (Nursery legs, seed 43) — say so, or use a dedicated seed so the pilot is not also a production leg. | Rewrite §3.6 and the manifest to the three-pilot set before `training-runner` is spawned; add the Pilot 2 schedules under `configs/continual/continual_worlds/`. | experiment-designer |
| F2 | 🟡 | §3.3, §3.6 (stage-length rule) | "Stage length = 1.5 × time to plateau" has no pre-registered definition of *plateau*, no rule for combining the two worlds of a pair (and the two agents), no fallback if a pilot has not levelled off by 3–4 M, and no feasibility cap. A 3 M plateau gives 4.5 M stages and 22.5 M-episode main runs — 4–5 GPU-days each at 15 × 15 speed (§3.3's own 2-day ceiling would be breached). Also: the pilots switch **Home → X**; the main runs switch Forage → A and A ↔ B, so the pilot's dip is not the main run's dip — only the plateau time and the survivability verdict transfer. | Pre-register: plateau = first episode at which the 20 000-episode running mean stays within 5 % of the pilot's last-200 000 mean for the rest of the pilot; stage length = 1.5 × the **largest** plateau over both worlds and both agents of the pair, rounded up to 100 000 and **capped at 3 M** (3 × 5 = 15 M episodes on top of 10 M); if a world has not levelled off by the pilot's end, that is a survivability fail (§3.6 softening step), not a longer stage. Schedules are regenerated from that number, so §4.1's `[12M…20M]` are provisional and must be marked so. | experiment-designer |
| F3 | 🟡 | §5.1 Recovery, §2 H-rec | Stages and recovery are counted in **episodes**, but the trainer updates per iteration of fixed environment steps (`num_envs × num_steps`), so an agent that survives longer gets **more gradient updates per 20 000 episodes**. Recovery-in-episodes therefore favours whichever agent already survives longer — the same agent H-dip favours — a systematic bias, not noise. It also makes a 2 M-episode stage in a 120-step world half the training of one in a 250-step world. | Report every recovery time in both units: episodes and cumulative environment steps (reconstructible per row as Σ `Episode/Steps_mean × window episodes`; `global_step` is not on the episode rows). Make the H-rec vote require the favourable sign in **both** units. Keep episode-based boundaries (the trainer supports nothing else) but state the per-stage update count in the results. | experiment-designer (rule); experiment-analyzer (extraction) |
| F4 | 🟡 | §5.5 Noise yardstick | Yardstick (b) is the **Home** seed SD (1.5 steps at ~250 survival) applied to Danger / Famine / Winter / Fog, where nobody has measured seed spread and where the earlier continual probe saw ±4.4 steps on a harder world. Yardstick (a) (three near-duplicate Forage segments) measures GPU non-determinism only. A 5-step Famine gap can clear "2 × the larger" and still be seed noise. | Say the yardstick is a floor, not an estimate; add the across-checkpoint spread of the 200 000-episode window means within a visit (the factorial's own device) as yardstick (c); and, if Open decision 5 is taken (branch from one Forage run), drop (a) with nothing lost. | experiment-designer |
| F5 | 🟡 | §5.3 Forgetting matrix | 500 evaluation episodes per cell gives a 95 % CI of roughly ±9–13 survival steps (per-episode survival SD is ~100–150 in these worlds), so the matrix cannot resolve differences at the §5.5 scale, and H-forget's vote in the §2 rule has no noise criterion of its own. The sweep spec's episode count is the `episodes:` key (default 30), so it must be set explicitly. | Set `episodes: 2000` (evaluation is cheap: one model build per checkpoint) and pre-register H-forget's "beyond noise" as non-overlapping CIs. | experiment-designer |
| F6 | 🟡 | §1 ("So far the modulator has only been tested in one world at a time"), §2 | Prior art: [[NMN_CONTINUAL_DOUBLE_RETURN_PROBE]] (2026-05) already ran a 5-stage A-B-A-B-A external-world switch (active ↔ passive predator; body unchanged) and reported the modulated agent ~107–132 steps ahead on the return stages, less forgetting confirmed, and the dip predicate found ill-posed. This design is a **replication at scale** of that positive (tiny 1 500-episode stages, MC returns, single seed then) with a stationary-body framing — say so, and let the pre-registered prediction inherit its lesson that the dip lives in recovery speed, not depth. As written the doc contradicts a result the project already has. | Rewrite the §1 sentence; add one paragraph in §2 positioning H-ret / H-forget as the replication targets and the earlier ±4.4-step noise. | experiment-designer |
| F7 | 🟡 | §2 support rule | "2 of 3 sequences" counts sequences as independent votes; §3.4 already says they are not (same weights, same optimizer state, same key; P1 and P3 share Famine, P1 and P2 share Danger). A single lucky initialisation pairing wins 3 of 3. | Keep the rule but state that its support verdict is "one initialisation pair, three world-pairs"; the fresh-seed replication (§3.5) is the only route to "the modulator". | experiment-designer |
| F8 | 🟢 | §4.2 | Launch commands read `python train.py`; the project runs `/home/vncuser/miniconda3/envs/grid_world_pain/bin/python`. The runner's script owns the interpreter, but the doc should not show the wrong one. | Replace the interpreter. | experiment-designer |
| F9 | 🟢 | §5.4 | `loss/entropy` is on the iteration stream, not the episode rows; "per stage, first / last 200 000 episodes" needs the iteration → episode mapping. | Say the entropy windows are cut by `stage/index` on the iteration stream. | experiment-analyzer |

### Verified — claims I tried to break and could not

- **A2 workaround holds.** `train.py:1410-1415` sizes the per-animal accumulators from stage 0; `train.py:1773` never puts `dist_per_predator` into the info dict when `num_predator_for_log == 0`, so a Forage-first run never touches the crashing line (`train.py:1825`). The behaviour-measure toolkit is off (`behavior_measures.enabled: false` in the pre-trained runs' saved config), so nothing else is sized from stage 0. Cost is exactly what §6.2 says: no per-predator distance curves. Nearest-predator distance (`dist_to_pred`), survival, food eaten and the balance counters come from the current stage's environment.
- **Grid size is not a direct cue.** The pre-trained agents have `location_sensor: false` (saved config), so no absolute-position channel rescales with the grid; walls are only seen within vision range 2. And within every A ↔ B pair both worlds are 15 × 15 — the grid changes once (Forage → A) and never on the alternation being measured. Good property; state it in §3.2.
- **Stage-end checkpoint claim** (§5.3): the transition check runs at the top of an iteration (`train.py:1663`) and the checkpoint scheduler at the bottom (`train.py:2601`); boundaries are multiples of 100 000, so the first checkpoint at or after a boundary is the crossing iteration's, saved before the world switches. One extra checkpoint is written at the first iteration after a restore (`last_checkpoint_save` starts at 0) — harmless, it is row 0.
- **Restore picks the right checkpoint** — `mngr.latest_step()` (numeric), not a string sort; S-A/S-C confirm 10 000 046 / 10 000 021.
- **Fog's noise table** lists all 12 modalities in `default.yaml`'s order; `env-config-reviewer` owns the mechanical obs ↔ noise check.
- **Episode-vs-checkpoint arithmetic**: `--episodes` is the absolute counter (`train.py:1656`), so `--episodes 11000000` on a 10 000 046 restore is ≈ 1 M more; Nursery 2 M → Home `--episodes 10000000` lands the fresh seeds on the same counter the schedules assume.
- Registry change-log entry present (CONFIG_CRITICAL_SETTINGS.md, 2026-09-28); no `scripts/` change; no schema change; no destructive git step anywhere in the plan.

### Can the pilots answer "is it working as expected"?

- **Pilot 1 (single switch, both agents, 3–4 M)** answers survivability, plateau time and the Home → X zero-shot dip, per world and per agent. It does **not** measure the main run's dips (different source world) and, with the same weights and key as the main runs, its Forage segment is a near-copy of main-run stage 1. Worth it, provided F2's plateau rule is written first — otherwise the number it produces has no consumer.
- **Pilot 2 (1 M-per-stage A-B-A-B, both agents)** is a **pipeline shakedown**, not a science pilot: four GPU stage switches on the real checkpoints, checkpoint cadence, `stage/index` rows, the forgetting-matrix sweep on a real continual run (`eval_rollout` refuses stage-0 `config.yaml` for continual runs — the sweep's per-condition `--config` bypasses it; test that once here). By §3.3's own argument 1 M is below plateau, so its return-visit numbers must not be read as evidence. Frame it that way in the doc.
- **Pilot 3 (Nursery from scratch, both agents)** has no pass criterion — only the Home leg has one (§3.5). Pre-register one (e.g. last-200 000 survival and bites ≥ 1, no collapse), otherwise the leg cannot fail.

### Assumptions the conclusion rests on

| Assumption | Status |
|---|---|
| The pre-trained pair is competent enough that Famine / Harsh do not reproduce context-exploration's "never learns to eat" | unverified — that is what Pilot 1 tests (good) |
| Seed noise in the new worlds is of the Home order (1.5 steps) | unverified; F4 |
| 15 × 15 / 20 × 20 throughput keeps a 10–15 M-episode run under ~2–3 days | unverified; Pilot 1 measures it — record it/s in the manifest |
| `nmngaenorm_t1none.yaml` is the no-modulator baseline (not a one-site modulator) | verified via the level-05 factorial's own labelling; not re-derived here |
| The three smoke runs (S-A … S-C) ran on the same code as the launch will | unverified — HEAD moves; re-run S-A once on the launch node before run 7 |
| GPU non-determinism is small relative to seed noise | untested; the three Forage copies will show it, or branching removes the question |

### Cost of being wrong

If the pilots launch from the manifest as committed, the cost is one day of six wrong 1 M runs
and a second pilot round. If the stage length is set without F2's rule, the cost is twelve
10–20 M-episode main runs (2–5 GPU-days each) whose return-visit measure sits below plateau and
cannot be re-read. If F3 is left as is, the headline "recovers faster" claim carries a built-in
bias in the modulator's favour and would not survive a referee. Nothing here risks data loss.

Reviewed by: plan-reviewer

### Response from experiment-designer (Revision 1, 2026-09-28)

| # | Resolution | Where |
|---|---|---|
| F1 | Pilots replaced by the requested three-pilot set (18 rows); Pilot 2 schedules and stage folders added; Pilot 3 is the seed-43 Nursery legs, stated | 3.6, 4, 4.1, `configs/continual/continual_worlds/pilot2{a,b}_*` |
| F2 | Plateau, per-concept stage length (1.5 × slower agent, 1 M floor, 3 M cap), no-plateau fallback pre-registered; P1–P3 boundaries marked provisional in the files | 3.3, 7.8 |
| F3 | Recovery in episodes and environment steps; H-rec vote needs both; iterations per stage reported | 2, 5.1, 7.9 |
| F4 | Yardstick stated as a floor; within-visit checkpoint spread added; (a) dropped with branching; May ±4.4 printed alongside | 5.5 |
| F5 | 2,000 episodes per cell, `episodes: 2000` explicit; non-overlapping 95 % CIs for H-forget | 5.3 |
| F6 | May probe cited in section 1; replication framing and "recovery speed over dip depth" lesson in section 2 | 1, 2 |
| F7 | Verdict wording "one initialisation pair, three world-pairs" | 1, 2, 3.4 |
| F8 | Project interpreter in every command | 4.2 |
| F9 | Entropy windows cut by `stage/index` on the iteration stream | 5.4 |

Signed: experiment-designer
