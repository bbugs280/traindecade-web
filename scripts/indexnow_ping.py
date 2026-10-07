#!/usr/bin/env python3
"""IndexNow ping for traindecade.com.

Notifies Bing / Yandex / Seznam / Naver that URLs changed — near-instant crawl.
Google does NOT participate in IndexNow (it uses sitemap + Search Console).

Usage:
  python3 scripts/indexnow_ping.py URL [URL ...]   # submit specific (changed) URLs — PREFERRED
  python3 scripts/indexnow_ping.py                 # submit every page URL from public/

⚠️ IndexNow etiquette: submit URLs THAT CHANGED, not the whole site on every deploy.
Frequent full-site submissions degrade how seriously future pings are taken.
The CI job submits home + sitemap only; add changed post URLs when useful.

Exit 0 on success/benign, non-zero on hard failure.
IndexNow is a crawl HINT, not a command — 200/202 means accepted, not indexed.
"""
import sys, json, os, urllib.request, urllib.error, re, glob

HOST = "traindecade.com"
KEY = "0cd209af07b04d46976cb91bdbf715ba"
KEY_LOCATION = "https://%s/%s.txt" % (HOST, KEY)
ENDPOINT = "https://api.indexnow.org/indexnow"

def page_urls():
    """Collect real page URLs from the built site under public/.

    Expands sitemap INDEX files (which list sitemap.xml children) down to the
    actual page <loc> entries, and also reads post index.html dirs — so we never
    submit a sitemap.xml path as if it were a page.
    """
    urls = set()

    def locs(text):
        return [m.strip() for m in re.findall(r"<loc>\s*(.*?)\s*</loc>", text)]

    seen_sitemaps = set()
    queue = glob.glob("public/**/sitemap.xml", recursive=True)
    while queue:
        f = queue.pop(0)
        if f in seen_sitemaps:
            continue
        seen_sitemaps.add(f)
        try:
            xml = open(f, encoding="utf-8").read()
        except OSError:
            continue
        for u in locs(xml):
            if u.endswith(".xml"):
                rel = u.split(HOST, 1)[-1].lstrip("/")
                cand = os.path.join("public", rel)
                if os.path.exists(cand):
                    queue.append(cand)
            elif u.startswith("https://" + HOST):
                urls.add(u)

    for idx in glob.glob("public/**/index.html", recursive=True):
        if "/tags/" in idx or "/categories/" in idx:
            continue
        rel = os.path.relpath(os.path.dirname(idx), "public")
        if rel in (".", ""):
            urls.add("https://%s/" % HOST)
        else:
            urls.add("https://%s/%s/" % (HOST, rel))
    return sorted(urls)

def ping(urls):
    if not urls:
        print("no URLs to submit"); return 0
    body = json.dumps({
        "host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": urls,
    }).encode()
    req = urllib.request.Request(ENDPOINT, data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        r = urllib.request.urlopen(req, timeout=30)
        print("IndexNow HTTP %s — submitted %d URLs" % (r.status, len(urls)))
        return 0
    except urllib.error.HTTPError as e:
        if e.code in (200, 202):
            print("IndexNow HTTP %s — accepted %d URLs" % (e.code, len(urls))); return 0
        print("IndexNow HTTP %s — %s" % (e.code, e.read().decode()[:200]))
        return 1
    except Exception as e:
        print("IndexNow error: %s" % e); return 1

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a.startswith("http")]
    urls = args if args else page_urls()
    sys.exit(ping(urls))
