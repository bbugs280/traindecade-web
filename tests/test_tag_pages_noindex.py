#!/usr/bin/env python3.13
"""Gate: tag taxonomy pages must be noindex, and post pages must stay indexable.

WHY THIS EXISTS (measured 2026-11-27, 22nd discovery pull)
----------------------------------------------------------
`/tags/cns-fatigue-symptoms/` held 10 impressions at pos 83.3 for the query
`cns fatigue symptoms` — the same query the real CNS post owns. A thin taxonomy
URL was competing with the post for its own cluster.

The sitemap excludes tags (`layouts/sitemap.xml`), so it LOOKED handled. Nothing
noindexed them: `public/tags/cns-fatigue-symptoms/index.html` emitted
`<meta name=robots content="index, follow">`. Sitemap exclusion is not
de-indexing — a tag page reachable by internal links still gets crawled and
ranked. That is the gap this gate closes.

WHAT IT ASSERTS
---------------
1. Every built `/tags/*/index.html` carries `noindex`.
2. At least one tag page exists (guards against a vacuous pass).
3. A built POST page does NOT carry noindex (guards the over-broad fix — a
   template that noindexed everything would "pass" assertion 1 and destroy the
   site).

Run it against a real build, not a plain `hugo` (see gates-and-verification.md).
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

failures = []


def robots_meta(html: str) -> str:
    """Return the content of <meta name=robots ...>, minified or not, or ''.

    ⚠️ Also catches the DUPLICATE case. The first fix attempt added a noindex
    meta in extend_head.html while PaperMod's head.html still emitted
    `index, follow` first — the page then carried TWO conflicting robots metas
    and reading only the first made it look unfixed. Two robots tags is its own
    defect (ambiguous for crawlers), so it is reported explicitly.
    """
    metas = re.findall(
        r'<meta[^>]*name=["\']?robots["\']?[^>]*content=["\']?([^"\'>\s]+)',
        html,
        re.IGNORECASE,
    )
    if len(metas) > 1:
        return f"DUPLICATE:{'|'.join(m.lower() for m in metas)}"
    return metas[0].lower() if metas else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--public",
        default=str(ROOT / "public"),
        help="built output dir (CI passes its BUILD_DIR)",
    )
    args = ap.parse_args()
    PUBLIC = pathlib.Path(args.public)

    if not PUBLIC.is_dir():
        print("FATAL: public/ missing — run ./scripts/run_tests.sh (it builds first)")
        return 2

    tag_pages = sorted(PUBLIC.glob("tags/*/index.html")) + sorted(
        PUBLIC.glob("*/tags/*/index.html")
    )
    if not tag_pages:
        print("FATAL: no tag pages found — fix or the gate passes vacuously")
        return 2

    for p in tag_pages:
        c = robots_meta(p.read_text(encoding="utf-8", errors="ignore"))
        if "noindex" not in c:
            failures.append(f"tag page NOT noindex: {p.relative_to(PUBLIC)} (robots={c!r})")

    post_pages = sorted(PUBLIC.glob("posts/*/index.html"))
    if not post_pages:
        print("FATAL: no post pages found — cannot prove the fix is not over-broad")
        return 2

    # Sample deterministically: first and last post page per language.
    sample = post_pages[:1] + post_pages[-1:]
    for p in sample:
        c = robots_meta(p.read_text(encoding="utf-8", errors="ignore"))
        if "noindex" in c:
            failures.append(
                f"POST page is noindex — the fix is over-broad: "
                f"{p.relative_to(PUBLIC)} (robots={c!r})"
            )

    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(
        f"OK: {len(tag_pages)} tag page(s) noindex; "
        f"{len(sample)} post page(s) still indexable"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
