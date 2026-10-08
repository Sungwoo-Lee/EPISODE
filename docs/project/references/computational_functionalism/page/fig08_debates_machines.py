#!/usr/bin/env python3
"""FIGURE 8 - the three debates about the machines now in front of us.

QUESTION IT ANSWERS. Is what a system says evidence about whether it has a mind, are today's
language models candidates, and what should be done while the question stays open?

WHAT IS IN IT. One panel per debate, drawn exactly as figure 5: rows are positions from
positions.csv, marks are works at their year in their community's colour and shape, arrows are
documented critiques and replies from edges.csv with both ends in the same panel. These three
debates are young, so their marks crowd into the right-hand decade.
"""
import _debategroup

STEM = "fig08_debates_machines"

if __name__ == "__main__":
    _debategroup.build(STEM, ["evidence", "llm", "precaution"], x_min=1968)
