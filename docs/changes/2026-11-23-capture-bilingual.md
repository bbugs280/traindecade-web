# 2026-11-23 — Capture form bilingual, copy honest, IG link removed

Three changes, all Vincent's calls in one conversation.

## 1. Email capture is now bilingual

The first version gated the form to ZH only. **That was the wrong call**, and
the mistake is worth naming: I applied the GainCut CTA's logic to a different
kind of element.

```
GainCut CTA   asks for a SALE      → ZH only is right. Asking a
                                     passing ghost for money is noise.
Capture form  asks for NOTHING     → ZH only is wrong. A free signup
                                     costs the reader nothing; the one
                                     EN reader who lands is worth having.
```

Same page, same lane logic — opposite conclusion, because the ask differs.
The language guard is removed from `email_capture.html`. The GainCut guard
stays. `test_email_capture.py` now requires **90/90** posts wired, not 45/45.

## 2. Copy: 每週 → 不定時

Vincent wrote:

> 每週一封信：一個經得起檢驗的訓練或營養結論，附上研究出處。沒有廣告，隨時可退訂。

Changed one word — 每週 (weekly) to **不定時** (irregular) — because there is no
publishing plan. Promising weekly and delivering irregularly is the fastest way
to lose the subscribers just won.

**The deeper rule:** when you have no calendar, state a **standard** instead.
"經得起檢驗" + "附上研究出處" tells the reader what kind of thing arrives, which
is what actually earns the address. Frequency is the one thing not to promise.

EN equivalent written to match, not translated literally:

> The next one, straight to your inbox
> An occasional letter: one training or nutrition conclusion that survives
> scrutiny, with the research cited. No ads. Unsubscribe any time.

## 3. Instagram footer link removed

Vincent asked whether exposing his identity was worth it. It is not, for two
reasons — and the second is the one that matters:

**Direction.** A backlink earns value when an authority links **to** you.
traindecade → IG moves our ~20 quarterly readers into a feed that has measured
**0 attributed sessions in 90 days**. That helps Instagram, not the site.

**Identity.** `@vincenty3d` carries his real name. It sat beside a fitness blog
he may not want attached to his banking identity, earning measured zero.

Rule applied: **expose identity only when it pays.** Right now it does not.

`@ideafactoryone` and `@gaincut.app` remain name reservations — see the
`distribution-channels` skill before re-adding any social link.

## ⚠️ Two tests encoded the OLD decisions and had to be flipped

This is the useful part. Both suites asserted the previous state as correct:

```
test_gaincut_connector.py   required instagram.com/vincenty3d in footer
                            ("site is a dead end again" on absence)
test_email_capture.py       required 0 EN posts to carry the form
```

Changing the code alone would have left two green tests asserting the opposite
of the decision. Both were updated **with the reasoning inline**, so a future
agent reads *why* rather than mechanically restoring the old assertion.

**Rule:** a test that encodes a past decision must be edited when the decision
changes — otherwise the suite becomes a ratchet against the owner.

## Verification

```
test_multilingual.py        PASS
check_no_stray_emphasis.py  PASS
test_gaincut_connector.py   PASS (IG absence now asserted)
test_ga_event_binding.py    PASS
test_email_capture.py       PASS 90/90 posts wired (EN+ZH) · 90/90 slugs
                                 · 0 leaks in 1003 files · 0 IG links
```

Rendered output confirmed:

```
EN  "The next one, straight to your inbox"
    "An occasional letter: ... survives scrutiny ... No ads."
ZH  "不定時一封信：一個經得起檢驗的訓練或營養結論，附上研究出處。沒有廣告，隨時可退訂。"
footer  instagram.com/vincenty3d → 0 occurrences
```

## Pillar

💼 BUSINESS · Vehicle: IdeaFactory.one · Product: GainCut
