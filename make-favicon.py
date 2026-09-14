#!/usr/bin/env python3
"""Фавиконки сайта: своё эмодзи на каждый раздел.

Берём картинки прямо из системного шрифта Apple Color Emoji — это ровно те начертания,
что на айфоне, без пересъёмки со скриншотов.

Запуск:  python3 make-favicon.py
Деплой:  rsync -az assets/icons/ roschupka:public_html/

⚠️ Рендерить эмодзи текстом через PIL нельзя: без библиотеки сложной вёрстки (raqm)
составные последовательности рассыпаются — «программист» превращается в мужчину
и отдельный ноутбук, а тон кожи теряется. Поэтому достаём готовый глиф из таблицы sbix,
где Apple хранит их картинками PNG на 160 пикселей.

Имена глифов: суффикс после точки — тон кожи по Фитцпатрику, .0 базовый (жёлтый),
.1 светлый, дальше темнее.
"""
import io
import os

from fontTools.ttLib import TTCollection
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets", "icons")
FONT = "/System/Library/Fonts/Apple Color Emoji.ttc"

SECTIONS = {
    "blog":      ("u1F468_u1F4BB.1", "программист со светлым тоном кожи"),
    "portfolio": ("u1F977.0",        "ниндзя"),
    "generator": ("u1F916",          "робот"),
}

PAD = 0.04   # эмодзи и так с полями внутри картинки, добавляем чуть-чуть


def square(art, size, bg=None):
    """Вписывает эмодзи в квадрат. bg=None — прозрачный фон."""
    canvas = Image.new("RGBA", (size, size), (*bg, 255) if bg else (0, 0, 0, 0))
    box = round(size * (1 - PAD * 2))
    scaled = art.resize((box, box), Image.LANCZOS)
    canvas.paste(scaled, ((size - box) // 2, (size - box) // 2), scaled)
    return canvas


def main():
    font = TTCollection(FONT).fonts[0]
    strike = max(font["sbix"].strikes.values(), key=lambda s: s.ppem)
    os.makedirs(OUT, exist_ok=True)

    for slug, (glyph, title) in SECTIONS.items():
        art = Image.open(io.BytesIO(strike.glyphs[glyph].imageData)).convert("RGBA")
        square(art, 32).save(os.path.join(OUT, f"{slug}-32.png"))
        square(art, 192).save(os.path.join(OUT, f"{slug}-192.png"))
        # ⚠️ iOS не умеет прозрачность в иконке — подкладываем белый.
        square(art, 180, bg=(255, 255, 255)).save(os.path.join(OUT, f"{slug}-apple.png"))
        square(art, 64).save(os.path.join(OUT, f"{slug}.ico"),
                             sizes=[(16, 16), (32, 32), (48, 48)])
        print(f"{slug}: {title}")

    # В корне лежит запасная иконка для тех, кто ищет /favicon.ico вслепую.
    # Главная страница сайта — блог, значит она блоговая.
    blog = Image.open(io.BytesIO(strike.glyphs[SECTIONS["blog"][0]].imageData)).convert("RGBA")
    square(blog, 64).save(os.path.join(OUT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])

    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print(f"\nфайлов: {len(os.listdir(OUT))}, всего {total / 1024:.0f} КБ")
    print("дальше: rsync -az assets/icons/ roschupka:public_html/")


if __name__ == "__main__":
    main()
