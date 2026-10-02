#!/usr/bin/env python3
"""FIGURE 4 - the three graphs a graph-engineered system keeps.

QUESTION IT ANSWERS. When the survey by Feng et al. (2026, arXiv:2608.21156) says graph engineering
makes relationships "explicit", explicit relationships between what? Its sections 4.2-4.4 name
three: tasks (which subtask feeds which), agents (who hands work to whom) and runtime state (where
the run is, and how it recovers). Each panel is a small made-up example of one.

WHAT IS IN IT. Three panels, each a small graph with its edge meaning stated under the title.
Blue = agent, orange = check / sends work back (colour map fixed in _diagram.py). The node names
are invented examples, not taken from any system in the survey.

HOW IT IS COMPUTED. Nothing is computed; hand-placed inches on a 10.6 x 4.4 inch canvas.
"""
import _diagram as D
import house

NODE = dict(title_size=12)


def panel_head(ax, x, title, sub):
    D.label(ax, x, 4.15, title, ha="left", colour=house.INK, size=house.FS_BODY, weight="semibold")
    D.label(ax, x, 3.85, sub, ha="left")


def main():
    fig, ax = D.canvas(10.6, 4.4)
    h = 0.46

    # ---- A: tasks ------------------------------------------------------------------------------
    panel_head(ax, 0.15, "Tasks", "arrow: this output feeds that task")
    D.box(ax, 1.8, 3.2, 1.4, h, "Split goal", **NODE)
    D.box(ax, 1.0, 2.3, 1.4, h, "Find papers", **NODE)
    D.box(ax, 2.6, 2.3, 1.4, h, "Run baseline", **NODE)
    D.box(ax, 1.8, 1.4, 1.4, h, "Compare", **NODE)
    D.box(ax, 1.8, 0.5, 1.4, h, "Write report", **NODE)
    D.arrow(ax, (1.6, 2.97), (1.1, 2.53))
    D.arrow(ax, (2.0, 2.97), (2.5, 2.53))
    D.arrow(ax, (1.1, 2.07), (1.6, 1.63))
    D.arrow(ax, (2.5, 2.07), (2.0, 1.63))
    D.arrow(ax, (1.8, 1.17), (1.8, 0.73))

    D.line(ax, (3.55, 0.2), (3.55, 4.3), house.TICK_LINE)

    # ---- B: agents -----------------------------------------------------------------------------
    panel_head(ax, 3.75, "Agents", "arrow: hands work to")
    D.box(ax, 5.35, 3.2, 1.6, h, "Orchestrator", role="agent", **NODE)
    D.box(ax, 4.35, 1.95, 1.3, h, "Researcher", role="agent", **NODE)
    D.box(ax, 6.35, 1.95, 1.3, h, "Coder", role="agent", **NODE)
    D.box(ax, 6.35, 0.6, 1.3, h, "Reviewer", role="check", **NODE)
    D.arrow(ax, (5.1, 2.97), (4.5, 2.18))
    D.arrow(ax, (5.6, 2.97), (6.2, 2.18))
    D.arrow(ax, (5.0, 1.95), (5.7, 1.95))
    D.arrow(ax, (6.55, 1.72), (6.55, 0.83))
    D.arrow(ax, (6.15, 0.83), (6.15, 1.72), colour=house.ORANGE)
    D.label(ax, 6.05, 1.27, "sends back", ha="right")

    D.line(ax, (7.12, 0.2), (7.12, 4.3), house.TICK_LINE)

    # ---- C: runtime state ----------------------------------------------------------------------
    panel_head(ax, 7.32, "Runtime state", "arrow: can move to")
    for y, name in [(3.2, "Planned"), (2.3, "Running"), (1.4, "Verified"), (0.5, "Done")]:
        D.box(ax, 8.1, y, 1.4, h, name, **NODE)
    D.box(ax, 9.8, 2.3, 1.1, h, "Failed", ls="--", **NODE)
    for y0, y1 in [(2.97, 2.53), (2.07, 1.63), (1.17, 0.73)]:
        D.arrow(ax, (8.1, y0), (8.1, y1))
    D.arrow(ax, (8.8, 2.3), (9.25, 2.3))
    D.arrow(ax, (9.8, 2.07), (8.6, 2.07), rad=-0.5)
    D.label(ax, 9.8, 1.45, "retry from a\nsaved step")

    D.save(fig, "lg04_graph_three_views",
           "Conceptual diagram, not a measurement: all 3 of the 3 graph views in Feng et al. (2026) "
           "sections 4.2-4.4 drawn (100%), as 3 invented examples of 5, 4 and 5 nodes. No run, "
           "episode or seed is summarised.")


if __name__ == "__main__":
    main()
