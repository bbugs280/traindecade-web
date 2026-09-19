# 2026-09-19 — JSON-LD author fix + llms.txt regeneration

## 1. JSON-LD `author` was a Person named after a company

**Defect:** traindecade's BlogPosting schema emitted

```json
"author": {"@type": "Person", "name": "Train Decade"}
```

A *Person* whose name is a *brand* — semantically wrong, and PaperMod's
`schema_json.html` hardcodes `"@type": "Person"` so `params.author` alone
cannot fix it.

**Fix:** ported the `layouts/partials/templates/schema_json.html` override
already proven on builderdecade. The override reads a
`site.Params.schema.authorType` knob (default `Organization`), and Hugo
resolves `layouts/` before `themes/`.

```
before   74 BlogPosting blocks, author @type = Person
after    74 BlogPosting blocks, author @type = Organization  ✅
```

Verified across **every** built post (EN + ZH), not a sample — a single-page
check can pass while a different template branch fails.

⚠️ **Extraction trap hit during verification:** the first probe used
`application/ld\+json>` and returned **0 blocks**, which read as "schema
broken." The real tag is `<script type="application/ld+json">` — the `>`
sits after a closing quote. Correct pattern:

```python
re.findall(r'application/ld\+json["\']?\s*>(.*?)</script>', h, re.S)
```

A 0-count from one regex is a hypothesis, not a finding. This is the same
quoted-attribute family documented in the SEO skill.

## 2. `llms.txt` was stale — 6 of 74 posts listed

**Defect:** hand-maintained static files had silently drifted:

```
traindecade    6 of 68 posts listed    (omitted its ONLY converting page)
builderdecade  2 of 74 posts listed
```

The omitted traindecade page was `zh/posts/whey-vs-beef-protein/` — the site's
single converter (pos 5.2, 25% CTR) and its highest-impression page.

**Fix:** `scripts/gen_llms_txt.py` generates the file from the content
directory, so it cannot drift again. Covers all posts in both languages.

```
traindecade    68 entries (34 EN + 34 ZH)
builderdecade  74 entries (37 EN + 37 ZH)
```

⚠️ **Honest framing on effectiveness — do NOT oversell this.** Research
(2026-09-19) shows llms.txt is **not** a discovery or ranking lever:

- Google does not support it (Gary Illyes, Search Central Live 2025); Mueller
  compares it to the keywords meta tag
- 515M LLM-bot events → **408** requests to `/llms.txt`
- Ahrefs: **97%** of llms.txt files received zero requests in a month
- SE Ranking (300K domains): no link between adoption and citation frequency

Its real use is **inference-time context loading** — an agent already on the
site parsing clean Markdown instead of scraping HTML. Treat as cheap
insurance (regenerating costs minutes), **not** as traffic. It will not move a
page stuck at position 75.

## Verification

```
traindecade    schema 74/74 Organization · multilingual suite PASS
               llms.txt 68 entries, 0 cross-site leakage
builderdecade  language isolation PASS · stray-emphasis guard PASS (74 posts)
               llms.txt 74 entries, 0 cross-site leakage
both           hugo exit 0 · built output carries the regenerated file
```

## Follow-ups

- GA4 `analytics.readonly` scope is **absent entirely** (not stale) — needs a
  scope addition + Vincent's interactive consent before `calculator_used` is
  readable
