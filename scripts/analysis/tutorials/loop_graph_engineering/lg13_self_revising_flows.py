#!/usr/bin/env python3
"""FIGURE 13 - idea F: the flows are revised from the record of past jobs, with a person deciding.

QUESTION IT ANSWERS. The survey behind this page (Feng et al. 2026) names "self-evolving graphs" as
an open problem. What is the smallest safe version of that here? A loop around the graph itself:
jobs leave ledgers, a periodic review proposes one edit to the flow file, a reviewer checks the
evidence, and you accept or reject it.

WHAT IS IN IT. Six boxes clockwise: the flow file (green), jobs running (blue), their ledgers
(green), a periodic review (blue), plan-reviewer (orange) and you (outline). The dashed box in the
middle is a hypothetical proposal, invented to show the kind of edit meant.

HOW IT IS COMPUTED. Nothing is computed; hand-placed inches on a 10.5 x 4.8 inch canvas.
"""
import _diagram as D
import house

W, H = 2.3, 0.85
STEPS = [(1.55, 2.4, "Flow file", "the current graph", "state"),
         (4.0, 4.05, "Jobs run", "following the flows", "agent"),
         (7.0, 4.05, "Job ledgers", "what each gate caught", "state"),
         (9.0, 2.4, "Periodic review", "proposes one edit", "agent"),
         (7.0, 0.75, "plan-reviewer", "is the evidence enough?", "check"),
         (4.0, 0.75, "You", "accept or reject", "person")]


def main():
    fig, ax = D.canvas(10.5, 4.8)
    for x, y, t, s, role in STEPS:
        D.box(ax, x, y, W, H, t, s, role=role)

    D.arrow(ax, (1.55, 2.4 + H / 2), (2.85, 4.05), rad=-0.25)
    D.arrow(ax, (5.15, 4.05), (5.85, 4.05))
    D.arrow(ax, (8.15, 4.05), (9.0, 2.4 + H / 2), rad=-0.25)
    D.arrow(ax, (9.0, 2.4 - H / 2), (8.15, 0.75), rad=-0.25)
    D.arrow(ax, (5.85, 0.75), (5.15, 0.75))
    D.arrow(ax, (2.85, 0.75), (1.55, 2.4 - H / 2), rad=-0.25, colour=house.GREEN)   # writes the flow file: green = state on disk, not orange
    D.label(ax, 1.3, 1.15, "edit applied\nand logged", ha="center")

    D.box(ax, 5.5, 2.4, 4.3, 1.05, "A hypothetical proposal",
          '"math-reviewer was never needed on doc-only\nchanges; drop it from that flow?"', ls="--")

    D.save(fig, "lg13_self_revising_flows",
           f"Proposal sketch, not a measurement: {len(STEPS)} of {len(STEPS)} steps of the revision "
           f"loop drawn (100%), plus 1 invented example proposal. No run, episode or seed is "
           f"summarised.")


if __name__ == "__main__":
    main()
