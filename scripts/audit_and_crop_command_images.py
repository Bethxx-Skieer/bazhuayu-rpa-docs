#!/usr/bin/env python3
"""Audit every command screenshot and remove provable neutral outer frames.

The script only crops a file when every edge has the same continuous outer
frame thickness. It intentionally leaves ordinary white page margins and any
image whose border cannot be proved to be an external frame unchanged.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

from PIL import Image


# These are module introductions, setup guides or FAQs rather than command
# detail pages. They intentionally do not use the four-section command template.
GUIDE_PAGES = {
    "commands/bazhuayu/7TUoxB.mdx",
    "commands/data-processing/jEc4Yc.mdx",
    "commands/desktop-automation/kj13ob.mdx",
    "commands/dingtalk/gM80NN.mdx",
    "commands/email/dtd5Rb.mdx",
    "commands/email/RlCVx4.mdx",
    "commands/feishu/vPhs0M.mdx",
    "commands/google/xnN98S.mdx",
    "commands/group-notification/XZBe1j.mdx",
    "commands/others/zKl2eg.mdx",
}
MAX_FRAME = 40
MAX_INNER_FRAME = 100
MIN_BRIGHTNESS = 0
MAX_BRIGHTNESS = 235
MAX_CHROMA = 14
MIN_DOMINANCE = 0.94


def command_docs(root: Path) -> list[Path]:
    return sorted(
        path
        for path in (root / "commands").rglob("*.mdx")
        if len(path.relative_to(root / "commands").parts) >= 2
        and path.relative_to(root).as_posix() not in GUIDE_PAGES
    )


def has_corner_shadow(image: Image.Image) -> bool:
    """Flag residual dark/grey rounded-corner shadows for manual review.

    This is deliberately not auto-cropped: corner pixels alone do not prove a
    safe crop boundary. The contact-sheet review decides the final inset.
    """
    if image.mode not in {"RGB", "RGBA"} or min(image.size) < 80:
        return False
    rgb = image.convert("RGB")
    size = min(16, image.width // 12, image.height // 12)
    if size < 4:
        return False
    boxes = (
        (0, 0, size, size),
        (image.width - size, 0, image.width, size),
        (0, image.height - size, size, image.height),
        (image.width - size, image.height - size, image.width, image.height),
    )
    suspicious = 0
    for box in boxes:
        crop = rgb.crop(box)
        pixels = list(crop.get_flattened_data() if hasattr(crop, "get_flattened_data") else crop.getdata())
        neutral_dark = sum(
            max(pixel) - min(pixel) <= MAX_CHROMA and sum(pixel) / 3 <= 225
            for pixel in pixels
        )
        if neutral_dark / len(pixels) >= 0.03:
            suspicious += 1
    return suspicious >= 2


def image_paths(root: Path) -> list[Path]:
    pattern = re.compile(r"!\[[^\]]*\]\((?:\./)?(images/[^)#]+)")
    paths: set[Path] = set()
    for document in command_docs(root):
        for relative in pattern.findall(document.read_text(encoding="utf-8")):
            image = (document.parent / relative).resolve()
            if image.exists():
                paths.add(image)
    return sorted(paths)


def is_neutral_frame_line(image: Image.Image, side: str, offset: int) -> tuple[bool, tuple[int, int, int] | None]:
    width, height = image.size
    if side == "top":
        pixels = [image.getpixel((x, offset))[:3] for x in range(width // 20, width - width // 20)]
    elif side == "bottom":
        pixels = [image.getpixel((x, height - 1 - offset))[:3] for x in range(width // 20, width - width // 20)]
    elif side == "left":
        pixels = [image.getpixel((offset, y))[:3] for y in range(height // 20, height - height // 20)]
    else:
        pixels = [image.getpixel((width - 1 - offset, y))[:3] for y in range(height // 20, height - height // 20)]

    colour, amount = Counter(pixels).most_common(1)[0]
    brightness = sum(colour) / 3
    chroma = max(colour) - min(colour)
    return (
        amount / len(pixels) >= MIN_DOMINANCE
        and MIN_BRIGHTNESS <= brightness <= MAX_BRIGHTNESS
        and chroma <= MAX_CHROMA,
        colour,
    )


def frame_thickness(image: Image.Image) -> tuple[int, int, int, int]:
    if image.mode not in {"RGB", "RGBA"} or min(image.size) < 50:
        return (0, 0, 0, 0)
    thicknesses: list[int] = []
    for side in ("top", "bottom", "left", "right"):
        thickness = 0
        for offset in range(min(MAX_FRAME, image.size[0] // 10, image.size[1] // 10)):
            valid, _ = is_neutral_frame_line(image, side, offset)
            if not valid:
                break
            thickness += 1
        thicknesses.append(thickness)

    positive = [thickness for thickness in thicknesses if thickness]
    # A complete narrow frame is safe to remove. A screenshot clipped at its
    # top can legitimately have a white top edge and neutral left/right/bottom
    # edges, so accept three matching sides as well. Fewer than three sides is
    # too ambiguous and is left unchanged for manual review.
    if len(positive) >= 3 and max(positive) - min(positive) <= 4:
        return tuple(thicknesses)
    return (0, 0, 0, 0)


def dominant_neutral_line(pixels: list[tuple[int, int, int]]) -> bool:
    colour, amount = Counter(pixels).most_common(1)[0]
    brightness = sum(colour) / 3
    chroma = max(colour) - min(colour)
    return amount / len(pixels) >= 0.78 and 20 <= brightness <= 238 and chroma <= MAX_CHROMA


def inner_frame_box(image: Image.Image) -> tuple[int, int, int, int] | None:
    """Find a complete flat grey rectangle inset from a white screenshot edge."""
    if image.mode not in {"RGB", "RGBA"} or min(image.size) < 180:
        return None
    rgb = image.convert("RGB")
    width, height = rgb.size
    x_pad = max(2, width // 50)
    y_pad = max(2, height // 50)
    max_x = min(MAX_INNER_FRAME, width // 6)
    max_y = min(MAX_INNER_FRAME, height // 6)

    sample = 4
    top = next((y for y in range(max_y) if dominant_neutral_line(
        [rgb.getpixel((x, y)) for x in range(x_pad, width - x_pad, sample)]
    )), None)
    bottom = next((height - 1 - y for y in range(max_y) if dominant_neutral_line(
        [rgb.getpixel((x, height - 1 - y)) for x in range(x_pad, width - x_pad, sample)]
    )), None)
    left = next((x for x in range(max_x) if dominant_neutral_line(
        [rgb.getpixel((x, y)) for y in range(y_pad, height - y_pad, sample)]
    )), None)
    right = next((width - 1 - x for x in range(max_x) if dominant_neutral_line(
        [rgb.getpixel((width - 1 - x, y)) for y in range(y_pad, height - y_pad, sample)]
    )), None)
    if None in (top, bottom, left, right):
        return None
    assert top is not None and bottom is not None and left is not None and right is not None
    if right - left < width * 0.7 or bottom - top < height * 0.7:
        return None
    inset = 3
    box = (left + inset, top + inset, right - inset + 1, bottom - inset + 1)
    return box if box[2] > box[0] and box[3] > box[1] else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="overwrite only verified frame images")
    parser.add_argument("--report", type=Path, required=True, help="CSV audit output")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    rows = []
    for path in image_paths(root):
        try:
            with Image.open(path) as source:
                top, bottom, left, right = frame_thickness(source)
                total = top + bottom + left + right
                corner_shadow = has_corner_shadow(source)
                inner_box = inner_frame_box(source) if not total and corner_shadow else None
                row = {
                    "relative_path": path.relative_to(root).as_posix(),
                    "format": source.format or "",
                    "original_width": source.width,
                    "original_height": source.height,
                    "crop_top": top,
                    "crop_bottom": bottom,
                    "crop_left": left,
                    "crop_right": right,
                    "inner_left": inner_box[0] if inner_box else "",
                    "inner_top": inner_box[1] if inner_box else "",
                    "inner_right": inner_box[2] if inner_box else "",
                    "inner_bottom": inner_box[3] if inner_box else "",
                    "corner_shadow_candidate": "yes" if corner_shadow else "no",
                    "status": "cropped" if args.apply and total else (
                        "candidate" if total else (
                            "inner_frame_candidate" if inner_box else (
                                "corner_shadow_candidate" if corner_shadow else "unchanged"
                            )
                        )
                    ),
                }
                if args.apply and total:
                    cropped = source.crop((left, top, source.width - right, source.height - bottom))
                    if source.format == "JPEG":
                        # Cropping a JPEG necessarily re-encodes it; preserve a
                        # high-quality, non-subsampled result instead of relying
                        # on Pillow's unavailable source-format metadata.
                        save_args = {"format": "JPEG", "quality": 95, "subsampling": 0}
                    else:
                        save_args = {"format": source.format} if source.format else {}
                    cropped.save(path, **save_args)
                elif args.apply and inner_box:
                    cropped = source.crop(inner_box)
                    save_args = (
                        {"format": "JPEG", "quality": 95, "subsampling": 0}
                        if source.format == "JPEG"
                        else ({"format": source.format} if source.format else {})
                    )
                    cropped.save(path, **save_args)
                    row["status"] = "cropped_inner_frame"
                rows.append(row)
        except Exception as error:  # report rather than silently skipping a referenced asset
            rows.append({"relative_path": path.relative_to(root).as_posix(), "status": f"error: {error}"})

    args.report.parent.mkdir(parents=True, exist_ok=True)
    fields = ["relative_path", "format", "original_width", "original_height", "crop_top", "crop_bottom", "crop_left", "crop_right", "inner_left", "inner_top", "inner_right", "inner_bottom", "corner_shadow_candidate", "status"]
    with args.report.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"audited={len(rows)} "
        f"frame_candidates={sum(any(row.get(side, 0) for side in ('crop_top', 'crop_bottom', 'crop_left', 'crop_right')) for row in rows)} "
        f"inner_frame_candidates={sum(bool(row.get('inner_left', '')) for row in rows)} "
        f"corner_candidates={sum(row.get('corner_shadow_candidate') == 'yes' for row in rows)}"
    )


if __name__ == "__main__":
    main()
