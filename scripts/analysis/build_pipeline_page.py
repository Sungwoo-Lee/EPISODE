#!/usr/bin/env python3
"""build_pipeline_page.py - assemble the analysis-pipeline page from the code it documents.

WHY A BUILDER. This page's whole claim is "every code block is copied verbatim from the file it
names, so you can open any of them and find what you see here". Pasted by hand, that claim decays
the first time somebody edits a module: the excerpt is still there, still plausible, and no longer
what the file says. Here the excerpts are pulled from the tree at build time by line range, and the
line numbers printed under each block are the ones the extraction used - so a reference cannot be
stale without the build also being stale.

TOKENS the template may use:
    {{CODE:path#12-30}}     the lines, syntax-highlighted, with a `path · lines 12-30` caption
    {{CODE:path#func}}      the whole of a named def/class, lines resolved by parsing the file
    {{LC:path}}             that file's line count, so "107 lines" in the prose stays true
    {{SHA}}                 the short commit the page was built from

FAILS LOUDLY on: a path that does not exist, a line range past the end of the file, a named
function that is not in the file, an empty excerpt, and any token left unsubstituted.

Highlighting emits pygments' SEMANTIC classes (.k keyword, .s string, .c comment, ...) and never a
colour, because the page has a dark theme and a fixed palette baked into the markup would be
unreadable in half of it. The colours live in the template's CSS, per theme.
"""
from __future__ import annotations
import ast
import html
import os
import re
import subprocess
import sys

from pygments import highlight
from pygments.lexers import PythonLexer, BashLexer
from pygments.formatters import HtmlFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
os.chdir(ROOT)

TEMPLATE = "scripts/analysis/pipeline_layout.template.html"
OUT = "scripts/analysis/pipeline_layout.html"
FMT = HtmlFormatter(nowrap=True, classprefix="")


def fail(msg: str):
    sys.exit(f"build_pipeline_page: {msg}")


def _lines(path: str) -> list[str]:
    if not os.path.exists(path):
        fail(f"{path}: no such file - the page names a module that is not in the tree")
    return open(path).read().splitlines()


def _resolve_named(path: str, name: str) -> tuple[int, int]:
    """Line range of a top-level def/class, or of `Class.method`."""
    tree = ast.parse(open(path).read())
    target, cls = (name.split(".", 1)[1], name.split(".", 1)[0]) if "." in name else (name, None)
    for node in ast.walk(tree) if cls else tree.body:
        if cls and isinstance(node, ast.ClassDef) and node.name == cls:
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == target:
                    return m.lineno, m.end_lineno
        if not cls and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                and node.name == target:
            return node.lineno, node.end_lineno
    fail(f"{path}: no top-level `{name}` to quote")


def code_block(spec: str) -> str:
    path, _, sel = spec.partition("#")
    src = _lines(path)
    if re.fullmatch(r"\d+-\d+", sel):
        a, b = (int(x) for x in sel.split("-"))
    elif sel:
        a, b = _resolve_named(path, sel)
    else:
        a, b = 1, len(src)
    if b > len(src):
        fail(f"{path}: asked for line {b} but the file has {len(src)}")
    body = "\n".join(src[a - 1:b])
    if not body.strip():
        fail(f"{path}#{sel}: the excerpt is empty")
    # dedent so a snippet lifted from inside a function does not sit in a gutter of whitespace
    pad = min((len(l) - len(l.lstrip()) for l in body.splitlines() if l.strip()), default=0)
    body = "\n".join(l[pad:] if len(l) >= pad else l for l in body.splitlines())
    lexer = BashLexer() if path.endswith(".sh") else PythonLexer()
    hl = highlight(body, lexer, FMT).rstrip("\n")
    ref = f"{path} &middot; line{'s' if b > a else ''} {a}{f'&ndash;{b}' if b > a else ''}"
    return (f'<figure class="code">\n<pre class="hl"><code>{hl}</code></pre>\n'
            f'<figcaption class="srcref">{ref}</figcaption>\n</figure>')


def main():
    page = open(TEMPLATE).read()

    for spec in dict.fromkeys(re.findall(r"\{\{CODE:([^}]+)\}\}", page)):
        page = page.replace(f"{{{{CODE:{spec}}}}}", code_block(spec))
    for path in dict.fromkeys(re.findall(r"\{\{LC:([^}]+)\}\}", page)):
        page = page.replace(f"{{{{LC:{path}}}}}", str(len(_lines(path))))
    if "{{SHA}}" in page:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip() or "unknown"
        page = page.replace("{{SHA}}", sha)

    # Literal blocks written in the template (shell sessions, invented examples) are highlighted
    # in place. They have no file to be pulled from, so they carry no line reference -- which is
    # the honest signal that they are illustrative rather than quoted.
    def _inline(m):
        lang, body = m.group(1), html.unescape(m.group(2))
        lexer = BashLexer() if lang == "sh" else PythonLexer()
        return f'<pre class="hl"><code>{highlight(body, lexer, FMT).rstrip()}</code></pre>'
    page = re.sub(r'<pre class="(sh|py)">(.*?)</pre>', _inline, page, flags=re.S)

    # Only THIS builder's namespace. The page documents the ladder page-builder's own
    # `{{FIG:...}}` / `{{TABLE:n}}` syntax as example text, and a guard that flags any `{{...}}`
    # would refuse to build a page whose subject is templating.
    left = re.findall(r"\{\{(?:CODE|LC|SHA)[^}]*\}\}", page)
    if left:
        fail(f"unsubstituted tokens remain: {sorted(set(left))}")

    open(OUT, "w").write(page)
    n_code = page.count('<figure class="code">')
    print(f"  built {OUT}  ({len(page):,} chars, {n_code} code blocks)")


if __name__ == "__main__":
    main()
