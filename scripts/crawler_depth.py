#!/usr/bin/env python3
"""Baseline + follow-up measurement for the related-posts change (2026-11-26).

WHY: the related-posts gate proves links EXIST and RESOLVE. It does NOT prove
crawlers follow them. That is a separate, time-based measurement against the
Cloudflare D1 crawler log — and it is the only thing that can justify calling
the change a success.

Run this BEFORE deploying and again ~2 weeks later, then compare.

    python3 scripts/crawler_depth.py            # current reading
    python3 scripts/crawler_depth.py --note "baseline"

WHAT IT MEASURES
  distinct EN post paths fetched by REAL AI retrieval bots (not Amazonbot, not
  BingBot — those crawl for search/retail, not for AI answers).

⚠️ Log noise warning: the total row count is ~29% 404s from credential-hunting
scanners. Never quote the raw total as "AI traffic".
"""
import json
import subprocess
import sys
from datetime import datetime, timezone

DB = "ai_crawler_log"
# Bots whose fetching tells you something about AI *answer* visibility.
AI_BOTS = [
    "GPTBot", "OAI-SearchBot", "PerplexityBot", "Perplexity-User",
    "ChatGPT-User", "ClaudeBot", "Claude-User", "Claude-SearchBot",
    "Google-Extended",
]


def q(sql: str) -> list[dict]:
    out = subprocess.run(
        ["npx", "wrangler", "d1", "execute", DB, "--remote", "--json", f"--command={sql}"],
        capture_output=True, text=True, cwd="/Users/home/Projects/ai-crawler-logger",
    )
    raw = out.stdout
    i = raw.find("[")
    if i == -1:
        raise RuntimeError(f"no JSON in output:\n{raw[:500]}\n{out.stderr[:500]}")
    return json.loads(raw[i:])[0]["results"]


def main():
    note = ""
    if "--note" in sys.argv:
        note = sys.argv[sys.argv.index("--note") + 1]

    bots = ",".join(f"'{b}'" for b in AI_BOTS)
    depth = q(f"SELECT COUNT(DISTINCT path) n FROM ai_fetches "
              f"WHERE path LIKE '/posts/%' AND bot IN ({bots})")[0]["n"]
    total_posts = 45
    per_bot = q(f"SELECT bot, COUNT(*) n, MAX(ts) last FROM ai_fetches "
                f"WHERE bot IN ({bots}) GROUP BY bot ORDER BY n DESC")
    noise = q("SELECT COUNT(*) n FROM ai_fetches WHERE status=404")[0]["n"]
    total = q("SELECT COUNT(*) n FROM ai_fetches")[0]["n"]

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    print(f"\n{'='*58}")
    print(f"CRAWLER DEPTH READING — {stamp} {note and '['+note+']'}")
    print(f"{'='*58}")
    print(f"  EN post pages ever fetched by real AI bots : {depth} / {total_posts}"
          f"  ({100*depth/total_posts:.0f}%)")
    print(f"  Raw log rows                               : {total}")
    print(f"  of which 404 (scanner noise)               : {noise}"
          f"  ({100*noise/total:.0f}%)")
    print("\n  By bot:")
    for r in per_bot:
        print(f"    {r['bot']:<18}{r['n']:>5}   last {r['last'][:16]}")
    print(f"\n  BASELINE TO BEAT: {depth}/{total_posts} post pages.")
    print("  Re-run in ~2 weeks. If depth has not risen, the change did not work")
    print("  and should be said so plainly rather than defended.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
