#!/usr/bin/env python3
"""FIGURE 8 - the debates about separating pain's parts: dimensions, unpleasantness vs avoidance, cingulate and action.

Each panel is one debate from debates.csv, drawn exactly as Figure 6.
"""
import _debategroup
if __name__ == "__main__":
    _debategroup.build("fig08_debates_separation", ["dimensions", "unpleasantness-vs-avoidance", "cingulate-action"])
