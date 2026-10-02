#!/usr/bin/env python3
"""FIGURE 3 - the parts of one engineered loop.

QUESTION IT ANSWERS. What does a loop specification contain, and how do the parts connect when it
runs? Macedo (2026, arXiv:2607.00038) names five parts - trigger, goal, verification step, stopping
rule, memory; IBM's explainer (Belcic & Stryker, 2026) describes the running cycle as goal -> action
-> observation -> adjustment, which is the reason-act-observe pattern of ReAct (Yao et al., 2022).
The figure puts the five parts on that cycle.

WHAT IS IN IT. Trigger starts an agent pass (blue); its result goes to a verifier (orange); a stop
rule (orange) either exits or sends the loop round again; the goal (grey) is read by both the agent
and the verifier; memory (green) is read and updated by each pass.

HOW IT IS COMPUTED. Nothing is computed; hand-placed inches on a 10 x 5.4 inch canvas.
"""
import _diagram as D
import house


def main():
    fig, ax = D.canvas(10.0, 5.4)

    D.box(ax, 1.0, 2.7, 1.6, 1.0, "Trigger", "a schedule, an\nevent, a person", role="plain")
    D.box(ax, 5.2, 4.75, 4.2, 0.8, "Goal", 'fixed for every pass, e.g. "all tests pass"', role="plain")
    D.box(ax, 4.0, 2.7, 2.0, 1.0, "Agent pass", "reason, act, observe", role="agent")
    D.box(ax, 7.0, 2.7, 1.8, 1.0, "Verify", "tests, a build,\na reviewer agent", role="check")
    D.box(ax, 7.0, 0.85, 1.8, 0.9, "Stop rule", "goal met, or\nbudget spent", role="check")
    D.box(ax, 9.2, 0.85, 1.3, 0.9, "Exit", "report, or\nask a person", role="person")
    D.box(ax, 1.0, 0.85, 1.6, 0.9, "Memory", "plan file, notes,\ngit history", role="state")

    D.arrow(ax, (1.8, 2.7), (3.0, 2.7))
    D.label(ax, 2.4, 2.9, "starts")
    D.arrow(ax, (5.0, 2.7), (6.1, 2.7))
    D.label(ax, 5.55, 2.9, "result")
    D.arrow(ax, (7.0, 2.2), (7.0, 1.3))
    D.arrow(ax, (7.9, 0.85), (8.55, 0.85))
    D.label(ax, 8.22, 1.03, "yes")
    # "no": back round to the agent, along a right-angled path
    D.arrow(ax, (6.1, 0.85), (4.0, 2.2), colour=house.ORANGE,
            conn="angle,angleA=180,angleB=90,rad=0")
    D.label(ax, 5.05, 0.64, "no: next pass")

    D.arrow(ax, (4.0, 4.35), (4.0, 3.2), ls="--")
    D.label(ax, 3.9, 3.78, "read", ha="right")
    D.arrow(ax, (7.0, 4.35), (7.0, 3.2), ls="--")
    D.label(ax, 7.1, 3.78, "checked against", ha="left")

    D.arrow(ax, (1.8, 1.05), (3.0, 2.25), both=True, colour=house.GREEN, ls="--")
    D.label(ax, 2.6, 1.25, "read and\nupdated", ha="left")

    D.save(fig, "lg03_loop_anatomy",
           "Conceptual diagram, not a measurement: all 5 of the 5 loop-specification parts named by "
           "Macedo (2026) drawn (100%), plus the agent pass and the exit. No run, episode or seed "
           "is summarised.")


if __name__ == "__main__":
    main()
