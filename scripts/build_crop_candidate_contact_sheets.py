#!/usr/bin/env python3
"""Build labelled contact sheets from a crop-audit CSV for visual review."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


COLUMNS = 4
ROWS = 4
CELL_WIDTH = 480
CELL_HEIGHT = 330
LABEL_HEIGHT = 48


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--status", default="corner_shadow_candidate")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    report = args.report if args.report.is_absolute() else root / args.report
    output = args.output if args.output.is_absolute() else root / args.output
    output.mkdir(parents=True, exist_ok=True)
    rows = [
        row for row in csv.DictReader(report.open(encoding="utf-8-sig"))
        if row.get("status") == args.status
    ]
    font = ImageFont.load_default()
    page_size = COLUMNS * ROWS
    for page_index in range(0, len(rows), page_size):
        sheet = Image.new("RGB", (COLUMNS * CELL_WIDTH, ROWS * CELL_HEIGHT), "white")
        draw = ImageDraw.Draw(sheet)
        for item_index, row in enumerate(rows[page_index:page_index + page_size]):
            col = item_index % COLUMNS
            line = item_index // COLUMNS
            x = col * CELL_WIDTH
            y = line * CELL_HEIGHT
            path = root / row["relative_path"]
            with Image.open(path) as source:
                preview = source.convert("RGB")
                preview.thumbnail((CELL_WIDTH - 12, CELL_HEIGHT - LABEL_HEIGHT - 12))
            px = x + (CELL_WIDTH - preview.width) // 2
            py = y + LABEL_HEIGHT + (CELL_HEIGHT - LABEL_HEIGHT - preview.height) // 2
            sheet.paste(preview, (px, py))
            draw.rectangle((x, y, x + CELL_WIDTH - 1, y + CELL_HEIGHT - 1), outline="#999999")
            label = f"{page_index + item_index + 1}. {row['relative_path']}"
            draw.text((x + 6, y + 6), label[:78], fill="black", font=font)
            draw.text((x + 6, y + 23), f"{row['original_width']}x{row['original_height']}", fill="#555555", font=font)
        page = page_index // page_size + 1
        sheet.save(output / f"crop-candidates-{page:02d}.png")
    print(f"candidates={len(rows)} sheets={(len(rows) + page_size - 1) // page_size} output={output}")


if __name__ == "__main__":
    main()
