import os
#!/usr/bin/env python3
"""
技能敘述中文化補丁
遞迴掃描 ~/.hermes/skills/ 下所有 SKILL.md，透過 name frontmatter 對應中文。
更新 Hermes 後執行一次即可。
"""

import re
from pathlib import Path

SKILLS_DIR = Path(os.getenv("HERMES_HOME", str(Path.home() / ".hermes"))) / "skills"

# name frontmatter → 中文描述
NAME_TO_ZH = {
    # mlops
    "huggingface-hub": "Hugging Face Hub CLI 搜尋、下載、上傳模型",
    "lm-evaluation-harness": "在 60+ 學術基準上評估 LLM（MMLU、HumaEval 等）",
    "weights-and-biases": "追蹤 ML 實驗並自動記錄視覺化",
    "gguf": "GGUF 格式和 llama.cpp 量化（高效 CPU/GPU 推論）",
    "guidance": "用正規表達式和語法控制 LLM 輸出，保證輸出結構",
    "llama-cpp": "在 CPU、Apple Silicon、消費者 GPU 上執行 LLM 推論",
    "obliteratus": "移除開放權重 LLM 的拒絕行為",
    "outlines": "保證生成有效的 JSON/XML/程式碼結構",
    "vllm": "以高吞吐量服務 LLM（vLLM PagedAttention）",
    "axolotl": "使用 Axolotl 微調 LLM（專家指引）",
    "grpo-rl-training": "GRPO/RL 微調（TRL 強化學習訓練）",
    "peft": "LoRA、QLoRA 等參數高效微調技術",
    "pytorch-fsdp": "完全分片資料並行訓練（FSDP）專家指引",
    "trl-fine-tuning": "使用 TRL 強化學習微調 LLM",
    "unsloth": "快速微調 Unsloth（2-5x 加速）",
    "clip": "連接視覺和語言的 CLIP 模型，零樣本影像分類",
    "segment-anything": "Segment Anything 基礎模型，零樣本影像分割",
    "stable-diffusion": "最先进的文字生成圖片模型（Stable Diffusion）",
    "whisper": "通用語音辨識模型，支援多語言轉文字",
    "dspy": "用宣告式程式設計建立複雜 AI 系統（DSPy）",
    "audiocraft": "PyTorch 音樂生成庫（文字轉音樂）",
    "manim-video": "數學和技術動畫生成（3Blue1Brown 風格）",

    # productivity
    "github-trending-report": "生成 GitHub 趨勢報告（每日追蹤）",
    "google-workspace": "Gmail、行事曆、雲端硬碟、通訊錄整合",
    "linear": "Linear 專案管理工作",
    "make-health-monitor": "監控 Make.com 66 個 Scenario 健康狀態",
    "nano-pdf": "用自然語言指令編輯 PDF",
    "notion": "Notion API 建立和管理頁面、資料庫",
    "ocr-and-documents": "從 PDF 和掃描文件擷取文字",
    "powerpoint": "將講稿一鍵生成專業級 HTML 簡報",
    "wordpress-longform-publishing": "發布 2000+ 字圖文並茂的 WordPress 文章",

    # research
    "arxiv": "從 arXiv 搜尋和擷取學術論文",
    "blogwatcher": "監控部落格和 RSS/Atom 饋給更新",
    "polymarket": "查詢 Polymarket 預測市場數據",

    # media
    "gif-search": "從 Tenor 搜尋和下載 GIF",
    "heartmula": "設定和執行 HeartMuLa 開源音樂生成",
    "songsee": "生成聲譜圖和音頻特徵視覺化",
    "youtube-content": "取得 YouTube 影片字幕並轉換成文章",

    # social-media
    "xitter": "透過 x-cli 終端機用戶操作 X/Twitter",

    # gaming
    "minecraft-modpack-server": "從 CurseForge/Modrinth 架設模組化 Minecraft 伺服器",
    "pokemon-player": "透過無頭模擬器自動遊玩 Pokemon 遊戲",

    # creative
    "ascii-art": "用 pyfiglet 生成 ASCII 藝術（571 種字體）",
    "ascii-video": "ASCII 藝術影片產製管線（任何格式）",
    "excalidraw": "建立手繪風格 Excalidraw 圖表",
    "songwriting-and-ai-music": "歌曲創作和 AI 音樂生成提示（Suno）",

    # note-taking
    "obsidian": "讀取、搜尋、建立 Obsidian 保險庫中的筆記",

    # github
    "codebase-inspection": "使用 pygount 檢查程式碼並計算 LOC",
    "github-auth": "設定 GitHub 認證（git/universal）",
    "github-code-review": "分析 git diff，留下行內程式碼審查意見",
    "github-issues": "建立、管理、分類、關閉 GitHub Issues",
    "github-pr-workflow": "完整 Pull Request 生命週期",
    "github-repo-management": "克隆、建立、分叉、設定和管理 GitHub 倉庫",

    # devops
    "webhook-subscriptions": "建立和管理 Webhook 訂閱（事件驅動架構）",

    # data-science
    "jupyter-live-kernel": "使用即時 Jupyter Kernel 進行狀態迭代 Python 分析",

    # mcp
    "mcporter": "使用 mcporter CLI 設定、認證、呼叫 MCP 伺服器",
    "native-mcp": "內建 MCP 客戶端連接外部 MCP 伺服器並自動發現工具",

    # openclaw-imports
    "browser": "操控已登入的 Chrome 瀏覽器（CDP Attach Mode）",
    "claude-code-delegate": "委託 Claude Code 處理編碼任務",
    "daily-automation": "日常自動化工作流程",
    "deep-research": "最大化資料收集的深入研究",
    "github-monitor": "監控 GitHub 倉庫動態（Issues、PR、Release）",
    "make-monitor": "監控 Make.com Scenario 健康狀態",
    "portfolio-update": "自動解析並更新持倉報告",
    "ppt-generator": "將講稿一鍵生成專業級 HTML 演示稿",
    "quotation-generator": "生成報價單",
    "site-deploy": "透過 Cloudflare Tunnel 部署靜態網站",
    "article-image-generator": "產生符合 替代方案有限公司官網風格的 1:1 文章圖卡",
    "ui-ux-pro-max": "UI/UX 設計與實作（含 替代方案有限公司設計系統）",
    "weekly-content-series": "每週內容系列自動化",

    # autonomous-ai-agents
    "claude-code": "委託 Claude Code 處理編碼任務（Anthropic CLI agent）",
    "codex": "委託 OpenAI Codex CLI 處理編碼任務",
    "opencode": "委託 OpenCode CLI 處理編碼任務",

    # smart-home
    "openhue": "透過 OpenHue API 控制 Philips Hue 照明",

    # red-teaming
    "godmode": "使用 G0DM0D3 技巧越獄 API 服務的 LLM",

    # software-development
    "plan": "Plan 模式：檢查上下文、寫 Markdown 計劃、委託 Claude Code 執行",
    "requesting-code-review": "提交前驗證管線：靜態安全掃描、程式碼審查、單元測試",
    "subagent-driven-development": "使用子代理執行實施計劃（獨立開發流程）",
    "systematic-debugging": "系統性偵錯：任何錯誤、測試失敗、未預期行為都用這個",
    "test-driven-development": "TDD 測試驅動開發：實作任何功能前先寫測試",
    "writing-plans": "寫作計劃：多步驟規格和需求转化为实施计划",

    # apple
    "imessage": "透過 AppleScript 控制 iMessage 傳送訊息",
    "apple-notes": "讀取和寫入 Apple Notes 筆記",
    "apple-reminders": "與 Apple Reminders 同步管理提醒事項",
    "findmy": "查找我的 Apple 裝置位置",

    # leisure
    "find-nearby": "尋找附近場所（餐廳、咖啡廳、酒吧、藥局等）",

    # dogfood
    "dogfood": "系統性探索 QA 測試 web 應用程式",
}


def patch_skill(skill_md: Path, zh_desc: str) -> bool:
    """修改單一 SKILL.md 的 description frontmatter。"""
    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception:
        return False

    # 已經是中文就不重複補丁
    if zh_desc in content:
        return False

    # 替換 description: 行
    pattern = r'^description:\s*.+$'
    replacement = f'description: {zh_desc}'
    new_content, n = re.subn(pattern, replacement, content, flags=re.MULTILINE)

    if n > 0:
        skill_md.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    total = 0
    patched = 0
    skipped = 0

    for skill_md in SKILLS_DIR.rglob("SKILL.md"):
        # 跳過 .hub 等目錄
        if ".hub" in skill_md.parts:
            continue

        try:
            content = skill_md.read_text(encoding="utf-8")
            frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if not frontmatter_match:
                continue

            fm_text = frontmatter_match.group(1)
            name_match = re.search(r'^name:\s*(.+)$', fm_text, re.MULTILINE)
            if not name_match:
                continue

            skill_name = name_match.group(1).strip()
        except Exception:
            continue

        if skill_name in NAME_TO_ZH:
            total += 1
            if patch_skill(skill_md, NAME_TO_ZH[skill_name]):
                patched += 1
                print(f"✓ {skill_name}")
            else:
                skipped += 1

    print(f"\n補丁完成：共 {patched}/{total} 個技能更新。")


if __name__ == "__main__":
    main()