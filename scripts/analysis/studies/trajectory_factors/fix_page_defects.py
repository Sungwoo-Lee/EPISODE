#!/usr/bin/env python3
"""fix_page_defects.py - targeted corrections to the a01 page's pre-existing prose and legends.

The other three scripts in this folder each own a block they generate. This one owns small,
surgical fixes to text that was already on the page before any of them ran - the kind a reader
turns up by going through the figures one at a time.

Every correction is a (before, after) pair with its own assert, so a fix whose anchor has moved is
a hard failure rather than a silent no-op. That failure mode is not hypothetical: a `.replace` with
a stale anchor and no assert has silently done nothing twice in this page's history, once leaving
raw `__PC_HI__` placeholders in published text.

Idempotent by construction - a correction whose "after" is already present is skipped, so the
script can be re-run after the page is regenerated from the other three.
"""
from __future__ import annotations
import os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
os.chdir(ROOT)
PAGE = "docs/experiments/active/trajectory_factors/a01_hiding_drivers.html"



CAP_BEFORE = """<figcaption>Extra hiding caused by a rabbit smelling predator-like, split by what was actually
  nearby at the time."""

CAP_AFTER = """<figcaption><b>Read the gap inside each row, not the bars across rows.</b> Each row is one
  situation, and its two bars are the same measurement under two draws of the rabbit&rsquo;s smell.
  The distance between them is the extra hiding the smell alone caused: <strong>+8.1</strong> points
  with nothing nearby, <strong>+6.3</strong> with the predator nearby, and <strong>+23.1</strong>
  when the misread rabbit is itself the animal standing close. A smell that merely made the agent
  jumpy would move all three rows alike; this one is aimed, about three times as strongly."""

FIXES = [
    # Figure 9 drew its second bar as `aim ? --false : --true`, so two rows came out teal and one
    # red - three fills, two legend entries, and an unexplained colour. But the teal and the red
    # are the SAME measurement; the red was only emphasis on the row the argument turns on. The
    # honest fix is to delete the distinction rather than document it: one quantity, one colour.
    # Red is the right one to keep - Figure 7 already spends `--false` on "the rabbit's smell, a
    # false alarm", and every bar in this figure is that same false alarm.
    ("figure 9: one quantity drawn in two colours",
     'bar(d[1],y,V("--muted"),.55); bar(d[2],y+16,aim?V("--false"):V("--true"),aim?1:.75);',
     'bar(d[1],y,V("--muted"),.55); bar(d[2],y+16,V("--false"),.9);'),

    # The figure is read WITHIN a row - the distance between a row's two bars is the effect - and
    # nothing said so. Read across rows instead and it looks like it says "the agent hides most
    # when a predator is near", which is true, uninteresting, and not the point.
    ("figure 9 caption: say the comparison is within a row",
     CAP_BEFORE, CAP_AFTER),

    # the rewritten caption makes the aiming claim with numbers, so the sentence that made it
    # without them is now a repeat
    ("figure 9 caption: drop the duplicated claim",
     """The response is aimed at the rabbit roughly three times more strongly than
  anywhere else. When that rabbit""",
     """When that rabbit"""),
]


def main():
    write = "--write" in sys.argv
    html = open(PAGE, encoding="utf-8").read()
    applied = skipped = 0
    for name, before, after in FIXES:
        if html.count(before) == 1:
            pass                                  # anchor present: apply it below
        elif before not in html and after in html:
            print(f"  already applied: {name}")
            skipped += 1
            continue
        if html.count(before) != 1:
            raise SystemExit(
                f"fix_page_defects: anchor for {name!r} matched {html.count(before)} times, "
                f"expected exactly 1. The page changed under this fix - re-derive it rather "
                f"than letting the replacement silently do nothing.")
        html = html.replace(before, after)
        print(f"  applied: {name}")
        applied += 1
    print(f"  {applied} applied, {skipped} already present")
    if not write:
        print("  DRY RUN - pass --write to apply")
        return
    open(PAGE, "w", encoding="utf-8").write(html)
    print(f"  wrote {PAGE}")

# One short worked row apiece, inside the method block each figure already has - not a new box.
# Both figures report a share of STEPS, and the two differ in exactly one respect (when the
# animal's position is read), which is the thing a reader is most likely to get wrong.
FIXES += [
    ("figure 9: worked example",
     "<dt>three states</dt><dd>predator near takes precedence; &ldquo;rabbit near&rdquo; means a "
     "rabbit within 2 and no predator within 2</dd>",
     "<dt>three states</dt><dd>predator near takes precedence; &ldquo;rabbit near&rdquo; means a "
     "rabbit within 2 and no predator within 2</dd>"
     "<dt>worked</dt><dd>the 49.8% counts STEPS, not episodes. A step qualifies if, <em>at that "
     "same step</em>, a rabbit is within 2 tiles and no predator is &mdash; in an episode whose "
     "one rabbit was drawn predator-like. Of all such steps, 49.8% had the agent standing in a "
     "bush</dd>"),

    ("figure 10: worked example",
     "<dt>population</dt><dd>all 189,906,610 action steps, unconditioned</dd>",
     "<dt>population</dt><dd>all 189,906,610 action steps, unconditioned</dd>"
     "<dt>worked</dt><dd>each step is filed by where the animals were <em>one step earlier</em>, "
     "then scored by where the agent is <em>now</em>. So 67.9% is: of every step whose previous "
     "step had a predator within 2 tiles, 67.9% found the agent in a bush. This is the one "
     "difference from Figure&nbsp;9, which reads position and cover at the same step</dd>"),
]

if __name__ == "__main__":
    main()
