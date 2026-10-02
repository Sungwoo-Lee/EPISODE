#!/usr/bin/env python3
"""FIGURE 6 - this repository's own agent team, read as a graph of loops.

QUESTION IT ANSWERS. Is any of this new to grid_world_pain? No: the agent team in CLAUDE.md and the
"Adding a new feature" flow in docs/AGENT_PLAYBOOK.md are already a hand-designed graph, and several
of its nodes run loops of their own. The figure draws that flow so the two ideas can be seen on
something this project actually uses.

WHAT IS IN IT. Nodes and edges are transcribed from AGENT_PLAYBOOK.md "Adding a new feature /
capability" and the CLAUDE.md Default-routing paragraph (checked 2026-09-14): agent-manager returns
a routing plan to top-level Claude, which spawns senior-developer (plan) -> plan-reviewer -> the
user approves -> developer -> senior-developer (Verification Protocol), with env-config-reviewer
in parallel only when the diff touches configs or environment code. The PI step, which runs only
for roadmap-level plans, is left out. Orange arrows are the places a check can send work back.

HOW IT IS COMPUTED. Nothing is computed; hand-placed inches on an 11.4 x 5.4 inch canvas. Every box
records where it came from, and the Data line counts those records - no count is typed (guide 11b).
If the playbook's flow changes, this script must be edited by hand to match.
"""
from collections import Counter

import _diagram as D
import house

N = dict(title_size=12)
NODES = []   # (title, source) for every box that stands for a node, in drawing order

SOURCE = {
    "playbook": "steps of the AGENT_PLAYBOOK.md feature-add flow, including the user's approval",
    "claude_md": "from the CLAUDE.md default-routing paragraph",
    "added": "added by this figure: the requester and the commit/diary state the flow ends in",
}


def node(ax, cx, cy, w, h, title, sub, src, **kw):
    NODES.append((title, src))
    D.box(ax, cx, cy, w, h, title, sub, **kw)


def main():
    fig, ax = D.canvas(11.4, 5.4)
    W, H = 1.8, 0.75

    # ---- row 1: request -> plan -> review -> approval -----------------------------------------
    y1 = 3.55
    row1 = [(1.0, "You", "ask for a feature", "person", "added"),
            (3.2, "Top-level Claude", "spawns each agent", "plain", "claude_md"),
            (5.4, "senior-developer", "writes the plan", "agent", "playbook"),
            (7.6, "plan-reviewer", "hunts for failures", "check", "playbook"),
            (9.8, "You", "approve the plan", "person", "playbook")]
    for x, t, s, role, src in row1:
        node(ax, x, y1, W, H, t, s, src, role=role, **N)
    for a, b in zip(row1, row1[1:]):
        D.arrow(ax, (a[0] + W / 2, y1), (b[0] - W / 2, y1))

    node(ax, 3.2, 4.85, 1.9, H, "agent-manager", "returns the route", "claude_md", role="agent", **N)
    D.arrow(ax, (3.2, 4.475), (3.2, 3.925), both=True)

    D.arrow(ax, (7.3, 3.925), (5.7, 3.925), rad=0.5, colour=house.ORANGE)
    D.label(ax, 6.5, 4.55, "NOT READY: revise")

    # ---- row 2: build -> verify -> record ------------------------------------------------------
    y2 = 1.5
    node(ax, 9.8, y2, W, H, "developer", "builds, runs tests", "playbook", role="agent", **N)
    node(ax, 7.6, y2, W, H, "senior-developer", "checks against plan", "playbook", role="check", **N)
    node(ax, 5.4, y2, W, H, "commit + diary", "state on disk", "added", role="state", **N)
    node(ax, 7.6, 0.5, 2.1, H, "env-config-reviewer", "only if configs change", "playbook",
         role="check", ls="--", **N)

    D.arrow(ax, (9.8, y1 - H / 2), (9.8, y2 + H / 2))
    D.arrow(ax, (8.9, y2), (8.5, y2))
    D.arrow(ax, (6.7, y2), (6.3, y2))
    D.arrow(ax, (9.3, y2 - H / 2), (8.65, 0.75), ls="--")

    D.arrow(ax, (7.9, y2 + H / 2), (9.4, y2 + H / 2), rad=-0.5, colour=house.ORANGE)
    D.label(ax, 8.65, 2.5, "does not match: fix")

    # developer's own loop: test, fix, re-test
    D.arrow(ax, (10.7, 1.7), (10.7, 1.3), rad=-1.5, colour=house.ORANGE)
    D.label(ax, 10.85, 2.25, "test, fix,\nre-test")

    # ---- legend (swatches, not nodes) ----------------------------------------------------------
    items = [("agent", "blue: an agent, running its own loop"),
             ("check", "orange: a check that can send work back"),
             ("state", "green: state written to disk"),
             ("person", "outline: a person")]
    for i, (role, text) in enumerate(items):
        yy = 1.95 - 0.4 * i
        D.box(ax, 0.45, yy, 0.4, 0.26, "", role=role, r=0.04)
        D.label(ax, 0.8, yy, text, ha="left")
    yy = 1.95 - 0.4 * 4
    D.arrow(ax, (0.25, yy), (0.65, yy), colour=house.ORANGE)
    D.label(ax, 0.8, yy, "orange arrow: work sent back", ha="left")

    n = len(NODES)
    by = Counter(src for _, src in NODES)
    repeats = [t for t, c in Counter(t for t, _ in NODES).items() if c > 1]
    parts = "; ".join(f"{by[k]} {SOURCE[k]}" for k in SOURCE if by[k])
    D.save(fig, "lg06_project_team_graph",
           f"Transcribed, not measured: {n} of {n} node boxes drawn (100%). Of those, {parts}. "
           f"Names drawn twice, once for each of two roles: {', '.join(repeats) or 'none'}. The playbook was "
           f"read on 2026-09-14 and its optional PI step is left out. No run, episode or seed is "
           f"summarised.")


if __name__ == "__main__":
    main()
