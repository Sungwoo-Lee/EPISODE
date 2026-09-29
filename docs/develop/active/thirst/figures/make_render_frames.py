"""Mock-up frames for the thirst artifact: a REAL level-05 episode, with a
SYNTHETIC pond and hydration injected, rendered through the real dashboard.

What is real: the world, every entity's position at every step, the agent's
actions, the olfaction/vision/thermal observations.
What is synthetic: the pond's position (one fixed 2x2 block for the whole
episode, as the env will do), the hydration values, `water_max_hydration=200`,
and one "Hydration" observation dimension inserted at THIRST_WATER_PLAN A5's
offset (directly after Body Temperature) carrying hydration/200 (noise off).
NOT recomputed: the smell maps. They are the recording's level-05 smell, with
the level-06 channel LABELS applied.
"""
import copy
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
import src.environment.sensor as S
from src.environment.dashboard import EpisodeRenderer
from src.environment.state import select_by_class
from src.utils.eval_recording import load_episode, load_run_meta

REC = ROOT / "results/JAX_RecurrentPPO/20260921-114858_rppo_basicq2_lvl05_t1none_s42/recordings/10000058"
EPISODE = "episode_000002.rec.gz"
OUT = ROOT / "docs/develop/active/thirst/figures"
MAXH = 200.0
EDGE = 1   # plan D1: edge_margin 1 -- pond rows/cols 1..8 on a 10x10 world

meta = load_run_meta(REC)
params = copy.copy(meta["params"])
object.__setattr__(params, "water_max_hydration", MAXH)
object.__setattr__(params, "water_enabled", True)
payload = load_episode(REC / EPISODE)
snaps = payload["snapshots"]
T = len(snaps)
H, W = int(params.height), int(params.width)
is_pred = np.asarray(select_by_class(params, "predator")).astype(bool)


def blocked(t):
    """Cells no pond may cover: obstacles and active resources (plan: every
    other entity is placed after the pond and never on it)."""
    s = snaps[t]
    cells = {tuple(map(int, p)) for p in np.asarray(s["obs_pos"])}
    act = np.asarray(s["res_active"])
    cells |= {tuple(map(int, p)) for i, p in enumerate(np.asarray(s["res_pos"])) if act[i]}
    return cells


def block(r, c):
    return [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]


def legal(r, c):
    return EDGE <= r and r + 1 <= H - 1 - EDGE and EDGE <= c and c + 1 <= W - 1 - EDGE


# --- (b): a step where a predator is next to the agent, both fit one 2x2 pond ---
fixed_blocked = set().union(*(blocked(t) for t in range(T)))   # never cover any of them, any step
choice = None
for t in range(T):
    a = tuple(map(int, snaps[t]["agent_pos"]))
    for k, p in enumerate(np.asarray(snaps[t]["animal_pos"])):
        if not is_pred[k]:
            continue
        p = tuple(map(int, p))
        if p == a or max(abs(p[0] - a[0]), abs(p[1] - a[1])) != 1:
            continue
        for r in range(min(a[0], p[0]) - 1, max(a[0], p[0]) + 1):
            for c in range(min(a[1], p[1]) - 1, max(a[1], p[1]) + 1):
                cells = block(r, c)
                if legal(r, c) and a in cells and p in cells \
                        and not (set(cells) & fixed_blocked):
                    choice = (t, r, c, a, p)
                    break
            if choice:
                break
        if choice:
            break
    if choice:
        break
if choice is None:
    sys.exit("no step puts a predator next to the agent inside a legal pond block")
tb, pr, pc, a_b, p_b = choice
pond = np.array(block(pr, pc), dtype=np.int32)       # [4, 2], every cell, like D2

# --- (a): a step where the agent is far from that pond ---
def dist_to_pond(t):
    a = np.asarray(snaps[t]["agent_pos"])
    return min(max(abs(int(a[0]) - r), abs(int(a[1]) - c)) for r, c in pond)
ta = max((t for t in range(T) if t != tb), key=lambda t: (dist_to_pond(t) >= 4, -abs(t - tb) * 0, dist_to_pond(t)))
# --- (c): a CLEAN thirst death. The episode's real final step is a predator
# kill (injury 1.00), so using it would show two lethal causes at once. Pick
# instead the latest step with no injury, no predator within one square, and
# the agent at least 3 squares from the pond; the episode is then TRUNCATED
# there so the step counter reads k/k. Both facts are stated in the reply.
def pred_near(t):
    a = np.asarray(snaps[t]['agent_pos'])
    for k, q in enumerate(np.asarray(snaps[t]['animal_pos'])):
        if is_pred[k] and max(abs(int(q[0]) - int(a[0])), abs(int(q[1]) - int(a[1]))) <= 1:
            return True
    return False
clean = [t for t in range(T) if t not in (ta, tb)
         and float(snaps[t]['injury_level']) == 0.0 and not pred_near(t)
         and dist_to_pond(t) >= 3]
if not clean:
    sys.exit('no clean step for a thirst-death frame')
tc = max(clean)

HYD = {ta: 34.0, tb: 104.0, tc: 0.0}   # scripted; stated in the reply

# --- inject into every snapshot (pond is fixed per episode) ---
for t, s in enumerate(snaps):
    s["water_pos"] = pond
    s["hydration"] = float(HYD.get(t, 100.0))

# --- one "Hydration" observation dim, directly after Body Temperature (A5) ---
orig_breakdown = S.get_observation_breakdown


def breakdown_with_hydration(p):
    out = {}
    for k, v in orig_breakdown(p).items():
        out[k] = v
        if k == "Body Temperature":
            out["Hydration"] = 1
    return out


bd = orig_breakdown(params)
offset = 0
for k, v in bd.items():
    offset += v
    if k == "Body Temperature":
        break
obs = np.asarray(payload["obs"], dtype=np.float32)
hcol = np.array([snaps[t]["hydration"] / MAXH for t in range(T)], dtype=np.float32)[:, None]
payload["obs"] = np.concatenate([obs[:, :offset], hcol, obs[:, offset:]], axis=1)
S.get_observation_breakdown = breakdown_with_hydration

# --- level-06 channel labels (smell), per the thirst session ---
names = lambda xs: [{"name": n, "qualifier": q} for n, q in xs]
display = {
    "Olfaction": {"names": names([
        ("Food", "shared with water"), ("Odour A", "predator-leaning"),
        ("Odour B", "neutral-leaning"), ("Bush", ""), ("Odour C", "water-leaning")]),
        "groups": []},
    "Visual": {"names": names([("Visible", "")]), "groups": []},
}

OUT.mkdir(parents=True, exist_ok=True)
r = EpisodeRenderer(params, meta["icon_config"], payload,
                    title="MOCK-UP · synthetic pond + hydration",
                    action_map=meta.get("action_map"), channel_display=display)
try:
    for tag, t, what in (("a", ta, "far_from_pond_low_hydration"),
                         ("b", tb, "drinking_predator_in_pond")):
        path = OUT / f"render_{tag}_{what}.png"
        iio.imwrite(path, r.frame(t))
        a = tuple(map(int, snaps[t]["agent_pos"]))
        print(f"{path.relative_to(ROOT)}  step={t}  agent={a}  "
              f"hydration={snaps[t]['hydration']:.0f}/200  dist_to_pond={dist_to_pond(t)}")
finally:
    r.close()

# --- (c) from a payload TRUNCATED at tc, so the counter reads tc/tc ---
trunc = dict(payload)
trunc['snapshots'] = snaps[:tc + 1]
trunc['obs'] = payload['obs'][:tc + 1]
trunc['actions'] = np.asarray(payload['actions'])[:tc + 1]
trunc['rewards'] = np.asarray(payload['rewards'])[:tc + 1]
rc = EpisodeRenderer(params, meta['icon_config'], trunc,
                     title='MOCK-UP · synthetic pond + hydration',
                     action_map=meta.get('action_map'), channel_display=display)
try:
    path = OUT / 'render_c_hydration_zero_terminal.png'
    iio.imwrite(path, rc.frame(tc))
    a = tuple(map(int, snaps[tc]['agent_pos']))
    print(f"{path.relative_to(ROOT)}  step={tc} (episode truncated here; real end {T-1})  "
          f"agent={a}  hydration={snaps[tc]['hydration']:.0f}/200  "
          f"injury={float(snaps[tc]['injury_level']):.2f}  dist_to_pond={dist_to_pond(tc)}")
finally:
    rc.close()
    S.get_observation_breakdown = orig_breakdown
print(f"pond top-left (array)={pr, pc}  cells={[tuple(x) for x in pond]}  "
      f"frame-b predator at {p_b}, agent at {a_b}  obs width {obs.shape[1]} -> {payload['obs'].shape[1]}")
