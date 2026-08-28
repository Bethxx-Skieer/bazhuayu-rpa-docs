#!/usr/bin/env python3
"""Render contact sheets of images currently placed in parameter sections.

This is a visual QA aid: it deliberately uses the MDX section placement rather
than filename order, so result images accidentally placed under 常规/高级 are
visible during review.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from audit_and_crop_command_images import command_docs


COLS = 4
ROWS = 4
CELL_W = 480
CELL_H = 330
LABEL_H = 50
PAGE_SIZE = COLS * ROWS


def section_references(text: str, section: str) -> list[str]:
    patterns = {
        "instruction": r"(?ms)^##\s+指令说明\s*$\n(.*?)(?=^##\s+参数说明\s*$|^##\s+[^#]|\Z)",
        "parameter": r"(?ms)^##\s+参数说明\s*$\n(.*?)(?=^##\s+使用示例\s*$|^##\s+[^#]|\Z)",
        "usage": r"(?ms)^##\s+使用示例\s*$\n(.*?)(?=^###\s+效果展示\s*$|^##\s+[^#]|\Z)",
        "effect": r"(?ms)^###\s+效果展示\s*$\n(.*?)(?=^<Info>|^##\s+[^#]|\Z)",
    }
    match = re.search(patterns[section], text)
    if not match:
        return []
    return re.findall(r"!\[[^\]]*\]\((?:\./)?(images/[^)#]+)", match.group(1))


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = Path("C:/Windows/Fonts/msyh.ttc")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--documents-file", type=Path)
    parser.add_argument("--all-images", action="store_true")
    parser.add_argument("--section", choices=("instruction", "parameter", "usage", "effect"), default="parameter")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output or (root / "reports" / "parameter-image-contact-sheets")
    if not output.is_absolute():
        output = root / output
    output.mkdir(parents=True, exist_ok=True)
    for stale in output.glob("parameter-images-*.png"):
        stale.unlink()
    items: list[tuple[Path, Path]] = []
    if args.documents_file:
        list_path = args.documents_file if args.documents_file.is_absolute() else root / args.documents_file
        documents = [root / line.strip() for line in list_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        documents = command_docs(root)
    all_image_pattern = re.compile(r"!\[[^\]]*\]\((?:\./)?(images/[^)#]+)")
    for document in documents:
        text = document.read_text(encoding="utf-8")
        references = all_image_pattern.findall(text) if args.all_images else section_references(text, args.section)
        for reference in references:
            image = document.parent / reference
            if image.exists():
                items.append((document, image))

    label_font = font(18)
    meta_font = font(15)
    for page_index in range(0, len(items), PAGE_SIZE):
        canvas = Image.new("RGB", (COLS * CELL_W, ROWS * CELL_H), "white")
        draw = ImageDraw.Draw(canvas)
        for slot, (document, image_path) in enumerate(items[page_index:page_index + PAGE_SIZE]):
            row, col = divmod(slot, COLS)
            x, y = col * CELL_W, row * CELL_H
            with Image.open(image_path) as source:
                preview = source.convert("RGB")
                preview.thumbnail((CELL_W - 16, CELL_H - LABEL_H - 16))
                px = x + (CELL_W - preview.width) // 2
                py = y + LABEL_H + (CELL_H - LABEL_H - preview.height) // 2
                canvas.paste(preview, (px, py))
                size = f"{source.width}x{source.height}"
            relative = document.relative_to(root).as_posix()
            draw.text((x + 8, y + 4), relative, fill="black", font=label_font)
            draw.text((x + 8, y + 27), f"{image_path.name}  {size}", fill="#555555", font=meta_font)
            draw.rectangle((x, y, x + CELL_W - 1, y + CELL_H - 1), outline="#bbbbbb", width=1)
        number = page_index // PAGE_SIZE + 1
        canvas.save(output / f"parameter-images-{number:02d}.png")

    print(f"images={len(items)} sheets={(len(items) + PAGE_SIZE - 1) // PAGE_SIZE} output={output.relative_to(root)}")


if __name__ == "__main__":
    main()
