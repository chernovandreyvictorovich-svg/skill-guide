#!/usr/bin/env python3
"""
usage-scan.py — считает, сколько раз каждый скилл реально вызывали.

Источники:
  Claude Code: ~/.claude/projects/**/*.jsonl  — вызовы инструмента Skill:
               "name":"Skill","input":{"skill":"X"}
  Codex:       ~/.codex/{sessions,archived_sessions}/**/*.jsonl — активации скиллов
               (best-effort; фильтр по реальным именам из каталога, чтобы отсечь заглушки)

Честная оговорка: считаются ЯВНЫЕ вызовы через инструмент. Скиллы, срабатывающие
сами по описанию, и часть чистых /-команд сюда не попадут — это «сколько раз позвал явно».

Пишет: data/usage.json  ->  { "имя-скилла": число, ... , "_meta": {...} }
Запуск: python3 scripts/usage-scan.py
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "usage.json"
SKILLS_JS = DATA / "skills-data.js"

CLAUDE_LOGS = HOME / ".claude" / "projects"
CODEX_LOGS = [HOME / ".codex" / "sessions", HOME / ".codex" / "archived_sessions"]


def catalog_names() -> set:
    """Имена скиллов из уже собранного каталога — фильтр против мусора/заглушек."""
    if not SKILLS_JS.exists():
        return set()
    m = re.search(r"window\.SKILLS = (\[.*?\]);\nwindow", SKILLS_JS.read_text(), re.S)
    if not m:
        return set()
    try:
        return {s["name"] for s in json.loads(m.group(1))}
    except Exception:
        return set()


def bare(name: str) -> str:
    """superpowers:brainstorming -> brainstorming"""
    return name.split(":")[-1].strip()


# Claude: инструмент Skill
# не зависим от порядка ключей внутри "input": допускаем любые ключи до "skill"
RE_CLAUDE = re.compile(r'"name"\s*:\s*"Skill"\s*,\s*"input"\s*:\s*\{[^{}]*?"skill"\s*:\s*"([^"]+)"')
# Codex/прочее: любое "skill":"X" или "skill_name":"X"
RE_SKILL = re.compile(r'"skill(?:_name)?"\s*:\s*"([a-zA-Z0-9:_-]+)"')


def scan_dir(root: Path, regex, names_filter=None):
    counts = defaultdict(int)
    files = 0
    if not root.exists():
        return counts, files
    for f in root.rglob("*.jsonl"):
        files += 1
        try:
            text = f.read_text(errors="ignore")
        except Exception:
            continue
        for m in regex.finditer(text):
            n = bare(m.group(1))
            if names_filter is not None and n not in names_filter:
                continue
            counts[n] += 1
    return counts, files


def main():
    names = catalog_names()
    total = defaultdict(int)

    # Claude — надёжно (инструмент Skill), фильтр по каталогу не обязателен, но чистит шум
    c_counts, c_files = scan_dir(CLAUDE_LOGS, RE_CLAUDE, names_filter=names or None)
    for k, v in c_counts.items():
        total[k] += v

    # Codex — best-effort, ЖЁСТКИЙ фильтр по реальным именам (иначе ловит "skillname" и т.п.)
    x_files = 0
    x_total = 0
    for d in CODEX_LOGS:
        x_counts, xf = scan_dir(d, RE_SKILL, names_filter=names)
        x_files += xf
        for k, v in x_counts.items():
            total[k] += v
            x_total += v

    out = dict(sorted(total.items(), key=lambda kv: -kv[1]))
    out["_meta"] = {
        "claudeFiles": c_files,
        "codexFiles": x_files,
        "codexHits": x_total,
        "note": "явные вызовы через инструмент Skill/activate_skill; авто-срабатывания не учтены",
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))

    top = [(k, v) for k, v in out.items() if not k.startswith("_")][:12]
    print(f"[ok] логов: Claude {c_files} · Codex {x_files} (совпадений в Codex: {x_total})")
    print(f"[ok] скиллов с вызовами: {len([k for k in out if not k.startswith('_')])}")
    print("[top] " + ", ".join(f"{k}×{v}" for k, v in top))
    print(f"[ok] записано -> {OUT}")


if __name__ == "__main__":
    main()
