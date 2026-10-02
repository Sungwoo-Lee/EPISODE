"""Dashboard frames for the thirst artifact, from REAL level-06 recordings.

Everything in these frames is the environment's own output: the pond's position,
hydration, the smell maps (including the pond's odour), vision, temperature, and
the cause of death. There is no trained level-06 agent yet, so the episodes are
driven by the project's fixture recorder with a SEEDED RANDOM POLICY -- the agent's
movements are not learned behaviour, and the frames say so in their title.

The recordings are regenerated, not stored (they live under gitignored tmp/). Two
batches, because a random walker rarely stands in the pond with a predator beside it
and is not dying, so frame (b) needs the larger pool:

    python scripts/eval/make_render_fixture_recordings.py --cells W1 \\
        --episodes 80 --max-steps 300 --seed 11 \\
        --out tmp/20260930_thirst_real/recordings --no-report
    python scripts/eval/make_render_fixture_recordings.py --cells W1 \\
        --episodes 320 --max-steps 300 --seed 23 \\
        --out tmp/20260930_thirst_real/recordings_more --no-report

This script then SEARCHES those episodes for three real moments and renders them:
  (a) the agent far from the pond with low hydration,
  (b) the agent standing in the pond with a predator next to it,
  (c) an episode that ENDED because hydration reached zero (a real thirst death).
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import matplotlib
matplotlib.use("Agg")
import numpy as np

ROOT = Path(__file__).resolve().parents[5]   # docs/develop/active/thirst/figures/ -> repo
sys.path.insert(0, str(ROOT))

import imageio.v2 as iio
from src.environment.dashboard import EpisodeRenderer
from src.environment.state import select_by_class
from src.utils.eval_recording import load_episode, load_run_meta

RECS = [ROOT / "tmp/20260930_thirst_real/recordings/W1/W1",
        ROOT / "tmp/20260930_thirst_real/recordings_more/W1/W1"]
OUT = Path(__file__).resolve().parent
MAX_STEPS = 300
for REC in RECS:
    if not REC.is_dir():
        sys.exit(f"recordings missing at {REC}; regenerate them with the commands in this "
                 f"script's docstring (they are gitignored and not stored)")

meta = load_run_meta(RECS[0])
params = meta["params"]
assert params.water_enabled, "W1 must be the water world (level 06)"
MAXH = float(params.water_max_hydration)
is_pred = np.asarray(select_by_class(params, "predator")).astype(bool)
eps = [e for REC in RECS for e in sorted(REC.glob("episode_*.rec.gz"))]


def cheb(a, b):
    return max(abs(int(a[0]) - int(b[0])), abs(int(a[1]) - int(b[1])))


def pond_of(s):
    return [tuple(map(int, p)) for p in np.asarray(s["water_pos"])]


best = {"a": None, "b": None, "c": None}
for ep in eps:
    pay = load_episode(ep)
    snaps = pay["snapshots"]
    T = len(snaps)
    for t, s in enumerate(snaps):
        a = tuple(map(int, s["agent_pos"]))
        pond = pond_of(s)
        h = float(s["hydration"]) / MAXH
        d = min(cheb(a, p) for p in pond)
        preds = [tuple(map(int, q)) for k, q in enumerate(np.asarray(s["animal_pos"])) if is_pred[k]]
        # (a) far from water and THIRSTY, but clearly alive: not the last step, injury
        # not lethal, hydration low but off the zero boundary. Ranking by "thirstiest"
        # drove an earlier version onto hydration 0.0 one step before death -- a death
        # frame, not a thirsty one -- so aim at ~15% of the maximum instead.
        inj_a = float(s["injury_level"]) / float(params.max_injury)
        if d >= 4 and 0.08 < h < 0.3 and inj_a < 0.5 and t < T - 1:
            key = (abs(h - 0.15),)
            if best["a"] is None or key < best["a"][0]:
                best["a"] = (key, ep, t)
        # (b) standing in the pond, a predator within one square (both in the pond is
        # best). Drinking, not dying: never the episode's last step, injury not
        # lethal, and hydration clear of BOTH death boundaries -- death sits at 0 AND
        # at the maximum, so a full reading here would be an over-drinking death. An
        # earlier version ranked higher hydration as better and picked exactly that.
        inj = float(s["injury_level"]) / float(params.max_injury)
        if a in pond and t < T - 1 and inj < 0.5 and 0.05 < h < 0.95:
            near = [q for q in preds if cheb(q, a) <= 1]
            if near:
                key = (-sum(q in pond for q in near), abs(h - 0.5))
                if best["b"] is None or key < best["b"][0]:
                    best["b"] = (key, ep, t)
    # (c) the episode ENDED (not cut at the step cap) with hydration at zero, and its
    # injury clearly NOT lethal, so the frame shows one cause of death, not two.
    # Injury is on a 0..max_injury scale (100 here), NOT 0..1 -- an earlier version
    # compared the raw value against 1.0 and rejected every real thirst death.
    last = snaps[-1]
    inj = float(last["injury_level"]) / float(params.max_injury)
    if T < MAX_STEPS and float(last["hydration"]) <= 1e-6 and inj < 0.5:
        key = (inj, -T)                      # least injured, then the longest
        if best["c"] is None or key < best["c"][0]:
            best["c"] = (key, ep, T - 1)

missing = [k for k, v in best.items() if v is None]
if missing:
    sys.exit(f"no real moment found for frame(s) {missing}; record more episodes")

names = {"a": "render_a_far_from_pond_low_hydration",
         "b": "render_b_drinking_predator_in_pond",
         "c": "render_c_hydration_zero_terminal"}
for tag in ("a", "b", "c"):
    _key, ep, t = best[tag]
    pay = load_episode(ep)
    r = EpisodeRenderer(params, meta["icon_config"], pay,
                        title="Level 06 · random policy (no trained agent yet)",
                        action_map=meta.get("action_map"),
                        channel_display=meta.get("channel_display"))
    try:
        path = OUT / f"{names[tag]}.png"
        iio.imwrite(path, r.frame(t))
    finally:
        r.close()
    s = pay["snapshots"][t]
    a = tuple(map(int, s["agent_pos"]))
    print(f"{path.relative_to(ROOT)}  {ep.parent.parent.parent.name}/{ep.name} step {t}/{len(pay['snapshots']) - 1}  "
          f"agent={a}  pond={pond_of(s)[0]}+  hydration={float(s['hydration']):.1f}/{MAXH:.0f}  "
          f"injury={float(s['injury_level']):.1f}/{float(params.max_injury):.0f}  "
          f"start hydration={float(pay['snapshots'][0]['hydration']):.1f}")
