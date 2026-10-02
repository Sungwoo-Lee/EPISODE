"""Load the sweep results written by sweep.py (shared by the simulation figures)."""
import json, os
import _common as C
SW = json.load(open(os.path.join(C.OUT, "sweep.json")))
META = SW["_meta"]
