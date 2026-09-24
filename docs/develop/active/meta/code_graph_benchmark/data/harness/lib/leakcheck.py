"""leakcheck.py <commit> <before_snapshot_dir>: new identifiers the commit introduces, and every
file in the before-snapshot that already mentions one (outside the files the commit edits)."""
import re, subprocess, sys, collections, os
R = "/media/nas01/projects/Interoceptive-AI/grid_world_pain"
h, snap = sys.argv[1], sys.argv[2]
diff = subprocess.run(["git", "-C", R, "show", "--format=", "-U0", h, "--", "src", "scripts", "train.py", "configs"],
                      capture_output=True, text=True, timeout=300).stdout
edited = set(subprocess.run(["git", "-C", R, "show", "--name-only", "--format=", h], capture_output=True, text=True).stdout.split())
TOK = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{5,}\b")
added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
removed = {t for l in diff.splitlines() if l.startswith("-") and not l.startswith("---") for t in TOK.findall(l)}
cand = {t for l in added for t in TOK.findall(l) if ("_" in t or t.isupper()) and t not in removed}
def grep(t, paths):
    r = subprocess.run(["grep", "-rlw", "--binary-files=without-match", t, *paths], cwd=snap, capture_output=True, text=True)
    return [p[2:] if p.startswith("./") else p for p in r.stdout.split()]
code = [p for p in ("src", "scripts", "tests", "train.py", "configs") if os.path.exists(os.path.join(snap, p))]
new = sorted(t for t in cand if not grep(t, code))
leaks = collections.defaultdict(set)
for t in new:
    for f in grep(t, ["."]):
        if f not in edited: leaks[f].add(t)
print(f"== {h}: {len(new)} new identifiers: {', '.join(new[:14])}{' ...' if len(new) > 14 else ''}")
for f, ts in sorted(leaks.items(), key=lambda x: -len(x[1])): print(f"   LEAK {f}: {', '.join(sorted(ts)[:6])}")
if not leaks: print("   no leaks")
