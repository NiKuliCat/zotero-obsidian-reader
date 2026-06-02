#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = WORKSPACE_ROOT / ".zotero-obsidian-reader.json"
LEGACY_CONFIG_PATH = WORKSPACE_ROOT / ".codex" / "zotero-obsidian-reader.json"


def load_config() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    if LEGACY_CONFIG_PATH.exists():
        return json.loads(LEGACY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    return {}


def save_config(config: dict[str, Any]) -> Path:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return CONFIG_PATH


def discover_obsidian_vaults(root: Path | None = None) -> list[Path]:
    search_root = root or WORKSPACE_ROOT
    vaults = []
    for dot_obsidian in search_root.rglob(".obsidian"):
        if dot_obsidian.is_dir():
            vaults.append(dot_obsidian.parent)
    return sort_vault_candidates(vaults)


def discover_zotero_dirs(root: Path | None = None) -> list[Path]:
    search_root = root or WORKSPACE_ROOT
    candidates = []

    for db_name in ("zotero.sqlite", "zotero.sqlite.bak"):
        for db_file in search_root.rglob(db_name):
            if db_file.is_file():
                candidates.append(db_file.parent)

    return sort_zotero_candidates(candidates)


def sort_vault_candidates(vaults: list[Path]) -> list[Path]:
    def score(path: Path) -> tuple[int, int, str]:
        parts_lower = [part.lower() for part in path.parts]
        note_bias = 0 if "note" in parts_lower else 1
        return (note_bias, len(path.parts), str(path).lower())

    seen = set()
    ordered = []
    for vault in sorted(vaults, key=score):
        text = str(vault).lower()
        if text not in seen:
            ordered.append(vault)
            seen.add(text)
    return ordered


def sort_zotero_candidates(paths: list[Path]) -> list[Path]:
    def score(path: Path) -> tuple[int, int, int, int, int, str]:
        has_sqlite = 0 if (path / "zotero.sqlite").exists() else 1
        has_storage = 0 if (path / "storage").exists() else 1
        has_better_bibtex = 0 if (path / "better-bibtex").exists() else 1
        has_translators = 0 if (path / "translators").exists() else 1
        return (
            has_sqlite,
            has_storage,
            has_better_bibtex,
            has_translators,
            len(path.parts),
            str(path).lower(),
        )

    seen = set()
    ordered = []
    for candidate in sorted(paths, key=score):
        text = str(candidate).lower()
        if text not in seen:
            ordered.append(candidate)
            seen.add(text)
    return ordered


def bootstrap_discovered_config(**updates: Any) -> Path:
    config = load_config()
    merged = {
        "vault_dir": config.get("vault_dir", ""),
        "zotero_dir": config.get("zotero_dir", ""),
        "paper_relative_dir": config.get("paper_relative_dir", ""),
        "synthesis_relative_dir": config.get("synthesis_relative_dir", ""),
        "paper_filename_suffix": config.get("paper_filename_suffix", ""),
        "synthesis_filename_suffix": config.get("synthesis_filename_suffix", ""),
        "research_domain": config.get("research_domain", ""),
        "research_focus": config.get("research_focus", ""),
        "research_keywords": config.get("research_keywords", []),
    }
    for key, value in updates.items():
        merged[key] = value
    return save_config(merged)


def detect_vault_dir(explicit: Path | None = None) -> Path:
    if explicit:
        return explicit

    config = load_config()
    configured = config.get("vault_dir")
    if configured:
        path = Path(configured)
        if path.exists():
            return path

    vaults = discover_obsidian_vaults()
    if not vaults:
        raise FileNotFoundError(
            "Could not find an Obsidian vault. Add .zotero-obsidian-reader.json with vault_dir or create a vault under the workspace."
        )
    selected = vaults[0]
    bootstrap_discovered_config(vault_dir=str(selected))
    return selected


def detect_zotero_dir(explicit: Path | None = None) -> Path:
    if explicit:
        return explicit

    config = load_config()
    configured = config.get("zotero_dir")
    if configured:
        path = Path(configured)
        if path.exists():
            return path

    candidates = discover_zotero_dirs()
    if not candidates:
        raise FileNotFoundError(
            "Could not find a Zotero data directory. Add .zotero-obsidian-reader.json with zotero_dir or place Zotero data under the workspace."
        )
    selected = candidates[0]
    bootstrap_discovered_config(zotero_dir=str(selected))
    return selected


def default_relative_dir(mode: str, config: dict[str, Any] | None = None) -> str:
    cfg = config or load_config()
    key = f"{mode}_relative_dir"
    value = cfg.get(key)
    if isinstance(value, str):
        return value.strip()
    return ""


def default_filename_suffix(mode: str, config: dict[str, Any] | None = None) -> str:
    cfg = config or load_config()
    key = f"{mode}_filename_suffix"
    value = cfg.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    if mode == "paper":
        return "_精读笔记"
    if mode == "synthesis":
        return "_综述"
    return ""


def get_research_profile(config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or load_config()
    keywords = cfg.get("research_keywords", [])
    if not isinstance(keywords, list):
        keywords = []
    return {
        "domain": str(cfg.get("research_domain", "") or "").strip(),
        "focus": str(cfg.get("research_focus", "") or "").strip(),
        "keywords": [str(keyword).strip() for keyword in keywords if str(keyword).strip()],
    }


def has_research_profile(config: dict[str, Any] | None = None) -> bool:
    profile = get_research_profile(config)
    return bool(profile["domain"])


def update_research_profile(domain: str, focus: str = "", keywords: list[str] | None = None) -> Path:
    cleaned_keywords = [keyword.strip() for keyword in (keywords or []) if keyword.strip()]
    return bootstrap_discovered_config(
        research_domain=domain.strip(),
        research_focus=focus.strip(),
        research_keywords=cleaned_keywords,
    )
