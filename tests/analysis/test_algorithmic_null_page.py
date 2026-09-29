"""The "What Both Agents Compute" page builder's figure checks (guide 2.7, 11a-c; tooling plan
File Changes 10, Checkpoint 3.4) and the an0N figure scripts' verdict-word policy.

The builder is run on a COPY of the template and of the page's figure folder, never on the real
page. Four figures are the real ones in docs/.../figures/algorithmic_null/ (skipped if absent); the
robustness and wake-up figures are drawn from synthetic inputs (tests/analysis/an_page_synthetic.py),
so every build here is a --preview build, except the one that checks a normal build refuses them.
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MC = os.path.join(ROOT, "scripts/analysis/studies/modulator_clues")
DOC = os.path.join(ROOT, "docs/experiments/active/modulator_clues")
REAL_FIGS = os.path.join(DOC, "figures/algorithmic_null")
PY = sys.executable
REAL = ("an01_similarity_layers", "an02_decoding_profiles", "an03_seed_yardstick", "an06_pilot_controls")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, MC)
import an_page_synthetic as S                                               # noqa: E402


def _builder():
    spec = importlib.util.spec_from_file_location("build_an_page",
                                                  os.path.join(MC, "build_algorithmic_null_page.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def figset(tmp_path_factory):
    for stem in REAL:
        if not os.path.exists(os.path.join(REAL_FIGS, f"{stem}.png")):
            pytest.skip(f"real figure {stem} not drawn (its driver output is gitignored)")
    base = tmp_path_factory.mktemp("figset")
    src = base / "src"
    figs = base / "figs"
    figs.mkdir()
    for stem in REAL:
        for ext in ("png", "svg", "pdf", "data.txt"):
            shutil.copy(os.path.join(REAL_FIGS, f"{stem}.{ext}"), figs)
    rob = S.write_robustness(str(src / "rob"))
    wake = S.write_wakeup(str(src / "wake"))
    for script, source in (("an04_similarity_robustness", rob), ("an05_wakeup", wake)):
        r = subprocess.run([PY, os.path.join(MC, f"{script}.py"), "--source", source,
                            "--out", str(figs)], capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, r.stdout + r.stderr
    return figs


@pytest.fixture
def page(tmp_path, figset):
    """A private copy: <tmp>/figures/algorithmic_null/ (the page's subfolder) and a template."""
    figs = tmp_path / "figures" / "algorithmic_null"
    shutil.copytree(figset, figs)
    tpl = tmp_path / "page.template.html"
    shutil.copy(os.path.join(DOC, "algorithmic_null.template.html"), tpl)
    return {"figs": figs, "tpl": tpl, "out": tmp_path / "page.html", "root": tmp_path}


def build(p, *extra, preview=True):
    argv = ["--template", str(p["tpl"]), "--figures", str(p["figs"]), "--out", str(p["out"])]
    return _builder().main(argv + (["--preview"] if preview else []) + list(extra))


def refused(p, match, **kw):
    with pytest.raises(SystemExit) as e:
        build(p, **kw)
    assert re.search(match, str(e.value)), str(e.value)


def edit_template(p, old, new, count=1):
    t = p["tpl"].read_text()
    assert old in t, old
    p["tpl"].write_text(t.replace(old, new, count))


# ------------------------------------------------------------------------ builder -----------
def test_preview_builds_with_all_six_figures(page):
    build(page)
    html = page["out"].read_text()
    assert html.count('<img data-fig="an0') == 6
    assert html.count('src="data:image/png;base64,') == 6
    assert 'id="lb"' in html and "full-size figure viewer" in html          # guide 2.6
    assert html.count("function updateCues()") == 1
    assert "Local preview" in html and "TEST INPUT" in html


def test_normal_build_refuses_test_input_figures(page):
    refused(page, r"TEST INPUT", preview=False)


def test_preview_refuses_an_output_under_docs(page):
    page["out"] = os.path.join(DOC, "zz_preview.html")
    refused(page, r"outside docs/")
    assert not os.path.exists(page["out"])


def test_missing_axes_sentence_is_refused(page):
    edit_template(page, "<b>Axes.</b> Small panels", "Small panels")
    refused(page, r"an05_wakeup: caption has no <b>Axes.</b>")


def test_short_howto_is_refused(page):
    t = page["tpl"].read_text()
    blk = re.search(r'<figure>\s*<img data-fig="an02_decoding_profiles".*?</figure>', t, re.S).group(0)
    para = re.search(r'<p class="eyebrow">How it is computed</p>\s*<p>(.*?)</p>', blk, re.S).group(1)
    short = " ".join(para.split()[:120])
    page["tpl"].write_text(t.replace(para, short, 1))
    refused(page, r"an02_decoding_profiles: 'How it is computed' is 120 words")


def test_wrong_howto_eyebrow_is_refused(page):
    edit_template(page, '<p class="eyebrow">How it is computed</p>', '<p class="eyebrow">How it is drawn</p>')
    refused(page, r"eyebrow must read exactly")


def test_inline_svg_is_refused(page):
    edit_template(page, '<p class="zoomhint">', '<svg width="4"></svg><p class="zoomhint">')
    refused(page, r"inline <svg>")


def test_stray_file_in_the_page_subfolder_is_refused(page):
    (page["figs"] / "an09_x.png").write_bytes(b"x")
    refused(page, r"never shows: \['an09_x.png'\]")


def test_stray_file_in_the_parent_folder_is_ignored(page):
    (page["root"] / "figures" / "zz_other.png").write_bytes(b"x")
    build(page)


def test_missing_figure_file_is_refused(page):
    (page["figs"] / "an03_seed_yardstick.svg").unlink()
    refused(page, r"an03_seed_yardstick: no svg")


def test_unregistered_rules_sha_is_refused(page):
    f = page["figs"] / "an01_similarity_layers.data.txt"
    t = f.read_text()
    f.write_text(re.sub(r"(decision_rules: \S+ )[0-9a-f]{64}", r"\g<1>" + "0" * 64, t))
    refused(page, r"an01_similarity_layers: rules sha 000000000000 is neither")


def test_missing_rules_line_is_refused(page):
    f = page["figs"] / "an02_decoding_profiles.data.txt"
    f.write_text("\n".join(l for l in f.read_text().splitlines() if not l.startswith("decision_rules")))
    refused(page, r"no decision_rules line")


def test_data_statement_without_rows_is_refused(page):
    f = page["figs"] / "an06_pilot_controls.data.txt"
    f.write_text("\n".join(l for l in f.read_text().splitlines() if not l.startswith("row: ")))
    refused(page, r"used / available rows")


def test_house_class_collision_is_refused(page):
    edit_template(page, ".plan { border", ".howto { color:red; }\n.plan { border")
    refused(page, r"F54")


# ------------------------------------------------------------------------ figures -----------
def test_pilot_figure_states_no_verdict_and_its_label():
    f = os.path.join(REAL_FIGS, "an06_pilot_controls.data.txt")
    if not os.path.exists(f):
        pytest.skip("pilot figure not drawn")
    t = open(f).read()
    assert "no verdict is drawn" in t
    assert "tool validation" in t and "not evidence" in t


def test_verdict_refused_for_the_pilot_and_without_prefix():
    import _an_common as C
    pilot = {"evidence_status": "pilot", "verdict_words_allowed": False}
    with pytest.raises(SystemExit):
        C.verdict(pilot, "different")
    interim = {"evidence_status": "interim", "verdict_words_allowed": True,
               "verdict_prefix": "provisional — end of stage 1 of 5"}
    with pytest.raises(SystemExit):
        C.verdict(interim, "different")
    assert C.verdict(interim, "provisional — end of stage 1 of 5: different").endswith("different")
    assert "no reading" in C.verdict(interim, "provisional — end of stage 1 of 5: x", test=True)


def test_test_input_figure_is_refused_the_page_folder(tmp_path):
    rob = S.write_robustness(str(tmp_path))
    r = subprocess.run([PY, os.path.join(MC, "an04_similarity_robustness.py"), "--source", rob],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "TEST INPUT" in (r.stdout + r.stderr)


def test_rules_note_refuses_an_unregistered_sha():
    import _an_common as C
    with pytest.raises(SystemExit):
        C.rules_note({"decision_rules": {"sha256": "f" * 64}})
