#!/usr/bin/env python3
"""Validate command-page structure, semantics and local image integrity."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from PIL import Image

from audit_and_crop_command_images import GUIDE_PAGES, command_docs


HEADINGS = ("## 指令说明", "## 参数说明", "## 使用示例", "### 效果展示")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((?:\./)?([^\)#]+)(?:#[^\)]*)?\)")
CIRCLED_CATEGORIES = {
    "mouse-keyboard", "datatable", "excel", "os", "bazhuayu", "email",
    "data-processing", "group-notification", "feishu", "dingtalk", "google",
    "ai", "database", "others",
}


def section(text: str, heading: str, next_heading: str | None) -> str:
    start = re.search(rf"(?m)^{re.escape(heading)}\s*$", text)
    if not start:
        return ""
    body_start = start.end()
    if next_heading:
        end = re.search(rf"(?m)^{re.escape(next_heading)}\s*$", text[body_start:])
        if end:
            return text[body_start:body_start + end.start()]
    return text[body_start:]


def visible_content(text: str) -> str:
    text = IMAGE_RE.sub("", text)
    text = re.sub(r"(?ms)<Info>.*?</Info>", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", "", text)


def title(text: str, fallback: str) -> str:
    match = re.search(r'(?m)^title:\s*["\'](.+?)["\']\s*$', text)
    return match.group(1) if match else fallback


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=Path("reports/command-page-audit.csv"))
    parser.add_argument("--no-fail", action="store_true", help="write the report without returning an error")
    parser.add_argument("--scope", choices=("all", "circled"), default="all")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    documents = command_docs(root)
    all_command_docs = sorted(
        path for path in (root / "commands").rglob("*.mdx")
        if len(path.relative_to(root / "commands").parts) >= 2
    )
    if args.scope == "circled":
        documents = [
            path for path in documents
            if path.relative_to(root / "commands").parts[0] in CIRCLED_CATEGORIES
        ]
        all_command_docs = [
            path for path in all_command_docs
            if path.relative_to(root / "commands").parts[0] in CIRCLED_CATEGORIES
        ]
    guide_count = sum(
        path.relative_to(root).as_posix() in GUIDE_PAGES for path in all_command_docs
    )
    rows: list[dict[str, str]] = []
    references = 0

    def issue(path: Path, page_title: str, kind: str, section_name: str, notes: str) -> None:
        rows.append({
            "command_title": page_title,
            "relative_path": path.relative_to(root).as_posix(),
            "category": path.relative_to(root / "commands").parts[0],
            "section": section_name,
            "issue": kind,
            "notes": notes,
        })

    # Image integrity applies to command pages and the ten guide/module pages.
    for document in all_command_docs:
        text = document.read_text(encoding="utf-8")
        page_title = title(text, document.stem)
        refs = IMAGE_RE.findall(text)
        references += len(refs)
        paths = [ref for _, ref in refs]
        if len(paths) != len(set(paths)):
            issue(document, page_title, "duplicate_image_reference", "images", "同一页面重复引用同一图片。")
        for _, ref in refs:
            if ref.startswith(("http://", "https://", "data:")):
                continue
            image_path = document.parent / ref
            if not image_path.exists():
                issue(document, page_title, "missing_image", "images", ref)
                continue
            try:
                with Image.open(image_path) as image:
                    image.verify()
            except Exception as error:
                issue(document, page_title, "invalid_image", "images", f"{ref}: {error}")

    # The standard four-section contract applies only to actual command pages.
    for document in documents:
        text = document.read_text(encoding="utf-8")
        page_title = title(text, document.stem)
        found = [match.group(1) for match in re.finditer(
            r"(?m)^(## 指令说明|## 参数说明|## 使用示例|### 效果展示)\s*$", text
        )]
        if found != list(HEADINGS):
            issue(document, page_title, "section_order", "page", " > ".join(found) or "未找到标准章节。")

        instruction = section(text, HEADINGS[0], HEADINGS[1])
        parameter = section(text, HEADINGS[1], HEADINGS[2])
        usage = section(text, HEADINGS[2], HEADINGS[3])
        effect = section(text, HEADINGS[3], None)

        # 兼容历史的“描述：”标签写法和当前直接使用正文段落的写法。
        # 指令说明的关键要求是存在可读的非空描述，而不是固定的 Markdown 标签。
        description = re.search(r"(?m)^\*\*描述：\*\*\s*(.+?)\s*$", instruction)
        if not description:
            description = re.search(
                r"(?m)^(?!\s*(?:#|<|!|\||```))\s*\S.*\S\s*$",
                instruction,
            )
        if not description:
            issue(document, page_title, "missing_description", "指令说明", "缺少非空指令描述。")
        if IMAGE_RE.search(instruction):
            issue(document, page_title, "image_in_instruction", "指令说明", "指令说明不应放置正文图片。")

        if not IMAGE_RE.search(parameter):
            issue(document, page_title, "missing_parameter_image", "参数说明", "缺少客户端默认态参数截图。")
        has_table = bool(
            re.search(r"(?m)^\s*\|\s*参数\s*\|\s*说明\s*\|\s*$", parameter)
            and re.search(r"(?m)^\s*\|\s*\*\*.+?\*\*\s*\|", parameter)
        )
        explicit_no_params = bool(re.search(r"无(?:可配置|常规)?参数|指令本身无参数|仅作为标记", parameter))
        if not has_table and not explicit_no_params:
            issue(document, page_title, "missing_parameter_details", "参数说明", "缺少参数表或无参数说明。")

        logic = re.search(r"(?ms)\*\*该流程执行逻辑：\*\*\s*(.*?)(?=^<Info>|\Z)", usage)
        if not logic or not visible_content(logic.group(1)):
            issue(document, page_title, "missing_execution_logic", "使用示例", "缺少标准流程执行逻辑。")
        if not visible_content(effect) and not IMAGE_RE.search(effect):
            issue(document, page_title, "missing_effect", "效果展示", "效果展示为空。")

        for alt, ref in IMAGE_RE.findall(parameter):
            if re.search(r"使用示例|效果展示", alt):
                issue(document, page_title, "semantic_image_candidate", "参数说明", f"{ref}: {alt}")
        for alt, ref in IMAGE_RE.findall(usage):
            if re.search(r"参数面板|指令参数|效果展示", alt):
                issue(document, page_title, "semantic_image_candidate", "使用示例", f"{ref}: {alt}")
        for alt, ref in IMAGE_RE.findall(effect):
            if re.search(r"参数面板|指令参数", alt):
                issue(document, page_title, "semantic_image_candidate", "效果展示", f"{ref}: {alt}")

    report = args.report if args.report.is_absolute() else root / args.report
    report.parent.mkdir(parents=True, exist_ok=True)
    fields = ["command_title", "relative_path", "category", "section", "issue", "notes"]
    with report.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"command_documents={len(documents)} guides={guide_count} "
        f"references={references} issues={len(rows)} report={report.relative_to(root)}"
    )
    if rows and not args.no_fail:
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["issue"]] = counts.get(row["issue"], 0) + 1
        raise ValueError("; ".join(f"{key}={value}" for key, value in sorted(counts.items())))


if __name__ == "__main__":
    main()
