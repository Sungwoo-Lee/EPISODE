#!/usr/bin/env python3
"""FIGURE 6 - the debates about pain's badness: what it is, why we take painkillers, what asymbolia shows.

Each panel is one debate from debates.csv. Lanes are its positions (positions.csv); a mark is a work
holding that position, at its year, shaped and coloured by community; arrows are documented engagements
(edges.csv) between works in the same panel, styled by relation. Status is the synthesis's.
"""
import _debategroup
if __name__ == "__main__":
    _debategroup.build("fig07_debates_badness", ["valence-nature", "relief-seeking", "asymbolia"])
