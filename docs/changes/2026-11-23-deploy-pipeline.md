# 2026-11-23 (later) — Deploy pipeline repaired: GitHub Actions → Cloudflare Pages

## What was broken

`traindecade.com` is served by **Cloudflare Pages**. The CI workflow
`.github/workflows/hugo.yaml` built with Hugo and deployed to **GitHub Pages** —
a different host. Nobody visits the GitHub Pages copy of this domain.

```
git push → Actions ✅ green → GitHub Pages (dead host)
                           ✗ NO PATH → traindecade.com
```

`wrangler pages project list` → `Git Provider: No` (manual upload only).

**Blast radius:** every content push from **2026-11-11 to 2026-11-23** went
green and never reached production. The 2026-11-22 GainCut connector on 45/45
ZH posts had never been live at any point.

**Scope correction:** this affects **traindecade only**. Verified by response
headers:

| Domain | `server:` header | Status |
|---|---|---|
| traindecade.com | `cloudflare` | ❌ was broken |
| builderdecade.com | `GitHub.com` | ✅ fine |
| ideafactory.one | `GitHub.com` | ✅ fine |

Earlier in the session I claimed both decade sites were broken. That was wrong —
I grouped them without checking. Only traindecade.

## The fix — Option B

Build **and** all test gates run in GitHub Actions. Only the final artefact goes
to Cloudflare via `cloudflare/wrangler-action@v3`. Cloudflare never builds, so a
host-side rebuild can never bypass a gate.

```
Actions: install hugo → build → 4 gates → wrangler pages deploy → verify live
                                    │
                          red gate = nothing published
```

**Secret:** `CLOUDFLARE_API_TOKEN` (Account → Cloudflare Pages → Edit,
account-scoped). Set 2026-11-23.

⚠️ The local `wrangler` login is an **OAuth token**
(`~/Library/Preferences/.wrangler/config/default.toml`) and cannot be used as a
CI secret. CI needs a scoped API token, minted in the dashboard.

## Gates are standalone scripts, NOT pytest

`pytest tests/` on this repo exits **0** with *"no tests ran"* — a false green.
The workflow invokes each script directly:

```
python3 tests/test_multilingual.py       --public ./public
python3 tests/check_no_stray_emphasis.py --public ./public
python3 tests/test_gaincut_connector.py  --public ./public
python3 tests/test_ga_event_binding.py   --public ./public
```

## The verify-live step — the check that was missing

```yaml
- Verify live site actually serves this build
  # wrangler exit 0 is not evidence the URL serves the new build.
  # Assert: ZH callout present, listener present, EN clean.
```

This is the guard that would have caught the 11-day outage on day one. Both
`hugo` and `wrangler` exit 0 while deploying nothing users can see; only a
request against the live URL distinguishes shipped from green.

## Proof

Run `45158485103` — every step green:

```
✓ Build with Hugo
✓ Gate — bilingual invariants
✓ Gate — no stray emphasis markers
✓ Gate — GainCut connector present on ZH, absent on EN
✓ Gate — data-ga event binding is real
✓ Deploy to Cloudflare Pages
✓ Verify live site actually serves this build
```

Independent verification of live production:

```
/zh/posts/whey-vs-beef-protein/   gaincut-cta=1  getAttribute("data-ga")=1
                                  data-ga=gaincut_click=1  footer=3   ✅
/posts/whey-vs-beef-protein/      gaincut-cta=0                       ✅
```

## Cost

Cloudflare Pages free tier: unlimited requests, unlimited bandwidth, 500
builds/month. This repo pushes a handful of times a week. **$0**, no card.

## Pillar

💼 BUSINESS · Vehicle: IdeaFactory.one · Product: GainCut

## Still open

- Email capture provider — Buttondown vs MailerLite (recommended: MailerLite on
  free-tier headroom; Buttondown wins on taste but caps at 100 subs)
- IG bio links — manual, no repo path
- A real GA4 Realtime click — the last mile is a human click, not a code fix
