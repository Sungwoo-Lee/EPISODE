#!/usr/bin/env python3
"""FIGURE 8 - idea A: the agent flows written once, as data, and checked.

QUESTION IT ANSWERS. What would "flows as data" change? Today each flow lives as ASCII arrows in
docs/AGENT_PLAYBOOK.md and as prose in the agent profiles, with nothing checking one against the
other. The figure shows a single flow file feeding three consumers, one of which is a check.

WHAT IS IN IT. Two existing sources (grey), the proposed flow file (green, a file on disk), and
three consumers: diagrams (grey), agent-manager (blue) and a lint check (orange). The dashed box
is the real defect of 2026-07-28 (wiki entry subagents_cannot_delegate_dead_instructions),
restated as the failure such a check would print.

HOW IT IS COMPUTED. Nothing is computed; hand-placed inches on a 10.5 x 4.4 inch canvas. The file
name and the lint's rules are a proposal - no such file or check exists yet.
"""
import _diagram as D


def main():
    fig, ax = D.canvas(10.5, 4.4)

    D.box(ax, 1.3, 3.35, 2.2, 0.8, "Agent playbook", "flows as prose today")
    D.box(ax, 1.3, 1.95, 2.2, 0.8, "Agent profiles", "the tools each agent holds")
    D.box(ax, 4.6, 2.65, 2.3, 0.95, "Flow file", "nodes, hand-offs, gates", role="state")
    D.arrow(ax, (2.4, 3.2), (3.45, 2.85))
    D.label(ax, 2.95, 3.35, "written once", ha="left")
    D.arrow(ax, (2.4, 2.1), (3.45, 2.45))
    D.label(ax, 2.95, 1.95, "read", ha="left")

    D.box(ax, 8.55, 3.65, 2.3, 0.8, "Diagrams", "flow figures, redrawn")
    D.box(ax, 8.55, 2.55, 2.3, 0.8, "agent-manager", "routes from the file", role="agent")
    D.box(ax, 8.55, 1.45, 2.3, 0.8, "Lint check", "rejects impossible edges", role="check")
    for y in (3.65, 2.55, 1.45):
        D.arrow(ax, (5.75, 2.65 + (y - 2.55) * 0.25), (7.4, y))

    D.box(ax, 4.6, 0.6, 5.6, 0.95, "Example failure it would print",
          'edge "code-reviewer asks bug-curator" is impossible:\n'
          "code-reviewer cannot start agents (a real defect, 2026-07-28)", ls="--")
    D.arrow(ax, (7.4, 1.2), (7.1, 0.9))

    boxes = [t for t, _ in D.DRAWN if not t.startswith("Example")]
    examples = len(D.DRAWN) - len(boxes)
    D.save(fig, "lg08_flows_as_data",
           f"Proposal sketch, not a measurement: {len(boxes)} of {len(boxes)} boxes drawn (100%) - "
           f"existing sources, the proposed file and its readers - plus {examples} example failure "
           f"restated from the 2026-07-28 wiki entry. No run, episode or seed is summarised.")


if __name__ == "__main__":
    main()
