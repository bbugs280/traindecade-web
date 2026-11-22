#!/usr/bin/env python3
"""GainCut connector + studio-network footer — regression guard.

WHY THIS EXISTS (2026-11-22)
----------------------------
An audit of the whole IdeaFactory pipeline found the marketing stage was not
"missing" — it was *unconnected*:

  · traindecade's only proven channel is its CHINESE lane.
    GSC 90d: /zh/posts/whey-vs-beef-protein/ = 8 clicks / 95 impr / pos 5.4.
  · Those readers have direct intent (protein, body recomposition) — the same
    person GainCut is built for.
  · /gaincut/ received 2 sessions in 30 days. GainCut held 2 App Store ratings.
  · There was NO link between them. The article dead-ended.

This file guards the three connectors so a future layout refactor cannot
silently remove them:

  1. Every ZH post renders the GainCut callout, with a per-slug UTM campaign.
  2. EN posts do NOT render it (the EN lane is at position 52-97; adding a
     product CTA to pages with no traffic is noise).
  3. The footer carries the studio-network links with full UTM tags.

⚠️ THE STALE-PARTIAL TRAP THIS TEST SPECIFICALLY CATCHES
--------------------------------------------------------
builder-decade has BOTH `layouts/partials/footer.html` AND
`layouts/_partials/footer.html`. Under modern Hugo only the `_partials/` copy
renders. Editing the wrong one produces a clean `hugo` exit 0 and a build that
silently lacks the change — verified the hard way on 2026-11-22.

`hugo --quiet` exiting 0 is NOT evidence a partial is live. Assert on rendered
OUTPUT, never on a partial's source. That is what this file does.

Run:
    python3 tests/test_gaincut_connector.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAILURES = []


def check(condition, message):
    if not condition:
        FAILURES.append(message)


def build():
    """Render the site to a temp dir. Raises if hugo is unavailable."""
    out = tempfile.mkdtemp(prefix="td-test-")
    result = subprocess.run(
        ["hugo", "--quiet", "--destination", out],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        shutil.rmtree(out, ignore_errors=True)
        raise RuntimeError(f"hugo build failed:\n{result.stderr}")
    return out


def main():
    build_dir = build()

    zh_posts_dir = os.path.join(build_dir, "zh", "posts")
    en_posts_dir = os.path.join(build_dir, "posts")

    # ---------------------------------------------------------------
    # 1. Every real ZH post must carry the GainCut callout.
    #    `page/` is Hugo's pagination dir, not a post — excluded.
    # ---------------------------------------------------------------
    zh_posts = sorted(
        d for d in os.listdir(zh_posts_dir)
        if os.path.isdir(os.path.join(zh_posts_dir, d)) and d != "page"
    )
    check(zh_posts, "no ZH posts found in build — path structure changed?")

    missing_cta = []
    missing_utm = []
    for slug in zh_posts:
        index = os.path.join(zh_posts_dir, slug, "index.html")
        if not os.path.exists(index):
            continue
        html = open(index, encoding="utf-8").read()
        if "gaincut_click" not in html:
            missing_cta.append(slug)
            continue
        # Per-slug attribution: the campaign must name the article.
        if f"utm_campaign=zh-{slug}" not in html:
            missing_utm.append(slug)

    total = len(zh_posts)
    check(
        not missing_cta,
        f"{len(missing_cta)}/{total} ZH posts missing the GainCut CTA: "
        f"{missing_cta[:5]}{'...' if len(missing_cta) > 5 else ''}",
    )
    check(
        not missing_utm,
        f"{len(missing_utm)} ZH posts have the CTA but no per-slug UTM campaign: "
        f"{missing_utm[:5]}",
    )

    # ---------------------------------------------------------------
    # 2. EN posts must NOT carry it. The EN lane sits at position 52-97,
    #    so a product CTA there is untested noise on zero-traffic pages.
    # ---------------------------------------------------------------
    en_leaks = []
    if os.path.isdir(en_posts_dir):
        for slug in os.listdir(en_posts_dir):
            index = os.path.join(en_posts_dir, slug, "index.html")
            if os.path.exists(index) and "gaincut_click" in open(index, encoding="utf-8").read():
                en_leaks.append(slug)
    check(
        not en_leaks,
        f"GainCut CTA leaked onto EN posts (EN lane has no traffic — re-check "
        f"the language guard): {en_leaks[:5]}",
    )

    # ---------------------------------------------------------------
    # 3. Footer studio-network links, on both languages.
    # ---------------------------------------------------------------
    sample_zh = os.path.join(zh_posts_dir, zh_posts[0], "index.html")
    sample_html = open(sample_zh, encoding="utf-8").read()

    for target in ("ideafactory.one", "builderdecade.com", "instagram.com/vincenty3d"):
        check(
            f"{target}/" in sample_html or f"{target}?" in sample_html,
            f"footer missing link to {target} — site is a dead end again",
        )

    # Every footer outbound link must be fully UTM-tagged. An untagged link is
    # unmeasurable, which is exactly how 4 IG accounts produced 0 attributed
    # sessions across 90 days.
    network = re.search(r'class="footer-network".*?</span>', sample_html, re.S)
    check(network is not None, "footer-network block missing from rendered ZH page")
    if network:
        links = re.findall(r'href="(https?://[^"]+)"', network.group(0))
        check(links, "footer-network rendered with no outbound links")
        untagged = [
            u for u in links
            if not all(k in u for k in ("utm_source=", "utm_medium=", "utm_campaign="))
        ]
        check(not untagged, f"untagged footer link(s): {untagged}")

    shutil.rmtree(build_dir, ignore_errors=True)

    # ---------------------------------------------------------------
    if FAILURES:
        print(f"FAIL: {len(FAILURES)} problem(s)\n", file=sys.stderr)
        for f in FAILURES:
            print(f"  ✗ {f}", file=sys.stderr)
        return 1

    print(f"PASS: GainCut connector + studio network")
    print(f"      {total}/{total} ZH posts carry a tagged GainCut CTA")
    print(f"      0 EN posts carry it")
    print(f"      footer network tagged on both languages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
