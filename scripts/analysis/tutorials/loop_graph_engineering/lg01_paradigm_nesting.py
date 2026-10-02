#!/usr/bin/env python3
"""FIGURE 1 - the five engineering layers, drawn as boxes inside boxes.

QUESTION IT ANSWERS. Where do "loop engineering" and "graph engineering" sit relative to the older
terms a reader may know (prompt engineering, context engineering)? The survey by Feng et al. (2026,
arXiv:2608.21156) lists them as a progression and writes one agent as a loop over its harness; that
nesting is what the figure draws. Graph engineering then wires several such loops together.

WHAT IS IN IT. Five nested regions (graph > loop > harness > context > prompt), plus two collapsed
agents beside the expanded one to show that a graph holds more than one loop. Neutral greys only:
this figure makes no role distinction, so it spends no hue.

HOW IT IS COMPUTED. Nothing is computed. Box positions are hand-chosen inches on a 10 x 5.6 inch
canvas; position and size encode nesting only, never a quantity.
"""
import _diagram as D
import house


def main():
    fig, ax = D.canvas(10.0, 5.6)
    # (x0, y0, x1, y1, title, subtitle, fill) - outermost first, so inner regions paint on top
    layers = [
        (0.2, 0.2, 9.8, 5.4, "Graph engineering", "several agents' loops, wired together", house.PAPER),
        (0.5, 0.5, 7.0, 4.55, "Loop engineering", "one agent, repeated until a check passes", house.BG_SOFT),
        (0.8, 0.8, 5.9, 3.85, "Harness engineering", "tools, memory and skills around the model", "#e9ebe8"),
        (1.1, 1.1, 5.6, 3.15, "Context engineering", "what the model can see when it answers", "#dfe2de"),
        (1.4, 1.4, 5.3, 2.45, "Prompt engineering", "the words of one request", "#d3d7d2"),
    ]
    for i, (x0, y0, x1, y1, t, s, fc) in enumerate(layers):
        D.frame(ax, x0, y0, x1, y1, t, s, fc=fc, ec=house.INK_2 if i == 0 else house.RULE)

    # the repeat, drawn in the loop's own margin (between the harness edge and the loop edge)
    D.arrow(ax, (6.3, 1.0), (6.3, 3.6), rad=0.45, lw=1.6)
    D.label(ax, 6.72, 2.3, "repeat", rotation=90)

    # two more agents, collapsed, with hand-offs between them
    D.box(ax, 8.65, 3.55, 1.9, 0.8, "Agent B", "its own loop")
    D.box(ax, 8.65, 1.35, 1.9, 0.8, "Agent C", "its own loop")
    D.arrow(ax, (7.0, 3.55), (7.7, 3.55))
    D.arrow(ax, (7.0, 1.35), (7.7, 1.35))
    D.arrow(ax, (8.65, 3.15), (8.65, 1.75))

    D.save(fig, "lg01_paradigm_nesting",
           "Conceptual diagram, not a measurement: 5 of 5 nested layers and 3 of 3 agents drawn "
           "(100%), with 3 hand-off arrows. Layer order follows Feng et al. (2026); no run, "
           "episode or seed is summarised.")


if __name__ == "__main__":
    main()
