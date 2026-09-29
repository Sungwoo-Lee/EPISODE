"""Write the data and kind statements for the three dashboard renders on the thirst page.

The renders themselves are made by the rendering session with the dashboard package
(src/environment/dashboard/); this script only records what each frame is built from, so the page
builder can embed the same used / available / why table it requires of every figure (guide 11b).
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

SRC = "real level-05 recording: ordinary agent (t1none), final checkpoint, episode 2, seed 8217"
FRAMES = {
    "render_a_far_from_pond_low_hydration": (59, 336, "step 59 of the real episode; hydration set to 34 of 200"),
    "render_b_drinking_predator_in_pond": (264, 336, "step 264; hydration set to 104 of 200; the pond placed at array rows 5-6, cols 4-5 so the agent and a predator both stand in it"),
    "render_c_hydration_zero_terminal": (333, 336, "step 333, the last step with no injury and no predator adjacent; the episode is truncated there and hydration set to 0"),
}
for stem, (step, total, why) in FRAMES.items():
    C.record_kind(stem, "mockup")
    C.record_samples(stem, [
        dict(what="frames from the recorded episode", used=1, total=total, note=f"{SRC}; {why}"),
        dict(what="synthetic fields added to that frame", used=4, total=4,
             note="pond position, hydration value, the 200 maximum, one Hydration observation equal to hydration/200 (noise off)")])
