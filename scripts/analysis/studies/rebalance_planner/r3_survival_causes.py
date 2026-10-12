"""Figure r3_survival_causes of the 'Hide or Forage Balance' page. The drawing lives in figures.r3 (one shared module
for the eight planner figures, so they share one palette and layout); this file is the figure's own
entry point, so every figure on the page has exactly one generating script.

  python r3_survival_causes.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figures

figures.r3()
