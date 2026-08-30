"""Regression tests for traindecade.com bilingual invariants.

Run against the Hugo build output in `public/` AFTER `hugo` (CI runs this
between build and deploy). Guards the exact class of bug Vincent keeps hitting:
the site "stuck in Chinese" / language toggle silently breaking.

Invariants asserted:
  1. `/`  serves lang=en + the English site title (NOT zh).
  2. `/zh/` serves lang=zh + the Chinese site title (訓練十年).
  3. hreflang=en (-> /) and hreflang=zh (-> /zh/) are BOTH emitted on both pages.
  4. Every EN post has a matching ZH translation (no orphan posts) and vice-versa.
  5. **The EN home LIST renders English titles, and the ZH home LIST renders
     Chinese titles** — the "site chrome is English but every card is Chinese"
     regression (2026-08-30). This is the mixing bug past versions missed.

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

# ZH content lives in content-zh/ (NOT content/zh) — the overlapping-content-dir
# bug (zh files double-imported into EN) is the root cause of the mixing.
ZH_CONTENT_DIR = "content-zh"

# A known EN post title fragment and its ZH counterpart, used to assert the
# home LIST renders in the right language (not just the site <title>/chrome).
EN_POST_TITLE_FRAGMENT = "Zone 2 and VO2max"
ZH_POST_TITLE_FRAGMENT = "Zone 2 與 VO2max"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_public_root() -> Path:
    here = Path(__file__).resolve().parent.parent  # repo root
    return here / "public"


def grep_html_attr(html: str, attr: str) -> list[str]:
    """Minified Hugo output may quote attrs (hreflang=\"en\") or not — strip both."""
    return re.findall(rf"{attr}=[\"']?([^\s>\"']+)[\"']?", html)


def _home_list_titles(html: str) -> list[str]:
    """Extract the actual post-card titles from the home list.

    Hugo/PaperMod renders each card with an entry-link whose aria-label is
    'post link to <Title>' — the same string the visible <h2> shows, and the
    most reliable thing to assert language on (plain text, no markup).

    NOTE: match the aria-label directly and tolerate any attribute ordering /
    spacing, because the Hugo minifier emits attribute order differently on
    Linux (Go map ordering) vs macOS. Do NOT anchor on a preceding 'entry-link'
    token or exact whitespace — that was the brittle regex that false-failed
    on Linux CI (2026-08-30).
    """
    return re.findall(r'aria-label="post link to ([^"]*)"', html)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--public", default=None, help="path to Hugo public/ dir")
    args = ap.parse_args()
    public = Path(args.public) if args.public else find_public_root()

    failures: list[str] = []

    # --- 1 & 2: language + site title per surface ---
    for rel, expect_lang, expect_title in [
        ("index.html", "en", EN_TITLE),
        ("zh/index.html", "zh", ZH_TITLE),
    ]:
        f = public / rel
        if not f.exists():
            failures.append(f"MISSING {rel} (build incomplete?)")
            continue
        html = _read(f)
        m = re.search(r"<html[^>]*lang=[\"']?([^\s>\"']+)[\"']?", html)
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
        hrefs = re.findall(r'hreflang=[\"\']?(\w+)[\"\']?\s+href=[\"\']?([^\s>\"\']+)[\"\']?', html)
        pairs = {lang: url for lang, url in hrefs}
        for lang, path in [("en", "/"), ("zh", "/zh/")]:
            if lang not in pairs:
                failures.append(f"{rel}: hreflang={lang} missing")
            elif not pairs[lang].rstrip("/").endswith(path.rstrip("/")):
                failures.append(f"{rel}: hreflang={lang} -> {pairs[lang]} (expected {path})")

    # --- 5 (NEW, the actual regression): home LIST language ---
    # The EN home must render ENGLISH post titles, the ZH home CHINESE ones.
    # This catches "English chrome + Chinese cards" (content/zh leaking into EN).
    for rel, expect_fragment in [
        ("index.html", EN_POST_TITLE_FRAGMENT),
        ("zh/index.html", ZH_POST_TITLE_FRAGMENT),
    ]:
        f = public / rel
        if not f.exists():
            continue
        html = _read(f)
        titles = _home_list_titles(html)
        if not titles:
            failures.append(f"{rel}: no post-card titles found in home list (layout change?)")
            continue
        if not any(expect_fragment in t for t in titles):
            got_sample = titles[:3]
            failures.append(
                f"{rel}: home list is in the WRONG language — expected a title containing "
                f"{expect_fragment!r}, got {got_sample}"
            )

    # --- 6 (lang switcher targets the CURRENT page, not home) ---
    # Bug (2026-08-30): theme header.html used `site.Home.Translations`, so the
    # header lang-toggle always linked to the home page's translation (/zh/ or /)
    # instead of the CURRENT page's translation (/zh/posts/<slug>/ etc). Fix: the
    # site-level header override uses `.Translations` (the current page's).
    # Assert: on a deep post page, the lang-menu href points at the SAME slug in
    # the other language, NOT the bare home. Extract from a representative post.
    DEEP_SLUG = "zone2-vo2max-longevity-engine"
    for rel, expect_path in [
        # EN post → should link to /zh/posts/<slug>/ (same post in ZH)
        (f"posts/{DEEP_SLUG}/index.html", f"/zh/posts/{DEEP_SLUG}/"),
        # ZH post → should link to /posts/<slug>/ (same post in EN)
        (f"zh/posts/{DEEP_SLUG}/index.html", f"/posts/{DEEP_SLUG}/"),
    ]:
        f = public / rel
        if not f.exists():
            continue  # post not built in this run — skip silently (parity check covers orphans)
        html = _read(f)
        # lang-menu block: <ul class=lang-menu> ... <a href=...> ... </ul>.
        # The minifier may or may not quote attrs and may or may not collapse
        # newlines, so anchor on the literal `lang-menu` token and span to the
        # first `</ul>` with DOTALL (the lang switcher is the first </ul> after).
        i = html.find("lang-menu")
        if i < 0:
            failures.append(f"{rel}: no lang-menu block found (header override missing?)")
            continue
        j = html.find("</ul>", i)
        menu = html[i:j] if j > 0 else html[i:i+400]
        # Anchor hrefs come quoted ("...") in the non-minified build and may be
        # unquoted in --minify output. Match both forms explicitly (avoid a raw
        # string's backslash-class footgun that silently mis-escapes \s → 's').
        hrefs = re.findall(r'href="([^"]+)"|href=\'([^\']+)\'|href=([^\s>"\']+)', menu)
        hrefs = [a or b or c for a, b, c in hrefs]
        combined = " ".join(hrefs)
        # The anchor href may be a root-relative path (minifier drops the scheme
        # + host) or absolute; normalize by keeping only the path tail.
        if expect_path not in combined:
            failures.append(
                f"{rel}: lang-menu links to {hrefs!r}, expected the current page's "
                f"translation {expect_path!r} (got the home page instead?)"
            )

    # --- 4: EN <-> ZH post parity (orphan translation guard) ---
    repo = Path(__file__).resolve().parent.parent
    en_src = {p.stem for p in (repo / "content" / "posts").glob("*.md")}
    zh_src = {p.stem for p in (repo / ZH_CONTENT_DIR / "posts").glob("*.md")}
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

    print(f"✅ multilingual invariants OK (EN+ZH, hreflang bidirectional, {len(en_src)} EN / {len(zh_src)} ZH paired, home lists in correct language)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
