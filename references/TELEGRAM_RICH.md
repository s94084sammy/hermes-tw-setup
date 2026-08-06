# Telegram 富訊息（Rich Messages）與表格

台灣 Hermes 基線**主動開通** Bot API 10.1 富訊息，讓表格等結構能原生渲染。  
本檔整理：**官方預設為何關、怎麼開、開了會踩什麼坑**（依 Hermes 閘道行為與實務）。

---

## 1. 官方預設：關閉（opt-in）

Hermes 預設：

```yaml
# config_defaults：rich_messages: false
telegram:
  extra:
    rich_messages: false   # 或未寫 = 關閉
```

**為什麼預設關（官方理由）：**

- 富訊息在部分 Telegram 客戶端**不好整段複製成純文字**（指令片段、轉貼手感差）
- 故上游採 **opt-in**：要格子表／任務清單原生渲染才打開

本基線取捨：**可讀性與表格優先** → apply 設 `true`。若你大量貼指令、在意複製純文字，可自行改回 `false`。

---

## 2. 怎麼打開

### 2a 用本技能（建議）

```bash
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes
# check 應見：Telegram 富訊息 rich_messages = OK
```

### 2b 手動寫 config（主副 profile 都要）

**路徑 A（本基線／常見部署）：**

```yaml
telegram:
  extra:
    rich_messages: true
    # rich_drafts: false   # 建議維持 false（見下方坑）
```

**路徑 B（官方文件寫法，部分版本）：**

```yaml
gateway:
  platforms:
    telegram:
      extra:
        rich_messages: true
        rich_drafts: false
```

`baseline.py` 以 **路徑 A** 為準寫入；check 會認 `telegram.extra` 或 `gateway.platforms.telegram.extra`。

### 2c 必做：重啟 gateway

只改 yaml **不夠**，adapter 在啟動時讀設定：

```bash
# 依實際服務名
systemctl --user restart hermes-gateway
# 副 profile 若獨立 unit，一併重啟
# 或：hermes gateway 重開／hermes -p side gateway
```

### 2d 驗證是否真的開到

1. 對 bot 丟一則**合法** pipe table（含 `|---|`、表前空行）  
2. 應看到 **格子表**，不是 bullet「• 欄: 值」群  
3. check：

```bash
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py check
# default.telegram.rich_messages / side.… 應 OK
```

---

## 3. 開了之後會怎樣（行為）

| 情況 | 行為 |
|------|------|
| 內容含可被偵測的表／任務清單等 | 走 `sendRichMessage`（raw markdown） |
| 普通散文、粗體、簡單清單 | 多半仍 MarkdownV2（字重／間距較一致） |
| rich 被拒、過長、舊 ptb 無 API | **自動 fallback** legacy，訊息不應整則消失 |
| 網路短暫失敗 | 不應靜默重送成重複兩則 |

Legacy 下表格會被拆成 **row-group bullet** 或 **code block 對齊**，看起來「不像表」——常被誤判成「Telegram 不能表格」。其實是 **沒開 rich 或沒走 rich 路徑**。

---

## 4. 實務踩坑（必寫進技能）

### 坑 1：以為開了，其實沒重啟

改 config 後 gateway 未重啟 → 仍 legacy。先重啟再測表。

### 坑 2：表「語法不合法」→ 根本不進 rich

必須同時滿足：

- 有 **分隔列** `|---|`（或 `|------|`）  
- 列是 pipe 列  

缺分隔列 → 不觸發 rich 表格路徑；使用者只看到一堆 `|` 或 bullet。

### 坑 3：表格前沒空一行（最常中）

上一行是正文、中間沒空行 → Markdown 把表當段落延續，**整表爛成直線符號**。

```text
錯：
狀態如下
| 項目 | 值 |
|---|---|

對：
狀態如下

| 項目 | 值 |
|---|---|
```

自檢：每個以 `|` 開頭的資料列，前一行必須是**空行**或**表格列**。

### 坑 4：對話像表、排程／standalone 不像表

- **對話**：走 adapter `send` → 可 rich  
- **部分排程／standalone 投遞**：若落到無 rich 的發送路徑 → 只有 legacy  

除錯：看日誌是 live adapter 還是 standalone；同內容在對話測一次對照。

### 坑 5：內容太長

Rich 上限約 **32768** 字元；一般 TG 一則也常被切。長報告自己分段，避免切在表中間。

### 坑 6：`rich_drafts` 不要亂開

`rich_drafts: true` 是串流草稿實驗路徑；Desktop／macOS 可能**畫面疊影**直到重繪。基線建議 **維持 false**（只開 `rich_messages` 即可）。

### 坑 7：複製貼上變差

開 rich 後，部分客戶端複製表格／訊息不如純 MarkdownV2 好用。這是官方預設關閉的主因。需要時可對「指令密集」bot 關 rich，對「報告／表格」bot 開 rich。

### 坑 8：舊 python-telegram-bot 沒有 sendRichMessage

能力失敗後閘道可能 **latch 關閉** rich 嘗試。需升級 Hermes／依賴並重啟。日誌會有 rich capability 相關訊息。

### 坑 9：誤以為「TG 永遠不能表」

錯誤結論。正確是：

1. 設 `rich_messages: true` + 重啟  
2. 輸出合法 GFM 表  
3. 確認走 live adapter  

仍非格子 → 查 fallback 原因（過長、API 拒、路徑 standalone）。

### 坑 10：主副 profile 只開一邊

副助理獨立 config 時兩邊都要 `rich_messages: true`，並重啟對應 gateway。

---

## 5. 寫表規範（表格優先）

結構化、欄位固定 → **優先 pipe table**，少用難掃長點列。

```markdown
| 項目 | 狀態 | 備註 |
|------|------|------|
| rich_messages | OK | 已重啟 gateway |
| 表前空行 | OK | 必做 |
```

適合：排行、對照、狀態、檢查結果、參數摘要。  
不適合：超多欄＋每行超長敘事 → 改短段落／行格式。

禁止：只交 HTML `<table>` 當唯一手段；無分隔列的假表。

---

## 6. Agent 檢查清單

- [ ] config 已 `rich_messages: true`（主副）  
- [ ] 已重啟相關 gateway  
- [ ] 輸出含 `|---|` 且**表前空行**  
- [ ] 對話實測是格子表  
- [ ] 長文已分段  
- [ ] 未誤開 `rich_drafts`（除非自知風險）  
- [ ] 交付文字報告仍遵守「表格優先」；檔案另走純視覺 QA（見 DELIVERY_QA.md）  

---

## 7. 與 baseline 腳本

| 動作 | 行為 |
|------|------|
| apply | 寫入 `telegram.extra.rich_messages: true`；SOUL／MEMORY 提醒表格優先 |
| check | `*.telegram.rich_messages` 未開則 NO 並印修復指令 |
| 本檔 | 開通步驟 + 開後坑點（給 agent／使用者） |
