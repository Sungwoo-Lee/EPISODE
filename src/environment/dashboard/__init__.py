"""Registry-based episode dashboard renderer (the "V2" of 2026-09-14 onward).

WHAT THIS PACKAGE IS. The new episode-video renderer described by
``docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md``. Its organising
claim is that panels overlapping each other becomes *structurally impossible*
rather than something tuned away by hand: every panel declares the box it needs
(:mod:`panels`), a packer places those boxes (:mod:`layout`), and when the
budget cannot close the packer **raises** instead of quietly shrinking a panel
or letting two boxes share pixels.

Matplotlib's ``constrained_layout`` -- what the production V1 renderer leans on
-- only ever considers ticklabels, axis labels, titles and legends. Text drawn
inside an Axes is invisible to it, which is the root cause of the overlapping
dashboard text this package replaces. Placement is therefore never delegated
back to it.

WHAT IS HERE. The registry, the packer and the channel-label table (Phase 1),
and from Phase 2 the painters, the square composition and the episode renderer.

WHY THE TWO PHASE-2 NAMES ARE EXPORTED LAZILY. ``EpisodeRenderer`` and
``render_dashboard_frame`` are importable from this package -- ``from
src.environment.dashboard import EpisodeRenderer`` works -- but they are resolved
on **first use** through a module-level ``__getattr__`` rather than imported at
the top of this file. The reason is a property Phase 1 pinned with a test: a bare
``import src.environment.dashboard`` must not drag in Matplotlib, because layout
runs once per episode before any figure exists and nothing on the training path
should pay for a drawing library to ask a panel how tall it is. Importing
``episode`` here eagerly would import ``painters``, which imports Matplotlib, and
that test would go red for a reason that has nothing to do with what it protects.

NAMING. "V2" in documents written before 2026-09-14 means the dormant April 2026
subfigures renderer in ``src/environment/renderer_v2.py``, which is frozen and
untouched by this package.
"""

from .labels import channel_labels, olfactory_labels, visual_labels
from .layout import (
    ARENA_CELL_MIN_PX,
    ARENA_CELL_PX,
    Box,
    Layout,
    LayoutOverflowError,
    Size,
    pack,
)
from .panels import (
    ABSENT,
    PANELS,
    FontMetrics,
    LayoutContext,
    PanelSpec,
    check_completeness,
    present_panels,
    real_available,
)

_LAZY = {
    "EpisodeRenderer": ".episode",
    "render_dashboard_frame": ".episode",
    "occupancy_of": ".episode",
}


def __getattr__(name):
    """Resolve the drawing-side exports on first use (see the module docstring)."""
    if name in _LAZY:
        import importlib

        mod = importlib.import_module(_LAZY[name], __name__)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(_LAZY))


__all__ = [
    "ABSENT",
    "EpisodeRenderer",
    "render_dashboard_frame",
    "ARENA_CELL_MIN_PX",
    "ARENA_CELL_PX",
    "Box",
    "FontMetrics",
    "Layout",
    "LayoutContext",
    "LayoutOverflowError",
    "PANELS",
    "PanelSpec",
    "Size",
    "channel_labels",
    "check_completeness",
    "olfactory_labels",
    "pack",
    "present_panels",
    "real_available",
    "visual_labels",
]
