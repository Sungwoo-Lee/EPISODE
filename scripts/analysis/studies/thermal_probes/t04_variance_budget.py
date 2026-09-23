"""FIGURE 4 - Where the uncertainty actually lives, and why more episodes would not help.

THE QUESTION BEHIND THE FIGURE. Every estimate on this page could be made more precise two ways:
run more evaluation episodes at each saved checkpoint, or average more checkpoints. They cost the
same per unit of compute, so it matters which one the noise is in.

HOW IT IS COMPUTED. Two spreads are put side by side for the same quantity -- the share of an
episode's steps spent on the hiding bush. The first is the standard error of one checkpoint's
estimate: the spread ACROSS the thirty evaluation episodes behind it, divided by the square root of
thirty. That is the error that more episodes would shrink. The second is the standard deviation
ACROSS the last twenty saved checkpoints of the same run: how much the agent's own behaviour moves
from one checkpoint to the next, late in training, with the world held fixed. That is what more
checkpoints, or more training seeds, would shrink.

WHAT IT SHOWS. The second is four to ten times the first. The thirty episodes already pin down what
a given checkpoint does; what moves is the policy itself. So more episodes buy almost nothing, and
the honest unit of replication is the checkpoint -- and beyond it the training seed, of which this
study has exactly one per arm.
"""
import sys, os, glob, gzip, pickle; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, window_profile as W, house
house.apply()

BUSH = (4, 1)
ARM = "fire_away_clean"
SCRATCH = os.path.join(C.arm_dir(ARM), "_scratch")
cells, n_rec = [], 0
for lvl in C.LEVELS:
    for kind in ("control", "modulated"):
        run = f"{lvl}_{kind}"
        for cond, cl in ((C.PRED, "predator"), (C.NONE, "empty")):
            recs = sorted(glob.glob(f"{SCRATCH}/{run}/{cond}/**/episode_*.rec.gz", recursive=True))
            if not recs:
                continue
            # newest checkpoint directory only -- one checkpoint's worth of episodes
            newest = max({os.path.normpath(os.path.join(r, "..", "..", "..")) for r in recs})
            sel = [r for r in recs if r.startswith(newest)][:30] or recs[:30]
            per_ep = []
            for f in sel:
                S = pickle.load(gzip.open(f, "rb"))["snapshots"]
                per_ep.append(100.0 * np.mean(
                    [tuple(np.asarray(s["agent_pos"]).tolist()) == BUSH for s in S]))
            n_rec += len(sel)
            ep = np.asarray(per_ep)
            _, series = W.read_series(C.arm_dir(ARM), run, cond)
            cells.append((f"{C.LEVEL_NAME[lvl]}\n{C.KIND_NAME[kind].replace(chr(110)+chr(101)+chr(117)+chr(114)+chr(111), chr(110)+chr(101)+chr(117)+chr(114)+chr(111)+chr(45)+chr(10))}\n{cl}",
                          ep.std(ddof=1) / np.sqrt(ep.size), series[-20:].std(ddof=1)))

fig, ax = plt.subplots(figsize=(10.0, 5.4))
x = np.arange(len(cells)); w = 0.36
# NEUTRALS, NOT THE SERIES HUES. The first build drew these bars in the house green and orange --
# the same two values the other three figures spend on "plain agent" and "neuromodulated agent",
# so orange meant two different things across the figure set (register F11). Nothing here is an
# agent, so the pair is neutral and separated by lightness plus a hatch.
ax.bar(x - w/2, [c[1] for c in cells], width=w, color=house.TEXT_LIGHT, edgecolor="none",
       label="sampling error of one checkpoint (30 episodes)")
ax.bar(x + w/2, [c[2] for c in cells], width=w, color=house.INK_2, edgecolor="white",
       hatch="///", linewidth=0.0, label="variation between checkpoints (last 20)")
# Four of the eight cells have a sampling error of exactly zero: in the empty world every one of
# the thirty episodes produced the SAME bush occupancy, so thirty episodes leave no residual error
# at all while the policy still moves 1-2.7 pp between checkpoints. That is the argument in its
# strongest form, so it is labelled rather than smoothed away or dropped.
for i, c in enumerate(cells):
    txt = f"x{c[2]/c[1]:.0f}" if c[1] > 0.05 else "all 30 episodes\nidentical"
    ax.annotate(txt, xy=(x[i], max(c[1], c[2]) + 0.7), ha="center", va="bottom",
                fontsize=10, color=house.INK_2)
ax.set_xticks(x); ax.set_xticklabels([c[0] for c in cells], fontsize=10)
ax.set_ylabel("spread in bush occupancy (pp)")
ax.set_ylim(0, 15.5)
ax.set_xlabel("run and probe condition, in the world where the fire sits away from the bush")
ax.set_title("More episodes would not help; the policy is what moves\n"
             "The lighter solid bar is the error 30 episodes leave behind. The darker hatched "
             "bar is how\nmuch the agent itself changes between late checkpoints. The multiplier "
             "above each pair\nis hatched over solid.",
             fontsize=10, color=house.INK_2, loc="left", pad=8)
C.legend_below(ax, ncol=2, offset=-0.40)   # 4-line tick labels + x-label sit above it
C.record_samples("t04_variance_budget", [
    dict(what="recordings read", used=n_rec, total=n_rec,
         note="the newest checkpoint's 30 episodes for each run and condition shown, read "
              "step-by-step rather than from the summary CSV"),
    dict(what="checkpoints for the between-checkpoint spread", used=20, total=50,
         note="the newest 20, matching the window the rest of the page quotes"),
    dict(what="arms represented", used=1, total=4,
         note="one thermal arm is drawn; the ratio is the same order in the other three, and "
              "showing four would repeat the same point")])
fig.subplots_adjust(bottom=0.34)
fig.tight_layout()
C.assert_ticks_dont_collide(ax)
C.assert_no_text_overlap(fig)
C.assert_min_text_px(fig)
house.save(fig, os.path.join(C.FIG, "t04_variance_budget"), column_px=C.COLUMN_PX)
for c in cells:
    r = f"x{c[2]/c[1]:.1f}" if c[1] > 0.05 else "SE=0 (all episodes identical)"
    print(f"{c[0].replace(chr(10),' '):26} SE={c[1]:5.2f}  ckpt sd={c[2]:5.2f}  {r}")
