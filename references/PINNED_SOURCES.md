# 釘死的第三方來源

apply 不抓「當下最新」。下列值與 `scripts/baseline.py` 常數同步；改一處就要改另一處。

| 來源 | 釘法 | 值（2026-08-25） |
|------|------|------------------|
| PyYAML | pip 版本範圍 | `PyYAML>=6.0.1,<7` |
| Chrome DevTools MCP | npm 精確版本 | `chrome-devtools-mcp@1.7.0` |
| Superpowers | git tag + 提交 | `v4.1.1` / `469a6d81ebb8b827e284d4afb090c6c622d97747` |
| Office／前端技能 | `anthropics/skills` 提交 | `3b3fad96af16a10759d930941b4520ba0c40edae` |

升級釘版：先核對上游發行與變更，改本表與 `baseline.py` 常數，再跑隔離測試。

不要：

- `git clone` 預設分支頭
- `npx …@latest`
- `hermes skills install … --yes` 當未釘來源的後門
