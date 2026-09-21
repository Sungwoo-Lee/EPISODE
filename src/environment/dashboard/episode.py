"""The episode renderer: build the figure once, update artists per step.

PLAIN-LANGUAGE SUMMARY. This is the thing that turns one recorded episode into
one video's worth of frames. It does three things in order, once per episode:
work out which panels this world has (:mod:`.panels`), give each of them a
rectangle that cannot overlap any other (:mod:`.layout`), and build every artist
it will ever need. After that, drawing step 23 is not "build a dashboard" -- it
is "set 400 values on artists that already exist and ask the canvas to compose
them". The production renderer rebuilds its entire figure every frame; this one
does not, and that is the architectural claim the plan's speed gate measures.

WHAT A FRAME IS MADE OF. Three columns under a header: body states and the small
World map on the left, the arena in the middle drawing a **window** of the world
centred on the agent, and the exteroceptive pods on the right. No panel is placed
by hand and no panel is shrunk to make room -- if the budget cannot close, the
packer raises before a single frame exists.

THE WINDOW IS THE CONFIG'S DECISION, AND THE PANEL HOLDING IT IS A FIXED SIZE
(plan Revision 27). ``visualization.local_view_size`` says how many world squares
the grid draws across; the arena's box is always 480 px, so the square size
follows from the window (96 px at 5x5, 48 px at 10x10) and every other panel on
the frame is identical whatever the world. The World map beside it draws the
whole world with a box around the part the grid view is showing.

TWO THINGS THAT LOOK LIKE DETAILS AND ARE LOAD-BEARING.

* **The page colour is painted as a rectangle, and the figure's own background
  stays white.** The pixel audit calls something "ink" when it differs from the
  figure's background, and the arena's neutral ground is only 5-6/255 away from
  the page colour -- so setting the figure's background to the page colour would
  make the ground invisible to the instrument, and "the ground was painted over
  the animals" would stop being detectable (plan section R20.6).
* **Colour scales are fixed once, from the whole episode**, in a pre-pass before
  frame 0. A temperature range recomputed per frame would render a steadily
  cooling world as a world of constant appearance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import cells as C
from . import painters as PN
from . import palette as P
from .layout import Box, Layout, pack
from .panels import (
    LayoutContext,
    check_completeness,
    pack_or_explain,
    present_panels,
)
from .style import DPI, TYPE, register_fonts
from .thermal import scale_from_params

CANVAS_W, CANVAS_H = 1440, 896

#: Which viz entry each vitals row reads. ``build_sensory_viz`` renames
#: interoceptive nociception on the way out, so the mapping is stated once.
VIZ_NAME = {
    "Satiation": "Satiation",
    "Nutrition": "Nutrition",
    "Injury": "Injury",
    "Interoceptive Nociception": "Intero Nociception",
    "Body Temperature": "Body Temperature",
    "Extero Nociception": "Extero Nociception",
    "Thermoception": "Thermoception",
    "Olfaction": "Olfactory",
    "Collision": "Collision",
    "Proprioception": "Proprioception",
    "Visual": "Visual",
    "Location": "LOC",
}


@dataclass
class FrameValues:
    """Everything one frame needs, extracted from one recorded step."""

    step: int
    action_name: str | None
    occupancy: dict
    body_temp: float
    state: object
    viz: dict = field(default_factory=dict)

    def sense(self, name, key):
        entry = self.viz.get(VIZ_NAME.get(name, name))
        if entry is None:
            raise KeyError(
                f"the frame has no sensory entry for {name!r}; the registry says a panel "
                f"for it is present, so either the panel or the adapter is wrong"
            )
        return entry[key]


def occupancy_of(snapshot, params) -> dict:
    """Which entity kinds are in which square -- KINDS, never instances.

    Two predators in one square are one predator token by design (plan section
    R17.5 item 1): no variant in the design round counts occupants, and counting
    would need a badge or a numeral, which is the legend the user's principle
    rules out. Anything measuring this frame must use the same ground truth or it
    will report failures that are not failures.

    Inactive entity slots are parked off the grid each step, so an out-of-bounds
    position is skipped rather than drawn (environment rule R5).
    """
    from ..state import select_by_class

    h, w = int(params.height), int(params.width)
    out: dict[tuple[int, int], set] = {}

    def put(r, c, name):
        if 0 <= r < h and 0 <= c < w:
            out.setdefault((r, c), set()).add(name)

    names = list(params.obstacle_names)
    obs_type = np.asarray(params.obs_type)
    for i, pos in enumerate(np.asarray(snapshot["obs_pos"])):
        put(int(pos[0]), int(pos[1]), names[int(obs_type[i])])

    res_type = np.asarray(params.res_type)
    res_active = np.asarray(snapshot["res_active"])
    for i, pos in enumerate(np.asarray(snapshot["res_pos"])):
        if bool(res_active[i]):
            put(int(pos[0]), int(pos[1]),
                "food" if int(res_type[i]) == 0 else "hiding_predator")

    pred = np.asarray(select_by_class(params, "predator"))
    animal = np.asarray(snapshot["animal_pos"])
    for i in range(animal.shape[0]):
        put(int(animal[i, 0]), int(animal[i, 1]),
            "predator" if bool(pred[i]) else "neutral")

    a = np.asarray(snapshot["agent_pos"])
    put(int(a[0]), int(a[1]), "agent")
    return {k: tuple(sorted(v)) for k, v in out.items()}


class EpisodeRenderer:
    """Build once, update per step.

    ``payload`` is a loaded ``.rec.gz`` episode; ``params`` and ``icon_config``
    come from the recording's ``run_meta.pkl``.
    """

    def __init__(self, params, icon_config, payload, *, title="GridWorld",
                 action_map=None, dpi=DPI, channel_display=None):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        register_fonts()
        self.params = params
        self.payload = payload
        self.icon_config = icon_config
        self.snapshots = payload["snapshots"]
        self.n_steps = len(self.snapshots)
        self.actions = np.asarray(payload["actions"])
        self.action_names = [str(a).upper() for a in (action_map or
                                                      ["Up", "Right", "Down", "Left"])]

        # -- context, completeness, layout -- all before anything is drawn -----
        # `channel_display` is the recording's own names payload, or None for a
        # recording written before channel names existed -- which is the legacy
        # signal the whole labelling path branches on.
        self.channel_display = channel_display
        self.ctx = LayoutContext.from_params(params, channel_display=channel_display)
        check_completeness(self.ctx)
        self.layout: Layout = pack_or_explain(self.ctx)
        self.cell_px = self.layout.cell_px
        self.breakdown = dict(self.ctx.breakdown)

        # -- episode-wide scales, fixed in a pre-pass ------------------------
        field0 = self.snapshots[0].get("thermal_field")
        self.scale = scale_from_params(field0, params) if self.ctx.thermal else None
        self.thermal_field = np.asarray(field0) if self.scale is not None else None
        self.viz_cache: dict[int, dict] = {}
        self.sense_max = self._sense_maxima()

        self.meta = {
            "title": title,
            "width": int(params.width), "height": int(params.height),
            "meta": (f"seed {int(payload.get('seed', 0))}  ·  episode "
                     f"{int(payload.get('episode_index', 0))}  ·  "
                     f"{self.layout.view_cells} × {self.layout.view_cells} view of a "
                     f"{int(params.width)} × {int(params.height)} world"),
            "noise_note": ("Noise off in this episode, so observed = noise-free."
                           if not bool(getattr(params, "perceptual_noise_enabled", False))
                           else "Noise on: the observed and noise-free values differ."),
        }

        # -- the figure ------------------------------------------------------
        self.fig = plt.figure(figsize=(CANVAS_W / dpi, CANVAS_H / dpi), dpi=dpi)
        self.fig.set_layout_engine("none")
        self.fig.set_facecolor(P.FIGURE_FACECOLOR)
        self.canvas = FigureCanvasAgg(self.fig)
        self.renderer = self.canvas.get_renderer()
        bg = self.fig.add_axes([0, 0, 1, 1], label="page")
        bg.axis("off")
        bg._px_w, bg._px_h = CANVAS_W, CANVAS_H
        from matplotlib.patches import Rectangle
        bg.add_patch(Rectangle((0, 0), 1, 1, transform=bg.transAxes, fc=P.CANVAS,
                               lw=0, zorder=0))
        self.bg = bg
        self.updates = []
        self.axes: dict[str, object] = {}
        self._build()

    # -- small services the painters use ----------------------------------
    def fit(self, ax, x, y, role, max_w, numeric=True, **kw):
        return PN.Fit(self, ax, x, y, role, max_w, numeric=numeric, **kw)

    def width(self, s, role) -> float:
        from .style import text as _text
        t = _text(self.bg, 0, 0, s, role)
        w = float(t.get_window_extent(self.renderer).width)
        t.remove()
        return w

    def type_of(self, role):
        return TYPE[role]

    def viz_name(self, name) -> str:
        """The adapter's own key for a breakdown name (Olfaction -> Olfactory)."""
        return VIZ_NAME.get(name, name)

    def has(self, name) -> bool:
        return name in self.breakdown

    def ground_colour(self, r, c):
        if self.thermal_field is None:
            return P.TRACK
        return self.scale.colour(float(self.thermal_field[r, c]))

    def view_origin(self, v) -> tuple[int, int]:
        """The world square at the grid view's top-left corner, this step.

        The window is centred on the agent and CLAMPED to the world's edges, so
        it never shows squares outside the world while any real square is
        available -- the agent walks toward the edge of a stationary frame rather
        than the frame walking off the world. Both the arena and the World map's
        viewport box read this one function, so the box can never disagree with
        what the grid is drawing.
        """
        n = int(self.layout.view_cells)
        a = np.asarray(v.state.agent_pos)
        hh, ww = int(self.params.height), int(self.params.width)
        r0 = max(0, min(hh - n, int(a[0]) - n // 2))
        c0 = max(0, min(ww - n, int(a[1]) - n // 2))
        return r0, c0

    # -- setup -------------------------------------------------------------
    def _sense_maxima(self) -> dict:
        """Per-sense colour/bar maxima, over the WHOLE episode (plan D7.4).

        Smell readings above 1.0 have been observed, so a [0,1] assumption would
        clip a real value and show a full bar for two different numbers. A sense
        whose episode maximum is 0 gets a scale of [0, 1] and a caption rather
        than a division by zero.
        """
        out: dict[str, float] = {}
        for name in ("Olfactory", "Visual"):
            vals = []
            for t in range(self.n_steps):
                entry = self._viz(t).get(name)
                if entry is None:
                    continue
                vals.append(float(np.max(np.asarray(entry["vector"], dtype=float))))
                if entry.get("true_vector") is not None:
                    vals.append(float(np.max(np.asarray(entry["true_vector"], dtype=float))))
            if vals:
                out[name] = max(1e-6, max(vals))
        return out

    def _viz(self, t) -> dict:
        if t not in self.viz_cache:
            from ..sensor import build_sensory_viz

            class _Snap:
                pass

            s = _Snap()
            for k, v in self.snapshots[t].items():
                setattr(s, k, v)
            true_obs = (self.payload["true_obs"][t]
                        if self.payload.get("true_obs") is not None else None)
            entries = build_sensory_viz(self.payload["obs"][t], s, self.params, true_obs)
            self.viz_cache[t] = {e["name"]: e for e in entries}
        return self.viz_cache[t]

    def _panel_card(self, key, label=None):
        """An Axes over one PANEL's box, for a child that is itself a card.

        The sensor band is the only case: it is a placement region holding one
        card per sense rather than one card with a divider, so its children get
        their own surfaces and their own hairlines.
        """
        return self._card(key, label=label, box=self.layout.panels[key])

    def _card(self, key, label=None, box=None):
        box: Box = self.layout.cards[key] if box is None else box
        ax = self.fig.add_axes([box.x / CANVAS_W, 1 - (box.y + box.h) / CANVAS_H,
                                box.w / CANVAS_W, box.h / CANVAS_H],
                               label=label or key)
        ax._px_w, ax._px_h = box.w, box.h
        ax.set_autoscale_on(False)
        ax.set_xlim(0, box.w)
        ax.set_ylim(box.h, 0)
        ax.axis("off")
        self.axes[label or key] = ax
        return ax, box

    def grid_axes(self, card_ax, x, y, w, h, label):
        """A child Axes covering EXACTLY one panel's grid, inside a card.

        The arena is already built this way, and the World map needs it for the
        same reason. The pixel audit's co-occupancy rules derive their square
        grid by dividing the NAMED axes into ``height x width`` squares, which is
        exact only when that axes IS the grid. Pointed at a whole card -- with a
        title above the map and a two-line caption below it -- the derived grid
        is offset from the real one, every square samples card background, and
        the rule can only say "the grid is wrong" instead of answering the
        question it was asked. Giving the map its own axes costs one artist and
        makes the map auditable.

        ``x``/``y``/``w``/``h`` are in the CARD's pixel coordinates (y downward);
        the returned axes carries the same convention over its own extent.
        """
        pos = card_ax.get_position()
        fx = pos.x0 + (x / card_ax._px_w) * pos.width
        fy = pos.y1 - ((y + h) / card_ax._px_h) * pos.height
        ax = self.fig.add_axes([fx, fy, (w / card_ax._px_w) * pos.width,
                                (h / card_ax._px_h) * pos.height], label=label)
        ax._px_w, ax._px_h = w, h
        ax.set_autoscale_on(False)
        ax.axis("off")
        ax.patch.set_visible(False)
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        self.axes[label] = ax
        return ax

    def _vitals_rows(self):
        """One row per body state, with its two columns decided by the breakdown.

        A state the agent cannot sense still gets a row -- the state is real --
        but its observed column reads "not observed" and prints no number. That
        is decided question Q10 and it is what makes defect D10 unreachable.
        """
        card = self.layout.cards["vitals"]
        noise = bool(getattr(self.params, "perceptual_noise_enabled", False))
        recorded = self.payload.get("true_obs") is not None
        rows = []
        spec = [
            ("satiation", "Satiation", "Satiation", "satiation", "max_satiation"),
            ("nutrition", "Nutrition", "Nutrition", "nutrition", "max_nutrition"),
            ("injury", "Injury", "Injury", "injury_level", "max_injury"),
        ]
        placed = self.layout.panels
        for key, label, name, field_name, max_name in spec:
            rk = key if key in placed else f"{key}_hidden"
            if rk not in placed:
                continue
            mx = float(getattr(self.params, max_name))
            rows.append(dict(
                key=rk, label=label, kind="bar", colour=P.STATE,
                y=placed[rk].y - card.y,
                obs=(lambda v, n=name: float(v.sense(n, "intensity")))
                    if self.has(name) else None,
                true=lambda v, f=field_name, mx=mx: float(getattr(v.state, f)) / mx,
            ))
        if "intero_nociception" in placed:
            rows.append(dict(
                key="intero_nociception", label="Interoceptive nociception",
                kind="bar", colour=P.NOCI, y=placed["intero_nociception"].y - card.y,
                obs=lambda v: float(v.sense("Interoceptive Nociception", "intensity")),
                true=((lambda v: float(v.sense("Interoceptive Nociception", "true_intensity")))
                      if (not noise or recorded) else None),
            ))
        if "body_temp" in placed:
            rows.append(dict(
                key="body_temp", label="Body temperature", kind="temp", colour=None,
                y=placed["body_temp"].y - card.y,
                obs=((lambda v: float(v.sense("Body Temperature", "value")))
                     if self.has("Body Temperature") else None),
                true=lambda v: float(v.body_temp),
            ))
        for r in rows:
            r["true_head"] = "Noise-free" if noise else "True"
        return rows

    def _build(self):
        from ..sensor import get_visual_offsets

        cards = self.layout.cards
        if "header" in cards:
            ax, _ = self._card("header")
            PN.build_header(self, ax, ax._px_w, ax._px_h)
        if "vitals" in cards:
            ax, box = self._card("vitals")
            PN.card_frame(ax, box)
            PN.build_vitals(self, ax, box.w, box.h, self._vitals_rows())
        # The World map is TWO axes for the same reason the arena is: the card
        # carries the title and the shared-square caption, and the map GRID gets
        # an axes of its own so a census can be taken against the grid's own
        # extent. See `grid_axes`.
        if "minimap" in cards:
            ax, box = self._card("minimap", label="minimap_card")
            PN.card_frame(ax, box)
            PN.build_minimap(self, ax, box.w, box.h)

        # The arena is TWO axes: the card's chrome, and the grid itself. They are
        # separate so "no numbers inside the grid view" can be checked against
        # the grid's own extent -- the card's title legitimately carries the
        # world's size, and a single axes would make that title a violation.
        ax, box = self._card("arena", label="arena_card")
        PN.card_frame(ax, box)
        PN.build_arena_chrome(self, ax, box.w, box.h)
        grid = self.layout.panels["arena"]
        gax = self.fig.add_axes([grid.x / CANVAS_W, 1 - (grid.y + grid.h) / CANVAS_H,
                                 grid.w / CANVAS_W, grid.h / CANVAS_H], label="arena")
        gax._px_w, gax._px_h = grid.w, grid.h
        gax.set_autoscale_on(False)
        gax.axis("off")
        gax.patch.set_visible(False)
        self.axes["arena"] = gax
        PN.build_arena(self, gax, grid.w, grid.h)

        for key in ("proprioception", "extero_nociception", "collision",
                    "thermoception", "location"):
            if key not in cards:
                continue
            ax, box = self._card(key)
            PN.card_frame(ax, box)
            if key == "proprioception":
                PN.build_proprioception(self, ax, box.w, box.h, self.action_names)
            elif key == "extero_nociception":
                PN.build_intensity(self, ax, box.w, box.h, "Extero nociception",
                                   "Extero Nociception", P.NOCI,
                                   real=self.payload.get("true_obs") is not None)
            elif key == "collision":
                offs = [tuple(o) for o in get_visual_offsets(int(self.ctx.collision_range))]
                PN.build_cross_bars(self, ax, box.w, box.h, "Collision", "Collision",
                                    offs, "CURDL")
            elif key == "thermoception":
                offs = [tuple(o) for o in get_visual_offsets(int(self.ctx.thermal_range))]
                PN.build_thermoception(self, ax, box.w, box.h, offs)
            elif key == "location":
                PN.build_text_row(self, ax, box.w, box.h, "Location", "Location")

        # -- the sensor band: one card per sense, side by side under the arena --
        #
        # Both senses are titled with the breakdown's OWN name -- "Olfaction",
        # "Visual", never "Smell" or "Vision". The pixel audit decides "is this
        # modality drawn?" by reading the rendered panel title against a fixed
        # table of breakdown names, so a prettier synonym makes a panel that is
        # plainly on the screen report as missing.
        band_keys = [k for k in ("olfactory", "visual")
                     if self.layout.parent.get(k) == "band"]
        if band_keys:
            ax, box = self._card("band")
            PN.card_frame(ax, box)
            for key in band_keys:
                child = self.layout.panels[key]
                x0 = child.x - box.x + PN.PAD
                cw = child.w - 2 * PN.PAD
                if key == "olfactory":
                    sense, title = "Olfaction", "Olfaction"
                    rng, stops = int(self.ctx.olfactory_range), P.OLF_STOPS
                else:
                    # "Vision" is the reader's word and the approved design's;
                    # "Visual" is the observation breakdown's key and stays the
                    # `sense` the values are looked up under.
                    sense, title = "Visual", "Vision"
                    rng, stops = int(self.ctx.visual_range), P.VIS_STOPS
                # Built here rather than up front: only the senses actually drawn
                # are ever asked for, so a configured recording with a sense
                # switched off never needs an entry for it.
                display = self.ctx.display_for(sense)
                if rng >= 1:
                    offs = [tuple(o) for o in get_visual_offsets(rng)]
                    PN.build_channel_maps(self, ax, x0, cw, box.h, sense, title,
                                          display, stops, offs, rng)
                else:
                    PN.build_channel_rows(self, ax, x0, cw, box.h, sense, title,
                                          display, stops)
            if len(band_keys) == 2:
                second = self.layout.panels[band_keys[1]]
                PN.band_divider(ax, second.x - box.x - PN.GAP / 2, box.h)

    # -- per step ----------------------------------------------------------
    def values(self, t: int) -> FrameValues:
        snap = self.snapshots[t]

        class _Snap:
            pass

        s = _Snap()
        for k, v in snap.items():
            setattr(s, k, v)
        a = int(self.actions[t]) if t < len(self.actions) else -1
        name = self.action_names[a] if 0 <= a < len(self.action_names) else None
        return FrameValues(
            step=t, action_name=name,
            occupancy=occupancy_of(snap, self.params),
            body_temp=float(snap.get("body_temp", 0.0)),
            state=s, viz=self._viz(t),
        )

    def frame(self, t: int) -> np.ndarray:
        v = self.values(t)
        for upd in self.updates:
            upd(v)
        self.canvas.draw()
        return np.asarray(self.canvas.buffer_rgba())[..., :3].copy()

    def close(self):
        import matplotlib.pyplot as plt
        plt.close(self.fig)

    def layout_signature(self) -> str:
        """A hash of everything a concatenated video must not switch mid-video.

        Panel keys, their kinds, their boxes, whether each has a noise-free slot,
        the arena's square size and the window rule. Two episodes of one run hash
        the same; two different worlds do not.
        """
        payload = {
            "panels": [(p.key, p.kind_for(self.ctx)) for p in present_panels(self.ctx)],
            "cards": {k: (b.x, b.y, b.w, b.h) for k, b in sorted(self.layout.cards.items())},
            "boxes": {k: (b.x, b.y, b.w, b.h) for k, b in sorted(self.layout.panels.items())},
            "real": dict(sorted(self.ctx.real_available.items())),
            "cell_px": self.layout.cell_px,
            "view_cells": self.layout.view_cells,
            "window": "whole_world" if self.layout.step == "whole_world" else self.layout.step,
            "band": self.layout.band,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True,
                                         default=str).encode()).hexdigest()

    # -- convenience --------------------------------------------------------
    @classmethod
    def from_recording(cls, rec_dir, episode: int = 0, **kw) -> "EpisodeRenderer":
        from ...utils.eval_recording import load_episode, load_run_meta

        rec_dir = Path(rec_dir)
        meta = load_run_meta(rec_dir)
        eps = sorted(rec_dir.glob("episode_*.rec.gz"))
        if not eps:
            raise FileNotFoundError(f"no episode_*.rec.gz in {rec_dir}")
        payload = load_episode(eps[episode])
        return cls(meta["params"], meta["icon_config"], payload,
                   title=kw.pop("title", rec_dir.name),
                   action_map=meta.get("action_map"),
                   channel_display=meta.get("channel_display"), **kw)


def render_dashboard_frame(params, icon_config, payload, step: int = 0, **kw):
    """One frame, for the demo, the dream visualiser and the benchmark.

    Builds a one-frame renderer and closes it. Any per-episode scale it needs is
    taken from the payload it was given, exactly as a full episode would.
    """
    r = EpisodeRenderer(params, icon_config, payload, **kw)
    try:
        return r.frame(step)
    finally:
        r.close()
