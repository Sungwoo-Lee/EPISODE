---
title: "Continual worlds: does the modulator help an agent move between worlds whose body rules never change?"
topic: continual_worlds
status: active
created: 2026-09-28
last_updated: 2026-09-29
phase: continual / A-B-A-B structure (user framing 2026-09-28)
wandb_tag: "rppo_cw_*"
---

# Continual worlds: an A-B-A-B test of the modulator with a stationary body

> **Status (2026-09-28, Revision 2a — answers the plan-reviewer's Revision 2 gate):** one analysis
> rule is added before anything main launches (box below); **Winter ↔ Famine is still the only ready
> sequence**, now also waiting on the Pilot 2 closure (run 14 ending, one forgetting-sweep test).
> Nothing new is launched by this revision.
>
> *Revision 2 status, kept for the record:* the pilots are read out (Revision 2
> box below). **One sequence, Winter ↔ Famine, is ready** to launch once the Forage runs have finished
> and the pre-launch checklist (6.3) passes; **the other two need the user's decision** on replacement
> worlds (3.7.6). Nothing new is launched by this revision.
> *Revision 1b status, kept for the record:* the softened Danger, Fog and Harsh worlds (rows 31–36) still
> fail at the interim read-out, so the pre-registered rule drops them and their replacement goes to
> the user; an exploratory, not-pre-registered scouting ladder (five ordinary-agent runs, rows 37–41,
> **planned, not launched**) gives the user options (Revision 1b box below).
> *Revision 1a status, kept for the record:* pilots 1–18 **running** since 13:16; an interim read-out
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

> **Revision 2a (2026-09-28, late night) — a fairer yardstick for "who adapts faster", in plain
> words.** Two of the four "did the modulator help?" measures — how far survival drops right after a
> switch into a world, and how long it takes to climb back — were defined against **each agent's own**
> settled level in that world. The pilots showed why that is unfair: in the cold world (Winter) the two
> agents started out almost equal right after the switch (129 vs 138 survival steps), but the ordinary
> agent later settled much higher (198 vs 161). Measured against its own higher target, the ordinary
> agent "took" 132,000 episodes to recover and the modulated agent 40,000 — a 3× "win" for the
> modulator that is really just "the modulated agent's target was lower". Measured against **one
> shared target** (90 % of the lower of the two settled levels), the order **reverses**: 28,000 vs
> 40,000 episodes. So, fixed **before** any main run launches: dip and recovery are now read **both
> ways** — against each agent's own level and against a shared level — and a vote counts for the
> modulator only if **both readings agree** (5.1, new paragraph "Common-reference companion"). The
> "return" and "forgetting" measures are already absolute survival steps and are unchanged. Also
> corrected: Winter did **not** simply level off for the modulated agent (it peaked, then slid 8.5 %;
> 3.7.1); the pipeline trial is **3 of 4 checks passed, provisional** (3.7.5); the launch checklist now
> names the log lines a branch really prints (6.3); a new user decision D8 asks whether the branches
> must wait for the Forage runs to finish (3.7.6). Response table at the bottom of this doc.

> **Revision 2 (2026-09-28, night) — what the pilots found and what happens next, in plain words.**
> Before the long runs, short trial runs ("pilots") checked each new world: can our two pre-trained
> agents — the ordinary one and the one with the modulator — survive there at all, and how long do
> they take to level off? **Two worlds pass for both agents:** the scarce-food world (Famine) and the
> cold world with a single fire (Winter). **Three worlds fail for both agents even after their one
> pre-planned softening step** — the world with many hunters (Danger), the foggy world (Fog) and the
> cold-hungry-hunted world (Harsh) — so, by the rule written before the pilots, they are **dropped**.
> That leaves one of the three planned alternating sequences intact: **Winter ↔ Famine**. Its stage
> lengths now follow from the pre-registered rule (each Winter visit 3 million episodes, each Famine
> visit 1 million) and its schedule file is **ready**. The other two sequences lost their Danger
> world (one also its Fog world). Extra scouting runs, **not planned in advance**, found two
> survivable variants — a Danger world whose hunters give up as quickly as Home's ("Danger-A") and a
> Fog world without sensory noise ("Fog-B"). We **draft** two replacement sequences from them, but
> they **need the user's approval**: Danger-A is survivable for the modulated agent only (the
> ordinary agent falls just short, 122.6 against a 124.9-step line), and both variants were found by
> exploring, not pre-registered. The pipeline trial and the from-scratch warm-up world both passed.
> Two places where the pre-registered rules differ from the working assumption at writing time
> (stage length set per world, not per pair; branch point at 11 M episodes, not 14 M) are listed as
> user decisions (3.7.6). Details: section 3.7.

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

> **Revision 1b (2026-09-28, late evening) — an EXPLORATORY scouting ladder for Danger and Fog.
> NOT pre-registered; it does not change any verdict.** A refreshed interim read-out shows that the
> once-softened worlds (rows 31–36, about 2 M of their 3 M episodes in, curves flat) **still fail** the
> survivable rule for both agents (ordinary / modulated, last-200k survival in steps; pass lines 124.9 /
> 126.7): Danger-soft 91.6 / 91.2, Fog-soft 113.6 / 110.6, Harsh-soft 93.5 / 94.5. The pre-registered
> rule (3.6) therefore stands: **each of these worlds is dropped and its sequence goes to the user
> for replacement** — that decision is the user's, and nothing below makes it for them. (Numbers are
> interim until the runs end, as in Revision 1a.)
>
> *Why scout anyway.* Danger sits in sequences P1 and P2, so dropping it removes two of the three
> sequences. Deaths in all three softened worlds split roughly **45 % injury / 40–45 % starvation** —
> starvation is large even where food density is Home-like. Our reading (a hypothesis, not a result):
> the short smell range (5 cells; Fog 3) plus heavy predator pressure keeps the agent from foraging.
> Famine is the contrast: the same smell range 5 and even less food (1–2 items), but only 0–2 hunters
> that give up quickly — and it passes at ≈ 210 steps. So the scouts vary **predator persistence,
> predator count, smell range and noise**, one or two at a time, to show the user which factor makes
> the world survivable. They are options for the replacement decision, nothing more.
>
> | Scout | What changes vs the original world | Question it answers |
> |---|---|---|
> | Danger-scout-A | hunters 5–7 → 3–5 (as Danger-soft) **and** Home's hunting style: notice the agent from 3–5 cells (Danger 5–9), chase stamina 30–150 (Danger 100–200), give up at 1.5 (Danger 2.0) | Is it how *persistent* the hunters are, rather than how many? |
> | Danger-scout-B | hunters 5–7 → 2–4; Danger's own detection and chase | Is one more step down in count enough? |
> | Danger-scout-C | hunters 3–5 (as Danger-soft) + smell range 5 → 8 | Is finding food under threat the bottleneck? |
> | Fog-scout-A | Fog-soft (noise halved) + smell range 3 → 5 | Does a longer smell range rescue Fog? |
> | Fog-scout-B | Fog's smell range 3 and 3× sight blur, but **no perceptual noise at all** | Is it the short range or the noise? (read against Fog and Fog-soft) |
>
> Harsh comes later in the sequences (stage 5), so it is not scouted now. Everything else — the body
> (level 05), the 58-number observation, vision range — is unchanged (check C12, 6.1). "Smell range"
> is the olfactory radius (`sensory.sensor_radius`), which does not change the observation width.
>
> *Runs.* Ordinary agent only, from the seed-42 pre-trained Home checkpoint, 1.5 M episodes each
> (`--episodes 11500000`; Pilot 1 plateaus came at 0.2–0.9 M), otherwise the flags of rows 3–12;
> job type `pilot`; manifest rows **37–41**, planned. *Reading (descriptive, not a gate):* the same
> survivable rule on the last 200,000 episodes, reported per scout with the death split (injury /
> starvation) and bites per episode, plus the survival curve over training. A scout that passes with
> the ordinary agent is a *candidate* only; a world the user adopts from it still needs the modulated
> agent's pilot before it enters a sequence. One seed, one agent: no claim beyond "this variant looks
> survivable / not" is drawn from these runs.
>
> Other interim observations, recorded, **nothing changed**:
> - **Winter, modulated agent recovered to pass**: 156 steps against its 126.7 line (ordinary 205);
>   Revision 1a's borderline note is resolved pending the final read-out.
> - **Seed-43 Home legs** (rows 27–28, started from the Nursery warm-up) reached ≈ 238 steps of
>   survival within ≈ 1 M Home episodes — already at the Home competence gate (237.3 ordinary /
>   240.7 modulated).
>
> Source: `results/analysis/continual_worlds/pilot_readout.json` (refreshed 2026-09-28).

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
- *Revision 2a addition (pre-registered before any main run):* H-dip and H-rec are each read twice —
  against the agent's **own** reference level (as above) and against a **common** reference shared by
  both agents (the lower of the two agents' reference levels; 5.1). The H-dip vote counts only if the
  modulated-minus-ordinary difference is favourable under both readings; the H-rec vote only if it is
  favourable under all four readings (own / common × episodes / environment steps). Otherwise that
  switch's vote is "not counted" (7.11).
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
*Revision 2:* P3 regenerated (`[11M, 14M, 15M, 18M, 19M]`); P1 and P2 lost their Danger / Fog worlds and
are replaced by drafts pending the user's approval (3.7).

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

### 3.7 Post-pilot verdicts and the revised sequences (Revision 2, 2026-09-28)

**What this section settles.** It applies the pre-registered pilot rules (3.3 stage length, 3.6
survivable rule) to the final pilot numbers, says which sequences can run, and lists what the user
must decide. All survival numbers are **mean survival steps per episode over each run's last 200,000
episodes** (the pass line is half of the agent's own Home level: 124.9 ordinary / 126.7 modulated;
bites ≥ 1.0 per episode). Source: `scripts/analysis/studies/continual_worlds/pilot_readout.py` →
`results/analysis/continual_worlds/pilot_readout.json`, full print `tmp/20260928_pilot_readout_run4.log`.
Every number below is **final** (run ended) unless marked *provisional*.

#### 3.7.1 Per-world verdicts

| World | Ordinary: survival / bites | Modulated: survival / bites | Deaths, ordinary (injury / starvation / cold-heat / reached 500-step cap) | Plateau `T` ord / mod | Verdict (3.6) |
|---|---|---|---|---|---|
| Forage | 478.1 / 93.5 *prov.* | 477.4 / 93.3 *prov.* | 0.00 / 0.04 / 0.00 / 0.95 | 200k / 200k *prov.* | **pass**, "too easy to be a distinct world" flag (expected for the safe first stage; not changed). Runs continue to 14 M (ETA ≈ 8 h) |
| Famine | 214.1 / 28.0 | 213.6 / 27.8 | 0.31 / 0.53 / 0.01 / 0.15 | 452k / 484k | **pass, both** |
| Winter | 198.0 / 31.1 | 160.8 / 24.4 | 0.30 / 0.15 / 0.32 / 0.23 (modulated 0.26 / 0.13 / **0.44** / 0.18) | 2,448k / 2,456k | **pass, both** — see the Winter finding below |
| Danger | 77.8 / 2.3 | 77.8 / 2.2 | 0.40 / 0.45 / 0.15 / 0.00 | 388k / 200k | fail, both |
| Danger-soft (3–5 hunters) | 90.5 / 4.1 | 92.3 / 4.3 | 0.43 / 0.45 / 0.12 / 0.00 | 216k / 204k | fail, both again → **Danger DROPPED** |
| Fog | 93.6 / 6.5 | 94.3 / 6.4 | 0.56 / 0.37 / 0.06 / 0.00 | 844k / 836k | fail, both |
| Fog-soft (noise halved) | 113.3 / 9.8 | 114.7 / 9.8 | 0.55 / 0.39 / 0.04 / 0.01 | 596k / 864k | fail, both again → **Fog DROPPED** |
| Harsh | 82.8 / 3.9 | 80.6 / 3.6 | 0.47 / 0.46 / 0.07 / 0.00 | 200k / 200k | fail, both |
| Harsh-soft (food 2–4) | 94.3 / 7.0 | 97.1 / 7.5 | 0.55 / 0.37 / 0.07 / 0.01 | 332k / 200k | fail, both again → **Harsh DROPPED** (it was only in the later sequence P5) |

**Exploratory scouts (Revision 1b; NOT pre-registered; 1.5 M episodes each; read descriptively).**

| Scout | What changes vs the original world | Ordinary | Modulated | `T` ord / mod | Reading |
|---|---|---|---|---|---|
| Danger-A | 3–5 hunters with Home's chase persistence (notice at 3–5 cells, stamina 30–150, give up at 1.5) | 122.6 ~~(best window 130.1)~~ / 11.1 bites | 131.0 / 12.6 bites | 384k / 260k | **one agent only**: modulated passes by 4.3 steps; ordinary misses by 2.3 on the last window ~~although its best window cleared the line~~ *(Rev 2a, R6: the best window is not a 3.6 criterion)* |
| Danger-B | 2–4 hunters, Danger's own persistence | 104.6 | — | 248k / — | fail |
| Danger-C | 3–5 hunters + smell range 8 | 90.0 | — | 224k / — | fail |
| Fog-A | Fog-soft + smell range 5 | 110.5 | — | 348k / — | fail |
| Fog-B | Fog's smell range 3 and 3× sight blur, **no perceptual noise** | 131.6 / 12.5 bites | 135.3 / 13.1 bites | 384k / 480k | **pass, both** (margins 6.7 / 8.6 steps) |

*What the ladder suggests (a pattern from single runs, not a result):* in Danger it is the hunters'
**persistence**, not their number, that kills (fewer persistent hunters, Danger-B, 104.6, does worse than
the same count as soft Danger with Home-like persistence, Danger-A, 122.6; a longer smell range,
Danger-C, does not help); in Fog it is the **noise**, not the short range (removing noise, Fog-B, passes;
a longer smell range with halved noise, Fog-A, does not).

**Winter finding (reported, not a verdict).** Both agents pass Winter, but the modulated agent ends
clearly lower (160.8 vs 198.0 steps) and dies of cold or heat more often (44 % vs 32 % of episodes). This
is one seed of a Home → Winter switch, so it is a description of this initialisation pair, not evidence
about the modulator; it is shown to the user before P3 launches because P3 spends 6 M of its 8 M
episodes in Winter.

*Revision 2a addition (R2) — the Winter curves over time, not just their endpoints.* Trailing
200,000-episode mean survival (steps) at points of the 3 M-episode pilot:

| Episodes since switch | 0.5 M | 1.0 M | 1.5 M | 2.0 M | 2.5 M | 2.75 M | 3.0 M (end) | Best window |
|---|---|---|---|---|---|---|---|---|
| Ordinary | 152.9 | 149.3 | 182.6 | 184.3 | 200.2 | 195.8 | **198.0** | 205.6 at 2.67 M |
| Modulated | 132.3 | 147.4 | 149.8 | 146.4 | 162.4 | 153.1 | **160.8** | **175.7 at 2.54 M** |

The modulated agent **peaked at 175.7 and ended 8.5 % lower (160.8)**, outside the 5 % band the plateau
rule uses; the ordinary agent ended 3.7 % below its best (inside the band). Part of the 37-step gap is
therefore a late decline of the modulated agent (the gap between best windows is 30 steps), and the
first-visit reference `R_Winter` in P3 may be measured on a **falling or oscillating** curve rather than a
flat one. This is carried into the results as a "reference on a non-monotonic curve" note, and it is
evidence **for** decision D6's *look first* option (3.7.6). Zero-shot survival right after the switch
(first 20,000 episodes) was similar: ordinary 129.4, modulated 138.4 steps — the basis of the 5.1
common-reference example.

#### 3.7.2 Stage lengths (rule of 3.3, applied)

Per world X: `L_X = min(3 M, max(1 M, 1.5 × max(T_ord, T_mod)))`, rounded up to 100,000 episodes.

| World | 1.5 × slower `T` | `L_X` |
|---|---|---|
| Forage | 1.5 × 200k = 300k | **1,000,000** (floor) — *provisional until runs 1–2 end; robustness in 3.7.3* |
| Famine | 1.5 × 484k = 726k | **1,000,000** (floor) |
| Winter | 1.5 × 2,456k = 3,684k | **3,000,000** (cap) |
| Danger-A (scout) | 1.5 × 384k = 576k | 1,000,000 (floor) |
| Fog-B (scout) | 1.5 × 480k = 720k | 1,000,000 (floor) |

Winter hits the cap~~, but it did level off~~ *(Rev 2a: overstated — see the correction below)*: its `T` (2.448 M / 2.456 M) falls 52k / 44k episodes
before the pilot's last 500,000 episodes, so the "not plateaued" fallback of 3.3 (which needs `T` inside
the last 500,000, i.e. > 2.5 M) does **not** fire. Its return visits are therefore **not** marked "below plateau"; the 3 M visit
still sits only 1.2× `T` rather than the intended 1.5×, so `R_Winter` (last 200,000 episodes of the first
visit, 2.8–3.0 M) is measured with a thinner post-plateau margin than the rule aimed for — stated here,
carried into the results.

*Revision 2a correction (R2):* "it did level off" above overstates. What is true is narrower: the plateau
rule's `T` (the **first** window within 5 % of the best) falls before the last 500,000 episodes, so the
3.3 fallback correctly does not fire and `L_Winter` = 3 M stands. The modulated curve itself did not stay
flat after `T` — it peaked at 2.54 M and ended 8.5 % lower (trajectory in 3.7.1). No rule changes.

*Revision 2a note (R4) — unequal interference in P3.* Because stage length is set per world (3.3), P3's
two returns are not symmetric: the **Famine return** (stage 5) follows **3 M** episodes of Winter, while
the **Winter return** (stage 4) follows only **1 M** of Famine. The four switch votes therefore carry
unequal amounts of interfering training, and in the forgetting matrix (5.3) "forgetting of Famine" and
"forgetting of Winter" are **not** measured after matched amounts of other-world training. The heavier
interference also lands on Famine, the world where the pilots show no difference between agents
(214.1 / 213.6). The schedule is the same for both agents, so this is not an agent confound, and the rule
is applied as pre-registered — **no rule change**; the asymmetry is reported (5.2, 5.3).

Per candidate pair (throughput from the Home → X pilots, `ep/h` ordinary / modulated; branch nodes may
differ):

| Sequence | Stage lengths A / B | Boundaries (episode counter) | Episodes after the branch | Est. wall time ord / mod |
|---|---|---|---|---|
| **P3** Winter ↔ Famine | 3 M / 1 M | `[11M, 14M, 15M, 18M, 19M]` | 8 M | ≈ 16 h / 18 h |
| P1-replacement Danger-A ↔ Famine | 1 M / 1 M | `[11M, 12M, 13M, 14M, 15M]` | 4 M | ≈ 7 h / 8 h |
| P2-replacement Fog-B ↔ Danger-A | 1 M / 1 M | `[11M, 12M, 13M, 14M, 15M]` | 4 M | ≈ 5 h / 6 h |
| (alternative, no file) Fog-B ↔ Famine | 1 M / 1 M | `[11M, 12M, 13M, 14M, 15M]` | 4 M | ≈ 6 h / 8 h |

**Per world, not per pair.** 3.3 fixes `L_X` **per world** ("every visit to X lasts `L_X`"); the
plan-reviewer's F2 had suggested one length per pair (1.5 × the largest `T` over both worlds), and
Revision 1 adopted the per-world form instead (Response to F2). Under a per-pair rule only P3 changes:
Famine visits would also last 3 M, boundaries `[11M, 14M, 17M, 20M, 23M]`, 12 M episodes after the branch
(≈ 24 h / 29 h). The files follow the pre-registered per-world rule; switching is a one-line edit
(decision D1, 3.7.6).

#### 3.7.3 The branch point B0

By 3.4, `B0 = 10,000,000 + L_Forage` = **11,000,000**, not the 14,000,000 at which the Forage pilots end
(14 M was the pilot's length, chosen so the pilot would certainly pass any `B0` the rule could give).
The branch checkpoints already exist (checkpoints are every 100,000 episodes and all are kept): the first
at or after 11 M is **step 11,000,025** (ordinary, run 1) and **step 11,000,022** (modulated, run 2). The
trainer's own schedule builder maps both restored counters to stage 1 (the first A-world), 6.1 C13.

*Why `L_Forage` = 1 M is safe to use before the Forage runs end.* `T` is the first full 200,000-episode
window within 5 % of the best window. The earliest window already reads 473.4 (ordinary) / 472.2
(modulated), and every window up to 666,000 episodes is at least that. For `L_Forage` to leave the 1 M
floor, `T` would have to exceed 666,667 episodes, which needs a best window above 473.4 / 0.95 = 498.3
(497.0 modulated) — within 2 steps of the 500-step episode cap, against a flat 478 for the last 1.5 M
episodes. The pre-registered wording still requires the full curve, so the value is **confirmed when runs
1–2 end** (6.3); if it ever changed, the schedules are regenerated before any branch launches.

If the user prefers to branch at 14 M instead (decision D2), every boundary in the three files moves up
by 3 M and the Forage stage becomes 4 M long (more training in the "too easy" world; the curriculum
lessons in the LLM wiki warn that long over-training on an easy stage costs plasticity).

#### 3.7.4 Revised sequence proposal

| Sequence | Stages 2–5 | Status | Schedule |
|---|---|---|---|
| **P3** Winter ↔ Famine (as pre-registered) | Winter, Famine, Winter, Famine | **READY** — both worlds pass for both agents; launch after 6.3 and the user's go | `configs/continual/continual_worlds/p3_winter_famine.yaml` + `p3_winter_famine_stages/` (regenerated) |
| **P1-replacement** Danger-A ↔ Famine (replaces P1 Danger ↔ Famine) | Danger-A, Famine, Danger-A, Famine | ~~DRAFT — pending user approval~~ **approved 2026-09-29 (D4, 3.7.7)** | `configs/continual/continual_worlds/p1_danger_scout_a_famine.yaml` + `_stages/` |
| **P2-replacement** Fog-B ↔ Danger-A (replaces P2 Fog ↔ Danger) | Fog-B, Danger-A, Fog-B, Danger-A | ~~DRAFT — pending user approval~~ **approved 2026-09-29 (D5, 3.7.7)** | `configs/continual/continual_worlds/p2_fog_scout_b_danger_scout_a.yaml` + `_stages/` |
| P4 (P1 reversed, order control) | — | later; follows whatever replaces P1 | none |
| P5 Harsh ↔ Forage | — | **cannot run as designed** (Harsh dropped); user decides later | none |

The original P1 / P2 files (`p1_danger_famine*`, `p2_fog_danger*`) are left untouched; they use the
dropped worlds and must not be launched.

**Why the replacements need the user, not the rule.**
1. **Danger-A is "one agent only".** Under 3.6, a world where exactly one agent fails is reported to the
   user before any main run, not adopted automatically. The ordinary agent's last window is 122.6 against
   124.9 ~~(its best window, 130.1, cleared the line)~~. Danger-A appears in **both** replacement sequences, so
   if the ordinary agent struggles there, two of three sequences carry it ~~(failure mode 7.4: the verdict
   is then computed with and without those sequences)~~.
   *Revision 2a (R6):* the struck citation was wrong — failure mode 7.4 triggers on an agent collapsing
   below 0.6 × its own reference during a visit, a different condition — and the best window is not a
   3.6 criterion (only the last 200,000 episodes are). Stated on its own instead: **if Danger-A sequences
   are run, the section 2 verdict is computed twice, with and without every sequence that contains
   Danger-A**, because Danger-A passed the survivable rule for one agent only; both are reported.
2. **Exploratory origin.** Danger-A and Fog-B come from a five-scout ladder read after seeing the
   pre-registered worlds fail; picking the variants that passed is a selection step. The support rule of
   section 2 stays unchanged, but a result from P1/P2-replacement is reported as resting on worlds chosen
   after the pilots.
3. **Thin margins.** Danger-A (modulated +4.3 steps) and Fog-B (+6.7 / +8.6) sit just above the line; a
   switch dip of 20–30 % will take them well below it, so recovery there may be censored more often
   (failure mode 7.3).

**Alternatives for the user.** (a) **Fog-B ↔ Famine** (drops Danger from the study altogether; both worlds
pass both agents; no file yet, one-minute generation). (b) **A Danger variant one notch easier than
Danger-A** (e.g. Danger-A's Home-like hunting with 2–4 hunters) so that both agents pass — needs its own
two-agent pilot (≈ 1.5 M episodes, ≈ 2–3 h) before it enters a sequence. (c) **Run P3 alone now** and
decide P1/P2 after its first stages.

**Sharing between sequences (carried into the verdict wording).** All sequences branch from the same
Forage checkpoint per agent ("one initialisation pair", 3.4). P3 and P1-replacement share Famine;
P1- and P2-replacement share Danger-A.

#### 3.7.5 Pilot 2 (pipeline) and Pilot 3 (Nursery), Home legs

- **Pilot 2 — pipeline pass** (not evidence; its dips and returns are not read). Runs 13, 15, 16 completed
  all five stages; run 14 (2a, modulated) is in its last stage (14.44 M of 15 M, ETA ≈ 1.3 h). Every
  `[STAGE]` switch fired at the first iteration past its boundary (drift 3–186 episodes), no traceback in
  any log, and every completed stage holds **10 checkpoints** (51 per finished run = the restore-time
  checkpoint + 50). **Not exercised:** the forgetting-matrix sweep on a real continual run (no sweep spec
  or output exists) and the restore-into-a-later-stage path that the branches use (Pilot 2 started in
  stage 0). Both are in the 6.3 checklist.
  *Revision 2a relabel (R3):* "pipeline pass" above overstates. Against the four pre-registered pass
  clauses of 3.6 the status is **3 of 4 clauses met — provisional**: stage switches at their boundaries
  (met), no traceback (met), 10 checkpoints per stage (met), forgetting-matrix sweep produces a full matrix
  on a real continual run (**not yet run**) — and run 14 has not yet finished (at 14.61 M of 15 M at
  23:45, ≈ 17 min left). Pilot 2 is declared passed only when run 14 ends with the same signs **and** the
  sweep has run once on a finished Pilot 2 run (run 15; a developer is running it now). Both are gates for
  the branches (6.3 items 4 and 7), not "at the latest before their first stage ends".
- **Pilot 3 — pass, both agents** (seed-43 Nursery legs): survival 414.3 / 417.4 (≥ 200), bites 75.8 / 76.6,
  eat ratio 13.4 / 17.1, hide ratio 2.96 / 3.03, time warm 0.21 / 0.21, thermal late-death share 0.04 /
  0.03; first competent window ends at 384k / 364k; no collapse. The seed-44 Nursery legs (rows 25–26) are
  therefore unblocked.
- **Seed-43 Home legs** (rows 27–28, *provisional*, still training): 246.6 / 248.0 steps after 4.86 M /
  3.28 M Home episodes (counter 6.86 M / 5.28 M of 10 M), already above the competence gate (237.3 /
  240.7, 3.5). The gate is judged formally at the counter of 10 M (≈ 4 h / 8 h), together with its
  "rose < 5 % over the last fifth" condition.

#### 3.7.6 Open decisions for the user

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | Stage length per world (pre-registered) or per pair | per world: P3 = 8 M after branch; per pair: P3 = 12 M, Famine visits 3 M | **per world** — it is what 3.3 pre-registered and what the read-out script computes; per pair costs ≈ 8–10 h more per run |
| D2 | Branch point | 11 M (rule, 3.4) or 14 M (end of the Forage pilot) | **11 M** — the rule's value; checkpoints exist; avoids 3 M extra episodes in a world flagged too easy |
| D3 | Launch P3 now (after 6.3) or wait for P1/P2 decisions | now / together | **now** — P3 is fully pre-registered and independent |
| D4 | P1 replacement | Danger-A ↔ Famine (draft) / Fog-B ↔ Famine / new Danger variant + pilot / none | user's call; if speed matters, Fog-B ↔ Famine is the only option where both worlds pass both agents |
| D5 | P2 replacement | Fog-B ↔ Danger-A (draft) / new Danger variant + pilot / drop P2 | user's call |
| D6 | Winter finding (modulated lower, more thermal deaths) | proceed / look first (e.g. `trajectory-story` read of both agents in Winter) | proceed — both pass; reported as a finding |
| D7 | P5 (Harsh ↔ Forage), later | drop / replace Harsh | defer |
| D8 *(Rev 2a, from plan-reviewer O5)* | Must the branches wait for the Forage runs (1–2) to reach 14 M? | wait (the pre-registered wording of 3.3 / 3.7.3 asks for the full curve) / waive | **waive is defensible, user's call.** 3.7.3 shows `L_Forage` cannot leave the 1 M floor (it would need a 200k window above 498 of a 500-step cap), so runs 1–2 only confirm a number that cannot change; the branch checkpoints at 11 M already exist and are not touched by further training. The cost of waiting is now small (at 23:45 run 1 was at 12.35 M, run 2 at 11.94 M: ≈ 1.5–2 h left, not the 8 h stated in Revision 2). Waiving is a departure from the written rule and would be recorded as such |

#### 3.7.7 Decisions (user, 2026-09-29)

*Appended 2026-09-29; the pre-registered text above is unchanged. Taken by the user through a structured
question on the open decisions of 3.7.6.*

**In plain words.** The user approved the plan as recommended: each world keeps its own stage length, the
sequences branch from the Forage run at 11 million episodes without waiting for that run to finish, the
Winter ↔ Famine sequence launches as soon as the remaining pre-launch checks pass, and the two sequences
whose original worlds failed the pilots are replaced by the scout worlds that passed (the softer-hunting
Danger variant and the noise-free Fog variant). The Winter observation (modulated agent ending lower)
is carried as a caveat, not investigated first.

| # | Decision | Taken |
|---|---|---|
| D1 | Stage length per world or per pair | **per world** (as pre-registered in 3.3). P3 boundaries stay `[11M, 14M, 15M, 18M, 19M]` |
| D2 | Branch point | **11 M** (`B0` by the 3.4 rule; branch checkpoints 11,000,025 / 11,000,022) |
| D8 | Wait for Forage runs 1–2 to reach 14 M before branching | **waived.** Recorded as a departure from the written wording of 3.3 / 3.7.3 ("the full curve"); justification in 3.7.3 / D8 (`L_Forage` cannot leave the 1 M floor). The read-out is still re-run when runs 1–2 end and the confirmation reported; if `L_Forage` ever changed, any branch already launched is reported as launched on a waived rule |
| D3 | Launch P3 now or together with P1 / P2 | **now**, as soon as the 6.3 checklist items that gate it are done |
| D4 | P1 replacement | **Danger-A ↔ Famine** (rows 19–20). Carries the three caveats of 3.7.4 (one-agent-only world; exploratory origin; thin margins) and the with / without-Danger-A verdict of 3.7.4 item 1 |
| D5 | P2 replacement | **Fog-B ↔ Danger-A** (rows 21–22). Same caveats |
| D6 | Winter finding: proceed or look first | **proceed** ("launch now" chosen over "look at Winter first"). The finding (3.7.1: modulated 160.8 vs 198.0 steps, more cold/heat deaths, a late decline after a 175.7 peak) is a **caveat** carried into the P3 results: `R_Winter` may sit on a falling curve, and any P3 H-dip / H-rec reading involving Winter is reported next to it |
| D7 | P5 Harsh ↔ Forage | **not asked; deferred** |

**Pre-registered scoring choices (before any main run).** Two choices made in the read-out code
(`scripts/analysis/studies/continual_worlds/pilot_readout.py`, commit `a72eb943`, function `_vote`) that
the text of 5.1 / 7.9 / 7.11 did not fix are adopted here as part of the analysis plan:

- **(a) A recovery tie is not favourable.** If both agents recover in the same logged row (episodes are
  resolved only to the 4,000-episode logging interval), that reading is a tie; a vote with any tied reading
  is **"not counted (tie)"** — named as a tie, not as a 7.9 / 7.11 disagreement (those are checked between
  untied readings only).
- **(b) Unanimous against the modulator counts.** When every reading (own / common reference × episodes /
  environment steps) favours the ordinary agent, the vote is **unfavourable** and counts against the
  modulator in section 2's tally, symmetrically with the all-favourable case.

**Known reporting issue (follow-up for the script owner, `developer`).** In `pilot_readout.json`, the
field `survivable.survival_line` for the seed-43 **Home legs** (rows 27–28) is computed with the
world-pilot rule (half of the Home level). That rule does not govern those runs: a Home leg is judged by
the **competence gate of 3.5** (237.3 ordinary / 240.7 modulated, plus the "rose < 5 % over the last
fifth" condition). The field is to be ignored for rows 27–30 until the script labels or omits it; no
verdict in this doc uses it.

**Effect on the manifest and configs.** Rows 19–24 are "ready — pending pre-launch checklist" (section 4).
The P1- and P2-replacement schedule files and their stage folders have their header comments changed from
"DRAFT — pending user approval / do not launch" to "READY (user approved 2026-09-29)"; boundaries and stage
files are unchanged, so the `env-config-reviewer` GO WITH NOTES on them still holds.

## 4. Launch Manifest

All rows: `wandb-group` = `continual_worlds`. Tag = wandb-name. Scheme:
`rppo_cw_<cell>_<agent>_s<seed>`, agent ∈ {`t1none` ordinary, `t16quad` modulated}. Seed 42 rows load
the pre-trained pair; `--seed 42` is passed for the record, the restored key governs. Node / GPU are
assigned by the parent (candidate nodes 106–112, 102, 113; pack node-first).

**Launch order:** pilots (runs 1–18, all at once) → pilot verdicts, `L_X` computed, P1–P3 schedules
regenerated, branch-point copies made, user go → branches (19–24) and seed-44 Nursery legs (25–26) →
Home legs (27–30) after their Nursery leg ends (27–28 only if Pilot 3 passed).
*Revision 2:* P3 (rows 23–24) is ready after the 6.3 checklist and the user's go; P1 / P2 (rows 19–22)
wait for the user's replacement decision (3.7.6) and carry new tags naming their replacement worlds;
Pilot 3 passed, so rows 25–26 are unblocked.
*2026-09-29 (3.7.7):* the user approved D1–D6 and D8; rows 19–24 are all "ready — pending pre-launch
checklist" (6.3) with the tags below.

| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|-----|--------|------|--------------------|-------------|----------------|------|------|-----|-------------|--------------|----------|
| 1 | running (at 23:45 Rev 2a) | Pilot 1 Forage (= main stage 1) | `rppo_cw_pilot1_forage_t1none_s42` | continual_worlds | pilot | 42 | 106 | cuda:0 | 2026-09-28T13:16:42 | `6sf68was` | `logs/20260928_131642.log` |
| 2 | running (at 23:45 Rev 2a) | Pilot 1 Forage (= main stage 1) | `rppo_cw_pilot1_forage_t16quad_s42` | continual_worlds | pilot | 42 | 106 | cuda:1 | 2026-09-28T13:16:46 | `e78og819` | `logs/20260928_131646.log` |
| 3 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1 Danger | `rppo_cw_pilot1_danger_t1none_s42` | continual_worlds | pilot | 42 | 107 | cuda:0 | 2026-09-28T13:16:50 | `7e8rr45p` | `logs/20260928_131650.log` |
| 4 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1 Danger | `rppo_cw_pilot1_danger_t16quad_s42` | continual_worlds | pilot | 42 | 107 | cuda:1 | 2026-09-28T13:16:53 | `gwkhnlpl` | `logs/20260928_131653.log` |
| 5 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1 Famine | `rppo_cw_pilot1_famine_t1none_s42` | continual_worlds | pilot | 42 | 108 | cuda:0 | 2026-09-28T13:16:56 | `p0ev5nbw` | `logs/20260928_131656.log` |
| 6 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1 Famine | `rppo_cw_pilot1_famine_t16quad_s42` | continual_worlds | pilot | 42 | 108 | cuda:1 | 2026-09-28T13:17:00 | `lf5tquew` | `logs/20260928_131700.log` |
| 7 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1 Winter | `rppo_cw_pilot1_winter_t1none_s42` | continual_worlds | pilot | 42 | 109 | cuda:0 | 2026-09-28T13:17:04 | `s85qrj65` | `logs/20260928_131704.log` |
| 8 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1 Winter | `rppo_cw_pilot1_winter_t16quad_s42` | continual_worlds | pilot | 42 | 109 | cuda:1 | 2026-09-28T13:17:07 | `4bapjjog` | `logs/20260928_131707.log` |
| 9 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1 Fog | `rppo_cw_pilot1_fog_t1none_s42` | continual_worlds | pilot | 42 | 110 | cuda:0 | 2026-09-28T13:17:11 | `nealqwms` | `logs/20260928_131711.log` |
| 10 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1 Fog | `rppo_cw_pilot1_fog_t16quad_s42` | continual_worlds | pilot | 42 | 110 | cuda:1 | 2026-09-28T13:17:14 | `4rkcrqzp` | `logs/20260928_131714.log` |
| 11 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1 Harsh | `rppo_cw_pilot1_harsh_t1none_s42` | continual_worlds | pilot | 42 | 111 | cuda:0 | 2026-09-28T13:17:18 | `cssu3qc3` | `logs/20260928_131718.log` |
| 12 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1 Harsh | `rppo_cw_pilot1_harsh_t16quad_s42` | continual_worlds | pilot | 42 | 111 | cuda:1 | 2026-09-28T13:17:22 | `xbpq1y9s` | `logs/20260928_131722.log` |
| 13 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 2a shakedown | `rppo_cw_pilot2a_t1none_s42` | continual_worlds | pilot | 42 | 112 | cuda:0 | 2026-09-28T13:17:26 | `tdpz3ju7` | `logs/20260928_131726.log` |
| 14 | running (at 23:45 Rev 2a) | Pilot 2a shakedown | `rppo_cw_pilot2a_t16quad_s42` | continual_worlds | pilot | 42 | 112 | cuda:1 | 2026-09-28T13:17:30 | `si97t2j5` | `logs/20260928_131730.log` |
| 15 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 2b shakedown | `rppo_cw_pilot2b_t1none_s42` | continual_worlds | pilot | 42 | 113 | cuda:0 | 2026-09-28T13:17:34 | `rygfw76a` | `logs/20260928_131734.log` |
| 16 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 2b shakedown | `rppo_cw_pilot2b_t16quad_s42` | continual_worlds | pilot | 42 | 113 | cuda:1 | 2026-09-28T13:17:38 | `zjsdfoyq` | `logs/20260928_131738.log` |
| 17 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 3 Nursery (= seed-43 leg) | `rppo_cw_nursery_t1none_s43` | continual_worlds | pilot | 43 | 102 | cuda:0 | 2026-09-28T13:17:41 | `98tm6jxe` | `logs/20260928_131741.log` |
| 18 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 3 Nursery (= seed-43 leg) | `rppo_cw_nursery_t16quad_s43` | continual_worlds | pilot | 43 | 102 | cuda:1 | 2026-09-28T13:17:45 | `q3ni07j6` | `logs/20260928_131745.log` |
| 19 | running | P1-replacement branch Danger-A ↔ Famine, ordinary | `rppo_cw_p1_danger_scout_a_famine_t1none_s42` | continual_worlds | prod | 42 | 108 | cuda:0 | 2026-09-29T00:39:59 | `6jz5xgtf` | `logs/20260929_003959.log` |
| 20 | running | P1-replacement branch Danger-A ↔ Famine, modulated | `rppo_cw_p1_danger_scout_a_famine_t16quad_s42` | continual_worlds | prod | 42 | 108 | cuda:1 | 2026-09-29T00:40:06 | `f6sqgsgg` | `logs/20260929_004006.log` |
| 21 | running | P2-replacement branch Fog-B ↔ Danger-A, ordinary | `rppo_cw_p2_fog_scout_b_danger_scout_a_t1none_s42` | continual_worlds | prod | 42 | 109 | cuda:0 | 2026-09-29T00:40:12 | `7szjx34t` | `logs/20260929_004012.log` |
| 22 | running | P2-replacement branch Fog-B ↔ Danger-A, modulated | `rppo_cw_p2_fog_scout_b_danger_scout_a_t16quad_s42` | continual_worlds | prod | 42 | 109 | cuda:1 | 2026-09-29T00:40:18 | `r96fgv4u` | `logs/20260929_004018.log` |
| 23 | running | P3 branch Winter ↔ Famine, ordinary | `rppo_cw_p3_t1none_s42` | continual_worlds | prod | 42 | 107 | cuda:0 | 2026-09-29T00:39:47 | `qdnh5rzy` | `logs/20260929_003947.log` |
| 24 | running | P3 branch Winter ↔ Famine, modulated | `rppo_cw_p3_t16quad_s42` | continual_worlds | prod | 42 | 107 | cuda:1 | 2026-09-29T00:39:53 | `q6j9pu1o` | `logs/20260929_003953.log` |
| 25 | planned — unblocked (Pilot 3 passed) | Nursery leg | `rppo_cw_nursery_t1none_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 26 | planned — unblocked (Pilot 3 passed) | Nursery leg | `rppo_cw_nursery_t16quad_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 27 | running (at 23:45 Rev 2a) | Home leg | `rppo_cw_home_t1none_s43` | continual_worlds | prod | 43 | 102 | cuda:0 | 2026-09-28T17:14:41 | `6gc2tok9` | `logs/20260928_171441.log` |
| 28 | running (at 23:45 Rev 2a) | Home leg | `rppo_cw_home_t16quad_s43` | continual_worlds | prod | 43 | 102 | cuda:1 | 2026-09-28T18:02:28 | `cmnof24a` | `logs/20260928_180229.log` |
| 29 | planned (after 25) | Home leg | `rppo_cw_home_t1none_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 30 | planned (after 26) | Home leg | `rppo_cw_home_t16quad_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 31 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1s Danger-soft | `rppo_cw_pilot1s_danger_soft_t1none_s42` | continual_worlds | pilot | 42 | 101 | cuda:0 | 2026-09-28T16:20:23 | `ww9ck47l` | `logs/20260928_162023.log` |
| 32 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1s Danger-soft | `rppo_cw_pilot1s_danger_soft_t16quad_s42` | continual_worlds | pilot | 42 | 101 | cuda:1 | 2026-09-28T16:20:24 | `kgvn98p5` | `logs/20260928_162024.log` |
| 33 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1s Fog-soft | `rppo_cw_pilot1s_fog_soft_t1none_s42` | continual_worlds | pilot | 42 | 104 | cuda:0 | 2026-09-28T16:28:58 | `ruudv8i6` | `logs/20260928_162858.log` (shared with row 34; clean copy `wandb/run-20260928_162915-ruudv8i6/files/output.log`) |
| 34 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1s Fog-soft | `rppo_cw_pilot1s_fog_soft_t16quad_s42` | continual_worlds | pilot | 42 | 104 | cuda:1 | 2026-09-28T16:28:58 | `il157bos` | `logs/20260928_162858.log` (shared with row 33; clean copy `wandb/run-20260928_162915-il157bos/files/output.log`) |
| 35 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1s Harsh-soft | `rppo_cw_pilot1s_harsh_soft_t1none_s42` | continual_worlds | pilot | 42 | 103 | cuda:0 | 2026-09-28T16:20:25 | `dxkzhykp` | `logs/20260928_162025.log` |
| 36 | finished ("Training complete", checked 23:45 Rev 2a) | Pilot 1s Harsh-soft | `rppo_cw_pilot1s_harsh_soft_t16quad_s42` | continual_worlds | pilot | 42 | 103 | cuda:1 | 2026-09-28T16:20:26 | `hjktbwln` | `logs/20260928_162026.log` |
| 37 | finished ("Training complete", checked 23:45 Rev 2a) | Scout Danger-A (3–5 hunters, Home-like persistence) | `rppo_cw_scout_danger_scout_a_t1none_s42` | continual_worlds | pilot | 42 | 105 | cuda:0 | 2026-09-28T19:07:59 | `yhezxekl` | `logs/20260928_190759.log` |
| 38 | finished ("Training complete", checked 23:45 Rev 2a) | Scout Danger-B (2–4 hunters) | `rppo_cw_scout_danger_scout_b_t1none_s42` | continual_worlds | pilot | 42 | 105 | cuda:1 | 2026-09-28T19:08:06 | `59wq3jqj` | `logs/20260928_190807.log` |
| 39 | abandoned — node 114 hung during compile ~19:09; if 114 recovers, kill any rppo_cw_scout_ processes there (relaunched as `_r2`, next row) | Scout Danger-C (3–5 hunters + smell 8) | `rppo_cw_scout_danger_scout_c_t1none_s42` | continual_worlds | pilot | 42 | 114 | cuda:0 | 2026-09-28T19:08:13 | `4k8wgp8j` | `logs/20260928_190814.log` |
| 39-r2 | finished ("Training complete", checked 23:45 Rev 2a) | Scout Danger-C (3–5 hunters + smell 8) — relaunch of 39 | `rppo_cw_scout_danger_scout_c_t1none_s42_r2` | continual_worlds | pilot | 42 | 107 | cuda:0 | 2026-09-28T19:27:46 | `fv0sdsvh` | `logs/20260928_192746.log` |
| 40 | abandoned — node 114 hung during compile ~19:09; if 114 recovers, kill any rppo_cw_scout_ processes there (relaunched as `_r2`, next row) | Scout Fog-A (Fog-soft + smell 5) | `rppo_cw_scout_fog_scout_a_t1none_s42` | continual_worlds | pilot | 42 | 114 | cuda:1 | 2026-09-28T19:08:20 | `zm73ti5c` | `logs/20260928_190821.log` |
| 40-r2 | finished ("Training complete", checked 23:45 Rev 2a) | Scout Fog-A (Fog-soft + smell 5) — relaunch of 40 | `rppo_cw_scout_fog_scout_a_t1none_s42_r2` | continual_worlds | pilot | 42 | 107 | cuda:1 | 2026-09-28T19:27:55 | `n1zmj65i` | `logs/20260928_192755.log` |
| 41 | abandoned — node 114 hung during compile ~19:09; if 114 recovers, kill any rppo_cw_scout_ processes there (relaunched as `_r2`, next row) | Scout Fog-B (smell 3, no noise) | `rppo_cw_scout_fog_scout_b_t1none_s42` | continual_worlds | pilot | 42 | 114 | cuda:2 | 2026-09-28T19:08:27 | `h4772olp` | `logs/20260928_190827.log` |
| 41-r2 | finished ("Training complete", checked 23:45 Rev 2a) | Scout Fog-B (smell 3, no noise) — relaunch of 41 | `rppo_cw_scout_fog_scout_b_t1none_s42_r2` | continual_worlds | pilot | 42 | 110 | cuda:0 | 2026-09-28T19:28:03 | `pvzvl7bm` | `logs/20260928_192803.log` |
| 42 | finished ("Training complete", checked 23:45 Rev 2a) | Scout Danger-A, modulated agent (pairs row 37) | `rppo_cw_scout_danger_scout_a_t16quad_s42` | continual_worlds | pilot | 42 | 109 | cuda:0 | 2026-09-28T20:54:17 | `35fobtmf` | `logs/20260928_205417.log` |
| 43 | finished ("Training complete", checked 23:45 Rev 2a) | Scout Fog-B, modulated agent (pairs row 41-r2) | `rppo_cw_scout_fog_scout_b_t16quad_s42` | continual_worlds | pilot | 42 | 109 | cuda:1 | 2026-09-28T21:01:05 | `v9qvx2p3` | `logs/20260928_210105.log` |

*Revision 2a (R7), statuses checked 23:45 against each log's "Training complete" line:* rows 3–13,
15–18, 31–38, 39-r2 / 40-r2 / 41-r2, 42 and 43 **finished**; rows 39–41 **abandoned** (node 114);
still **running**: 1 (12.35 M of 14 M), 2 (11.94 M of 14 M), 14 (14.61 M of 15 M), 27 (7.15 M of 10 M),
28 (5.51 M of 10 M). Row 13 is finished (the Revision 2 text already said so).

Row 42 (added 2026-09-28 at the user's request) is the modulated-agent twin of row 37 — Danger-A is
the candidate replacement closest to the survivable line, and a replacement world needs both agents.
Row 43 (added 2026-09-28 at the user's request) is the modulated-agent twin of row 41-r2 (Fog-B), whose ordinary agent passes the survivable line.
Rows 37–41 (Revision 1b) are **exploratory scouts, not pre-registered**: ordinary agent only, read
descriptively with the survivable rule; they do not overturn the dropped worlds' verdicts.

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
`results/JAX_RecurrentPPO/cw_branchpoint_forage_{t1none,t16quad}_s42/models` (made after Pilot 1, 3.4;
Rev 2: from step 11,000,025 of run 1 / step 11,000,022 of run 2, 3.7.3).

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
| 19, 20 | **Rev 2, approved 2026-09-29 (D4):** `CS/p1_danger_scout_a_famine_stages/` + `CS/p1_danger_scout_a_famine.yaml` (boundaries 11 M … 15 M). *The original `CS/p1_danger_famine*` uses the dropped Danger world — do not launch.* | T1, T16 | `BP_O`, `BP_M` | none |
| 21, 22 | **Rev 2, approved 2026-09-29 (D5):** `CS/p2_fog_scout_b_danger_scout_a_stages/` + `CS/p2_fog_scout_b_danger_scout_a.yaml` (boundaries 11 M … 15 M). *The original `CS/p2_fog_danger*` uses the dropped worlds — do not launch.* | T1, T16 | `BP_O`, `BP_M` | none |
| 23, 24 | `CS/p3_winter_famine_stages/` + `CS/p3_winter_famine.yaml` (**regenerated, Rev 2:** `[11M, 14M, 15M, 18M, 19M]`) | T1, T16 | `BP_O`, `BP_M` | none |
| 25, 26 | `CW/nursery_10x10.yaml` | T1, T16 | scratch | 2000000 |
| 27–30 | `CW/home_10x10.yaml` | as its Nursery leg | its Nursery leg's `models/` | 10000000 |
| 31, 32 | `CW/danger_soft_15x15.yaml` (Revision 1a) | T1, T16 | `CK_O`, `CK_M` | 13000000 |
| 33, 34 | `CW/fog_soft_15x15.yaml` (Revision 1a) | T1, T16 | `CK_O`, `CK_M` | 13000000 |
| 35, 36 | `CW/harsh_soft_15x15.yaml` (Revision 1a) | T1, T16 | `CK_O`, `CK_M` | 13000000 |
| 37 | `CW/danger_scout_a_15x15.yaml` (Revision 1b) | T1 | `CK_O` | 11500000 |
| 38 | `CW/danger_scout_b_15x15.yaml` (Revision 1b) | T1 | `CK_O` | 11500000 |
| 39 | `CW/danger_scout_c_15x15.yaml` (Revision 1b) | T1 | `CK_O` | 11500000 |
| 40 | `CW/fog_scout_a_15x15.yaml` (Revision 1b) | T1 | `CK_O` | 11500000 |
| 41 | `CW/fog_scout_b_15x15.yaml` (Revision 1b) | T1 | `CK_O` | 11500000 |
| 42 | `CW/danger_scout_a_15x15.yaml` (Revision 1b) | T16 | `CK_M` | 11500000 |
| 43 | `CW/fog_scout_b_15x15.yaml` (Revision 1b) | T16 | `CK_M` | 11500000 |

Rows 31–36 use exactly the flags of rows 3–12 (the Pilot 1 command in 4.2 with the world file and
tag swapped): `--load-checkpoint` the same pre-trained `CK_O` / `CK_M`, `--episodes 13000000
--checkpoint-frequency 100000 --seed 42`, `--wandb-group continual_worlds --wandb-job-type pilot`.

Rows 37–41 use the same Pilot 1 command with the ordinary agent config (`T1`) and `CK_O` only,
`--episodes 11500000` (1.5 M episodes past the restored ≈ 10 M counter), the scout world file, and
tag = wandb-name `rppo_cw_scout_<world>_t1none_s42`; `--checkpoint-frequency 100000 --seed 42
--wandb-group continual_worlds --wandb-job-type pilot` unchanged. Row 37 in full:

```bash
$PY train.py --config configs/environment/experiment/continual_worlds/danger_scout_a_15x15.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml \
  --load-checkpoint results/JAX_RecurrentPPO/20260927-053057_rppo_l05body_w0000_t1none_s42/models \
  --episodes 11500000 --checkpoint-frequency 100000 --seed 42 --device cuda:0 \
  --tag rppo_cw_scout_danger_scout_a_t1none_s42 --wandb-name rppo_cw_scout_danger_scout_a_t1none_s42 \
  --wandb-group continual_worlds --wandb-job-type pilot
```

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

# Branch-point copy (Rev 2; once per agent, read-only copy, nothing moved or deleted; 3.4, 3.7.3)
R=results/JAX_RecurrentPPO
mkdir -p $R/cw_branchpoint_forage_t1none_s42/models $R/cw_branchpoint_forage_t16quad_s42/models
cp -a $R/20260928-131647_rppo_cw_pilot1_forage_t1none_s42/models/11000025 \
      $R/20260928-131647_rppo_cw_pilot1_forage_t1none_s42/models/config.yaml $R/cw_branchpoint_forage_t1none_s42/models/
cp -a $R/20260928-131651_rppo_cw_pilot1_forage_t16quad_s42/models/11000022 \
      $R/20260928-131651_rppo_cw_pilot1_forage_t16quad_s42/models/config.yaml $R/cw_branchpoint_forage_t16quad_s42/models/

# Branch (run 24 shown = P3, modulated; run 23 uses the T1 agent config, BP_O and its tag.
# Rows 19-22 use the same command with their schedule + stage dir and tag (approved 2026-09-29, 3.7.7).)
$PY train.py --configs-dir configs/continual/continual_worlds/p3_winter_famine_stages \
  --continual-schedule configs/continual/continual_worlds/p3_winter_famine.yaml \
  --agent_config configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml \
  --load-checkpoint results/JAX_RecurrentPPO/cw_branchpoint_forage_t16quad_s42/models \
  --seed 42 --device cuda:0 --tag rppo_cw_p3_t16quad_s42 --wandb-name rppo_cw_p3_t16quad_s42 \
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

**Common-reference companion (Revision 2a, 2026-09-28; pre-registered before any main run launched —
plan-reviewer R1).** The dip and recovery above are relative to each agent's **own** `R_X`. When the two
agents settle at different levels in X, those readings partly measure "whose settled level is lower"
rather than "who adapts faster". Each is therefore also computed against one reference shared by both
agents of the same sequence:

- `R_X,common` = min(`R_X,ord`, `R_X,mod`) — the lower of the two agents' first-visit reference levels for
  world X (same windows as `R_X`).
- **Dip, common reference** = `R_X,common` − (mean survival over the first 20,000 episodes of visit v), in
  **absolute survival steps** (also shown as a fraction of `R_X,common`). Because the reference is shared,
  the modulated-minus-ordinary difference is simply the difference in post-switch survival, sign
  reversed: negative (smaller dip) favours the modulator.
- **Recovery, common reference** = training after the switch until the 20,000-episode running mean first
  reaches **0.9 × `R_X,common`**, in episodes **and** environment steps, censored at `L_X` as above.

**Vote rule (amends section 2 for H-dip and H-rec only).** The H-dip vote for a switch counts only if the
modulated-minus-ordinary difference has the favourable sign under **both** the own-reference and the
common-reference reading. The H-rec vote counts only if it is favourable under **all four** readings
(own / common reference × episodes / environment steps). A switch whose readings disagree is recorded as
"not counted" (7.11) — the same device the episodes-vs-environment-steps rule (F3, 7.9) already uses.
Each reading has an opposite bias — the own-reference reading favours the agent with the lower plateau,
the common-reference reading the agent with the higher level overall — so requiring agreement removes
the plateau-level artefact in both directions. **Return and forgetting need no companion**: both are
already differences in absolute survival steps (return: return-visit level − first-visit level of the
same agent; forgetting: 5.3), and are unchanged.

*Why, with the pilot example (descriptive; the pilots are Home → X switches, not votes).* In the Winter
pilot the two agents started almost equal right after the switch (first 20,000 episodes: ordinary 129.4,
modulated 138.4 steps) but settled 37 steps apart (198.0 vs 160.8). Own-reference recovery then reads
**132,000 vs 40,000 episodes** (20.7 M vs 5.7 M environment steps) — a 3× apparent advantage for the
modulator produced by the lower target (0.9 × 198.0 = 178 vs 0.9 × 160.8 = 145). Against the common
target 0.9 × 160.8 = 145, recovery reads **28,000 vs 40,000 episodes** (3.9 M vs 5.7 M environment
steps): the sign **reverses**. Under the Revision 2 rule, P3 (6 M of its 8 M episodes in Winter) would
have counted this artefact as a modulator win; under Revision 2a it is "not counted". In Danger-A the
levels are ordered the other way (ordinary lower), so the own-reference bias there would run against
the modulator — the companion guards both directions.

*Implementation hand-off (named; no code changed by this revision).* The common-reference readings are
**not** computed by `scripts/analysis/studies/continual_worlds/pilot_readout.py` today (its
`analyse_sequence` computes dip and recovery against each run's own `R_X` only), and the main analysis
does not exist yet. **`developer`** (via the `feature-workflow`, `senior-developer` plans) adds: per
sequence, pairing of the ordinary and modulated runs, `R_X,common`, the common-reference dip (steps and
fraction) and recovery (episodes and environment steps), and the four-reading vote per switch — before
the first P3 stage ends (14 M), so the first real switch is read with the rule as registered here. The
Winter numbers above were computed with the script's own `scan` / `Series` / `recovery` functions and a
fixed target of 0.9 × 160.8.

### 5.2 Modulator comparison

For every switch measure, the **modulated-minus-ordinary difference** (dip and recovery: negative
favours the modulator; return: positive). Reported per switch (4 per sequence), per sequence and
pooled across the 3 sequences, always next to the noise yardstick (5.5). The support / refute rule is
section 2's.

*Revision 2a (R4):* for every switch, the number of episodes (and environment steps) of other-world
training since that world's previous visit is printed next to its return value. In P3 this is 3 M
episodes of Winter before the Famine return and 1 M of Famine before the Winter return (3.7.2), so the
two returns are not read as equally tested.

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

*Revision 2a (R4):* every forgetting value is reported next to the **number of interfering episodes**
(and environment steps) between the two checkpoints it compares. With per-world stage lengths the
forgetting of Famine and of Winter in P3 are not measured after matched amounts of interference (3 M vs
1 M episodes), so forgetting is compared **between agents within a world**, never across worlds as if
matched. No rule change.

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
| C12 | Revision 1b scout worlds: each loaded through `load_env_config` → `load_env_params` and every `EnvParams` field (208) compared with its original | pass. **Danger-scout-A:** hunters [5, 7] → [3, 5], detection [5, 9] → [3, 5], chase stamina [100, 200] → [30, 150], lose-interest 2.0 → 1.5 (Home's resolved values: stamina [30, 150], lose-interest 1.5, detection [1, 7]); against Danger-soft only the detection / stamina / lose-interest arrays differ. **Danger-scout-B:** hunters [5, 7] → [2, 4]; per-hunter values identical. **Danger-scout-C:** hunters [5, 7] → [3, 5] and `sensor_radius` 5 → 8; against Danger-soft only `sensor_radius`. Every other Danger-scout difference is a per-slot array or index 2–3 slots shorter (12 → 10 / 9), per-entry values identical. **Fog-scout-A:** `sensor_radius` 3 → 5 and `noise_sigmas` smell 0.3 → 0.15, sight 0.2 → 0.1 (against Fog-soft: only `sensor_radius`). **Fog-scout-B:** only `perceptual_noise_enabled` True → False (disabled rather than σ 0, because the enabled path also clips every channel; Home runs with it disabled). No body, thermal, interoception or reward field differs; observation width 58 on all five (real `ParallelEnv.reset`) |
| C13 | Revision 2 schedules (P3 regenerated; P1- / P2-replacement drafts) built by `train._build_continual_schedule` itself, plus the trainer's own stage checks (observation width, action count, sensor-modality fingerprint, copied from `train.py`) | pass on all three: 5 stages each; P3 `[11M, 14M, 15M, 18M, 19M]`, drafts `[11M … 15M]`; restored counters 11,000,025 / 11,000,022 map to stage 1 (the first A-world), 10,999,999 to stage 0; width 58, 6 actions and an identical fingerprint in every stage. **Known Bug A2 slot check:** stage 0 (Forage) has 0 hunting-predator slots, so per-predator distance logging is off for the whole run; later stages have 2 (Winter, Famine) or 5 (Danger-A, Fog-B) hunter slots, which is safe only because stage 0 has none; rabbit slots are 5 in every stage (= stage 0), which the per-rabbit accumulator requires. No noise in any Rev 2 stage (Fog-B has it disabled) |

### 6.2 Blockers and hand-offs

- **B1 — roster-size change between stages (Known Bugs A2) — workaround accepted by the user.** The
  trainer sizes its per-animal distance buffers from stage 0 and never resizes them. Every
  continual run here (Pilot 2, the branches) has Forage (no hunting predator, 5 rabbit slots) as stage
  0 and 5 rabbit slots in every stage, so per-predator distance logging is off and nothing crashes.
  Cost: no per-predator distance curves. Pilot 1 and Pilot 3 are single-world runs and unaffected.
- **B2 — pilots not yet run.** No branch launches before Pilot 1 is analysed, `L_X` computed and the
  P1–P3 schedule files regenerated and re-built (C8 repeated). *Revision 2:* done for P3 (C13); P1 / P2
  blocked on the user's replacement decision (3.7.6).
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
  *Revision 2a correction (R5):* the first half applies to runs that start in stage 0 (Pilot 2), **not to
  the branches**. A branch restores into stage 1 and prints **no** `[STAGE] 0:01_forage -> 1:...` line.
  Its expected start-up lines are, in this order: `[RESUME] Checkpoint 'stage' field (0) != schedule-derived
  stage (1) ... trusting the schedule.` — **expected, not a fault** (the checkpoint was saved in Forage,
  stage 0; the trainer rebuilds the schedule's stage, the fixed Known Bug H2) — then `[RESUME] Stage
  1:02_winter environment rebuilt` (P3; the stage-1 world's name for other sequences). The first `[STAGE]`
  line of a P3 branch is `1:02_winter -> 2:03_famine` at ≈ 14 M episodes.
- Before the branches: repeat C8 on the regenerated schedules and C10 on the real branch-point copy;
  the smoke path S-A is re-run on the launch node if HEAD has moved since Pilot 2.

**Remaining pre-launch checklist for the branches (Revision 2).** P3 launches when 1–7 are done and the
user has said go; P1 / P2 additionally need the user's decision (3.7.6) and item 8.
*Revision 2a:* P3 launches when items 1–7 and 9 are done (item 1 unless waived under D8, item 10) and
the user has said go.

1. **Forage runs 1–2 end at 14 M** (ETA ≈ 8 h) → re-run the read-out and confirm `T_Forage` still gives
   `L_Forage` = 1 M, hence `B0` = 11 M (3.7.3). If it changed, regenerate the schedules first.
2. **Branch-point copies** of step 11,000,025 (ordinary) / 11,000,022 (modulated) with `config.yaml`
   (command in 4.2), then C10 on the real copies (the checkpoint manager's latest step = the copied step).
3. **`env-config-reviewer` pre-flight** on the regenerated P3 schedule and its stage folder (and, once
   approved, the two draft schedules and the Danger-A / Fog-B world files they use).
4. **Forgetting-matrix sweep, first real use.** Pilot 2 did not exercise it (no sweep spec or output
   exists). Before the branches — or at the latest before their first stage ends — write the sweep spec
   (5.3: `probe: configs/environment/experiment/continual_worlds`, `algo: rppo`, `episodes: 2000`,
   conditions updated for Rev 2: Home, Forage, Famine, Winter, Danger-A, Fog-B instead of the dropped
   worlds, subject to D4 / D5) and run it once on a finished Pilot 2 run (e.g. run 15) to confirm a full
   matrix comes out.
   *Revision 2a (R3):* this is a gate **before the branches launch** — the "or at the latest before their
   first stage ends" wording above is withdrawn. Run 15 is finished and its checkpoints exist; a developer
   is running the sweep on it now. Pilot 2 is "3 of 4 clauses met, provisional" until it produces a full
   matrix (3.7.5).
5. **Restore-into-a-later-stage path.** Pilot 2 started in stage 0; the branches start in stage 1 from a
   restored counter. At launch, check the first log lines: `[RESUME]` at the copied step, the run in stage
   1 (`02_winter` for P3) from its first iteration, and no traceback through the first checkpoint.
   *Revision 2a (R5), exact lines for `training-runner`:* (a) `[RESUME]` at step 11,000,025 (ordinary) /
   11,000,022 (modulated); (b) `[RESUME] Checkpoint 'stage' field (0) != schedule-derived stage (1) ...
   trusting the schedule.` — **expected; do not relaunch on it**; (c) `[RESUME] Stage 1:02_winter
   environment rebuilt`; (d) **no** `[STAGE] 0 -> 1` line — do not wait for one; the first `[STAGE]` line
   is `1:02_winter -> 2:03_famine` at ≈ 14 M episodes; (e) no traceback through the first checkpoint.
   A missing (c), or a `[STAGE] 0:01_forage -> ...` line, **is** a fault: stop the run.
6. **Live GPU state** (diary + `pgrep`, not only `nvidia-smi`) and NAS mount on each node; node 114 is not
   used until it answers SSH (it hung during the scout launch).
7. **Run 14** (Pilot 2a, modulated) finishes its last stage (≈ 1.3 h) with the same pass signs as runs 13,
   15, 16 — closes the Pilot 2 pipeline verdict.
   *Revision 2a:* at 23:45 run 14 was at 14.61 M of 15 M (≈ 17 min left). Items 4 and 7 together close
   Pilot 2 (3.7.5).
9. *(Revision 2a, R1)* The common-reference companion (5.1) is registered in this doc before launch —
   **done by this revision**. Its implementation in the analysis code (`developer` hand-off, 5.1) is
   needed before the first P3 stage ends (≈ 14 M), not before launch.
10. *(Revision 2a, D8)* Item 1 applies unless the user waives it (3.7.6 D8).
8. (P1 / P2 only) the user's decision D4 / D5; if a new Danger variant is chosen, its two-agent pilot first.

**Checklist status, 2026-09-29 (after the user's decisions, 3.7.7).** Applies to all branches, rows 19–24.

| Item | Status |
|---|---|
| 1 Forage runs reach 14 M | **waived for launch** (D8); the read-out is re-run and the confirmation reported when runs 1–2 end |
| 3 `env-config-reviewer` pre-flight on the schedules | **done — GO WITH NOTES** (P3 and the P1- / P2-replacement schedules; only header comments changed since) |
| Plan review of Revision 2a | **done — SOUND WITH CONCERNS** (addendum at the end of this doc) |
| 9 Common-reference analysis (5.1) | **done** — implemented in the read-out script, commit `a72eb943` |
| 8 User decisions D4 / D5 (and D1–D3, D6, D8) | **done** (3.7.7) |
| 4 Forgetting-matrix sweep run once on a finished Pilot 2 run | **in progress** (driver committed `9b0f753d`; a full matrix not yet seen) — gates the branches |
| 7 Run 14 finishes | **remaining** — at 00:12 on 2026-09-29 its log showed 14.81 M of 15 M, no "Training complete" yet |
| 2 Branch-point copies + C10 on the real copies | **remaining** |
| 6 Live GPU state (diary + `pgrep`) and NAS mount per node | **remaining** (at launch) |
| 5 Restore-into-stage-1 log lines | **at launch** (exact lines in item 5) |

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
| 7.11 *(Rev 2a)* | Dip or recovery favours the modulator under the own-reference reading but not under the common-reference reading (or the reverse) | that switch's H-dip / H-rec vote is not counted (5.1); both readings are reported. If this happens on most switches of a sequence, the sequence's verdict rests on return and forgetting only, and is worded so |

## 8. Metrics requested (optional, for the user)

| Metric | Why now | Where it'd live | Cost |
|---|---|---|---|
| Per-stage modulator activity (mean and spread of the FiLM scale and shift per site, per stage) | the "why" behind any H-dip / H-ret effect | `train.py` rPPO logging, `mod_info` already returned by the train step | cheap |
| Per-predator distance curves across roster changes | lost under B1's workaround | `train.py` continual stage switch (A2 fix) | cheap |
| Cumulative environment steps on the episode rows | makes F3's step-unit recovery exact rather than reconstructed | `train.py` `_emit_episode_row` (`global_step`) | cheap |

If accepted, route through `feature-workflow` before launch; none blocks the pilots.

## 9. Decisions (all taken 2026-09-28; user: "follow your recommendations")

*Revision 2 adds open decisions D1–D7 for the user (3.7.6); none is taken yet. Revision 2a adds D8.*
*2026-09-29: D1–D6 and D8 taken by the user, D7 deferred — see 3.7.7.*

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

## Feedback from plan-reviewer (Revision 2, 2026-09-28, against commit `bc2d32d3`)

**Verdict on the plan: NOT READY** — one Critical finding, cheap to fix, no rerun involved: the
pre-registered dip and recovery measures compare each agent with *its own* first-visit level, and the
pilots now show the two agents level off 37 steps apart in Winter (198 vs 161), so in P3 those two
votes would measure "how much lower is your plateau" rather than "how fast do you adapt". Adding a
common-reference companion reading to 5.1 **before** P3 launches flips this to SOUND WITH CONCERNS.
**Verdict on the pilot read-out: SUPPORTED WITH CAVEATS** — every per-world verdict, stage length,
the 11 M branch point and the Pilot 3 pass follow the pre-registered rules and match the read-out
data; the caveats are two overstated labels ("Pilot 2 pass", "Winter levelled off").
No goalpost was moved silently: the scouts are labelled exploratory everywhere, the drafts say DO NOT
LAUNCH in the files themselves, and per-world stage length and 11 M are what 3.3 / 3.4 say.
Full report with evidence: `docs/reviews/plan_continual_worlds_rev2.md`.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| R1 | 🔴 | 5.1, 2 (H-dip, H-rec), 3.7.1 Winter finding | Dip and recovery are relative to each agent's own `R_X`. The Winter pilot shows the artefact directly: zero-shot survival after the Home → Winter switch was similar (ordinary ≈ 129, modulated ≈ 138 steps), yet "recovery" reads 132k vs 40k episodes only because the targets differ (0.9 × 198 = 178 vs 0.9 × 161 = 145). In Danger-A the bias runs the other way (ordinary lower). Two of the four votes therefore track plateau level, not adaptation speed; with "3 of 4 measures" as the support rule this can manufacture or hide a verdict. | Before launch, pre-register in 5.1 a common-reference companion for both measures (dip in absolute steps, or against the lower of the two agents' `R_X`; recovery to 0.9 × min(`R_X,ord`, `R_X,mod`)) and make the H-dip / H-rec vote require the favourable sign under **both** the own- and common-reference readings — the same device F3 used for episodes vs environment steps. Return and forgetting are absolute already and need nothing. | experiment-designer |
| R2 | 🟡 | 3.7.2 ("it did level off"), 3.7.1 Winter finding, D6 | The modulated Winter curve is not flat: its trailing 200k mean peaks at 175.7 (2.54 M) and ends at 160.8, 8.5 % below — outside the 5 % plateau band (ordinary: 205.6 → 198.0, inside). The 3.3 fallback correctly does not fire (`T` is the *first* crossing), but the sentence overstates, the 37-step gap is partly a late decline (30 steps at the best windows), and `R_Winter` (2.8–3.0 M of the first visit) may be measured on a falling curve. | Reword; put the trailing-window trajectory in the Winter finding (project rule: temporal evolution, not endpoints); carry a "reference on a non-monotonic curve" note into results. This is evidence for D6's *look first* option. | experiment-designer |
| R3 | 🟡 | 3.7.5 "Pilot 2 — pipeline pass" | The pre-registered pass (3.6) has four clauses; two are unmet — run 14 is still in stage 5 and the forgetting-matrix sweep has never run. Verified clauses: 4 `[STAGE]` lines per run at 3–186 episodes drift, 0 tracebacks, 51 checkpoints, 3 of 4 runs "Training complete". 6.3 item 4's "or at the latest before their first stage ends" loosens the gate. | Label it "3 of 4 clauses met, provisional"; run the sweep on run 15 before the branches launch (checkpoints exist; nothing waits on training). | experiment-designer |
| R4 | 🟡 | 3.7.2, 5.2, 5.3 | Per-world lengths make P3 lopsided: the Famine return follows 3 M of Winter, the Winter return only 1 M of Famine, so the four switch votes carry unequal interference, the forgetting matrix's "matched times" are not matched across the two worlds, and the heavy-interference return lands on the world where the pilots show no agent difference (214 / 214). Same schedule for both agents, so not an agent confound; the rule is pre-registered and correctly applied. | State it in 5.2 / 5.3; report forgetting next to the number of interfering episodes; no rule change. | experiment-designer / experiment-analyzer |
| R5 | 🟡 | 6.3 (first bullet, item 5), 4.2 | The branch restore path is sound in code (`train.py:1559-1580` rebuilds the stage-1 world unconditionally — the fixed Known Bug H2) but the checklist names lines that will not appear and omits one that will: a branch prints `[RESUME] Checkpoint 'stage' field (0) != schedule-derived stage (1) ... trusting the schedule.` **before** `[RESUME] Stage 1:02_winter environment rebuilt`, and prints **no** `[STAGE] 0:01_forage -> 1:...` line at start. A runner reading the mismatch line as a fault, or waiting for a `[STAGE]` line, costs a relaunch. | Name the mismatch line as expected; drop the first-switch expectation for branches (the first `[STAGE]` is 1 → 2 at 14 M). | experiment-designer → training-runner |
| R6 | 🟢 | 3.7.4 point 1 | Cites failure mode 7.4 for Danger-A, but 7.4 triggers on survival < 0.6 × an agent's own `R_X` during a visit — a different condition; "best window 130.1 cleared the line" is not a 3.6 criterion. | State the with / without computation for Danger-A sequences on its own; keep "best window" out of the verdict sentence. | experiment-designer |
| R7 | 🟢 | 4 manifest | Rows 3–12 and 31–43 still read "running" though the section says every number is final. | Update statuses. | experiment-designer |

**Open assumptions (❓):** (O1) Winter's time to plateau from Forage ≈ from Home — if slower, `R_Winter` sits below plateau for both agents (3.3 caveat). (O2) Replacement-world verdicts rest on 1.5 M-episode reads where the pre-registered pilots used 3 M; curves are flat after ≈ 0.4 M, so probably robust — say so. (O3) One seed per arm everywhere; yardstick (c) exists only after the main runs. (O4) Node 114 times out on SSH now; the abandoned rows 39–41 never wrote data (wandb files untouched since 19:08, results dirs hold only `config.yaml`), so there is no collision — kill them if 114 returns live. (O5) Runs 1–2 hold node 106 for ≈ 8–11 h only to confirm an `L_Forage` that 3.7.3 proves cannot change; the pre-registered wording requires the wait, the user may waive it. (O6) No commit has touched `train.py` / `src/` since the 13:16 launch, so the "re-run S-A if HEAD moved" item is currently moot.

**Cost of being wrong:** if R1 stands and P3 (plus any Danger-A sequence) launches, the runs' data are fine but the two pre-registered adaptation votes are contaminated by a plateau-level difference the pilot already measures at 3×, and amending the rule after seeing P3 would be post-hoc — a headline claim that would not survive review, on the study's longest sequence. R2 / R3 cost a wrong label, not a run. Nothing here risks data loss (the only file operation is a read-only `cp -a` into a new directory).

Reviewed by: plan-reviewer

### Response from experiment-designer (Revision 2a, 2026-09-28)

All seven findings addressed in the doc; changed text is marked *Revision 2a* in place and replaced
wording is struck through (~~like this~~), not deleted. No config, schedule or script was changed.

| # | Resolution | Where |
|---|---|---|
| R1 🔴 | Common-reference companion pre-registered for dip (absolute steps against min(`R_X,ord`, `R_X,mod`), also as a fraction) and recovery (to 0.9 × min(`R_X,ord`, `R_X,mod`), episodes and environment steps). H-dip vote needs the favourable sign under own **and** common reference; H-rec under all four readings. Return and forgetting unchanged (already absolute). Winter pilot shown as motivation: own-reference recovery 132k vs 40k episodes, common-reference **28k vs 40k** (sign reverses) from near-equal zero-shot survival 129.4 vs 138.4. New failure mode 7.11. **Hand-off to `developer`** (via `feature-workflow`): implement the companion in `pilot_readout.py`'s sequence analysis and in the main analysis, before the first P3 stage ends | Rev 2a box, 2, 5.1, 7.11, 6.3 item 9 |
| R2 🟡 | "Levelled off" struck; Winter trailing-200k trajectory added (modulated peak 175.7 at 2.54 M → 160.8 at the end, −8.5 %; ordinary 205.6 → 198.0, −3.7 %); `R_Winter` may sit on a falling curve — carried into results; stated as evidence for D6 *look first* | 3.7.1, 3.7.2 |
| R3 🟡 | Pilot 2 relabelled "3 of 4 clauses met, provisional" until run 14 ends and the forgetting sweep runs once on run 15 (in progress by a developer); the sweep is now a gate before the branches | 3.7.5, 6.3 items 4, 7 |
| R4 🟡 | P3 asymmetry stated (Famine return after 3 M Winter; Winter return after 1 M Famine; forgetting not at matched times); interfering-episode counts reported next to every return and forgetting value; no rule change | 3.7.2, 5.2, 5.3 |
| R5 🟡 | Branch start-up lines named exactly (`[RESUME] Checkpoint 'stage' field (0) != schedule-derived stage (1) ... trusting the schedule.` expected, then `[RESUME] Stage 1:02_winter environment rebuilt`); no `[STAGE] 0 -> 1` line; first `[STAGE]` is 1 → 2 at ≈ 14 M. Checked against `train.py:1559-1580` | 6.3 first bullet, item 5 |
| R6 🟢 | 7.4 citation struck; the with / without-Danger-A verdict stated on its own (one-agent-only survivable); "best window 130.1" struck as a criterion | 3.7.1 scout table, 3.7.4 point 1 |
| R7 🟢 | Manifest statuses updated from the logs (23:45): 3–13, 15–18, 31–38, the three `_r2` rows, 42, 43 finished; 39–41 abandoned; 1, 2, 14, 27, 28 running | 4 |
| O5 | Recorded as user decision **D8**: the branches need not wait for runs 1–2 to reach 14 M (`L_Forage` cannot change; the 11 M checkpoints exist); waiting now costs ≈ 1.5–2 h, not 8 h | 3.7.6, 6.3 item 10 |

Signed: experiment-designer

### Addendum from plan-reviewer (re-check of Revision 2a, commit `e67ed196`, 2026-09-28)

**Verdict: SOUND WITH CONCERNS** — the exit condition is met. R1 is resolved in 5.1 before rows 23–24
launch: the common-reference companion (dip in absolute steps against the lower of the two agents'
first-visit levels; recovery to 0.9 × that level, in episodes and environment steps) is pre-registered,
the H-dip vote needs both readings and the H-rec vote all four, and failure mode 7.11 records a
disagreeing switch as "not counted". I recomputed the Winter example independently from the WandB rows
with the read-out script's own functions: shared target 144.7 steps, ordinary recovers at **28,000**
episodes, modulated at **40,000** — the sign reverses exactly as stated; zero-shot survival 129.4 /
138.4 confirmed. The rule is conservative in both directions (for the lower-plateau agent the two
readings coincide), which is the right shape for a screen.

R2–R7 wording confirmed: the Winter trajectory table matches the data at every column (152.9 … 198.0;
132.3 … 160.8); "3 of 4 clauses met, provisional" is the honest Pilot 2 label and the sweep is now a
launch gate; the R4 asymmetry statements and interfering-episode reporting are right; the branch
start-up lines in 6.3 match `train.py:1559-1580`; the 7.4 citation and "best window" are struck; manifest
statuses updated; D8 is a fair statement of O5.

Remaining concerns (none blocks launch):
- 🟢 6.3 item 5 line (a): the restore prints the step as `  -> Restored N model param leaves + optimizer
  state (checkpoint step 11000025).` (`src/utils/checkpoint_restore.py:60`), not as a `[RESUME]` line;
  name that line so the runner looks for the right one. Owner: experiment-designer.
- ❓ O7: the companion is registered but not yet implemented (`pilot_readout.py` reads own-reference only);
  the `developer` hand-off must land before the first P3 stage ends (≈ 6–7 h after launch at Winter's
  pilot throughput). Nothing is lost if it slips — the rows are logged — but the first switch would be
  read late. Owner: senior-developer → developer.
- ❓ O1–O4 from the Revision 2 feedback stand unchanged.

Cost of being wrong now: a wrong label or a late read, not a wrong claim and not a rerun.

Reviewed by: plan-reviewer
