# Editorial B2B 攝影 Prompt 配方（2026-06-28 實測可用）

## 適用場景

替 aibud.tw 等 B2B 品牌網站產背景圖、Hero 圖、OG 圖。Agnes Image 2.1 Flash 實測。

## 共通 Style 前綴（所有圖都要套）

```
editorial photography, cinematic warm lighting, shallow depth of field,
muted desaturated palette, sophisticated B2B feel,
warm bronze gold, burgundy red, cream ivory, deep ebony shadows,
contemplative mood, quietly confident,
35mm prime lens, photorealistic, ultra detailed,
no people, no logos, no readable text
```

## 色票

| 色名 | Hex | 用途 |
|------|-----|------|
| Warm Bronze Gold | #A6825B | 金屬、暖光、桌面 |
| Burgundy Red | #8C3B2E | 書背、簾幕、強調色 |
| Cream Ivory | #E5D8BD | 書頁、燈光、背景 |
| Deep Ebony | #0F0B09 | 陰影、疊字區 |
| Accent Gold | #C0992B | 羅盤、邊框點綴 |

## 5 張圖的 Prompt 結構

### 圖 1：書房書架（blog 背景）

```
{共通前綴},
a quiet dimly lit private study at dusk, antique wooden bookshelf
filling the right two-thirds of frame, weathered leather-bound books
in deep burgundy bronze gold and cream tones,
warm tungsten reading lamp glow from upper-left casting long soft shadows,
a single open hardback book on desk lower foreground slightly out of focus,
aged paper texture, left third of frame darker and empty for text overlay
```

### 圖 2：活動講堂（events 背景）

```
{共通前綴},
an empty intimate lecture hall just before an event begins,
staggered rows of modern wooden chairs facing a softly lit stage
on the right side of frame,
a single warm amber spotlight pools on the stage center,
rest of room in deep ebony shadow,
subtle haze in the air catching the light beam, wooden panel walls,
left half of frame darker for text overlay
```

### 圖 3：工作空間（careers 背景）

```
{共通前綴},
a modern boutique consulting workspace at golden hour,
a long wooden communal table on the right side of frame with
open notebooks two minimal laptops screens off,
one ceramic coffee cup a small bronze desk lamp,
a large arched window in background letting in soft amber late-day light
casting long warm shadows, hardwood floor exposed brick wall,
potted olive plant, left third of frame darker empty wall for text overlay
```

### 圖 4：Hero 圖（品牌哲學）

```
{共通前綴},
a symbolic still-life composition representing ethical leadership,
center an old-world brass compass with ornate engravings
on weathered ivory parchment,
blurred warm-lit bookshelves and antique brass desk lamp
casting golden light from upper-right,
foreground an open fountain pen and folded silk ribbon in burgundy,
subtle dust motes catching light, East-Asian scholarly restraint,
deep shadow edges
```

### 圖 5：OG 分享卡

```
{共通前綴},
a wide cinematic banner for social media preview card,
left half warm-lit study aesthetic with bookshelf hints and
brass lamp glow and soft bokeh in burgundy tones,
right half deep ebony void with a single subtle gold compass-rose motif
faintly etched into the darkness,
designed for text overlay,
New York Times opinion piece banner aesthetic
```

## 尺寸對照表

| 要求尺寸 | Agnes 實際產出 | 比例 | 適用 |
|----------|---------------|------|------|
| 1600×900 | ~1312×736 | 16:9 | 網站背景 |
| 1200×900 | ~1152×864 | 4:3 | Hero 圖 |
| 1200×628 | ~1312×736 | 16:9（非精確 1.91:1） | OG 圖 |

Agnes 的 size 參數不精確匹配，但 aspect ratio 接近。web 用 CSS `object-fit: cover` 解決。

## 輸出後處理

- 預設 PNG ~1.3MB → 轉 JPEG quality 85 可壓到 150-300KB
- 解析度若不足（1312×736 for 2x retina），上傳後 CSS cover 即可，不需要重生成
