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

WHAT IS HERE AT PHASE 1. The registry, the packer and the channel-label table
only. **Nothing in this package imports Matplotlib**, and there are no painters
yet -- a Phase-1 import must not cause any drawing. ``EpisodeRenderer`` and
``render_dashboard_frame`` arrive with ``episode.py`` in Phase 2, at which point
they join the exports below (the plan's File Changes row for this file names
them; they cannot be exported before the module that defines them exists).

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

__all__ = [
    "ABSENT",
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
