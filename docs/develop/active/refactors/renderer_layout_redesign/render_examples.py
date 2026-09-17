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
    figures/fig09_range1_maps.png            the one world whose smell reaches past its own square
    figures/fig09_range1_maps.data.txt       its used/available/percentage rows
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
from src.environment.dashboard import cells as C  # noqa: E402
from src.environment.dashboard import labels as L  # noqa: E402
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

#: Figure 9's world. Cell M5 is the ONLY maintained world whose smell reaches
#: past the agent's own square (olfaction range 1), so it is the only recording
#: in which the band under the grid holds the per-channel DIAMOND MAPS rather
#: than named rows -- option A, as the renderer now draws it. Every other cell,
#: Figure 3's campfire world included, reads both senses at range 0.
RANGE1 = ("M5", None, "Range-1 smell world · cell M5")

#: The viz key a sense is stored under, against the breakdown name the label
#: table is keyed by. Two namespaces exist in the package already (``labels``
#: names sensor channels, ``cells`` names things in a square); this is only the
#: viz-key-to-breakdown-name bridge, and it lives here rather than growing a
#: third table anywhere.
SENSE_OF_VIZ = {"Olfactory": "Olfaction", "Visual": "Visual"}


def reader_labels(entry):
    """A sense entry's channel labels as a READER's names.

    Plan section R25.4: the short codes (``AN-A``, ``GRS``, ``HPR``) are an
    internal index and had stopped reaching rendered frames, but they still
    reached this page's ``data/episode.json``. They are translated at the
    exporter -- through the package's own ``display_channel``, which RAISES on
    an unknown code, so a new channel cannot leak a code here either.

    THE CODES ARE TAKEN FROM THE PACKAGE, NOT FROM THE ENTRY. The frozen
    adapter labels the hiding predator's visual channel ``DNG``, a name the
    renderer refuses to inherit (``labels.SUPERSEDED_VISUAL_LABELS``), so it
    rebuilds the code list from its own table and so must this exporter --
    translating the adapter's list directly raises on ``DNG``, which is how
    this was found.
    """
    sense = SENSE_OF_VIZ.get(entry.get("name"))
    if sense is None or "labels" not in entry:
        return None
    codes = L.channel_labels(sense, len(entry["labels"]))
    out = []
    for code in codes:
        name, qualifier = L.display_channel(sense, str(code))
        out.append(f"{name} ({qualifier})" if qualifier else name)
    return out


def export_sensor(entry):
    """One sense's per-step payload, JSON-safe and with reader-facing labels."""
    out = {k: plain(val) for k, val in entry.items()}
    named = reader_labels(entry)
    if named is not None:
        out["labels"] = named
    return out


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
            # The READER'S names, not the code's tokens. The renderer's occupancy
            # census is keyed by token -- and one token, ``neutral``, is the rabbit
            # that Figure 8 labels "Rabbit" and the caption above calls "a rabbit".
            # Serialising the token here printed "neutral + rock" in the numbers
            # table beside a caption saying "a rabbit and a rock", with nothing on
            # the page to tell a reader they are the same animal (register F57).
            shared=[[C.display(n) for n in occ]
                    for occ in sorted(list(o) for _, o in v.occupancy.items() if len(o) > 1)],
            sensors=[export_sensor(entry) for entry in v.viz.values()]))
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


# ------------------------------------------------------- the range-1 smell world
def range1_world():
    """One frame of the world whose smell reaches past the agent's own square.

    WHY THIS FIGURE EXISTS. Section 04 of the page chose option A -- one small
    diamond map per channel -- from three MOCKED options, at a time when the
    renderer had no builder for that panel at all. It has one now
    (``painters.build_channel_maps``), and this is the only recorded world that
    exercises it, so the figure turns a chosen option into shipped output.

    WHICH STEP. The step whose smell reading, summed over the whole diamond and
    all five channels, is the largest in the episode -- so the maps are shown
    with something in them rather than at an arbitrary step that might be
    nearly empty. Stated in the figure's own data-used table.
    """
    cell, episode, title = RANGE1
    r, payload, _ = open_cell(cell, episode, title)
    n_eps = len(sorted(f for f in os.listdir(os.path.join(RECORDINGS, cell, cell))
                       if f.endswith(".rec.gz")))
    entry = r.values(0).viz.get("Olfactory")
    if entry is None or int(entry.get("range", 0)) < 1:
        raise SystemExit(
            f"{cell} does not read smell past the agent's own square, so it has no "
            f"channel maps to show; Figure 9 needs a world with olfactory_range >= 1"
        )
    rng, n_ch = int(entry["range"]), int(entry["num_features"])
    totals = [float(np.asarray(r.values(t).viz["Olfactory"]["vector"], dtype=float).sum())
              for t in range(r.n_steps)]
    step = int(np.argmax(totals))
    Image.fromarray(r.frame(step)).save(os.path.join(FIGS, "fig09_range1_maps.png"),
                                        optimize=True)
    n_cells = 2 * rng * rng + 2 * rng + 1
    write_data("fig09_range1_maps", [
        ("steps drawn", 1, r.n_steps,
         f"the one step of this {r.n_steps}-step episode whose smell reading, summed over the "
         f"whole diamond and all {n_ch} channels, is the largest ({max(totals):.2f} against a "
         f"{sum(totals) / len(totals):.2f} episode mean), so the maps are shown carrying signal "
         f"rather than at a step that happens to be nearly empty"),
        ("episodes of this recording drawn", 1, n_eps,
         f"the longer of the {n_eps} ({r.n_steps} steps)"),
        ("smell channels mapped", n_ch, n_ch,
         f"every channel the observation carries, each drawn as its own {n_cells}-square diamond; "
         f"the panel draws one map per channel and hides none"),
        ("recorded worlds with smell past the agent's square", 1, 9,
         "of the nine recorded matrix cells this is the only one configured with olfaction "
         "range 1; the other eight read both senses at range 0 and take the named-rows band"),
    ])
    r.close()
    print(f"range-1 world: {cell} step {step}/{r.n_steps - 1}, olfaction range {rng} "
          f"({n_cells} squares) x {n_ch} channels, diamond sum {max(totals):.2f}")


if __name__ == "__main__":
    # "example", "worlds" and "range1" run one part each -- the example view is 38
    # renders and there is no reason to repeat it while iterating on another figure.
    what = sys.argv[1] if len(sys.argv) > 1 else "both"
    if what not in ("both", "example", "worlds", "range1"):
        raise SystemExit(f"usage: {os.path.basename(__file__)} [both|example|worlds|range1]")
    if what in ("both", "example"):
        example_view()
    if what in ("both", "worlds"):
        three_worlds()
    if what in ("both", "range1"):
        range1_world()
