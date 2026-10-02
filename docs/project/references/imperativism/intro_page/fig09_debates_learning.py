#!/usr/bin/env python3
"""FIGURE 9 - the debates about pain, learning and avoidance.

Each panel is one debate from debates.csv, drawn exactly as Figure 6.
"""
import _debategroup
if __name__ == "__main__":
    _debategroup.build("fig09_debates_learning", ["learning-signal", "avoidance-drivers"])
