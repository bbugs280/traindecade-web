# 2026-11-13 — Link repairs (Rank 1 + 2) and one ZH tune (Rank 3)

Stage 3 approval of the traindecade 2026-11-13 shortlist. **No new post** — the shortlist's
own evidence killed the content candidate (see below). All work is repair, and all of it is
invisible to a reader: no new URL, homepage unchanged.

## Why no new post this cycle

The 11-11 content candidate proposed a 4th CNS post on the premise *"`does-heavy-lifting-fry-your-cns`
gets 85 impressions at position 6.8 = page 1 = extend the cluster."*

**The premise is an artefact.** Verified against live GSC (`query`×`page`, 30d, 40 rows):

| real query | impressions | actual position |
|---|---|---|
| cns fatigue symptoms | 27 | 84.1 |
| central nervous system fatigue | 25 | 88.0 |
| cns fatigue recovery time | 24 | 81.7 |
| what is cns fatigue | 12 | 86.2 |
| cns fatigue | 9 | 87.4 |

The 6.8 page average is dragged down by two 1-impression strays at position 1.0 and 3.0.
**The EN CNS cluster is a page-8 cluster wearing a page-1 costume.** A 4th CNS post would
join three existing posts already splitting 20+ near-identical variants at position 81–89.

Not offered, and why: REFERRAL is blocked-on-access *and* blocked-on-position (candidate
pages sit 21–89; one link moves page 9 → page 8). Terminal action is downstream of traffic.
Content volume had no surviving candidate. Reporting that is the useful output.

---

## Rank 1 — `pump-or-real-muscle` two-way orphan closed

**Before: 0 inbound links in EITHER language.** Verified by grep before any edit. The page
holds a page-1 ZH position (`肌肉充血英文` pos 8.3, `肌肉充血 英文` pos 9.0) with zero link
equity. Third run running as an orphan.

Added 3 contextual inbound links per language, each anchoring a paragraph that argues the
same point rather than a "related posts" list:

| Neighbour | Where the link sits |
|---|---|
| `muscle-is-metabolic-armor-not-vanity` | after the "what builds the armor" prescription |
| `body-recomposition-men-over-40` | on the "patience not the mirror" point |
| `why-crash-diets-fail` | on the "protect the muscle" caveat |

## Rank 2 — three outbound dead ends closed

All three verified at **0 outbound** before the edit:

| Page | Before | After |
|---|---|---|
| `who-can-actually-help-you` (newest post) | 0 EN / 0 ZH | 2 EN / 2 ZH |
| `exercise-snacking-short-daily-bursts-beat-no-time` | 0 EN / 0 ZH | 1 EN / 1 ZH |
| `muscle-is-metabolic-armor-not-vanity` | 2 EN / **0 ZH** | 2 EN / 2 ZH |

The third was also an **EN/ZH asymmetry** — the ZH twin had dropped the
`你到底需要多少蛋白質？` link its EN counterpart carries. Restored.

## Rank 3 — ZH tune, `muscle-power`

Query `作戰持久力估算` at **position 4.0 / 5 impressions** — confirmed live in GSC, the
highest position on any non-whey ZH query this pull, and it passes the crest test (pos 4 =
page 1) where tune fails everywhere else.

⚠️ **The causal read, stated honestly:** the page ranked pos 4 while containing **zero
mentions** of 持久力 / 作戰 / 估算. It is not ranking *for* that term on merit — it is
ranking on partial character overlap. The tune adds the vocabulary where it genuinely
belongs (military-fitness framing of sustained output), in the body and in the `description`,
so the page actually answers the query it already surfaces for.

ZH file only. EN untouched. `lastmod` bumped.

⚠️ **5 impressions is the measurement floor.** This may be noise. It is scoped narrowly and
costs one paragraph; it is not a strategy pivot.

---

## Verification

| Check | Result |
|---|---|
| Build | exit 0 — 332 EN / 354 ZH pages |
| Rank 1 inbound rendered (EN) | 3 of 3 files ✅ |
| Rank 1 inbound rendered (ZH) | 3 of 3 files ✅ |
| Rank 2 outbound rendered (EN) | 2 / 1 / 2 ✅ |
| Rank 2 outbound rendered (ZH) | 2 / 1 / 2 ✅ |
| Rank 3 term in built ZH page | present (7 occurrences) ✅ |
| ZH pages linking into EN lane | **0** ✅ |
| EN/ZH post parity | 45 / 45 (unchanged — no new posts) |

## ⚠️ Pitfall hit during this session — `patch` swallowing the trailing newline

Four separate `patch` calls collapsed a following line into the edited line, because the
`old_string` ended with a newline that the replacement then consumed. It silently merged a
numbered list item into the previous one in `muscle-is-metabolic-armor-not-vanity` and
`why-crash-diets-fail`.

**Tell:** the diff shows a `-` line and `+` line differing only by a missing line break, with
the *next* line appearing appended.

**Fix:** always re-read the diff for merged lines, and prefer an `old_string` that ends on
content (no trailing `\n`) — or include the following line as context so the newline is
inside the matched region. Both mangled spots were caught and restored before commit.

## Files changed

```
M content/posts/muscle-is-metabolic-armor-not-vanity.md
M content/posts/body-recomposition-men-over-40.md
M content/posts/why-crash-diets-fail.md
M content/posts/who-can-actually-help-you.md
M content/posts/exercise-snacking-short-daily-bursts-beat-no-time.md
M content-zh/posts/muscle-is-metabolic-armor-not-vanity.md
M content-zh/posts/body-recomposition-men-over-40.md
M content-zh/posts/why-crash-diets-fail.md
M content-zh/posts/who-can-actually-help-you.md
M content-zh/posts/exercise-snacking-short-daily-bursts-beat-no-time.md
M content-zh/posts/muscle-power-the-longevity-number-your-strength-test-misses.md
```

No build artefacts committed.

🎯 PILLAR: 💼 BUSINESS · Domain: 💼 Business
