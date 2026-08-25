# Telegram 富訊息（Rich Messages）與表格

台灣 Hermes 基線**主動開通** Bot API 10.1 富訊息，並**關閉 Telegram progressive streaming**，讓表格穩定原生渲染。  
本檔整理：官方預設、怎麼開、開了會踩什麼坑（含 2026-08 實戰）。

---

## 1. 官方預設：rich 關閉（opt-in）

```yaml
telegram:
  extra:
    rich_messages: false   # 或未寫 = 關閉
```

**為什麼預設關：** 部分客戶端不好整段複製成純文字。  
**本基線取捨：** 可讀性與表格優先 → apply 設 `true`。

---

## 2. 基線完整設定（主副都要）

```yaml
telegram:
  extra:
    rich_messages: true
    rich_drafts: false      # 不要開：Desktop／macOS 草稿可能疊影

streaming:
  enabled: false            # 總開關

display:
  language: zh-TW
  platforms:
    telegram:
      streaming: false      # gateway 以這個為準；關了才不會 progressive 拆表
```

### 套用

```bash
python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes
# check 應見：
#   *.telegram.rich_messages = OK
#   *.telegram.streaming_off = OK
```

**必做：重啟所有相關 gateway**（只改 yaml 不夠）。

---

## 3. 為什麼一定要關 streaming（2026-08 血淚）

Hermes v0.20+ 在 `streaming: true` 且 `rich_drafts: false` 時：

1. 先送 **MarkdownV2 預覽**（表格被 `_wrap_markdown_tables` **拆成 bullet**）  
2. 最後才 `editMessageText` 升級 rich  

結果：

| 層 | 看起來像 | 真相 |
|----|----------|------|
| config | rich_messages true | 只代表「允許 rich」 |
| API／rich_sent_index | 有 message_id 紀錄 | **API 接受 ≠ 畫面是格子** |
| 使用者眼睛 | bullet／歪掉／像失敗 | progressive 路徑或 client |

**基線做法：關 streaming → 一次 `sendRichMessage`，不走 interim 拆表。**

關閉 streaming **不影響**工具進度氣泡（「執行程式／搜尋檔案…」那條是另一開關）。

---

## 4. 三層驗證（禁止先斬後奏）

表格「成功」必須三層都過：

1. **設定**：`rich_messages: true` + Telegram `streaming: false`  
2. **API**：Bot 接受 rich（可有 rich_sent 紀錄）  
3. **目視**：使用者確認是**格子表**  

沒有第 3 層前，只能說「設定與 API 層通過，等待確認畫面」。

---

## 5. 寫表規範（表格紅線 2026-08-24 定案）

送出 Telegram 前**逐表自檢**，以下全部是紅線，不是建議：

```markdown
狀態如下

| 項目 | 值 |
|---|---|
| rich | OK |
```

必做：

- **表前必空行**：表格前一行若為文字標題或段落且沒空行，整張不渲染（變直線符號）  
- **表格內禁粗體／斜體標記**：`**`、`*` 不進格子，會破壞原生表格解析  
- **單格文字 ≤ 約 20 字**：超長就拆行、拆表或改點列  
- **欄數 ≤ 4**：超過就拆成多張或換結構  
- **每行以 `|` 開頭**（含表頭、分隔列、資料列）  
- **表頭下必有分隔列 `|---|`**  
- 長文自己分段，避免切在表中間  

適合：排行、對照、狀態、檢查結果（欄少、值短）。  
不適合：超多欄＋每行超長敘事（這種改用點列）。

---

## 6. 其它踩坑

| 坑 | 說明 |
|----|------|
| 未重啟 gateway | 改 yaml 仍走舊 adapter |
| 缺 `\|---` | 不進 rich 表格路徑 |
| 表前没空行 | Markdown 當段落延續 |
| 排程／standalone | 部分路徑無 rich，只有 legacy |
| `rich_drafts: true` | Desktop 疊影風險 |
| 舊 PTB 無 sendRichMessage | capability 失敗後可能 latch 關 rich |
| 誤以為 TG 不能表 | 錯；是沒開 rich／開了 streaming／語法不合法 |

---

## 7. Agent 檢查清單

- [ ] 主副 `rich_messages: true`  
- [ ] 主副 `display.platforms.telegram.streaming: false`（或 `streaming.enabled: false`）  
- [ ] `rich_drafts` 未開  
- [ ] 已重啟 gateway  
- [ ] 表前空行；每行以 `|` 開頭；有 `|---|`  
- [ ] 格內無粗體／斜體標記；單格 ≤ 約 20 字；欄數 ≤ 4  
- [ ] **使用者目視**是格子表  
- [ ] 未只憑 rich_sent_index 宣稱成功  

---

## 8. 與 baseline

| 動作 | 行為 |
|------|------|
| apply | 寫 rich_messages／關 streaming／rich_drafts false |
| check | `*.telegram.rich_messages`、`*.telegram.streaming_off` |
| 本檔 | 原理與踩坑 |
