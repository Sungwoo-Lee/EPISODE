"""Figure r6_hazard_mapping of the 'Hide or Forage Balance' page. The drawing lives in figures.r6 (one shared module
for the eight planner figures, so they share one palette and layout); this file is the figure's own
entry point, so every figure on the page has exactly one generating script.

  python r6_hazard_mapping.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figures

figures.r6()
