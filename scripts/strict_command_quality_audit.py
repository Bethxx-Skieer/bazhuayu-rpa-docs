#!/usr/bin/env python3
"""Generate high-signal review candidates beyond the hard command-page contract.

This audit intentionally separates definite defects from heuristic candidates.
It never rewrites documentation or images; every semantic candidate must be
visually reviewed before a page is changed.
"""

from __future__ import annotations

import csv
import math
import re
from collections import Counter
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

from audit_and_crop_command_images import command_docs
from validate_command_images import HEADINGS, IMAGE_RE, section, title, visible_content


TABLE_ROW_RE = re.compile(r"(?m)^\s*\|(.+?)\|(.+?)\|\s*$")
NUMBERED_IMAGE_RE = re.compile(r"-(\d+)\.(?:png|jpe?g|webp)$", re.I)
PLACEHOLDERS = {"", "-", "—", "待补充", "后续补充", "todo", "tbd"}
SCOPE_CATEGORIES = {
    "mouse-keyboard",
    "datatable",
    "excel",
    "os",
    "bazhuayu",
    "email",
    "data-processing",
    "group-notification",
    "feishu",
    "dingtalk",
    "google",
    "ai",
    "database",
    "others",
}


def image_number(ref: str) -> int | None:
    match = NUMBERED_IMAGE_RE.search(ref)
    return int(match.group(1)) if match else None


def panel_metrics(path: Path) -> tuple[float, float, float, int, int]:
    """Return entropy, edge density, non-white ratio and dimensions."""
    with Image.open(path) as source:
        width, height = source.size
        image = source.convert("L")
        image.thumbnail((220, 220))
        histogram = image.histogram()
        total = sum(histogram) or 1
        entropy = -sum((count / total) * math.log2(count / total) for count in histogram if count)
        edges = image.filter(ImageFilter.FIND_EDGES)
        edge_density = ImageStat.Stat(edges).mean[0] / 255
        non_white = sum(histogram[:246]) / total
        return entropy, edge_density, non_white, width, height


def table_rows(parameter: str) -> list[tuple[str, str]]:
    rows = []
    for left, right in TABLE_ROW_RE.findall(parameter):
        name = re.sub(r"[*`\s]", "", left).strip().lower()
        description = re.sub(r"<[^>]+>|[*`]", "", right).strip()
        if name in {"参数", "---", ":---", "---:"} or set(name) <= {"-", ":"}:
            continue
        rows.append((name, description))
    return rows


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    rows: list[dict[str, str]] = []

    def add(document: Path, page_title: str, kind: str, section_name: str, severity: str, notes: str) -> None:
        rows.append({
            "command_title": page_title,
            "relative_path": document.relative_to(root).as_posix(),
            "category": document.relative_to(root / "commands").parts[0],
            "section": section_name,
            "severity": severity,
            "issue": kind,
            "notes": notes,
        })

    documents = [
        document for document in command_docs(root)
        if document.relative_to(root / "commands").parts[0] in SCOPE_CATEGORIES
    ]

    for document in documents:
        text = document.read_text(encoding="utf-8")
        page_title = title(text, document.stem)
        instruction = section(text, HEADINGS[0], HEADINGS[1])
        parameter = section(text, HEADINGS[1], HEADINGS[2])
        usage = section(text, HEADINGS[2], HEADINGS[3])
        effect = section(text, HEADINGS[3], None)

        description = re.search(r"(?m)^\*\*描述：\*\*\s*(.+?)\s*$", instruction)
        if description:
            value = visible_content(description.group(1))
            if len(value) < 8 or value.lower() in PLACEHOLDERS:
                add(document, page_title, "weak_description", "指令说明", "defect", value)

        parameter_images = IMAGE_RE.findall(parameter)
        usage_images = IMAGE_RE.findall(usage)
        effect_images = IMAGE_RE.findall(effect)

        table_header = re.search(r"(?m)^\s*\|\s*参数\s*\|\s*说明\s*\|", parameter)
        first_parameter_image = IMAGE_RE.search(parameter)
        if table_header and first_parameter_image and first_parameter_image.start() > table_header.start():
            add(document, page_title, "parameter_image_after_table", "参数说明", "defect", "客户端图示应位于文字参数表之前。")

        for name, description_text in table_rows(parameter):
            normalized = re.sub(r"\s+", "", description_text).lower()
            if normalized in PLACEHOLDERS or len(normalized) < 4:
                add(document, page_title, "weak_parameter_description", "参数说明", "defect", f"{name}: {description_text}")

        logic = re.search(r"(?ms)\*\*该流程执行逻辑：\*\*\s*(.*?)(?=^<Info>|\Z)", usage)
        if logic:
            logic_text = visible_content(logic.group(1))
            if len(logic_text) < 15:
                add(document, page_title, "weak_execution_logic", "使用示例", "review", logic_text)

        for alt, ref in effect_images:
            if re.search(r"流程(?:搭建|示例|截图|图)?|主流程|工作流", alt, re.I):
                add(document, page_title, "flow_image_in_effect", "效果展示", "defect", f"{ref}: {alt}")

        # Filename order is not authoritative, but inversions often expose a
        # pair that was moved to the wrong section during bulk normalization.
        parameter_numbers = [number for _, ref in parameter_images if (number := image_number(ref)) is not None]
        usage_numbers = [number for _, ref in usage_images if (number := image_number(ref)) is not None]
        if parameter_numbers and usage_numbers and min(parameter_numbers) > min(usage_numbers):
            add(
                document, page_title, "image_number_order_inversion", "参数说明/使用示例", "review",
                f"parameter={parameter_numbers}; usage={usage_numbers}",
            )

        # Compare the first similarly sized panel in each section. A much denser
        # parameter panel than the usage panel is a useful, conservative signal
        # for the common default/filled screenshot reversal.
        if parameter_images and usage_images:
            parameter_ref = parameter_images[0][1]
            usage_ref = usage_images[0][1]
            parameter_path = document.parent / parameter_ref
            usage_path = document.parent / usage_ref
            if parameter_path.exists() and usage_path.exists():
                try:
                    pm = panel_metrics(parameter_path)
                    um = panel_metrics(usage_path)
                    size_ratio = (pm[3] * pm[4]) / max(1, um[3] * um[4])
                    if 0.55 <= size_ratio <= 1.8 and pm[1] > um[1] * 1.28 and pm[2] > um[2] * 1.18:
                        add(
                            document, page_title, "possible_default_example_reversal", "参数说明/使用示例", "review",
                            f"parameter={parameter_ref} edge={pm[1]:.3f} content={pm[2]:.3f}; "
                            f"usage={usage_ref} edge={um[1]:.3f} content={um[2]:.3f}",
                        )
                except Exception as error:
                    add(document, page_title, "image_metric_error", "images", "defect", str(error))

    report = root / "reports" / "strict-command-quality-audit.csv"
    report.parent.mkdir(parents=True, exist_ok=True)
    fields = ["command_title", "relative_path", "category", "section", "severity", "issue", "notes"]
    with report.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter((row["severity"], row["issue"]) for row in rows)
    summary = ", ".join(f"{severity}:{kind}={count}" for (severity, kind), count in sorted(counts.items()))
    print(f"documents={len(documents)} candidates={len(rows)} report={report.relative_to(root)}")
    print(summary or "no candidates")


if __name__ == "__main__":
    main()
