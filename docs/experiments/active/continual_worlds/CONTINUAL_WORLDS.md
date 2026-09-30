---
title: "Continual worlds: does the modulator help an agent move between worlds whose body rules never change?"
topic: continual_worlds
status: active
created: 2026-09-28
last_updated: 2026-09-30
phase: continual / A-B-A-B structure (user framing 2026-09-28)
wandb_tag: "rppo_cw_*"
---

# Continual worlds: an A-B-A-B test of the modulator with a stationary body

> **Results — revision after verdict review (2026-09-30, `experiment-analyzer`) — in plain words.** Two agents, one
> ordinary and one with a modulator (a small side network that rescales the main network), learned a safe foraging
> world and then went back and forth four times between two harder worlds — hunters ↔ scarce food, fog ↔ hunters,
> cold ↔ scarce food — one run per agent per sequence, all six finished. **The rule written in advance does not decide
> the question.** Whether the modulated agent "forgot less" depends on whether the foraging world (learned before the
> back-and-forth) counts: counted, the rule says *supported* in 2 of 3 sequences; left out, so that only the alternating
> worlds count, the rule's *refutation* clause fires instead. Both readings are defensible from the design; neither was
> fixed before the data. What the data do show: the modulated agent's starting checkpoint already plays unseen worlds
> better **before any training there** (by 2–18 steps), which explains most of its smaller drop on first entering a new
> world — measured from its own start, it does not improve faster; it lost less foraging skill after cold- and
> hunter-world training (the largest case confirmed with sampled actions; one shared starting point); returns and
> forgetting on the alternating worlds show no difference beyond noise in the modulator's favour, so the May probe's
> large return advantage is not reproduced. One seed; both agents' pre-training began from identical main-network weights. Details: section 10 (revised verdict
> 10.8, exploratory head-start check 10.11); conclusions: section 11. An independent review of the first write-up is
> linked at the end of the doc.

> *Superseded 2026-09-29 results box, kept for the record (struck: its "support (fragile)" label and its first-entry
> reading did not survive the verdict review):*
> ~~**Results (2026-09-29, `experiment-analyzer`) — in plain words.** All six main runs finished (three~~
> ~~alternating sequences — hunters ↔ scarce food, fog ↔ hunters, cold ↔ scarce food — each with the ordinary and the~~
> ~~modulated agent, one seed each). Read the most literal way, the rule written in advance counts as **support** for~~
> ~~the modulator in 2 of the 3 sequences. The support is **fragile**: the rule never said how the per-switch votes~~
> ~~combine, and four of the five other reasonable ways of combining them give "not supported". What carries it is the~~
> ~~modulated agent's **smaller drop on first entering a new, harder world** (largest in the cold world) and its **better~~
> ~~memory of the foraging world learned before the alternation** — not better returns or less forgetting on the~~
> ~~alternating worlds, which is what the May probe found and what this study was built to replicate. Every result is a~~
> ~~single-seed first read for one pair of starting agents. Full results and caveats: section 10; conclusions: section 11.~~

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
> its direct 3-seed from-scratch replication under today's settings (separate design, 2026-09-29) [[MAY_DOUBLE_RETURN_REPLICATION]] ·
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
~~the ordinary and modulated agents differ in initialisation, capacity and seed as well as in the
modulator (factorial plan-review finding A2)~~ *[struck 2026-09-30, see the correction below]*. Hence the "one initialisation pair, three world-pairs"
wording (section 2) and the fresh-seed pre-training (3.5). Branching removes the three near-duplicate
Forage copies, and with them the old noise yardstick (a); nothing is lost (5.5).

**Correction (2026-09-30, `experiment-designer`; plan-review finding M1 on the results, [[plan_continual_worlds_main_verdict]]).**
The struck sentence was wrong about initialisation and seed. Checked directly: the two pre-trained agents
began their 10 M Home episodes from **the same starting network**.
- **Shared.** Both runs are seed 42 (saved config and launch argument agree). Rebuilding each run's untrained
  network with the trainer's own construction code gives **bitwise-identical main-network weights: 27 of 27
  arrays, 640,903 parameters**. The trainer's starting random keys (the first world's reset key and the
  training-loop key) are identical, and the saved environment sections of the two runs are equal, so the
  environment stream starts the same way. It diverges only once the two policies act differently.
- **Different.** Only the modulator: one extra parameter subtree in the modulated agent (33 arrays, 26,640
  parameters, about 4 % on top of the main network), and whatever it does to learning from step 1 on.
- **Consequence.** The study has **one initialisation pair**, not two independent agents: every between-agent
  difference is "the same start, perturbed by adding a modulator", and nothing here measures how far the same
  start drifts under *any* perturbation in these worlds (an ordinary agent from a different seed, say). No
  noise yardstick for that drift exists in this study. The head start on first entries (10.11) and every vote in
  10.8 are properties of this pair. Section 11.5 item 1 lists the controls a replication needs.
- **Method.** The same check as the parallel study's shared-start test on the May replication
  ([[ALGORITHMIC_NULL_ANALYSIS_TOOLING]], "Checkpoint 3.3"), which uses `scripts/analysis/nmn/untrained.py` (`build`,
  `run_seed`), itself tested bitwise against `train.py`'s construction. Script
  `tmp/20260930_cw_shared_start_l05.py`, output `tmp/20260930_cw_shared_start_l05.json`, CPU. Control: the same
  architecture built from seed 142 matches only 15 of the 27 arrays (the constant-initialised biases and LayerNorm
  scales), so the comparison can fail. Assumption: the construction code at launch (2026-09-27) equals today's; the
  key recipe is pinned by golden keys recorded before it was refactored (`tests/utils/test_init_keys.py`), and no
  step-0 checkpoint exists to check this more directly.

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
| 1 | finished ("Training complete", checked 2026-09-30) | Pilot 1 Forage (= main stage 1) | `rppo_cw_pilot1_forage_t1none_s42` | continual_worlds | pilot | 42 | 106 | cuda:0 | 2026-09-28T13:16:42 | `6sf68was` | `logs/20260928_131642.log` |
| 2 | finished ("Training complete", checked 2026-09-30) | Pilot 1 Forage (= main stage 1) | `rppo_cw_pilot1_forage_t16quad_s42` | continual_worlds | pilot | 42 | 106 | cuda:1 | 2026-09-28T13:16:46 | `e78og819` | `logs/20260928_131646.log` |
| 3 | finished ("Training complete", checked 2026-09-30) | Pilot 1 Danger | `rppo_cw_pilot1_danger_t1none_s42` | continual_worlds | pilot | 42 | 107 | cuda:0 | 2026-09-28T13:16:50 | `7e8rr45p` | `logs/20260928_131650.log` |
| 4 | finished ("Training complete", checked 2026-09-30) | Pilot 1 Danger | `rppo_cw_pilot1_danger_t16quad_s42` | continual_worlds | pilot | 42 | 107 | cuda:1 | 2026-09-28T13:16:53 | `gwkhnlpl` | `logs/20260928_131653.log` |
| 5 | finished ("Training complete", checked 2026-09-30) | Pilot 1 Famine | `rppo_cw_pilot1_famine_t1none_s42` | continual_worlds | pilot | 42 | 108 | cuda:0 | 2026-09-28T13:16:56 | `p0ev5nbw` | `logs/20260928_131656.log` |
| 6 | finished ("Training complete", checked 2026-09-30) | Pilot 1 Famine | `rppo_cw_pilot1_famine_t16quad_s42` | continual_worlds | pilot | 42 | 108 | cuda:1 | 2026-09-28T13:17:00 | `lf5tquew` | `logs/20260928_131700.log` |
| 7 | finished ("Training complete", checked 2026-09-30) | Pilot 1 Winter | `rppo_cw_pilot1_winter_t1none_s42` | continual_worlds | pilot | 42 | 109 | cuda:0 | 2026-09-28T13:17:04 | `s85qrj65` | `logs/20260928_131704.log` |
| 8 | finished ("Training complete", checked 2026-09-30) | Pilot 1 Winter | `rppo_cw_pilot1_winter_t16quad_s42` | continual_worlds | pilot | 42 | 109 | cuda:1 | 2026-09-28T13:17:07 | `4bapjjog` | `logs/20260928_131707.log` |
| 9 | finished ("Training complete", checked 2026-09-30) | Pilot 1 Fog | `rppo_cw_pilot1_fog_t1none_s42` | continual_worlds | pilot | 42 | 110 | cuda:0 | 2026-09-28T13:17:11 | `nealqwms` | `logs/20260928_131711.log` |
| 10 | finished ("Training complete", checked 2026-09-30) | Pilot 1 Fog | `rppo_cw_pilot1_fog_t16quad_s42` | continual_worlds | pilot | 42 | 110 | cuda:1 | 2026-09-28T13:17:14 | `4rkcrqzp` | `logs/20260928_131714.log` |
| 11 | finished ("Training complete", checked 2026-09-30) | Pilot 1 Harsh | `rppo_cw_pilot1_harsh_t1none_s42` | continual_worlds | pilot | 42 | 111 | cuda:0 | 2026-09-28T13:17:18 | `cssu3qc3` | `logs/20260928_131718.log` |
| 12 | finished ("Training complete", checked 2026-09-30) | Pilot 1 Harsh | `rppo_cw_pilot1_harsh_t16quad_s42` | continual_worlds | pilot | 42 | 111 | cuda:1 | 2026-09-28T13:17:22 | `xbpq1y9s` | `logs/20260928_131722.log` |
| 13 | finished ("Training complete", checked 2026-09-30) | Pilot 2a shakedown | `rppo_cw_pilot2a_t1none_s42` | continual_worlds | pilot | 42 | 112 | cuda:0 | 2026-09-28T13:17:26 | `tdpz3ju7` | `logs/20260928_131726.log` |
| 14 | finished ("Training complete", checked 2026-09-30) | Pilot 2a shakedown | `rppo_cw_pilot2a_t16quad_s42` | continual_worlds | pilot | 42 | 112 | cuda:1 | 2026-09-28T13:17:30 | `si97t2j5` | `logs/20260928_131730.log` |
| 15 | finished ("Training complete", checked 2026-09-30) | Pilot 2b shakedown | `rppo_cw_pilot2b_t1none_s42` | continual_worlds | pilot | 42 | 113 | cuda:0 | 2026-09-28T13:17:34 | `rygfw76a` | `logs/20260928_131734.log` |
| 16 | finished ("Training complete", checked 2026-09-30) | Pilot 2b shakedown | `rppo_cw_pilot2b_t16quad_s42` | continual_worlds | pilot | 42 | 113 | cuda:1 | 2026-09-28T13:17:38 | `zjsdfoyq` | `logs/20260928_131738.log` |
| 17 | finished ("Training complete", checked 2026-09-30) | Pilot 3 Nursery (= seed-43 leg) | `rppo_cw_nursery_t1none_s43` | continual_worlds | pilot | 43 | 102 | cuda:0 | 2026-09-28T13:17:41 | `98tm6jxe` | `logs/20260928_131741.log` |
| 18 | finished ("Training complete", checked 2026-09-30) | Pilot 3 Nursery (= seed-43 leg) | `rppo_cw_nursery_t16quad_s43` | continual_worlds | pilot | 43 | 102 | cuda:1 | 2026-09-28T13:17:45 | `q3ni07j6` | `logs/20260928_131745.log` |
| 19 | finished ("Training complete", checked 2026-09-30) | P1-replacement branch Danger-A ↔ Famine, ordinary | `rppo_cw_p1_danger_scout_a_famine_t1none_s42` | continual_worlds | prod | 42 | 108 | cuda:0 | 2026-09-29T00:39:59 | `6jz5xgtf` | `logs/20260929_003959.log` |
| 20 | finished ("Training complete", checked 2026-09-30) | P1-replacement branch Danger-A ↔ Famine, modulated | `rppo_cw_p1_danger_scout_a_famine_t16quad_s42` | continual_worlds | prod | 42 | 108 | cuda:1 | 2026-09-29T00:40:06 | `f6sqgsgg` | `logs/20260929_004006.log` |
| 21 | finished ("Training complete", checked 2026-09-30) | P2-replacement branch Fog-B ↔ Danger-A, ordinary | `rppo_cw_p2_fog_scout_b_danger_scout_a_t1none_s42` | continual_worlds | prod | 42 | 109 | cuda:0 | 2026-09-29T00:40:12 | `7szjx34t` | `logs/20260929_004012.log` |
| 22 | finished ("Training complete", checked 2026-09-30) | P2-replacement branch Fog-B ↔ Danger-A, modulated | `rppo_cw_p2_fog_scout_b_danger_scout_a_t16quad_s42` | continual_worlds | prod | 42 | 109 | cuda:1 | 2026-09-29T00:40:18 | `r96fgv4u` | `logs/20260929_004018.log` |
| 23 | finished ("Training complete", checked 2026-09-30) | P3 branch Winter ↔ Famine, ordinary | `rppo_cw_p3_t1none_s42` | continual_worlds | prod | 42 | 107 | cuda:0 | 2026-09-29T00:39:47 | `qdnh5rzy` | `logs/20260929_003947.log` |
| 24 | finished ("Training complete", checked 2026-09-30) | P3 branch Winter ↔ Famine, modulated | `rppo_cw_p3_t16quad_s42` | continual_worlds | prod | 42 | 107 | cuda:1 | 2026-09-29T00:39:53 | `q6j9pu1o` | `logs/20260929_003953.log` |
| 25 | planned — unblocked (Pilot 3 passed) | Nursery leg | `rppo_cw_nursery_t1none_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 26 | planned — unblocked (Pilot 3 passed) | Nursery leg | `rppo_cw_nursery_t16quad_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 27 | finished ("Training complete", checked 2026-09-30) | Home leg | `rppo_cw_home_t1none_s43` | continual_worlds | prod | 43 | 102 | cuda:0 | 2026-09-28T17:14:41 | `6gc2tok9` | `logs/20260928_171441.log` |
| 28 | finished ("Training complete", checked 2026-09-30) | Home leg | `rppo_cw_home_t16quad_s43` | continual_worlds | prod | 43 | 102 | cuda:1 | 2026-09-28T18:02:28 | `cmnof24a` | `logs/20260928_180229.log` |
| 29 | planned (after 25) | Home leg | `rppo_cw_home_t1none_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 30 | planned (after 26) | Home leg | `rppo_cw_home_t16quad_s44` | continual_worlds | prod | 44 | — | — | — | — | — |
| 31 | finished ("Training complete", checked 2026-09-30) | Pilot 1s Danger-soft | `rppo_cw_pilot1s_danger_soft_t1none_s42` | continual_worlds | pilot | 42 | 101 | cuda:0 | 2026-09-28T16:20:23 | `ww9ck47l` | `logs/20260928_162023.log` |
| 32 | finished ("Training complete", checked 2026-09-30) | Pilot 1s Danger-soft | `rppo_cw_pilot1s_danger_soft_t16quad_s42` | continual_worlds | pilot | 42 | 101 | cuda:1 | 2026-09-28T16:20:24 | `kgvn98p5` | `logs/20260928_162024.log` |
| 33 | finished ("Training complete", checked 2026-09-30) | Pilot 1s Fog-soft | `rppo_cw_pilot1s_fog_soft_t1none_s42` | continual_worlds | pilot | 42 | 104 | cuda:0 | 2026-09-28T16:28:58 | `ruudv8i6` | `logs/20260928_162858.log` (shared with row 34; clean copy `wandb/run-20260928_162915-ruudv8i6/files/output.log`) |
| 34 | finished ("Training complete", checked 2026-09-30) | Pilot 1s Fog-soft | `rppo_cw_pilot1s_fog_soft_t16quad_s42` | continual_worlds | pilot | 42 | 104 | cuda:1 | 2026-09-28T16:28:58 | `il157bos` | `logs/20260928_162858.log` (shared with row 33; clean copy `wandb/run-20260928_162915-il157bos/files/output.log`) |
| 35 | finished ("Training complete", checked 2026-09-30) | Pilot 1s Harsh-soft | `rppo_cw_pilot1s_harsh_soft_t1none_s42` | continual_worlds | pilot | 42 | 103 | cuda:0 | 2026-09-28T16:20:25 | `dxkzhykp` | `logs/20260928_162025.log` |
| 36 | finished ("Training complete", checked 2026-09-30) | Pilot 1s Harsh-soft | `rppo_cw_pilot1s_harsh_soft_t16quad_s42` | continual_worlds | pilot | 42 | 103 | cuda:1 | 2026-09-28T16:20:26 | `hjktbwln` | `logs/20260928_162026.log` |
| 37 | finished ("Training complete", checked 2026-09-30) | Scout Danger-A (3–5 hunters, Home-like persistence) | `rppo_cw_scout_danger_scout_a_t1none_s42` | continual_worlds | pilot | 42 | 105 | cuda:0 | 2026-09-28T19:07:59 | `yhezxekl` | `logs/20260928_190759.log` |
| 38 | finished ("Training complete", checked 2026-09-30) | Scout Danger-B (2–4 hunters) | `rppo_cw_scout_danger_scout_b_t1none_s42` | continual_worlds | pilot | 42 | 105 | cuda:1 | 2026-09-28T19:08:06 | `59wq3jqj` | `logs/20260928_190807.log` |
| 39 | abandoned — node 114 hung during compile ~19:09; if 114 recovers, kill any rppo_cw_scout_ processes there (relaunched as `_r2`, next row) | Scout Danger-C (3–5 hunters + smell 8) | `rppo_cw_scout_danger_scout_c_t1none_s42` | continual_worlds | pilot | 42 | 114 | cuda:0 | 2026-09-28T19:08:13 | `4k8wgp8j` | `logs/20260928_190814.log` |
| 39-r2 | finished ("Training complete", checked 2026-09-30) | Scout Danger-C (3–5 hunters + smell 8) — relaunch of 39 | `rppo_cw_scout_danger_scout_c_t1none_s42_r2` | continual_worlds | pilot | 42 | 107 | cuda:0 | 2026-09-28T19:27:46 | `fv0sdsvh` | `logs/20260928_192746.log` |
| 40 | abandoned — node 114 hung during compile ~19:09; if 114 recovers, kill any rppo_cw_scout_ processes there (relaunched as `_r2`, next row) | Scout Fog-A (Fog-soft + smell 5) | `rppo_cw_scout_fog_scout_a_t1none_s42` | continual_worlds | pilot | 42 | 114 | cuda:1 | 2026-09-28T19:08:20 | `zm73ti5c` | `logs/20260928_190821.log` |
| 40-r2 | finished ("Training complete", checked 2026-09-30) | Scout Fog-A (Fog-soft + smell 5) — relaunch of 40 | `rppo_cw_scout_fog_scout_a_t1none_s42_r2` | continual_worlds | pilot | 42 | 107 | cuda:1 | 2026-09-28T19:27:55 | `n1zmj65i` | `logs/20260928_192755.log` |
| 41 | abandoned — node 114 hung during compile ~19:09; if 114 recovers, kill any rppo_cw_scout_ processes there (relaunched as `_r2`, next row) | Scout Fog-B (smell 3, no noise) | `rppo_cw_scout_fog_scout_b_t1none_s42` | continual_worlds | pilot | 42 | 114 | cuda:2 | 2026-09-28T19:08:27 | `h4772olp` | `logs/20260928_190827.log` |
| 41-r2 | finished ("Training complete", checked 2026-09-30) | Scout Fog-B (smell 3, no noise) — relaunch of 41 | `rppo_cw_scout_fog_scout_b_t1none_s42_r2` | continual_worlds | pilot | 42 | 110 | cuda:0 | 2026-09-28T19:28:03 | `pvzvl7bm` | `logs/20260928_192803.log` |
| 42 | finished ("Training complete", checked 2026-09-30) | Scout Danger-A, modulated agent (pairs row 37) | `rppo_cw_scout_danger_scout_a_t16quad_s42` | continual_worlds | pilot | 42 | 109 | cuda:0 | 2026-09-28T20:54:17 | `35fobtmf` | `logs/20260928_205417.log` |
| 43 | finished ("Training complete", checked 2026-09-30) | Scout Fog-B, modulated agent (pairs row 41-r2) | `rppo_cw_scout_fog_scout_b_t16quad_s42` | continual_worlds | pilot | 42 | 109 | cuda:1 | 2026-09-28T21:01:05 | `v9qvx2p3` | `logs/20260928_210105.log` |

*Revision 2a (R7), statuses checked 23:45 against each log's "Training complete" line:* rows 3–13,
15–18, 31–38, 39-r2 / 40-r2 / 41-r2, 42 and 43 **finished**; rows 39–41 **abandoned** (node 114);
still **running**: 1 (12.35 M of 14 M), 2 (11.94 M of 14 M), 14 (14.61 M of 15 M), 27 (7.15 M of 10 M),
28 (5.51 M of 10 M). Row 13 is finished (the Revision 2 text already said so).

*2026-09-30 (experiment-designer, reviewer M1 follow-up):* every row's log re-checked for its "Training complete"
line (rows 33–34 in their clean WandB copies). Rows 1–24, 27–28, 31–38, 39-r2 / 40-r2 / 41-r2, 42 and 43 are
**finished**, including the main runs 19–24 (P1-replacement, P2-replacement, P3). Rows 39–41 stay **abandoned**
(node 114; no "Training complete" line). Rows 25–26 and 29–30 (seed-44 Nursery and Home legs) were **never
launched** — no log or results folder carries their tags — and stay planned; before any launch they are subject
to the cross-seed checklist in 11.5 item 1.

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

*Added 2026-09-29 by `experiment-analyzer` (Step C of the continual analysis plan). Nothing above this
section was changed except a pointer box at the top of the doc. Every verdict here is a **single-seed first
read**: one ordinary and one modulated run per sequence, all six branching from the same pair of agents.*

> **Revision after verdict review, 2026-09-30 — the verdict in plain words.** An independent review of the first
> write-up (below, kept with its unsupported passages struck) found that its label, "fragile support", picked one of two
> outcomes the pre-registered rule allows. Revised:
>
> **The rule written in advance does not decide this study.** It has a clause for "supported" and a clause for
> "refuted", and on these data it reaches **both**, depending on whether the forgetting of the **foraging world** —
> learned *before* the back-and-forth began — counts. Count it: the modulator is supported in 2 of 3 sequences.
> Leave it out and only the alternating worlds count — the ones the May probe was about and this study was built to
> replicate: the rule's refutation clause fires instead (hunters ↔ scarce food mixed, and there the modulated agent
> actually forgot *more*, 14 steps in total though each entry is inside noise; fog ↔ hunters with no favourable difference beyond noise and one
> difference beyond noise *against* the modulator). The design justifies both readings, and neither was fixed before
> the data were seen. So the verdict is **not decided**, and the hinge is which worlds count in the forgetting vote
> (10.8).
>
> **What the data do show.** (1) The modulated agent's checkpoint plays unseen worlds better **before any training in
> them**, by 2–18 steps (cold world 133 vs 114). Most of its apparent "smaller drop on first entry" is this head start
> (18.5 of the 24.5 steps in the cold world), and measured from its own starting level it does **not** improve faster
> after a switch (better in 2 of 6 first visits, worse in 4; exploratory, 10.11). (2) It lost less of its foraging skill
> after cold-world and hunter-world training — but this rests on one shared starting checkpoint at the survival ceiling,
> reverses once (hunter world, second visit) and shows up only after those two worlds; its largest case (after the cold
> world, 114 steps) holds with sampled as well as greedy actions, and at that point the modulated agent is not worse in
> the cold world itself, so "it just specialised less" does not explain it (10.5). (3) On returns
> and on forgetting of the alternating worlds, nothing distinguishes the two agents; May's 107–132-step return advantage
> is not reproduced.
>
> **Scope.** One seed; the two agents' pre-training began from the same main-network weights (the modulator was the
> only difference at initialisation), and all three sequences branch from the same pair of pre-trained checkpoints — a
> first read of **one starting pair**, not of the modulator.
>
> *Superseded 2026-09-29 box, kept for the record:*
>
> **Verdict in plain words.**
>
> **What was tested.** Two agents — an ordinary recurrent agent and the same agent with a modulator (a side
> network that rescales the main network's layers) — each learned a safe foraging world, then went back and
> forth four times between two harder worlds: (P1) a world with several hunting predators ↔ a world with
> scarce food; (P2) a foggy world ↔ the hunter world; (P3) a cold world with a single fire ↔ the scarce-food
> world. Survival (steps alive per episode) is the only yardstick. Four questions were fixed in advance:
> does the modulated agent's survival **drop less** right after a switch, **climb back faster**, do better on
> the **return** visit, and **forget less** of a world while it trains in another?
>
> ~~**Answer: a fragile, rule-dependent pass of the pre-registered support rule — and not the May pattern.**~~
> ~~Read the most literal way (10.2), the rule written in advance is **met**: in 2 of the 3 sequences (fog ↔ hunters~~
> ~~and cold ↔ scarce food) three of the four measures favour the modulator and at least one favourable difference is~~
> ~~beyond noise. But the pass is **fragile**. The beyond-noise differences behind it are the modulator's smaller drop on~~
> ~~first entering the cold world and its better memory of the **foraging world** — the world both agents learned~~
> ~~*before* the alternation began — not anything on the alternating worlds themselves. And the pass disappears under four~~
> ~~of the five other reasonable ways of combining the per-switch votes (10.9). In the wording the design requires: **one~~
> ~~initialisation pair, three world-pairs, one seed — weak, rule-dependent support, not evidence about the modulator in~~
> ~~general.**~~
> *[Struck 2026-09-30: the rule reaches both its support and its refutation clause; the hinge is the forgetting
> entry set, not the combination rule — 10.8 revised verdict, 10.9 R7.]*
>
> ~~**Where the modulator does look better:** on the **first entry into a new, harder world** it falls less and~~
> ~~climbs back sooner — in all three sequences. The largest case is the cold world: in its first 20,000~~
> ~~episodes there the modulated agent survived 133 steps against 109 for the ordinary agent (+24.5 steps,~~
> ~~just beyond this study's noise yardstick).~~
> *[Struck 2026-09-30: mostly the starting checkpoint's zero-shot head start (18.5 of 24.5 steps in the cold world), not
> adaptation — 10.11; the yardstick it clears is a two-window SD — 10.3 revision.]* **Where it does not:** once both agents have seen a world, the
> switches back into it cost both agents about the same, and the returns differ by −4 to +11 steps — none
> beyond noise in the modulator's favour, one beyond noise against it. In May, the modulated agent was
> 107–132 steps ahead on returns and forgot far less; nothing that large appears here. Forgetting is mixed:
> on the alternating worlds themselves the forgetting differences are small (−8 to +8 steps) and all inside
> noise — favouring the modulator in the fog sequence, the ordinary agent in the hunter ↔ scarce-food sequence, and split
> in the cold sequence. What the modulated agent clearly kept better is the **foraging world**: after 3 M episodes of
> cold-world training it had lost 63 steps of foraging survival, the ordinary agent 175 ~~(beyond noise at one or more
> checkpoints in every sequence)~~ *[qualified 2026-09-30: reverses at P1's second hunter-world visit, appears only after
> cold/hunter stages, one shared ceiling-level starting cell; the largest cell holds with sampled actions — 10.5 revision]*.
>
> **Caveats that travel with every sentence above:** one seed per agent; the three sequences share the
> same starting agents, so they are not independent votes; the hunter and fog worlds were chosen by
> exploratory scouting after the pre-registered versions proved unsurvivable; in the cold world the
> modulated agent again settled lower than the ordinary one over the reference window (175 vs 195 steps,
> last 200,000 episodes of the first visit — though its curve was swinging, and its final checkpoint plays the
> cold world as well as the ordinary one's), which inflates its "own-reference" readings there; and §2 never said how the four per-switch votes of a measure combine
> into one sign — the rule used below was chosen **after** the data were seen, so every combination rule
> we considered reasonable is reported side by side (10.9), and **the verdict changes with the rule**.

### 10.1 Runs, identity and completeness

| Row | Sequence | Agent | WandB id | Finished | Episodes after branch | Iterations per stage (2 / 3 / 4 / 5) |
|---|---|---|---|---|---|---|
| 19 | P1 Danger-A ↔ Famine | ordinary | `6jz5xgtf` | yes ("Training complete") | 4.000 M | 6,900 / 12,450 / 7,850 / 12,700 |
| 20 | P1 Danger-A ↔ Famine | modulated | `f6sqgsgg` | yes | 3.996 M | 7,050 / 12,500 / 7,900 / 12,950 |
| 21 | P2 Fog-B ↔ Danger-A | ordinary | `7szjx34t` | yes | 4.000 M | 7,400 / 7,650 / 8,150 / 7,950 |
| 22 | P2 Fog-B ↔ Danger-A | modulated | `r96fgv4u` | yes | 3.996 M | 7,600 / 7,750 / 8,250 / 7,950 |
| 23 | P3 Winter ↔ Famine | ordinary | `qdnh5rzy` | yes | 8.000 M | 29,350 / 12,900 / 37,650 / 13,150 |
| 24 | P3 Winter ↔ Famine | modulated | `q6j9pu1o` | yes | 7.996 M | 30,350 / 12,900 / 35,400 / 13,150 |

Every branch restored the intended branch-point copy (step 11,000,025 ordinary / 11,000,022 modulated;
matched on step directory, byte-identical `config.yaml` and file sizes) and started in stage 2. The D8
waiver is confirmed after the fact: the finished Forage runs give `T_Forage` = 200k for both agents, so
`L_Forage` = 1 M and `B0` = 11 M as used. (Manifest statuses for rows 19–24 still read "running"; the
manifest belongs to `experiment-designer` / `training-runner` and is not edited here.)

Sources: `results/analysis/continual_worlds/pilot_readout.json` (read-out script re-run 2026-09-29 ≈ 20:20 after P3 finished,
print `tmp/20260929_continual_main_readout.log`); extra per-stage quantities
`tmp/20260929_cw_main_extra.json` (`tmp/20260929_cw_main_analysis.py`, which imports the read-out
script's own `Series` / `recovery` functions); votes, forgetting and sensitivity
`tmp/20260929_cw_main_verdict.json` (`tmp/20260929_cw_main_verdict.py`); forgetting matrices
`results/analysis/continual_worlds/forgetting_{p1,p2,p3}_{t1none,t16quad}.json`.

### 10.2 Two scoring issues, stated before the tables

**(i) The tie rule as written vs. as coded.** 3.7.7 (a) pre-registers: *"If both agents recover in the same
logged row … that reading is a tie; a vote with any tied reading is 'not counted (tie)'."* The read-out
script implements a tie as **exact equality** of the recovery episode counts. In 7 of the 12 main-run
switches both agents recover in the **same logged row** — in 6 of them the very first row at which a full
20,000-episode window exists, i.e. neither agent needed any recovery — and their episode counts differ by
2–127 episodes (the jitter of where each run's logging grid falls, not adaptation). The script turns five of
these into votes (four "unfavourable", one "favourable"). **This analysis applies 3.7.7 (a) as written**
(same logged row → tie → not counted). The script's version is reported as sensitivity rule R2. Hand-off
to `developer` in 11.4.

**(ii) The combination gap (a post-data choice).** Section 2 asks whether "the modulated-minus-ordinary
difference has the favourable sign on at least 3 of the 4 switch measures" per sequence, but each measure
has up to four per-switch votes (dip, recovery), two return values, and several forgetting entries per
sequence; nothing says how they combine into one sign. **Primary rule (R1), adopted as the most literal
reading:** a measure has the favourable sign in a sequence when, among its **counted** switch-level votes,
favourable votes **outnumber** unfavourable ones; equal counts (including none counted) are not favourable.
Why this reading: (1) Revision 2a makes the **per-switch vote** the unit for dip and recovery ("the H-dip
vote for a switch counts only if …"); (2) 3.7.7 (b) says a unanimous-against vote "counts **against** the
modulator in **section 2's tally**" — a tally in which votes for and against offset each other; (3) "not
counted" (5.1, 7.9, 7.11) means dropped from that tally, not scored as against; (4) 3.7.7 (a) says a tie
is not favourable, so an even tally is not favourable either. The same tally is applied to return (one vote
per return visit) and to forgetting (one vote per forgetting entry of 5.3: every world of the sequence —
Forage, A, B — at every later stage-end checkpoint, since 3.3 lists Forage as stage 1 of every sequence).
**"Beyond noise"** (section 2's second clause) is read as: at least one favourable switch-level difference,
inside a measure that is favourable, exceeds the 5.5 yardstick (dip in common-reference steps; return) or
has non-overlapping 95 % CIs (forgetting, 5.3). Recovery is counted in episodes and has no yardstick in
survival units, so it cannot supply this clause. **Both choices were made after the per-switch numbers had
been printed**; they are flagged as post-data, and 10.9 reports the verdict under five alternatives.

### 10.3 Dip and recovery, switch by switch

"S20k" = mean survival (steps) over the first 20,000 episodes after the switch. "R" = the agent's own
reference (last 200,000 episodes of its first visit to that world); "R_common" = the lower of the two.
Differences are modulated minus ordinary; for dip and recovery, **negative favours the modulator**. Noise
threshold = 2 × max(seed floor 2.1, √2 × the larger within-visit SD) in steps (5.5). May's ±4.4 steps for
scale.

| Seq | Switch (visit) | S20k ord / mod | R ord / mod (common) | Own dip ord / mod | Common-dip diff (steps) | Noise thr. | **H-dip vote** | Recovery own, k-episodes ord / mod | Recovery common, k-ep ord / mod | Same logged row? | **H-rec vote** (as registered) | Script's H-rec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | Forage → Danger-A (1st) | 31.8 / 36.3 | 122.0 / 126.3 (122.0) | 73.9 % / 71.2 % | −4.5 | 5.2 | **favourable** | 212 / 184 | 212 / 148 | no | **favourable** | favourable |
| P1 | Danger-A → Famine (1st) | 178.1 / 184.1 | 208.1 / 210.7 (208.1) | 14.4 % / 12.6 % | −5.9 | 9.6 | **favourable** | 28 / 24 | 28 / 24 | no | **favourable** | favourable |
| P1 | Famine → Danger-A (return) | 117.1 / 120.7 | as above | 4.0 % / 4.4 % | −3.5 | 4.2 | not counted (7.11: own favours ordinary, common favours modulated) | 20.0 / 20.0 | 20.0 / 20.0 | yes (first row) | **not counted (tie)** | unfavourable |
| P1 | Danger-A → Famine (return) | 193.1 / 192.7 | as above | 7.2 % / 8.5 % | +0.4 | 4.2 | **unfavourable** | 20.0 / 20.1 | 20.0 / 20.1 | yes (first row) | **not counted (tie)** | unfavourable |
| P2 | Forage → Fog-B (1st) | 40.1 / 45.3 | 133.0 / 131.2 (131.2) | 69.9 % / 65.5 % | −5.2 | 5.6 | **favourable** | 144 / 104 | 140 / 104 | no | **favourable** | favourable |
| P2 | Fog-B → Danger-A (1st) | 114.2 / 117.1 | 127.5 / 130.4 (127.5) | 10.5 % / 10.2 % | −3.0 | 4.2 | **favourable** | 20.1 / 32.0 | 20.1 / 20.0 | own no, common yes | **not counted (tie; own and common also disagree)** | not counted |
| P2 | Danger-A → Fog-B (return) | 117.5 / 121.7 | as above | 11.6 % / 7.2 % | −4.2 | 4.2 | **favourable** | 20.0 / 20.0 | 20.0 / 20.0 | yes (first row) | **not counted (tie)** | unfavourable |
| P2 | Fog-B → Danger-A (return) | 125.2 / 127.5 | as above | 1.8 % / 2.2 % | −2.4 | 4.2 | not counted (7.11) | 20.0 / 20.1 | 20.0 / 20.1 | yes (first row) | **not counted (tie)** | unfavourable |
| P3 | Forage → Winter (1st) | 108.9 / 133.4 | 195.2 / 174.7 (174.7) | 44.2 % / 23.6 % | **−24.5** | 22.6 | **favourable, beyond noise** | 568 / 84 | 196 / 84 | no | **favourable** | favourable |
| P3 | Winter → Famine (1st) | 196.2 / 197.8 | 214.7 / 212.1 (212.1) | 8.6 % / 6.7 % | −1.6 | 5.2 | **favourable** | 20.1 / 20.0 | 20.1 / 20.0 | yes (first row) | **not counted (tie)** | favourable |
| P3 | Famine → Winter (return) | 120.7 / 144.6 | as above | 38.2 % / 17.2 % | −23.9 | 27.3 | **favourable** (inside noise) | 36 / 40 | 32 / 40 | no | **unfavourable** | unfavourable |
| P3 | Winter → Famine (return) | 206.5 / 205.5 | as above | 3.8 % / 3.1 % | +0.9 | 4.2 | not counted (7.11) | 20.0 / 20.1 | 20.0 / 20.1 | yes (first row) | **not counted (tie)** | not counted (7.9) |

Recovery in environment steps agrees in sign with episodes on every untied reading (e.g. P3 first Winter
entry: own 65.6 M vs 10.1 M steps, common 18.9 M vs 10.1 M; P3 Winter return: common 4.7 M vs 6.2 M).

**Tally per sequence (R1).** H-dip: P1 2 favourable / 1 unfavourable / 1 not counted → favourable; P2 3 / 0 /
1 → favourable; P3 3 / 0 / 1 → favourable. H-rec: P1 2 / 0 / 2 ties → favourable; P2 1 / 0 / 3 → favourable;
P3 1 / 1 / 2 → **not favourable** (even).

*What the recovery column really shows.* Recovery carries information only where survival fell well below 90 % of
the reference: the three first entries from Forage, the Winter return, and marginally the first Danger-A → Famine switch
of P1 (28k vs 24k episodes) and the own-reference reading of P2's first Fog-B → Danger-A switch (20k vs 32k).
Everywhere else both agents were above the recovery line in the first 20,000-episode window, so the measure sits at its
floor. The modulator recovers faster on all three first entries (by 64k, 36k and 112k episodes on the common target;
28k, 40k and 484k on the own targets) and slower on the Winter return (by 8k episodes on the common target).

*Revision after verdict review, 2026-09-30 (reviewer M2, M5, C2).*
- **The one beyond-noise dip is thin.** The first Winter entry (−24.5 steps against a threshold of 22.6) is the only
  dip beyond noise, and that threshold is 2 × √2 × the SD of just **two** 200,000-episode windows (195.2 and 183.9 →
  SD 7.99). It is also a 200k-scale spread applied to a 20k-window quantity that swings between ≈ 60 and ≈ 210 steps
  within the same visit (10.6). Clearing a two-number floor by 1.9 steps is close to a coin flip, so **the Winter dip
  cannot carry the "beyond noise" clause on its own**.
- **Recovery in Winter has the same weakness.** The Winter recovery readings (84k vs 196k episodes on the common target;
  36k–40k on the return) are the first time an oscillating curve crosses a line. The D6 "oscillating curve" caveat,
  already applied to R, applies to these readings too.
- **Two dip votes are inside 2 steps.** H-dip has no registered tie rule, so +0.4 (P1 stage 4, unfavourable) and −1.6
  (P3 stage 2, favourable) count as full votes (P3 stage 4, +0.9, is not counted for another reason). Dropping them
  leaves the dip sign unchanged in every sequence, but "favourable dip in every sequence" rests on differences that,
  apart from the first Winter entry, are all inside the noise yardstick.
- **First-entry dips are mostly a head start.** On a first entry the modulated agent starts from a checkpoint that already
  plays the new world better, before any training there (10.11). The first-20k differences above are not adaptation
  differences.

### 10.4 Return visits

Return = (survival over the last 200,000 episodes of the return visit) − the same agent's own reference R;
positive favours the modulator. Interfering training since the previous visit to that world is listed
(5.2, Revision 2a).

| Seq | World returned to | Interfering training | Return ord | Return mod | Diff | Noise thr. | **H-ret vote** | Absolute level on return, ord / mod |
|---|---|---|---|---|---|---|---|---|
| P1 | Danger-A | 1 M ep of Famine | +7.6 | +6.0 | −1.7 | 5.2 | unfavourable (inside noise) | 129.6 / 132.3 |
| P1 | Famine | 1 M ep of Danger-A | +1.9 | +3.1 | +1.2 | 9.6 | favourable (inside noise) | 210.0 / 213.8 |
| P2 | Fog-B | 1 M ep of Danger-A | +2.1 | +6.0 | +4.0 | 5.6 | favourable (inside noise) | 135.1 / 137.2 |
| P2 | Danger-A | 1 M ep of Fog-B | +5.7 | +1.4 | **−4.3** | 4.2 | **unfavourable, beyond noise** | 133.2 / 131.8 |
| P3 | Winter | 1 M ep of Famine | +20.6 | +31.2 | +10.5 | 27.3 | favourable (inside noise) | **215.8 / 205.8** |
| P3 | Famine | **3 M** ep of Winter | +3.2 | +6.0 | +2.9 | 5.2 | favourable (inside noise) | 217.9 / 218.1 |

Tally (R1): P1 1 / 1 → not favourable; P2 1 / 1 → not favourable; P3 2 / 0 → favourable.

The P3 Winter return is favourable on the registered measure (gain over own first visit) but the modulated
agent's gain is measured from its lower first-visit level (174.7 vs 195.2, the D6 caveat); in absolute
survival the ordinary agent is still **10 steps ahead** on the return (215.8 vs 205.8). Revision 2a said
return "needs no companion" because it is already in survival steps; that is true of its units, but it is
still referenced to each agent's own first visit, so the same plateau-level effect that motivated the
companion applies here. Reported, not re-scored.

### 10.5 Forgetting matrix (no training)

Each stage-end checkpoint was played, frozen, for 2,000 episodes (same seeds 0–1999 in every cell) in every
usable world. **Forgetting of world X at stage k** = survival on X at the end of X's latest visit − survival
on X at the end of stage k (positive = forgot); the modulator is favoured when its forgetting is smaller.
95 % CIs from the two cells' standard errors; "beyond noise" = the two agents' CIs do not overlap (5.3).

*Deviations from 5.3, stated:* (1) the evaluation plays the policy **greedily** (most-likely action) while
the training curves are sampled; on its own world every stage-end cell is 2–18 steps (typically 7–12) above
the training-log survival of the same checkpoint (diagonal check, `tmp/20260929_forgetting_diag_check_all.log`,
~~script commit `c6f33eb3`~~ *[corrected 2026-09-30, reviewer L1: `c6f33eb3` is the commit that last changed the
matrix script; the cells themselves record the repository head at evaluation time — `0b9bc250` / `225f9db3` for P1 and
P2, and ten commits made between 17:14 and 21:01 on 2026-09-29 (`711b2abb` … `ba42cb98`) for P3. All descend from `c6f33eb3`, and
none of them changes `continual_forgetting_matrix.py`, `eval_rollout.py` or `src/`]*). Matrix values are therefore used **only** within the matrix and between agents,
never next to training-curve numbers; forgetting is a within-agent difference on one scale, so it stays
comparable between agents. (2) Row 0 (the pre-trained Home checkpoint) is not in the matrix; the first row
is the Forage branch point itself (step 11,000,025 ordinary / 11,000,022 modulated; 5.3's row 1), shared by
the three sequences of an agent. *[Added 2026-09-30, reviewer L1: 5.3 lists row 0; leaving it out is conservative for
the modulator, since the one descriptive Home reading we have favours it (168.6 vs 201.1 after the first Winter visit,
below).]* Stage-end rows are named by the world trained in that stage. Home is not a world of any sequence, so no vote uses it. (3) Seven worlds, not eight (Danger, Fog,
Harsh were dropped; Danger-A and Fog-B added; Nursery included).

**P1 Danger-A ↔ Famine** (worlds of the sequence; forgetting in steps, 95 % CI)

| World | From → to | Interfering episodes | Forgetting ord | Forgetting mod | Diff (mod − ord) | CIs overlap? | **Vote** |
|---|---|---|---|---|---|---|---|
| Forage | Forage end (branch point) → end of stage 2 (Danger-A) | 1.0 M | +108.2 [99.9, 116.4] | +84.8 [77.0, 92.7] | -23.3 | no | favourable, beyond noise |
| Danger-A | end of stage 2 (Danger-A) → end of stage 3 (Famine) | 1.0 M | +14.5 [7.3, 21.7] | +22.4 [15.4, 29.3] | +7.9 | yes | unfavourable |
| Forage | Forage end (branch point) → end of stage 3 (Famine) | 2.0 M | +5.6 [-0.7, 12.0] | +4.9 [-1.3, 11.1] | -0.7 | yes | favourable |
| Famine | end of stage 3 (Famine) → end of stage 4 (Danger-A) | 1.0 M | +56.8 [47.2, 66.4] | +62.2 [52.8, 71.7] | +5.4 | yes | unfavourable |
| Forage | Forage end (branch point) → end of stage 4 (Danger-A) | 3.0 M | +74.8 [66.9, 82.7] | +81.0 [73.2, 88.9] | +6.2 | yes | unfavourable |
| Danger-A | end of stage 4 (Danger-A) → end of stage 5 (Famine) | 1.0 M | +22.5 [15.2, 29.9] | +23.6 [16.4, 30.8] | +1.1 | yes | unfavourable |
| Forage | Forage end (branch point) → end of stage 5 (Famine) | 4.0 M | +5.9 [-0.4, 12.3] | +7.0 [0.7, 13.2] | +1.0 | yes | unfavourable |

Tally (R1, all entries): 2 favourable / 5 unfavourable. A/B worlds only: 0 / 3.

**P2 Fog-B ↔ Danger-A** (worlds of the sequence; forgetting in steps, 95 % CI)

| World | From → to | Interfering episodes | Forgetting ord | Forgetting mod | Diff (mod − ord) | CIs overlap? | **Vote** |
|---|---|---|---|---|---|---|---|
| Forage | Forage end (branch point) → end of stage 2 (Fog-B) | 1.0 M | +62.8 [54.9, 70.7] | +64.6 [56.7, 72.6] | +1.8 | yes | unfavourable |
| Fog-B | end of stage 2 (Fog-B) → end of stage 3 (Danger-A) | 1.0 M | +29.1 [21.6, 36.6] | +26.2 [18.8, 33.6] | -2.9 | yes | favourable |
| Forage | Forage end (branch point) → end of stage 3 (Danger-A) | 2.0 M | +93.1 [85.1, 101.1] | +63.5 [56.0, 71.1] | -29.6 | no | favourable, beyond noise |
| Danger-A | end of stage 3 (Danger-A) → end of stage 4 (Fog-B) | 1.0 M | +17.1 [9.9, 24.3] | +11.9 [4.7, 19.2] | -5.2 | yes | favourable |
| Forage | Forage end (branch point) → end of stage 4 (Fog-B) | 3.0 M | +68.3 [60.2, 76.5] | +56.1 [48.2, 64.0] | -12.2 | yes | favourable |
| Fog-B | end of stage 4 (Fog-B) → end of stage 5 (Danger-A) | 1.0 M | +37.3 [29.9, 44.6] | +28.9 [21.3, 36.4] | -8.4 | yes | favourable |
| Forage | Forage end (branch point) → end of stage 5 (Danger-A) | 4.0 M | +77.7 [69.8, 85.7] | +57.3 [49.8, 64.9] | -20.4 | no | favourable, beyond noise |

Tally (R1, all entries): 6 favourable / 1 unfavourable. A/B worlds only: 3 / 0.

**P3 Winter ↔ Famine** (worlds of the sequence; forgetting in steps, 95 % CI)

| World | From → to | Interfering episodes | Forgetting ord | Forgetting mod | Diff (mod − ord) | CIs overlap? | **Vote** |
|---|---|---|---|---|---|---|---|
| Forage | Forage end (branch point) → end of stage 2 (Winter) | 3.0 M | +174.8 [165.8, 183.7] | +62.7 [54.4, 71.0] | -112.1 | no | favourable, beyond noise |
| Forage | Forage end (branch point) → end of stage 3 (Famine) | 4.0 M | +5.0 [-1.3, 11.2] | +7.6 [1.3, 13.9] | +2.6 | yes | unfavourable |
| Winter | end of stage 2 (Winter) → end of stage 3 (Famine) | 1.0 M | +43.5 [31.8, 55.2] | +40.3 [28.3, 52.3] | -3.2 | yes | favourable |
| Famine | end of stage 3 (Famine) → end of stage 4 (Winter) | 3.0 M | +19.4 [8.9, 29.9] | +18.3 [7.7, 28.9] | -1.1 | yes | favourable |
| Forage | Forage end (branch point) → end of stage 4 (Winter) | 7.0 M | +39.8 [32.1, 47.5] | +33.5 [26.1, 40.9] | -6.3 | yes | favourable |
| Forage | Forage end (branch point) → end of stage 5 (Famine) | 8.0 M | +8.6 [2.1, 15.0] | +4.2 [-2.0, 10.4] | -4.4 | yes | favourable |
| Winter | end of stage 4 (Winter) → end of stage 5 (Famine) | 1.0 M | +49.2 [37.3, 61.2] | +51.4 [39.3, 63.4] | +2.1 | yes | unfavourable |

Tally (R1, all entries): 5 favourable / 2 unfavourable. A/B worlds only: 2 / 1.

*Reading.* On the **alternating worlds** the two agents forget about the same: differences run from −8.4 to +7.9
steps, every pair of CIs overlaps, and the direction differs by sequence (modulator 3 / 0 in P2, ordinary 3 / 0 in P1,
2 / 1 in P3). The large, beyond-noise differences are all on **Forage**, and all favour the modulator: it keeps more of
its foraging skill after the first hard world (P1: loses 85 vs 108 steps; P3: 63 vs 175) and, in P2, after hunters
(64 vs 93 at stage 3; 57 vs 78 at stage 5). Forage is shared by the three sequences and was flagged "too easy to be a
distinct world" (3.6), so these entries are not independent across sequences. *Descriptive, not voted:* Home (not a
world of any sequence) shows the same direction after the first Winter visit (deterministic Home survival 168.6 ordinary
vs 201.1 modulated at the end of stage 2 of P3).

*Revision after verdict review, 2026-09-30 (reviewer M3, M4) — what the Forage result does and does not show.*
- **Not in every sequence without exception.** In P1 the Forage advantage **reverses** at the end of the second Danger-A
  visit (stage 4: +81.0 vs +74.8 forgotten, +6.2 against the modulator, inside noise).
- **Only after some worlds.** The four beyond-noise Forage entries all sit at checkpoints that end a **Winter** or
  **Danger-A** stage (P1 stage 2; P2 stages 3 and 5; P3 stage 2). After Fog-B or Famine stages no Forage entry is beyond
  noise (−12.2 at best, P2 stage 4), and after Famine both agents are back within 9 steps of their Forage level.
- **It dominates the tally.** Forage supplies 4 of the 7 forgetting votes in every sequence, so the forgetting sign
  under R1 is mostly a Forage sign (compare "A/B worlds only" under each table).
- **One shared, capped starting cell.** All three sequences measure Forage forgetting from the **same** branch-point
  checkpoint per agent, and that checkpoint is at the ceiling in Forage (478.8 vs 479.4 steps; 95.6 % of episodes of
  both agents hit the 500-step cap). The drops can be compared, but there is no room to compare baseline Forage
  competence, and the three sequences' Forage entries are not independent.
- **An alternative that is weakened but not excluded.** The agent that specialises *less* to the hard world may simply
  keep more of its generic foraging policy. The training curve fits it in Winter (the modulated agent's last-200k level
  there is lower, 174.7 vs 195.2), but the checkpoints that end the Winter stage do not: played in Winter they are level
  greedy (215.1 vs 213.1) and the modulated one is *ahead* with sampled actions (215.2 vs 204.6, +10.6; 95 % CI of the
  paired difference +3.1 to +18.1, unpaired −1.7 to +22.8). In Danger-A the training-curve levels do not show weaker
  specialisation either (modulated R 126.3 vs 122.0 in P1, 130.4 vs 127.5 in P2). So at the checkpoint where the
  largest Forage gap is measured, the modulated agent kept more foraging skill **without** being worse in the hard
  world. The alternative survives only in the weaker form "the two agents reached equal Winter competence by different
  routes, one of which overwrote less of Forage", which is not separable from "protection" here.
- **Greedy vs sampled (reviewer M4) — checked for the headline cell.** Every value in these tables comes from greedy
  (most-likely-action) play, and the diagonal check verifies each agent's level, not the between-agent gap. ~~The headline
  Forage entry (P3, end of Winter: −112.1) is therefore **greedy only; a sampled-action check of that cell for both
  agents is pending** (`developer`, reviewer M4) and this number should not travel without it.~~ *[Updated 2026-09-30:]*
  the `developer` re-ran the key cells with **sampled** actions for both agents (2,000 episodes each, same seeds;
  `results/analysis/continual_worlds/sampled_check_p3.json`). The gap survives: the end-of-Winter checkpoints played in Forage survive 306.0 (ordinary) vs 419.9
  (modulated) steps, **+113.9 [95 % CI +103.4, +124.5]** sampled against +112.7 greedy; the branch checkpoints tie in
  Forage under both modes (≈ 479). The other P1/P2 Forage entries and all A/B entries remain greedy only.

*Matched times (R4).* In P3 the Famine entry is measured after **3 M** interfering Winter episodes and the two Winter
entries after **1 M** Famine episodes; each is compared between agents only, never across worlds.

### 10.6 Temporal evolution

Survival over training (20,000-episode running mean at fixed offsets after each switch, steps):

| Stage (visit) | Agent | 20k | 50k | 100k | 200k | 500k | 1.0 M | 1.5 M | 2.0 M | 2.5 M | 3.0 M |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 Danger-A (1st) | ord | 31.8 | 61.5 | 86.2 | 109.2 | 120.7 | 122.1 | | | | |
| | mod | 36.3 | 63.5 | 87.8 | 114.0 | 123.9 | 128.8 | | | | |
| P2 Fog-B (1st) | ord | 40.1 | 61.9 | 106.7 | 120.4 | 123.5 | 134.0 | | | | |
| | mod | 45.3 | 82.6 | 117.3 | 123.0 | 130.1 | 131.7 | | | | |
| P3 Winter (1st) | ord | 108.9 | 97.5 | 80.9 | 162.9 | 167.9 | 110.4 | 147.9 | 194.6 | 205.3 | 196.7 |
| | mod | 133.4 | 89.6 | 174.3 | 83.7 | 185.3 | 182.6 | 156.5 | 186.8 | 209.7 | 211.0 |
| P3 Winter (return) | ord | 120.7 | 201.6 | 206.0 | 207.1 | 212.3 | 211.3 | 212.8 | 214.0 | 218.8 | 218.1 |
| | mod | 144.6 | 180.5 | 162.7 | 172.5 | 147.0 | 212.1 | 215.0 | 217.4 | 212.6 | 215.6 |

Trailing 200,000-episode means in Winter (the window the reference R is read from), steps:

| Winter visit | Agent | 0.5 M | 1.0 M | 1.5 M | 2.0 M | 2.5 M | 3.0 M (= R or return level) |
|---|---|---|---|---|---|---|---|
| 1st | ord | 128.1 | 117.4 | 182.5 | 186.8 | 189.6 | 195.2 |
| 1st | mod | 151.5 | 166.1 | 159.8 | 184.2 | 173.0 | 174.0 |
| return | ord | 199.3 | 184.8 | 212.3 | 207.2 | 212.0 | 215.8 |
| return | mod | 197.4 | 211.0 | 197.2 | 198.3 | 199.8 | 206.0 |

What the curves show:
- **Hunter and fog worlds (P1, P2), first entry.** Both agents crash to 30–45 steps (≈ 96 % of deaths in the
  first 20,000 episodes are injuries — the Forage-trained agents walk into hunters) and climb back over
  ≈ 0.2–0.5 M episodes. The modulated curve is above the ordinary one at every offset up to 0.5 M, by 2–5 steps
  in Danger-A and by up to 21 steps (at 50k) in Fog-B; by the end of the visit the two have converged. From the second switch on, the
  alternation between these worlds costs both agents 2–15 % and is recovered within 32,000 episodes.
- **Winter is not a smooth curve for either agent.** Both 20k running means swing between ≈ 60–75 and ≈ 210 steps within
  the 3 M-episode visit (ordinary low 59.4, modulated low 74.6); neither meets failure mode 7.4 (best window above
  0.6 × R). The modulated agent climbed faster early (trailing 200k 151.5 vs 128.1 at 0.5 M) but finished its
  first visit lower (174.0 vs 195.2), with its last 20k window at 211 — so its `R_Winter` sits on an
  oscillating curve, as the D6 caveat warned. On the return both agents start far above their first-entry
  level (121 / 145 vs 109 / 133) and reach ≈ 200 within 50k (ordinary) or after a mid-visit slump
  (modulated, 147 at 0.5 M).
- **Famine** changes little for anyone: every switch into it costs 3–15 % and is recovered within 28,000
  episodes; the two agents' Famine levels differ by ≤ 4 steps throughout.
- Deaths (last 200k): in Winter the modulated agent dies of cold/heat more often on the first visit (38 %
  vs 33 %) and about equally on the return (29 % vs 26 %); in every other world the death split is within
  5 points between agents.

### 10.7 Failure-mode catalog check (section 7)

| # | Triggered? | Note |
|---|---|---|
| 7.1 NaN / explosion | no | all six runs completed |
| 7.2 no dip anywhere | no | first entries dip 24–74 % |
| 7.3 never recovered by both | no | every switch recovered |
| 7.4 one agent collapses | no | in every visit the best 20k window is above the agent's own R (0.6 × R is the trigger) |
| 7.5 late stages learn slower | no sign | return recoveries are at their floor except Winter, which is faster on return for both |
| 7.6 all inside noise | nearly | only one favourable dip (P3 first Winter entry, 24.5 vs threshold 22.6) and one unfavourable return (P2 Danger-A, −4.3 vs 4.2) exceed the training-curve yardstick; forgetting: four favourable entries beyond noise, all on Forage (P1 stage 2; P2 stages 3 and 5; P3 stage 2), none on the alternating worlds |
| 7.9 episodes vs env steps disagree | once in the script's scoring (P3 Winter → Famine return); under 3.7.7 (a) that reading is a tie | |
| 7.11 own vs common disagree | H-dip on one switch per sequence (the returns P1 → Danger-A, P2 → Danger-A, P3 → Famine); H-rec on P2 Fog-B → Danger-A | not "most switches", so the sequence verdicts do not fall back on return + forgetting alone |

### 10.8 Section 2 verdict (primary rule R1)

| Sequence | Dip (fav / unfav / not counted) | Recovery | Return | Forgetting | Favourable measures | Favourable and beyond noise | Meets the per-sequence criterion? |
|---|---|---|---|---|---|---|---|
| P1 Danger-A ↔ Famine | **favourable** (2 / 1 / 1) | **favourable** (2 / 0 / 2 ties) | not favourable (1 / 1) | unfavourable (2 / 5) | 2 of 4 | none | **no** |
| P2 Fog-B ↔ Danger-A | **favourable** (3 / 0 / 1) | **favourable** (1 / 0 / 3) | not favourable (1 / 1) | **favourable** (6 / 1) | 3 of 4 | forgetting — Forage entries only | **yes** |
| P3 Winter ↔ Famine | **favourable** (3 / 0 / 1) | not favourable (1 / 1 / 2 ties) | **favourable** (2 / 0) | **favourable** (5 / 2) | 3 of 4 | dip (first Winter entry, 24.5 vs 22.6); forgetting — Forage after Winter | **yes** |

~~**Section 2 verdict under R1: SUPPORT — 2 of 3 sequences meet the criterion.**~~ *[Struck 2026-09-30 after the
verdict review — the table above is correct, but "SUPPORT" is one of two outcomes the registered rule reaches; see the
revised verdict at the end of this subsection.]* Worded as registered: *one
initialisation pair, three world-pairs*. What carries it: in P2 the only beyond-noise differences are Forage-forgetting
entries; in P3 the first-entry Winter dip (which clears its threshold by 1.9 steps) and Forage forgetting. No
favourable difference on the alternating worlds' returns or forgetting is beyond noise. The predicted shape ("small or
absent on first visits, appears on the returns", section 2) is **not** what happened — the difference is largest on first
entries.

**With and without the Danger-A sequences (3.7.4 item 1).** Danger-A passed the survivable rule for the
modulated agent only, so the verdict is also computed without P1 and P2. That leaves P3 alone, and one
sequence cannot meet "2 of 3": **the without-Danger-A verdict is "not supported" by construction**; P3 on its
own reads 3 of 4 measures favourable with two beyond-noise differences (it meets its per-sequence criterion on its own).

**Revised verdict (revision after verdict review, 2026-09-30): the registered rule is NOT DECISIVE on these data.**
Section 2 has a support clause and a refutation clause. On these data **each of them is reached**, depending on one
question the design answers both ways: *does the foraging world (Forage) — learned before the alternation began — count
as a world of the sequence in the forgetting vote?* §3.3 lists Forage as stage 1 of every sequence, which says yes; §2
names May's forgetting on the **alternating** worlds as the replication target, which says no. Both readings are
registered-consistent; neither was chosen before the data were seen.

| | Forage **counted** in the forgetting vote (R1, R5) | Forage **not counted** (R6, R7) |
|---|---|---|
| P1 Danger-A ↔ Famine | 2 of 4 favourable → mixed | 2 of 4 favourable → mixed (A/B forgetting sums to +14.4 steps **against**) |
| P2 Fog-B ↔ Danger-A | 3 of 4 favourable; beyond noise only via Forage entries → **meets support** | 3 of 4 favourable, but **no favourable difference beyond noise**; its only beyond-noise difference (Danger-A return, −4.3) is **against** → meets the refutation clause |
| P3 Winter ↔ Famine | 3–4 of 4 favourable; beyond noise via the Winter dip and Forage → **meets support** | 3–4 of 4 favourable; beyond noise via the Winter dip alone (M2: a two-window floor, cleared by 1.9 steps) → meets support, thinly |
| **Section 2 outcome** | **support clause met** (P2, P3) | **refutation clause met** (P1, P2) under every combination rule |

(Here "mixed" is read as "fewer than 3 of the 4 measures favourable" and "all inside noise" as "no favourable difference
beyond noise"; that is the reading under which §2's two clauses do not overlap.) If the Winter dip is not allowed to
carry the beyond-noise clause on its own (M2), P3 also drops out when Forage is not counted, and no sequence meets
support. **The hinge is the forgetting entry set, not the combination rule**: R1 and R5 (both with Forage) agree on
support; R6 and R7 (both without) agree on not-supported / refutation; R2 and R3 were never registered-literal (the
script's tie bug and a stricter-than-registered unanimity rule), and R4 is the predicted *shape*, not the rule. The
previous wording "four of five alternatives disagree" overstated the combination-rule fragility and understated this
entry-set hinge. Wording as required: *one initialisation pair, three world-pairs, one seed — registered rule not decisive.*

### 10.9 Sensitivity to the combination rule

Signs per sequence are listed dip / recovery / return / forgetting (+ favourable, − unfavourable, 0 not
favourable either way). "BN" = which favourable measure supplies the beyond-noise clause.

| Rule | How per-switch values become one sign per measure | P1 | P2 | P3 | Section-2 verdict |
|---|---|---|---|---|---|
| **R1 (primary)** | net tally of counted votes; ties as registered in 3.7.7 (a); forgetting over Forage + A + B | + + 0 − → 2, no BN | + + 0 + → 3, BN forgetting (Forage) | + 0 + + → 3, BN dip, forgetting (Forage) | **SUPPORT** (P2, P3) |
| R2 | as R1, but recovery ties as coded in `pilot_readout.py` (exact equality) | + 0 0 − → 1 | + − 0 + → 2 | + + + + → 4, BN dip, forgetting | NOT SUPPORTED (P3 only) |
| R3 | unanimity: a measure is favourable only if no counted vote is unfavourable | 0 + 0 0 → 1 | + + 0 0 → 2 | + 0 + 0 → 2 | NOT SUPPORTED |
| R4 | return visits only (switches into the second visit; forgetting on A / B only) | − 0 0 − → 0 | + 0 0 + → 2 | + − + + → 3, no BN | NOT SUPPORTED |
| R5 | sum of signed effects per reading across the sequence (Rev 2a agreement applied to the sums) | + + − + → 3, BN forgetting (Forage) | + + − + → 3, BN forgetting (Forage) | + + + + → 4, BN dip, forgetting | **SUPPORT** (all three) |
| R6 | as R1, forgetting on the alternating worlds A / B only (Forage excluded) | + + 0 − → 2 | + + 0 + → 3, **no BN** | + 0 + + → 3, BN dip | NOT SUPPORTED (P3 only) |
| R7 *(added 2026-09-30)* | as R5, forgetting on A / B only (Forage excluded) | + + − − → 2 (A/B forgetting sums to **+14.4 against**) | + + − + → 3, **no BN** (its only beyond-noise difference, the Danger-A return −4.3, is against) | + + + + → 4, BN dip only | NOT SUPPORTED (P3 only) |
| R8 *(added 2026-09-30)* | as R1, and a recovery reading whose episode difference is below one 4,000-episode logging interval is also a tie (the second reading 3.7.7 (a)'s parenthetical admits) | + + 0 − → 2 | + + 0 + → 3, BN forgetting (Forage) | + **+** + + → 4 (Winter return: own-reference 36,059 vs 40,050, Δ 3,991 → tie; H-rec becomes 1 / 0 / 3 → favourable), BN dip, forgetting (Forage) | SUPPORT (P2, P3) — no change |

*Revision after verdict review, 2026-09-30.* R7 and R8 are added. R8 changes only P3's recovery sign and no verdict. R7
completes the Forage-excluded pair: with R6 it shows that **no combination rule gives support once Forage is left out of
the forgetting vote**, and that without Forage P1 is mixed and P2 has no favourable difference beyond noise — §2's
refutation clause (10.8, revised verdict). The *Reading* paragraph below (2026-09-29) framed the fragility as a matter
of the combination rule; the entry set is the real hinge. The sentence "The one robust pattern across all six rules is a
favourable dip in every sequence" stands as arithmetic, but per 10.3 (revision) and 10.11 that dip is mostly a head
start plus sub-noise votes.

*Reading.* The two rules that give support (R1, R5) both need the **Forage** forgetting entries for P2's beyond-noise
clause; remove them (R6) and P2 drops out. Scoring the recovery ties as the script does (R2) or requiring unanimity (R3)
also removes the support. Only P3 meets its per-sequence criterion under a majority of the rules (R1, R2, R5, R6). The
one robust pattern across all six rules is a **favourable dip in every sequence except under R3 / R4 for P1**.

*Pre-registered wording check (7.6).* Outside the Forage entries and the first Winter entry, every difference is inside
the noise yardstick; one return (P2 Danger-A, −4.3 vs 4.2) is beyond noise **against** the modulator.

### 10.10 Comparison with the May probe

The May double-return probe ([[NMN_CONTINUAL_DOUBLE_RETURN_PROBE]] §5.5–6.1) found: dips of equal depth
for both agents on the switches back into the hunting world; the modulated agent **107–132 steps ahead** on
the two returns (2× the ordinary agent's survival); forgetting 65–72 % smaller; the difference "lives in
recovery, not in dip depth".

| May's finding | This study (one seed, three world pairs) | Same pattern? |
|---|---|---|
| Returns: modulator +107 / +133 steps | returns differ by −4.3 to +10.5 steps on the registered measure; in absolute level the ordinary agent is ahead on the Winter return (by 10) and on the P2 Danger-A return (by 1.4) | **no** — nothing May-sized; one return beyond noise *against* the modulator |
| Forgetting 65–72 % smaller | on the alternating worlds: −8.4 to +7.9 steps, none beyond noise, direction differs by sequence (P2 favours the modulator 3 / 0, P1 the ordinary agent 3 / 0, P3 2 / 1). On Forage — the first-learned world — the modulated agent keeps 20–112 steps more at one or more checkpoints in every sequence (beyond noise) | **no** on the alternating worlds; a May-like retention effect appears only for the first-learned world |
| Dip depth equal | first-entry dips smaller for the modulator in all three sequences (by 4.5, 5.2 and 24.5 steps of first-20k survival); on return switches the first-20k survival differs by at most 4.2 steps except on the Winter return (+23.9 for the modulator, inside Winter's wide noise) | **no — the opposite emphasis**: the modulator's edge is on first contact with a new world, not on returns |
| Recovery faster | faster on the three first entries (common target: 64k, 36k, 112k episodes sooner); slower on the Winter return (8k later); elsewhere no recovery was needed | partly, and on first entries rather than returns |

So the early read — *the modulator drops less on first entry; returns and recovery are mixed* — holds up on
the full data. May's pattern (equal dip, large return and forgetting advantage) is **not** reproduced. Two
differences in set-up bear on this and are not controlled here: May's agents started each world from
scratch in a 1,500-episode-per-stage probe with a different modulator configuration, while these agents
were pre-trained for 10 M episodes and spend 1–3 M episodes per visit; a return after 1 M episodes of
another world may simply be too easy for either agent to forget much. The from-scratch 3-seed replication of
May under today's settings ([[MAY_DOUBLE_RETURN_REPLICATION]]) is the direct test of that.

*Revision after verdict review, 2026-09-30 (C2):* the "Dip depth" row above reads "first-entry dips smaller for the
modulator"; per 10.11 that is mostly a zero-shot head start, not a smaller drop caused by adapting. May's "dip depth
equal" is compared here with a quantity that mixes starting level and adaptation.

### 10.11 Head start vs adaptation on first entries (EXPLORATORY, post-data — added 2026-09-30)

*Not pre-registered. Added after the verdict review showed that the first-entry advantage was not separated from the
starting checkpoints' zero-shot difference (reviewer C2). Nothing here enters the section-2 vote.*

**The head start.** The forgetting matrix's first row plays the two branch-point checkpoints — frozen, before any
training in the new world, greedy actions, 2,000 episodes each — in every world. The modulated checkpoint survives
longer in **all seven** worlds:

| World | Ordinary | Modulated | Difference |
|---|---|---|---|
| Forage (trained) | 478.8 | 479.4 | +0.6 (both at the 500-step cap in 95.6 % of episodes) |
| Winter | 114.3 | 132.8 | **+18.5** (sampled actions: 117.5 vs 137.3, +19.7 [95 % CI +9.2, +30.2]) |
| Nursery | 199.1 | 212.5 | +13.4 |
| Famine | 161.5 | 166.9 | +5.4 |
| Danger-A | 30.3 | 34.2 | +3.9 |
| Home | 172.6 | 175.8 | +3.2 |
| Fog-B | 38.3 | 40.3 | +2.0 |

Against the first-20k gaps credited to the switch (Winter +24.5, Danger-A +4.5, Fog-B +5.2), the head start accounts for
18.5, 3.9 and 2.0 steps. The Home lead (+3.2 here) is the same one the level-05 factorial flagged as not licensed as a
modulator effect.

**Early learning measured from each agent's own start.** Two post-data measures, each read from the training log
(sampled actions, same scale as the registered measures):
- **Start level** = mean survival in the first logged row after the switch (≈ 4,000 episodes, ≈ 28 training
  iterations — close to, but not strictly, zero-shot). The greedy matrix cell of the checkpoint that ended the previous
  stage is shown next to it for scale.
- **Gain** = first-20k mean survival minus the agent's own start level: how much it improved over its first 20,000
  episodes, whatever it started from.
- **Half-gap time** = episodes until a logged row first closes half of the gap between the agent's own start level and
  the common recovery line (0.9 × the lower reference level). "n/a" = the agent started above the line.

Modulated minus ordinary; positive start and gain differences favour the modulator:

| Seq | First visit into | Start level diff (sampled, first 4k) | Start diff (greedy matrix) | First-20k diff (registered) | **Gain diff** | Half-gap time, ord / mod (k episodes) |
|---|---|---|---|---|---|---|
| P1 | Forage → Danger-A | +5.2 | +3.9 | +4.5 | **−0.6** | 48 / 52 |
| P1 | Danger-A → Famine | +5.2 | +9.2 | +5.9 | **+0.7** | 8 / 8 |
| P2 | Forage → Fog-B | +2.0 | +2.0 | +5.2 | **+3.2** | 56 / 40 |
| P2 | Fog-B → Danger-A | +10.4 | +11.4 | +3.0 | **−7.4** | 8 / n/a |
| P3 | Forage → Winter | +29.4 | +18.5 | +24.5 | **−4.9** | 140 / 68 |
| P3 | Winter → Famine | +14.0 | +41.3 | +1.6 | **−12.4** | 8 / n/a |

What this shows:
- **The modulated agent starts ahead on every first visit** — by 2 to 29 steps in the first 4,000 episodes, by 2 to 41
  steps in greedy play of the checkpoint it arrives with — and its first-20k advantage never exceeds its sampled start
  lead by more than 3.2 steps (Winter: 6.0 steps above the greedy start lead, 4.9 below the sampled one).
- **It does not improve faster from its own start.** Its gain over the first 20,000 episodes is larger in 2 of the 6
  first visits (Fog-B +3.2, Famine in P1 +0.7) and smaller in 4 (−0.6 to −12.4); in Winter both curves are *falling*
  over the first 20k (ordinary +2.6, modulated −2.3 steps of gain).
- **Fog-B is the one first entry where an edge beyond the head start shows**: gain +3.2 and half-gap 16k episodes
  sooner, matching the 50k-offset lead of 21 steps in 10.6 while the start difference is only 2.0.
- **Winter's half-gap time (68k vs 140k) favours the modulator but is not evidence of faster adaptation**: the modulated
  agent had less than half the gap to close (≈ 22 vs ≈ 51 steps to the line), and the reading is the first crossing of a
  single 4,000-episode row on a curve that swings by ±60 steps (M2).

These measures were chosen after the data were seen, on one seed, with no noise yardstick of their own; they can
**undercut** the registered first-entry reading, but not replace it with a new positive claim. What the data support is:
**the modulated branch checkpoint generalises better zero-shot to unseen worlds, by 2–18 steps at the start of the
alternation, for this one pair of agents** — not that the modulated agent adapts faster after a switch.

Source: `tmp/20260930_cw_zeroshot_relative.py` → `tmp/20260930_cw_zeroshot_relative.json` (the registered first-20k
values are reproduced exactly); start row from `results/analysis/continual_worlds/forgetting_p3_{t1none,t16quad}.json`.

## 11. Conclusions

### 11.1 Summary

**Revision after verdict review, 2026-09-30.** Three A-B-A-B sequences, one ordinary and one modulated run each, all six
finished. **The pre-registered rule is not decisive on these data** (10.8, revised verdict). Its support clause is met
(2 of 3 sequences) if the foraging world — learned before the alternation — counts in the forgetting vote; its
refutation clause is met (P1 mixed, P2 without any favourable difference beyond noise and one against) if only the
alternating worlds count, under every combination rule (10.9, R6 and R7). The design supports both entry sets and
neither was fixed in advance; which one applies is the hinge, and it is a decision for the fresh-seed design, not for
this analysis.

What the data show, at the weight they bear:
1. **A zero-shot head start, not faster adaptation.** The modulated branch-point checkpoint survives longer than the
   ordinary one in every unseen world before any training there — by 2–18 steps (Winter 132.8 vs 114.3) — and it
   arrives ahead at every first visit. That head start accounts for most of the first-20k advantage the first write-up
   credited to "coping with the switch" (Winter 18.5 of 24.5 steps; Danger-A 3.9 of 4.5; Fog-B 2.0 of 5.2). Measured
   from each agent's own starting level (exploratory, post-data, 10.11), the modulated agent improves more over its
   first 20,000 episodes in 2 of 6 first visits and less in 4; only Fog-B shows an edge beyond the head start
   (+3.2 steps). The one first-entry dip beyond noise (Winter) clears a two-window yardstick by 1.9 steps on an
   oscillating curve (10.3 revision).
2. **Less loss of foraging skill after cold- and hunter-world stages** (up to 112 steps greedy; the largest cell,
   after the first Winter stage, confirmed with sampled actions at +113.9 steps [+103.4, +124.5]) — at that checkpoint
   the modulated agent is not worse in Winter itself (sampled +10.6), so it is not simply "less specialised". But the
   effect comes from one shared checkpoint at the survival ceiling, reverses once (P1, second hunter-world visit, +6.2
   against), is absent after fog or scarce-food stages, and rests on one starting pair (10.5 revision). This is the
   study's clearest beyond-noise difference, and it is about the world learned **before** the alternation, not the
   alternating worlds the design targeted.
3. **No difference on the alternating worlds.** Returns differ by −4.3 to +10.5 steps (one beyond noise, against the
   modulator); forgetting of the alternating worlds differs by −8.4 to +7.9 steps, all inside noise, with the sign
   varying by sequence. May's 107–132-step return advantage is not reproduced, and the predicted shape ("appears on the
   returns") did not occur.

The cold-world caveat (D6) reproduced: the modulated agent settles lower there over the reference window (174.7 vs 195.2).

*First write-up (2026-09-29), kept for the record, struck:*

~~Three A-B-A-B sequences, one ordinary and one modulated run each, all six finished. **Under the most literal
reading of the pre-registered rule the modulator is supported — in 2 of 3 sequences (fog ↔ hunters, cold ↔ scarce
food) — but only as "one initialisation pair, three world-pairs", on a single seed, and only under that reading**: the
combination of per-switch votes was not fixed in advance, and four of the five other reasonable combination rules give
"not supported" (10.9). What is behind the support is also not what the study was built to find. The modulated agent's
clear advantages are (1) a **smaller drop and faster climb back on first entering a new, harder world**, in every
sequence and largest in the cold world (+24.5 steps in the first 20,000 episodes, just beyond noise), and (2) **better
retention of the foraging world** learned before the alternation (up to 112 steps). On the alternating worlds
themselves — the returns and their forgetting, where May's probe found a 107–132-step advantage — the two agents are
within noise of each other, the sign varies by sequence, and one return is beyond noise against the modulator. The
registered prediction ("small on first visits, appears on the returns") is the reverse of what was seen. The cold-world
caveat (D6) reproduced: the modulated agent settles lower there (174.7 vs 195.2) and is still 10 steps behind in absolute
survival on its return, even though its gain over its own first visit is larger.~~

### 11.2 What this does and does not say

- ~~It says: **for this one pair of starting agents**, across three world pairs, the modulated agent coped
  better with the **first** switch into an unfamiliar harder world (smaller drop, faster climb back), most
  clearly in the cold world.~~ *[Struck 2026-09-30, reviewer C2: this is mostly a zero-shot head start (10.11).]*
- *(Revised 2026-09-30.)* It says: **for this one pair of starting agents**, the modulated branch checkpoint generalises
  better zero-shot to unseen worlds, by 2–18 steps; and after cold- and hunter-world training it kept more of the
  foraging world, with the qualifications in 10.5. It does **not** say that the modulated agent adapts faster after a
  switch, and it does not return a registered verdict either way (10.8).
- It does not say: that the modulator protects what was learned (returns and forgetting are mixed and small),
  or anything about the modulator in general (one initialisation pair, one seed per arm; sequences share
  agents and worlds), or any mechanism.
- It depends on a scoring choice made after the data (10.2 ii) and on correcting the script's tie handling to
  the registered rule (10.2 i); both are visible in 10.9. *(2026-09-30:)* The decisive post-data choice is the
  forgetting entry set (with or without Forage), not the combination rule; the second tie reading (Δ below one logging
  interval, R8) changes no verdict.

### 11.3 Limitations

- **Single-seed first read.** One run per agent per sequence; the noise yardstick is a floor built from
  within-run spread (5.5), not seed-to-seed variance. The three sequences share the same starting weights,
  optimizer state and random key (3.4).
- **One shared start, no yardstick for it (added 2026-09-30, reviewer M1).** §3.4 states that the two agents "differ in
  initialisation, capacity and seed as well as in the modulator". That is not so: both are seed 42, and a parallel study
  verified that same-seed ordinary and modulated agents built by the trainer's recipe start from **bitwise-identical
  main-network weights** (27 of 27 arrays) with a shared environment stream ([[ALGORITHMIC_NULL_TODO]], 2026-09-30;
  checked on the May replication's untrained seed-42 pair — the level-05 runs these agents come from use the same
  recipe but were not separately checked; *confirmed directly 2026-09-30, 27 of 27 bitwise, see the 3.4 correction*). The two pre-trained agents here therefore most likely began their 10 M
  Home episodes from one shared initialisation. The confound is the opposite shape: one shared start, perturbed only by
  the modulator, with no measure of how far *any* perturbation of
  that start would drift in these worlds. The zero-shot head start (10.11) is a property of this one pair and cannot
  be attributed to the modulator without that yardstick. §3.4 belongs to `experiment-designer`, who owns the correction.
- **Two-window yardstick in Winter (M2).** Winter's noise threshold is built from two 200k windows (SD 7.99) and applied
  to a 20k quantity that swings 60–210 steps; Winter recovery is a first crossing on that curve.
- **Forage at ceiling (M3).** 95.6 % of both agents' Forage episodes hit the 500-step cap at the branch point, so
  Forage forgetting has no baseline comparison and all its entries share that one cell.
- **Exploratory worlds.** Danger-A and Fog-B were found by scouting after the registered worlds failed
  (3.7.4); Danger-A passed the survivable rule for the modulated agent only.
- **Winter reference on an oscillating curve (D6).** The modulated agent settled lower in Winter over the
  reference window (174.7 vs 195.2), as in the pilot, but its last 20,000 episodes of that visit read 211.0 (ordinary
  196.7) and its end-of-visit checkpoint plays Winter as well as the ordinary one's (greedy evaluation 215.1 vs 213.1; *added
  2026-09-30:* sampled 215.2 vs 204.6).
  `R_Winter,mod` is therefore a point on a swinging curve; own-reference dip and recovery and the return measure are
  all referenced to it, and the common-reference readings inherit it through `R_common`.
- **Unequal interference in P3 (R4).** The Famine return follows 3 M Winter episodes, the Winter return 1 M
  Famine episodes; forgetting of Famine at the end of stage 4 is after 3 M interfering episodes, forgetting
  of Winter at stages 3 and 5 after 1 M. Compared between agents within a world only.
- **Deterministic evaluation** in the forgetting matrix vs sampled training (10.5). *(2026-09-30:)* the diagonal check
  verifies each agent's level, not the between-agent gap; the −112-step Forage headline was re-checked with sampled
  actions and holds (+113.9 steps, M4); the other matrix entries remain greedy only.
- **Recovery floor.** On most switches both agents were above the recovery line within the first 20,000
  episodes, so H-rec carries information on first entries and the Winter return only.

### 11.4 Related issues (hand-offs, named; nothing changed here)

- **`developer` (via `senior-developer`):** `pilot_readout.py` `_sign` / `_rec_sign` score a recovery tie as
  exact equality; 3.7.7 (a) registers "same logged row". Seven main-run switches are affected; five change
  from a vote to "not counted (tie)". Suggested fix: compare the recovery **row index** (or treat |Δ| below
  the 4,000-episode logging interval as a tie) and add a test with two runs recovering in the same row.
- **`developer`:** the read-out does not compute the 5.5 yardstick (c), the forgetting values of 5.3 or the
  section-2 combination; they are in the analyzer's working scripts (`tmp/20260929_cw_main_analysis.py`,
  `tmp/20260929_cw_main_verdict.py`) and would belong in the read-out if this analysis is repeated on the
  fresh seeds.
- **`experiment-designer`:** before the fresh-seed replication (3.5) runs, pre-register (a) how per-switch
  votes combine into one sign per measure (10.2 ii), (b) the forgetting entry set (with or without Forage),
  (c) a common-reference companion for the return measure (10.4), and (d) whether the forgetting matrix
  plays the policy deterministically or sampled. ~~The manifest statuses of rows 19–24 are stale ("running").~~
  *(Done 2026-09-30: statuses re-checked against the logs, section 4.)*
- *(Added 2026-09-30, after the verdict review; done the same day.)* **`developer`:** the P3 sampled-action re-check
  (reviewer M4) is done — `results/analysis/continual_worlds/sampled_check_p3.json`; Forage gap +113.9 sampled vs +112.7 greedy, zero-shot Winter gap +19.7 vs
  +18.5. The matrix script's policy-mode option was uncommitted in the working tree when this revision was written.
- *(Added 2026-09-30.)* **`experiment-designer`:** correct §3.4's confound statement with a dated note (same seed,
  bitwise-identical main-network initialisation, shared environment stream — worth confirming directly on the two
  level-05 runs; reviewer M1), and add to the fresh-seed
  pre-registration (e) the forgetting entry set as an explicit decision (it decided this verdict), (f) a zero-shot
  baseline for every first entry (the matrix start row, sampled) so that dip and recovery can be read relative to it,
  (g) a dip tie rule, and (h) the cross-seed controls in 11.5.

### 11.5 Recommended next experiments

1. ~~**Fresh seeds (3.5)** — the only route from "one initialisation pair" to a claim; with the scoring
   choices above pre-registered first.~~ *[Revised 2026-09-30, reviewer M1:]* **Fresh seeds with cross-seed
   controls.** 3.5's plan (seeds 43/44, same-seed ordinary/modulated pairs) re-creates the shared start and cannot on
   its own separate the modulator from the starting weights. The replication needs (a) **ordinary-42 vs ordinary-43/44
   in these worlds** as the noise yardstick for how far two starts drift with no modulator involved, and (b)
   **cross-seed pairs** (e.g. ordinary-43 vs modulated-44) alongside the same-seed pairs — as step 11 of the updated
   analysis plan (`tmp/20260930_continual_analysis_plan_v2.md`) already proposes. Scoring choices (11.4) pre-registered
   first.
2. ~~**First-entry effect as its own hypothesis.** The only consistent signal is on first contact with a new
   world; a design that measures many first entries (several unseen worlds from one checkpoint, several
   seeds) tests it directly rather than as a side-effect of an A-B-A-B schedule.~~ *[Revised 2026-09-30, reviewer C2:]*
   **Zero-shot generalisation as its own question.** What this study found on first entries is a zero-shot head start
   of one checkpoint pair. Whether a modulated agent generalises better to unseen worlds is cheap to test without any
   training: play several seeds' pre-trained checkpoints (both agents, and ordinary vs ordinary across seeds as the
   yardstick) in the unseen worlds, sampled and greedy. Only if that difference is seed-stable is an adaptation-speed
   design (many first entries, measured relative to the zero-shot level) worth running.
3. **May replication under today's settings** ([[MAY_DOUBLE_RETURN_REPLICATION]]) — decides whether May's
   return/forgetting advantage was specific to its tiny from-scratch stages.
4. **A trajectory-level read of Winter (D6 "look first", still open)** — why the modulated agent climbs
   faster early yet settles lower, with more cold/heat deaths.

**Pre-launch checklist for any replication of this study (appended 2026-09-30, `experiment-designer`, reviewer M1).**
Same-seed ordinary/modulated pairs share their starting network (3.4 correction), so a replication does not go to
`training-runner` until its design includes:
- [ ] **Noise yardstick:** ordinary-42 against ordinary-43 and ordinary-44, run through the same worlds and schedule,
  so that "how far do two different starts drift with no modulator involved" is measured in these worlds.
- [ ] **Cross-seed pairs:** ordinary-*a* against modulated-*b* with *a* ≠ *b* (for example ordinary-43 vs modulated-44),
  read beside the same-seed pairs, so the modulator effect is not confounded with the shared start.
- [ ] **Shared start verified** for every same-seed pair used, with the 3.4 method (27 of 27 main-network arrays
  bitwise), and the pair's launch code version recorded.
- [ ] The scoring choices of 11.4 (a)–(h) pre-registered before any run is read.

### 11.6 Metrics requested

| Metric | Why now | Where it'd live | Cost |
|---|---|---|---|
| Per-stage modulator activity (FiLM scale / shift mean and spread per site) — repeated from section 8 | the first-entry advantage is the one consistent effect; whether the modulator's output moves at the switch is the first mechanistic question | `train.py` rPPO logging (`mod_info`) | cheap |
| Recovery-row index in the read-out JSON | makes the 3.7.7 (a) tie rule checkable without re-deriving rows | `pilot_readout.py` `recovery` | cheap (analysis only) |

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

## Feedback from plan-reviewer (analysis-verdict gate on §10–§11, commit `d4f6e0cf`, 2026-09-30)

**Verdict: NOT SUPPORTED BY THE EVIDENCE SHOWN — as labelled.** A statement about the argument, not a
claim that the opposite is true; the same data, relabelled, would be SUPPORTED WITH CAVEATS. Full
review with the findings table, the answers to the six questions asked, and the exit condition:
[[plan_continual_worlds_main_verdict]] (`docs/reviews/plan_continual_worlds_main_verdict.md`).

In plain words: the analysis is careful and its caveats are all present, but the label a reader
carries away — "SUPPORT (fragile)" — is not what the registered rule returns. Two Critical points:

1. **The registered rule is not decisive here, and the label was picked from the clause that
   supports.** Whether the foraging world (learned before the alternation) counts as a world of the
   sequence for the forgetting vote is defensible either way — §3.3 lists it as stage 1; §2 names May's
   forgetting on the *alternating* worlds as the replication target. Count it and the support clause
   fires (2 of 3). Leave it out and §2's **refutation** clause fires (P1 mixed under every rule; P2 then
   has one beyond-noise difference and it is *against* the modulator) — under every combination rule,
   including R5-without-Forage, which 10.9 omits (P1 A/B forgetting sums to +14.4; P2 loses its only
   beyond-noise entry). Honest headline: **"registered rule not decisive; hinge = the H-forget entry
   set"**, both clauses at equal weight. Owner: `experiment-analyzer`.
2. **"Coped better with the first switch (smaller drop, faster climb back)" is mostly a head start the
   starting checkpoint already has, and the doc's own data show it.** The forgetting matrix's `start`
   row plays the two branch checkpoints frozen in every world: the modulated one survives longer
   zero-shot in all seven — Winter 114.3 vs 132.8 (+18.5 of the +24.5 first-20k gap), Danger-A +3.9 (of
   +4.5), Fog-B +2.0 (of +5.2). Recovery inherits it (starting 24 steps closer to 0.9·R reaches it sooner
   without adapting faster). What the data support is *"the modulated branch checkpoint generalises
   better zero-shot to unseen worlds, by 2–18 steps, for this one pair"*. Owner: `experiment-analyzer`.

Moderate (details and fixes in the review file): §3.4's "differ in initialisation, capacity and seed"
is wrong — both are seed 42 and start from bitwise-identical main-network weights (parallel study,
verified 2026-09-30), so the shared start is the confound and §11.5's same-seed fresh pairs will not
break it (owner `experiment-designer`, with plan-v2 step 11's cross-seed pairing) · the Winter
beyond-noise threshold is 2·√2·SD of **two** 200k windows (SD 7.99) applied to a 20k quantity that
swings 60–210 within the visit, and Winter recovery is a first crossing on that oscillating curve ·
the Forage-retention headline hides P1's reversal on its second Danger-A visit (+6.2 against), appears
only after Winter/Danger-A stages, rests on 4 of 7 votes per sequence from one shared checkpoint at
ceiling (95.6 % capped), and has an unexcluded alternative (less specialisation to the hard world ⇒ more
generic foraging kept) · greedy-mode matrices: the diagonal check verifies each agent's level, not the
between-agent gap — re-run `P3 end_02_winter × forage` sampled for both agents before −112 travels
(owner `developer`) · the tie rule's parenthetical also admits "Δ < one logging interval = tie" (P3
Winter return own-episodes Δ = 3,991 → P3 H-rec flips favourable; no verdict change; add to 10.9), and
H-dip has no tie rule at all (+0.4 and −1.6-step dips are full votes).

On the six questions asked: (a) R1 is a fair literal reading and R5 agrees with it; R2 is the script's
bug, R3 stricter than registered, R4 the predicted shape — so "4 of 5 alternatives disagree" overstates
the *combination-rule* fragility and understates the *entry-set* hinge. (b) The tie correction is right
and conservative. (c) Forage-in-forgetting is registered-consistent but so is its exclusion; picked, not
invented. (d) Greedy: stated, wrong check for a between-agent claim. (e) §3.4 is wrong in the way that
matters for the next design; the Forage ceiling does not void the drops but voids any baseline
comparison. (f) The first-entry claim does not survive as an adaptation claim.

**Exit condition to SUPPORTED WITH CAVEATS:** relabel (1), reword the first-entry conclusion (2),
correct §3.4. No rerun. **Cost of being wrong:** no compute — a label already in a commit subject and
headed for the cross-study dossier and a PI call, which would steer the seed-43/44 replication toward
a design that cannot separate the modulator from its shared start, and turn a one-pair zero-shot
generalisation difference into a paper claim about continual adaptation.

Reviewed by: plan-reviewer

### Response from experiment-analyzer (revision after verdict review, 2026-09-30)

In plain words: the verdict is relabelled from "support (fragile)" to **"registered rule not decisive"**, and the
first-entry claim is reworded to a zero-shot generalisation difference of this one starting pair. No run was repeated.
Pre-registered text (sections 1–9) is untouched; changed passages in §10–§11 and the two results boxes are struck, not
deleted, and every addition is dated.

| # | What changed | Where |
|---|---|---|
| C1 | Verdict relabelled "registered rule NOT DECISIVE"; support and refutation clauses shown side by side at equal weight; hinge named (the forgetting entry set, Forage in or out); R7 (sum rule without Forage: P1 A/B forgetting +14.4 against, P2 loses its only beyond-noise entry → not supported under every rule) added | top box, §10 box, 10.8 revised verdict, 10.9, 11.1 |
| C2 | First-entry claim reworded to "the modulated branch checkpoint generalises better zero-shot to unseen worlds, by 2–18 steps, for this one pair"; start-row table added; exploratory post-data measures relative to each agent's own start (gain over the first 20k: modulator better in 2 of 6 first visits, worse in 4; only Fog-B shows an edge beyond the head start) | new 10.11, 10.3 note, 10.10 note, 11.1–11.2, 11.5 item 2 |
| M1 | Named in 11.3 and 11.5: shared initialisation (verified on the May seed-42 pair, same recipe; not separately checked on the level-05 runs), no yardstick; replication must add ordinary-42 vs ordinary-43/44 and cross-seed pairs. §3.4 itself left to `experiment-designer` | 11.3, 11.4, 11.5 item 1 |
| M2 | Two-window yardstick and oscillating Winter curve stated for dip and recovery; the Winter dip cannot carry the beyond-noise clause alone | 10.3 note, 10.8, 11.3 |
| M3 | P1 reversal (+6.2), after-which-worlds pattern, Forage = 4 of 7 votes from one shared ceiling-level cell (95.6 % capped), "less specialisation" alternative named — then weakened by the M4 sampled cell (the end-of-Winter modulated checkpoint is not worse in Winter) but not excluded | 10.5 note, 11.1 |
| M4 | Sampled-action re-run by `developer` (`results/analysis/continual_worlds/sampled_check_p3.json`): Forage gap after the first Winter stage +113.9 [+103.4, +124.5] sampled vs +112.7 greedy; zero-shot Winter gap +19.7 [+9.2, +30.2] vs +18.5; end-of-Winter checkpoints in Winter +10.6 sampled, +2.0 greedy — which weakens the "less specialisation" alternative of M3. One pair only | 10.5 note, 10.11 table, top box, §10 box, 11.1, 11.3, 11.4 |
| M5 | R8 row (Δ below one logging interval = tie: P3 recovery flips favourable, no verdict change); sub-2-step dip votes named | 10.9, 10.3 note |
| L1 | Commit citation corrected (cells carry the repository head at evaluation time, all descendants of `c6f33eb3` with no eval-code change); row-0 omission stated as conservative. Manifest statuses of rows 19–24 still stale — `experiment-designer` / `training-runner` own them | 10.5, 11.4 |

Working files: `tmp/20260930_1800_cw_verdict_revision.md`, `tmp/20260930_cw_sensitivity_extra.{py,json}`,
`tmp/20260930_cw_zeroshot_relative.{py,json,log}`.

Signed: experiment-analyzer
