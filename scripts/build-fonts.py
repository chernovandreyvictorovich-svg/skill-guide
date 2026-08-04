#!/usr/bin/env python3
"""
build-fonts.py — вшивает woff2 из assets/fonts/ в assets/fonts.css как data-URI.

Шрифты: JetBrains Mono (моно) + IBM Plex Sans (текст), веса 400/600,
подмножества latin + cyrillic (русский). Источник — fontsource (jsDelivr).
Работает офлайн, без CDN. Запуск: python3 scripts/build-fonts.py
"""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
OUT = ROOT / "assets" / "fonts.css"

# (family, weight, файл, unicode-range)
CYR = "U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116"
LAT = "U+0000-00FF,U+0131,U+0152-0153,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215"
FACES = [
    # Lora — сериф-заголовки (издательский стиль)
    ("Lora", 500, "lora-latin-500.woff2", LAT),
    ("Lora", 500, "lora-cyr-500.woff2", CYR),
    ("Lora", 600, "lora-latin-600.woff2", LAT),
    ("Lora", 600, "lora-cyr-600.woff2", CYR),
    ("Lora", 700, "lora-latin-700.woff2", LAT),
    ("Lora", 700, "lora-cyr-700.woff2", CYR),
    # Manrope — основной текст
    ("Manrope", 400, "man-latin-400.woff2", LAT),
    ("Manrope", 400, "man-cyr-400.woff2", CYR),
    ("Manrope", 500, "man-latin-500.woff2", LAT),
    ("Manrope", 500, "man-cyr-500.woff2", CYR),
    ("Manrope", 600, "man-latin-600.woff2", LAT),
    ("Manrope", 600, "man-cyr-600.woff2", CYR),
    ("Manrope", 700, "man-latin-700.woff2", LAT),
    ("Manrope", 700, "man-cyr-700.woff2", CYR),
    # JetBrains Mono — код-идентификаторы и метки
    ("JetBrains Mono", 400, "jbm-latin-400.woff2", LAT),
    ("JetBrains Mono", 400, "jbm-cyr-400.woff2", CYR),
    ("JetBrains Mono", 600, "jbm-latin-600.woff2", LAT),
    ("JetBrains Mono", 600, "jbm-cyr-600.woff2", CYR),
]


def main():
    blocks = ["/* Вшитые шрифты — сгенерировано build-fonts.py. Офлайн, без CDN. */"]
    for family, weight, fname, urange in FACES:
        p = FONTS / fname
        if not p.exists():
            print(f"[warn] нет {fname}")
            continue
        b64 = base64.b64encode(p.read_bytes()).decode()
        blocks.append(
            f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weight};"
            f"font-display:swap;src:url(data:font/woff2;base64,{b64}) format('woff2');"
            f"unicode-range:{urange};}}"
        )
    OUT.write_text("\n".join(blocks))
    print(f"[ok] {OUT}  ({OUT.stat().st_size // 1024} KB, {len(FACES)} начертаний)")


if __name__ == "__main__":
    main()
