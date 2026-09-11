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

# ---- Figure 11 -------------------------------------------------------------------------------
# Its two lines were --muted and --cover: relative luminance 0.147 against 0.115, a contrast of
# 1.19:1. Separable by hue alone, and both desaturated mid-tones, so on a thin line they read as
# one series. This palette is luminance-flat (0.115-0.146) everywhere except --warm at 0.274, so
# amber is its only member that separates by LIGHTNESS as well as hue. Grey keeps "every injury",
# where a neutral suits the unfiltered set; the subset takes amber and a heavier stroke.
FIXES += [
    ("figure 11: the two lines were the same lightness",
     '[[A,V("--muted"),2],[I,V("--cover"),2.3]]',
     '[[A,V("--muted"),2],[I,V("--warm"),2.9]]'),

    ("figure 11 legend: match the new colour",
     '<span><i class="sw" style="background:var(--cover)"></i>isolated injuries only</span>',
     '<span><i class="sw" style="background:var(--warm)"></i>isolated injuries only</span>'),

    # "isolated" named a filter without saying what it selects for, or why anyone would want it.
    ("figure 11: say what an isolated injury is",
     "<dt>isolated</dt><dd>the subset with no other damage event in the 10 steps before or 25 after</dd>",
     "<dt>isolated</dt><dd>the subset of hits with <strong>no other damage in the 10 steps before "
     "or the 25 after</strong> &mdash; a single, one-off wound rather than one blow inside a "
     "sustained mauling. It matters because during a chase the agent is struck again and again, so "
     "what follows a hit there is its response to an <em>attack still in progress</em> rather than "
     "to the wound itself. Isolating single hits is the only way to watch one injury's effect rise "
     "and decay on its own &mdash; at the cost recorded in the next row</dd>"),
]

# ---- Figure 12 -------------------------------------------------------------------------------
# Its rows were worded ("feels nothing" ... "extreme") while Figure 18, built from the SAME
# reconstruction, labels the same six bins numerically. The producer is
# scripts/analysis/supplementary/injdeep.py: `PE=[1e-9,8,18,32,50]` with
# `PL=["felt 0","0-8","8-18","18-32","32-50","50+"]`, and `HB=[1,2,3,5]` for the hit columns.
# Numbers let a reader see that the bins are uneven and that the signal shares the 0-100 scale
# with injury, neither of which a word conveys.
FIXES += [
    ("figure 12: number the nociception rows",
     'heat("hits",D.hits.hide,["feels nothing","a little","some","a lot","severe","extreme"],',
     'heat("hits",D.hits.hide,["felt 0","0\u20138","8\u201318","18\u201332","32\u201350","50+"],'),

    ("figure 12: how a step lands in a cell",
     "<dt>conditioning</dt><dd>steps with no predator within 2 tiles only, so current proximity "
     "cannot drive the pattern</dd>",
     "<dt>conditioning</dt><dd>steps with no predator within 2 tiles only, so current proximity "
     "cannot drive the pattern</dd>"
     "<dt>the rows</dt><dd>the reconstructed nociception signal, binned at 0, 0&ndash;8, "
     "8&ndash;18, 18&ndash;32, 32&ndash;50 and 50+ &mdash; the same 0&ndash;100 scale injury uses, "
     "and the same bins Figure&nbsp;18 draws</dd>"
     "<dt>one step, one cell</dt><dd>each step is filed by two things read at that moment: the "
     "nociception it was feeling (row) and how many times it had <em>already</em> been struck "
     "earlier in the same episode (column). Every step lands in exactly one cell and nothing is "
     "counted twice</dd>"
     "<dt>episodes move</dt><dd>so an episode travels <strong>rightward</strong> through the grid "
     "as it goes: it starts in &ldquo;0 strikes&rdquo;, and each hit moves all its later steps one "
     "column right. An episode struck exactly twice contributes steps to columns 0, 1 and 2 and "
     "<strong>never appears in 3&ndash;4 or 5+</strong> &mdash; so the right-hand columns are not "
     "the same episodes later on, they are a smaller and more heavily attacked set. It moves "
     "<strong>vertically</strong> too: nociception climbs after a hit and decays over the next "
     "dozen steps, so one episode's steps spread down and back up the rows as it is wounded and "
     "recovers</dd>"
     "<dt>cell sizes</dt><dd>the grid holds 175.1M steps, very unevenly: 47.8M sit in &ldquo;felt "
     "0, 5+ strikes&rdquo; and only 0.29M in &ldquo;50+, 2 strikes&rdquo;. The comparison the "
     "figure is built on &mdash; 50+ nociception at 0 strikes against 1 strike &mdash; rests on "
     "0.96M and 0.44M steps respectively</dd>"),
]

# The run carries TWO nociceptors and the figure named neither:
#   sense_interoceptive_nociception - tonic, a 12-slot injury buffer convolved with an alpha
#     kernel (tau 3), kernel[0]=0 so the current step never leaks in. This is what Figure 12 bins.
#   sense_extero_nociception - phasic, the maximum intensity among CURRENT painful contacts
#     (hiding predator, damaging animal, rock overlap, rock collision). Instantaneous.
# Both are enabled in this run's saved config (nociception_enabled: true alongside
# interoceptive_nociception_enabled: true) and both appear as separate entries in its
# perceptual-noise block, so "nociception level" was genuinely ambiguous. 25 characters fits the
# rotated row block; 52 did not, which is why this is a rename and not a sentence.
FIXES += [
    ("figure 12: name which nociceptor",
     '"nociception level","how many times it has actually been struck this episode",45,',
     '"interoceptive nociception","how many times it has actually been struck this episode",45,'),

    ("figure 12: say the other channel is live and uncontrolled",
     "<dt>the rows</dt><dd>the reconstructed nociception signal, binned at 0, 0&ndash;8, "
     "8&ndash;18, 18&ndash;32, 32&ndash;50 and 50+ &mdash; the same 0&ndash;100 scale injury uses, "
     "and the same bins Figure&nbsp;18 draws</dd>",
     "<dt>the rows</dt><dd>the reconstructed <strong>interoceptive</strong> signal, binned at 0, "
     "0&ndash;8, 8&ndash;18, 18&ndash;32, 32&ndash;50 and 50+ &mdash; the same 0&ndash;100 scale "
     "injury uses, and the same bins Figure&nbsp;18 draws</dd>"
     "<dt>which nociceptor</dt><dd>this run has <strong>two</strong>, and they are different "
     "signals. <code>sense_interoceptive_nociception</code> is <em>tonic</em>: a 12-slot buffer of "
     "recent injury convolved with an alpha kernel, peaking about three steps back and never "
     "including the present one. That is the signal binned here. "
     "<code>sense_extero_nociception</code> is <em>phasic</em>: the strongest painful contact "
     "happening right now &mdash; a hiding predator, a damaging animal, a rock. Both were enabled "
     "in this run and both reach the agent as separate observation entries</dd>"
     "<dt>and so</dt><dd>holding the interoceptive row constant does <strong>not</strong> hold the "
     "phasic channel constant. A step at high interoceptive nociception with one strike behind it "
     "may also be carrying a contact signal that a step with zero strikes cannot. This is the same "
     "gap &ldquo;What we cannot say about nociception&rdquo; names below &mdash; the figure "
     "separates <em>feeling</em> from <em>origin</em>, not one channel from the other</dd>"),
]

PANEL_ARMS = ("<div class=\"panel\" id=\"arm-table\">\n<div class=\"fignum\">What actually differs between the ten agents</div>\n<p>Diffing the ten runs&rsquo; own saved <code>config.yaml</code> files leaf by leaf &mdash; 244 keys compared &mdash; <strong>two</strong> settings differ, not one, and they move together. Healing while resting is <code>base_rate &times; (1 + accel_rate)<sup>streak&minus;1</sup></code>, so the pair decides <em>how back-loaded</em> resting&rsquo;s payoff is: a01 pays a flat 5 per rest step forever, a10 pays almost nothing until about ten consecutive rest steps and then pays enormously. Everything else &mdash; environment, sensors, training length, seed &mdash; is identical. <strong>heal @10</strong> below is the injury recovered on the tenth consecutive rest step, and <strong>total</strong> the sum over a fifteen-step rest &mdash; which is roughly matched across the arms, so the sweep varies the SHAPE of the payoff rather than its size. The first rest step is not shown because it always equals the base rate.</p>\n<div class=\"scroll\"><table>\n<thead><tr><th>agent</th><th class=\"num\">accel</th><th class=\"num\">base</th><th class=\"num\">heal @10</th><th class=\"num\">total, 15 rests</th><th class=\"num\">hiding</th><th class=\"num\">survived</th></tr></thead>\n<tbody><tr><td>a01</td><td class=\"num\">0</td><td class=\"num\">5</td><td class=\"num\">5</td><td class=\"num\">75</td><td class=\"num\">16.62%</td><td class=\"num\">189.9</td></tr><tr><td>a02</td><td class=\"num\">0.3</td><td class=\"num\">0.55</td><td class=\"num\">5.83</td><td class=\"num\">92</td><td class=\"num\">18.98%</td><td class=\"num\">187.9</td></tr><tr><td>a03</td><td class=\"num\">0.5</td><td class=\"num\">0.12</td><td class=\"num\">4.61</td><td class=\"num\">105</td><td class=\"num\">17.29%</td><td class=\"num\">186.9</td></tr><tr><td>a04</td><td class=\"num\">0.7</td><td class=\"num\">0.029</td><td class=\"num\">3.44</td><td class=\"num\">119</td><td class=\"num\">17.62%</td><td class=\"num\">186.7</td></tr><tr><td>a05</td><td class=\"num\">0.9</td><td class=\"num\">0.0079</td><td class=\"num\">2.55</td><td class=\"num\">133</td><td class=\"num\">17.82%</td><td class=\"num\">184.1</td></tr><tr><td>a06 <span class=\"sub\">off-trend</span></td><td class=\"num\">1</td><td class=\"num\">0.01</td><td class=\"num\">5.12</td><td class=\"num\">328</td><td class=\"num\">18.73%</td><td class=\"num\">186.9</td></tr><tr><td>a07</td><td class=\"num\">1.2</td><td class=\"num\">0.0014</td><td class=\"num\">1.69</td><td class=\"num\">160</td><td class=\"num\">18.64%</td><td class=\"num\">182.3</td></tr><tr><td>a08</td><td class=\"num\">1.5</td><td class=\"num\">0.00028</td><td class=\"num\">1.07</td><td class=\"num\">174</td><td class=\"num\">17.13%</td><td class=\"num\">180.3</td></tr><tr><td>a09</td><td class=\"num\">2</td><td class=\"num\">2.9e-05</td><td class=\"num\">0.571</td><td class=\"num\">208</td><td class=\"num\">18.96%</td><td class=\"num\">184.6</td></tr><tr><td>a10</td><td class=\"num\">2.7</td><td class=\"num\">2.1e-06</td><td class=\"num\">0.273</td><td class=\"num\">259</td><td class=\"num\">18.75%</td><td class=\"num\">183.2</td></tr></tbody></table></div>\n<div class=\"note\"><strong>So nothing here can be credited to the accel rate alone.</strong> The base rate was evidently re-tuned for each setting to keep total healing over a long rest in the same range, so the two are confounded by construction. It is one conceptual dial implemented with two keys &mdash; which is why Figure&nbsp;16 shades by the accel rate but the section below declines to credit it. a06 is also slightly off the trend: its base rate, 0.01, is larger than a05&rsquo;s 0.0079 where every other step decreases.</div>\n</div>\n")

# ---- Section 7 -------------------------------------------------------------------------------
# The page says the ten agents are "identical except for one dial" and "differing in one setting".
# Diffing their saved configs leaf by leaf (244 keys) says TWO body settings differ:
#   body.recovery_accel_rate  0.0 0.3 0.5 0.7 0.9 1.0 1.2 1.5 2.0 2.7
#   body.recovery_base_rate   5.0 .55 .12 .029 .0079 .01 .0014 .00028 2.9e-5 2.1e-6
# plus `tag` and `wandb.name`, which are naming only. Healing is
# `base_rate * (1+accel_rate)**(streak-1)` (core.py:207), so the two are a single design axis --
# how back-loaded resting's payoff is -- implemented with two knobs that were co-tuned. The claim
# "one setting" is therefore wrong as written, and it matters: it is a second reason the accel
# rate cannot be credited, which the section's own "ruled out" list does not mention.
# Values are literals because they come from ten immutable saved configs under results/, which is
# gitignored and absent on a fresh clone; the derivation is the diff described above.
FIXES += [
    ("section 7: two settings differ, not one",
     "We trained ten, identical except for one dial &mdash; how much extra healing they earn for\n"
     "<em>continuing</em> to rest &mdash; and dropped all ten through the <em>same</em> million worlds.",
     "We trained ten that differ in how much extra healing they earn for <em>continuing</em> to "
     "rest, and dropped all ten through the <em>same</em> million worlds."),

    ("section 7: the ten agents, side by side",
     '<div class="motive"><b>Why this analysis</b>Every result up to here comes from one trained agent.',
     PANEL_ARMS +
     '<div class="motive"><b>Why this analysis</b>Every result up to here comes from one trained agent.'),
]

if __name__ == "__main__":
    main()
