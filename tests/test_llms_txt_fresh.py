#!/usr/bin/env python3
"""llms.txt must list every post. Stale llms.txt = AI crawlers fed a truncated site.

MEASURED FAILURE (2026-11-26): `static/llms.txt` claimed "English posts (34)" and
"中文文章 (34)" while the repo held 45 + 45. Eleven posts per language were absent
from the file that AI retrieval crawlers read first.

The posts missing were not random — they were the NEWEST ones, and they included
the only page on the site that converts (`pump-or-real-muscle`). The generator
`scripts/gen_llms_txt.py` was correct the whole time; nobody re-ran it and nothing
tested it. A generator with no test is a manual process with extra steps.

This gate compares llms.txt against the content directory directly. It is a
FRESHNESS check, not a style check — it does not care about wording, only that
every published post appears exactly once with the right URL.

⚠️ Deliberately does NOT shell out to the generator: a test that regenerates the
file to compare it with itself would pass forever. It parses the existing file.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LLMS = ROOT / "static" / "llms.txt"
SITE = "https://traindecade.com"


def _posts(dirname: str) -> set[str]:
    d = ROOT / dirname / "posts"
    return {p.stem for p in d.glob("*.md")} if d.is_dir() else set()


def _listed(llms_text: str, prefix: str) -> list[str]:
    """Slugs referenced under a URL prefix. Order preserved, dupes kept."""
    out = []
    for m in re.finditer(rf"\]\({SITE}{prefix}/posts/([^)/]+)/\)", llms_text):
        out.append(m.group(1))
    return out


def test_llms_txt_exists():
    assert LLMS.is_file(), f"missing {LLMS} — AI crawlers get no site map"


def test_every_english_post_is_listed():
    text = LLMS.read_text(encoding="utf-8")
    listed = set(_listed(text, ""))
    on_disk = _posts("content")
    missing = sorted(on_disk - listed)
    assert not missing, (
        "EN post(s) published but ABSENT from llms.txt — AI crawlers cannot see them:\n  "
        + "\n  ".join(missing)
        + "\n  → run: python3 scripts/gen_llms_txt.py --apply")


def test_every_chinese_post_is_listed():
    text = LLMS.read_text(encoding="utf-8")
    listed = set(_listed(text, "/zh"))
    on_disk = _posts("content-zh")
    missing = sorted(on_disk - listed)
    assert not missing, (
        "ZH post(s) published but ABSENT from llms.txt:\n  "
        + "\n  ".join(missing)
        + "\n  → run: python3 scripts/gen_llms_txt.py --apply")


def test_llms_txt_has_no_ghost_entries():
    """A listed post that no longer exists is a 404 handed to a crawler."""
    text = LLMS.read_text(encoding="utf-8")
    ghosts = []
    for slug in set(_listed(text, "")) - _posts("content"):
        ghosts.append(f"EN {slug}")
    for slug in set(_listed(text, "/zh")) - _posts("content-zh"):
        ghosts.append(f"ZH {slug}")
    assert not ghosts, (
        "llms.txt lists post(s) that do not exist — dead links for crawlers:\n  "
        + "\n  ".join(sorted(ghosts)))


def test_counts_in_headings_match_reality():
    """The '(N)' in each heading is a claim. It must be true."""
    text = LLMS.read_text(encoding="utf-8")
    en_n = len(_listed(text, ""))
    zh_n = len(_listed(text, "/zh"))

    m_en = re.search(r"##\s*English posts \((\d+)\)", text)
    assert m_en, "EN section heading lost its '(N)' count"
    assert int(m_en.group(1)) == en_n, (
        f"EN heading claims {m_en.group(1)} posts, file lists {en_n}")
    assert en_n == len(_posts("content")), (
        f"EN heading claims {en_n}, disk has {len(_posts('content'))}")

    m_zh = re.search(r"##\s*中文文章 \((\d+)\)", text)
    assert m_zh, "ZH section heading lost its '(N)' count"
    assert int(m_zh.group(1)) == zh_n, (
        f"ZH heading claims {m_zh.group(1)} posts, file lists {zh_n}")
    assert zh_n == len(_posts("content-zh")), (
        f"ZH heading claims {zh_n}, disk has {len(_posts('content-zh'))}")


def test_no_duplicate_entries():
    text = LLMS.read_text(encoding="utf-8")
    for prefix, label in (("", "EN"), ("/zh", "ZH")):
        slugs = _listed(text, prefix)
        dupes = {s for s in slugs if slugs.count(s) > 1}
        assert not dupes, f"duplicate {label} entries in llms.txt: {sorted(dupes)}"


if __name__ == "__main__":
    import sys
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                fails += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if fails else 0)
