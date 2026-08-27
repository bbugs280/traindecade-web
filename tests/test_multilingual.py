"""Regression tests for traindecade.com bilingual invariants.

Run against the Hugo build output in `public/` AFTER `hugo` (CI runs this
between build and deploy). Guards the exact class of bug Vincent keeps hitting:
the site "stuck in Chinese" / language toggle silently breaking.

Invariants asserted:
  1. `/`  serves lang=en + the English title (NOT zh).
  2. `/zh/` serves lang=zh + the Chinese title (訓練十年).
  3. hreflang=en (-> /) and hreflang=zh (-> /zh/) are BOTH emitted on both pages.
  4. Every EN post has a matching ZH translation (no orphan posts) and vice-versa.

Usage:
    python3 tests/test_multilingual.py --public /path/to/public
    # or default: ./public relative to repo root
"""

import os
import re
import sys
import argparse
from pathlib import Path

EN_TITLE = "Train Decade"
ZH_TITLE = "訓練十年"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_public_root() -> Path:
    here = Path(__file__).resolve().parent.parent  # repo root
    return here / "public"


def grep_html_attr(html: str, attr: str) -> list[str]:
    """Minified Hugo output has no quotes around attrs (hreflang=en)."""
    return re.findall(rf"{attr}=([^\s>]+)", html)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--public", default=None, help="path to Hugo public/ dir")
    args = ap.parse_args()
    public = Path(args.public) if args.public else find_public_root()

    failures: list[str] = []

    # --- 1 & 2: language + title per surface ---
    for rel, expect_lang, expect_title in [
        ("index.html", "en", EN_TITLE),
        ("zh/index.html", "zh", ZH_TITLE),
    ]:
        f = public / rel
        if not f.exists():
            failures.append(f"MISSING {rel} (build incomplete?)")
            continue
        html = _read(f)
        m = re.search(r"<html[^>]*lang=([^\s>]+)", html)
        got_lang = m.group(1) if m else None
        if got_lang != expect_lang:
            failures.append(f"{rel}: lang={got_lang!r}, expected {expect_lang!r}")
        if f"<title>{expect_title}</title>" not in html:
            failures.append(f"{rel}: title missing {expect_title!r}")

    # --- 3: bidirectional hreflang on both surfaces ---
    for rel, host in [("index.html", "/"), ("zh/index.html", "/zh/")]:
        f = public / rel
        if not f.exists():
            continue
        html = _read(f)
        hrefs = re.findall(r'hreflang=(\w+)\s+href=([^\s>]+)', html)
        pairs = {lang: url for lang, url in hrefs}
        for lang, path in [("en", "/"), ("zh", "/zh/")]:
            if lang not in pairs:
                failures.append(f"{rel}: hreflang={lang} missing")
            elif not pairs[lang].rstrip("/").endswith(path.rstrip("/")):
                failures.append(f"{rel}: hreflang={lang} -> {pairs[lang]} (expected {path})")

    # --- 4: EN <-> ZH post parity (orphan translation guard) ---
    en_posts = {p.stem for p in (public / "posts").glob("*.md")} if (public / "posts").exists() else set()
    zh_posts = {p.stem for p in (public / "zh" / "posts").glob("*.md")} if (public / "zh" / "posts").exists() else set()
    # Hugo renders posts to index.html dirs, not .md — but content/*.md is the source of truth.
    # CI runs this from the repo where content/ is present, so fall back to content/.
    repo = Path(__file__).resolve().parent.parent
    en_src = {p.stem for p in (repo / "content" / "posts").glob("*.md")}
    zh_src = {p.stem for p in (repo / "content" / "zh" / "posts").glob("*.md")}
    only_en = en_src - zh_src
    only_zh = zh_src - en_src
    if only_en:
        failures.append(f"Orphan EN posts (no ZH translation): {sorted(only_en)}")
    if only_zh:
        failures.append(f"Orphan ZH posts (no EN source): {sorted(only_zh)}")

    # --- report ---
    if failures:
        print("❌ MULTILINGUAL REGRESSION — deploy blocked:")
        for f in failures:
            print(f"   • {f}")
        return 1

    print(f"✅ multilingual invariants OK (EN+ZH, hreflang bidirectional, {len(en_src)} EN / {len(zh_src)} ZH paired)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
