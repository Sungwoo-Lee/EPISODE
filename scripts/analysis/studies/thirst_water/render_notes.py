"""Write the data and kind statements for the three dashboard frames on the thirst page.

The frames are drawn by the rendering session's docs/develop/active/thirst/figures/make_render_frames.py from
real level-06 recordings (seeded random policy); this script only records what each frame is built from, so the
page builder can embed the used / available / why table it requires of every figure (guide 11b).
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

POOL = 400   # episodes recorded: 80 (seed 11) + 320 (seed 23), level-06 test world W1, random policy
FRAMES = {
    "render_a_far_from_pond_low_hydration": "episode 260, step 74 of 102: agent >= 4 squares from the pond, hydration 30 of 200, episode continues",
    "render_b_drinking_predator_in_pond": "episode 258, step 9 of 48: agent on a pond cell with a predator on an adjacent pond cell",
    "render_c_hydration_zero_terminal": "episode 97, final step 53: the environment ended it with the dehydration cause (code 6), injury 0",
}
for stem, why in FRAMES.items():
    C.record_kind(stem, "recording")
    C.record_samples(stem, [
        dict(what="recorded level-06 episodes searched", used=1, total=POOL,
             note=f"one episode chosen per frame by the frame script's search; {why}; nothing set by hand")])
