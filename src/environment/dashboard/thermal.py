"""The temperature colour scale, fixed once per episode.

PLAIN-LANGUAGE SUMMARY. In the campfire world every square of the map has a
temperature, and so does the agent's body. This module turns a temperature into
a colour. The single thing it exists to guarantee is that **the same colour means
the same temperature in every frame of an episode** -- so a world that is
steadily cooling looks like it is cooling, instead of looking constant because
the colours quietly re-scaled themselves to whatever each frame contained.

WHY IT IS COPIED RATHER THAN IMPORTED. ``src/environment/renderer.py`` has
thermal helpers, and it is a **frozen** file for the whole of this plan. Its
scale is also a different design: a symmetric red-blue ramp about the setpoint.
The adopted design (plan Revision 9, decided question Q17) is an
*episode-anchored* scale -- near-white at the setpoint, pale across the
survivable body band, and colour deepening only beyond the body limits. The plan
says a helper that needs a behaviour change is **copied** into this package,
never edited in place (section D1.3), so this is that copy, taken from the
approved sketch ``renderer_layout_redesign/dashboard_style.py``.

THE FIVE ANCHORS, in plain words: the coldest square in the episode, the
temperature below which the body dies, the setpoint the body defends, the
temperature above which the body dies, and the hottest square in the episode. An
anchor the episode never reaches is dropped, so the ramp stays monotonic. A
reading outside the episode's range is clamped to the end colour, and callers
draw an outline round it (decided question Q15, "clamp and outline") rather than
raising.
"""

from __future__ import annotations

import numpy as np
from matplotlib.colors import FuncNorm, LinearSegmentedColormap, to_rgb

from .palette import (
    TEMP_COLD,
    TEMP_COOL,
    TEMP_HOT,
    TEMP_HOT_MID,
    TEMP_NEUTRAL,
    TEMP_WARM,
)

#: How the legend strip's width is shared: each half of the survivable band
#: against each tail beyond a body limit. Copied from the sketch.
BAND_WEIGHT, OUTER_WEIGHT = 1.0, 1.25


def _mix(c1, c2, t: float):
    t = min(1.0, max(0.0, float(t)))
    return tuple(np.array(to_rgb(c1)) * (1 - t) + np.array(to_rgb(c2)) * t)


class TemperatureScale:
    """One colour scale for one episode.

    ``field`` is the episode's recorded thermal field, ``low`` / ``high`` the two
    body death limits and ``setpoint`` the temperature the body defends.
    """

    def __init__(self, field, low, high, setpoint):
        f = np.asarray(field, dtype=float)
        if f.size == 0:
            raise ValueError("TemperatureScale needs the episode's thermal field")
        if not low < setpoint < high:
            raise ValueError(
                f"the body limits must bracket the setpoint: {low} < {setpoint} < {high}"
            )
        vmin, vmax = float(f.min()), float(f.max())
        if vmax <= vmin:
            # A uniform field (e.g. the thermal-neutral test scenes: air 0 C everywhere, no
            # campfire) is valid; give the scale a 1-degree margin either side so it still draws.
            vmin, vmax = vmin - 1.0, vmax + 1.0
        self.vmin, self.vmax = vmin, vmax
        self.low, self.high, self.sp = float(low), float(high), float(setpoint)

        cand = [("episode min", vmin), ("lower body limit", self.low),
                ("setpoint", self.sp), ("upper body limit", self.high),
                ("episode max", vmax)]
        anchors = [(n, v) for n, v in cand
                   if n.startswith("episode") or vmin < v < vmax]
        xs = [v for _, v in anchors]
        pos = [0.0]
        for x0, x1 in zip(xs, xs[1:]):
            if x1 <= self.low or x0 >= self.high:
                w = OUTER_WEIGHT
            else:
                half = (self.sp - self.low) if x1 <= self.sp else (self.high - self.sp)
                w = BAND_WEIGHT * (x1 - x0) / half
            pos.append(pos[-1] + w)
        pos = [q / pos[-1] for q in pos]
        stops = [(q, self.ref_colour(v)) for q, v in zip(pos, xs)]
        if vmax > self.high:
            q0 = pos[xs.index(self.high)]
            stops.insert(-1, ((q0 + 1.0) / 2, TEMP_HOT_MID))
        self.X, self.Y = np.array(xs), np.array(pos)
        self.cmap = LinearSegmentedColormap.from_list("temperature", stops)
        self.norm = FuncNorm(
            (lambda v: np.interp(v, self.X, self.Y),
             lambda y: np.interp(y, self.Y, self.X)),
            vmin=vmin, vmax=vmax,
        )
        self.anchors = anchors
        self.n_cells = int(f.size)

    # -- reading ------------------------------------------------------------
    def ref_colour(self, v: float):
        """The anchor colour at one temperature, before the ramp is built."""
        if v <= self.low:
            return (_mix(TEMP_COOL, TEMP_COLD, (self.low - v) / (self.low - self.vmin))
                    if self.vmin < self.low else TEMP_COOL)
        if v <= self.sp:
            return _mix(TEMP_NEUTRAL, TEMP_COOL, (self.sp - v) / (self.sp - self.low))
        if v <= self.high:
            return _mix(TEMP_NEUTRAL, TEMP_WARM, (v - self.sp) / (self.high - self.sp))
        return (TEMP_HOT if v >= self.vmax
                else _mix(TEMP_WARM, TEMP_HOT, (v - self.high) / (self.vmax - self.high)))

    def pos(self, v: float) -> float:
        """Where a temperature sits along the legend strip, in 0..1 (clamped)."""
        return float(np.interp(v, self.X, self.Y))

    def colour(self, v: float):
        return self.cmap(self.pos(v))

    def out_of_range(self, v: float) -> bool:
        """True when the value was clamped -- the caller outlines it (Q15)."""
        return bool(v < self.vmin - 1e-9 or v > self.vmax + 1e-9)


def scale_from_params(field, params) -> TemperatureScale | None:
    """Build the episode's scale, or ``None`` when the world has no temperature.

    ``min_temperature`` / ``max_temperature`` are the body's death limits and
    ``temperature_setpoint`` the value it defends -- read from the resolved
    params, never guessed.
    """
    if field is None:
        return None
    f = np.asarray(field)
    if f.size == 0:
        return None
    return TemperatureScale(
        f,
        float(params.min_temperature),
        float(params.max_temperature),
        float(params.temperature_setpoint),
    )
