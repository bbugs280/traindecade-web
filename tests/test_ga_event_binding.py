#!/usr/bin/env python3
"""Assert the data-ga → GA4 event binding is real, on RENDERED output.

WHY THIS TEST EXISTS (2026-11-23)
---------------------------------
`gaincut_cta.html` shipped an anchor carrying:

    data-ga="gaincut_click"
    data-ga-location="zh-post-<slug>"

...with a code comment asserting "data-ga is bound by the site's existing
outbound-click listener."

That claim was FALSE. The listener in `extend_footer.html` only ever emitted
`outbound_click`; it never read `data-ga`. The attribute was decorative.

Root cause of the miss: the previous verification checked that the ANCHOR
rendered and that a UTM existed. It never checked that the EVENT could fire.
An attribute in the HTML proves nothing about what the Javascript does with it.

THE RULE THIS ENCODES
---------------------
`hugo` exit 0 is not evidence. A rendered attribute is not evidence.
Evidence = the listener SOURCE reads the attribute, and the built page carries
BOTH the attribute and the listener that consumes it.

Run: python3 tests/test_ga_event_binding.py --public ./public
Exit 0 = bound. Exit 1 = the event cannot fire.
"""

import argparse
import glob
import os
import sys

CTA_ATTR = 'data-ga="gaincut_click"'
BINDING_MARKER = 'getAttribute("data-ga")'

failures = []
checks = 0


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        failures.append(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--public", default="./public")
    ap.add_argument("--layouts", default="./layouts/partials")
    args = ap.parse_args()

    # ---- 1. The listener SOURCE must actually read data-ga ----------------
    footer = os.path.join(args.layouts, "extend_footer.html")
    check(os.path.exists(footer), f"MISSING: {footer}")
    if os.path.exists(footer):
        src = open(footer, encoding="utf-8").read()
        check(
            BINDING_MARKER in src,
            "extend_footer.html does not read data-ga — a custom event cannot fire.\n"
            "  Expected to find: " + BINDING_MARKER,
        )
        check(
            'gtag("event", gaName' in src or "gtag('event', gaName" in src,
            "extend_footer.html reads data-ga but never dispatches it to gtag().",
        )

    # ---- 2. The CTA must still carry the attribute ----------------------
    cta = os.path.join(args.layouts, "gaincut_cta.html")
    check(os.path.exists(cta), f"MISSING: {cta}")
    if os.path.exists(cta):
        csrc = open(cta, encoding="utf-8").read()
        check(CTA_ATTR in csrc, f'gaincut_cta.html lost {CTA_ATTR}')

    # ---- 3. RENDERED output: attribute AND listener on the same page ----
    zh_pages = glob.glob(
        os.path.join(args.public, "zh", "posts", "*", "index.html")
    )
    check(len(zh_pages) > 0, f"no ZH post pages found under {args.public}/zh/posts/")

    with_attr, with_listener = 0, 0
    for p in zh_pages:
        html = open(p, encoding="utf-8").read()
        if "gaincut_click" in html:
            with_attr += 1
            # The listener is injected by extend_footer; without it the
            # attribute is inert no matter how correct it looks.
            if 'getAttribute("data-ga")' in html:
                with_listener += 1
            else:
                failures.append(
                    f"listener MISSING on rendered page: {os.path.basename(os.path.dirname(p))}"
                )

    check(
        with_attr == len(zh_pages),
        f"only {with_attr}/{len(zh_pages)} ZH posts carry the GainCut event attribute",
    )
    check(
        with_listener == with_attr,
        f"only {with_listener}/{with_attr} pages carrying the attribute also "
        f"carry the listener that dispatches it",
    )

    # ---- 4. EN must stay clean (deliberate, per 2026-11-22 decision) ----
    en_hits = 0
    for p in glob.glob(os.path.join(args.public, "posts", "*", "index.html")):
        if "gaincut_click" in open(p, encoding="utf-8").read():
            en_hits += 1
    check(en_hits == 0, f"{en_hits} EN posts carry the ZH-only GainCut event")

    # ---- report ---------------------------------------------------------
    if failures:
        print(f"FAIL  data-ga → GA4 binding  ({len(failures)} problem(s), {checks} checks)")
        for f in failures:
            print("  ✗ " + f)
        return 1

    print(
        f"PASS  data-ga → GA4 binding  "
        f"({checks} checks: listener reads attribute · CTA carries it · "
        f"{with_listener}/{len(zh_pages)} ZH posts wired · 0 EN)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
