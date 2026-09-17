"""The page's example views, drawn by the REAL renderer from REAL recordings.

WHAT THIS REPLACES, AND WHY. Until 2026-09-17 Figures 3 and 4 were drawn by
``fig03_proposed_dashboard.py`` -- a *mock* that imitated the proposed layout
because, when the page was built, the renderer did not exist yet. It does now
(``src/environment/dashboard/``), so a mock's picture of it would be a second
implementation of one design, free to drift from the shipped one. That is plan
finding #56's failure mode: two parts of one system disagreeing, with the reader
building from the stale one. This script therefore **imports the renderer and
asks it for frames**. Nothing here draws a panel.

WHAT IT WRITES (all under this folder)

    figures/fig03_rendered_dashboard.png     the still shown before the scrubber loads
    figures/fig03_rendered_dashboard.data.txt   its used/available/percentage rows
    figures/fig03_frames/step_NNN.png        one PNG per recorded step (the scrubber)
    figures/fig04_three_worlds.png           one frame from each of three worlds, stacked
    figures/fig04_three_worlds.data.txt      its used/available/percentage rows
    data/episode.json                        the numbers table beside the scrubber

WHY THE NUMBERS AND THE FRAMES COME OUT OF ONE RUN. ``data/episode.json`` is
read by the page's numbers table and by ``build_page.py``'s ``{{FACT:...}}``
tokens. It is written here, from the same ``EpisodeRenderer`` that drew the
frames, using that renderer's own ``values(t)`` -- so the number the table shows
for step 32 is the number the frame for step 32 was drawn from. A separate
exporter stepping the environment again could disagree with the frames, which is
the class of defect this whole page is about.

WHY THESE FIGURES HAVE NO SVG OR PDF. They are the renderer's own raster output,
exactly like Figures 1 and 2, and for the same reason: the renderer's look is the
subject, so redrawing it in the house figure style would show something else.
``build_page.py`` requires vector siblings only of the figures that ARE drawn in
the house style (Figures 5-8).

WHY THESE RECORDINGS. They are the plan's own verification matrix, written by
``scripts/eval/make_render_fixture_recordings.py`` through the production
recorder -- the same ``run_meta.pkl`` + ``episode_*.rec.gz`` pair the video path
reads. No world is stepped here and no policy is run.

Run (from anywhere)
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        docs/develop/active/refactors/renderer_layout_redesign/render_examples.py
"""
import json
import os
import sys
from pathlib import Path

# CPU only, before anything imports JAX: this draws pictures and must never take a GPU.
os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from src.environment.dashboard import EpisodeRenderer  # noqa: E402
from src.utils.eval_recording import load_episode, load_run_meta  # noqa: E402

FIGS = os.path.join(HERE, "figures")
DATA = os.path.join(HERE, "data")
RECORDINGS = os.path.join(ROOT, "results", "render_audit", "recordings")

#: The example episode. Cell M4 is the maintained campfire temperature world;
#: episode index 1 is the longer of its two recordings (75 steps against 24).
EXAMPLE = ("M4", 1, "Campfire world · cell M4")

#: The still shown before the scrubber loads. Step 32 is chosen, not arbitrary:
#: it is the frame the plan's co-occupancy work used (§CP2.8), because it carries
#: TWO shared squares -- an agent standing on food, and a rabbit on a rock -- so
#: the still shows the one thing the redesign exists to fix.
REP_STEP = 32

#: The scrubber holds every ``STRIDE``-th step rather than every step, and this is
#: a PAGE-SIZE decision with a measured reason. The platform rejects an artifact
#: over 16 MB; 75 frames of 1440 x 896 build a 19.65 MB page. The two ways to fit
#: were fewer frames or smaller ones, and smaller was rejected twice over: the
#: viewer advertises "actual size" and the caption states 1440 x 896, so shrinking
#: the pixels would make the page lie about itself, while palette-quantising them
#: (measured: 4.45 MB, a 9.29 MB page) shifts pixels by up to 80/255 INSIDE the
#: grid view, where a square's colour is its temperature -- i.e. it corrupts data
#: to save bytes. Dropping every second step costs only temporal resolution, keeps
#: every remaining pixel exact, and the figure's own data-used table states it.
#: Step 0, the last step and REP_STEP all survive an even stride.
STRIDE = 2

#: Figure 4's three worlds: the same renderer, three different sense sets, three
#: real recordings. Chosen so each row removes or adds something visible.
#: ``None`` for the episode means "the longest one in this recording" -- a fixed
#: index picked a 9-step episode for two of the three cells, so every panel would
#: have shown a frame a few steps after the start.
WORLDS = [
    ("M4", None, "Campfire world · cell M4"),
    ("M1x", None, "Default world, no interoceptive nociception · cell M1x"),
    ("M6", None, "Default world with the location sensor · cell M6"),
]


def plain(x):
    """JSON-safe: numpy scalars and arrays become Python numbers and lists."""
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        return x.item()
    if hasattr(x, "tolist") and hasattr(x, "shape"):   # a jax array
        return np.asarray(x).tolist()
    return x


def open_cell(cell, episode, title):
    """An EpisodeRenderer over one matrix cell's recording, plus its payload."""
    rec_dir = os.path.join(RECORDINGS, cell, cell)
    if not os.path.exists(os.path.join(rec_dir, "run_meta.pkl")):
        raise SystemExit(
            f"no recording at {os.path.relpath(rec_dir, ROOT)}. Regenerate the matrix with "
            f"scripts/eval/make_render_fixture_recordings.py --cells {cell}"
        )
    meta = load_run_meta(Path(rec_dir))
    eps = sorted(f for f in os.listdir(rec_dir) if f.endswith(".rec.gz"))
    if episode is None:
        lengths = [len(load_episode(Path(rec_dir) / e)["snapshots"]) for e in eps]
        episode = int(np.argmax(lengths))
    payload = load_episode(Path(rec_dir) / eps[episode])
    r = EpisodeRenderer(meta["params"], meta["icon_config"], payload, title=title,
                        action_map=meta.get("action_map"))
    return r, payload, meta


def write_data(stem, rows):
    """The used / available / percentage rows, emitted by this script (guide §11)."""
    with open(os.path.join(FIGS, f"{stem}.data.txt"), "w") as fh:
        for what, used, total, note in rows:
            fh.write(f"{what}\t{int(used)}\t{int(total)}\t{note}\n")


# ---------------------------------------------------------------- the example view
def example_view():
    cell, episode, title = EXAMPLE
    r, payload, meta = open_cell(cell, episode, title)
    n_eps = len(sorted(f for f in os.listdir(os.path.join(RECORDINGS, cell, cell))
                       if f.endswith(".rec.gz")))
    params = r.params
    frames_dir = os.path.join(FIGS, "fig03_frames")
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):                 # a shorter episode must not leave stale frames
        if f.endswith(".png"):
            os.remove(os.path.join(frames_dir, f))

    # Every STRIDE-th step, with the episode's LAST step guaranteed present so that
    # "the last recorded step" on the page is really the last recorded step.
    drawn = list(range(0, r.n_steps, STRIDE))
    if drawn[-1] != r.n_steps - 1:
        drawn.append(r.n_steps - 1)
    if REP_STEP not in drawn:
        raise SystemExit(
            f"the still's step {REP_STEP} is not among the {len(drawn)} steps drawn at stride "
            f"{STRIDE}; the scrubber could not open on it"
        )

    steps = []
    for t in drawn:
        img = r.frame(t)
        Image.fromarray(img).save(os.path.join(frames_dir, f"step_{t:03d}.png"), optimize=True)
        if t == REP_STEP:
            Image.fromarray(img).save(os.path.join(FIGS, "fig03_rendered_dashboard.png"),
                                      optimize=True)
        v = r.values(t)
        a = int(payload["actions"][t]) if t < len(payload["actions"]) else -1
        steps.append(dict(
            t=t, action=a, agent=plain(np.asarray(v.state.agent_pos)),
            satiation=float(v.state.satiation), nutrition=float(v.state.nutrition),
            injury=float(v.state.injury_level), body_temp=float(v.body_temp),
            shared=sorted(list(occ) for sq, occ in v.occupancy.items() if len(occ) > 1),
            sensors=[{k: plain(val) for k, val in entry.items()}
                     for entry in v.viz.values()]))
    if REP_STEP >= r.n_steps:
        raise SystemExit(f"REP_STEP {REP_STEP} is past the episode's last step {r.n_steps - 1}")

    field = np.asarray(r.thermal_field) if r.thermal_field is not None else np.zeros((1, 1))
    out = dict(
        meta=dict(
            cell=cell, recording=os.path.relpath(os.path.join(RECORDINGS, cell, cell), ROOT),
            title=title, episode_index=int(payload.get("episode_index", 0)),
            episodes_in_recording=n_eps, seed=int(payload.get("seed", 0)),
            renderer="src/environment/dashboard", rep_step=REP_STEP,
            rep_index=drawn.index(REP_STEP), frame_stride=STRIDE,
            total_steps=int(r.n_steps), steps_drawn=len(drawn),
            frame_width=int(img.shape[1]), frame_height=int(img.shape[0]),
            cell_px=int(r.cell_px), view_cells=int(r.layout.view_cells),
            height=int(params.height), width=int(params.width),
            action_names=list(r.action_names),
            max_satiation=float(params.max_satiation),
            max_nutrition=float(params.max_nutrition),
            max_injury=float(params.max_injury),
            min_temperature=float(params.min_temperature),
            max_temperature=float(params.max_temperature),
            temperature_setpoint=float(params.temperature_setpoint),
            thermal_field=plain(field),
            clim=[float(r.scale.vmin), float(r.scale.vmax)] if r.scale else [0.0, 1.0],
            noise=bool(getattr(params, "perceptual_noise_enabled", False)),
            true_obs_recorded=payload.get("true_obs") is not None,
            layout_signature=r.layout_signature(),
        ),
        steps=steps)
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "episode.json"), "w") as fh:
        json.dump(out, fh)

    n_shared = sum(1 for s in steps if s["shared"])
    write_data("fig03_rendered_dashboard", [
        ("environment steps in the scrubber", len(drawn), r.n_steps,
         f"one step in {STRIDE}, first to last, each drawn by src/environment/dashboard from the "
         f"saved recording. Every pixel is exact; temporal resolution was spent instead of image "
         f"quality so the page fits under its 16 MB publishing ceiling"),
        ("episodes of this recording drawn", 1, n_eps,
         f"the longer of the {n_eps} ({r.n_steps} steps); the other is shorter and shows less behaviour"),
        ("drawn steps in which a square is shared", n_shared, len(drawn),
         "drawn steps where at least one square holds more than one occupant -- the case the "
         "redesign exists to draw correctly"),
    ])
    r.close()
    print(f"example view: {cell} ep{episode}, {len(drawn)} frames drawn of {r.n_steps} steps "
          f"(stride {STRIDE}), still at step {REP_STEP} (index {drawn.index(REP_STEP)}), "
          f"{n_shared} drawn steps with a shared square")
    return len(drawn)


# ------------------------------------------------------------------ three worlds
def three_worlds():
    """One frame from each of three real worlds, stacked, unretouched."""
    gap, rows, notes = 16, [], []
    for cell, episode, title in WORLDS:
        r, payload, _ = open_cell(cell, episode, title)
        step = min(REP_STEP, r.n_steps - 1)
        rows.append(r.frame(step))
        notes.append(f"{cell} step {step}/{r.n_steps - 1}")
        r.close()
    w = max(f.shape[1] for f in rows)
    h = sum(f.shape[0] for f in rows) + gap * (len(rows) - 1)
    sheet = np.full((h, w, 3), 255, dtype=np.uint8)
    y = 0
    for f in rows:
        sheet[y:y + f.shape[0], :f.shape[1]] = f
        y += f.shape[0] + gap
    Image.fromarray(sheet).save(os.path.join(FIGS, "fig04_three_worlds.png"), optimize=True)
    write_data("fig04_three_worlds", [
        ("worlds drawn", len(WORLDS), 9,
         "three of the nine recorded matrix cells, chosen because each changes which panels are "
         "present; the other six differ in ways the layout does not have to re-pack"),
        ("frames drawn per world", 1, 1,
         "one step per world (" + ", ".join(notes) + "); the layout is fixed for a whole episode, "
         "so a second step of the same world would re-pack identically"),
    ])
    print("three worlds: " + ", ".join(notes))


if __name__ == "__main__":
    # "example" and "worlds" run one half each -- the example view is 75 renders and
    # there is no reason to repeat it while iterating on the other figure.
    what = sys.argv[1] if len(sys.argv) > 1 else "both"
    if what not in ("both", "example", "worlds"):
        raise SystemExit(f"usage: {os.path.basename(__file__)} [both|example|worlds]")
    if what in ("both", "example"):
        example_view()
    if what in ("both", "worlds"):
        three_worlds()
