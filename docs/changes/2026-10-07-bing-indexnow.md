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

---

## ✅ RESOLUTION (2026-10-07) — both decade sites now HTTP 200

```
traindecade.com    IndexNow 200 ✅  (upgraded from 202 — key now validated by Bing)
builderdecade.com  IndexNow 200 ✅  (403 cleared)
```

**traindecade moved 202 → 200**: the earlier 202 was a *soft* accept (well-formed key,
validation pending). It has now been validated. **202 → 200 is the observable signal that
Bing's gates cleared** — never report a 202 as success; only 200 is real acceptance.

### The 403 root cause — Bing's own docs, not inference

`bing.com/indexnow/getstarted` lists integration **Step 1 = "Generate API Key"**, and its
response-code table states:

```
403 Forbidden → "Key not valid (e.g. key not found, or file found but key not in file)"
```

Builderdecade's Bing IndexNow page was still the **onboarding hero** ("Take control of your SEO
game" + *Get Started* button) — no key, no status. **Bing had never issued a key for that
domain.** The UUID minted in-repo was invisible to Bing until a key was generated in Bing's own
UI. **The repo, key file, and deploy were all correct.**

**⇒ Diagnose by PAGE STATE, not by error code.** `UserForbiddedToAccessSite` is identical whether
the domain is unverified OR the key is simply unregistered — so it cannot distinguish the two.
Open the site's Bing IndexNow page: if it is still the onboarding hero, the answer is "generate
the key," full stop.

### Fix shipped (builderdecade, commit `b1fbab6`)

```
hugo.yaml                  indexNowKey → 7544e52888da4e97b8e7921a794bd6d4  (Bing-issued)
static/7544e5…d6d4.txt     new key file added
static/224d20…2ae34.txt    old key file DELETED — a leftover key file is a second, wrong
                           answer at a guessable public URL; never leave one behind
scripts/indexnow_ping.py   KEY constant updated
```

The swap must be **atomic across all three files**; a key file that doesn't match the
YAML/script constant, or a stale key file left served, re-breaks the handshake.

### Verified end-to-end

| Check | Result |
|---|---|
| New key file live | HTTP 200, content correct ✅ |
| Old key file | HTTP 404 ✅ |
| Re-ping (118 URLs) | HTTP 200 ✅ |
| Raw `api.indexnow.org` curl | HTTP 200 ✅ |

Two independent probes (script report **and** raw curl) — so the 200 is not a script-level
false positive.

### Rollback
- Tag `rollback-pre-bing-key-swap-2026-10-07` (builderdecade).

---

## ⚠️ Original post-deploy finding (2026-10-07) — SUPERSEDED, see RESOLUTION above

```
traindecade    IndexNow HTTP 202  (accepted — but see caveat below)
builderdecade  IndexNow HTTP 403  UserForbiddedToAccessSite
```

Both key files are served correctly (HTTP 200, byte-identical 32-hex + newline).

⚠️ **`202` is NOT proof of success.** Per the IndexNow docs: *"Bing, Yandex and the
global endpoint return 202 for any well-formed key and validate it later, discarding
the submission silently if it fails."*

⚠️ **The "domain-verification state" diagnosis below was WRONG.** Kept only as a record of the
false lead. Builderdecade's BWT dashboard loaded fully (Home/Sitemaps/IndexNow/Backlinks),
proving the domain **was** verified. The real cause was the **un-generated IndexNow key** — a
second, independent Bing-side gate. Two false leads were burned before this landed:

- ❌ *"verify the domain in Bing WMT"* — it was already verified.
- ❌ *"our key file is wrong / Bing cached a rejection"* — the file served 200 and was
  byte-identical to traindecade's. Because traindecade was a **different key** and worked, the
  file format was never the variable.
