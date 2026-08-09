# 2026/6 免費 AI 生圖 API 全景

> 研究日期: 2026-06-24 | 來源: LaoZhang AI Blog, Pixazo, Reddit, DataCamp, 各平台官方文件

## 核心結論

**主流封閉平台已無真正免費 API tier**。OpenAI GPT Image 全線付費，Google 舊 preview 路徑 2025/11 關閉。多數「免費 API」文章資訊過時。

## 真正零成本方案（2026/6）

| 平台 | 費用 | 模型 | 限制 | 適合 |
|------|------|------|------|------|
| **Agnes AI** | 完全免費 | Image 2.0/2.1 Flash + Video | 未知（新平台） | 🥇 主力 |
| **Cloudflare Workers AI** | 10k neurons/天 | SDXL Lightning | ~20-30 張/天 | 🥈 備援 |
| **Pollinations.ai** | 免費註冊 | Flux / GPT Image / Seedream | 需 API key | 🥉 備援 |
| **Puter.js** | 開發者零成本 | GPT Image / Flux / SD / Nano Banana | 純前端 JS | 嵌入產品 |

## 試用型（非長期方案）

| 平台 | 額度 | 備註 |
|------|------|------|
| Leonardo AI | $5 一次性 | 新帳號 credit，用完即止 |
| Hugging Face | 極小月額 | 僅夠 smoke test |
| Replicate | 模型特定 | playground 模式，非穩定 tier |
| Pixazo | 免費 tier | 商業聚合器，600+ 模型 |

## 已過時/不可用的「免費」資訊

- **Google Gemini Image API** — 舊 preview 路徑 2025/11/14 關閉。現有 pricing 頁顯示 "Free Tier: Not available"（Gemini 3 Pro Image Preview、Imagen 4）
- **OpenAI GPT Image** — 全線顯示 "Free: Not supported"
- **Gemini app 消費端** — 有 20 張/天免費，但這是 consumer app 不是 API

## 選用決策

我們選擇 **Agnes AI 當主力** 的原因：
1. 真正免費、免信用卡
2. REST API，OpenAI 相容格式
3. 新加坡節點（對台灣延遲低）
4. 多模態（文字+圖片+影片）
5. 2026/6/1 剛宣布免費開放，無已知額度限制

風險：新平台，穩定度待驗證。備援方案：Cloudflare Workers AI（我們已有 CF 帳號）。
