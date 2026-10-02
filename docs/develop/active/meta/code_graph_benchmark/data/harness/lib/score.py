"""score.py <task> <run_dir> -> JSON: correctness, P2P breakage, reference-set recall, tokens, tool use."""
import json, os, subprocess, sys, collections
sys.path.insert(0, os.path.dirname(__file__)); from junit import outcomes
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = "/media/nas01/projects/Interoceptive-AI/grid_world_pain"
t, run = sys.argv[1], sys.argv[2]
g = json.load(open(f"{B}/grading.json"))[t]
res = outcomes(f"{run}/grade.xml")
f2p_ok = [x for x in g["F2P"] if res.get(x) == "passed"]
p2p_broken = [x for x in g["P2P"] if res.get(x) != "passed"]
ref = [f for f in subprocess.run(["git", "-C", R, "show", "--name-only", "--format=", g["commit"]], capture_output=True, text=True).stdout.split()
       if not f.startswith(("tests/", "docs/"))]
changed = set(open(f"{run}/changed_files.txt").read().split()) if os.path.exists(f"{run}/changed_files.txt") else set()
tools, first_edit, t0, result, n_tool = collections.Counter(), None, None, {}, 0
for line in open(f"{run}/stream.tsv"):
    ts, _, js = line.partition("\t")
    try: ev = json.loads(js)
    except ValueError: continue
    t0 = t0 or int(ts)
    if ev.get("type") == "assistant":
        for blk in ev.get("message", {}).get("content", []):
            if blk.get("type") == "tool_use":
                n_tool += 1; tools[blk["name"]] += 1
                if first_edit is None and blk["name"] in ("Edit", "Write", "MultiEdit"):
                    first_edit = {"tool_calls_before": n_tool - 1, "seconds": int(ts) - t0}
    if ev.get("type") == "result": result = ev
u = result.get("usage", {})
print(json.dumps({
    "task": t, "run": os.path.basename(run),
    "correct": len(f2p_ok) == len(g["F2P"]) and len(g["F2P"]) > 0,
    "f2p_passed": f"{len(f2p_ok)}/{len(g['F2P'])}", "p2p_broken": len(p2p_broken), "p2p_total": len(g["P2P"]),
    "ref_recall": round(len([f for f in ref if f in changed]) / len(ref), 2) if ref else None,
    "ref_files": ref, "changed_files": sorted(changed),
    "wall_s": int(open(f"{run}/wall_s").read()), "turns": result.get("num_turns"),
    "input_tokens": u.get("input_tokens"), "cache_read": u.get("cache_read_input_tokens"),
    "cache_write": u.get("cache_creation_input_tokens"), "output_tokens": u.get("output_tokens"),
    "usd_equiv": result.get("total_cost_usd"), "is_error": result.get("is_error"), "subtype": result.get("subtype"),
    "tool_calls": n_tool, "tools": dict(tools), "first_edit": first_edit}, indent=1))
