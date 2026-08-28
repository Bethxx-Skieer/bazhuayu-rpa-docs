#!/usr/bin/env python3
"""Normalize misplaced command screenshots into parameter/example/effect sections."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from PIL import Image


# Values are image sequence numbers after visual review of each page.
# `regular` and `advanced` are inserted into their matching parameter tabs.
# Configured panels and flow canvases belong to `usage`; application results,
# before/after states and run logs belong to `effect`.
LAYOUTS = {
    "commands/ai/interactivechatcommand.mdx": dict(regular=[2], usage=[4, 3, 7, 5, 8], effect=[1, 6, 9]),
    "commands/ai/parsingunstructureddatacommand.mdx": dict(regular=[2], usage=[4, 1], effect=[3, 5]),
    "commands/ai/recognizecardcommand.mdx": dict(regular=[1], usage=[2, 4], effect=[3, 5]),
    "commands/ai/recognizeinvoicecommand.mdx": dict(regular=[1], advanced=[2], usage=[3, 4, 5], effect=[6]),
    "commands/ai/recognizecharactercommand.mdx": dict(regular=[2], usage=[1, 4], effect=[3, 5]),
    "commands/ai/recognizegeneraltextcommand.mdx": dict(regular=[2], advanced=[6], usage=[3, 5], effect=[1, 4]),
    "commands/ai/recognizerecaptchav2command.mdx": dict(regular=[1], usage=[4, 5, 3], effect=[2, 6]),
    "commands/ai/recognizerotationcommand.mdx": dict(regular=[10], usage=[6, 5, 4, 8], effect=[1, 2, 3, 7, 9]),
    "commands/ai/recognizeslidercommand.mdx": dict(regular=[1], usage=[4], effect=[2, 3, 5, 6]),
    "commands/ai/recognizesliderpuzzlecommand.mdx": dict(regular=[2], advanced=[7], usage=[5], effect=[1, 3, 4, 8, 6]),
    "commands/ai/recognizetablecommand.mdx": dict(regular=[1], advanced=[6], usage=[3, 5], effect=[2, 4]),
    "commands/ai/recognizetrajectorycommand.mdx": dict(regular=[3], usage=[4, 2], effect=[1]),
    "commands/ai/translatecommand.mdx": dict(regular=[2], usage=[4, 1], effect=[3]),
    "commands/bazhuayu/getaccesstokencommand.mdx": dict(regular=[3], usage=[1], effect=[2]),
    "commands/bazhuayu/gettaskdatacommand.mdx": dict(regular=[2], usage=[4, 3], effect=[1]),
    "commands/bazhuayu/gettaskdatacountcommand.mdx": dict(regular=[3], usage=[1], effect=[2]),
    "commands/bazhuayu/stoptaskcommand.mdx": dict(regular=[3], usage=[2], effect=[1, 4]),
    "commands/bazhuayu/starttaskcommand.mdx": dict(regular=[4], usage=[3], effect=[1, 2]),
    "commands/data-processing/appendprefixorsuffixcommand.mdx": dict(regular=[3], usage=[2], effect=[1]),
    "commands/data-processing/clearlistcommand.mdx": dict(regular=[2], usage=[3], effect=[1, 4, 5]),
    "commands/data-processing/createlistcommand.mdx": dict(regular=[4], usage=[1], effect=[2, 3]),
    "commands/data-processing/datetimeconverttotimestampcommand.mdx": dict(regular=[2], usage=[1], effect=[3]),
    "commands/data-processing/distinctlistcommand.mdx": dict(regular=[1], usage=[2, 4], effect=[3, 5]),
    "commands/data-processing/getdictionarykeyscommand.mdx": dict(regular=[2], usage=[3], effect=[1, 4]),
    "commands/data-processing/getdictionaryvaluescommand.mdx": dict(regular=[2], usage=[3], effect=[1, 4]),
    "commands/data-processing/intersectlistcommand.mdx": dict(regular=[5], usage=[1], effect=[2, 3, 4]),
    "commands/data-processing/jEc4Yc.mdx": dict(regular=[], usage=[1, 2, 4], effect=[3, 5, 6, 7, 8]),
    "commands/data-processing/regexmatchcommand.mdx": dict(regular=[1, 2], usage=[3, 5], effect=[4, 6]),
    "commands/data-processing/reverselistcommand.mdx": dict(regular=[2], usage=[3], effect=[1, 4, 5]),
    "commands/data-processing/setdictionarykeyvaluecommand.mdx": dict(regular=[5], usage=[1, 6], effect=[2, 3, 4]),
    "commands/data-processing/setvariablecommand.mdx": dict(regular=[1, 2], usage=[3, 8], effect=[4, 5, 6, 7, 9]),
    "commands/data-processing/timestampconverttodatetimecommand.mdx": dict(regular=[2], usage=[1], effect=[3]),
    "commands/data-processing/trimtextcommand.mdx": dict(regular=[2], usage=[3], effect=[1]),
    "commands/data-processing/updatelistitemcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4, 5]),
    "commands/data-processing/urldecodecommand.mdx": dict(regular=[1], usage=[2, 3], effect=[]),
    "commands/datatable/readdatasheetcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[]),
    "commands/database/closedatabasecommand.mdx": dict(regular=[2], usage=[1], effect=[3]),
    "commands/database/batchinserttodatabasecommand.mdx": dict(regular=[9], usage=[5, 4, 2, 3], effect=[6, 7, 8, 1]),
    "commands/database/executesqlcommand.mdx": dict(regular=[5], usage=[4], effect=[2, 3, 1]),
    "commands/dingtalk/getalldingtalksheetnamescommand.mdx": dict(regular=[4], usage=[1], effect=[2, 3]),
    "commands/dingtalk/getdingtalksheetrowcountcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[]),
    "commands/dingtalk/insertdingtalkroworcolumncommand.mdx": dict(regular=[3], usage=[2], effect=[1]),
    "commands/dingtalk/readdingtalksheetcommand.mdx": dict(regular=[4], usage=[1], effect=[3, 2]),
    "commands/dingtalk/writetodingtalksheetcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4, 5]),
    "commands/email/addflagtoemailcommand.mdx": dict(regular=[3], usage=[4, 5], effect=[1, 2]),
    "commands/email/downloademailattachmentcommand.mdx": dict(regular=[3], usage=[2], effect=[4, 1]),
    "commands/email/getemailscommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4]),
    "commands/email/moveemailcommand.mdx": dict(regular=[2], usage=[3], effect=[1, 4]),
    "commands/email/sendemailcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4, 5, 6, 7, 8, 9]),
    "commands/excel/activateexcelsheetcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4, 5]),
    "commands/excel/deleteexcelduplicaterowcommand.mdx": dict(regular=[1], usage=[2, 4, 3], effect=[5, 6]),
    "commands/excel/findexcelcellcommand.mdx": dict(regular=[1], usage=[5, 4], effect=[2, 3, 6, 7, 8]),
    "commands/excel/filterexcelcolumncommand.mdx": dict(regular=[1], usage=[2, 4], effect=[3, 5, 6, 7, 8, 9]),
    "commands/excel/getexcelcolumncountcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4]),
    "commands/excel/getexcelformulacommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4]),
    "commands/excel/getexcelregionscreenshotcommand.mdx": dict(regular=[1], usage=[3, 2], effect=[4, 5, 6]),
    "commands/excel/getexcelrowcountcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4]),
    "commands/excel/getlastemptycellofcolumncommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4]),
    "commands/excel/runexcelmacrocommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4, 5]),
    "commands/feishu/deleterowfromlarkspreadsheetcommand.mdx": dict(regular=[5], usage=[2], effect=[1, 3, 4]),
    "commands/feishu/addcolumntolarkspreadsheetcommand.mdx": dict(regular=[5], usage=[3], effect=[1, 2, 4]),
    "commands/feishu/addlarkbitabledatatablecommand.mdx": dict(regular=[4], usage=[1], effect=[2, 3]),
    "commands/feishu/addlarkbitablefieldcommand.mdx": dict(regular=[3], usage=[1], effect=[2, 4]),
    "commands/feishu/addlarkbitablerecordcommand.mdx": dict(regular=[4], usage=[1], effect=[2, 3]),
    "commands/feishu/addrowtolarkspreadsheetcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4]),
    "commands/feishu/deletecolumnfromlarkspreadsheetcommand.mdx": dict(regular=[1], usage=[2, 4], effect=[3, 5]),
    "commands/feishu/deletelarkbitablefieldcommand.mdx": dict(regular=[3], usage=[1], effect=[2, 4, 5]),
    "commands/feishu/deletelarkbitablerecordcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4]),
    "commands/feishu/deletelarkbitableviewcommand.mdx": dict(regular=[3], usage=[1], effect=[2]),
    "commands/feishu/findlarkspreadsheetcellcommand.mdx": dict(regular=[3], usage=[2], effect=[4, 1]),
    "commands/feishu/getlarkaccesstokencommand.mdx": dict(regular=[3], usage=[2], effect=[1]),
    "commands/feishu/getlarkbitablerecordcommand.mdx": dict(regular=[3], usage=[1], effect=[2]),
    "commands/feishu/getlarkbitablefieldcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4, 5]),
    "commands/feishu/getlarkbitableviewcommand.mdx": dict(regular=[4], usage=[1], effect=[2, 3]),
    "commands/feishu/renamelarkbitabledatatablecommand.mdx": dict(regular=[3], usage=[1], effect=[2]),
    "commands/feishu/updatelarkbitableviewcommand.mdx": dict(regular=[2], usage=[3], effect=[1]),
    "commands/feishu/writecolumntolarkspreadsheetcommand.mdx": dict(regular=[4], usage=[3], effect=[1, 5, 2]),
    "commands/feishu/writerowtolarkspreadsheetcommand.mdx": dict(regular=[2], usage=[1], effect=[4, 5, 3]),
    "commands/google/deletecolumnfromgooglespreadsheetcommand.mdx": dict(regular=[2], usage=[1], effect=[3]),
    "commands/google/addcolumntogooglespreadsheetcommand.mdx": dict(regular=[1], usage=[2, 4], effect=[3]),
    "commands/google/findgooglespreadsheetcellcommand.mdx": dict(regular=[3], usage=[1], effect=[2, 4, 5]),
    "commands/google/getgooglecredentialcommand.mdx": dict(regular=[1], usage=[2], effect=[3]),
    "commands/google/getgooglespreadsheetcommand.mdx": dict(regular=[3], usage=[1], effect=[2, 4]),
    "commands/google/readgooglespreadsheetcommand.mdx": dict(regular=[4], usage=[2], effect=[1, 3]),
    "commands/google/writecolumntogooglespreadsheetcommand.mdx": dict(regular=[2], usage=[1], effect=[3, 4]),
    "commands/google/writerowtogooglespreadsheetcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4]),
    "commands/group-notification/notifydingtalkgroupcommand.mdx": dict(regular=[3], usage=[2], effect=[1]),
    "commands/mouse-keyboard/clickimagecommand.mdx": dict(regular=[1], advanced=[2], usage=[3, 4, 5], effect=[6]),
    "commands/mouse-keyboard/keyboardinputcommand.mdx": dict(regular=[1], usage=[2, 4], effect=[3]),
    "commands/mouse-keyboard/hoverimagecommand.mdx": dict(regular=[1], advanced=[2], usage=[7], effect=[3, 4, 5, 6, 8]),
    "commands/mouse-keyboard/mousescrollcommand.mdx": dict(regular=[1], advanced=[2], usage=[3], effect=[]),
    "commands/os/copyfilecommand.mdx": dict(regular=[3], usage=[4, 1], effect=[2]),
    "commands/os/checkprocessexistcommand.mdx": dict(regular=[4], usage=[1], effect=[2, 3]),
    "commands/os/compressfilecommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4, 5]),
    "commands/os/createfoldercommand.mdx": dict(regular=[4], usage=[1], effect=[3, 5, 2]),
    "commands/os/deletefilecommand.mdx": dict(regular=[2], usage=[4, 3], effect=[1]),
    "commands/os/executedoscommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4, 5]),
    "commands/os/decompressfilecommand.mdx": dict(regular=[3], usage=[1], effect=[2, 5, 4]),
    "commands/os/getcurrentdatetimecommand.mdx": dict(regular=[2], usage=[1], effect=[3]),
    "commands/os/getfilecontentcommand.mdx": dict(regular=[4], usage=[2], effect=[3, 1]),
    "commands/os/getfilepathinfocommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4]),
    "commands/os/killprocesscommand.mdx": dict(regular=[4], usage=[3], effect=[2, 1]),
    "commands/os/movefilecommand.mdx": dict(regular=[3], usage=[2, 4], effect=[1]),
    "commands/os/renamefilecommand.mdx": dict(regular=[3], usage=[1], effect=[2]),
    "commands/os/renamefoldercommand.mdx": dict(regular=[3], usage=[1], effect=[2]),
    "commands/os/setclipboarddatacommand.mdx": dict(regular=[3], usage=[1], effect=[2]),
    "commands/os/writefilecontentcommand.mdx": dict(regular=[3], usage=[4, 1], effect=[2]),
    "commands/others/catchcommand.mdx": dict(regular=[2], usage=[3], effect=[1]),
    "commands/others/addlogmessagecommand.mdx": dict(regular=[4], usage=[1, 3], effect=[2]),
    "commands/others/commentcommand.mdx": dict(regular=[3], usage=[2, 1], effect=[4]),
    "commands/others/endtrycommand.mdx": dict(regular=[3], usage=[2], effect=[1]),
    "commands/others/raisecommand.mdx": dict(regular=[2], usage=[1, 3], effect=[4]),
    "commands/others/showmessageboxcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4]),
    "commands/others/showmessagetipscommand.mdx": dict(regular=[3], advanced=[5], usage=[1], effect=[2, 4]),
    "commands/others/showopenfilecommand.mdx": dict(regular=[1], usage=[2, 4], effect=[3, 5, 6]),
    "commands/others/showtextinputcommand.mdx": dict(regular=[1], usage=[2, 3], effect=[4, 5]),
    "commands/others/trycommand.mdx": dict(regular=[1], usage=[2, 4], effect=[3]),
    "commands/others/zKl2eg.mdx": dict(regular=[], usage=[1, 2], effect=[3, 4, 5, 6]),
}


# Semantic corrections found by reviewing every image in the command-detail
# scope. A selected 高级 tab belongs to the matching parameter tab. Configured
# command panels are examples, not execution results, and belong under 使用示例.
ADVANCED_RELOCATIONS = {
    "commands/excel/runexcelmacrocommand.mdx": ["runexcelmacrocommand-02.png"],
    "commands/excel/addimagetoexcelcommand.mdx": ["addimagetoexcelcommand-04.png"],
    "commands/os/executedoscommand.mdx": ["executedoscommand-05.png"],
    "commands/others/showopenfilecommand.mdx": ["showopenfilecommand-02.png"],
    "commands/others/showopenfoldercommand.mdx": ["showopenfoldercommand-05.png"],
}

USAGE_RELOCATIONS = {
    "commands/ai/getemotionaltendencycommand.mdx": ["getemotionaltendencycommand-03.png"],
    "commands/ai/recognizecaptchabyprovidercommand.mdx": ["recognizecaptchabyprovidercommand-13.png"],
    "commands/bazhuayu/gettaskdataoffsetcommand.mdx": ["gettaskdataoffsetcommand-03.png"],
    "commands/bazhuayu/updateactionpropertiescommand.mdx": ["updateactionpropertiescommand-05.png"],
    "commands/data-processing/convertdatetimetextcommand.mdx": ["convertdatetimetextcommand-03.png"],
    "commands/data-processing/getsubtextcommand.mdx": ["getsubtextcommand-03.png"],
    "commands/data-processing/insertitemtolistcommand.mdx": ["insertitemtolistcommand-03.png"],
    "commands/data-processing/jEc4Yc.mdx": ["jEc4Yc-03.png"],
    "commands/data-processing/jointextcommand.mdx": ["jointextcommand-03.png", "jointextcommand-04.png"],
    "commands/data-processing/parsejsoncommand.mdx": ["parsejsoncommand-03.png"],
    "commands/data-processing/randomnumbercommand.mdx": ["randomnumbercommand-03.png"],
    "commands/data-processing/removelistitemcommand.mdx": ["removelistitemcommand-03.png"],
    "commands/data-processing/replacetextcommand.mdx": ["replacetextcommand-03.png"],
    "commands/data-processing/setvariablecommand.mdx": ["setvariablecommand-07.png"],
    "commands/data-processing/splittextcommand.mdx": ["splittextcommand-03.png"],
    "commands/data-processing/texttonumbercommand.mdx": ["texttonumbercommand-03.png"],
    "commands/database/connecttodatabasecommand.mdx": ["connecttodatabasecommand-04.png"],
    "commands/datatable/exportdatasheettofilecommand.mdx": ["exportdatasheettofilecommand-03.png"],
    "commands/email/sendemailcommand.mdx": [
        "sendemailcommand-05.png", "sendemailcommand-06.png", "sendemailcommand-07.png",
        "sendemailcommand-08.png", "sendemailcommand-09.png",
    ],
    "commands/email/logintomailboxcommand.mdx": ["logintomailboxcommand-03.png", "logintomailboxcommand-04.png"],
    "commands/excel/addimagetoexcelcommand.mdx": ["addimagetoexcelcommand-03.png"],
    "commands/excel/autofillexcelcommand.mdx": ["autofillexcelcommand-03.png"],
    "commands/excel/clearexcelcellformatcommand.mdx": ["clearexcelcellformatcommand-03.png"],
    "commands/excel/deleteexcelimagecommand.mdx": ["deleteexcelimagecommand-03.png"],
    "commands/excel/deleteexcelsheetcommand.mdx": ["deleteexcelsheetcommand-03.png"],
    "commands/excel/exportexcelimagecommand.mdx": ["exportexcelimagecommand-03.png"],
    "commands/excel/filterexcelcolumncommand.mdx": ["filterexcelcolumncommand-05.png", "filterexcelcolumncommand-06.png"],
    "commands/excel/findexcelcellcommand.mdx": ["findexcelcellcommand-02.png", "findexcelcellcommand-03.png"],
    "commands/excel/getexcelsheetnamecommand.mdx": ["getexcelsheetnamecommand-04.png"],
    "commands/excel/launchexcelcommand.mdx": ["launchexcelcommand-03.png"],
    "commands/excel/readfilteredcontentcommand.mdx": ["readfilteredcontentcommand-03.png"],
    "commands/excel/renameexcelsheetcommand.mdx": ["renameexcelsheetcommand-04.png"],
    "commands/excel/saveexcelcommand.mdx": ["saveexcelcommand-03.png"],
    "commands/excel/setexcelcellformatcommand.mdx": ["setexcelcellformatcommand-03.png", "setexcelcellformatcommand-04.png"],
    "commands/excel/setexcelcellsizecommand.mdx": ["setexcelcellsizecommand-03.png"],
    "commands/excel/writeexcelcellcommand.mdx": ["writeexcelcellcommand-03.png"],
    "commands/excel/writeexcelcolumncommand.mdx": ["writeexcelcolumncommand-03.png"],
    "commands/excel/writeexcelrowcommand.mdx": ["writeexcelrowcommand-03.png"],
    "commands/feishu/getlarkbitablefieldcommand.mdx": ["getlarkbitablefieldcommand-04.png"],
    "commands/feishu/getlarkspreadsheetcommand.mdx": ["getlarkspreadsheetcommand-03.png"],
    "commands/feishu/IgnCWQ.mdx": ["IgnCWQ-03.png"],
    "commands/group-notification/notifywechatworkgroupcommand.mdx": ["notifywechatworkgroupcommand-03.png"],
    "commands/mouse-keyboard/hoverimagecommand.mdx": ["hoverimagecommand-05.png"],
    "commands/os/copyfoldercommand.mdx": ["copyfoldercommand-03.png"],
    "commands/os/decompressfilecommand.mdx": ["decompressfilecommand-04.png"],
    "commands/os/getfilescommand.mdx": ["getfilescommand-03.png"],
    "commands/os/movefoldercommand.mdx": ["movefoldercommand-04.png"],
    "commands/others/executepythonmodulecommand.mdx": ["executepythonmodulecommand-03.png"],
    "commands/others/sendhttprequestcommand.mdx": ["sendhttprequestcommand-03.png"],
    "commands/others/showtextinputcommand.mdx": ["showtextinputcommand-04.png"],
    "commands/others/zKl2eg.mdx": ["zKl2eg-04.png", "zKl2eg-05.png", "zKl2eg-06.png"],
}


IMAGE_LINE = re.compile(r"(?m)^[ \t]*!\[[^\]]*\]\([^)]+\)[ \t]*\r?\n?")


def title(text: str) -> str:
    match = re.search(r'(?m)^title:\s*["\'](.+?)["\']\s*$', text)
    if not match:
        raise ValueError("title not found")
    return match.group(1)


def image_name(path: Path, number: int) -> str:
    return f"{path.stem}-{number:02d}.png"


def markdown_images(page_title: str, kind: str, names: list[str], indent: str = "") -> str:
    return "\n\n".join(
        f"{indent}![{page_title}{kind}](images/{name})" for name in names
    )


def inject_tab(body: str, tab: str, block: str) -> str:
    if not block:
        return body
    pattern = re.compile(rf'(<Tab title="{re.escape(tab)}">\s*\r?\n)')
    updated, count = pattern.subn(lambda match: match.group(1) + block + "\n\n", body, count=1)
    if count != 1:
        raise ValueError(f"parameter tab not found: {tab}")
    return updated


def relocate_images(path: Path, names: list[str], target: str) -> None:
    text = path.read_text(encoding="utf-8")
    page_title = title(text)
    lines = []
    for name in names:
        pattern = re.compile(rf"(?m)^[ \t]*!\[[^\]]*\]\([^\n)]*images/{re.escape(name)}\)[ \t]*\r?\n?")
        match = pattern.search(text)
        if not match:
            raise ValueError(f"image reference not found for relocation: {path} {name}")
        line = match.group(0).strip()
        kind = "高级参数面板" if target == "advanced" else "使用示例"
        line = re.sub(r"!\[[^\]]*\]", f"![{page_title}{kind}]", line, count=1)
        lines.append(line)
        text = text[:match.start()] + text[match.end():]
    block = "\n\n".join(lines) + "\n\n"
    if target == "usage":
        pattern = re.compile(r"(?m)(^## 使用示例\s*$\r?\n)")
    elif target == "advanced":
        pattern = re.compile(r'(<Tab title="高级">\s*\r?\n)')
    else:
        raise ValueError(f"unknown relocation target: {target}")
    text, count = pattern.subn(lambda match: match.group(1) + block, text, count=1)
    if count != 1:
        raise ValueError(f"target section not found: {path} {target}")
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize(path: Path, layout: dict[str, list[int]]) -> tuple[str, dict[str, list[str]]]:
    text = path.read_text(encoding="utf-8")
    page_title = title(text)
    base = path.stem
    names = {
        key: [image_name(path, number) for number in values]
        for key, values in layout.items()
    }

    param_heading = re.search(r"(?m)^## 参数说明\s*$", text)
    usage_heading = re.search(r"(?m)^## 使用示例\s*$", text)
    effect_heading = re.search(r"(?m)^### 效果展示\s*$", text)
    if param_heading and not usage_heading:
        info = re.search(r"(?m)^<Info>\s*$", text)
        insert_at = info.start() if info else len(text)
        text = text[:insert_at].rstrip() + "\n\n## 使用示例\n\n### 效果展示\n\n" + text[insert_at:].lstrip()
    elif usage_heading and not effect_heading:
        info = re.search(r"(?m)^<Info>\s*$", text)
        insert_at = info.start() if info else len(text)
        text = text[:insert_at].rstrip() + "\n\n### 效果展示\n\n" + text[insert_at:].lstrip()
    param_heading = re.search(r"(?m)^## 参数说明\s*$", text)
    usage_heading = re.search(r"(?m)^## 使用示例\s*$", text)
    effect_heading = re.search(r"(?m)^### 效果展示\s*$", text)
    if not (param_heading and usage_heading and effect_heading):
        raise ValueError(f"required headings not found: {path}")
    suffix_match = re.search(r"(?m)^<Info>\s*$", text[effect_heading.end():])
    suffix_start = effect_heading.end() + suffix_match.start() if suffix_match else len(text)

    original_refs = {
        match.group(1).split("/")[-1]
        for match in re.finditer(r"!\[[^\]]*\]\((images/[^)]+)\)", text[param_heading.start():suffix_start])
    }
    desired_refs = {name for values in names.values() for name in values}
    if original_refs != desired_refs:
        raise ValueError(f"image mapping is not exhaustive for {path}: {original_refs ^ desired_refs}")

    param_body = IMAGE_LINE.sub("", text[param_heading.end():usage_heading.start()]).strip("\n")
    regular = markdown_images(page_title, "指令参数面板", names.get("regular", []), "    ")
    advanced = markdown_images(page_title, "高级参数面板", names.get("advanced", []), "    ")
    if "<Tabs>" in param_body:
        param_body = inject_tab(param_body, "常规", regular)
        param_body = inject_tab(param_body, "高级", advanced)
    elif regular:
        param_body = regular.strip() + "\n\n" + param_body

    usage_body = IMAGE_LINE.sub("", text[usage_heading.end():effect_heading.start()]).strip("\n")
    usage_block = markdown_images(page_title, "使用示例", names.get("usage", []))
    usage_body = (usage_block + "\n\n" + usage_body).strip()

    effect_body = IMAGE_LINE.sub("", text[effect_heading.end():suffix_start]).strip("\n")
    effect_block = markdown_images(page_title, "效果展示", names.get("effect", []))
    effect_body = (effect_block + "\n\n" + effect_body).strip()

    updated = (
        text[:param_heading.end()] + "\n\n" + param_body + "\n\n"
        + text[usage_heading.start():usage_heading.end()] + "\n\n" + usage_body + "\n\n"
        + text[effect_heading.start():effect_heading.end()] + "\n\n" + effect_body + "\n\n"
        + text[suffix_start:].lstrip("\n")
    )
    return updated, names


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    rows = []
    for relative, layout in LAYOUTS.items():
        path = root / relative
        updated, names = normalize(path, layout)
        path.write_text(updated, encoding="utf-8", newline="\n")
        rows.append({
            "command_title": title(updated),
            "relative_path": relative,
            "parameter_images": ";".join(names.get("regular", []) + names.get("advanced", [])),
            "usage_images": ";".join(names.get("usage", [])),
            "effect_images": ";".join(names.get("effect", [])),
            "status": "normalized",
        })
    for relative, names in ADVANCED_RELOCATIONS.items():
        relocate_images(root / relative, names, "advanced")
    for relative, names in USAGE_RELOCATIONS.items():
        relocate_images(root / relative, names, "usage")
    rows = []
    affected = sorted(set(LAYOUTS) | set(ADVANCED_RELOCATIONS) | set(USAGE_RELOCATIONS))
    section_patterns = {
        "parameter_images": r"(?ms)^##\s+参数说明\s*$\n(.*?)(?=^##\s+使用示例\s*$)",
        "usage_images": r"(?ms)^##\s+使用示例\s*$\n(.*?)(?=^###\s+效果展示\s*$)",
        "effect_images": r"(?ms)^###\s+效果展示\s*$\n(.*?)(?=^<Info>|\Z)",
    }
    for relative in affected:
        document = root / relative
        document_text = document.read_text(encoding="utf-8")
        row = {
            "command_title": title(document_text),
            "relative_path": relative,
            "status": "semantic_reclassified" if relative in ADVANCED_RELOCATIONS or relative in USAGE_RELOCATIONS else "normalized",
        }
        for field, pattern in section_patterns.items():
            match = re.search(pattern, document_text)
            refs = re.findall(r"!\[[^\]]*\]\((?:\./)?images/([^\)#]+)", match.group(1)) if match else []
            row[field] = ";".join(refs)
        rows.append(row)
    report = root / "reports" / "image-structure-audit.csv"
    with report.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    errors = []
    for row in rows:
        document = root / row["relative_path"]
        text = document.read_text(encoding="utf-8")
        section_refs = []
        for pattern in (
            r"(?ms)^##\s+参数说明\s*$\n(.*?)(?=^##\s+使用示例\s*$)",
            r"(?ms)^##\s+使用示例\s*$\n(.*?)(?=^###\s+效果展示\s*$)",
            r"(?ms)^###\s+效果展示\s*$\n(.*?)(?=^<Info>|\Z)",
        ):
            match = re.search(pattern, text)
            if not match:
                errors.append(f"missing section in {document}")
                continue
            section_refs.extend(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", match.group(1)))
        if len(section_refs) != len(set(section_refs)):
            errors.append(f"duplicate image reference in {document}")
        for reference in section_refs:
            image_path = document.parent / reference
            if not image_path.exists():
                errors.append(f"missing image {image_path}")
                continue
            try:
                with Image.open(image_path) as image:
                    image.verify()
            except Exception as error:
                errors.append(f"unreadable image {image_path}: {error}")
    if errors:
        raise ValueError("\n".join(errors))
    print(f"normalized={len(rows)} validation_errors=0 report={report.relative_to(root)}")


if __name__ == "__main__":
    main()
