"""FIGURE G9 — In the training world, behaviour against the injury the agent FEELS (observational).

WHAT IS PLOTTED. Every decision of the 1,000,000 recorded episodes, binned by the felt injury the
agent received for it (the interoceptive signal, reconstructed from the injury history exactly as the
environment computes it), with no predator within reach. Same three behaviours and bands as G8.
Observational: a currently injured agent has usually just been attacked, and has chosen where it is.
Level 02 is included (its injuries come only from attacks).
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import _inj as I, house
house.apply()
I.dose_grid("felt", ["lvl02", "lvl03", "lvl04", "lvl05", "lvl06"], "g9_training_felt", "observational",
            "felt injury (0-100)", "all decisions, no predator within reach")
