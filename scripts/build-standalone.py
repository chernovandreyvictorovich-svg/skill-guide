#!/usr/bin/env python3
"""
build-standalone.py — собирает самодостаточный файл для публикации онлайн (артефакт).

Берёт index.html + data/skills-data.js, инлайнит данные внутрь и пишет:
  dist/skill-guide.html         — полный standalone (можно открыть где угодно локально)
  dist/skill-guide.fragment.html — фрагмент для Artifact (без doctype/html/head/body)

Запуск: python3 scripts/generate.py && python3 scripts/build-standalone.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)

html = (ROOT / "index.html").read_text()
data = (ROOT / "data" / "skills-data.js").read_text()
fonts = (ROOT / "assets" / "fonts.css").read_text()

# инлайним шрифты вместо <link rel="stylesheet" href="assets/fonts.css">
inlined = re.sub(
    r'<link rel="stylesheet" href="assets/fonts\.css">',
    f"<style>\n{fonts}\n</style>",
    html,
)
# инлайним данные вместо <script src="data/skills-data.js">
inlined = re.sub(
    r'<script src="data/skills-data\.js"></script>',
    f"<script>\n{data}\n</script>",
    inlined,
)

(DIST / "skill-guide.html").write_text(inlined)

# фрагмент для Artifact: все <style>…</style> из head + всё между <body>…</body>
styles = "\n".join(re.findall(r"<style>.*?</style>", inlined, re.S))
body = re.search(r"<body>(.*?)</body>", inlined, re.S).group(1)
fragment = styles + "\n" + body
(DIST / "skill-guide.fragment.html").write_text(fragment)

print(f"[ok] dist/skill-guide.html ({len(inlined)//1024} KB)")
print(f"[ok] dist/skill-guide.fragment.html ({len(fragment)//1024} KB)")
