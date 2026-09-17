"""The panel registry: what exists on a dashboard, and how much room it needs.

PLAIN-LANGUAGE SUMMARY. A dashboard panel is anything drawn on the episode
video: a satiation bar, the arena, the small world map, a sensor pod. This
module is the single list of every panel, and for each one it records three
things -- whether it is on screen for a given world (``present``), the smallest
box it can be drawn in (``min_size``), and which entries of the environment's
own observation list it is responsible for showing (``breakdown_names``). The
packer in :mod:`.layout` consumes those declarations; it knows nothing about
what any panel means.

WHY A REGISTRY AT ALL. Adding a new sense to the environment should be a new row
here and nothing else. A new *visual style* adds a painter in Phase 2. Neither
touches layout. And because every panel declares its minimum rather than being
placed by hand, a world whose panels genuinely cannot fit produces an exception
instead of a video with two labels printed on top of each other.

THE COMPLETENESS RULE. At setup, every name the environment says it is showing
the agent must be owned by exactly one present panel. If the environment grows a
modality and nobody adds a row here, :func:`check_completeness` raises
``ValueError`` naming the orphan -- rather than the modality silently never being
drawn, which is the live bug this replaces (the prior-action panel is built by
the current renderer and then never drawn).

OBSERVED VERSUS HIDDEN (plan section D1.1, user decision Q10 = show). Body states
like nutrition and injury exist in the world even when the agent cannot sense
them. Those rows are still drawn, but the observed column reads ``not observed``
and only the true value is shown. This matters because the current renderer
prints the true value and captions it ``OBS``, which tells a viewer the agent can
sense something it cannot. The rule is encoded structurally: an observed row and
its hidden twin are two registry entries with mutually exclusive ``present``
predicates, so a hidden modality cannot produce an observed row by construction.

NO MATPLOTLIB, AND NO EPISODE DATA. Nothing here imports a drawing library, and
every ``min_size`` takes only a :class:`LayoutContext` -- which is built from
environment params, never from a recorded episode. Two episodes of one run
therefore pack identically. A test inspects the signatures to keep it that way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping

from .layout import (
    CARD_TITLE_H,
    LEFT_W,
    PAD,
    CardDemand,
    Size,
)

# --------------------------------------------------------------------------
# Minimum sizes.
#
# WHERE THESE NUMBERS CAME FROM, AND WHAT HOLDS THEM NOW. The heights marked
# (fig3) were measured off the approved design sketch -- the Figure 3 mock that
# used to live at `renderer_layout_redesign/fig03_proposed_dashboard.py`. That
# file was DELETED on 2026-09-17, when this redesign's page moved to showing the
# real renderer's own output instead of a drawing of it. The citation is kept
# here as history rather than as a pointer: these heights are NOT re-derivable
# from anything in the repository today, and saying so is the honest answer to
# "why is this panel 220 px tall?".
#
# What holds them now is `tests/env/test_dashboard_layout.py`, which pins the
# geometry they produce -- a 10x10 world packs to a 564 x 564 arena card, a
# 476 px right column and a 236 px sensor band -- together with the arithmetic
# re-derived in the plan's Revision 18 (section R18.1). Move one of these and a
# test goes red carrying the worked numbers in its message. That, not the
# deleted mock, is what a reader should follow.
#
# The ones marked (chosen) are for panels the sketch did not draw -- it always
# has a sensor band, so it never draws a spectrum smell pod, a range-0 vision
# pod or the location row. Those three are built from the sketch's own unit
# heights (a 46 px title strip, a 76 px labelled-bar block, a 20 px legend,
# 16 px padding) rather than invented from nothing, and they are the numbers
# most likely to move when a design pass measures real text.
# --------------------------------------------------------------------------
VITAL_ROW_H: int = 76                 # (fig3) one labelled bar row
VITAL_ROW_H_COMPACT: int = 64         # the compact fallback's row
VITALS_CHROME_TOP: int = 92           # (fig3) title strip + the "obs (real)" column header
VITALS_CHROME_BOTTOM: int = 32        # (fig3) 92 + 32 = the sketch's pinned 124
VITALS_CHROME_TOP_COMPACT: int = 80
VITALS_CHROME_BOTTOM_COMPACT: int = 24

MINIMAP_MIN_H: int = 220              # (fig3)
#: The world map grows only until it is as wide as its card; past that the left
#: column simply stays top-aligned rather than stretching a square map.
MINIMAP_MAX_H: int = CARD_TITLE_H + LEFT_W - 2 * PAD + PAD   # 350

PROP_H: int = 104                     # (fig3) six action chips
EXTERO_NOC_H: int = 150               # (fig3)
COLLISION_H: int = 150                # (fig3) shares its row with extero nociception
THERMO_H: int = 230                   # (fig3)
#: The thermoception diamond plus the temperature scale it shares with the body
#: row. This is the demand that sets the right column's 440 px minimum.
THERMO_MIN_W: int = 440

LOCATION_H: int = 46                  # (chosen) one text line plus padding

# A sense read at range 0, drawn as NAMED ROWS in the band rather than as coded
# swatches in the right column (see `LayoutContext.band_senses`). Two columns of
# rows, so the height is set by the taller column: a 64 px title strip, the rows,
# and a footer caption naming the scale.
#     olfaction  5 channels -> 3 rows at 40 px  = 64 + 120 + 16 = 200
#     vision     8 channels -> 4 rows at 38 px  = 64 + 152 + 16 = 232
# Both fit the 236 px the band gets under a 10x10 world's arena.
#
# WHAT THIS REPLACES. `OLF_SPECTRUM_H = 118` and `VISUAL_BARS_H = 134`, which
# sized the two pods for the RIGHT COLUMN, where they were the binding constraint
# in the whole layout: the campfire world put five pods in one column and fitted
# with 16 px to spare out of 816. Moving both senses into the band removes that
# budget entirely -- the right column now carries three pods needing 516 px of
# the 564 it has -- and it is what closes the 564 x 269 px hole the shipped frame
# left under the arena. The row pitches belong to the painter that draws them
# (`painters.CHANNEL_ROW_PITCH`); these two numbers are what LAYOUT needs, and the
# layout tests assert the two agree.
OLF_ROWS_H: int = 200
VISUAL_ROWS_H: int = 232

# The header's demand. The packer gives the header the WHOLE 64 px band rather
# than this, because the band's Axes has to contain the step-progress bar the
# design draws at y = 48; see `layout._pack_once`. The constant remains the
# registry's declared minimum, which is what makes the header a panel like any
# other rather than a special case in the packer.
HEADER_H: int = 32
#: Kept for reference: the band itself now declares no chrome, because its
#: CHILDREN are the cards (see `present_cards`). Each child carries the title
#: strip and padding these two once described.
BAND_CHROME_TOP: int = CARD_TITLE_H
BAND_CHROME_BOTTOM: int = PAD

#: Smallest legible cell in a per-channel diamond map (plan section D7.2).
MAP_CELL_MIN_PX: int = 10
MAP_GAP_PX: int = 8

#: Sentinel returned by :func:`_recording_flag` when an archived recording's
#: params simply do not have the attribute.
class _Absent:
    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "ABSENT"

    def __bool__(self) -> bool:
        return False


ABSENT = _Absent()


def _recording_flag(params, name: str):
    """Read a flag off params that an **archived recording** may predate.

    Returns :data:`ABSENT` -- and only then -- when the attribute does not exist.
    This is absence-shaped backward compatibility for recordings saved before a
    modality existed; it is deliberately **never** used on the live config path,
    where a missing key must raise rather than be papered over. A test pins that
    only this package imports it.
    """
    return getattr(params, name, ABSENT)


@dataclass(frozen=True)
class FontMetrics:
    """Text metrics available to layout.

    Phase 1 has no Matplotlib, so nothing here is measured yet; every pinned
    height above comes from the approved design sketch instead. The type exists
    so Phase 2 can supply real measurements without changing any signature.
    """

    playback_floor_px: int = 14
    caption_floor_px: int = 12


@dataclass(frozen=True)
class LayoutContext:
    """Everything layout is allowed to know. Built from params, never from data.

    Construct it from a real config with :meth:`from_params`, or directly for a
    world no maintained config produces -- which the tests need, because no
    maintained config has both a thermoception card and a sensor band.
    """

    world_w: int
    world_h: int
    local_view_size: int
    breakdown: Mapping[str, int]
    thermal: bool
    intero_noc_enabled: bool
    olfactory_range: int = 0
    visual_range: int = 0
    thermal_range: int = 0
    collision_range: int = 1
    visual_vector_size: int = 8
    olfactory_channels: int = 5
    real_available: Mapping[str, bool] = field(default_factory=dict)
    action_recorded: bool = True
    font: FontMetrics = FontMetrics()

    @classmethod
    def from_params(cls, params, action_recorded: bool = True) -> "LayoutContext":
        """Build a context from resolved environment params.

        ``params`` comes from ``load_env_params(load_env_config(path))`` -- the
        trainer's own loader, which resolves ``extends:``. A raw YAML read would
        report inherited keys as missing.
        """
        # Deferred so importing this package does not pull in JAX.
        from ..sensor import get_observation_breakdown

        breakdown = dict(get_observation_breakdown(params))
        thermal = bool(_recording_flag(params, "thermal_enabled") or False)
        olf_channels = 5
        if "Olfaction" in breakdown:
            cells = _diamond_cells(int(getattr(params, "olfactory_grid_range", 0)))
            olf_channels = max(1, breakdown["Olfaction"] // cells)
        return cls(
            world_w=int(params.width),
            world_h=int(params.height),
            local_view_size=int(params.local_view_size),
            breakdown=breakdown,
            thermal=thermal,
            intero_noc_enabled=bool(
                _recording_flag(params, "interoceptive_nociception_enabled") or False
            ),
            olfactory_range=int(getattr(params, "olfactory_grid_range", 0)),
            visual_range=int(getattr(params, "visual_sensor_range", 0)),
            thermal_range=int(getattr(params, "thermal_grid_range", 0) or 0),
            collision_range=int(getattr(params, "sensor_range", 1)),
            visual_vector_size=int(getattr(params, "visual_vector_size", 8)),
            olfactory_channels=olf_channels,
            real_available=real_available(params),
            action_recorded=action_recorded,
        )

    # -- derived -----------------------------------------------------------
    def observed(self, name: str) -> bool:
        return name in self.breakdown

    def range_of(self, panel_key: str) -> int:
        return {
            "olfactory": self.olfactory_range,
            "visual": self.visual_range,
        }[panel_key]

    @property
    def grid_senses(self) -> tuple[str, ...]:
        """Present senses drawn as diamond maps, i.e. at range >= 1."""
        out = []
        if self.observed("Olfaction") and self.olfactory_range >= 1:
            out.append("olfactory")
        if self.observed("Visual") and self.visual_range >= 1:
            out.append("visual")
        return tuple(out)

    @property
    def has_grid_sense(self) -> bool:
        return bool(self.grid_senses)

    @property
    def band_senses(self) -> tuple[str, ...]:
        """Present senses drawn in the band under the arena -- at ANY range.

        WHY THIS IS NOT ``grid_senses`` (changed 2026-09-17). The band used to
        exist only for a sense that reaches past the agent's own square, so the
        two maintained worlds that read smell AND sight at range 0 -- the
        campfire world among them -- got no band at all and their two sense
        panels were pushed into the right-hand column as narrow code swatches,
        leaving a 564 x 269 px hole under the arena. The approved design puts
        both senses in a full-width band beneath the grid whatever their range;
        what the range decides is the KIND drawn there (``grid_senses`` still
        answers that -- diamond maps at range >= 1, named rows at range 0), not
        whether the band exists.
        """
        out = []
        if self.observed("Olfaction"):
            out.append("olfactory")
        if self.observed("Visual"):
            out.append("visual")
        return tuple(out)

    @property
    def max_sense_range(self) -> int:
        return max(
            self.olfactory_range,
            self.visual_range,
            self.thermal_range,
            self.collision_range,
        )


def _diamond_cells(r: int) -> int:
    """Cells in a diamond of radius ``r``: the environment's own formula."""
    return 2 * r * r + 2 * r + 1


def real_available(params) -> dict[str, bool]:
    """Which modalities can show a noise-free ("REAL") value, decided from params.

    True for a modality when perceptual noise is on **and** that modality's noise
    mode is not "none". Every episode of a run shares these params, so the REAL
    slot is identical across a concatenated video -- which is why this may be
    used in layout at all.

    The noise order carries the same names as the observation breakdown, so the
    mapping is identity rather than a translation table; a name that cannot be
    resolved raises instead of silently reading as "no REAL".
    """
    enabled = _recording_flag(params, "perceptual_noise_enabled")
    order = _recording_flag(params, "noise_modality_order")
    modes = _recording_flag(params, "noise_modes")
    if order is ABSENT or modes is ABSENT:
        return {}
    order = tuple(order)
    if enabled is ABSENT or not bool(enabled):
        return {name: False for name in order}
    out: dict[str, bool] = {}
    for i, name in enumerate(order):
        if i >= len(modes):
            raise ValueError(
                f"perceptual noise names modality {name!r} at index {i}, but "
                f"noise_modes has only {len(modes)} entries; the breakdown-to-"
                f"noise mapping cannot be resolved"
            )
        out[name] = int(modes[i]) != 0
    return out


# --------------------------------------------------------------------------
# The registry
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class PanelSpec:
    """One panel's declaration.

    ``extract`` turns a step's inputs into the values the painter draws. It is
    declared here because it is part of a panel's identity, and filled in by
    Phase 2 -- Phase 1 has no painters, so nothing calls it yet.
    """

    key: str
    group: str                       # 'header'|'vitals'|'world'|'arena'|'extero'
    order: int
    kind: str
    breakdown_names: tuple[str, ...]
    present: Callable[[LayoutContext], bool]
    min_size: Callable[[LayoutContext], Size]
    kind_of: Callable[[LayoutContext], str] | None = None
    extract: Callable | None = None

    def kind_for(self, ctx: LayoutContext) -> str:
        return self.kind_of(ctx) if self.kind_of is not None else self.kind


def _vital_row_size(ctx: LayoutContext) -> Size:
    return Size(0, VITAL_ROW_H)


def _olf_min_size(ctx: LayoutContext) -> Size:
    if ctx.olfactory_range >= 1:
        n = ctx.olfactory_channels
        span = _span(n, ctx.olfactory_range)
        return Size(span, CARD_TITLE_H + _map_h(ctx.olfactory_range) + PAD)
    return Size(0, OLF_ROWS_H)


def _visual_min_size(ctx: LayoutContext) -> Size:
    if ctx.visual_range >= 1:
        n = ctx.visual_vector_size
        span = _span(n, ctx.visual_range)
        return Size(span, CARD_TITLE_H + _map_h(ctx.visual_range) + PAD)
    return Size(0, VISUAL_ROWS_H)


def _span(n_maps: int, r: int) -> int:
    cells = 2 * r + 1
    return n_maps * cells * MAP_CELL_MIN_PX + MAP_GAP_PX * (n_maps - 1)


def _map_h(r: int) -> int:
    return (2 * r + 1) * MAP_CELL_MIN_PX


def _state_exists(ctx: LayoutContext) -> bool:
    """Satiation, nutrition and injury exist in every world this plan covers."""
    return True


PANELS: tuple[PanelSpec, ...] = (
    PanelSpec(
        key="header", group="header", order=0, kind="header",
        breakdown_names=(),
        present=lambda ctx: True,
        min_size=lambda ctx: Size(0, HEADER_H),
    ),
    # -- vitals: an observed row and its hidden twin are mutually exclusive ----
    PanelSpec(
        key="satiation", group="vitals", order=10, kind="vital_row",
        breakdown_names=("Satiation",),
        present=lambda ctx: ctx.observed("Satiation"),
        min_size=_vital_row_size,
    ),
    PanelSpec(
        key="satiation_hidden", group="vitals", order=10, kind="hidden_state",
        breakdown_names=(),
        present=lambda ctx: _state_exists(ctx) and not ctx.observed("Satiation"),
        min_size=_vital_row_size,
    ),
    PanelSpec(
        key="nutrition", group="vitals", order=20, kind="vital_row",
        breakdown_names=("Nutrition",),
        present=lambda ctx: ctx.observed("Nutrition"),
        min_size=_vital_row_size,
    ),
    PanelSpec(
        key="nutrition_hidden", group="vitals", order=20, kind="hidden_state",
        breakdown_names=(),
        present=lambda ctx: _state_exists(ctx) and not ctx.observed("Nutrition"),
        min_size=_vital_row_size,
    ),
    PanelSpec(
        key="injury", group="vitals", order=30, kind="vital_row",
        breakdown_names=("Injury",),
        present=lambda ctx: ctx.observed("Injury"),
        min_size=_vital_row_size,
    ),
    PanelSpec(
        key="injury_hidden", group="vitals", order=30, kind="hidden_state",
        breakdown_names=(),
        present=lambda ctx: _state_exists(ctx) and not ctx.observed("Injury"),
        min_size=_vital_row_size,
    ),
    PanelSpec(
        key="intero_nociception", group="vitals", order=40, kind="vital_row",
        breakdown_names=("Interoceptive Nociception",),
        present=lambda ctx: ctx.intero_noc_enabled,
        min_size=_vital_row_size,
    ),
    # Body temperature is one row with two faces: an observed gauge when the
    # agent senses it, otherwise the same row captioned "not observed", keeping
    # its die-threshold and setpoint marks either way.
    PanelSpec(
        key="body_temp", group="vitals", order=50, kind="temp_row",
        breakdown_names=("Body Temperature",),
        present=lambda ctx: ctx.thermal,
        kind_of=lambda ctx: "temp_row" if ctx.observed("Body Temperature") else "hidden_state",
        min_size=_vital_row_size,
    ),
    # -- world ---------------------------------------------------------------
    PanelSpec(
        key="minimap", group="world", order=60, kind="minimap",
        breakdown_names=(),
        present=lambda ctx: True,
        min_size=lambda ctx: Size(0, MINIMAP_MIN_H),
    ),
    PanelSpec(
        key="location", group="world", order=70, kind="text_row",
        breakdown_names=("Location",),
        present=lambda ctx: ctx.observed("Location"),
        min_size=lambda ctx: Size(0, LOCATION_H),
    ),
    # -- arena ---------------------------------------------------------------
    PanelSpec(
        key="arena", group="arena", order=80, kind="arena",
        breakdown_names=(),
        present=lambda ctx: True,
        min_size=lambda ctx: Size(0, 0),   # the arena's box is fixed by the packer
    ),
    PanelSpec(
        key="action_badge", group="arena", order=90, kind="action_badge",
        breakdown_names=(),
        present=lambda ctx: ctx.action_recorded,
        min_size=lambda ctx: Size(0, 0),   # sits in the arena card's title strip
    ),
    # -- exteroceptive pods --------------------------------------------------
    PanelSpec(
        key="proprioception", group="extero", order=100, kind="action_chips",
        breakdown_names=("Proprioception",),
        present=lambda ctx: ctx.observed("Proprioception"),
        min_size=lambda ctx: Size(0, PROP_H),
    ),
    PanelSpec(
        key="olfactory", group="extero", order=110, kind="spectrum",
        breakdown_names=("Olfaction",),
        present=lambda ctx: ctx.observed("Olfaction"),
        kind_of=lambda ctx: "channel_maps" if ctx.olfactory_range >= 1 else "spectrum",
        min_size=_olf_min_size,
    ),
    PanelSpec(
        key="extero_nociception", group="extero", order=120, kind="intensity",
        breakdown_names=("Extero Nociception",),
        present=lambda ctx: ctx.observed("Extero Nociception"),
        min_size=lambda ctx: Size(0, EXTERO_NOC_H),
    ),
    PanelSpec(
        key="collision", group="extero", order=120, kind="cross_bars",
        breakdown_names=("Collision",),
        present=lambda ctx: ctx.observed("Collision"),
        kind_of=lambda ctx: "cross_bars" if ctx.collision_range <= 1 else "dir_grid",
        min_size=lambda ctx: Size(0, COLLISION_H),
    ),
    PanelSpec(
        key="thermoception", group="extero", order=130, kind="thermal_diamond",
        breakdown_names=("Thermoception",),
        present=lambda ctx: ctx.observed("Thermoception"),
        min_size=lambda ctx: Size(THERMO_MIN_W, THERMO_H),
    ),
    PanelSpec(
        key="visual", group="extero", order=140, kind="cross_bars",
        breakdown_names=("Visual",),
        present=lambda ctx: ctx.observed("Visual"),
        kind_of=lambda ctx: "channel_maps" if ctx.visual_range >= 1 else "cross_bars",
        min_size=_visual_min_size,
    ),
)

_BY_KEY = {p.key: p for p in PANELS}


def present_panels(ctx: LayoutContext) -> tuple[PanelSpec, ...]:
    """Every panel on screen for this world, in draw order."""
    return tuple(sorted((p for p in PANELS if p.present(ctx)), key=lambda p: p.order))


def check_completeness(ctx: LayoutContext) -> None:
    """Every observed modality must be owned by exactly one present panel.

    Raises ``ValueError`` naming the orphan. This is what turns "somebody added a
    sense and nobody drew it" from a silently missing panel into a setup failure.
    """
    present = present_panels(ctx)

    owners: dict[str, list[str]] = {}
    for panel in present:
        for name in panel.breakdown_names:
            if name in ctx.breakdown:
                owners.setdefault(name, []).append(panel.key)

    orphans = sorted(set(ctx.breakdown) - set(owners))
    if orphans:
        raise ValueError(
            f"observation breakdown name(s) {orphans} have no panel in the "
            f"dashboard registry. Add a registry entry in "
            f"src/environment/dashboard/panels.py, or the modality is recorded "
            f"and never drawn."
        )

    doubled = {n: ks for n, ks in owners.items() if len(ks) > 1}
    if doubled:
        raise ValueError(
            f"breakdown name(s) owned by more than one present panel: {doubled}"
        )

    # A panel drawing an OBSERVED value must actually have that value. The
    # hidden-state kinds are exempt by design: the body-temperature row exists
    # whenever the world has a body temperature, and reads "not observed" when
    # the agent cannot sense it -- that is the whole point of Q10 = show.
    for panel in present:
        if panel.kind_for(ctx) == "hidden_state":
            continue
        absent = [n for n in panel.breakdown_names if n not in ctx.breakdown]
        if absent:
            raise ValueError(
                f"panel {panel.key!r} is drawn as observed ({panel.kind_for(ctx)!r}) "
                f"but this world does not observe {absent}"
            )


def present_cards(
    ctx: LayoutContext, band: bool = False, compact: bool = False
) -> tuple[CardDemand, ...]:
    """Turn the present panels into the cards the packer places.

    ``compact`` is the packer's late fallback: it shrinks the *text* rows of the
    merged vitals card. It deliberately does **not** shrink the sensor pods,
    whose minimums come from the geometry they must draw (a thermoception
    diamond cannot be compacted into a smaller diamond and stay legible), so a
    right column that does not fit still raises rather than being squeezed.
    """
    check_completeness(ctx)
    present = present_panels(ctx)
    keys = {p.key for p in present}

    row_h = VITAL_ROW_H_COMPACT if compact else VITAL_ROW_H
    chrome_top = VITALS_CHROME_TOP_COMPACT if compact else VITALS_CHROME_TOP
    chrome_bot = VITALS_CHROME_BOTTOM_COMPACT if compact else VITALS_CHROME_BOTTOM

    cards: list[CardDemand] = []

    if "header" in keys:
        cards.append(
            CardDemand(
                key="header", region="header", order=0, min_h=HEADER_H,
                chrome_top=0, chrome_bottom=0, chrome_side=0,
                flow="single", children=("header",),
            )
        )

    vitals = [p.key for p in present if p.group == "vitals"]
    if vitals:
        cards.append(
            CardDemand(
                key="vitals", region="left", order=10,
                min_h=chrome_top + chrome_bot + row_h * len(vitals),
                chrome_top=chrome_top, chrome_bottom=chrome_bot,
                flow="stack", children=tuple(vitals), child_h=row_h,
            )
        )

    if "minimap" in keys:
        cards.append(
            CardDemand(
                key="minimap", region="left", order=20, min_h=MINIMAP_MIN_H,
                grow=True, max_h=MINIMAP_MAX_H,
                flow="single", children=("minimap",),
            )
        )

    if "location" in keys:
        cards.append(
            CardDemand(
                key="location", region="left", order=30, min_h=LOCATION_H,
                chrome_top=8, chrome_bottom=8,
                flow="single", children=("location",),
            )
        )

    arena_children = ("arena",) + (("action_badge",) if "action_badge" in keys else ())
    cards.append(
        CardDemand(
            key="arena", region="centre", order=40, min_h=0,
            chrome_top=48, chrome_bottom=16, chrome_side=32,
            flow="arena", children=arena_children,
        )
    )

    band_keys = [k for k in ctx.band_senses if k in keys] if band else []

    for key, order, row in (
        ("proprioception", 100, None),
        ("olfactory", 110, None),
        ("extero_nociception", 120, "ec"),
        ("collision", 120, "ec"),
        ("thermoception", 130, None),
        ("visual", 140, None),
    ):
        if key not in keys or key in band_keys:
            continue
        size = _BY_KEY[key].min_size(ctx)
        cards.append(
            CardDemand(
                key=key, region="right", order=order,
                min_h=size.h, min_w=size.w, row=row,
                grow=(key == "thermoception"),
                flow="single", children=(key,),
            )
        )

    if band_keys:
        sizes = [_BY_KEY[k].min_size(ctx) for k in band_keys]
        cards.append(
            CardDemand(
                key="band", region="band", order=200,
                # each sense's min_size already includes its own chrome
                min_h=max(s.h for s in sizes),
                # NO CHROME OF ITS OWN. The band is a placement region, not a
                # drawn card: the approved design shows the two senses as two
                # separate white cards side by side, each with its own title and
                # its own hairline, rather than one wide card with a divider.
                # Giving the band padding here would inset both of them and put
                # their edges 16 px inside the columns everything else lines up
                # with. The CHILDREN carry the cards; `episode.py` draws one
                # frame per child.
                chrome_top=0, chrome_bottom=0, chrome_side=0,
                flow="row", children=tuple(band_keys),
                child_min_w=tuple(s.w for s in sizes),
            )
        )

    return tuple(cards)
