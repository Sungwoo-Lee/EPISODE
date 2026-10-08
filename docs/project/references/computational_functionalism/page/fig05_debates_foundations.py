#!/usr/bin/env python3
"""FIGURE 5 - the three foundational debates, drawn as maps: who holds which position, and who attacks whom.

QUESTION IT ANSWERS. Inside the oldest three questions - is the right computation sufficient, does
everything implement everything, and which computation is a system even running - what are the
positions, when was each taken, and where are the recorded attacks?

WHAT IS IN IT. One panel per debate. Each row is a position from positions.csv, worded as the
synthesis words it; each mark is a work holding that position, placed at its year and drawn in its
community's colour and shape (figure 2's key). An arrow is a documented critique or reply from
edges.csv, drawn only when both ends sit in the same panel. Agreement is not drawn as an arrow: two
works sharing a row already show it.
"""
import _debategroup

STEM = "fig05_debates_foundations"

if __name__ == "__main__":
    _debategroup.build(STEM, ["sufficiency", "triviality", "individuation"], x_min=1968)
