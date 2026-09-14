#!/usr/bin/env python3
"""FIGURE 11 - idea D: parallel sessions claim shared resources, and claims expire.

QUESTION IT ANSWERS. Several Claude sessions work in this repository at once, and they collide over
things only one can use at a time. The figure draws those collisions as a graph with sessions on one
side and resources on the other, and a claim as an edge that carries a lease.

WHAT IS IN IT. Three sessions (blue) and four resources (grey). Solid edges are claims held; the
dashed grey edge is a session waiting for a claim another session holds (grey, not orange: orange
means "work sent back" in Figure 6's legend). The resources are real
ones that have collided here: a GPU on node 102 (double-booked 2026-08-04), the git index
(index.lock contention described in CLAUDE.md), the format-defect register (held with another
session's uncommitted edits when this page was built, 2026-09-14), and CLAUDE.md itself (edited by
parallel sessions with no locking). Which session holds what in the drawing is invented.

HOW IT IS COMPUTED. Nothing is computed; hand-placed inches on a 10.5 x 4.6 inch canvas. Resources
are ordered so that no two claim edges cross, and each label sits beside the middle of its own edge.
"""
import math

import _diagram as D
import house

SESSIONS = {"A": (1.4, 3.55, "Session A", "renderer plan"),
            "B": (1.4, 2.25, "Session B", "tutorial page"),
            "C": (1.4, 0.95, "Session C", "training launch")}
RESOURCES = {"register": (9.0, 3.75, "format register"),
             "git": (9.0, 2.35, "git index"),
             "claude": (9.0, 1.5, "CLAUDE.md"),
             "gpu": (9.0, 0.65, "node 102, GPU 0")}
# (session, resource, label, held?, label offset above (+) or below (-) the edge, in inches)
CLAIMS = [("A", "register", "holds: editing, lease 30 min", True, 0.2),
          ("B", "register", "waits: lease held by A", False, -0.25),
          ("B", "git", "holds: committing, lease 2 min", True, -0.2),
          ("C", "gpu", "holds: until the run ends", True, 0.2)]


def main():
    fig, ax = D.canvas(10.5, 4.6)
    D.label(ax, 5.25, 4.35, "First claim wins. A lease that is not renewed expires.", colour=house.INK,
            size=house.FS_BODY, weight="semibold")
    for x, y, t, s in SESSIONS.values():
        D.box(ax, x, y, 2.2, 0.8, t, s, role="agent")
    for x, y, t in RESOURCES.values():
        D.box(ax, x, y, 2.6, 0.62, t, role="plain", title_size=12)

    for s, r, text, held, off in CLAIMS:
        xs, ys = SESSIONS[s][:2]
        xr, yr = RESOURCES[r][:2]
        p, q = (xs + 1.1, ys), (xr - 1.3, yr)
        D.arrow(ax, p, q, colour=house.INK_2, ls="-" if held else "--")
        # the label runs along its own edge, offset at a right angle to it, so a steep edge cannot
        # cut through a horizontal label (canvas units are inches on both axes, so angles are true)
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        mx, my = (p[0] + q[0]) / 2 - off * math.sin(ang), (p[1] + q[1]) / 2 + off * math.cos(ang)
        D.label(ax, mx, my, text, colour=house.INK_2,
                rotation=math.degrees(ang), rotation_mode="anchor")

    D.save(fig, "lg11_resource_claims",
           f"Proposal sketch, not a measurement: {len(SESSIONS)} sessions, {len(RESOURCES)} resources "
           f"and {len(CLAIMS)} of {len(CLAIMS)} example claims drawn (100%). The resources are real "
           f"collision points; who holds what is invented.")


if __name__ == "__main__":
    main()
