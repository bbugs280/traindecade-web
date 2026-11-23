# 2026-11-23 — Email capture: Pages Function, token server-side

## Decision

**Option A — Cloudflare Pages Function**, not a MailerLite embedded form.

| | Embedded form | Pages Function (chosen) |
|---|---|---|
| Per-post attribution | ❌ cannot report which post | ✅ `source_post` field per subscriber |
| Token exposure | group ID in page source | ✅ never leaves the server |
| Works without JS | ✅ | ✅ (native form POST fallback) |

The card's purpose is knowing **which article converts**. An embed can only say
"someone subscribed". traindecade's whole value is that its ZH lane is the one
channel with measured demand — so attribution is the deliverable, not a nicety.

## What shipped

```
functions/api/subscribe.js        POST endpoint → MailerLite API
layouts/partials/email_capture.html   ZH-only form, below the GainCut callout
tests/test_email_capture.py       9 checks incl. credential-leak scan
.github/workflows/hugo.yaml       new gate + endpoint liveness probe
```

Order on page: **GainCut callout first, then email capture.** Give the reader
the free thing before asking for their address. Reversing it asks for payment
before showing the goods.

## MailerLite setup

```
Group        traindecade · 204928889296782726 · 0 subscribers
Field        source_post (text, id 2665814) — MUST exist or the API 422s
Secrets      MAILERLITE_API_TOKEN + MAILERLITE_GROUP_ID (CF Pages, encrypted)
```

⚠️ `fields` keys that do not exist in the account cause MailerLite to reject
the **entire** subscriber request, not just ignore the field. Created
`source_post` before first use for this reason.

## Three failure modes this design closes

**1. A form that renders but collects nobody.** The endpoint returns
`not_configured` (HTTP 500) when the token is missing. Returning `{ok:true}`
would be the same silent-success bug already found twice this session.

**2. A token leaking into page source.** `test_email_capture.py` scans 1,003
rendered files for `MAILERLITE_API_TOKEN = "<literal>"` and for
credential-in-query-string patterns. The security property is now tested, not
remembered — a future edit cannot silently reintroduce an embed.

**3. A click counted as a conversion.** The GA4 `email_capture_success` event
fires only on a **confirmed server response**, never on button click. A submit
that fails upstream is not a conversion, and counting it would report a funnel
health that does not exist.

## Verification

```
test_multilingual.py        PASS
check_no_stray_emphasis.py  PASS
test_gaincut_connector.py   PASS 45/45 ZH, 0 EN
test_ga_event_binding.py    PASS
test_email_capture.py       PASS 45/45 ZH wired · 45/45 slugs ·
                                 0 leaks in 1003 files · 0 EN
```

CI additionally probes the live endpoint with a junk address and fails the
build if it returns `not_configured` instead of `invalid_email`.

## ⚠️ Trap found while writing the test

Hugo `--minify` strips quotes from bare attribute values:
`value="whey-vs-beef"` renders as `value=whey-vs-beef`. The first version of
the slug assertion checked only the quoted form and reported 46 false
failures. Asserting on minified output means matching the minified shape.

## Pillar

💼 BUSINESS · Vehicle: IdeaFactory.one · Product: GainCut

## Still open

- IG bio links — manual, no repo path
- One real GA4 Realtime click — human last mile
- ⚠️ Rotate `MAILERLITE_API_TOKEN` and `CLOUDFLARE_API_TOKEN`: both were pasted
  into chat. Tokens are now in Cloudflare's encrypted store, but the copies in
  the chat transcript should be considered exposed.
