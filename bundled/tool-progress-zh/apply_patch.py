#!/usr/bin/env python3
"""
工具進度標籤繁中補丁（tool-progress-zh）

目標：agent/display.py
- 注入 _TOOL_VERBS_ZH_HANT
- get_tool_verb / build_tool_label / tool_verb_connector / build_status_phrase
  依 display.language（zh-TW／zh-hant）出繁中

不依賴作者本機。冪等。Hermes update 後重跑。
"""
from __future__ import annotations

import ast
import os
import re
import shutil
import sys
from pathlib import Path

MARKER = "_TOOL_VERBS_ZH_HANT"

INJECT_BLOCK = r'''
# Traditional Chinese (zh-hant / zh-TW) surface labels for Telegram tool-progress.
# Injected by hermes-tw-setup bundled/tool-progress-zh (re-run after hermes update).
_TOOL_VERBS_ZH_HANT: dict[str, str] = {
    "web_search": "搜尋網路",
    "web_extract": "讀取網頁",
    "browser_navigate": "瀏覽網頁",
    "browser_click": "點擊",
    "browser_type": "輸入文字",
    "read_file": "讀取檔案",
    "write_file": "寫入檔案",
    "patch": "編輯檔案",
    "search_files": "搜尋檔案",
    "terminal": "執行指令",
    "execute_code": "執行程式",
    "image_generate": "產生圖片",
    "video_generate": "產生影片",
    "text_to_speech": "產生語音",
    "vision_analyze": "檢視圖片",
    "session_search": "搜尋過往對話",
    "skill_view": "讀取技能",
    "skills_list": "列出技能",
    "skill_manage": "更新技能",
    "delegate_task": "委派任務",
    "cronjob": "設定排程",
    "clarify": "詢問確認",
    "memory": "更新記憶",
    "todo": "更新待辦",
}


def _tool_label_lang() -> str:
    """Active UI language for tool-progress labels (env > config)."""
    try:
        from agent.i18n import get_language
        return get_language() or "en"
    except Exception:
        return "en"


def _is_zh_hant_labels() -> bool:
    lang = _tool_label_lang()
    return lang in {"zh-hant", "zh"} or str(lang).startswith("zh")


def _tool_verbs() -> dict[str, str]:
    """Return the verb map for the active language."""
    if _is_zh_hant_labels():
        merged = dict(_TOOL_VERBS)
        merged.update(_TOOL_VERBS_ZH_HANT)
        return merged
    return _TOOL_VERBS

'''


def _find_display_py() -> Path:
    env_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()
    candidates: list[Path] = []
    try:
        import agent.display as ad  # type: ignore

        candidates.append(Path(ad.__file__).resolve())
    except Exception:
        pass
    try:
        import hermes_cli  # type: ignore

        root = Path(hermes_cli.__file__).resolve().parent.parent
        candidates.append(root / "agent" / "display.py")
    except Exception:
        pass
    candidates.extend(
        [
            env_home / "hermes-agent" / "agent" / "display.py",
            Path.home() / ".hermes" / "hermes-agent" / "agent" / "display.py",
            Path("/opt/hermes/agent/display.py"),
            Path("/opt/hermes/hermes-agent/agent/display.py"),
        ]
    )
    seen: set[Path] = set()
    for c in candidates:
        try:
            c = c.resolve()
        except Exception:
            continue
        if c in seen:
            continue
        seen.add(c)
        if c.is_file():
            return c
    raise FileNotFoundError(
        "找不到 agent/display.py；請設定 HERMES_HOME 或確認 Hermes 安裝路徑"
    )


def _already_patched(text: str) -> bool:
    return MARKER in text and "def _tool_verbs(" in text and "def _is_zh_hant_labels(" in text


def _insert_after_tool_verbs(text: str) -> str:
    m = re.search(r"^_TOOL_VERBS:\s*dict\[str,\s*str\]\s*=\s*\{", text, re.M)
    if not m:
        m = re.search(r"^_TOOL_VERBS\s*=\s*\{", text, re.M)
    if not m:
        raise RuntimeError("找不到 _TOOL_VERBS = { ... } 定義，上游可能改版")

    start = text.index("{", m.start())
    depth = 0
    end = None
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        raise RuntimeError("_TOOL_VERBS dict 括號不平衡")

    insert_at = end + 1
    if insert_at < len(text) and text[insert_at] == "\n":
        insert_at += 1

    if MARKER in text:
        return text

    return text[:insert_at] + "\n" + INJECT_BLOCK.lstrip("\n") + text[insert_at:]


def _patch_functions(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []

    text2, c = re.subn(
        r"(def get_tool_verb\(tool_name: str\) -> str \| None:.*?if not _friendly_tool_labels:\n\s+return None\n\s+)return _TOOL_VERBS\.get\(tool_name\)",
        r"\1return _tool_verbs().get(tool_name)",
        text,
        count=1,
        flags=re.S,
    )
    if c:
        text = text2
        notes.append("get_tool_verb → _tool_verbs()")
    else:
        text2, c = re.subn(
            r"return _TOOL_VERBS\.get\(tool_name\)",
            "return _tool_verbs().get(tool_name)",
            text,
            count=1,
        )
        if c:
            text = text2
            notes.append("get_tool_verb fallback replace")

    new_conn = (
        "def tool_verb_connector(tool_name: str) -> str:\n"
        '    """Return the connector between a verb and its preview (" for " or " ")."""\n'
        "    if tool_name not in _TOOL_VERBS_FOR_CONNECTOR:\n"
        '        return " "\n'
        '    return "：" if _is_zh_hant_labels() else " for "'
    )
    if 'return "：" if _is_zh_hant_labels() else " for "' in text:
        notes.append("tool_verb_connector already zh-aware")
    else:
        text2, c = re.subn(
            r'def tool_verb_connector\(tool_name: str\) -> str:.*?return " for " if tool_name in _TOOL_VERBS_FOR_CONNECTOR else " "',
            new_conn,
            text,
            count=1,
            flags=re.S,
        )
        if c:
            text = text2
            notes.append("tool_verb_connector zh colon")
        else:
            notes.append("WARN: tool_verb_connector 未改（上游可能改版）")

    if 'f"正在{verb}"' in text or "f'正在{verb}'" in text:
        notes.append("build_status_phrase already zh-aware")
    else:
        text2, c1 = re.subn(
            r"verb = _TOOL_VERBS\.get\(tool_name\)",
            "verb = _tool_verbs().get(tool_name)",
            text,
        )
        text = text2
        text2, c3 = re.subn(
            r'head = f"is \{verb\[0\]\.lower\(\)\}\\{verb\[1:\]\}"',
            'head = f"正在{verb}" if _is_zh_hant_labels() else f"is {verb[0].lower()}{verb[1:]}"',
            text,
            count=1,
        )
        text = text2
        text2, c4 = re.subn(
            r'head = f"is using \{tool_name\}"',
            'head = f"正在使用 {tool_name}" if _is_zh_hant_labels() else f"is using {tool_name}"',
            text,
            count=1,
        )
        text = text2
        if c1 or c3 or c4:
            notes.append("build_status_phrase zh head")
        else:
            notes.append("WARN: build_status_phrase 可能未改")

    # Remaining _TOOL_VERBS.get in build_tool_label etc.
    text2, c = re.subn(
        r"verb = _TOOL_VERBS\.get\(tool_name\)",
        "verb = _tool_verbs().get(tool_name)",
        text,
    )
    text = text2
    if c:
        notes.append(f"verb lookups → _tool_verbs ({c})")

    if 'return f"{verb}{tool_verb_connector(tool_name)}{preview}"' in text:
        notes.append("build_tool_label connector already unified")
    else:
        text2, c = re.subn(
            r'if tool_name in _TOOL_VERBS_FOR_CONNECTOR:\n\s+return f"\{verb\} for \{preview\}"\n\s+return f"\{verb\} \{preview\}"',
            'return f"{verb}{tool_verb_connector(tool_name)}{preview}"',
            text,
            count=1,
        )
        if c:
            text = text2
            notes.append("build_tool_label connector unified")
        else:
            notes.append("WARN: build_tool_label connector 可能未改")

    return text, notes


def apply_patch() -> int:
    path = _find_display_py()
    print(f"目標：{path}")
    original = path.read_text(encoding="utf-8")

    if _already_patched(original):
        print("已是繁中進度標籤補丁，無需變更")
        return 0

    text = original
    if MARKER not in text:
        text = _insert_after_tool_verbs(text)
        print("已注入 _TOOL_VERBS_ZH_HANT 與語言切換函式")

    text, notes = _patch_functions(text)
    for n in notes:
        print(" ", n)

    try:
        ast.parse(text)
    except SyntaxError as e:
        print(f"❌ 套用後 SyntaxError (line {e.lineno}: {e.msg}) — 不寫入")
        return 2

    bak = path.with_suffix(path.suffix + ".bak.before_tool_progress_zh")
    if not bak.exists():
        shutil.copy2(path, bak)
        print(f"備份：{bak.name}")
    path.write_text(text, encoding="utf-8")
    print("補丁完成。請重啟所有 Hermes gateway 後生效。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(apply_patch())
    except Exception as e:
        print(f"❌ {e}")
        raise SystemExit(1)
