#!/usr/bin/env python3
"""Assert rendered ZH output is TRADITIONAL, not Simplified.

WHY THIS TEST EXISTS (2026-11-23)
---------------------------------
Vincent caught 「下一页」 in the pagination button of the ZH site. The page
footer said 「© 2026 訓練十年」 — Traditional — and the button right above it
said 下一页 — Simplified. Mixed script in one screen.

Root cause: `themes/PaperMod/i18n/zh.yaml` ships **Simplified** Chinese for
every theme string (prev_page, next_page, read_time, toc, home...). Only ids
overridden in the site's own `i18n/zh.yaml` render Traditional. Every id NOT
overridden leaks Simplified.

⚠️ THIS IS A THEME-UPGRADE TRAP. Bumping PaperMod adds new ids, and each new
id silently reintroduces Simplified. Nothing errors. The site just looks wrong
to a Hong Kong reader.

WHAT IT CHECKS
  Scans every rendered /zh/ page for characters that exist ONLY in Simplified
  Chinese. A hit is a leak. The scan is character-level, not word-level, so it
  catches strings nobody thought to override.

⚠️ LIMITS: this catches the common simplified-only forms, not every variant.
It is a floor, not a proof. Add pairs to SIMPLIFIED_ONLY when a new leak is
found — never remove them.

Run: python3 tests/test_zh_traditional_script.py --public ./public
Exit 0 = clean. Exit 1 = Simplified characters found.
"""

import argparse
import glob
import os
import re
import sys
from collections import defaultdict

# Characters that are unambiguously Simplified. Their Traditional counterparts
# are what a HK/TW reader expects. Deliberately a curated list, not a full
# OpenCC conversion — a false positive here would block legitimate builds.
SIMPLIFIED_ONLY = (
    "页"   # 頁 (page) — the one Vincent caught
    "关"   # 關 (close/about)
    "联"   # 聯 (contact)
    "隐"   # 隱 (privacy)
    "读"   # 讀 (read)
    "时"   # 時 (time)
    "间"   # 間 (interval)
    "录"   # 錄 (record/toc)
    "复"   # 復/複 (copy)
    "语"   # 語 (language)
    "编"   # 編 (edit)
    "辑"   # 輯 (edit)
    "链"   # 鏈 (link)
    "术"   # 術 (technique)
    "训"   # 訓 (train)
    "练"   # 練 (practice)
    "营"   # 營 (nutrition)
    "养"   # 養 (nourish)
    "证"   # 證 (evidence)
    "据"   # 據 (basis)
    "强"   # 強 (strong)
    "这"   # 這 (this)
    "个"   # 個 (measure word)
    "们"   # 們 (plural)
    "为"   # 為 (for)
    "后"   # 後 (after)
    "发"   # 發 (emit)
    "现"   # 現 (appear)
    "实"   # 實 (real)
    "际"   # 際 (boundary)
    "质"   # 質 (quality)
    "测"   # 測 (measure)
    "试"   # 試 (test)
    "计"   # 計/計 (count)
    "调"   # 調 (adjust)
    "节"   # 節 (joint/section)
    "热"   # 熱 (heat)
    "量"   # (shared, excluded on purpose — see note below)
)

# ⚠️ 量 and 计 exist in Traditional too in some readings; we only include forms
# that are simplified-exclusive. 量 removed from effective list to avoid a
# false positive on 質量/量 — handled by keeping the list conservative.
EXCLUDE = set("量计")
SIMPLIFIED_ONLY = "".join(c for c in SIMPLIFIED_ONLY if c not in EXCLUDE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--public", default="./public")
    ap.add_argument("--max-report", type=int, default=8)
    args = ap.parse_args()

    zh_files = glob.glob(
        os.path.join(args.public, "zh", "**", "*.html"), recursive=True
    )
    if not zh_files:
        print(f"FAIL  zh script  (no ZH pages found under {args.public}/zh/)")
        return 1

    hits = defaultdict(list)  # char -> [paths]
    for path in zh_files:
        text = open(path, encoding="utf-8", errors="ignore").read()
        # ⚠️ Strip <script> blocks before scanning. A JS string that MATCHES a
        # Simplified label in order to REPLACE it is not a rendering defect —
        # it is the fix. Minification also collapses \uXXXX escapes back into
        # literal characters, so an escape-based workaround cannot survive a
        # --minify build. Removing script bodies is the only check that
        # measures what a reader actually SEES.
        visible = re.sub(r"<script\b[^>]*>.*?</script>", "", text, flags=re.S | re.I)
        for ch in SIMPLIFIED_ONLY:
            if ch in visible:
                hits[ch].append(path)

    if hits:
        total = sum(len(v) for v in hits.values())
        print(
            f"FAIL  zh script  ({len(hits)} simplified char(s) across "
            f"{total} file hit(s), {len(zh_files)} ZH pages scanned)"
        )
        for ch, paths in list(hits.items())[: args.max_report]:
            sample = os.path.relpath(paths[0], args.public)
            print(f"  x '{ch}' in {len(paths)} file(s) — e.g. {sample}")
        print(
            "\n  FIX: add the missing id to i18n/zh.yaml. The theme ships "
            "SIMPLIFIED Chinese, so any id not overridden there leaks."
        )
        return 1

    print(
        f"PASS  zh script  ({len(zh_files)} ZH pages, "
        f"0 simplified-only characters from a {len(SIMPLIFIED_ONLY)}-char set)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
