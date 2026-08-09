# Agnes Image API 完整規格

> 來源: https://agnes-ai.com/doc/agnes-image-21-flash（2026-06-24 擷取）

## 基本資訊

- **Base URL**: `https://apihub.agnes-ai.com`
- **Endpoint**: `POST /v1/images/generations`
- **認證**: `Authorization: Bearer YOUR_API_KEY`
- **Content-Type**: `application/json`

## 模型

| 模型 | 說明 |
|------|------|
| `agnes-image-2.1-flash` | 最新，高資訊密度圖像優化 |
| `agnes-image-2.0` | 穩定版，Elo 1178（AA 排行榜） |

## 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `model` | string | ✅ | 模型名稱 |
| `prompt` | string | ✅ | 提示詞 |
| `size` | string | ✅ | 輸出尺寸，如 `1024x768` |
| `image` | string[] | img2img 必填 | 輸入圖片 URL 或 Data URI |
| `return_base64` | boolean | 否 | txt2img 回傳 Base64 時設 true |
| `extra_body` | object | 否 | 進階參數 |
| `extra_body.response_format` | string | 否 | `url` 或 `b64_json` |
| `extra_body.image` | string[] | 否 | img2img 輸入圖片（放 extra_body 內） |

## txt2img — URL 輸出

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "A floating city above a canyon at sunrise",
    "size": "1024x768",
    "extra_body": {"response_format": "url"}
  }'
```

回傳: `data[0].url`

## txt2img — Base64 輸出

```bash
curl ... -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "...",
    "size": "1024x768",
    "return_base64": true
  }'
```

回傳: `data[0].b64_json`

## img2img — URL 輸入，URL 輸出

```bash
curl ... -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "Transform to cyberpunk night with neon",
    "size": "1024x768",
    "extra_body": {
      "image": ["https://example.com/input.png"],
      "response_format": "url"
    }
  }'
```

## img2img — Data URI Base64 輸入

```bash
curl ... -d '{
    "model": "agnes-image-2.1-flash",
    "prompt": "Make it matte black",
    "size": "1024x768",
    "extra_body": {
      "image": ["data:image/png;base64,BASE64_HERE"],
      "response_format": "b64_json"
    }
  }'
```

## 回傳格式

### URL 輸出
```json
{
  "created": 1780000000,
  "data": [{"url": "https://storage.googleapis.com/agnes-aigc/xxx.png"}]
}
```

### Base64 輸出
```json
{
  "created": 1780000000,
  "data": [{"b64_json": "iVBORw0KGgo..."}]
}
```

## 踩坑

1. **response_format 必須放 extra_body**，放頂層 → 400
2. **image 參數位置**: txt2img 不放任何 image；img2img 的 image 放 extra_body 內
3. **不要傳 tags: ["img2img"]** — 不需此參數
4. **API base URL 是 apihub.agnes-ai.com**，不是 platform.agnes-ai.com（platform 是管理後台）
