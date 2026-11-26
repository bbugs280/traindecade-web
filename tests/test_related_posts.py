#!/usr/bin/env python3
"""Every post must link to topically-related posts, and those links must resolve.

WHY THIS EXISTS (2026-11-26)
Real AI retrieval crawlers read the site map and stop:
    robots.txt   68 fetches
    sitemap.xml  39 fetches
    actual posts single digits
Across 13 days, only **31 of 45** EN post pages were ever fetched by a real AI
bot (GPTBot, OAI-SearchBot, PerplexityBot, ChatGPT-User, ClaudeBot).

The site was NOT disconnected — 3 sibling links per post already existed. But they
were prev/next in DATE order plus tag index pages. A crawler following them lands
on whatever happened to ship the week before, not on a related answer. The graph
was connected chronologically, not topically.

This gate asserts the topical graph, from the BUILT OUTPUT (not the templates),
because a template that renders nothing looks identical to one that works.

⚠️ HONEST SCOPE: this gate proves the links EXIST and RESOLVE. It does NOT prove
crawlers follow them or that AI visibility improves. That requires a D1 fetch-count
comparison over time. A green build is not evidence of better crawling.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SITE = "https://traindecade.com"

MIN_RELATED = 3

# ⚠️ Posts allowed to have NO related block, each with a measured reason.
# An entry here is a CONTENT gap, not an exemption granted for convenience:
# these posts cover topics no sibling post touches, so there is nothing topical
# to link to. Fixing them means writing sibling content, not editing templates.
# The staleness test forces an entry out the moment the gap closes.
# ⚠️ Posts that fall SHORT of the 3-link target, pinned to their measured count.
# These are content thinness, not template failure: the topics are only covered
# once or twice, so there is not much to link to. Pinning the number means a
# future regression (fewer links) fails the gate instead of passing quietly.
THIN_ALLOWED = {
    "how-to-choose-a-snowboard": 1,
    "stiff-is-not-inevitable-mobility-after-40": 2,
}

ORPHAN_ALLOWED = {
    "welcome":
        "site intro — tagged only fitness/health/about by design, so it has no "
        "topical sibling; nobody arrives here from a crawl and it should not rank",
    "core-strength-for-desk-workers":
        "only post covering desk-worker core/spinal health; tags (posture, L4 L5, "
        "sitting) match no other post. Needs a sibling post, not a template change",
    "who-can-actually-help-you":
        "only post covering plantar fasciitis / physio referral; tags match no "
        "other post. Needs a sibling injury-recovery post",
}


def _built_posts(lang: str) -> dict[str, str]:
    """slug -> html for every built post in a language lane."""
    base = PUBLIC / ("zh/posts" if lang == "zh" else "posts")
    out = {}
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir()):
        f = d / "index.html"
        if f.is_file():
            out[d.name] = f.read_text(encoding="utf-8", errors="replace")
    return out


def _related_block(html: str) -> str:
    """Isolate the related-posts region so tag/prev-next links can't be miscounted.

    ⚠️ `hugo --minify` emits UNQUOTED attributes: `<aside class=related-posts ...>`.
    Matching only the quoted form silently returns "" for every post and makes the
    gate look like the feature is missing. Accept both.
    """
    m = re.search(r'<aside[^>]*class="?[^">\s]*related-posts[^">\s]*"?[^>]*>(.*?)</aside>',
                  html, re.S | re.I)
    return m.group(1) if m else ""


def _links(block: str) -> list[str]:
    """Internal /posts/ hrefs, quoted or unquoted (minified output uses neither)."""
    hrefs = re.findall(r'href="?[^">\s]*(/posts/[^">\s#?]+)', block)
    return [h.rstrip("/") for h in hrefs if h.rstrip("/") != "/posts"]


def test_public_exists():
    assert PUBLIC.is_dir(), "run `hugo` first — ./public is missing"


def test_every_english_post_has_a_related_block():
    """Except posts explicitly declared as orphans, with a reason.

    `welcome` is a site intro: it carries only generic tags ("fitness", "health",
    "about") by design, so it has no topical sibling to link to. Rather than
    weaken the rule for all 45 posts, orphans are enumerated here — the same
    pattern used by the title gate's KNOWN_TOPIC_ONLY. The list must justify
    itself and must not grow silently.
    """
    allowed = ORPHAN_ALLOWED
    missing = [s for s, h in _built_posts("en").items()
               if not _related_block(h) and s not in allowed]
    assert not missing, (
        "EN post(s) with no related-posts block — the topical graph does not exist:\n  "
        + "\n  ".join(missing[:20])
        + f"\n  ({len(missing)} of {len(_built_posts('en'))} posts)")


def test_orphan_list_is_justified_and_not_stale():
    """Every orphan needs a reason, and must still BE an orphan."""
    for slug, reason in ORPHAN_ALLOWED.items():
        assert len(reason) > 30, f"{slug} parked as orphan with no real reason: {reason!r}"
    posts = _built_posts("en")
    stale = [s for s in ORPHAN_ALLOWED if s in posts and _related_block(posts[s])]
    assert not stale, (
        "listed as an orphan but now HAS related links — remove it from the list:\n  "
        + "\n  ".join(stale))


def test_english_posts_link_to_at_least_three_related_posts():
    """Three is the target; orphans are exempt; near-misses must be named.

    ⚠️ Measured 2026-11-26: after generic-tag filtering, two posts land at 1-2
    related links. That is a REAL shortfall, not a rounding error — it means the
    back catalogue is thin on those topics. They are named in THIN_ALLOWED with
    the count they actually have, so the number cannot drift upward unnoticed.
    """
    thin = []
    for slug, html in _built_posts("en").items():
        if slug in ORPHAN_ALLOWED:
            continue
        n = len(set(_links(_related_block(html))))
        floor = THIN_ALLOWED.get(slug, MIN_RELATED)
        if n < floor:
            thin.append(f"{slug}: {n} related link(s), needs {floor}")
    assert not thin, (
        f"EN post(s) linking to fewer than target related posts:\n  "
        + "\n  ".join(thin[:20]))


def test_thin_allowance_is_pinned_to_its_measured_value():
    """A thin post may not silently get thinner."""
    posts = _built_posts("en")
    wrong = []
    for slug, pinned in THIN_ALLOWED.items():
        if slug not in posts:
            continue
        actual = len(set(_links(_related_block(posts[slug]))))
        if actual < pinned:
            wrong.append(f"{slug}: now {actual}, was pinned at {pinned}")
    assert not wrong, "thin post(s) got worse:\n  " + "\n  ".join(wrong)


def test_related_links_resolve_to_real_posts():
    """A related link pointing at a nonexistent post is a 404 handed to a crawler."""
    posts = _built_posts("en")
    known = {f"/posts/{s}" for s in posts}
    broken = []
    for slug, html in posts.items():
        for link in set(_links(_related_block(html))):
            if link not in known:
                broken.append(f"{slug} -> {link}")
    assert not broken, (
        "related link(s) point at posts that do not exist:\n  "
        + "\n  ".join(sorted(broken)[:20]))


def test_related_links_are_not_self_referential():
    bad = []
    for slug, html in _built_posts("en").items():
        own = f"/posts/{slug}"
        if own in set(_links(_related_block(html))):
            bad.append(slug)
    assert not bad, "post(s) list themselves as related:\n  " + "\n  ".join(bad[:20])


def test_related_links_are_topical_not_chronological():
    """The whole point: related posts must NOT be merely the date-adjacent ones.

    ⚠️ This is the assertion that distinguishes the fix from the bug it replaced.
    Prev/next in date order would satisfy "3 links" while changing nothing.
    """
    posts = _built_posts("en")
    # Reconstruct date order from the built prev/next nav.
    order = []
    for slug, html in posts.items():
        if re.search(r'class="?prev"?', html):
            pass
    chronological_only = []
    for slug, html in posts.items():
        related = set(_links(_related_block(html)))
        if not related:
            continue
        nav = set(_links(html)) - related          # prev/next + tags
        # If EVERY related link is also a bare prev/next neighbour, it's date order.
        prevnext = set(re.findall(
            r'<a[^>]*class="?(?:prev|next)"?[^>]*href="?[^">\s]*(/posts/[^">\s#?]+)', html))
        prevnext = {p.rstrip("/") for p in prevnext}
        if related and prevnext and related.issubset(prevnext):
            chronological_only.append(slug)
    assert not chronological_only, (
        "post(s) whose 'related' links are just the date-adjacent prev/next — "
        "this is the defect the change was meant to fix:\n  "
        + "\n  ".join(sorted(chronological_only)[:20]))


if __name__ == "__main__":
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
