#!/usr/bin/env python3
"""Apply a final safe inset to images already proven to have external frames.

Rounded modal screenshots can retain a one-to-several-pixel shadow in the
corners after their coloured frame is removed. This intentionally runs only on
the paths recorded as cropped in the audit report.
"""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image


INSET = 6


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    report = root / "reports" / "image-crop-audit.csv"
    rows = list(csv.DictReader(report.open(encoding="utf-8-sig")))
    changed = 0
    for row in rows:
        if not row["status"].startswith("cropped"):
            continue
        path = root / row["relative_path"]
        with Image.open(path) as source:
            expected_width = int(row["original_width"]) - int(row["crop_left"]) - int(row["crop_right"])
            expected_height = int(row["original_height"]) - int(row["crop_top"]) - int(row["crop_bottom"])
            # The prior interrupted run may already have trimmed this file. Do
            # not crop it again; mark it complete below.
            if (source.width, source.height) == (expected_width - INSET * 2, expected_height - INSET * 2):
                trimmed = None
            elif (source.width, source.height) == (expected_width, expected_height):
                if source.width <= INSET * 2 or source.height <= INSET * 2:
                    continue
                source.load()
                trimmed = source.crop((INSET, INSET, source.width - INSET, source.height - INSET))
            else:
                raise ValueError(f"unexpected dimensions for {path}: {(source.width, source.height)}")
            image_format = source.format
        if trimmed is not None:
            save_args = (
                {"format": "JPEG", "quality": 95, "subsampling": 0}
                if image_format == "JPEG"
                else ({"format": image_format} if image_format else {})
            )
            trimmed.save(path, **save_args)
        if trimmed is not None:
            changed += 1
        row["shadow_trim_pixels"] = str(INSET)
        row["status"] = "cropped_shadow_trim"

    fields = list(rows[0])
    if "shadow_trim_pixels" not in fields:
        fields.append("shadow_trim_pixels")
    with report.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"shadow_trimmed={changed} inset={INSET}px")


if __name__ == "__main__":
    main()
