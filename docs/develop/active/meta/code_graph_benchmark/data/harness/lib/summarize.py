"""summarize.py [trial-filter] — per-arm and per-task×arm tables from runs/*/score.json (smoke runs excluded)."""
import glob, json, os, statistics, sys, collections

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []
for f in glob.glob(f"{B}/runs/*/score.json"):
    try:
        d = json.load(open(f))
    except ValueError:
        continue
    t, a, k = d["run"].split("-")
    if k == "smoke" or (len(sys.argv) > 1 and k not in sys.argv[1].split(",")):
        continue
    d.update(arm=a, trial=k)
    d["total_in"] = (d["input_tokens"] or 0) + (d["cache_read"] or 0) + (d["cache_write"] or 0)
    rows.append(d)

def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None

print(f"{len(rows)} graded runs\n")
print(f"{'arm':4} {'n':>3} {'correct':>8} {'P2P broke':>9} {'recall':>6} {'med wall s':>10} {'med turns':>9} {'med tools':>9} "
      f"{'med in-tok':>11} {'med out-tok':>11} {'med pre-edit calls':>18}")
for a in "AGF":
    r = [d for d in rows if d["arm"] == a]
    if not r:
        continue
    pre = [d["first_edit"]["tool_calls_before"] for d in r if d.get("first_edit")]
    print(f"{a:4} {len(r):>3} {sum(d['correct'] for d in r):>4}/{len(r):<3} {sum(d['p2p_broken'] > 0 for d in r):>9} "
          f"{statistics.mean(d['ref_recall'] for d in r):>6.2f} {med([d['wall_s'] for d in r]):>10} {med([d['turns'] for d in r]):>9} "
          f"{med([d['tool_calls'] for d in r]):>9} {med([d['total_in'] for d in r]):>11,.0f} {med([d['output_tokens'] for d in r]):>11,.0f} "
          f"{str(med(pre)):>18}")
print("\nper task (correct/n · median wall s · median total input tokens)")
by = collections.defaultdict(list)
for d in rows:
    by[(d["task"], d["arm"])].append(d)
for t in sorted({d["task"] for d in rows}):
    cells = []
    for a in "AGF":
        r = by.get((t, a), [])
        cells.append(f"{a}: {sum(x['correct'] for x in r)}/{len(r)} {med([x['wall_s'] for x in r]) or '-':>5}s {med([x['total_in'] for x in r]) or 0:>10,.0f}" if r else f"{a}: -")
    print(f"{t}  " + "   ".join(cells))
