#!/usr/bin/env python3
"""Audit whether in-scope command examples are understandable and reproducible."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from audit_and_crop_command_images import command_docs
from validate_command_images import IMAGE_RE, section, title, visible_content
from strict_command_quality_audit import SCOPE_CATEGORIES


LOGIC_RE = re.compile(r"(?ms)\*\*该流程执行逻辑：\*\*\s*(.*?)(?=^###\s+效果展示|^<Info>|\Z)")
PLACEHOLDER_RE = re.compile(r"^(?:无|暂无|略|待补充|后续补充|todo|tbd)[。.!！]?$", re.I)
SEQUENCE_RE = re.compile(r"(?:^|\n)\s*(?:\d+[.、)]|[-*]\s+)|先.+再|首先|然后|最后|随后|依次|→|--->", re.M)
OUTPUT_RE = re.compile(
    r"保存|输出|返回|生成|结果|写入|显示|关闭|删除|发送|结束|继续执行|"
    r"确认|得到|读取|打印|增加|新增|修改|更新|移动|打开|触发|出现|进入|完成|生效"
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    documents = [
        path for path in command_docs(root)
        if path.relative_to(root / "commands").parts[0] in SCOPE_CATEGORIES
    ]
    rows: list[dict[str, str]] = []

    for document in documents:
        text = document.read_text(encoding="utf-8")
        page_title = title(text, document.stem)
        usage = section(text, "## 使用示例", "### 效果展示")
        match = LOGIC_RE.search(usage)
        logic = visible_content(match.group(1)) if match else ""
        raw_logic = match.group(1).strip() if match else ""
        usage_images = len(IMAGE_RE.findall(usage))
        issues: list[str] = []

        if not logic or PLACEHOLDER_RE.fullmatch(logic):
            issues.append("empty_or_placeholder")
        if len(logic) < 30:
            issues.append("too_short")
        if usage_images >= 2 and not SEQUENCE_RE.search(raw_logic):
            issues.append("multiple_images_without_sequence")
        if not OUTPUT_RE.search(logic):
            issues.append("missing_result_or_output")
        if "--->" in raw_logic or raw_logic.count("-->") >= 2:
            issues.append("arrow_chain_needs_steps")
        if page_title not in logic and f"【{page_title}】" not in raw_logic and "本指令" not in raw_logic:
            issues.append("command_not_named")

        if issues:
            rows.append({
                "command_title": page_title,
                "relative_path": document.relative_to(root).as_posix(),
                "category": document.relative_to(root / "commands").parts[0],
                "logic_length": str(len(logic)),
                "usage_images": str(usage_images),
                "issues": ";".join(issues),
                "logic": re.sub(r"\s+", " ", raw_logic),
            })

    report = root / "reports" / "execution-logic-clarity-audit.csv"
    fields = ["command_title", "relative_path", "category", "logic_length", "usage_images", "issues", "logic"]
    with report.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"documents={len(documents)} candidates={len(rows)} report={report.relative_to(root)}")


if __name__ == "__main__":
    main()
