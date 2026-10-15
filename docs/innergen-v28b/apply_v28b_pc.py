#!/usr/bin/env python3
"""
Apply v28b (facts update mode + standard pages) to the PC Slide Master source.

Works on top of v28 alone or v28 + v30: it copies the two new scripts and the
updated standard-decks doc, then inserts small blocks into files v30 also ships
(SKILL.chat.md, innergen_qaqc.py, qaqc-v21.json, build_chat_skill.py) instead of
overwriting them. Safe to run twice; keeps each file's line endings.

Usage (from PowerShell):
    python "<this folder>\\apply_v28b_pc.py" "B:\\CODEX\\Slide Master"
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

SKILL_BLOCKS = [
    ("수행 체계) reuses the §1 common blocks there.\n", "**Refreshing an existing deck.**", """
**Refreshing an existing deck.** When the user only wants an old PPTX brought up
to date (numbers, phone, address, brand spelling) and not a new deck, do not
redraw it. Write a corrected copy that keeps every run's font, size and color:

```bash
python3 ${SKILL_DIR}/scripts/innergen_facts_update.py <old>.pptx --dry-run
python3 ${SKILL_DIR}/scripts/innergen_facts_update.py <old>.pptx -o /mnt/user-data/outputs/<name>_갱신.pptx
python3 ${SKILL_DIR}/scripts/innergen_facts_check.py --pptx /mnt/user-data/outputs/<name>_갱신.pptx
```

Only `confirmed` ledger values are applied; values marked 확인 필요 are listed
and skipped until the user confirms them (then add `--include-unconfirmed`). The
input file is never overwritten. Hand off the copy with the change list
(`P05 '300만 톤+' → '250만 톤+'`) and anything still awaiting confirmation;
images (logos, staff cards) are not touched.
"""),
    ("Read `spec_lock.md` and `templates/design_spec.md` before the first page.\n", "innergen_standard_pages.py", """
For `company_intro` and `innercarry_intro`, write the fixed pages straight from
the ledger before drawing the rest:

```bash
python3 ${SKILL_DIR}/scripts/innergen_standard_pages.py /tmp/<deck> --deck <company_intro|innercarry_intro> [--date "2026. 10."] [--client-logo <file>]
```

It fills cover, company overview table, business-area grid, key-number page
(company_intro) and closing at the §A/§B page numbers in `svg_output/`, leaves
out 확인 필요 values unless `--include-unconfirmed`, and lists what still needs
an image or a confirmation. Skip any page the confirmed outline changed
(`--pages cover,overview,…`), and check the written pages like any other.
"""),
    ("| Slide design (layouts, chrome) | Slide Master source templates and locks | `svg_quality_checker.py`, `innergen_qaqc.py` |\n",
     "| Fixed pages (cover,", """| Fixed pages (cover, overview, areas, key numbers, closing) | `innergen_standard_pages.py` (`DECKS` page numbers and governing lines; values come from the ledger) | run it on a fresh `start_deck.py` project, then `svg_quality_checker.py` |
| Refreshing old decks after a ledger change | nothing to edit | `innergen_facts_update.py <deck>.pptx --dry-run`, then `-o <copy>` |
"""),
]

QAQC_OLD = '        if any(body.endswith(e) for e in tr["sentence_endings"]) or body.endswith("?"):\n'
QAQC_NEW = ('        noun_ok = any(body.endswith(w) for w in tr.get("noun_exceptions", []))  # 회사 개요, 다음\n'
            '        if (not noun_ok and any(body.endswith(e) for e in tr["sentence_endings"])) or body.endswith("?"):\n')

JSON_OLD = '      "음"\n    ],\n    "numbering_regex"'
JSON_NEW = ('      "음"\n    ],\n    "noun_exceptions": [\n      "개요",\n      "주요",\n      "중요",\n      "필요",\n'
            '      "수요",\n      "포함",\n      "다음"\n    ],\n    "numbering_regex"')


def edit(path: Path, fn) -> str:
    raw = path.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    new, note = fn(text)
    if new != text:
        path.write_bytes(new.replace("\n", nl).encode("utf-8"))
    return f"{path.name}: {note}"


def main(root: str) -> int:
    root_p = Path(root)
    pm = root_p / ".claude" / "skills" / "ppt-master" / "scripts"
    doc = root_p / "docs" / "styles" / "innergen"
    if not (pm / "innergen_facts_check.py").exists():
        print("upstream-v28을 먼저 반영하세요 (innergen_facts_check.py 없음)")
        return 1
    for name in ("innergen_facts_update.py", "innergen_standard_pages.py"):
        shutil.copyfile(HERE / name, pm / name)
        print(f"copied {name}")
    shutil.copyfile(HERE / "standard-decks-v28.md", doc / "standard-decks-v28.md")
    print("copied standard-decks-v28.md")

    def skill(text):
        notes = []
        for anchor, marker, block in SKILL_BLOCKS:
            if marker in text:
                notes.append("already")
                continue
            if anchor not in text:
                raise SystemExit(f"SKILL.chat.md: anchor not found: {anchor[:50]}")
            text = text.replace(anchor, anchor + block, 1)
            notes.append("added")
        return text, ", ".join(notes)

    def qaqc(text):
        if "noun_exceptions" in text:
            return text, "already"
        if QAQC_OLD not in text:
            raise SystemExit("innergen_qaqc.py: T02 line not found")
        return text.replace(QAQC_OLD, QAQC_NEW, 1), "T02 noun exceptions added"

    def rules(text):
        if "noun_exceptions" in text:
            return text, "already"
        if JSON_OLD not in text:
            raise SystemExit("qaqc-v21.json: title.sentence_endings not found")
        return text.replace(JSON_OLD, JSON_NEW, 1), "noun_exceptions added"

    def build(text):
        if "innergen_standard_pages.py" in text:
            return text, "already"
        new = re.sub(r"ENTRY_SCRIPTS = \(", 'ENTRY_SCRIPTS = ("innergen_facts_update.py", "innergen_standard_pages.py", ', text, count=1)
        if new == text:
            raise SystemExit("build_chat_skill.py: ENTRY_SCRIPTS not found")
        return new, "ENTRY_SCRIPTS extended"

    print(edit(pm / "chat_skill" / "SKILL.chat.md", skill))
    print(edit(pm / "innergen_qaqc.py", qaqc))
    print(edit(doc / "qaqc-v21.json", rules))
    print(edit(pm / "build_chat_skill.py", build))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
