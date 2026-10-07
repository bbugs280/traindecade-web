# 2026-10-07 — Bing Webmaster Tools + IndexNow (AI-search retrieval layer)

## Why
Bing is ~4–5% of global search by traffic (and ~36 pages crawled per referral vs Google's ~5),
so it is **not** a meaningful direct-traffic lever. It **is** the retrieval index that powers
**ChatGPT Search, Microsoft Copilot, and Perplexity**. Adding it is a *discovery* lever for the
AI-citation channel — not a ranking lever, and not a fix for the pos-55–76 EN pages (those need
authority). Cheap insurance that sits alongside the earlier AI-visibility work.

Bing traffic is also **7.45% from China** (its #2 market) — relevant to the ZH lane, the site's
only proven converting lane.

## Shipped
- **IndexNow key file** — `static/0cd209af07b04d46976cb91bdbf715ba.txt` (serves at
  `https://traindecade.com/0cd209af07b04d46976cb91bdbf715ba.txt`). IndexNow key = this site's
  own; one ping notifies **Bing, Yandex, Seznam, Naver** at once.
- **`scripts/indexnow_ping.py`** — submits changed URLs; expands the sitemap *index*
  (`/sitemap.xml` → `/en/sitemap.xml` + `/zh/sitemap.xml`) down to real page `<loc>` entries and
  also walks `public/**/index.html`, so no `sitemap.xml` path is ever submitted as a page.
  Excludes `/tags/`, `/categories/`. Prefers explicit URL args over full-site submission
  (frequent full-site pings degrade future submission trust).
- **`hugo.yaml`** — added `params.analytics.bingSiteVerification` + `params.analytics.indexNowKey`.
- **`layouts/partials/extend_head.html`** — emits `<meta name="msvalidate.01" content="…">`
  conditionally (verified: present when the param is filled, absent when empty).
- **`.github/workflows/hugo.yaml`** — post-deploy step pings IndexNow with home + `/zh/` +
  sitemap. `continue-on-error: true` — a ping failure must never fail the deploy.

## Verified
- `hugo --gc --minify` → exit 0.
- Key file lands at `public/<key>.txt` (root).
- Bing meta emits **only** when the param is non-empty (tested by temporarily filling it).
- **Live IndexNow ping → HTTP 202 accepted** (submitted home + /zh/).
- Sitemap expansion: 101 real page URLs; **0** `.xml` and **0** `/tags/` leaked.
- `test_multilingual.py` → ✅ 37 EN / 37 ZH paired, hreflang bidirectional, home lists correct.
- `check_no_stray_emphasis.py` → ✅ 74 rendered posts clean.

## ⚠️ Google does NOT participate
IndexNow notifies Bing/Yandex/Seznam/Naver only. Google publicly declined IndexNow — it uses
sitemap + Search Console (already wired). Both channels run in parallel; neither replaces the other.

## Next (needs Vincent — 2 min)
1. Open Bing Webmaster Tools → **Add site → import from Google Search Console** (fastest path,
   GSC is already verified).
2. Take the `msvalidate.01` content value Bing shows → paste it into
   `hugo.yaml` → `params.analytics.bingSiteVerification` → we push → click **Verify**.

## Rollback
- Tag `rollback-pre-bing-2026-10-07`.
