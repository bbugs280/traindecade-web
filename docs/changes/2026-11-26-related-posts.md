# 2026-11-26 — Topical related-posts graph (AI crawler depth)

**Route:** build → build-tester
**Repo:** `~/Projects/traindecade-web`
**Follows:** the earlier entry today (title backlog + llms.txt drift + tracker repair)

---

## The problem, measured

AI retrieval crawlers read the site map and leave:

| surface | fetches |
|---|---|
| `/robots.txt` | 68 |
| `/sitemap.xml` | 39 |
| individual posts | single digits |

**31 of 45** EN post pages had ever been fetched by a real AI bot (GPTBot,
OAI-SearchBot, PerplexityBot, ChatGPT-User, ClaudeBot) — 69%.

## ⚠️ First diagnosis was wrong

I initially reported "0 sibling links per post — every post is a dead end."
That was a **regex bug**: `hugo --minify` emits unquoted `href=`, and my pattern
required quotes. Measured correctly, every post already had **3 sibling links**
and **0 posts** had zero inbound links.

So the graph was connected — but only **chronologically**: `PrevInSection` /
`NextInSection` in date order, plus tag index pages. A crawler following them
lands on whatever shipped the week before, not a related answer.

## The change

**1. `hugo.yaml`** — `related:` block (keywords 100 / tags 80 / date 5).
**2. `layouts/partials/related_posts.html`** — new `<aside class="related-posts">`.
**3. `layouts/partials/extend_post_content.html`** — calls it on every page.

### ⚠️ Why it does NOT use Hugo's built-in `.Related`

It was built that way first. It produced measurably bad links:

```
creatine-after-40  ->  "10,000 Steps Is a Marketing Number"
                       "Best Protein Powder: Why the Ranking Keeps Changing"
```

Cause: two generic tags (`over 40`, `aging`) shared with the steps post supplied
enough relatedness to rank. Hugo's `related` has **no per-index tag blacklist**.

So scoring is computed in the partial over tags-minus-generics. Tag frequency
showed a clean break:

| tag | posts | share | verdict |
|---|---|---|---|
| `over 40` | 22 | **49%** | demographic label — filtered |
| `strength training` | 12 | 27% | a topic — kept |
| `men over 40` | 11 | 24% | kept |
| `recovery` | 9 | 20% | kept |

Filtered generics: `over 40`, `aging`, `fitness`, `health`, `about`.

Result — creatine's links after the fix:
`Creatine Without the Gym` · `Best Protein Powder` · `Collagen for Tendons`
(all share `supplements`). The steps post is gone.

### ⚠️ Bug I introduced and caught: param scope

`related_generic_tags` was first written at top level in `hugo.yaml`. The partial
reads `site.Params.related_generic_tags`, which sees **only keys under `params:`**.
The filter silently did nothing and the bad links persisted. Debugging this took
longer than writing it, and the give-away was the probe never rendering.

### ⚠️ Tag values vs slugs

Tag **value** is `over 40` (space). Tag **URL slug** is `over-40` (hyphen).
Filtering on the slug never matches. Filter on the value.

## Bilingual rule — verified, not assumed

ZH posts link only to ZH posts. `.Site.RegularPages` is language-scoped, so this
holds by construction — but it was **tested**: 0 cross-lane leaks across 43 ZH
blocks. A 繁體 reader never gets handed an English post.

## Honest limits, enumerated

**3 orphans** — no related block at all, each with a measured reason:

| post | why |
|---|---|
| `welcome` | site intro, tagged only fitness/health/about by design |
| `core-strength-for-desk-workers` | only post on desk-worker spinal health |
| `who-can-actually-help-you` | only post on plantar fasciitis / physio referral |

These are **content gaps, not template failures**. Fixing them means writing
sibling posts, not editing code. `test_orphan_list_is_justified_and_not_stale`
forces each entry out the moment the gap closes.

**2 thin** — below the 3-link target, pinned to their actual count so they cannot
silently get worse: `how-to-choose-a-snowboard` (1), `stiff-is-not-inevitable-mobility-after-40` (2).

## Verification

| check | result |
|---|---|
| `tests/test_related_posts.py` | ✅ 8/8 |
| `./scripts/run_tests.sh` (full, with build) | ✅ all tests passed |
| ZH blocks / cross-lane leaks | ✅ 43 blocks / **0 leaks** |
| Mutation: rename `aside` class | ✅ gate fails (exit 1) |
| Restore | ✅ gate passes (exit 0) |

## ⚠️ This has NOT been proven to work

A green build shows the links exist and resolve. It does not show a crawler
follows them.

**Baseline captured before deploy: 31/45 post pages (69%).**

`scripts/crawler_depth.py` re-runs the same measurement against D1. Re-run ~2
weeks after deploy. If 31 has not risen, this change did not work and that should
be stated plainly rather than defended.
