#!/usr/bin/env python3
"""FIGURE 10 - idea C: a ledger per job, so a new session can resume where the last one stopped.

QUESTION IT ANSWERS. What is a "runtime state graph" (Figure 4, third panel) for this project?
The simplest form is one small file per multi-agent job, written at every hand-off. The figure
shows an example ledger and what happens when the session running the job ends mid-flow.

WHAT IS IN IT. Left, a green file with five example rows (step, agent, status, evidence). Right,
the recovery path: a session ends, a new session reads the ledger first, and resumes at the step
marked running. Every row, session id and file name is invented for illustration.

HOW IT IS COMPUTED. Nothing is computed; hand-placed inches on a 10.8 x 4.6 inch canvas. The
ledger columns follow the pattern the Launch Manifest in docs/AGENT_PLAYBOOK.md already uses for
training runs (planned columns written by one agent, actual columns by another).
"""
import _diagram as D
import house

ROWS = [("step", "agent", "status", "evidence"),
        ("plan", "senior-developer", "done", "plan.md"),
        ("review", "plan-reviewer", "done", "verdict: SOUND"),
        ("approve", "you", "done", "approval line"),
        ("implement", "developer", "running", "session 7f3a"),
        ("verify", "senior-developer", "waiting", "-")]


def main():
    fig, ax = D.canvas(10.8, 4.6)

    D.box(ax, 3.0, 2.45, 5.5, 3.4, "", role="state")
    D.label(ax, 0.45, 3.85, "Job ledger: one small file per job", ha="left", colour=house.INK,
            size=house.FS_BODY, weight="semibold")
    for i, (step, agent, status, ev) in enumerate(ROWS):
        line = f"{step:<10} {agent:<17} {status:<8} {ev}"
        D.label(ax, 0.45, 3.3 - 0.46 * i, line, ha="left", family=house.FONT_MONO,
                colour=house.INK if i else house.INK_2, weight="semibold" if status == "running" else "normal")
    D.label(ax, 3.0, 0.4, "the Launch Manifest already does this for training runs")

    D.box(ax, 8.45, 3.75, 2.6, 0.9, "Session ends mid-job", "a crash, a compaction,\nor a closed laptop",
          role="plain")   # an event, not a person: the outline style means "a person" (Figure 6 legend)
    D.box(ax, 8.45, 2.4, 2.6, 0.9, "New session starts", "reads the ledger first", role="agent")
    D.box(ax, 8.45, 1.05, 2.6, 0.9, "Resumes at implement", "after checking session\n7f3a is gone",
          role="agent")
    D.arrow(ax, (8.45, 3.3), (8.45, 2.85))
    D.arrow(ax, (8.45, 1.95), (8.45, 1.5))
    D.arrow(ax, (5.75, 2.4), (7.15, 2.4), colour=house.GREEN)
    D.label(ax, 6.45, 2.6, "read")

    D.save(fig, "lg10_job_ledger",
           f"Proposal sketch, not a measurement: {len(ROWS) - 1} of {len(ROWS) - 1} example ledger rows "
           f"drawn (100%), all invented, plus a 3-step recovery path. No run, episode or seed is "
           f"summarised.")


if __name__ == "__main__":
    main()
