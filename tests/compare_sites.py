#!/usr/bin/env python3
"""
Compare the Cloudflare Pages preview against the live GitHub Pages site.

PURPOSE: Before switching the custom domain, prove the Pages build serves the
same content as what is live today. Checks status code, <title>, and the
EN/ZH language marker on a sample of pages drawn from the real sitemaps.

Exit code 0 = all sampled pages match; 1 = at least one mismatch.

Usage:
    python3 compare_sites.py
    python3 compare_sites.py --sample 30
"""

import argparse
import re
import sys
import urllib.error
import urllib.request

LIVE = "https://traindecade.com"
PREVIEW = "https://traindecade.pages.dev"

UA = "Mozilla/5.0 (compatible; SiteCompare/1.0)"


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def extract(html: str) -> dict:
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S)
    lang = re.search(r"<html[^>]*\blang=[\"']?([a-zA-Z-]+)", html)
    return {
        "title": (title.group(1).strip() if title else ""),
        "lang": (lang.group(1).strip().lower() if lang else ""),
    }


def sitemap_urls(base: str) -> list[str]:
    """Return page paths from the sitemap index (EN + ZH)."""
    paths: list[str] = ["/"]
    _, idx = fetch(base + "/sitemap.xml")
    subs = re.findall(r"<loc>([^<]+)</loc>", idx)
    for sub in subs:
        _, xml = fetch(sub)
        for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
            p = loc.replace(base, "")
            if p and p not in paths:
                paths.append(p)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=20,
                    help="pages to compare (0 = all)")
    args = ap.parse_args()

    print("Collecting sitemap URLs …")
    paths = sitemap_urls(LIVE)
    print(f"  found {len(paths)} paths")

    # Always include the structural pages, then sample the rest evenly so both
    # EN and ZH and post/article pages are represented.
    must = ["/", "/zh/", "/posts/", "/zh/posts/", "/about/", "/zh/about/"]
    sample = [p for p in must if p in paths]
    rest = [p for p in paths if p not in sample]
    if args.sample and len(rest) > args.sample:
        step = max(1, len(rest) // args.sample)
        rest = rest[::step][: args.sample]
    targets = sample + rest

    print(f"Comparing {len(targets)} pages …\n")

    bad: list[str] = []
    for p in targets:
        ls, lh = fetch(LIVE + p)
        ps, ph = fetch(PREVIEW + p)
        le, pe = extract(lh), extract(ph)

        ok = (ls == ps) and (le["title"] == pe["title"]) and (le["lang"] == pe["lang"])
        mark = "✅" if ok else "❌"
        print(f"{mark} {p}")
        if not ok:
            print(f"    live:    {ls} {le['title'][:50]!r} lang={le['lang']}")
            print(f"    preview: {ps} {pe['title'][:50]!r} lang={pe['lang']}")
            bad.append(p)

    print()
    if bad:
        print(f"❌ {len(bad)}/{len(targets)} pages differ — do NOT switch DNS yet.")
        return 1
    print(f"✅ all {len(targets)} sampled pages match live")
    return 0


if __name__ == "__main__":
    sys.exit(main())
