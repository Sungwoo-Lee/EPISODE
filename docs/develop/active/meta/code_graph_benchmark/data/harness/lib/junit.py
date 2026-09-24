"""junit.py — read pytest JUnit XML into {test_id: outcome}; outcome in passed/failed/error/skipped."""
import sys
import xml.etree.ElementTree as ET


def outcomes(path):
    try:
        root = ET.parse(path).getroot()
    except (FileNotFoundError, ET.ParseError):
        return {}
    res = {}
    for tc in root.iter("testcase"):
        tid = f"{tc.get('classname', '')}::{tc.get('name', '')}"
        kids = {c.tag for c in tc}
        if "failure" in kids:
            res[tid] = "failed"
        elif "error" in kids:
            res[tid] = "error"
        elif "skipped" in kids:
            res[tid] = "skipped"
        else:
            res[tid] = "passed"
    return res


def split(before, after, hidden_modules):
    """F2P = tests in hidden modules passing after and not passing before (or absent before);
    P2P = tests passing both before and after (any module in the run)."""
    def in_hidden(tid):
        return any(tid.startswith(m) for m in hidden_modules)
    f2p = sorted(t for t, o in after.items() if o == "passed" and in_hidden(t) and before.get(t) != "passed")
    p2p = sorted(t for t, o in after.items() if o == "passed" and before.get(t) == "passed")
    return f2p, p2p


if __name__ == "__main__":
    o = outcomes(sys.argv[1])
    from collections import Counter
    print(len(o), dict(Counter(o.values())))
