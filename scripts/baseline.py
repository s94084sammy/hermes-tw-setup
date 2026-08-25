#!/usr/bin/env python3
"""hermes-tw-setup — check / apply Taiwan Hermes baseline.

Usage:
  python3 baseline.py check
  python3 baseline.py apply [--yes]

Does not print secret values. apply makes safe, idempotent fixes; host power
policy and OAuth still need explicit user action where noted.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()
SIDE_NAME = "side"
SIDE_HOME = HERMES_HOME / "profiles" / SIDE_NAME
DOCKER_CONTAINER = os.environ.get("HERMES_TW_DOCKER", "").strip()
SKILL_ROOT = Path(__file__).resolve().parent.parent
REF = SKILL_ROOT / "references"
OPENROUTER_HERMES_APP = "https://openrouter.ai/apps/hermes-agent"
VOICE_CHOICES = {
    "female": "zh-TW-HsiaoChenNeural",
    "male": "zh-TW-YunJheNeural",
}

# Pinned third-party sources. Do not float to latest. Keep in sync with
# references/PINNED_SOURCES.md
PYYAML_SPEC = "PyYAML>=6.0.1,<7"
CHROME_DEVTOOLS_MCP = "chrome-devtools-mcp@1.7.0"
SUPERPOWERS_REPO = "https://github.com/obra/superpowers.git"
SUPERPOWERS_TAG = "v4.1.1"
SUPERPOWERS_REF = "469a6d81ebb8b827e284d4afb090c6c622d97747"
ANTHROPICS_SKILLS_REPO = "https://github.com/anthropics/skills.git"
ANTHROPICS_SKILLS_REF = "3b3fad96af16a10759d930941b4520ba0c40edae"

_ANTHROPICS_TREE: Optional[Path] = None


def live_home() -> Path:
    return (Path.home() / ".hermes").expanduser().resolve()


def isolated() -> bool:
    """True when the target home is not the live ~/.hermes, or Docker mode."""
    try:
        return HERMES_HOME.expanduser().resolve() != live_home() or bool(DOCKER_CONTAINER)
    except Exception:
        return True


def bind_env(extra: Optional[dict[str, str]] = None) -> dict[str, str]:
    env = {**os.environ, "HERMES_HOME": str(HERMES_HOME)}
    if isolated():
        env["HERMES_TW_ISOLATED"] = "1"
    if extra:
        env.update(extra)
    return env


def under_target_home(path: Path) -> bool:
    try:
        path.expanduser().resolve().relative_to(HERMES_HOME.expanduser().resolve())
        return True
    except Exception:
        return False


def safe_copytree(src: Path, dst: Path) -> None:
    """Copy a tree; skip symlinks that point outside src (zip-slip / clone tricks)."""
    src = src.resolve()

    def ignore(directory: str, names: list[str]) -> list[str]:
        skip: list[str] = []
        d = Path(directory)
        for n in names:
            p = d / n
            if not p.is_symlink():
                continue
            try:
                p.resolve().relative_to(src)
            except Exception:
                skip.append(n)
        return skip

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=False, ignore=ignore)


def git_clone_pinned(url: str, dest: Path, *, ref: str, tag: str = "") -> subprocess.CompletedProcess:
    """Clone a repo at a pinned tag/SHA. Refuse to proceed on mismatch."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if tag:
        r = subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", tag, url, str(dest)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if r.returncode == 0:
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=dest,
                capture_output=True,
                text=True,
                timeout=15,
            )
            got = (head.stdout or "").strip()
            if got == ref or got.startswith(ref) or ref.startswith(got):
                return r
            shutil.rmtree(dest, ignore_errors=True)
            r = subprocess.CompletedProcess(
                r.args,
                1,
                r.stdout,
                (r.stderr or "") + f"\nPIN_MISMATCH expected={ref} got={got}",
            )
            return r
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=dest, capture_output=True, text=True, timeout=30)
    subprocess.run(
        ["git", "remote", "add", "origin", url],
        cwd=dest,
        capture_output=True,
        text=True,
        timeout=30,
    )
    r = subprocess.run(
        ["git", "fetch", "--depth", "1", "origin", ref],
        cwd=dest,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if r.returncode != 0:
        return r
    return subprocess.run(
        ["git", "checkout", "--force", "FETCH_HEAD"],
        cwd=dest,
        capture_output=True,
        text=True,
        timeout=30,
    )


def anthropics_skills_tree() -> Optional[Path]:
    global _ANTHROPICS_TREE
    if _ANTHROPICS_TREE and (_ANTHROPICS_TREE / "skills").is_dir():
        return _ANTHROPICS_TREE
    dest = Path(f"/tmp/hermes-tw-anthropics-skills-{ANTHROPICS_SKILLS_REF[:12]}")
    marker = dest / ".hermes-tw-pin"
    if dest.is_dir() and (dest / "skills").is_dir() and marker.exists() and marker.read_text().strip() == ANTHROPICS_SKILLS_REF:
        _ANTHROPICS_TREE = dest
        return dest
    r = git_clone_pinned(ANTHROPICS_SKILLS_REPO, dest, ref=ANTHROPICS_SKILLS_REF)
    if r.returncode != 0:
        return None
    if not (dest / "skills").is_dir():
        return None
    marker.write_text(ANTHROPICS_SKILLS_REF, encoding="utf-8")
    _ANTHROPICS_TREE = dest
    return dest


def install_pinned_anthropic_skill(home: Path, folder_name: str) -> str:
    tree = anthropics_skills_tree()
    if not tree:
        return (
            f"釘版 anthropics/skills@{ANTHROPICS_SKILLS_REF[:12]} 取得失敗；"
            f"不回落到未釘版本的 Hub"
        )
    src = tree / "skills" / folder_name
    if not (src / "SKILL.md").is_file():
        return f"釘版樹沒有 skills/{folder_name}/SKILL.md"
    dst = skills_dir_for_home(home) / folder_name
    skills_dir_for_home(home).mkdir(parents=True, exist_ok=True)
    safe_copytree(src, dst)
    return f"已安裝 {folder_name} ← anthropics/skills@{ANTHROPICS_SKILLS_REF[:12]}"


@dataclass
class Item:
    id: str
    title: str
    ok: bool
    detail: str = ""
    fixable: bool = False
    level: str = "info"  # info | warn | fail
    fix_hint: str = ""  # 給使用者／agent 的具體指令（未過時印出）


@dataclass
class Report:
    items: list[Item] = field(default_factory=list)

    def add(self, item: Item) -> None:
        self.items.append(item)

    def ok_count(self) -> int:
        return sum(1 for i in self.items if i.ok)

    def fail_count(self) -> int:
        return sum(1 for i in self.items if not i.ok)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if yaml is None:
        raise SystemExit(f"需要 PyYAML：pip install '{PYYAML_SPEC}'")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {}
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    if yaml is None:
        raise SystemExit(f"需要 PyYAML：pip install '{PYYAML_SPEC}'")
    path.parent.mkdir(parents=True, exist_ok=True)
    # preserve nothing fancy; dump unicode
    text = yaml.safe_dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    path.write_text(text, encoding="utf-8")


def env_has_key(env_path: Path, key: str) -> bool:
    if not env_path.exists():
        return False
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == key and v.strip().strip("\"'"):
            return True
    return False


def env_get(env_path: Path, key: str) -> str:
    if not env_path.exists():
        return ""
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == key:
            return v.strip().strip("\"'")
    return ""


def detect_os() -> str:
    s = platform.system().lower()
    if s == "darwin":
        return "macos"
    if s == "windows" or s.startswith("win"):
        return "windows"
    return "linux"


def cdp_up(port: int = 9222) -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5)
        return True
    except Exception:
        return False


def systemd_user_active(unit: str) -> Optional[bool]:
    if detect_os() != "linux":
        return None
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-active", unit],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return r.returncode == 0 and r.stdout.strip() == "active"
    except Exception:
        return None


def systemd_user_enabled(unit: str) -> Optional[bool]:
    if detect_os() != "linux":
        return None
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-enabled", unit],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return r.returncode == 0 and "enabled" in r.stdout.strip()
    except Exception:
        return None


def docker_exec(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    if not DOCKER_CONTAINER:
        raise RuntimeError("DOCKER_CONTAINER not set")
    return subprocess.run(
        ["docker", "exec", DOCKER_CONTAINER, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def anysearch_provider_allows_anonymous() -> Optional[bool]:
    if DOCKER_CONTAINER:
        try:
            r = docker_exec(
                ["sh", "-c", "cat /opt/hermes/plugins/web/anysearch/provider.py 2>/dev/null || cat /opt/hermes/hermes-agent/plugins/web/anysearch/provider.py 2>/dev/null"],
                timeout=15,
            )
            if r.returncode != 0 or not (r.stdout or "").strip():
                return None
            text = r.stdout
        except Exception:
            return None
    else:
        prov = HERMES_HOME / "hermes-agent" / "plugins" / "web" / "anysearch" / "provider.py"
        if not prov.exists():
            return None
        text = prov.read_text(encoding="utf-8", errors="replace")
    if "HERMES_TW_ANONYMOUS_ANYSEARCH" in text:
        return True
    if "return bool(os.getenv(\"ANYSEARCH_API_KEY\"" in text or "return bool(os.getenv('ANYSEARCH_API_KEY'" in text:
        return False
    if "ANYSEARCH_API_KEY environment variable not set" in text:
        return False
    return True


def commands_py_has_zh() -> Optional[bool]:
    if DOCKER_CONTAINER:
        try:
            r = docker_exec(
                ["sh", "-c", "grep -E '開始新對話|清除螢幕' /opt/hermes/hermes_cli/commands.py 2>/dev/null | head -3"],
                timeout=15,
            )
            if r.returncode != 0:
                return None
            return bool((r.stdout or "").strip())
        except Exception:
            return None
    p = HERMES_HOME / "hermes-agent" / "hermes_cli" / "commands.py"
    if not p.exists():
        return None
    t = p.read_text(encoding="utf-8", errors="replace")
    return "開始新對話" in t or "清除螢幕" in t



def soul_has_core(path: Path) -> bool:
    if not path.exists():
        return False
    t = path.read_text(encoding="utf-8", errors="replace")
    markers = ["不輕易拒絕", "不預設", "先查再做", "不過度審查"]
    return sum(1 for m in markers if m in t) >= 2


def memory_has_snippet(path: Path) -> bool:
    if not path.exists():
        return False
    t = path.read_text(encoding="utf-8", errors="replace")
    return "hermes-tw" in t or "雙助理" in t or "openrouter.ai/apps/hermes-agent" in t


def check_linux_sleep() -> Item:
    # best-effort: logind or systemd targets
    detail_parts = []
    ok = True
    for unit in ("sleep.target", "suspend.target", "hibernate.target"):
        try:
            r = subprocess.run(
                ["systemctl", "is-enabled", unit],
                capture_output=True,
                text=True,
                timeout=5,
            )
            state = (r.stdout or r.stderr or "").strip()
            detail_parts.append(f"{unit}={state or 'unknown'}")
            # static / masked / disabled are OK for "no sleep"
            if state in ("enabled", "alias"):
                ok = False
        except Exception as e:
            detail_parts.append(f"{unit}=err")
    return Item(
        id="host.sleep",
        title="禁休眠（Linux 檢查）",
        ok=ok,
        detail="; ".join(detail_parts) + "（可關螢幕；系統不應自動 suspend）",
        fixable=True,
        level="warn" if not ok else "info",
    )


def check_profile(label: str, home: Path, is_side: bool) -> list[Item]:
    items: list[Item] = []
    cfg_path = home / "config.yaml"
    env_path = home / ".env"
    cfg = load_yaml(cfg_path) if cfg_path.exists() else {}

    items.append(
        Item(
            id=f"{label}.exists",
            title=f"{label} profile 目錄",
            ok=home.exists() and cfg_path.exists(),
            detail=str(home),
            fixable=is_side,
        )
    )
    if not cfg_path.exists():
        return items

    tz = cfg.get("timezone") or ""
    items.append(
        Item(
            id=f"{label}.timezone",
            title=f"{label} 時區 Asia/Taipei",
            ok=str(tz) == "Asia/Taipei",
            detail=f"目前={tz!r}",
            fixable=True,
        )
    )

    lang = (cfg.get("display") or {}).get("language") if isinstance(cfg.get("display"), dict) else None
    items.append(
        Item(
            id=f"{label}.language",
            title=f"{label} display.language zh-TW",
            ok=str(lang) in ("zh-TW", "zh-Hant", "zh-hant"),
            detail=f"目前={lang!r}",
            fixable=True,
        )
    )

    web = cfg.get("web") or {}
    sb = web.get("search_backend") or web.get("backend") or ""
    eb = web.get("extract_backend") or web.get("backend") or ""
    items.append(
        Item(
            id=f"{label}.search",
            title=f"{label} 搜尋 anysearch",
            ok=str(sb) == "anysearch" and (not eb or str(eb) == "anysearch"),
            detail=f"search={sb!r} extract={eb!r}",
            fixable=True,
        )
    )

    ext = (cfg.get("skills") or {}).get("external_dirs") if isinstance(cfg.get("skills"), dict) else None
    if is_side:
        ok_ext = False
        if isinstance(ext, list):
            allowed = {
                str(HERMES_HOME / "skills").rstrip("/"),
                "/opt/data/skills",
            }
            if not isolated():
                allowed.add("~/.hermes/skills")
                allowed.add(str(live_home() / "skills").rstrip("/"))
            for e in ext:
                es = str(e).replace(chr(92), "/").rstrip("/")
                if es in allowed or es.endswith("/.hermes/skills") or es.endswith("/opt/data/skills"):
                    ok_ext = True
        items.append(
            Item(
                id=f"{label}.skills_share",
                title=f"{label} 技能庫指向 default skills",
                ok=ok_ext,
                detail=f"external_dirs={ext!r}",
                fixable=True,
            )
        )
    else:
        items.append(
            Item(
                id=f"{label}.skills_home",
                title=f"{label} 技能本體目錄存在",
                ok=(home / "skills").is_dir(),
                detail=str(home / "skills"),
                fixable=False,
            )
        )

    fb = cfg.get("fallback_providers") or []
    has_or = isinstance(fb, list) and any(
        isinstance(x, dict) and str(x.get("provider")) == "openrouter" for x in fb
    )
    items.append(
        Item(
            id=f"{label}.openrouter_fallback",
            title=f"{label} OpenRouter fallback",
            ok=has_or and env_has_key(env_path, "OPENROUTER_API_KEY"),
            detail=(
                f"fallback_entries={len(fb) if isinstance(fb, list) else 0}; "
                f"key={'有' if env_has_key(env_path, 'OPENROUTER_API_KEY') else '無'}；"
                "缺則 agent 用已登入 Chrome（CDP）自取 key，見 API_KEYS_BROWSER.md"
            ),
            fixable=False,
            level="warn",
        )
    )

    has_tok = env_has_key(env_path, "TELEGRAM_BOT_TOKEN") or env_has_key(
        env_path, "TELEGRAM_BOT_TOKEN_DEFAULT"
    )
    items.append(
        Item(
            id=f"{label}.telegram_token",
            title=f"{label} Telegram bot token",
            ok=has_tok,
            detail="已設定" if has_tok else "未設定",
            fixable=False,
            level="warn",
        )
    )
    has_allow = env_has_key(env_path, "TELEGRAM_ALLOWED_USERS") or env_has_key(
        env_path, "TELEGRAM_ALLOWLIST"
    )
    items.append(
        Item(
            id=f"{label}.telegram_allowlist",
            title=f"{label} Telegram 允許清單或配對碼",
            ok=has_allow or not has_tok,
            detail=(
                "已設 TELEGRAM_ALLOWED_USERS"
                if has_allow
                else "未設允許清單；上游預設拒絕未知使用者並走配對碼，請確認你懂這層，不要以為有 token 就全開"
            ),
            fixable=False,
            level="warn",
        )
    )

    items.append(
        Item(
            id=f"{label}.soul",
            title=f"{label} SOUL 核心行為",
            ok=soul_has_core(home / "SOUL.md"),
            detail=str(home / "SOUL.md"),
            fixable=True,
        )
    )
    items.append(
        Item(
            id=f"{label}.memory",
            title=f"{label} MEMORY 基線短句",
            ok=memory_has_snippet(home / "memories" / "MEMORY.md"),
            detail=str(home / "memories" / "MEMORY.md"),
            fixable=True,
        )
    )

    mcp = cfg.get("mcp_servers") or {}
    has_cdp_mcp = False
    if isinstance(mcp, dict):
        for k, v in mcp.items():
            kl = str(k).lower()
            if "chrome" in kl or "devtools" in kl:
                has_cdp_mcp = True
            if isinstance(v, dict) and "chrome-devtools" in str(v).lower():
                has_cdp_mcp = True
    items.append(
        Item(
            id=f"{label}.chrome_mcp",
            title=f"{label} Chrome DevTools MCP 設定",
            ok=has_cdp_mcp,
            detail=f"mcp keys={list(mcp.keys()) if isinstance(mcp, dict) else []}",
            fixable=True,
            level="warn" if not has_cdp_mcp else "info",
        )
    )

    return items


def skills_dir_for_home(home: Path) -> Path:
    return home / "skills"


def skill_present(skills_root: Path, name: str) -> bool:
    p = skills_root / name
    return p.is_dir() and ((p / "SKILL.md").exists() or any(p.rglob("SKILL.md")))


def host_skill_source(name: str) -> Optional[Path]:
    """Locate a skill **shipped with this package** (no developer-machine skill library).

    Priority:
    1. ``hermes-tw-setup/bundled/<name>`` (released on GitHub with the skill)
    2. This package root when ``name == hermes-tw-setup``

    Other skills (Office / frontend / Superpowers) use **network** installs
    (Hermes Hub / git clone), not ``~/.hermes/skills`` on the author machine.
    """
    candidates = [
        SKILL_ROOT / "bundled" / name,
        SKILL_ROOT / "bundled" / "media" / name,
        SKILL_ROOT if name == "hermes-tw-setup" else None,
    ]
    for c in candidates:
        if c and c.is_dir() and (c / "SKILL.md").exists():
            return c
    return None


def copy_skill_into(home: Path, name: str) -> str:
    src = host_skill_source(name)
    if not src:
        return f"找不到來源 skill：{name}"
    dst = skills_dir_for_home(home) / name
    skills_dir_for_home(home).mkdir(parents=True, exist_ok=True)
    safe_copytree(src, dst)
    return f"已安裝／更新 {name} → {dst}"


def ensure_duckduckgo(home: Path) -> list[str]:
    notes: list[str] = []
    if skill_present(skills_dir_for_home(home), "duckduckgo-search"):
        notes.append("duckduckgo-search 已存在")
        return notes
    if DOCKER_CONTAINER:
        try:
            r = docker_exec(
                ["hermes", "skills", "repair-official", "duckduckgo-search", "--restore", "--yes"],
                timeout=120,
            )
            notes.append(f"repair-official duckduckgo-search → {r.returncode}")
            out = ((r.stdout or "") + (r.stderr or "")).strip()
            if out:
                notes.append(out[:500])
        except Exception as e:
            notes.append(f"duckduckgo 安裝失敗：{e}")
        return notes
    hermes = shutil.which("hermes")
    if not hermes:
        notes.append("無 hermes 指令，略過 duckduckgo-search")
        return notes
    try:
        r = subprocess.run(
            [hermes, "skills", "repair-official", "duckduckgo-search", "--restore", "--yes"],
            capture_output=True,
            text=True,
            timeout=120,
            env=bind_env(),
        )
        notes.append(f"repair-official duckduckgo-search → {r.returncode}")
        if (r.stdout or r.stderr):
            notes.append(((r.stdout or "") + (r.stderr or "")).strip()[:500])
    except Exception as e:
        notes.append(str(e))
    return notes


def check_preload_and_voice(home: Path, label: str = "default") -> list[Item]:
    items: list[Item] = []
    skills_root = skills_dir_for_home(home)
    no_bundled = (home / ".no-bundled-skills").exists()
    items.append(
        Item(
            id=f"{label}.skills.bundled_ok",
            title=f"{label} 未 opt-out bundled 技能",
            ok=not no_bundled,
            detail="存在 .no-bundled-skills" if no_bundled else "OK",
            fixable=False,
            level="warn" if no_bundled else "info",
        )
    )
    items.append(
        Item(
            id=f"{label}.skills.preload.hermes_tw_setup",
            title=f"{label} 預裝 hermes-tw-setup",
            ok=skill_present(skills_root, "hermes-tw-setup"),
            detail=str(skills_root / "hermes-tw-setup"),
            fixable=True,
        )
    )
    items.append(
        Item(
            id=f"{label}.skills.preload.telegram_zh",
            title=f"{label} 預裝 telegram-commands-zh",
            ok=skill_present(skills_root, "telegram-commands-zh"),
            detail=str(skills_root / "telegram-commands-zh"),
            fixable=True,
        )
    )
    ddg_ok = False
    if skills_root.is_dir():
        ddg_ok = skill_present(skills_root, "duckduckgo-search") or any(
            p.name == "SKILL.md" and p.parent.name == "duckduckgo-search"
            for p in skills_root.rglob("SKILL.md")
        )
    items.append(
        Item(
            id=f"{label}.skills.preload.duckduckgo",
            title=f"{label} 預裝 duckduckgo-search（免 API 備援）",
            ok=ddg_ok,
            detail="optional official skill",
            fixable=True,
            level="warn",
        )
    )
    # client skills warning only
    clientish = []
    if skills_root.is_dir():
        for p in skills_root.iterdir():
            n = p.name.lower()
            if n.startswith(("client-", "customer-")) or "客戶" in n:
                clientish.append(p.name)
    items.append(
        Item(
            id=f"{label}.skills.client_detected",
            title=f"{label} 個案 skill 偵測（不自動刪）",
            ok=True,
            detail=("發現：" + ", ".join(clientish[:12])) if clientish else "無常見個案前綴",
        )
    )

    cfg = load_yaml(home / "config.yaml") if (home / "config.yaml").exists() else {}
    tts = cfg.get("tts") or {}
    edge = (tts.get("edge") or {}) if isinstance(tts, dict) else {}
    voice = str(edge.get("voice") or "") if isinstance(edge, dict) else ""
    tw_voice = voice.startswith("zh-TW-")
    items.append(
        Item(
            id=f"{label}.tts.zh_tw",
            title=f"{label} TTS 台灣語音",
            ok=tw_voice,
            detail=f"voice={voice!r}（建議 zh-TW-HsiaoChenNeural 或 YunJheNeural）",
            fixable=True,
            level="warn" if not tw_voice else "info",
        )
    )
    stt = cfg.get("stt") or {}
    local = (stt.get("local") or {}) if isinstance(stt, dict) else {}
    stt_lang = str(local.get("language") or "") if isinstance(local, dict) else ""
    # also providers.persistent_local language
    ok_stt = stt_lang in ("zh", "zh-TW", "zh-tw", "chinese") or "zh" in stt_lang.lower()
    if not ok_stt and isinstance(stt, dict):
        provs = stt.get("providers") or {}
        if isinstance(provs, dict):
            for v in provs.values():
                if isinstance(v, dict) and str(v.get("language", "")).lower() in ("zh", "zh-tw", "chinese"):
                    ok_stt = True
    items.append(
        Item(
            id=f"{label}.stt.zh",
            title=f"{label} STT 中文傾向",
            ok=ok_stt,
            detail=f"stt.local.language={stt_lang!r}",
            fixable=True,
            level="warn" if not ok_stt else "info",
        )
    )
    return items


def apply_preload_skills(home: Path) -> list[str]:
    notes: list[str] = []
    for name in ("hermes-tw-setup", "telegram-commands-zh"):
        notes.append(copy_skill_into(home, name))
    notes.extend(ensure_duckduckgo(home))
    return notes


def apply_voice_tw(home: Path, voice: str = "zh-TW-HsiaoChenNeural") -> list[str]:
    notes: list[str] = []
    cfg_path = home / "config.yaml"
    if not cfg_path.exists():
        return ["無 config.yaml"]
    cfg = load_yaml(cfg_path)
    changed = False
    tts = cfg.get("tts")
    if not isinstance(tts, dict):
        tts = {}
        cfg["tts"] = tts
    tts["provider"] = tts.get("provider") or "edge"
    edge = tts.get("edge")
    if not isinstance(edge, dict):
        edge = {}
        tts["edge"] = edge
    if not str(edge.get("voice") or "").startswith("zh-TW-"):
        edge["voice"] = voice
        changed = True
        notes.append(f"tts.edge.voice → {voice}")
    stt = cfg.get("stt")
    if not isinstance(stt, dict):
        stt = {}
        cfg["stt"] = stt
    local = stt.get("local")
    if not isinstance(local, dict):
        local = {}
        stt["local"] = local
    lang = str(local.get("language") or "")
    if lang not in ("zh", "zh-TW", "zh-tw"):
        local["language"] = "zh"
        changed = True
        notes.append("stt.local.language → zh")
    # persistent_local provider if present
    provs = stt.get("providers")
    if isinstance(provs, dict) and "persistent_local" in provs:
        pl = provs.get("persistent_local")
        if isinstance(pl, dict) and str(pl.get("language") or "").lower() in ("", "auto", "en", "english"):
            pl["language"] = "zh"
            changed = True
            notes.append("stt.providers.persistent_local.language → zh")
    if changed:
        bak = cfg_path.with_suffix(cfg_path.suffix + ".bak-hermes-tw-voice")
        if not bak.exists():
            shutil.copy2(cfg_path, bak)
        write_yaml(cfg_path, cfg)
        notes.append("已寫入語音相關 config")
    else:
        notes.append("語音設定已符合")
    return notes



# Office suite: capability -> acceptable skill folder names; hub install id
OFFICE_CAPABILITIES = {
    "docx": {
        "names": ("docx",),
        "hub": "skills-sh/anthropics/skills/docx",
        "title": "Word（.docx）",
    },
    "xlsx": {
        "names": ("xlsx", "spreadsheet"),
        "hub": "skills-sh/anthropics/skills/xlsx",
        "title": "Excel（.xlsx）",
    },
    "pptx": {
        "names": ("pptx", "powerpoint"),
        "hub": "skills-sh/anthropics/skills/pptx",
        "title": "PowerPoint（.pptx）",
    },
    "pdf": {
        "names": ("pdf", "nano-pdf"),
        "hub": "skills-sh/anthropics/skills/pdf",
        "title": "PDF",
    },
}


def office_skill_present(skills_root: Path, names: tuple) -> bool:
    if not skills_root.is_dir():
        return False
    for name in names:
        if skill_present(skills_root, name):
            return True
        # nested productivity/
        if skill_present(skills_root / "productivity", name):
            return True
    # rglob last resort
    for name in names:
        for p in skills_root.rglob("SKILL.md"):
            if p.parent.name == name:
                return True
    return False


def host_productivity_skill(name: str) -> Optional[Path]:
    if isolated():
        return None
    base = live_home() / "hermes-agent" / "skills" / "productivity" / name
    if base.is_dir() and (base / "SKILL.md").exists():
        return base
    return None


def install_hub_skill(home: Path, identifier: str) -> str:
    if not identifier:
        return "無 hub id"
    folder = identifier.rstrip("/").split("/")[-1]
    if "anthropics/skills" in identifier.replace("\\", "/"):
        return install_pinned_anthropic_skill(home, folder)
    return f"拒絕未釘版本來源：{identifier}"


def ensure_office_skills(home: Path) -> list[str]:
    notes: list[str] = []
    skills_root = skills_dir_for_home(home)
    skills_root.mkdir(parents=True, exist_ok=True)
    for cap, meta in OFFICE_CAPABILITIES.items():
        names = meta["names"]
        if office_skill_present(skills_root, names):
            notes.append(f"Office {cap}: 已有 {names}")
            continue
        # 1) Network: Hermes Skills Hub
        hub = meta.get("hub") or ""
        if hub:
            notes.append(install_hub_skill(home, hub))
            if office_skill_present(skills_root, names):
                continue
        # 2) Optional: productivity skills that ship **with this machine's Hermes install**
        #    (not author laptop skill dump)
        copied = False
        for name in names:
            src = host_productivity_skill(name)
            if src:
                dst = skills_root / name
                safe_copytree(src, dst)
                notes.append(f"Office {cap}: 自本機 Hermes 安裝 productivity 複製 {name}")
                copied = True
                break
        if copied:
            continue
        if DOCKER_CONTAINER:
            for name in names:
                for cand in (
                    f"/opt/hermes/skills/productivity/{name}",
                    f"/opt/hermes/skills/{name}",
                ):
                    try:
                        r = docker_exec(["sh", "-c", f"test -f {cand}/SKILL.md && echo OK"], timeout=10)
                        if "OK" in (r.stdout or ""):
                            dst = skills_root / name
                            dst.mkdir(parents=True, exist_ok=True)
                            subprocess.run(
                                ["docker", "cp", f"{DOCKER_CONTAINER}:{cand}/.", str(dst) + "/"],
                                check=True,
                                timeout=60,
                            )
                            notes.append(f"Office {cap}: 自容器 {cand} 複製")
                            copied = True
                            break
                    except Exception:
                        continue
                if copied:
                    break
        if not office_skill_present(skills_root, names):
            notes.append(
                f"Office {cap}: 仍缺 {names}；請確認網路可裝 Hub，或 Hermes 已含 productivity"
            )
    return notes


def check_office_skills(home: Path, label: str = "default") -> list[Item]:
    items: list[Item] = []
    skills_root = skills_dir_for_home(home)
    for cap, meta in OFFICE_CAPABILITIES.items():
        ok = office_skill_present(skills_root, meta["names"])
        items.append(
            Item(
                id=f"{label}.skills.office.{cap}",
                title=f"{label} Office {meta['title']}",
                ok=ok,
                detail=f"接受技能名：{meta['names']}",
                fixable=True,
                level="warn" if not ok else "info",
            )
        )
    return items



def ensure_agnes_image(home: Path) -> list[str]:
    """Install free Agnes image skill and note AGNES_API_KEY."""
    notes: list[str] = []
    skills_root = skills_dir_for_home(home)
    # prefer flat name for discoverability
    src = host_skill_source("agnes-image-generation")
    if not src:
        notes.append(
            "找不到 agnes-image-generation（應在 hermes-tw-setup/bundled/ 或本機 skills）"
        )
        return notes
    dst = skills_root / "agnes-image-generation"
    safe_copytree(src, dst)
    notes.append(f"已安裝 agnes-image-generation → {dst}")
    # rewrite SKILL key hint to the active home only
    skill_md = dst / "SKILL.md"
    if skill_md.exists():
        body = skill_md.read_text(encoding="utf-8", errors="replace")
        if "台灣 Hermes 基線" not in body:
            body = body.replace(
                "API key 已存入 `.env`（`AGNES_API_KEY`）。若需重新取得：https://platform.agnes-ai.com → Google 登入 → Settings → API Keys",
                "API key 放在該 profile 的 `.env`（`AGNES_API_KEY`）。免費申請：https://platform.agnes-ai.com → Google 登入 → Settings → API Keys（免信用卡）。台灣 Hermes 基線預設生圖走 Agnes。",
            )
            skill_md.write_text(body, encoding="utf-8")
    env_path = home / ".env"
    if env_has_key(env_path, "AGNES_API_KEY"):
        notes.append("AGNES_API_KEY 已存在")
    else:
        notes.append("缺 AGNES_API_KEY：請到 platform.agnes-ai.com 免費申請後寫入 .env（腳本不代填）")
    return notes


def check_agnes(home: Path, label: str = "default") -> list[Item]:
    skills_root = skills_dir_for_home(home)
    has_skill = skill_present(skills_root, "agnes-image-generation") or any(
        p.parent.name == "agnes-image-generation" and p.name == "SKILL.md"
        for p in skills_root.rglob("SKILL.md")
    ) if skills_root.is_dir() else False
    has_key = env_has_key(home / ".env", "AGNES_API_KEY")
    return [
        Item(
            id=f"{label}.skills.agnes",
            title=f"{label} 免費生圖技能 Agnes",
            ok=has_skill,
            detail=str(skills_root / "agnes-image-generation"),
            fixable=True,
        ),
        Item(
            id=f"{label}.env.agnes_key",
            title=f"{label} AGNES_API_KEY",
            ok=has_key,
            detail="有 key" if has_key else "無 key；agent 應以已登入 Chrome 至 platform.agnes-ai.com 用 Google 登入自取（API_KEYS_BROWSER.md）",
            fixable=False,
            level="warn" if not has_key else "info",
        ),
    ]



# Frontend-code visual skills (HTML/CSS/Canvas → screenshot pipeline)
FRONTEND_IMAGE_SKILLS = {
    "frontend-design": {
        "names": ("frontend-design",),
        "hub": "skills-sh/anthropics/skills/frontend-design",
        "title": "frontend-design（HTML/CSS 版面）",
    },
    "canvas-design": {
        "names": ("canvas-design",),
        "hub": "skills-sh/anthropics/skills/canvas-design",
        "title": "canvas-design（Canvas 視覺）",
    },
    "algorithmic-art": {
        "names": ("algorithmic-art", "p5js"),
        "hub": "skills-sh/anthropics/skills/algorithmic-art",
        "title": "algorithmic-art／p5js（程式生成）",
    },
}


def skill_names_present(skills_root: Path, names: tuple) -> bool:
    return office_skill_present(skills_root, names)


def ensure_frontend_image_skills(home: Path) -> list[str]:
    """Install frontend visual skills via **Hermes Hub** (network), not author laptop skills."""
    notes: list[str] = []
    skills_root = skills_dir_for_home(home)
    skills_root.mkdir(parents=True, exist_ok=True)
    for key, meta in FRONTEND_IMAGE_SKILLS.items():
        if skill_names_present(skills_root, meta["names"]):
            notes.append(f"前端生圖 {key}: 已有 {meta['names']}")
            continue
        hub = meta.get("hub") or ""
        if hub:
            notes.append(install_hub_skill(home, hub))
            if skill_names_present(skills_root, meta["names"]):
                continue
        if not isolated():
            for name in meta["names"]:
                base = live_home() / "hermes-agent" / "skills" / "creative" / name
                if base.is_dir() and (base / "SKILL.md").exists():
                    dst = skills_root / name
                    safe_copytree(base, dst)
                    notes.append(f"前端生圖 {key}: 自本機 Hermes creative/{name} 複製")
                    break
        if DOCKER_CONTAINER and not skill_names_present(skills_root, meta["names"]):
            for name in meta["names"]:
                cand = f"/opt/hermes/skills/creative/{name}"
                try:
                    r = docker_exec(["sh", "-c", f"test -f {cand}/SKILL.md && echo OK"], timeout=10)
                    if "OK" in (r.stdout or ""):
                        dst = skills_root / name
                        dst.mkdir(parents=True, exist_ok=True)
                        subprocess.run(
                            ["docker", "cp", f"{DOCKER_CONTAINER}:{cand}/.", str(dst) + "/"],
                            check=True,
                            timeout=60,
                        )
                        notes.append(f"前端生圖 {key}: 自容器 creative/{name}")
                        break
                except Exception as e:
                    notes.append(f"容器複製 {name} 失敗: {e}")
        if not skill_names_present(skills_root, meta["names"]):
            notes.append(
                f"前端生圖 {key}: 仍缺；需要網路取得釘版 anthropics/skills@{ANTHROPICS_SKILLS_REF[:12]}"
            )
    return notes


def check_frontend_image_skills(home: Path, label: str = "default") -> list[Item]:
    items: list[Item] = []
    skills_root = skills_dir_for_home(home)
    for key, meta in FRONTEND_IMAGE_SKILLS.items():
        ok = skill_names_present(skills_root, meta["names"])
        items.append(
            Item(
                id=f"{label}.skills.frontend_img.{key}",
                title=f"{label} {meta['title']}",
                ok=ok,
                detail=f"hub={meta.get('hub','')}",
                fixable=True,
                level="warn" if not ok else "info",
            )
        )
    return items



def ensure_superpowers(home: Path) -> list[str]:
    """Install Superpowers via **git** (network). No author-machine skill cache required."""
    notes: list[str] = []
    skills_root = skills_dir_for_home(home)
    skills_root.mkdir(parents=True, exist_ok=True)
    dst = skills_root / "superpowers"
    if superpowers_present(skills_root):
        notes.append(f"Superpowers 已存在 → {dst}")
        return notes

    # Optional: package-bundled (if a release chooses to vendor)
    src = None
    bundled = SKILL_ROOT / "bundled" / "superpowers"
    if bundled.is_dir() and (
        (bundled / "using-superpowers" / "SKILL.md").exists()
        or (bundled / "brainstorming" / "SKILL.md").exists()
    ):
        src = bundled
        notes.append("使用套件 bundled/superpowers")

    if not src:
        tmp = Path(f"/tmp/hermes-tw-superpowers-{SUPERPOWERS_REF[:12]}")
        try:
            r = git_clone_pinned(
                SUPERPOWERS_REPO,
                tmp,
                ref=SUPERPOWERS_REF,
                tag=SUPERPOWERS_TAG,
            )
            notes.append(
                f"git clone {SUPERPOWERS_REPO} @{SUPERPOWERS_TAG} ({SUPERPOWERS_REF[:12]}) → code={r.returncode}"
            )
            if r.returncode != 0:
                notes.append(((r.stderr or r.stdout or "")[:300]))
            elif (tmp / "skills" / "using-superpowers" / "SKILL.md").exists():
                src = tmp / "skills"
            elif (tmp / "using-superpowers" / "SKILL.md").exists():
                src = tmp
            else:
                for cand in tmp.rglob("using-superpowers/SKILL.md"):
                    src = cand.parent.parent
                    break
        except Exception as e:
            notes.append(f"clone superpowers 失敗：{e}")

    if not src:
        notes.append(
            "Superpowers 安裝失敗：需要網路 git 存取 https://github.com/obra/superpowers"
        )
        return notes
    safe_copytree(src, dst)
    notes.append(f"已安裝 Superpowers 技能包 @{SUPERPOWERS_TAG} → {dst}")
    return notes


def superpowers_present(skills_root: Path) -> bool:
    if not skills_root.is_dir():
        return False
    sp = skills_root / "superpowers"
    if not sp.is_dir():
        return False
    return (
        (sp / "using-superpowers" / "SKILL.md").exists()
        or (sp / "brainstorming" / "SKILL.md").exists()
        or (sp / "SKILL.md").exists()
        or any(sp.rglob("using-superpowers/SKILL.md"))
    )


def ensure_memory_boost(home: Path) -> list[str]:
    """Enable built-in memory + holographic external provider (free local SQLite)."""
    notes: list[str] = []
    cfg_path = home / "config.yaml"
    if not cfg_path.exists():
        return ["無 config.yaml"]
    cfg = load_yaml(cfg_path)
    changed = False
    mem = cfg.get("memory")
    if not isinstance(mem, dict):
        mem = {}
        cfg["memory"] = mem
    if mem.get("memory_enabled") is False:
        mem["memory_enabled"] = True
        changed = True
        notes.append("memory.memory_enabled → true")
    # Only set holographic if empty / unset; do not clobber user-chosen provider
    prov = str(mem.get("provider") or "").strip()
    if not prov:
        mem["provider"] = "holographic"
        changed = True
        notes.append("memory.provider → holographic（本機強化記憶，免 API key）")
    else:
        notes.append(f"memory.provider 已是 {prov!r}，保留不覆蓋")
    # optional plugin config defaults
    plugins = cfg.get("plugins")
    if not isinstance(plugins, dict):
        plugins = {}
        cfg["plugins"] = plugins
    hms = plugins.get("hermes-memory-store")
    if not isinstance(hms, dict):
        hms = {}
        plugins["hermes-memory-store"] = hms
    if "auto_extract" not in hms:
        hms["auto_extract"] = True
        changed = True
        notes.append("plugins.hermes-memory-store.auto_extract → true")
    if changed:
        bak = cfg_path.with_suffix(cfg_path.suffix + ".bak-hermes-tw-memory")
        if not bak.exists():
            shutil.copy2(cfg_path, bak)
        write_yaml(cfg_path, cfg)
        notes.append("已寫入記憶強化設定")
    else:
        notes.append("記憶設定無需變更")
    return notes



def telegram_rich_enabled(cfg: dict) -> bool:
    """True if rich_messages is on under telegram.extra or gateway.platforms.telegram.extra."""
    def dig_extra(root: Any) -> bool:
        if not isinstance(root, dict):
            return False
        extra = root.get("extra")
        if isinstance(extra, dict) and extra.get("rich_messages") is True:
            return True
        if root.get("rich_messages") is True:
            return True
        return False

    tg = cfg.get("telegram")
    if dig_extra(tg if isinstance(tg, dict) else {}):
        return True
    gw = cfg.get("gateway") if isinstance(cfg.get("gateway"), dict) else {}
    plats = gw.get("platforms") if isinstance(gw.get("platforms"), dict) else {}
    ptg = plats.get("telegram") if isinstance(plats.get("telegram"), dict) else {}
    if dig_extra(ptg):
        return True
    plats2 = cfg.get("platforms") if isinstance(cfg.get("platforms"), dict) else {}
    ptg2 = plats2.get("telegram") if isinstance(plats2.get("telegram"), dict) else {}
    return dig_extra(ptg2)


def telegram_streaming_disabled(cfg: dict) -> bool:
    """True when Telegram will not progressive-stream (tables stay on one-shot rich).

    Gateway uses display.platforms.telegram.streaming when set; else top-level
    streaming.enabled. Baseline wants both off for stable pipe tables (v0.20+).
    """
    disp = cfg.get("display") if isinstance(cfg.get("display"), dict) else {}
    plats = disp.get("platforms") if isinstance(disp.get("platforms"), dict) else {}
    ptg = plats.get("telegram") if isinstance(plats.get("telegram"), dict) else {}
    if "streaming" in ptg:
        return ptg.get("streaming") is False
    stream = cfg.get("streaming") if isinstance(cfg.get("streaming"), dict) else {}
    if "enabled" in stream:
        return stream.get("enabled") is False
    # missing keys → Hermes defaults often enable progressive path; treat as NOT ok
    return False


def ensure_telegram_rich(home: Path) -> list[str]:
    """Opt in Telegram Bot API rich messages + disable TG streaming (table-stable)."""
    notes: list[str] = []
    cfg_path = home / "config.yaml"
    if not cfg_path.exists():
        return ["無 config.yaml"]
    cfg = load_yaml(cfg_path)
    changed = False
    tg = cfg.get("telegram")
    if not isinstance(tg, dict):
        tg = {}
        cfg["telegram"] = tg
    extra = tg.get("extra")
    if not isinstance(extra, dict):
        extra = {}
        tg["extra"] = extra
    if extra.get("rich_messages") is not True:
        extra["rich_messages"] = True
        changed = True
        notes.append("telegram.extra.rich_messages → true（富訊息／表格原生）")
    else:
        notes.append("telegram.extra.rich_messages 已是 true")
    # rich_drafts stays false (Desktop overlay risk)
    if extra.get("rich_drafts") is True:
        extra["rich_drafts"] = False
        changed = True
        notes.append("telegram.extra.rich_drafts → false（避免串流草稿疊影）")
    elif "rich_drafts" not in extra:
        extra["rich_drafts"] = False
        changed = True
        notes.append("telegram.extra.rich_drafts → false（明確寫入）")

    # Top-level streaming master switch
    stream = cfg.get("streaming")
    if not isinstance(stream, dict):
        stream = {}
        cfg["streaming"] = stream
    if stream.get("enabled") is not False:
        stream["enabled"] = False
        changed = True
        notes.append("streaming.enabled → false（關閉 progressive 拆表）")
    else:
        notes.append("streaming.enabled 已是 false")

    # Per-platform override (wins over global for gateway)
    disp = cfg.get("display")
    if not isinstance(disp, dict):
        disp = {}
        cfg["display"] = disp
    plats = disp.get("platforms")
    if not isinstance(plats, dict):
        plats = {}
        disp["platforms"] = plats
    ptg = plats.get("telegram")
    if not isinstance(ptg, dict):
        ptg = {}
        plats["telegram"] = ptg
    if ptg.get("streaming") is not False:
        ptg["streaming"] = False
        changed = True
        notes.append("display.platforms.telegram.streaming → false")
    else:
        notes.append("display.platforms.telegram.streaming 已是 false")

    # tool_progress: never leave invalid "none" (Hermes normalises unknown → all)
    tp = disp.get("tool_progress")
    if isinstance(tp, str) and tp.strip().lower() == "none":
        disp["tool_progress"] = "all"
        changed = True
        notes.append("display.tool_progress none → all（none 會被正規化成 all，改寫明確值）")

    if changed:
        bak = cfg_path.with_suffix(cfg_path.suffix + ".bak-hermes-tw-rich")
        if not bak.exists():
            shutil.copy2(cfg_path, bak)
        write_yaml(cfg_path, cfg)
        notes.append("已寫入 Telegram rich＋streaming 基線（重啟 gateway 後生效）")
    return notes


def check_telegram_rich(home: Path, label: str = "default") -> list[Item]:
    cfg = load_yaml(home / "config.yaml") if (home / "config.yaml").exists() else {}
    ok_rich = telegram_rich_enabled(cfg)
    ok_stream = telegram_streaming_disabled(cfg)
    items = [
        Item(
            id=f"{label}.telegram.rich_messages",
            title=f"{label} Telegram 富訊息 rich_messages",
            ok=ok_rich,
            detail="telegram.extra.rich_messages=true" if ok_rich else "未開啟；apply 會設 true，需重啟 gateway",
            fixable=True,
        ),
        Item(
            id=f"{label}.telegram.streaming_off",
            title=f"{label} Telegram streaming 關閉（表格穩定）",
            ok=ok_stream,
            detail=(
                "display.platforms.telegram.streaming=false 且／或 streaming.enabled=false"
                if ok_stream
                else "仍開著 progressive streaming；v0.20+ 會先拆表成 bullet。apply 會關"
            ),
            fixable=True,
        ),
    ]
    return items


def tool_progress_zh_present() -> bool:
    """True if agent/display.py has TW tool-progress verbs patch."""
    candidates = [
        HERMES_HOME / "hermes-agent" / "agent" / "display.py",
    ]
    if not isolated():
        candidates.extend(
            [
                live_home() / "hermes-agent" / "agent" / "display.py",
                Path("/opt/hermes/agent/display.py"),
                Path("/opt/hermes/hermes-agent/agent/display.py"),
            ]
        )
        try:
            import agent.display as ad  # type: ignore

            candidates.insert(0, Path(ad.__file__).resolve())
        except Exception:
            pass
        try:
            import hermes_cli  # type: ignore

            candidates.insert(0, Path(hermes_cli.__file__).resolve().parent.parent / "agent" / "display.py")
        except Exception:
            pass
    for p in candidates:
        try:
            if isolated() and not under_target_home(p):
                continue
            if p.is_file() and "_TOOL_VERBS_ZH_HANT" in p.read_text(encoding="utf-8", errors="ignore"):
                return True
        except Exception:
            continue
    return False


def check_tool_progress_zh(label: str = "host") -> list[Item]:
    ok = tool_progress_zh_present()
    return [
        Item(
            id=f"{label}.tool_progress_zh",
            title="工具進度標籤繁中（display.py）",
            ok=ok,
            detail="agent/display.py 含 _TOOL_VERBS_ZH_HANT" if ok else "未套用；apply 會跑 bundled/tool-progress-zh",
            fixable=True,
        )
    ]


def check_behavioral_docs() -> list[Item]:
    """行為規範文件在位（表格紅線、文案下限、多 agent 規則、視覺 QA／驗證）。"""
    refs = SKILL_ROOT / "references"
    docs = [
        ("WRITING_ZH.md", "對外中文文案下限（WRITING_ZH.md）"),
        ("MULTI_AGENT_RULES.md", "多 agent 共同規則（MULTI_AGENT_RULES.md）"),
        ("TELEGRAM_RICH.md", "表格紅線細節（TELEGRAM_RICH.md 2026-08-24）"),
        ("DELIVERY_QA.md", "視覺 QA 檔位紅線與驗證原則（DELIVERY_QA.md）"),
    ]
    items: list[Item] = []
    for fn, title in docs:
        path = refs / fn
        ok = path.exists()
        extra = ""
        if fn == "TELEGRAM_RICH.md" and ok and "2026-08-24" not in path.read_text(encoding="utf-8", errors="ignore"):
            ok = False
            extra = "缺 2026-08-24 紅線章節"
        detail = "在位" if ok else (extra or f"缺 {fn}；請升級本技能到最新發行")
        items.append(
            Item(
                id=f"docs.{fn.replace('.md', '')}",
                title=title,
                ok=ok,
                detail=detail,
                fixable=True,
                level="warn",
                fix_hint=f"升級技能目錄：cd {SKILL_ROOT} && git fetch --tags && git checkout $(git describe --tags --abbrev=0 origin/main 2>/dev/null || echo main)",
            )
        )
    return items


def apply_tool_progress_zh() -> list[str]:
    notes: list[str] = []
    candidates = [
        HERMES_HOME / "skills" / "hermes-tw-setup" / "bundled" / "tool-progress-zh" / "apply_patch.py",
        SKILL_ROOT / "bundled" / "tool-progress-zh" / "apply_patch.py",
    ]
    script = next((p for p in candidates if p.exists()), None)
    if DOCKER_CONTAINER:
        notes.append(
            "Docker 測試：工具進度繁中需改容器內 agent/display.py；"
            "預設不自動改映像，正式請在 host 跑 apply 或 bake 進 image"
        )
        if script:
            notes.append(f"本機可見腳本 {script}（未對容器自動執行）")
        return notes
    if isolated():
        target = HERMES_HOME / "hermes-agent" / "agent" / "display.py"
        if not target.is_file():
            notes.append("隔離家目錄沒有上游 display.py，略過進度補丁（不改正式安裝）")
            return notes
    if not script:
        notes.append("找不到 bundled/tool-progress-zh/apply_patch.py")
        return notes
    try:
        r = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=60,
            env=bind_env(),
        )
        notes.append(f"tool-progress-zh → code={r.returncode}")
        out = (r.stdout or "") + (r.stderr or "")
        if out.strip():
            notes.append(out.strip()[:800])
    except Exception as e:
        notes.append(f"執行失敗：{e}")
    return notes


def ensure_behavior_snippets(home: Path) -> list[str]:
    """Append new SOUL/MEMORY rules if core already present (idempotent needles)."""
    notes: list[str] = []
    soul = home / "SOUL.md"
    mem_path = home / "memories" / "MEMORY.md"
    full = (REF / "SOUL-TW.md").read_text(encoding="utf-8")
    soul_text = soul.read_text(encoding="utf-8", errors="replace") if soul.exists() else ""
    for title, needle in [
        ("## Telegram 富訊息（表格優先）", "Telegram 富訊息"),
        ("## 交付確認（與使用者對齊）", "交付確認"),
        ("## 檔案交付前：subagent 純視覺 QA", "純視覺 QA"),
    ]:
        if needle in soul_text:
            notes.append(f"SOUL 已有：{needle}")
            continue
        if title not in full:
            continue
        start = full.index(title)
        rest = full[start + len(title) :]
        m = re.search(r"\n## ", rest)
        section = full[start:] if not m else full[start : start + len(title) + m.start()]
        append_unique(soul, "\n" + section.strip() + "\n", needle)
        notes.append(f"SOUL 已追加：{needle}")
        soul_text = soul.read_text(encoding="utf-8", errors="replace") if soul.exists() else soul_text
    mem_text = mem_path.read_text(encoding="utf-8", errors="replace") if mem_path.exists() else ""
    for bullet in [
        "Telegram：`telegram.extra.rich_messages: true`，且 `display.platforms.telegram.streaming: false`",
        "表格成功＝設定＋API＋使用者目視格子；禁止只看 rich 紀錄就宣稱完成",
        "檔案交付前：派**獨立 subagent 做純視覺 QA**",
        "交付後習慣與使用者確認是否符合需求",
    ]:
        short = bullet[:24]
        if short in mem_text or bullet in mem_text:
            notes.append(f"MEMORY 已有：{short}…")
            continue
        append_unique(mem_path, "- " + bullet.lstrip("- ").strip(), short)
        notes.append(f"MEMORY 已追加：{short}…")
        mem_text = mem_path.read_text(encoding="utf-8", errors="replace") if mem_path.exists() else mem_text
    return notes


def check_superpowers_and_memory(home: Path, label: str = "default") -> list[Item]:
    items: list[Item] = []
    skills_root = skills_dir_for_home(home)
    items.append(
        Item(
            id=f"{label}.skills.superpowers",
            title=f"{label} Superpowers 技能包",
            ok=superpowers_present(skills_root),
            detail=str(skills_root / "superpowers"),
            fixable=True,
        )
    )
    cfg = load_yaml(home / "config.yaml") if (home / "config.yaml").exists() else {}
    mem = cfg.get("memory") if isinstance(cfg.get("memory"), dict) else {}
    prov = str(mem.get("provider") or "").strip()
    enabled = mem.get("memory_enabled", True) is not False
    boost_ok = enabled and bool(prov)  # any external provider counts as boosted
    items.append(
        Item(
            id=f"{label}.memory.boost",
            title=f"{label} 強化記憶（外部 provider）",
            ok=boost_ok,
            detail=f"enabled={enabled} provider={prov!r}（建議 holographic）",
            fixable=True,
            level="warn" if not boost_ok else "info",
        )
    )
    return items



def run_check() -> Report:
    r = Report()
    os_id = detect_os()
    r.add(
        Item(
            id="host.os",
            title="作業系統",
            ok=True,
            detail=f"{os_id} ({platform.platform()})",
        )
    )

    r.add(
        Item(
            id="hermes.home",
            title="HERMES_HOME",
            ok=HERMES_HOME.is_dir(),
            detail=str(HERMES_HOME),
        )
    )
    r.add(
        Item(
            id="host.isolation",
            title="家目錄隔離狀態",
            ok=True,
            detail=(
                f"測試目錄 {HERMES_HOME}（只寫這裡）"
                if isolated()
                else f"家目錄 {HERMES_HOME}"
            ),
        )
    )

    # side
    r.add(
        Item(
            id="profile.side",
            title="副 profile side 存在",
            ok=SIDE_HOME.exists() and (SIDE_HOME / "config.yaml").exists(),
            detail=str(SIDE_HOME),
            fixable=True,
        )
    )

    r.items.extend(check_profile("default", HERMES_HOME, is_side=False))
    r.items.extend(check_preload_and_voice(HERMES_HOME, "default"))
    r.items.extend(check_office_skills(HERMES_HOME, "default"))
    r.items.extend(check_agnes(HERMES_HOME, "default"))
    r.items.extend(check_frontend_image_skills(HERMES_HOME, "default"))
    r.items.extend(check_superpowers_and_memory(HERMES_HOME, "default"))
    r.items.extend(check_telegram_rich(HERMES_HOME, "default"))
    r.items.extend(check_tool_progress_zh("host"))
    r.items.extend(check_behavioral_docs())
    if SIDE_HOME.exists():
        r.items.extend(check_profile("side", SIDE_HOME, is_side=True))
        # 副共用技能庫：預裝 skill 以主目錄為準，只再查語音
        r.items.extend([i for i in check_preload_and_voice(SIDE_HOME, "side") if i.id.endswith(".tts.zh_tw") or i.id.endswith(".stt.zh")])
        # Superpowers 在主 skills；副只再查強化記憶（holographic）
        r.items.extend(
            [i for i in check_superpowers_and_memory(SIDE_HOME, "side") if i.id.endswith(".memory.boost")]
        )
        r.items.extend(check_telegram_rich(SIDE_HOME, "side"))

    # tokens distinct if both present
    main_tok = env_get(HERMES_HOME / ".env", "TELEGRAM_BOT_TOKEN") or env_get(
        HERMES_HOME / ".env", "TELEGRAM_BOT_TOKEN_DEFAULT"
    )
    side_tok = env_get(SIDE_HOME / ".env", "TELEGRAM_BOT_TOKEN") if SIDE_HOME.exists() else ""
    if main_tok and side_tok:
        r.add(
            Item(
                id="telegram.distinct",
                title="主副 Telegram token 不同",
                ok=main_tok != side_tok,
                detail="已比對（不顯示 token）",
                fixable=False,
            )
        )
    elif not SIDE_HOME.exists():
        r.add(
            Item(
                id="telegram.distinct",
                title="主副 Telegram token 不同",
                ok=False,
                detail="副 profile 尚未建立，無法比對",
                fixable=True,
                level="warn",
            )
        )

    # anysearch anonymous
    anon = anysearch_provider_allows_anonymous()
    r.add(
        Item(
            id="search.anysearch_anonymous",
            title="AnySearch provider 支援匿名（免 key）",
            ok=anon is True,
            detail="無法定位 provider.py" if anon is None else (
                "目前仍強制 ANYSEARCH_API_KEY" if anon is False else "已允許匿名"
            ),
            fixable=anon is False,
            level="warn" if anon is not True else "info",
        )
    )

    # CDP
    cdp_ports = [p for p in (9222, 9223) if cdp_up(p)]
    r.add(
        Item(
            id="browser.cdp",
            title="Chrome CDP 可連",
            ok=bool(cdp_ports),
            detail=f"up ports={cdp_ports or 'none'}；取 key 時必須是已登入 Google 的 user-data-dir profile",
            fixable=False,
            level="warn" if not cdp_ports else "info",
        )
    )
    r.add(
        Item(
            id="browser.keys_doc",
            title="API key 瀏覽器自取說明",
            ok=(REF / "API_KEYS_BROWSER.md").exists(),
            detail=str(REF / "API_KEYS_BROWSER.md"),
            fixable=False,
        )
    )

    # gateway
    if DOCKER_CONTAINER:
        try:
            dr = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", DOCKER_CONTAINER],
                capture_output=True,
                text=True,
                timeout=10,
            )
            running = (dr.stdout or "").strip().lower() == "true"
        except Exception:
            running = False
        r.add(
            Item(
                id="host.gateway_active",
                title=f"Docker 容器 {DOCKER_CONTAINER} 運行中",
                ok=running,
                detail=f"docker inspect Running={running}",
                fixable=False,
                level="warn" if not running else "info",
            )
        )
        r.add(
            Item(
                id="host.gateway_enabled",
                title="Docker 重啟策略（測試環境）",
                ok=True,
                detail="測試以容器為準；正式機再設 systemd／LaunchAgent",
            )
        )
        r.add(
            Item(
                id="host.sleep",
                title="禁休眠（Docker 測試略過主機電源）",
                ok=True,
                detail="主機電源政策不在容器資料目錄內驗證",
            )
        )
    elif os_id == "linux":
        active = systemd_user_active("hermes-gateway.service")
        enabled = systemd_user_enabled("hermes-gateway.service")
        r.add(
            Item(
                id="host.gateway_active",
                title="gateway 服務運行中",
                ok=active is True,
                detail=f"active={active}",
                fixable=True,
                level="warn" if active is not True else "info",
            )
        )
        r.add(
            Item(
                id="host.gateway_enabled",
                title="gateway 開機自啟",
                ok=enabled is True,
                detail=f"enabled={enabled}",
                fixable=True,
                level="warn" if enabled is not True else "info",
            )
        )
        r.add(check_linux_sleep())
    else:
        r.add(
            Item(
                id="host.gateway_active",
                title="gateway 自啟（非 Linux 請手動確認）",
                ok=False,
                detail=f"OS={os_id}：請確認 LaunchAgent／工作排程器",
                fixable=False,
                level="warn",
            )
        )
        r.add(
            Item(
                id="host.sleep",
                title="禁休眠（非 Linux 請手動確認）",
                ok=False,
                detail=f"OS={os_id}：請確認電源方案（可關螢幕、禁 sleep）",
                fixable=False,
                level="warn",
            )
        )

    zh_cmd = commands_py_has_zh()
    r.add(
        Item(
            id="telegram.commands_zh",
            title="Telegram 指令描述繁中（commands.py）",
            ok=zh_cmd is True,
            detail="未找到 commands.py" if zh_cmd is None else (
                "已含繁中描述" if zh_cmd else "仍偏英文，請跑 telegram-commands-zh"
            ),
            fixable=zh_cmd is False,
            level="warn" if zh_cmd is not True else "info",
        )
    )

    r.add(
        Item(
            id="openrouter.rank_source",
            title="OpenRouter Hermes 用量榜來源",
            ok=True,
            detail=f"必須用瀏覽器抓：{OPENROUTER_HERMES_APP}（本 check 不代替抓榜）",
        )
    )

    return r


def default_fix_hints() -> dict[str, str]:
    """未過項目的預設指令（可被 Item.fix_hint 覆蓋）。"""
    hh = str(HERMES_HOME)
    side = str(SIDE_HOME)
    return {
        "default.openrouter_fallback": (
            "1) 用已登入 Chrome（CDP）開 https://openrouter.ai/settings/keys 建立／複製 key\n"
            f"2) 寫入 {hh}/.env 與 {side}/.env：OPENROUTER_API_KEY=...\n"
            "3) 瀏覽器開 https://openrouter.ai/apps/hermes-agent 抓 Top models 前 10\n"
            "4) 主副 config.yaml 寫入 fallback_providers（只准前 10 內 model id）\n"
            "   或：hermes fallback add  （再對 side 同步同一組）\n"
            "詳見 references/API_KEYS_BROWSER.md 與 references/MANUAL_STEPS.md"
        ),
        "side.openrouter_fallback": (
            f"與主 profile 同一組 OPENROUTER_API_KEY + fallback_providers；寫入 {side}/.env 與 config.yaml\n"
            "詳見 references/MANUAL_STEPS.md §模型與 OpenRouter"
        ),
        "default.env.agnes_key": (
            "1) 已登入 Chrome（CDP）開 https://platform.agnes-ai.com → Settings → API Keys\n"
            f"2) 寫入 {hh}/.env：AGNES_API_KEY=...\n"
            "詳見 references/API_KEYS_BROWSER.md"
        ),
        "side.telegram_token": (
            "Telegram @BotFather → /newbot 再做一隻（第二個 token）\n"
            f"寫入 {side}/.env：TELEGRAM_BOT_TOKEN=...\n"
            "禁止與主 bot 共用 token\n"
            "詳見 references/MANUAL_STEPS.md §雙 Telegram bot"
        ),
        "default.telegram_token": (
            "Telegram @BotFather → /newbot\n"
            f"寫入 {hh}/.env：TELEGRAM_BOT_TOKEN=...\n"
            "並設定 TELEGRAM_ALLOWED_USERS（你的 Telegram 數字 ID）\n"
            "詳見 references/MANUAL_STEPS.md §雙 Telegram bot"
        ),
        "telegram.distinct": (
            "主副必須不同 token。副 token 在 @BotFather 再 /newbot 一隻\n"
            f"主：{hh}/.env  副：{side}/.env"
        ),
        "default.skills.superpowers": (
            f"需要網路：apply 會 git clone {SUPERPOWERS_REPO} --branch {SUPERPOWERS_TAG}（釘 {SUPERPOWERS_REF}）\n"
            "手動請用同一 tag／同一提交，不要 clone 預設分支頭\n"
            f"  或：python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes\n"
            "不依賴作者本機 skill 目錄"
        ),
        "default.telegram.streaming_off": (
            f"在 {hh}/config.yaml 設定：\n"
            "  streaming.enabled: false\n"
            "  display.platforms.telegram.streaming: false\n"
            "或：python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes\n"
            "然後重啟 gateway（表格才不會被 progressive 拆成 bullet）"
        ),
        "side.telegram.streaming_off": (
            f"在 {side}/config.yaml 同樣關閉 streaming（與主一致）\n"
            "或重新 apply --yes 後重啟副 gateway"
        ),
        "host.tool_progress_zh": (
            "python3 ~/.hermes/skills/hermes-tw-setup/bundled/tool-progress-zh/apply_patch.py\n"
            "或 baseline apply --yes；完成後重啟所有 gateway\n"
            "補丁改的是本機 Hermes 的 agent/display.py（部署端），不連作者機器"
        ),
        "default.memory.boost": (
            f"在 {hh}/config.yaml 設定 memory.provider: holographic 與 memory_enabled: true\n"
            "或重新 apply：python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes"
        ),
        "side.memory.boost": (
            f"在 {side}/config.yaml 設定 memory.provider: holographic\n"
            "或重新 apply"
        ),
        "host.gateway_autostart": (
            "Linux：systemctl --user enable --now hermes-gateway\n"
            "      loginctl enable-linger $USER\n"
            "macOS／Windows：見 references/MANUAL_STEPS.md §主機自啟與禁休眠"
        ),
        "host.no_sleep": (
            "Linux：sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target\n"
            "macOS：caffeinate / 系統設定→電池→防止自動睡眠\n"
            "Windows：powercfg /change standby-timeout-ac 0\n"
            "詳見 references/MANUAL_STEPS.md"
        ),
        "model.oauth": (
            "擇一：hermes model   或  hermes auth add openai-codex  /  hermes auth add xai-oauth\n"
            "副 profile：hermes -p side 再登一次（若 auth 分 profile）"
        ),
    }


def print_report(report: Report) -> None:
    print("=== hermes-tw-setup check ===")
    print(f"HERMES_HOME={HERMES_HOME}")
    print(f"OS={detect_os()}")
    if DOCKER_CONTAINER:
        print(f"DOCKER={DOCKER_CONTAINER}")
    print()
    for i in report.items:
        mark = "OK" if i.ok else "NO"
        fix = " [可修]" if (not i.ok and i.fixable) else ""
        print(f"[{mark}] {i.title}{fix}")
        if i.detail:
            print(f"      {i.detail}")
    print()
    print(f"合計：OK {report.ok_count()} / 全部 {len(report.items)}；未過 {report.fail_count()}")
    fails = [i for i in report.items if not i.ok]
    if fails:
        hints = default_fix_hints()
        print("未過項目（含建議指令）：")
        for i in fails:
            print(f"  - {i.id}: {i.title}")
            hint = (i.fix_hint or hints.get(i.id) or "").strip()
            if hint:
                for line in hint.splitlines():
                    print(f"      → {line}")
            elif i.fixable:
                print("      → 可跑：python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py apply --yes")
            else:
                print("      → 見 references/MANUAL_STEPS.md")
        print()
        print("完整開箱指令手冊：references/MANUAL_STEPS.md")


def append_unique(path: Path, content: str, needle: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if needle in existing:
        return False
    sep = "\n\n" if existing and not existing.endswith("\n") else "\n"
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + sep + content.strip() + "\n", encoding="utf-8")
    return True


def ensure_soul(home: Path) -> str:
    block = (REF / "SOUL-TW.md").read_text(encoding="utf-8")
    path = home / "SOUL.md"
    if soul_has_core(path):
        return "已有核心行為，略過"
    if not path.exists():
        path.write_text(block + "\n", encoding="utf-8")
        return "新建 SOUL.md"
    append_unique(path, "\n" + block, "台灣 Hermes 通用行為")
    return "已追加台灣通用行為區塊"


def ensure_memory(home: Path) -> str:
    snippet = (REF / "MEMORY-SNIPPET.md").read_text(encoding="utf-8")
    # strip markdown header lines for memory file friendliness
    body = "\n".join(
        ln for ln in snippet.splitlines() if not ln.startswith("#")
    ).strip()
    path = home / "memories" / "MEMORY.md"
    if memory_has_snippet(path):
        return "已有基線短句，略過"
    append_unique(path, body, "openrouter.ai/apps/hermes-agent")
    return "已追加 MEMORY 短句"


def patch_config_baseline(home: Path, is_side: bool) -> list[str]:
    notes: list[str] = []
    cfg_path = home / "config.yaml"
    if not cfg_path.exists():
        notes.append("無 config.yaml，略過")
        return notes
    cfg = load_yaml(cfg_path)
    changed = False

    if cfg.get("timezone") != "Asia/Taipei":
        cfg["timezone"] = "Asia/Taipei"
        changed = True
        notes.append("timezone → Asia/Taipei")

    disp = cfg.get("display")
    if not isinstance(disp, dict):
        disp = {}
        cfg["display"] = disp
    if disp.get("language") not in ("zh-TW", "zh-Hant", "zh-hant"):
        disp["language"] = "zh-TW"
        changed = True
        notes.append("display.language → zh-TW")

    web = cfg.get("web")
    if not isinstance(web, dict):
        web = {}
        cfg["web"] = web
    if web.get("search_backend") != "anysearch":
        web["search_backend"] = "anysearch"
        changed = True
        notes.append("search_backend → anysearch")
    if web.get("extract_backend") != "anysearch":
        web["extract_backend"] = "anysearch"
        changed = True
        notes.append("extract_backend → anysearch")

    if is_side:
        skills = cfg.get("skills")
        if not isinstance(skills, dict):
            skills = {}
            cfg["skills"] = skills
        ext = skills.get("external_dirs")
        if not isinstance(ext, list):
            ext = []
        # Docker 資料掛在 /opt/data；容器內路徑必須用 /opt/data/skills
        if DOCKER_CONTAINER:
            target = "/opt/data/skills"
            also_ok = {target, str(HERMES_HOME / "skills"), "~/.hermes/skills"}
        else:
            target = str(HERMES_HOME / "skills")
            also_ok = {target, "~/.hermes/skills", str(Path.home() / ".hermes" / "skills")}
        normalized = [str(x) for x in ext]
        if not any(n in also_ok or n.endswith("/.hermes/skills") or n.endswith("/skills") and "hermes" in n for n in normalized):
            # remove wrong host paths if docker
            if DOCKER_CONTAINER:
                ext = [x for x in ext if "/opt/data/skills" in str(x) or str(x) == target]
            ext = list(ext) + [target]
            skills["external_dirs"] = ext
            changed = True
            notes.append(f"external_dirs += {target}")
        elif DOCKER_CONTAINER and any(str(x).startswith(str(Path.home())) for x in ext):
            # fix host-path mistake
            ext = [target if str(x).startswith(str(Path.home())) else x for x in ext]
            if target not in [str(x) for x in ext]:
                ext.append(target)
            skills["external_dirs"] = ext
            changed = True
            notes.append(f"external_dirs 改為容器路徑 {target}")

    # chrome mcp if missing
    mcp = cfg.get("mcp_servers")
    if not isinstance(mcp, dict):
        mcp = {}
        cfg["mcp_servers"] = mcp
    has_chrome = any("chrome" in str(k).lower() or "devtools" in str(k).lower() for k in mcp)
    if not has_chrome:
        mcp["chrome-devtools"] = {
            "command": "npx",
            "args": [
                CHROME_DEVTOOLS_MCP,
                "--browserUrl",
                "http://127.0.0.1:9222",
            ],
            "description": "Chrome CDP DevTools MCP (port 9222)",
        }
        changed = True
        notes.append("mcp_servers += chrome-devtools → 9222")

    if changed:
        # backup
        bak = cfg_path.with_suffix(cfg_path.suffix + ".bak-hermes-tw-setup")
        if not bak.exists():
            shutil.copy2(cfg_path, bak)
            notes.append(f"備份 {bak.name}")
        write_yaml(cfg_path, cfg)
        notes.append("已寫入 config.yaml")
    else:
        notes.append("config 已符合，略過")
    return notes


def create_side_profile() -> list[str]:
    notes: list[str] = []
    if SIDE_HOME.exists() and (SIDE_HOME / "config.yaml").exists():
        notes.append("side 已存在")
        return notes
    if DOCKER_CONTAINER:
        try:
            r = docker_exec(
                ["hermes", "profile", "create", SIDE_NAME, "--clone"],
                timeout=180,
            )
            notes.append(f"docker exec hermes profile create side --clone → code={r.returncode}")
            if r.stdout:
                notes.append(r.stdout.strip()[:500])
            if r.returncode != 0 and r.stderr:
                notes.append(r.stderr.strip()[:500])
        except Exception as e:
            notes.append(f"docker create 失敗：{e}")
        return notes
    hermes = shutil.which("hermes")
    if not hermes:
        notes.append("找不到 hermes 指令，無法自動 create profile")
        return notes
    try:
        r = subprocess.run(
            [hermes, "profile", "create", SIDE_NAME, "--clone"],
            capture_output=True,
            text=True,
            timeout=120,
            env=bind_env(),
        )
        notes.append(f"hermes profile create side --clone → code={r.returncode}")
        if r.stdout:
            notes.append(r.stdout.strip()[:500])
        if r.returncode != 0 and r.stderr:
            notes.append(r.stderr.strip()[:500])
    except Exception as e:
        notes.append(f"create 失敗：{e}")
    return notes


def patch_anysearch_anonymous() -> list[str]:
    """Allow AnySearch without API key (anonymous HTTP)."""
    notes: list[str] = []
    import tempfile

    docker_mode = bool(DOCKER_CONTAINER)
    tmp_path: Optional[Path] = None
    container_prov = "/opt/hermes/plugins/web/anysearch/provider.py"

    if docker_mode:
        notes.append("Docker 模式：補丁打在容器映像檔案（重 build 會掉）")
        try:
            td = Path(tempfile.mkdtemp(prefix="hermes-tw-anysearch-"))
            tmp_path = td / "provider.py"
            # docker cp 可能產生 root 擁有檔；先 cp 再 chmod 或改用 stdout
            subprocess.run(
                ["docker", "cp", f"{DOCKER_CONTAINER}:{container_prov}", str(tmp_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            try:
                tmp_path.chmod(0o644)
            except Exception:
                pass
            # if still not writable, copy content via docker exec cat
            try:
                with open(tmp_path, "a", encoding="utf-8"):
                    pass
            except PermissionError:
                r = subprocess.run(
                    ["docker", "exec", DOCKER_CONTAINER, "cat", container_prov],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if r.returncode != 0:
                    notes.append("docker exec cat provider 失敗")
                    return notes
                tmp_path = td / "provider-user.py"
                tmp_path.write_text(r.stdout, encoding="utf-8")
            prov = tmp_path
        except Exception as e:
            notes.append(f"docker cp 失敗：{e}")
            return notes
    else:
        prov = HERMES_HOME / "hermes-agent" / "plugins" / "web" / "anysearch" / "provider.py"
        if not prov.exists():
            notes.append(
                f"找不到 {prov}；隔離家目錄不回落到正式安裝，略過 AnySearch 補丁"
            )
            return notes

    text = prov.read_text(encoding="utf-8")
    if "HERMES_TW_ANONYMOUS_ANYSEARCH" in text:
        notes.append("anysearch provider 已打過匿名補丁")
        return notes

    old_avail = (
        "    def is_available(self) -> bool:\n"
        '        """Return True when ``ANYSEARCH_API_KEY`` is set to a non-empty value."""\n'
        '        return bool(os.getenv("ANYSEARCH_API_KEY", "").strip())'
    )
    new_avail = (
        "    def is_available(self) -> bool:\n"
        '        """AnySearch supports anonymous access; key optional (HERMES_TW_ANONYMOUS_ANYSEARCH)."""\n'
        "        return True  # HERMES_TW_ANONYMOUS_ANYSEARCH"
    )

    if old_avail in text:
        text = text.replace(old_avail, new_avail, 1)
    else:
        text2, n = re.subn(
            r"def is_available\(self\) -> bool:.*?return bool\(os\.getenv\(\s*[\"']ANYSEARCH_API_KEY[\"'].*?\)\s*\)",
            "def is_available(self) -> bool:\n        return True  # HERMES_TW_ANONYMOUS_ANYSEARCH",
            text,
            count=1,
            flags=re.S,
        )
        if n:
            text = text2
        else:
            notes.append("無法自動替換 is_available")
            return notes

    old_raise = (
        '    api_key = os.getenv("ANYSEARCH_API_KEY", "").strip()\n'
        "    if not api_key:\n"
        "        raise ValueError(\n"
        '            "ANYSEARCH_API_KEY environment variable not set. "\n'
        '            "Get your API key at https://anysearch.com"\n'
        "        )\n"
        "\n"
        "    payload = {\n"
        '        "jsonrpc": "2.0",\n'
        '        "id": 1,\n'
        '        "method": "tools/call",\n'
        '        "params": {"name": method, "arguments": arguments},\n'
        "    }\n"
        "\n"
        "    headers = {\n"
        '        "Authorization": f"Bearer {api_key}",\n'
        '        "Content-Type": "application/json",\n'
        "    }"
    )
    new_raise = (
        '    api_key = os.getenv("ANYSEARCH_API_KEY", "").strip()\n'
        "    # HERMES_TW_ANONYMOUS_ANYSEARCH: empty key → anonymous (no Authorization)\n"
        "\n"
        "    payload = {\n"
        '        "jsonrpc": "2.0",\n'
        '        "id": 1,\n'
        '        "method": "tools/call",\n'
        '        "params": {"name": method, "arguments": arguments},\n'
        "    }\n"
        "\n"
        "    headers = {\n"
        '        "Content-Type": "application/json",\n'
        "    }\n"
        "    if api_key:\n"
        '        headers["Authorization"] = f"Bearer {api_key}"'
    )

    if old_raise in text:
        text = text.replace(old_raise, new_raise, 1)
    else:
        notes.append("headers 區塊與預期不符（is_available 可能已改）")

    if not docker_mode:
        bak = prov.with_suffix(".py.bak-hermes-tw-setup")
        if not bak.exists():
            shutil.copy2(prov, bak)
            notes.append(f"備份 {bak.name}")
        prov.write_text(text, encoding="utf-8")
        notes.append("AnySearch 匿名補丁已套用")
    else:
        assert tmp_path is not None
        tmp_path.write_text(text, encoding="utf-8")
        try:
            subprocess.run(
                ["docker", "cp", str(tmp_path), f"{DOCKER_CONTAINER}:{container_prov}"],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            notes.append("AnySearch 匿名補丁已寫入容器")
        except Exception as e:
            notes.append(f"docker cp 回寫失敗：{e}")
    return notes


def apply_telegram_zh() -> list[str]:
    notes: list[str] = []
    candidates = [
        HERMES_HOME / "skills" / "telegram-commands-zh" / "apply_patch.py",
        SKILL_ROOT / "bundled" / "telegram-commands-zh" / "apply_patch.py",
    ]
    script = next((p for p in candidates if p.exists()), None)
    if DOCKER_CONTAINER:
        notes.append(
            "Docker 測試：telegram 繁中選單需改容器內 commands.py；"
            "預設不自動改映像，正式應 bake 進 image 或掛載 skills"
        )
        if script:
            notes.append(f"本機可見腳本 {script}（未對容器自動執行）")
        return notes
    if isolated():
        target = HERMES_HOME / "hermes-agent" / "hermes_cli" / "commands.py"
        if not target.is_file():
            notes.append("隔離家目錄沒有上游 commands.py，略過選單補丁（不改正式安裝）")
            return notes
    if not script:
        notes.append("找不到 telegram-commands-zh/apply_patch.py")
        return notes
    try:
        r = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=60,
            env=bind_env(),
        )
        notes.append(f"telegram-commands-zh → code={r.returncode}")
        out = (r.stdout or "") + (r.stderr or "")
        if out.strip():
            notes.append(out.strip()[:800])
    except Exception as e:
        notes.append(f"執行失敗：{e}")
    return notes


def apply_linux_gateway_enable() -> list[str]:
    notes: list[str] = []
    if DOCKER_CONTAINER:
        return [f"Docker 模式（{DOCKER_CONTAINER}）：略過 host systemd"]
    if isolated():
        return ["隔離家目錄：略過本機閘道自啟（不啟用正式 hermes-gateway）"]
    if detect_os() != "linux":
        return ["非 Linux，略過 systemd"]
    try:
        r = subprocess.run(
            ["systemctl", "--user", "enable", "--now", "hermes-gateway.service"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        notes.append(f"enable --now hermes-gateway → {r.returncode}")
        if r.stderr:
            notes.append(r.stderr.strip()[:300])
    except Exception as e:
        notes.append(str(e))
    return notes


def run_apply(yes: bool) -> None:
    print("=== hermes-tw-setup apply ===")
    print(f"HERMES_HOME={HERMES_HOME}")
    if isolated():
        print("測試目錄：設定只寫進這個家目錄。")
    print(f"預裝鎖定：Superpowers {SUPERPOWERS_TAG}、anthropics/skills {ANTHROPICS_SKILLS_REF[:12]}、{CHROME_DEVTOOLS_MCP}、{PYYAML_SPEC}")
    if not yes:
        print("將套用基線（建立 side、config、SOUL/MEMORY、anysearch 匿名補丁、繁中選單等）。")
        print("不會自動改 macOS/Windows 電源；Linux 休眠策略僅報告、不強制 mask。")
        print("繼續請加 --yes")
        return

    all_notes: list[str] = []

    print("\n[1] 建立 side profile")
    notes = create_side_profile()
    for n in notes:
        print("  ", n)
    all_notes.extend(notes)

    print("\n[2] 主 profile config / SOUL / MEMORY")
    for n in patch_config_baseline(HERMES_HOME, is_side=False):
        print("  ", n)
    print("  ", ensure_soul(HERMES_HOME))
    print("  ", ensure_memory(HERMES_HOME))
    print("\n[2b] 預裝 skill + 台灣語音（主）")
    for n in apply_preload_skills(HERMES_HOME):
        print("  ", n)
    print("\n[2c] Office 檔案技能")
    for n in ensure_office_skills(HERMES_HOME):
        print("  ", n)
    print("\n[2d] 免費生圖 Agnes")
    for n in ensure_agnes_image(HERMES_HOME):
        print("  ", n)
    print("\n[2e] 前端程式碼生圖技能")
    for n in ensure_frontend_image_skills(HERMES_HOME):
        print("  ", n)
    print("\n[2f] Superpowers + 強化記憶")
    for n in ensure_superpowers(HERMES_HOME):
        print("  ", n)
    for n in ensure_memory_boost(HERMES_HOME):
        print("  ", n)
    print("\n[2g] Telegram 富訊息 + streaming 關 + 行為片段")
    for n in ensure_telegram_rich(HERMES_HOME):
        print("  ", n)
    for n in ensure_behavior_snippets(HERMES_HOME):
        print("  ", n)
    for n in apply_voice_tw(HERMES_HOME):
        print("  ", n)

    if SIDE_HOME.exists():
        print("\n[3] 副 profile side")
        for n in patch_config_baseline(SIDE_HOME, is_side=True):
            print("  ", n)
        print("  ", ensure_soul(SIDE_HOME))
        print("  ", ensure_memory(SIDE_HOME))
        print("\n[3b] 台灣語音（副；技能共用主庫）")
        for n in apply_voice_tw(SIDE_HOME):
            print("  ", n)
        for n in ensure_memory_boost(SIDE_HOME):
            print("   ", n)
        for n in ensure_telegram_rich(SIDE_HOME):
            print("   ", n)
        for n in ensure_behavior_snippets(SIDE_HOME):
            print("   ", n)
        # sync model + fallback from main if side empty-ish
        try:
            main_cfg = load_yaml(HERMES_HOME / "config.yaml")
            side_cfg = load_yaml(SIDE_HOME / "config.yaml")
            changed = False
            if main_cfg.get("model") and side_cfg.get("model") != main_cfg.get("model"):
                side_cfg["model"] = main_cfg.get("model")
                changed = True
            if main_cfg.get("fallback_providers") and side_cfg.get("fallback_providers") != main_cfg.get(
                "fallback_providers"
            ):
                side_cfg["fallback_providers"] = main_cfg.get("fallback_providers")
                changed = True
            if changed:
                bak = SIDE_HOME / "config.yaml.bak-hermes-tw-setup-model"
                if not bak.exists():
                    shutil.copy2(SIDE_HOME / "config.yaml", bak)
                write_yaml(SIDE_HOME / "config.yaml", side_cfg)
                print("   已同步 model 與 fallback_providers 自 default")
            else:
                print("   model/fallback 已對齊或略過")
            main_env = HERMES_HOME / ".env"
            side_env = SIDE_HOME / ".env"
            mt = env_get(main_env, "TELEGRAM_BOT_TOKEN") or env_get(main_env, "TELEGRAM_BOT_TOKEN_DEFAULT")
            st = env_get(side_env, "TELEGRAM_BOT_TOKEN")
            if mt and st and mt == st:
                raw = side_env.read_text(encoding="utf-8", errors="replace") if side_env.exists() else ""
                lines = []
                for line in raw.splitlines():
                    if line.strip().startswith("TELEGRAM_BOT_TOKEN=") and not line.strip().startswith("#"):
                        lines.append("# CLEARED by hermes-tw-setup: must be a DIFFERENT bot from main")
                        lines.append("# TELEGRAM_BOT_TOKEN=")
                    else:
                        lines.append(line)
                side_env.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
                print("   副 profile Telegram token 與主相同 → 已清空，請填第二個 bot token")
        except Exception as e:
            print("   同步模型失敗：", e)
    else:
        print("\n[3] 副 profile 仍不存在，跳過 side 設定")

    print("\n[4] AnySearch 匿名")
    for n in patch_anysearch_anonymous():
        print("  ", n)

    print("\n[5] Telegram 指令繁中")
    for n in apply_telegram_zh():
        print("  ", n)
    print("   提醒：需重啟各 profile gateway 後，Telegram 選單才會更新")

    print("\n[5b] 工具進度標籤繁中（Running code → 執行程式）")
    for n in apply_tool_progress_zh():
        print("  ", n)
    print("   提醒：需重啟 gateway 後進度氣泡才變繁中")

    print("\n[6] Linux gateway 自啟")
    for n in apply_linux_gateway_enable():
        print("  ", n)

    print("\n[7] 後續（agent／使用者）— 皆有指令，見 references/MANUAL_STEPS.md")
    print("  - 雙 bot：@BotFather /newbot 兩次；主副 .env 各填 TELEGRAM_BOT_TOKEN")
    print("  - 主模型：hermes model  或  hermes auth add openai-codex / xai-oauth")
    print("  - OpenRouter／Agnes：已登入 Chrome+CDP 自取 key → 寫 .env（API_KEYS_BROWSER.md）")
    print("  - fallback：開 https://openrouter.ai/apps/hermes-agent 抓前 10 → fallback_providers")
    print("  - 自啟／禁休眠：MANUAL_STEPS.md（Linux/macOS/Windows 指令）")
    print("  - CDP：固定 user-data-dir + --remote-debugging-port=9222（禁無痕）")
    print("  - 做完再跑：python3 ~/.hermes/skills/hermes-tw-setup/scripts/baseline.py check")

    print("\n=== apply 後重新 check ===\n")
    report = run_check()
    print_report(report)


def main() -> None:
    ap = argparse.ArgumentParser(description="hermes-tw-setup baseline check/apply")
    ap.add_argument("command", choices=["check", "apply"])
    ap.add_argument("--yes", action="store_true", help="apply 時確認執行")
    ap.add_argument(
        "--hermes-home",
        default="",
        help="覆寫 HERMES_HOME（預設 ~/.hermes）",
    )
    ap.add_argument(
        "--docker",
        default="",
        help="Docker 容器名（例 hermes-demo）。資料目錄預設 ~/.hermes-demo，並改以容器驗證 gateway／provider",
    )
    ap.add_argument(
        "--docker-data",
        default="",
        help="Docker 綁定的主機資料目錄（預設：容器名 hermes-demo → ~/.hermes-demo）",
    )
    args = ap.parse_args()
    global HERMES_HOME, SIDE_HOME, DOCKER_CONTAINER
    DOCKER_CONTAINER = (args.docker or os.environ.get("HERMES_TW_DOCKER", "")).strip()
    if args.hermes_home:
        HERMES_HOME = Path(args.hermes_home).expanduser()
    elif DOCKER_CONTAINER:
        if args.docker_data:
            HERMES_HOME = Path(args.docker_data).expanduser()
        elif DOCKER_CONTAINER == "hermes-demo":
            HERMES_HOME = Path.home() / ".hermes-demo"
        else:
            # try docker inspect mount /opt/data
            try:
                fmt = '{{range .Mounts}}{{if eq .Destination "/opt/data"}}{{.Source}}{{end}}{{end}}'
                ins = subprocess.run(
                    ["docker", "inspect", "-f", fmt, DOCKER_CONTAINER],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                src = (ins.stdout or "").strip()
                HERMES_HOME = Path(src) if src else Path.home() / f".{DOCKER_CONTAINER}"
            except Exception:
                HERMES_HOME = Path.home() / f".{DOCKER_CONTAINER}"
    SIDE_HOME = HERMES_HOME / "profiles" / SIDE_NAME
    os.environ["HERMES_HOME"] = str(HERMES_HOME)
    if isolated():
        os.environ["HERMES_TW_ISOLATED"] = "1"
    else:
        os.environ.pop("HERMES_TW_ISOLATED", None)

    if args.command == "check":
        report = run_check()
        print_report(report)
        sys.exit(0 if report.fail_count() == 0 else 1)
    else:
        run_apply(yes=args.yes)


if __name__ == "__main__":
    main()
