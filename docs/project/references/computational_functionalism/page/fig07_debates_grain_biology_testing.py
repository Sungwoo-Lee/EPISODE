#!/usr/bin/env python3
"""FIGURE 7 - the three debates about what would have to be copied, and whether any of it can be tested.

QUESTION IT ANSWERS. How fine must a copy be, does being alive matter, and can a theory of
consciousness be tested at all - who holds which position in each, and who attacks whom?

WHAT IS IN IT. One panel per debate, drawn exactly as figure 5: rows are positions from
positions.csv, marks are works at their year in their community's colour and shape, arrows are
documented critiques and replies from edges.csv with both ends in the same panel.
"""
import _debategroup

STEM = "fig07_debates_grain_biology_testing"

if __name__ == "__main__":
    _debategroup.build(STEM, ["grain", "biology", "testability"], x_min=1968)
