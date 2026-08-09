#!/usr/bin/env python3
"""
Telegram Menu 繁體中文補丁
將 hermes_cli/commands.py 的 COMMAND_REGISTRY description 改成繁體中文
更新 Hermes 後執行一次即可
"""

import re

COMMANDS_ZH = {
    # Session
    "Acknowledge platform start pings without a reply": "確認平台啟動 ping（不回應）",
    "Start a new session (fresh session ID + history)": "開始新對話（新 session ID + 清除歷史）",
    "Enable or inspect Telegram DM topic sessions": "啟用或檢查 Telegram 私訊主題對話",
    "Clear screen and start a new session": "清除螢幕並開始新對話",
    "Force a full UI repaint (recovers from terminal drift)": "強制完整重繪 UI（修復終端顯示偏移）",
    "Show conversation history": "顯示對話歷史",
    "Save the current conversation": "儲存目前對話",
    "Retry the last message (resend to agent)": "重試上一則訊息（重新送給 AI）",
    "Remove the last user/assistant exchange": "移除上一組對話",
    "Back up N user turns and re-prompt (default 1)": "回溯 N 輪對話並重新提問（預設 1 輪）",
    "Set a title for the current session": "設定對話標題",
    "Hand off this session to a messaging platform (Telegram, Discord, etc.)": "將此對話移交到訊息平台（Telegram、Discord 等）",
    "Branch the current session (explore a different path)": "分支對話（探索不同方向）",
    "Manually compress conversation context": "手動壓縮對話內容",
    "Compress conversation context (add 'here [N]' to keep recent N turns)": "壓縮對話上下文（加 'here [N]' 保留最近 N 輪）",
    "List or restore filesystem checkpoints": "列出/還原檔案系統檢查點",
    "Kill all running background processes": "停止所有背景程序",
    "Approve a pending dangerous command": "授權待確認的危險指令",
    "Deny a pending dangerous command": "拒絕待確認的危險指令",
    "Run a prompt in the background": "背景執行提示詞",
    "Ephemeral side question using session context (no tools, not persisted)": "暫時側問（使用 session 上下文，無工具，不留存）",
    "Queue a prompt for the next turn (doesn't interrupt)": "排隊下一輪（不會打斷 current）",
    "Show session info": "顯示 session 狀態",
    "Show session, model, token, and context info": "顯示對話、模型、token 和上下文資訊",
    "Show active profile name and home directory": "顯示當前 profile 名稱和主目錄",
    "Set this chat as the home channel": "將此聊天室設為主頻道",
    "Resume a previously-named session": "繼續之前的命名對話",
    "Set a standing goal Hermes works on across turns until achieved": "設定 Hermes 持續執行的常駐目標",
    "Add or manage extra criteria on the active goal": "新增或管理當前目標的附加條件",
    "Browse and resume previous sessions": "瀏覽並繼續之前的對話",

    # 新指令
    "Create or restore state snapshots of Hermes config/state": "建立或還原 Hermes 設定/狀態的快照",
    "Show active agents and running tasks": "顯示活躍的代理和執行中的任務",
    "Inject a message after the next tool call without interrupting": "在下一個工具呼叫後注入訊息，不打斷流程",
    "Show Google Gemini Code Assist quota usage": "顯示 Google Gemini Code Assist 配額使用量",
    "Toggle fast mode \u2014 OpenAI Priority Processing / Anthropic Fast Mode (Normal/Fast)": "切換快速模式 \u2014 OpenAI 優先處理 / Anthropic Fast Mode（正常/快速）",
    "Reload .env variables into the running session": "將 .env 變數重新載入執行中的 session",
    "Gracefully restart the gateway after draining active runs": "在傾倒執行中的任務後優雅地重啟 gateway",
    "Show token usage and rate limits for the current session": "顯示目前 session 的 token 使用量和速率限制",
    "Copy the last assistant response to clipboard": "複製上一個助理解答到剪貼簿",
    "Attach clipboard image from your clipboard": "附加剪貼簿中的圖片",
    "Attach a local image file for your next prompt": "附加本地圖檔作為下一個提示詞的圖片",
    "Show token usage for the current session": "顯示目前 session 的 token 使用量和速率限制",

    # Configuration
    "Show current configuration": "顯示目前設定",
    "Switch model for this session": "切換這個 session 的模型",
    "Switch model (persists by default)": "切換模型（預設會永久儲存）",
    "Toggle codex app-server runtime for OpenAI/Codex models": "切換 OpenAI/Codex 模型的 codex app-server 執行環境",
    "Show available providers and current provider": "顯示可用供應商和當前供應商",
    "View/set custom system prompt": "查看/設定自訂系統提示詞",
    "Set a predefined personality": "設定預設人格",
    "Toggle the context/model status bar": "切換狀態列",
    "Cycle tool progress display: off -> new -> all -> verbose": "循環工具進度顯示：關 → 新 → 全部 → 詳細",
    "Toggle gateway runtime-metadata footer on final replies": "切換 gateway 回覆末尾的執行資訊頁腳",
    "Toggle YOLO mode (skip all dangerous command approvals)": "切換 YOLO 模式（跳過所有危險指令授權）",
    "Manage reasoning effort and display": "管理思考層級和顯示方式",
    "Show or change the display skin/theme": "顯示或更換主題外觀",
    "Pick the TUI busy-indicator style": "選擇 TUI 忙碌指示器樣式",
    "Toggle voice mode": "切換語音模式",
    "Control what Enter does while Hermes is working": "控制 Hermes 工作中按下 Enter 的行為",

    # Tools & Skills
    "Manage tools: /tools [list|disable|enable] [name...]": "管理工具：/tools [list|disable|enable] [名稱...]",
    "List available toolsets": "列出可用工具集",
    "Search, install, inspect, or manage skills": "搜尋、安裝、檢視、管理技能",
    "Manage scheduled tasks": "管理排程任務",
    "Reload MCP servers from config": "從設定檔重新載入 MCP 伺服器",
    "Connect browser tools to your live Chrome via CDP": "透過 CDP 連接瀏覽器工具到你已登入的 Chrome",
    "Connect browser tools to your live Chromium-family browser via CDP": "透過 CDP 連接瀏覽器工具到你已登入的 Chromium 瀏覽器",
    "List installed plugins and their status": "列出已安裝的插件和狀態",
    "Review pending memory writes / toggle the approval gate": "檢查待寫入的記憶／切換核准開關",
    "List skill bundles (aliases /<name> for multiple skills)": "列出技能組合包（別名 /<name> 對應多個技能）",
    "Review suggested automations (accept/dismiss)": "檢查建議的自動化（接受／忽略）",
    "Set up an automation from a blueprint template": "從藍圖模板建立自動化",
    "Background skill maintenance (status, run, pin, archive, list-archived)": "背景技能維護（狀態、執行、釘選、歸檔、列出已歸檔）",
    "Multi-profile collaboration board (tasks, links, comments)": "多 profile 協作看板（任務、連結、留言）",
    "Re-scan ~/.hermes/skills/ for newly installed or removed skills": "重新掃描 ~/.hermes/skills/ 尋找新增或移除的技能",

    # Info
    "Browse all commands and skills (paginated)": "瀏覽所有指令和技能（分頁）",
    "Show available commands": "顯示所有可用指令",
    "Show usage insights and analytics": "顯示使用分析",
    "Show gateway/messaging platform status": "顯示訊息平台狀態",
    "Check clipboard for an image and attach it": "檢查剪貼簿是否有圖片並附加",
    "Update Hermes Agent to the latest version": "更新 Hermes 到最新版本",
    "Show your slash command access (admin / user)": "顯示你的斜線指令權限（管理員／使用者）",
    "Show Nous credit balance and top up": "顯示 Nous 點數餘額並加值",
    "Manage Nous terminal billing \u2014 buy credits, auto-reload, limits": "管理 Nous 終端計費——購買點數、自動加值、額度限制",
    "Pause, resume, or list a failing gateway platform": "暫停、恢復或列出故障的 gateway 平台",
    "Show Hermes Agent version": "顯示 Hermes Agent 版本",
    "Upload debug report and get shareable links": "上傳除錯報告並取得分享連結",
    "Upload debug report (system info + logs) and get shareable links": "上傳除錯報告（系統資訊 + 記錄）並取得分享連結",

    # Exit
    "Exit the CLI": "離開 CLI",
    "Exit the CLI (use --delete to also remove session history)": "離開 CLI（加 --delete 可同時刪除對話歷史）",
}


def _find_commands_py() -> str:
    import os
    from pathlib import Path
    env_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()
    candidates = [
        env_home / "hermes-agent" / "hermes_cli" / "commands.py",
        Path.home() / ".hermes" / "hermes-agent" / "hermes_cli" / "commands.py",
        Path("/opt/hermes/hermes_cli/commands.py"),
        Path("/opt/hermes/hermes-agent/hermes_cli/commands.py"),
    ]
    # sibling of installed hermes package
    try:
        import hermes_cli
        candidates.insert(0, Path(hermes_cli.__file__).resolve().parent / "commands.py")
    except Exception:
        pass
    for c in candidates:
        if c.is_file():
            return str(c)
    raise FileNotFoundError(
        "找不到 hermes_cli/commands.py；請設定 HERMES_HOME 或確認 Hermes 安裝路徑"
    )


def apply_patch():
    commands_py = _find_commands_py()
    print(f"目標：{commands_py}")

    with open(commands_py, "r", encoding="utf-8") as f:
        content = f.read()

    count = 0
    for en, zh in COMMANDS_ZH.items():
        escaped_en = re.escape(en)
        # Match: CommandDef("name", "...desc..."  followed by closing quote+comma+whitespace
        pattern = r'(CommandDef\("[^"]+", ")' + escaped_en + r'(",\s+)'
        replacement = r'\g<1>' + zh + r'\g<2>'
        new_content, n = re.subn(pattern, replacement, content)
        if n > 0:
            content = new_content
            count += n

    if count == 0:
        print("所有指令已是中文，無需補丁")
        return

    # Validate syntax
    import ast
    import shutil
    try:
        ast.parse(content)
    except SyntaxError as e:
        print(f"❌ 套用後產生 SyntaxError (line {e.lineno}: {e.msg})")
        print("   不寫入檔案，原檔保持不變")
        return

    # Backup
    shutil.copy(commands_py, commands_py + ".bak.before_telegram_zh_apply")

    with open(commands_py, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"補丁完成！共替換 {count} 處。")


if __name__ == "__main__":
    apply_patch()
