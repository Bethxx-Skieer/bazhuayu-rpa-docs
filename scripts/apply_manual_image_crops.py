#!/usr/bin/env python3
"""Apply visually reviewed deep crops that the conservative frame detector skips."""

import csv
from pathlib import Path

from PIL import Image


# path: (expected original size, crop box)
CROPS = {
    "commands/desktop-automation/images/captureelementcommand-01.png": (
        (669, 529),
        (9, 9, 660, 520),
    ),
    "commands/desktop-automation/images/getwindowpropertycontentcommand-01.png": (
        (831, 697),
        (9, 9, 822, 688),
    ),
    "commands/desktop-automation/images/setwindowstatecommand-01.png": (
        (663, 369),
        (9, 9, 654, 360),
    ),
    "commands/desktop-automation/images/setwindowvisibilitycommand-01.png": (
        (660, 375),
        (9, 9, 651, 366),
    ),
    "commands/desktop-automation/images/win_setcheckboxcommand-01.png": (
        (830, 389),
        (9, 9, 821, 380),
    ),
    "commands/desktop-automation/images/resizewindowcommand-03.png": (
        (665, 433),
        (9, 9, 656, 424),
    ),
    "commands/desktop-automation/images/win_loopsimilarelementscommand_1-02.png": (
        (829, 447),
        (9, 9, 820, 438),
    ),
    "commands/flow/images/exit-flow-01.png": (
        (665, 258),
        (9, 9, 656, 249),
    ),
    "commands/flow/images/exit-sub-01.png": (
        (658, 256),
        (9, 9, 649, 247),
    ),
    "commands/web-automation/images/web-cookie-del-01.png": (
        (664, 375),
        (9, 9, 655, 366),
    ),
    "commands/web-automation/images/web-drag-01.png": (
        (995, 788),
        (9, 9, 986, 779),
    ),
    "commands/web-automation/images/web-monitor-stop-01.png": (
        (661, 254),
        (9, 9, 652, 245),
    ),
    "commands/web-automation/images/web-popup-handle-01.png": (
        (660, 382),
        (9, 9, 651, 373),
    ),
    "commands/web-automation/images/web-wait-content-01.png": (
        (832, 717),
        (9, 9, 823, 708),
    ),
    "commands/os/images/writefilecontentcommand-04.png": (
        (999, 755),
        (9, 9, 990, 746),
    ),
    "commands/ai/images/recognizegeneraltextcommand-02.png": (
        (704, 550),
        (26, 22, 673, 527),
    ),
    "commands/excel/images/getexcelsheetnamecommand-01.png": (
        (659, 419),
        (9, 9, 650, 410),
    ),
    "commands/ai/images/parsingunstructureddatacommand-02.png": (
        (661, 496),
        (9, 9, 652, 487),
    ),
    "commands/ai/images/recognizetrajectorycommand-03.png": (
        (658, 584),
        (9, 9, 649, 575),
    ),
    "commands/data-processing/images/changetextcasecommand-01.png": (
        (989, 623),
        (9, 9, 980, 614),
    ),
    "commands/datatable/images/adddatasheetcolumncommand-01.png": (
        (660, 315),
        (9, 9, 651, 306),
    ),
    "commands/datatable/images/importexceltodatasheetcommand-01.png": (
        (660, 530),
        (9, 9, 651, 521),
    ),
    "commands/dingtalk/images/insertdingtalkroworcolumncommand-03.png": (
        (654, 473),
        (9, 9, 645, 464),
    ),
    "commands/feishu/images/addlarkbitablefieldcommand-03.png": (
        (661, 632),
        (9, 9, 652, 623),
    ),
    "commands/feishu/images/getlarkbitablerecordcommand-03.png": (
        (659, 518),
        (9, 9, 650, 509),
    ),
    "commands/google/images/addrowtogooglespreadsheetcommand-01.png": (
        (661, 435),
        (9, 9, 652, 426),
    ),
    "commands/google/images/findgooglespreadsheetcellcommand-03.png": (
        (665, 539),
        (9, 9, 656, 530),
    ),
    "commands/google/images/readgooglespreadsheetcommand-04.png": (
        (661, 528),
        (9, 9, 652, 519),
    ),
    "commands/os/images/clearclipboarddatacommand-01.png": (
        (979, 349),
        (9, 9, 970, 340),
    ),
    "commands/os/images/copyfoldercommand-01.png": (
        (865, 690),
        (9, 9, 856, 681),
    ),
    "commands/os/images/executedoscommand-05.png": (
        (654, 354),
        (9, 9, 645, 345),
    ),
    "commands/os/images/getclipboardtextcommand-01.png": (
        (985, 448),
        (9, 9, 976, 439),
    ),
    "commands/os/images/renamefilecommand-03.png": (
        (662, 471),
        (9, 9, 653, 462),
    ),
    "commands/os/images/setclipboarddatacommand-03.png": (
        (981, 567),
        (9, 9, 972, 558),
    ),
    "commands/others/images/showaccountinputcommand-01.png": (
        (660, 367),
        (9, 9, 651, 358),
    ),
    "commands/others/images/showopenfoldercommand-05.png": (
        (659, 273),
        (9, 9, 650, 264),
    ),
    "commands/ai/images/recognizerotationcommand-08.png": (
        (656, 339),
        (3, 3, 653, 336),
    ),
    "commands/ai/images/translatecommand-04.png": (
        (668, 550),
        (9, 9, 659, 541),
    ),
    "commands/bazhuayu/images/7TUoxB-05.png": (
        (609, 575),
        (9, 9, 600, 566),
    ),
    "commands/bazhuayu/images/gettaskdataoffsetcommand-03.png": (
        (993, 630),
        (9, 9, 984, 621),
    ),
    "commands/datatable/images/importexceltodatasheetcommand-02.png": (
        (655, 534),
        (9, 9, 646, 525),
    ),
    "commands/feishu/images/vPhs0M-02.png": (
        (600, 421),
        (6, 0, 600, 421),
    ),
    "commands/google/images/xnN98S-22.png": (
        (978, 708),
        (0, 0, 978, 704),
    ),
    "commands/os/images/getfilepathinfocommand-02.png": (
        (697, 451),
        (3, 0, 697, 448),
    ),
    "commands/others/images/showaccountinputcommand-03.png": (
        (602, 242),
        (9, 9, 593, 233),
    ),
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    changed = 0
    for relative, (expected_size, box) in CROPS.items():
        path = root / relative
        target_size = (box[2] - box[0], box[3] - box[1])
        with Image.open(path) as source:
            if source.size == target_size:
                continue
            if source.size != expected_size:
                raise ValueError(f"unexpected dimensions for {path}: {source.size}")
            source.load()
            cropped = source.crop(box)
            image_format = source.format
        cropped.save(path, format=image_format)
        changed += 1

    report = root / "reports" / "image-crop-audit.csv"
    rows = list(csv.DictReader(report.open(encoding="utf-8-sig")))
    fields = list(rows[0])
    for row in rows:
        relative = row["relative_path"]
        if relative not in CROPS:
            continue
        expected_size, box = CROPS[relative]
        row.update({
            "original_width": str(expected_size[0]),
            "original_height": str(expected_size[1]),
            "crop_top": str(box[1]),
            "crop_bottom": str(expected_size[1] - box[3]),
            "crop_left": str(box[0]),
            "crop_right": str(expected_size[0] - box[2]),
            "status": "manual_deep_crop",
        })
    with report.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"manual_crops={changed}")


if __name__ == "__main__":
    main()
