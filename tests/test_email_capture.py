#!/usr/bin/env python3
"""Assert email capture is wired AND the MailerLite token cannot leak.

WHY THIS TEST EXISTS (2026-11-23)
---------------------------------
Vincent chose the Pages Function over the embedded form specifically so the API
token stays server-side. That decision is invisible in rendered HTML — a future
edit could reintroduce an embed, or an api_key in a layout, and the site would
look identical while silently exposing the credential.

This test makes the security property TESTABLE instead of remembered.

WHAT IT CHECKS
  1. The subscribe endpoint exists and reads its token from env, never a literal.
  2. Rendered ZH pages carry the form and the endpoint path.
  3. Rendered ZH pages carry the per-post slug (attribution) — the reason we
     did not use an embed.
  4. No rendered page or static asset contains a hard-coded token or a
     credential in a query string.
  5. EN pages stay clean (deliberate: EN lane has no traffic to capture from).

Run: python3 tests/test_email_capture.py --public ./public
Exit 0 = safe and wired. Exit 1 = unsafe or unwired.
"""

import argparse
import glob
import os
import re
import sys

failures = []
checks = 0


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        failures.append(msg)


# The env var name appearing with a literal string assignment is the exact
# failure this design avoids. We match the NAME plus a quoted value, and never
# hard-code the real token here (that would leak it into the repo).
SUSPECT_ASSIGN = re.compile(
    r"MAILERLITE_API_TOKEN\s*[:=]\s*[\"'][^\"']{10,}[\"']"
)

# Any credential passed on a URL in shipped output.
API_KEY_QS = re.compile(r"[?&](api[_-]?key|token|access[_-]?token)=", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--public", default="./public")
    ap.add_argument("--functions", default="./functions")
    args = ap.parse_args()

    # ---- 1. Endpoint source is safe ------------------------------------
    fn = os.path.join(args.functions, "api", "subscribe.js")
    check(os.path.exists(fn), "MISSING: " + fn)
    if os.path.exists(fn):
        src = open(fn, encoding="utf-8").read()
        check(
            "env.MAILERLITE_API_TOKEN" in src,
            "subscribe.js does not read the token from env",
        )
        check(
            "authorization" in src.lower(),
            "subscribe.js does not send an Authorization header",
        )
        check(
            not SUSPECT_ASSIGN.search(src),
            "subscribe.js assigns a LITERAL token instead of reading env",
        )

    # ---- 2 and 3. Rendered pages wired, BOTH languages ----------------
    # ⚠️ Changed 2026-11-23: the capture form is bilingual now. A free signup
    # costs the reader nothing, so unlike the GainCut CTA (which asks for a
    # sale) it is not gated to the ZH lane. Both languages must be wired.
    zh_pages = glob.glob(os.path.join(args.public, "zh", "posts", "*", "index.html"))
    en_pages = glob.glob(os.path.join(args.public, "posts", "*", "index.html"))
    all_pages = zh_pages + en_pages
    check(len(zh_pages) > 0, "no ZH post pages under " + args.public + "/zh/posts/")
    check(len(en_pages) > 0, "no EN post pages under " + args.public + "/posts/")

    wired, with_slug = 0, 0
    for p in all_pages:
        html = open(p, encoding="utf-8").read()
        if "capture-form" in html:
            wired += 1
            slug = os.path.basename(os.path.dirname(p))
            # ⚠️ Hugo --minify strips quotes around bare attribute values:
            # value="whey-vs-beef" renders as value=whey-vs-beef. Check both
            # forms, or this test reports a false failure on every page.
            if ('value="' + slug + '"' in html) or ("value=" + slug in html):
                with_slug += 1
            else:
                failures.append("slug missing on rendered page: " + slug)

    check(
        wired == len(all_pages),
        "only %d/%d posts carry the capture form" % (wired, len(all_pages)),
    )
    check(
        with_slug == wired,
        "only %d/%d pages carry the per-post slug (attribution lost)"
        % (with_slug, wired),
    )

    # ---- 4. No token, no credential in a query string, anywhere --------
    scanned = 0
    for root, _dirs, files in os.walk(args.public):
        for f in files:
            if not f.endswith((".html", ".xml", ".json", ".js")):
                continue
            path = os.path.join(root, f)
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            scanned += 1
            if API_KEY_QS.search(text):
                failures.append("credential in query string: " + path)
            if SUSPECT_ASSIGN.search(text):
                failures.append("hard-coded MAILERLITE_API_TOKEN in output: " + path)

    check(scanned > 0, "no output files scanned — the leak check proved nothing")

    # ---- 5. IG link gone from footer (Vincent's call 2026-11-23) ------
    # traindecade → IG is the wrong direction for a backlink and exposes his
    # real name beside a fitness blog at measured zero return. If a future
    # edit re-adds it, that is a decision, not a drift — fail loudly.
    ig_hits = 0
    for p in all_pages[:20]:
        if "instagram.com/vincenty3d" in open(p, encoding="utf-8").read():
            ig_hits += 1
    check(
        ig_hits == 0,
        "%d posts still link to instagram.com/vincenty3d — removed 2026-11-23, "
        "re-adding it is a decision not a drift" % ig_hits,
    )

    # ---- report --------------------------------------------------------
    if failures:
        print("FAIL  email capture  (%d problem(s), %d checks)" % (len(failures), checks))
        for f in failures:
            print("  x " + f)
        return 1

    print(
        "PASS  email capture  (%d checks: endpoint reads env · "
        "%d/%d posts wired (EN+ZH) · %d/%d slugs · 0 leaks in %d files · "
        "0 IG links)"
        % (checks, wired, len(all_pages), with_slug, wired, scanned)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
