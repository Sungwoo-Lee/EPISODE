#!/usr/bin/env python3
"""FIGURE 12 - idea E: the research cycle drawn as one graph, with fan-out, joins and a way back.

QUESTION IT ANSWERS. docs/AGENT_PLAYBOOK.md writes "Designing and running a training experiment"
as a straight line that ends at pi, and "New-direction proposal" as a separate flow. What would it
look like as one graph? The figure closes the line into a cycle: pi's three outcomes become edges
back into design, out to a new question, or on to a write-up.

WHAT IS IN IT. Top row, left to right: question, design, two reviewers in parallel (a fan-out and a
join), pi, you. Bottom row, right to left: one training-runner per manifest row (drawn stacked),
analysis, the verdict review, pi again, and a paper draft. Orange arrows go back. The green box is
the shared memory every step reads and writes. Node order follows the playbook's experiment flow;
the parallel reviewers and the back edges are this figure's proposal.

HOW IT IS COMPUTED. Nothing is computed; hand-placed inches on an 11.4 x 5.6 inch canvas.
"""
import _diagram as D
import house

N = dict(title_size=12)
H = 0.75


def main():
    fig, ax = D.canvas(11.4, 5.6)
    y1, y2 = 4.45, 1.8
    top = [(1.0, 1.75, "Question", "from a researcher", "plain"),
           (3.15, 1.95, "experiment-designer", "design, manifest", "agent"),
           (7.45, 1.5, "pi", "go, or not now", "check"),
           (9.55, 1.75, "You", "approve, pick GPUs", "person")]
    for x, w, t, s, role in top:
        D.box(ax, x, y1, w, H, t, s, role=role, **N)
    D.box(ax, 5.35, 4.95, 1.95, H, "plan-reviewer", "the design", role="check", **N)
    D.box(ax, 5.35, 3.95, 1.95, H, "env-config-reviewer", "the configs", role="check", **N)

    D.arrow(ax, (1.875, y1), (2.175, y1))
    D.arrow(ax, (4.125, y1 + 0.1), (4.375, 4.95))
    D.arrow(ax, (4.125, y1 - 0.1), (4.375, 3.95))
    D.arrow(ax, (6.325, 4.95), (6.7, y1 + 0.1))
    D.arrow(ax, (6.325, 3.95), (6.7, y1 - 0.1))
    D.arrow(ax, (8.2, y1), (8.675, y1))
    D.label(ax, 5.35, 5.48, "in parallel, then joined", size=house.FS_LABEL)

    # bottom row, right to left
    for k in (2, 1):                                # stacked copies: one runner per manifest row
        D.box(ax, 9.55 + 0.09 * k, y2 + 0.09 * k, 1.75, H, "", role="agent")
    D.box(ax, 9.55, y2, 1.75, H, "training-runner", "one per run", role="agent", **N)
    D.box(ax, 7.45, y2, 1.95, H, "experiment-analyzer", "writes the verdict", role="agent", **N)
    D.box(ax, 5.35, y2, 1.95, H, "plan-reviewer", "does evidence hold?", role="check", **N)
    D.box(ax, 3.15, y2, 1.5, H, "pi", "deepen, pivot,\nor write up", role="check", **N)
    D.box(ax, 1.0, y2, 1.75, H, "Paper draft", "", role="plain", **N)

    D.arrow(ax, (9.55, y1 - H / 2), (9.55, y2 + H / 2 + 0.2))
    D.arrow(ax, (8.675, y2), (8.425, y2))
    D.arrow(ax, (6.475, y2), (6.325, y2))
    D.arrow(ax, (4.375, y2), (3.9, y2))
    D.arrow(ax, (2.4, y2), (1.875, y2))
    D.label(ax, 2.14, y2 - 0.55, "write up")   # under its own grey edge, away from the pivot line

    D.arrow(ax, (3.15, y2 + H / 2), (3.15, y1 - H / 2), colour=house.ORANGE)
    D.label(ax, 3.27, 3.1, "deepen:\nnext experiment", ha="left")
    D.arrow(ax, (2.75, y2 + H / 2), (1.1, y1 - H / 2), colour=house.ORANGE)
    D.label(ax, 1.78, 3.1, "pivot", ha="right")

    D.box(ax, 6.4, 2.95, 3.3, 0.55, "Memory: wiki, diary, manifest", role="state", **N)

    # crop the empty band under the bottom row (content starts at y ~1.3)
    fig.set_size_inches(11.4, 4.7)
    ax.set_ylim(0.9, 5.6)

    steps = [t for t, role in D.DRAWN if role != "state"]
    added = [t for t in steps if t in ("Question", "Paper draft")]
    D.save(fig, "lg12_research_cycle",
           f"Proposal sketch, not a measurement: {len(steps)} of {len(steps)} steps drawn (100%) - "
           f"{len(steps) - len(added)} named in the playbook's experiment flow, plus "
           f"{len(added)} added here ({', '.join(added)}) - with 2 back edges proposed here. "
           f"No run, episode or seed is summarised.")


if __name__ == "__main__":
    main()
