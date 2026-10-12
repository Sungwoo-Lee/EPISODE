"""Figure  of the 'Hide or Forage Balance' page. The drawing lives in figures.r8 r8_lever_sweep (one shared module
for the eight planner figures, so they share one palette and layout); this file is the figure's own
entry point, so every figure on the page has exactly one generating script.

  python .py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figures

figures.r8 r8_lever_sweep()
