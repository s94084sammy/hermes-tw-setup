# 預裝技能政策（台灣通用基線）

## 原則

1. 保留 Hermes **官方 bundled** 技能（不要 `.no-bundled-skills` 除非使用者明確 opt-out）。
2. 加裝少量**中性、高頻**技能；不預裝任何客戶／公司個案 skill。
3. 副 profile 透過 `external_dirs` 共用主 skills，不必重複大包複製。

## A. 官方 bundled

- 新建 profile：`hermes profile create` 預設會 seed。
- check：主 skills 目錄存在，且**沒有**根目錄 `.no-bundled-skills` 標記（除非使用者刻意）。
- 若 opt-out 過又想恢復：`hermes skills opt-in`（見官方）。

## B. 台灣基線建議（apply 會確保）

| 技能 | 用途 | 安裝方式 |
|------|------|----------|
| `hermes-tw-setup` | 本基線 check／apply | 複製本 skill 目錄到 `$HERMES_HOME/skills/hermes-tw-setup` |
| `telegram-commands-zh` | Telegram 選單繁中 | **發行包** `bundled/telegram-commands-zh` → skills |
| `duckduckgo-search` | 免 API 搜尋備援 | `hermes skills repair-official duckduckgo-search --restore -y` |
| `agnes-image-generation` | **免費生圖預設**（Agnes AI） | **發行包** `bundled/agnes-image-generation`；`.env` 設 `AGNES_API_KEY` |

### B2. 常見 Office 檔案（**預裝、缺則自動裝**）

| 能力 | 接受技能名 | 優先來源 |
|------|-----------|----------|
| Word | `docx` | Hub trusted `skills-sh/anthropics/skills/docx`；或 `hermes-agent/skills/productivity/docx` |
| Excel | `xlsx` / `spreadsheet` | Hub `skills-sh/anthropics/skills/xlsx` |
| PowerPoint | `pptx` / `powerpoint` | Hub `skills-sh/anthropics/skills/pptx`；或 bundled `powerpoint` |
| PDF | `pdf` / `nano-pdf` | 本機／bundled 複製；或既有 hub `pdf` |

check 四類各至少一個；apply 呼叫 `ensure_office_skills`。


## C. 禁止預裝（通用包）

- 任何客戶個案 skill（client-* 等）、公司內部 skill
- 沒有金鑰就必定失敗、且無免 key 路徑的付費專用包

## 檢查項 ID

- `skills.bundled_ok`
- `skills.preload.hermes_tw_setup`
- `skills.preload.telegram_zh`
- `skills.preload.duckduckgo`
- `skills.no_client_required`（僅提示：偵測到個案 skill 不刪，通用基線不負責）


## B4. 前端程式碼生圖（與 Agnes 互補）

**路線**：HTML／CSS／SVG／Canvas／p5 寫畫面 → Chrome DevTools MCP 截圖成 PNG。  
適合：資訊圖、圖卡、封面、UI 示意、文字要清楚的圖。  
Agnes：寫實／氛圍／插畫感點陣圖。

| 技能 | Hub / 來源 | 用途 |
|------|-----------|------|
| `frontend-design` | `skills-sh/anthropics/skills/frontend-design` | 高質感前端版面 |
| `canvas-design` | `skills-sh/anthropics/skills/canvas-design` | Canvas 視覺構圖 |
| `algorithmic-art` | `skills-sh/anthropics/skills/algorithmic-art` | p5.js 生成藝術 |
| `p5js`（bundled 若有） | Hermes creative | 互動／生成圖 |

check：上述至少 frontend-design + canvas-design 存在（或同名）。  
apply：Hub `--yes` 安裝；失敗則報告。


## B5. Superpowers（工作方法）

- 來源：本機 `~/.hermes/skills/superpowers/`（obra superpowers 技能包：brainstorming、verification-before-completion、using-superpowers 等）
- apply：整包複製到 `$HERMES_HOME/skills/superpowers/`
- 用途：計畫、驗證、少犯錯；社群常提「裝了之後比較少犯錯」
- **不**做 skill 裁剪（一般人太難）；bundled 全留

## B6. 強化記憶（免額外套件費優先）

- 內建 MEMORY.md／USER.md 維持開啟（`memory.memory_enabled: true`）
- 外部 provider 預設開 **holographic**（官方內建、本機 SQLite、免 API key）
  ```yaml
  memory:
    provider: holographic
    memory_enabled: true
  ```
- 進階（不預設強制）：Hindsight／ByteRover／Honcho 等需額外帳號或服務
- check：`memory.provider == holographic`（或已有其他外部 provider 也算強化通過）
