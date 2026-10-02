#!/usr/bin/env python3
"""FIGURE 2 - who closes the loop: you, or a loop you designed.

QUESTION IT ANSWERS. What actually changes between prompt engineering and loop engineering? Both
Osmani (2026) and Macedo (2026, arXiv:2607.00038) put it the same way: in the first a person types
each next request and reads each reply; in the second the person writes a loop specification once
and a program repeats agent -> check until the check passes.

WHAT IS IN IT. Left: a person and an agent with two arrows between them. Right: a person writes a
spec (trigger, goal, check, stop rule, memory - Macedo's five parts), the agent and a check cycle,
memory sits on disk, and the person comes back only at the end. Blue = agent, orange = check,
green = state on disk (colour map fixed in _diagram.py).

HOW IT IS COMPUTED. Nothing is computed; hand-placed inches on a 10.5 x 4.6 inch canvas.
"""
import _diagram as D
import house


def main():
    fig, ax = D.canvas(10.5, 4.6)
    head = dict(ha="left", colour=house.INK, size=house.FS_BODY, weight="semibold")

    # ---- left: prompt engineering -------------------------------------------------------------
    D.label(ax, 0.2, 4.3, "Prompt engineering: you are the loop", **head)
    D.box(ax, 1.1, 2.4, 1.4, 0.8, "You", "a person", role="person")
    D.box(ax, 3.7, 2.4, 1.4, 0.8, "Agent", "one reply", role="agent")
    D.arrow(ax, (1.8, 2.65), (3.0, 2.65), rad=-0.45)
    D.label(ax, 2.4, 3.2, "type the next request")
    D.arrow(ax, (3.0, 2.15), (1.8, 2.15), rad=-0.45)
    D.label(ax, 2.4, 1.6, "read the reply")
    D.label(ax, 0.2, 0.7, "Every step passes through you: you decide\nwhat comes next and when it is done.",
            ha="left")

    D.line(ax, (4.85, 0.25), (4.85, 4.4), house.TICK_LINE)

    # ---- right: loop engineering --------------------------------------------------------------
    D.label(ax, 5.05, 4.3, "Loop engineering: you design the loop", **head)
    D.box(ax, 5.75, 3.5, 1.3, 0.65, "You", "a person", role="person")
    D.box(ax, 5.75, 1.55, 1.3, 1.75, "", role="plain")
    D.label(ax, 5.75, 2.17, "Loop spec", colour=house.INK, size=house.FS_BODY, weight="semibold")
    for i, part in enumerate(["trigger", "goal", "check", "stop rule", "memory"]):
        D.label(ax, 5.75, 1.88 - 0.24 * i, part)
    D.arrow(ax, (5.75, 3.175), (5.75, 2.425))
    D.label(ax, 5.87, 2.8, "write once", ha="left")

    D.box(ax, 7.6, 3.0, 1.2, 0.7, "Agent", "one pass", role="agent")
    D.box(ax, 9.55, 3.0, 1.4, 0.7, "Check", "runs the tests", role="check")
    D.arrow(ax, (6.4, 2.05), (7.0, 2.75))
    D.arrow(ax, (8.2, 3.0), (8.85, 3.0))
    D.arrow(ax, (9.3, 2.65), (7.9, 2.65), rad=-0.45, colour=house.ORANGE)
    D.label(ax, 8.6, 2.02, "not yet: go again")

    D.box(ax, 7.6, 0.85, 1.5, 0.7, "Memory", "files on disk", role="state")
    D.arrow(ax, (7.3, 2.65), (7.3, 1.2), both=True, colour=house.GREEN)

    D.box(ax, 9.55, 0.85, 1.4, 0.7, "Done", "you review it", role="person")
    D.arrow(ax, (9.95, 2.65), (9.95, 1.2))
    D.label(ax, 10.05, 1.92, "passes", ha="left")

    D.save(fig, "lg02_prompting_vs_loop",
           "Conceptual diagram, not a measurement: 2 of 2 working styles drawn (100%) - 2 nodes on "
           "the left, 6 on the right, and all 5 of the 5 loop-spec parts named by Macedo (2026). "
           "No run, episode or seed is summarised.")


if __name__ == "__main__":
    main()
