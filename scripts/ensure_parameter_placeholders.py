#!/usr/bin/env python3
"""Add intentionally blank parameter-table placeholders and emit their maintenance CSV."""

from __future__ import annotations

import csv
import re
from pathlib import Path


MISSING_SECTION = {
    "commands/bazhuayu/7TUoxB.mdx",
    "commands/dingtalk/gM80NN.mdx",
    "commands/email/dtd5Rb.mdx",
    "commands/email/RlCVx4.mdx",
    "commands/feishu/vPhs0M.mdx",
    "commands/google/xnN98S.mdx",
    "commands/group-notification/XZBe1j.mdx",
}
MISSING_TABLE = {
    "commands/data-processing/createdictionarycommand.mdx",
    "commands/os/clearclipboarddatacommand.mdx",
    "commands/others/catchcommand.mdx",
    "commands/others/endtrycommand.mdx",
    "commands/others/trycommand.mdx",
}
TABLE = "| 参数 | 说明 |\n| --- | --- |"


def title(text: str) -> str:
    match = re.search(r'(?m)^title:\s*["\'](.+?)["\']\s*$', text)
    if not match:
        raise ValueError("front matter title not found")
    return match.group(1)


def add_missing_section(text: str) -> str:
    if re.search(r"(?m)^## 参数说明\s*$", text):
        if not re.search(r"(?m)^## 使用示例\s*$", text):
            updated, count = re.subn(
                re.escape(TABLE),
                TABLE + "\n\n## 使用示例",
                text,
                count=1,
            )
            if count != 1:
                raise ValueError("parameter placeholder table not found")
            return updated
        return text
    front_matter = re.match(r"\A---\r?\n.*?\r?\n---\r?\n", text, flags=re.DOTALL)
    if not front_matter:
        raise ValueError("front matter not found")
    insert_at = front_matter.end()
    return text[:insert_at] + f"\n## 参数说明\n\n{TABLE}\n\n## 使用示例\n" + text[insert_at:]


def add_missing_tables(text: str) -> str:
    if re.search(r"(?m)^\s*\|\s*参数\s*\|\s*说明\s*\|\s*$", text):
        return text
    result, count = re.subn(
        r"(?m)^(\s*)本指令暂无(?:常规|高级)?参数。\s*$",
        lambda match: f"{match.group(1)}{TABLE.replace(chr(10), chr(10) + match.group(1))}",
        text,
    )
    if count == 0:
        raise ValueError("no empty parameter placeholder found")
    return result


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    rows = []
    for relative in sorted(MISSING_SECTION | MISSING_TABLE):
        path = root / relative
        text = path.read_text(encoding="utf-8")
        issue = "missing_parameter_section" if relative in MISSING_SECTION else "missing_parameter_table"
        updated = add_missing_section(text) if relative in MISSING_SECTION else add_missing_tables(text)
        path.write_text(updated, encoding="utf-8", newline="\n")
        rows.append({
            "command_title": title(text),
            "relative_path": relative,
            "category": Path(relative).parts[1],
            "issue": issue,
            "placeholder_inserted": "yes",
            "notes": "Parameter and description cells intentionally left blank for future maintenance.",
        })

    report = root / "reports" / "missing-parameter-descriptions.csv"
    report.parent.mkdir(exist_ok=True)
    with report.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"updated={len(rows)} report={report.relative_to(root)}")


if __name__ == "__main__":
    main()
