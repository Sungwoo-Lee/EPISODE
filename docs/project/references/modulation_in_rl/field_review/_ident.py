"""Author-name matching, shared by the reference builder and the coverage audit.

Both scripts match a corpus row against files and documents by author surname, and both got
it wrong in the same three ways before this module existed:

1. **Concatenated surnames.** The corpus key packs a two-author paper into one token —
   `asadilittman`, `kendallgal`, `chevalierboisvert` — while a filename or a review says
   "Asadi and Littman" or `chevalier_boisvert_2017`. Matching on the key alone missed all
   of them. The paper LABEL carries the real names, so surnames come from the label and the
   key is only a fallback.
2. **Diacritics.** `Schöpf`, `Röder` and `Büchi` normalise to `schopf`, `roder`, `buchi` in
   a key, but appear with their diacritics in document text. Both sides must be folded.
3. **Separators.** `Rezaei-Shoshtari` in prose vs `rezaeishoshtari` in a key, and
   `chevalier_boisvert` in a filename. Hyphens and underscores have to go from both sides.

Fold once, on both sides, and match on any surname rather than only the first — a review
that discusses "Belongie" has reviewed the AdaIN paper whether or not it wrote "Huang".
"""
from __future__ import annotations

import re
import unicodedata

STOP = {"et", "al", "and", "the", "a", "an", "of", "on", "in", "for", "with", "via"}

# Words that are never a surname. A few corpus labels are a TITLE rather than an author list
# — "Volume Transmission… (e-nmRNN)", "Don't flatten, tokenize!", "DIVERSE" — and the last
# word of a title is not a name. Left unblocked, "transmission" matched a master review that
# merely records e-nmRNN as a paper the library never downloaded, scoring an unread paper as
# reviewed. Any name here is dropped, so such a row falls back to the key and, failing that,
# is reported as catalogued-only, which is the truth.
NOT_SURNAMES = {
    "transmission", "flatten", "tokenize", "diverse", "attention", "learning", "networks",
    "network", "policy", "policies", "modulation", "modulated", "control", "reasoning",
    "generalization", "generalisation", "representation", "representations", "models",
    "model", "agents", "agent", "search", "memory", "perception", "uncertainty", "review",
    "survey", "study", "platform", "benchmark", "layer", "layers", "transformers",
}


def fold(s: str) -> str:
    """Lowercase, strip diacritics, drop everything that is not a letter."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower())


def fold_text(s: str) -> str:
    """Fold a whole document for substring search: diacritics gone, separators gone."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[-_'’\s]+", " ", s)


def surnames(label: str, key: str = "") -> list[str]:
    """Candidate surnames for a paper, longest first.

    `label` is the digest's paper cell ("Asadi & Littman — mellowmax", "Schöpf, Auddy,
    Hollenstein & Rodriguez-Sanchez — HN-PPO"); everything before the em-dash is the author
    list. The key's surname token is appended as a fallback for rows whose label is only a
    method name.
    """
    head = re.split(r"\s*[—–]\s*|\s*[-]{2}\s*", label, maxsplit=1)[0]
    head = re.sub(r"\(.*?\)", " ", head)
    parts = re.split(r"\s*(?:,|&|\band\b|\bet al\.?\b|/)\s*", head)
    out: list[str] = []
    for p in parts:
        # Drop parts that are a title rather than a name. Labels without an em-dash put the
        # title straight after a comma ("Chevalier-Boisvert et al., BabyAI: A Platform to
        # Study..."), which otherwise contributed "learning" as a surname.
        if ":" in p or len(re.findall(r"[A-Za-zÀ-ÿ'’\-]+", p)) > 3:
            continue
        # take the last capitalised word of each part: "Wanting Yao" -> "yao"
        words = [w for w in re.findall(r"[A-Za-zÀ-ÿ'’\-]+", p) if w.lower() not in STOP]
        if not words:
            continue
        f = fold(words[-1])
        if f in NOT_SURNAMES:
            f = ""
        if len(f) >= 3 and f not in out:
            out.append(f)
        if len(words) > 1:                       # hyphenated / two-part surnames
            f2 = fold("".join(words))
            if len(f2) >= 3 and f2 not in out:
                out.append(f2)
    if key:
        kf = key.split("_")[0]
        if kf and kf not in out:
            out.append(kf)
    return sorted(out, key=len, reverse=True)
