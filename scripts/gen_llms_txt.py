#!/usr/bin/env python3
"""Generate llms.txt from the actual content directory.

WHY: the file was hand-maintained and silently drifted to 6 of 74 posts -
including omitting the site's only converting page. Generating from source
means it cannot go stale.

HONEST NOTE ON EFFECTIVENESS (2026-09-19 research):
  llms.txt is NOT a discovery/ranking lever. Google has stated it does not
  support it (Gary Illyes, Search Central Live 2025; Mueller likens it to the
  keywords meta tag). Crawl studies: 515M LLM-bot events yielded 408 requests
  to /llms.txt; Ahrefs found 97% of files got zero requests in a month.
  It IS useful for inference-time context loading (an agent already on the
  site parsing clean Markdown). Treat as cheap insurance, not a traffic lever.

Usage:  python3 scripts/gen_llms_txt.py [--apply]
"""
import pathlib
import re
import sys

BASE = pathlib.Path.home() / "Projects" / "traindecade-web"
SITE = "https://traindecade.com"

HEADER = """# Train Decade

> Train Decade is a fitness and health resource for men in their 30s, 40s, and 50s. Evidence-based training, nutrition, and body recomposition — focused on the long game (years, not weeks), with clear sourcing and bilingual English/Chinese content.

"""


def clean(s):
    """Unescape backslash-escaped quotes Hugo YAML carries through."""
    if not s:
        return s
    return s.replace('\\"', '"').replace("\\'", "'")


def parse_frontmatter(text):
    """Pull title/description/date/translationKey from a Hugo post."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    fm = text[3:end] if end > 0 else ""
    d = {}
    for key in ("title", "description", "date", "translationKey", "weight"):
        m = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', fm, re.M)
        if m:
            d[key] = clean(m.group(1).strip())
    return d


def collect(lang_dir, url_prefix):
    out = []
    d = BASE / lang_dir / "posts"
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.md")):
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        if not fm or not fm.get("title"):
            continue
        out.append(
            {
                "slug": f.stem,
                "title": fm["title"],
                "desc": fm.get("description", ""),
                "url": f"{SITE}{url_prefix}/posts/{f.stem}/",
            }
        )
    return out


def main():
    apply = "--apply" in sys.argv
    en = collect("content", "")
    zh = collect("content-zh", "/zh")

    lines = [HEADER]
    lines.append(f"## English posts ({len(en)})\n")
    for p in en:
        desc = f": {p['desc']}" if p["desc"] else ""
        lines.append(f"- [{p['title']}]({p['url']}){desc}\n")

    lines.append(f"\n## 中文文章 ({len(zh)})\n")
    for p in zh:
        desc = f"：{p['desc']}" if p["desc"] else ""
        lines.append(f"- [{p['title']}]({p['url']}){desc}\n")

    lines.append(
        "\n## About\n"
        "Train Decade is published in English and Chinese (繁體中文 at /zh/). "
        "All claims are sourced to peer-reviewed or institutional studies, "
        "listed in each article's Sources section. No crash diets, no "
        "quick-fix noise.\n"
    )

    body = "".join(lines)
    target = BASE / "static" / "llms.txt"

    if apply:
        target.write_text(body, encoding="utf-8")
        print(f"WROTE {target}")
    else:
        print(f"DRY RUN - {len(en)} EN + {len(zh)} ZH posts")
        print(f"target: {target}")
        print(f"chars: {len(body)}  (current: {len(target.read_text(encoding='utf-8'))})")
    print(f"total posts covered: {len(en) + len(zh)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
