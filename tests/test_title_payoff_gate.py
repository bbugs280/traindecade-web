#!/usr/bin/env python3
"""Plain-language title gate — the title must state a PAYOFF, not just a topic.

Measured failure this test locks in (2026-11-26):
`pump-or-real-muscle` EN sat at **36 impressions, position 7.2, ZERO clicks**.
Position 7.2 is page 1 — the page was being SEEN and not clicked. Its ZH twin,
same post and same structure, earned 84 impressions / 2 clicks at pos 6.5.
The only material difference was the title:

    EN  "Pump or Real Muscle? How to Tell the Difference"   ← states a topic
    ZH  "充血還是真肌肉？如何分辨"                              ← same shape

The EN title poses a question and promises nothing. A reader who does not already
want the answer has no reason to click. This is a TITLE defect, not an authority
gap — so it must be catchable before shipping, not diagnosed from GSC a month later.

The gate is deliberately narrow. It does NOT police style. It catches one shape:
a title made only of a question/topic with no outcome, benefit, named object,
number, or specificity marker.
"""
from __future__ import annotations

import re
from pathlib import Path

POSTS_EN = Path(__file__).resolve().parent.parent / "content" / "posts"

# A payoff signal: something the reader GETS, or a concrete anchor.
PAYOFF_MARKERS = [
    r"\d",                                   # a number: "3 sets", "after 40"
    r"\b(because|so that|why|when|until|before|after)\b",
    r"\b(fix|fixing|stop|start|avoid|build|keep|lose|gain|add|cut|skip|choose|swap|use|pays|beat|beats)\b",
    r"\b(the reason|the mistake|the cost|the fix|what works|truth|evidence|data)\b",
    r"\b(slower|faster|cheaper|stronger|leaner|worse|better|wrong|right)\b",
    r"\b(my|i)\b",                           # first-person concrete detail
    r"\b(mistake|myth|trap|lie|problem|signal|limit|rule|armor|number|numbers)\b",
    r"\b(ignore|ignored|skipping|missing|misses|miss)\b",
    r"\b(not|never|actually|probabl[ey])\b",
    r"\b(you|your|you're|youre)\b",          # direct address = stakes named
    r"\b(skill|weeks?|hours?|days?|months?)\b",
    # A concrete named object or scene = the hook carries specificity. Without this
    # class the gate false-positives on real hooks ("The Shirt That Tore at the Elbow").
    r"\b(shirt|elbow|knee|shoulder|back|bar|plate|belt|shoe|scale|mirror|photo|timer)\b",
    r"\b(knew|learned|found|found out|realised|realized|turns out)\b",
    # ⚠️ 2026-11-26: the two titles above were written with real payoffs and the
    # gate rejected BOTH, because every word was outside this vocabulary. That is
    # the known weakness of an allowlist — it is blind to payoff it has not seen.
    # These additions cover the shapes actually in use, not arbitrary synonyms.
    r"\b(symptom|symptoms|sign|signs)\b",        # names what to look for
    r"\b(blame|blamed|blaming|nobody|no one)\b", # names the wrong explanation
    r"\b(deadline|reason|reasons|worked|works)\b",
    r"\b(how long|how much|how many|when to)\b", # a bounded question
]

# Shapes that are a topic, not a payoff — a bare question or a guide label.
TOPIC_ONLY = [
    r"^how to tell the difference$",
    r"^(the )?(beginner'?s? guide|complete guide|ultimate guide|everything you need to know)$",
    r"^(what|why) (is|are) [a-z ]+\?$",
    r"^[a-z ]+\?$",                          # a bare topic question, nothing else
]


def title_of(path: Path) -> str | None:
    m = re.search(r'^title:\s*"?(.*?)"?\s*$', path.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def has_payoff(title: str) -> bool:
    """True only if the title names an outcome, anchor, or stakes.

    ⚠️ Topic-only shapes are checked FIRST and veto — otherwise a title like
    "How to Tell the Difference" passes on the word "difference" alone.
    """
    low = title.lower().strip()
    if any(re.search(p, low) for p in TOPIC_ONLY):
        return False
    return any(re.search(p, low) for p in PAYOFF_MARKERS)


def test_the_known_bad_title_would_fail():
    """RED-proof that the gate can fail. This is the exact shipped title."""
    bad = "Pump or Real Muscle? How to Tell the Difference"
    assert not has_payoff(bad), (
        "the gate passed the title that measurably earned 36 impr / 0 clicks at pos 7.2")


def test_topic_only_shapes_are_named():
    for t in ["How to Tell the Difference",
              "The Complete Guide",
              "What Is Body Recomposition?"]:
        low = t.lower().rstrip("?")
        caught = any(re.search(p, low + ("?" if t.endswith("?") else "")) for p in TOPIC_ONLY)
        assert caught or not has_payoff(t), f"topic-only shape not caught: {t}"


def test_good_titles_pass():
    for t in [
        "Creatine After 40: 3-5 g Is Not Enough",
        "Why Your Pump Disappears and Real Muscle Doesn't",
        "The Reuse Trap That Cost Me Six Months",
        "Cut vs Gain: The Signal Nobody Checks",
    ]:
        assert has_payoff(t), f"false positive on a title with a payoff: {t}"


def find_offenders() -> list[str]:
    ALLOWED = {
        "welcome": "site intro, not a search entry point — nobody arrives on it via SERP",
    }
    out = []
    for p in sorted(POSTS_EN.glob("*.md")):
        if p.stem in ALLOWED:
            continue
        t = title_of(p)
        if t and not has_payoff(t):
            out.append(f"{p.name}: {t}")
    return out


# ⚠️ KNOWN BACKLOG — titles already shipped with a topic-only shape.
# These are NOT exempt as "fine". They are recorded here so the gate can hold the
# line on NEW posts without the suite going red on pre-existing debt. Removing an
# entry (by fixing the title) must keep this list shrinking, never growing.
# Each entry needs a measured reason to be here.
#
# 2026-11-26: both original entries were fixed and removed — see
# `docs/changes/2026-11-26.md`. The list is now empty, which is the correct state:
# any new entry here is new debt and needs its own measured justification.
KNOWN_TOPIC_ONLY: dict[str, str] = {}


def test_backlog_is_empty_or_justified():
    """An entry here is debt. It must never be added without a measured reason."""
    for name, reason in KNOWN_TOPIC_ONLY.items():
        assert reason and len(reason) > 20, (
            f"{name} is parked in the backlog with no real justification: {reason!r}")


def test_no_NEW_topic_only_titles():
    """Gate on new debt only. Pre-existing debt is enumerated, not hidden."""
    offenders = [o for o in find_offenders() if o.split(":")[0] not in KNOWN_TOPIC_ONLY]
    assert not offenders, (
        "NEW EN post(s) whose title states a topic but no payoff — these will be "
        "seen and not clicked:\n  " + "\n  ".join(offenders))


def test_backlog_list_does_not_grow_stale():
    """A fixed title must be removed from the backlog list, or the list lies."""
    live = {o.split(":")[0] for o in find_offenders()}
    stale = [k for k in KNOWN_TOPIC_ONLY if k not in live]
    assert not stale, (
        "these are in KNOWN_TOPIC_ONLY but no longer offend — fix the list:\n  "
        + "\n  ".join(stale))


if __name__ == "__main__":
    import sys
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                fails += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if fails else 0)
