#!/usr/bin/env python3
"""Apply deterministic command-page fixes established by the full audit."""

from __future__ import annotations

import re
from pathlib import Path

from audit_and_crop_command_images import command_docs


EFFECT_TEXT = {
    "commands/ai/extractkeywordscommand.mdx": "执行完成后，提取出的关键词将保存至指定变量。",
    "commands/ai/getemotionaltendencycommand.mdx": "执行完成后，返回文本的积极、中性或消极情感倾向，并保存至指定变量。",
    "commands/condition/elsecommand.mdx": "If 条件不成立时，流程执行 Else 分支中的指令。",
    "commands/condition/endifcommand.mdx": "End If 闭合当前条件判断块，随后流程继续执行后续指令。",
    "commands/condition/ifpagecontainscommand.mdx": "页面包含目标元素时，流程进入对应的条件分支并执行提示操作。",
    "commands/condition/ifwindowcontainscommand.mdx": "窗口包含目标元素时，流程进入对应的条件分支。",
    "commands/data-processing/gettimespancommand.mdx": "执行完成后，两个时间之间的时间差将保存至指定变量。",
    "commands/data-processing/numbertotextcommand.mdx": "执行完成后，数字将转换为文本并保存至指定变量。",
    "commands/data-processing/urldecodecommand.mdx": "执行完成后，URL 编码内容将被解码为原始文本。",
    "commands/datatable/exportdatasheettofilecommand.mdx": "执行完成后，数据表格内容将导出到指定文件。",
    "commands/datatable/readdatasheetcommand.mdx": "执行完成后，指定范围的数据表格内容将保存至结果变量。",
    "commands/desktop-automation/setwindowvisibilitycommand.mdx": "执行完成后，目标窗口将按配置显示或隐藏。",
    "commands/dingtalk/getdingtalksheetrowcountcommand.mdx": "执行完成后，钉钉表格的总行数将保存至指定变量。",
    "commands/email/getemailcontentcommand.mdx": "执行完成后，所选邮件内容将保存至指定变量。",
    "commands/excel/addimagetoexcelcommand.mdx": "执行完成后，图片将插入到指定 Excel 工作表位置。",
    "commands/excel/launchexcelcommand.mdx": "执行完成后，Excel 文件将被打开，并生成可供后续指令使用的 Excel 对象。",
    "commands/feishu/connecttolarkbitablecommand.mdx": "执行完成后，将生成可供后续多维表格指令使用的对象。",
    "commands/feishu/getlarkspreadsheetcommand.mdx": "执行完成后，将获取飞书电子表格对象并保存至指定变量。",
    "commands/flow/invokesubflowcommand.mdx": "执行完成后，子流程运行结果将返回主流程，主流程继续执行。",
    "commands/group-notification/notifylarkgroupcommand.mdx": "执行完成后，消息将发送到配置的飞书群机器人。",
    "commands/mouse-keyboard/mousescrollcommand.mdx": "执行完成后，鼠标滚轮将在目标位置按指定方向和次数滚动。",
}

LOGIC_TEXT = {
    "commands/ai/extractkeywordscommand.mdx": (
        "1. 选择 AI 引擎，并输入待处理的文本或选择文件。\n"
        "2. 执行【关键词提取】，将提取结果保存至指定变量。"
    ),
    "commands/desktop-automation/setwindowvisibilitycommand.mdx": (
        "1. 使用【获取窗口对象】获取目标窗口。\n"
        "2. 使用【设置窗口是否显示】将窗口设置为显示或隐藏状态。"
    ),
    "commands/google/getgooglecredentialcommand.mdx": (
        "1. 填写 Google OAuth 客户端 ID 和客户端密钥。\n"
        "2. 执行【获取谷歌访问凭证】，完成授权并将凭证保存至指定变量。"
    ),
    "commands/google/getgooglespreadsheetcommand.mdx": (
        "1. 选择已经获取的谷歌访问凭证，并填写目标表格地址及 Sheet 名称。\n"
        "2. 执行【获取谷歌表格】，将表格对象保存至指定变量供后续指令使用。"
    ),
    "commands/group-notification/notifylarkgroupcommand.mdx": (
        "1. 在飞书群中创建机器人，并将机器人 Webhook 地址填入指令。\n"
        "2. 填写消息内容并执行【飞书群通知】，将消息发送到目标群。"
    ),
}


NO_PARAMETER_TEXT = {
    "commands/os/clearclipboarddatacommand.mdx": "本指令无可配置参数，执行后会清空系统剪贴板内容。",
    "commands/others/catchcommand.mdx": "本指令无可配置参数，用于承接 Try 块中捕获到的异常。",
    "commands/others/endtrycommand.mdx": "本指令无可配置参数，仅作为 Try/Catch 异常处理块的结束标记。",
    "commands/others/trycommand.mdx": "本指令无可配置参数，用于标记需要捕获异常的流程起点。",
}


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def remove_image_line(text: str, name: str) -> str:
    return re.sub(
        rf"(?m)^[ \t]*!\[[^\]]*\]\([^\n)]*images/{re.escape(name)}\)[ \t]*\r?\n?",
        "",
        text,
    )


def add_effect(text: str, content: str) -> str:
    if content in text:
        return text
    heading = re.search(r"(?m)^### 效果展示\s*$", text)
    if heading:
        return text[:heading.end()] + f"\n\n{content}" + text[heading.end():]
    info_matches = list(re.finditer(r"(?m)^<Info>\s*$", text))
    insert_at = info_matches[-1].start() if info_matches else len(text)
    block = f"### 效果展示\n\n{content}\n\n"
    return text[:insert_at].rstrip() + "\n\n" + block + text[insert_at:].lstrip()


def replace_effect_section(text: str, content: str) -> str:
    pattern = re.compile(r"(?ms)^### 效果展示\s*$.*?(?=^<Info>\s*$)")
    updated, count = pattern.subn(f"### 效果展示\n\n{content}\n\n", text, count=1)
    if count != 1:
        raise ValueError("效果展示章节不存在")
    return updated


def add_logic(text: str, content: str) -> str:
    if content in text:
        return text
    usage = re.search(r"(?m)^## 使用示例\s*$", text)
    if not usage:
        raise ValueError("使用示例章节不存在")
    effect = re.search(r"(?m)^### 效果展示\s*$", text[usage.end():])
    info = re.search(r"(?m)^<Info>\s*$", text[usage.end():])
    candidates = [match.start() for match in (effect, info) if match]
    insert_at = usage.end() + (min(candidates) if candidates else len(text) - usage.end())
    block = f"\n\n**该流程执行逻辑：**\n\n{content}\n"
    return text[:insert_at].rstrip() + block + "\n" + text[insert_at:].lstrip()


def replace_empty_parameter_tables(text: str, replacement: str) -> str:
    empty_table = re.compile(
        r"(?m)^[ \t]*\|\s*参数\s*\|\s*说明\s*\|\s*\r?\n"
        r"(?:[ \t]*\r?\n)*"
        r"^[ \t]*\|\s*---\s*\|\s*---\s*\|\s*$"
    )
    occurrence = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal occurrence
        occurrence += 1
        return replacement if occurrence == 1 else "本指令暂无高级参数。"

    text, count = empty_table.subn(replace, text)
    if count == 0:
        raise ValueError("未找到常规参数空表")
    return text


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    changed: list[str] = []
    for path in command_docs(root):
        rel = relative(path, root)
        original = path.read_text(encoding="utf-8")
        text = original.replace("**此流程执行逻辑：**", "**该流程执行逻辑：**")

        if rel in {"commands/condition/elsecommand.mdx", "commands/condition/endifcommand.mdx"}:
            misplaced = EFFECT_TEXT[rel]
            text = re.sub(
                rf"(?ms)\n### 效果展示\s*\n+{re.escape(misplaced)}\s*(?=\n<Info>)",
                "\n",
                text,
                count=1,
            )

        if rel == "commands/web-automation/startmonitornetworkcommand.mdx":
            effect_block = (
                "### 效果展示\n\n"
                "![开始监听网页请求 - 效果展示](images/web-monitor-start-09.png)\n\n"
            )
            text = text.replace(effect_block, "")
            info_matches = list(re.finditer(r"(?m)^<Info>\s*$", text))
            if info_matches:
                insert_at = info_matches[-1].start()
                text = text[:insert_at].rstrip() + "\n\n" + effect_block + text[insert_at:]

        if rel in NO_PARAMETER_TEXT:
            if NO_PARAMETER_TEXT[rel] not in text:
                text = replace_empty_parameter_tables(text, NO_PARAMETER_TEXT[rel])
        if rel == "commands/data-processing/createdictionarycommand.mdx":
            if "| **保存字典对象至** |" not in text:
                text = replace_empty_parameter_tables(
                    text,
                    "| 参数 | 说明 |\n"
                    "| --- | --- |\n"
                    "| **保存字典对象至** | 设置用于保存新建字典对象的变量名称。 |",
                )

        if rel in LOGIC_TEXT:
            logic_text = LOGIC_TEXT[rel]
            if logic_text in text:
                before = text[:text.index(logic_text)]
                usage_start = before.rfind("## 使用示例")
                if "**该流程执行逻辑：**" not in before[usage_start:]:
                    text = text.replace(logic_text, f"**该流程执行逻辑：**\n\n{logic_text}", 1)
            else:
                # Remove an empty marker before inserting the complete block.
                text = re.sub(r"(?m)^\*\*该流程执行逻辑：\*\*\s*$", "", text)
                text = add_logic(text, logic_text)

        if rel == "commands/condition/elsecommand.mdx":
            text = text.replace("![Else 使用示例 - 效果展示]", "![Else 使用示例 - 流程搭建]")

        effect_images: list[str] = []
        if rel == "commands/condition/ifpagecontainscommand.mdx":
            effect_images = ["if-page-03.png", "if-page-04.png"]
        elif rel == "commands/condition/ifwindowcontainscommand.mdx":
            effect_images = ["if-win-03.png"]
        for name in effect_images:
            text = remove_image_line(text, name)

        if rel in EFFECT_TEXT:
            effect = EFFECT_TEXT[rel]
            if effect_images:
                page_title = re.search(r'(?m)^title:\s*["\'](.+?)["\']', text).group(1)
                effect += "\n\n" + "\n\n".join(
                    f"![{page_title}效果展示](images/{name})" for name in effect_images
                )
                text = replace_effect_section(text, effect)
            else:
                text = add_effect(text, effect)

        for invalid_name in (
            "win_entertextcommand-04.png",
            "win_setcheckboxcommand-03.png",
            "web-cookie-get-03.png",
            "web-cookie-get-04.png",
        ):
            text = remove_image_line(text, invalid_name)

        # Keep whitespace readable after historical bulk relocations.
        text = re.sub(r"\n{5,}", "\n\n\n", text).rstrip() + "\n"
        if text != original:
            path.write_text(text, encoding="utf-8", newline="\n")
            changed.append(rel)

    print(f"normalized={len(changed)}")
    for item in changed:
        print(item)


if __name__ == "__main__":
    main()
