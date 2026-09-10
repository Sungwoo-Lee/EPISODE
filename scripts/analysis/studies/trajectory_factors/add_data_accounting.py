#!/usr/bin/env python3
"""add_data_accounting.py - give every figure on the a01 page a "Data behind this figure" block.

WHY. The artifact guide's standing requirement is that every figure declares how much data it used
- used / available / share, per subset, with the reason for the subset. The sensor-ladder page does
this with a `<details class="samples">` disclosure whose rows the figure scripts emit. This page was
written before that rule and states its subsets only in prose, inconsistently: of its 22 figures,
eight said nothing at all about their population.

The counts are NOT invented here. Each one is either read out of the page's own embedded data
object `D`, or taken from the figure's own method block, which already states it in prose - and the
two are cross-checked against each other wherever both exist. A figure whose population genuinely
was never recorded says so, in the row, rather than being given a plausible number.

Everything is derived from a handful of totals that are themselves checked on load:

  1,000,000   episodes collected           (sum of the per-bin counts for predator count)
  189,906,610 action steps in those        (Figure 10's method block; cross-checked against the
                                            mean episode length that Figure 13's counts imply)
    333,743   with exactly one predator    (the middle bin of predator count)
    333,766   with exactly one rabbit      (the middle bin of rabbit count)
    111,211   with exactly one of each     (Figure 9's method block)
 10,779,288   moments damage was taken     (the page's own "cover genuinely works" panel)
"""
from __future__ import annotations
import json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "..", ".."))
os.chdir(ROOT)
PAGE = "docs/experiments/active/trajectory_factors/a01_hiding_drivers.html"
MARKER = 'class="samples"'


def fail(msg):
    raise SystemExit(f"add_data_accounting: {msg}")


def totals(html, D):
    C = D["curves"]
    ep = sum(C["predator count"]["n"])
    if ep != 1_000_000:
        fail(f"the episode total is {ep:,}, not the 1,000,000 the page claims throughout")
    steps = 189_906_610                                   # Figure 10's method block, verbatim
    if f"{steps:,}" not in html:
        fail("the page no longer states 189,906,610 action steps; the total must be re-sourced")
    implied = sum(sum(r) for r in D["timectrl"]["inj_n"]) * ep
    if abs(implied - steps) / steps > 0.005:
        fail(f"Figure 13's binned counts imply {implied:,.0f} steps but Figure 10 states "
             f"{steps:,} - these must agree before either is printed")
    one_each = 111_211
    if f"{one_each:,}" not in html:
        fail("the page no longer states the 111,211 one-predator-one-rabbit episodes")
    dmg = 10_779_288
    if f"{dmg:,}" not in html:
        fail("the page no longer states the 10,779,288 damage moments")
    return {"ep": ep, "steps": steps, "one_pred": C["predator count"]["n"][1],
            "one_rab": C["rabbit count"]["n"][1], "one_each": one_each, "dmg": dmg,
            # step subsets, from each figure's own binned counts (steps per episode x episodes)
            # Rounded to the nearest hundred thousand ON PURPOSE. They are reconstructed from
            # per-cell counts the page stores as steps-per-episode to 2dp, so printing them to the
            # unit would claim a precision the stored data does not carry.
            "hits": int(round(sum(sum(r) for r in D["hits"]["n"]) * ep, -5)),
            "lethal": int(round(sum(D["lethal"]["n"]) * ep, -5))}


NR = "not recorded"          # a population the page genuinely never wrote down


def rows_for(D, T):
    """(what, used, available, why) per figure number. Sourced, never guessed."""
    C, ep, st = D["curves"], T["ep"], T["steps"]
    pred, rab, both = T["one_pred"], T["one_rab"], T["one_each"]
    trait_why = ("a predator trait is undefined when no predator is present and ambiguous when "
                 "two are, so only the exactly-one-predator episodes can be used")
    all_why = "defined in every episode, so nothing has to be dropped"
    A = {}
    A[1] = [("episodes replayed to check the sensors", 25, ep,
             "this figure is read from the run's saved config.yaml rather than measured, so the "
             "only data behind it is the replay that confirms today's code reproduces those "
             "sensors: 25 episodes, 5,298 steps, agreeing to 2.4e-07 across all 27 channels")]
    A[2] = [("factors defined in every episode", ep, ep, all_why),
            ("predator traits", pred, ep, trait_why),
            ("rabbit odour terms", rab, ep,
             "the same problem one animal along: a rabbit's smell needs exactly one rabbit")]
    A[3] = [(f"panel: {k}", sum(v["n"]), ep,
             trait_why if sum(v["n"]) == pred else
             ("needs exactly one rabbit" if sum(v["n"]) == rab else all_why))
            for k, v in C.items()]
    A[4] = [("episodes with exactly one predator", pred, ep, trait_why)]
    A[5] = [("the four predator traits", pred, ep, trait_why),
            ("predator count, bushes available, hiding predators", ep, ep, all_why)]
    A[6] = list(A[5])
    A[7] = [("predator smell ladder", pred, ep, trait_why),
            ("rabbit smell ladder", rab, ep, "needs exactly one rabbit, for the same reason")]
    A[8] = [("rabbit smell, every endpoint", rab, ep,
             "one rabbit, so the smell that was rolled is the smell the agent met")]
    A[9] = [("exactly one predator AND one rabbit", both, ep,
             "holds the predator context fixed while the rabbit's draw varies, which is what "
             "separates a targeted false alarm from general jumpiness")]
    A[10] = [("action steps, unconditioned", st, st,
              "every step counts; the lag is within an episode, so only the boundary steps drop")]
    A[11] = [("moments damage was taken", T["dmg"], st,
              "the figure aligns on damage, so a step with none is not an event"),
             ("of those, the isolated subset", NR, T["dmg"],
              "the count of events with no other damage within the window was never written into "
              "the page; the figure draws the subset but did not record its size")]
    A[12] = [("steps with no predator within 2 tiles", T["hits"], st,
              "current proximity is exactly what this figure holds constant, so steps with a "
              "predator nearby must be excluded. Reconstructed from the figure's own per-cell "
              "counts and so rounded to the nearest hundred thousand")]
    A[13] = [("action steps", st, st, "no conditioning; every step falls in some cell")]
    A[14] = [("steps with no predator within 2 tiles", T["lethal"], st,
              "the same exclusion as Figure 12, reconstructed and rounded the same way")]
    A[15] = [("action steps", st, st, "no conditioning; every step falls in some cell")]
    A[16] = [("episodes, per agent", ep, ep,
              "each of the ten agents replays the identical 1,000,000 world draws, so a "
              "difference between dots is the agent and never the world"),
             ("episodes across all ten agents", ep * 10, ep * 10, "ten agents x one million")]
    A[17] = [("(agent, world) outcomes", ep * 10, ep * 10,
              "the complete table rather than a sample: both policy and world are deterministic "
              "given the pair, so it decomposes with no residual term")]
    A[18] = [("action steps, per agent", st, st,
              "unconditioned, so this is the raw shape rather than the proximity-controlled one"),
             ("agents", 10, 10, "all ten arms of the rest-premium sweep")]
    A[19] = [("agents, as four matched pairs", 8, 8,
              "all eight of the modulator runs. Note these are a DIFFERENT population from the ten "
              "rest-premium arms of Figures 16-18, not a subset of them: within a pair the two "
              "runs differ only in the seven modulation keys, and both are replayed at a "
              "step-matched checkpoint over the same million worlds")]
    A[20] = list(A[19])
    return A


def ctx_rows(D, T):
    """Figures 21 and 22 read the randomised-injury slice, so their population is that slice."""
    keys = [k for k in D["ctx"] if k.endswith("_felt_pain")]
    rand = {k: sum(r["n_calm"] + r["n_threat"] for r in D["ctx"][k]["rows_rand"]) for k in keys}
    obs = {k: sum(r["n_calm"] + r["n_threat"] for r in D["ctx"][k]["rows_obs"]) for k in keys}
    lo, hi = int(min(rand.values())), int(max(rand.values()))
    spread = f"{lo:,} to {hi:,} depending on the agent" if lo != hi else f"{lo:,}"
    return [("steps in the randomised-injury slice, per agent", lo, int(max(obs.values())),
             "these two figures use the CAUSAL version: injury assigned by the world at episode "
             "start, first 25 steps only. The available column is the observational slice - "
             "binning by the agent's own current nociception - which is kept apart because it "
             f"disagrees in sign. Across the eight agents the used figure runs {spread}; the "
             "smallest is shown so the share is not flattered"),
            ("agents", 8, 8, "four matched pairs, modulated against unmodulated")]


CSS = """
/* Data accounting, one per figure. Same disclosure the sensor-ladder page uses, in this page's
   own tokens. Closed by default: it is provenance a reader should be able to reach, not read.
   NOTE the alignment rules below are not optional. This page sets `th,td{text-align:right}`
   globally and left-aligns only the FIRST cell, so without an override the prose column of this
   table renders right-aligned and its header is pushed out of the visible area. */
.samples{margin:.9rem 0 0;border:1px solid var(--rule);border-radius:3px;background:var(--panel2)}
.samples summary{cursor:pointer;padding:.5rem .7rem;font-family:var(--mono);font-size:.68rem;
  letter-spacing:.06em;text-transform:uppercase;color:var(--muted);list-style:none}
.samples summary::-webkit-details-marker{display:none}
.samples summary::before{content:'\\25B8\\00a0\\00a0';color:var(--cover)}
.samples[open] summary::before{content:'\\25BE\\00a0\\00a0'}
.samples summary:hover{color:var(--fg)}
.samples .sbox{overflow-x:auto;border-top:1px solid var(--rule)}
/* fixed layout + width:100% makes the prose column WRAP rather than push the table wider than
   its box; only genuinely long single tokens can then cause a scroll. */
/* NOT `table-layout:fixed` with percentage columns. Under fixed layout a `nowrap` cell whose
   content exceeds its column neither wraps nor widens it - it paints straight into the next cell,
   and at the 500px floor this fused three numbers into one string ("16,969,747186,754,1439.1%").
   Auto layout lets each numeric column take the width its widest value actually needs; only the
   prose column is given a floor, and it is the one column allowed to wrap. */
/* NOT `table-layout:fixed` with percentage columns. Under fixed layout a `nowrap` cell whose
   content exceeds its column neither wraps nor widens it - it paints straight into the next cell,
   and at the 500px floor that fused three numbers into one string ("16,969,747186,754,1439.1%").
   Auto layout lets each numeric column take the width its widest value needs; only the prose
   column carries a floor, and it is the only column allowed to wrap. */
.samples table{font-size:.75rem;width:100%}
.samples th,.samples td{padding:.34rem .6rem;vertical-align:top;text-align:right;
  white-space:nowrap}
.samples td.txt,.samples th.txt{text-align:left;white-space:normal;overflow-wrap:anywhere;
  min-width:13rem}
.samples thead th{font-size:.62rem;color:var(--muted)}
.samples tbody tr:last-child td{border-bottom:0}
"""


def block(rows):
    def num(v):
        return f"{v:,}" if isinstance(v, int) else str(v)
    body = ""
    for what, used, total, why in rows:
        if isinstance(used, int) and isinstance(total, int) and total:
            share = f"{used / total * 100:.1f}%"
        else:
            share = "&mdash;"
        body += (f'<tr><td class="txt">{what}</td><td>{num(used)}</td><td>{num(total)}</td>'
                 f'<td>{share}</td><td class="txt">{why}</td></tr>')
    # The summary must speak for the WHOLE figure, and only about ONE population. Taking row 0
    # let a fifteen-panel figure advertise its first panel; ranging over every row put an agent
    # count and a step count into one span ("10 to 189,906,610"). Use the rows that share the
    # largest denominator - that is the figure's population; the rest are other dimensions of it.
    ints = [(u, t) for _, u, t, _ in rows if isinstance(u, int) and isinstance(t, int) and t]
    if ints:
        t = max(t for _, t in ints)
        used = [u for u, tt in ints if tt == t]
        lo, hi = min(used), max(used)
        cap = (f"{lo:,} of {t:,} ({lo / t * 100:.1f}%)" if lo == hi
               else f"{len(used)} subsets, {lo:,} to {hi:,} of {t:,}")
    else:
        cap = f"{rows[0][1]} of {rows[0][2]}"
    return ('<details class="samples"><summary>Data behind this figure &mdash; '
            f'{cap}</summary><div class="sbox"><table><thead><tr>'
            '<th class="txt">what</th><th>used</th><th>available</th><th>share</th>'
            '<th class="txt">why this subset</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div></details>')


def main():
    write = "--write" in sys.argv
    html = open(PAGE, encoding="utf-8").read()
    if MARKER in html:
        fail("the page already carries data-accounting blocks")
    D = json.loads(re.search(r"const D=(\{.*?\});\n", html, re.S).group(1))
    T = totals(html, D)
    print(f"  totals check passed: {T['ep']:,} episodes, {T['steps']:,} action steps")
    A = rows_for(D, T)
    A[21] = A[22] = ctx_rows(D, T)

    figs = re.findall(r'class="fignum">Figure\s+(\d+)', html)
    nums = sorted(int(n) for n in figs)
    missing = [n for n in nums if n not in A]
    if missing:
        fail(f"no data accounting defined for figure(s) {missing} - every figure must declare "
             f"its population, so this is a hard error rather than a skipped block")

    def add(m):
        n = int(re.search(r'class="fignum">Figure\s+(\d+)', m.group(0)).group(1))
        return m.group(0)[:-len("</figure>")] + block(A[n]) + "\n</figure>"

    out = re.sub(r'<figure class="panel[^"]*">(?:(?!</figure>).)*?</figure>',
                 lambda m: add(m) if 'class="fignum"' in m.group(0) else m.group(0),
                 html, flags=re.S)

    anchor = "td.num{font-family:var(--mono);font-size:.83rem}"
    if out.count(anchor) != 1:
        fail("could not find the stylesheet anchor for the .samples rules")
    out = out.replace(anchor, anchor + CSS)

    got = out.count(MARKER)
    if got != len(nums):
        fail(f"{got} accounting blocks for {len(nums)} figures - every figure must get exactly one")
    print(f"  {got} blocks, one per figure, {len(nums)} figures")
    if not write:
        print("  DRY RUN - pass --write to apply")
        return
    open(PAGE, "w", encoding="utf-8").write(out)
    print(f"  wrote {PAGE} ({len(out):,} chars, was {len(html):,})")


if __name__ == "__main__":
    main()
