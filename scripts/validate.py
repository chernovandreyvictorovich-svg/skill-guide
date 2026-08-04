#!/usr/bin/env python3
"""
validate.py — проверка целостности курируемых данных (для CI и локально).

Что проверяет:
  • data/overrides.json — валидный JSON; есть categories[] и skills{}; у каждой
    категории id/emoji/title/desc; у каждого скилла cat ссылается на существующую
    категорию (или отсутствует).
  • data/links.json — валидный JSON с полем urls{}.

Выход: код 0 — всё ок; код 1 — есть ошибки (CI падает). Запуск: python3 scripts/validate.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []


def load(path):
    try:
        return json.loads((ROOT / path).read_text())
    except Exception as e:
        errors.append(f"{path}: не парсится как JSON — {e}")
        return None


def main():
    ov = load("data/overrides.json")
    if ov is not None:
        cats = ov.get("categories")
        skills = ov.get("skills")
        if not isinstance(cats, list) or not cats:
            errors.append("overrides.json: 'categories' должен быть непустым списком")
            cats = []
        if not isinstance(skills, dict):
            errors.append("overrides.json: 'skills' должен быть объектом")
            skills = {}

        cat_ids = set()
        for i, c in enumerate(cats):
            for k in ("id", "emoji", "title", "desc"):
                if not c.get(k):
                    errors.append(f"overrides.json: category[{i}] без поля '{k}'")
            if c.get("id"):
                if c["id"] in cat_ids:
                    errors.append(f"overrides.json: дублируется category id '{c['id']}'")
                cat_ids.add(c["id"])
        cat_ids.add("new")  # служебный бакет — всегда валиден

        for name, s in skills.items():
            if not isinstance(s, dict):
                errors.append(f"overrides.json: skill '{name}' не объект")
                continue
            cat = s.get("cat")
            if cat and cat not in cat_ids:
                errors.append(f"overrides.json: skill '{name}' ссылается на несуществующую категорию '{cat}'")
            if s.get("builtin") and not s.get("desc"):
                errors.append(f"overrides.json: builtin-скилл '{name}' без описания")

    links = load("data/links.json")
    if links is not None and not isinstance(links.get("urls"), dict):
        errors.append("links.json: поле 'urls' должно быть объектом")

    if errors:
        print("❌ Валидация не прошла:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"✓ Валидация ок: {len(ov.get('categories', []))} категорий, {len(ov.get('skills', {}))} скиллов")


if __name__ == "__main__":
    main()
