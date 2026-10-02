"""FIGURE G8 — In the training world, what a randomly assigned starting injury does (causal).

WHAT IS PLOTTED. Levels 03-06 start every training-world episode at a random injury, so binning the
first 25 decisions by the starting injury gives a causal dose-response. Three behaviours, each a
share of decisions taken with no predator within reach: being in the bush, choosing Rest, and — of
the decisions taken in the bush with no animal within reach — leaving it. Lines: the 1,000,000-episode
store at the final checkpoint. Bands: lowest to highest of the four late-checkpoint stores (100,000
episodes each), where they exist. Level 02 does not randomise the start, so it has no causal reading.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "basicq2_waves"))
import _inj as I, house
house.apply()
I.dose_grid("randomised", ["lvl03", "lvl04", "lvl05", "lvl06"], "g8_training_dose", "causal",
            "starting injury", "decisions 2-25, no predator within reach")
