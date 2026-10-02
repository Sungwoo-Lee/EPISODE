#!/usr/bin/env python3
"""FIGURE 9 - idea B: every hand-off passes a gate that reads a file, not an agent's say-so.

QUESTION IT ANSWERS. Where would evidence gates sit in flows this project already runs? Two rows:
the feature flow (docs/AGENT_PLAYBOOK.md "Adding a new feature") and the analysis flow, whose
plan-reviewer step before pi is the gate CLAUDE.md calls "the one that is easy to forget".

WHAT IS IN IT. Blue boxes are agents, orange boxes are the proposed gates, each naming what it
would look for on disk. The small labels under each gate are what happens when the evidence is
missing. The dashed box states the principle.

HOW IT IS COMPUTED. Nothing is computed; hand-placed inches on an 11 x 4.6 inch canvas. The gates
are a proposal; today these checks are rules a session must remember to follow.
"""
import _diagram as D
import house

N = dict(title_size=12)


def main():
    fig, ax = D.canvas(11.0, 4.6)
    head = dict(ha="left", colour=house.INK, size=house.FS_BODY, weight="semibold")

    # ---- feature flow --------------------------------------------------------------------------
    y = 3.25
    D.label(ax, 0.2, 4.3, "Feature flow", **head)
    row = [(0.95, 1.6, "senior-developer", "writes the plan", "agent"),
           (3.0, 2.0, "Gate", "review verdict and\nyour approval in plan", "check"),
           (5.05, 1.6, "developer", "implements", "agent"),
           (7.1, 2.0, "Gate", "tests pass and\ndiff left uncommitted", "check"),
           (9.25, 1.9, "senior-developer", "verifies", "agent")]
    for x, w, t, s, role in row:
        D.box(ax, x, y, w, 0.95 if role == "check" else 0.75, t, s, role=role, **N)
    for a, b in zip(row, row[1:]):
        D.arrow(ax, (a[0] + a[1] / 2, y), (b[0] - b[1] / 2, y))
    for x in (3.0, 7.1):
        D.arrow(ax, (x, y - 0.475), (x, 2.45), colour=house.ORANGE, ls="--")
        D.label(ax, x, 2.25, "missing: stop, and\nname the missing line")

    # ---- analysis flow -------------------------------------------------------------------------
    y2 = 1.0
    D.label(ax, 0.2, 1.85, "Analysis flow", **head)
    row2 = [(1.1, 1.95, "experiment-analyzer", "writes the verdict", "agent"),
            (3.4, 2.0, "Gate", "plan-reviewer pass\non the verdict", "check"),
            (5.6, 1.5, "pi", "continue or pivot", "check")]
    for x, w, t, s, role in row2:
        D.box(ax, x, y2, w, 0.95 if t == "Gate" else 0.75, t, s, role=role, **N)
    for a, b in zip(row2, row2[1:]):
        D.arrow(ax, (a[0] + a[1] / 2, y2), (b[0] - b[1] / 2, y2))
    D.label(ax, 3.4, 0.22, "the gate CLAUDE.md calls easy to forget")

    D.box(ax, 8.85, 1.0, 3.4, 1.0, "A gate reads a file",
          "so a skipped review cannot\npass without anyone noticing", ls="--")

    def tally(r):
        gates = sum(1 for _, _, t, _, _ in r if t == "Gate")
        return len(r) - gates, gates

    (a1, g1), (a2, g2) = tally(row), tally(row2)
    D.save(fig, "lg09_evidence_gates",
           f"Proposal sketch, not a measurement: 2 of 2 flows drawn (100%) - {a1} steps and {g1} gates "
           f"in the feature flow, {a2} steps and {g2} gate in the analysis flow. No run, episode or "
           f"seed is summarised.")


if __name__ == "__main__":
    main()
