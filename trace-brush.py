#!/usr/bin/env python3
"""Перевод нарисованного от руки мазка в вектор для маркера выделения.

Берёт картинку «тёмный штрих на белом», обводит её по верхней и нижней кромке
и кладёт результат в assets/img/brush.svg. Оригинал сохраняется в assets/img-src/.

Запуск:  python3 trace-brush.py ~/Downloads/новый-мазок.png

Почему именно обводка по кромкам, а не трассировка целиком: мазок — сплошная
горизонтальная фигура, и для неё достаточно двух линий. Внутренние просветы при этом
теряются — в первом мазке так пропала щель между двумя проходами маркера. Если
в рисунке будет разрыв по вертикали, два штриха склеятся в один.

Цвет и прозрачность зашиваются в файл: фоновую картинку из CSS не перекрасить,
а маской её не сделать — маска режет вместе с фоном и текст.
"""
import os
import shutil
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_SVG = os.path.join(ROOT, "assets", "img", "brush.svg")
SRC_DIR = os.path.join(ROOT, "assets", "img-src")

BACKGROUND = 238   # ярче этого — бумага, темнее — чернила
INK = 110          # порог чернил при обводке кромки
STEP = 4           # прореживание точек: неровность кромки остаётся, файл легче
COLOR = "#ffd801"
OPACITY = ".7"


def main(src):
    im = Image.open(src)
    alpha = im.getchannel("A") if im.mode in ("RGBA", "LA") else None
    if alpha and min(alpha.getdata()) < 10:
        ink = alpha                      # рисунок уже на прозрачном фоне
    else:
        ink = im.convert("L").point(
            lambda v: 0 if v > BACKGROUND else min(255, round((BACKGROUND - v) * 255 / 190))
        )

    ink = ink.crop(ink.getbbox())
    w, h = ink.size
    px = ink.load()

    tops, bots = {}, {}
    for x in range(w):
        col = [y for y in range(h) if px[x, y] > INK]
        if col:
            tops[x], bots[x] = col[0], col[-1]

    xs = sorted(tops)
    sample = [x for i, x in enumerate(xs) if i % STEP == 0 or x == xs[-1]]
    pts = [(x, tops[x]) for x in sample] + [(x, bots[x]) for x in reversed(sample)]

    d = "M" + " L".join(f"{x} {y}" for x, y in pts) + " Z"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'preserveAspectRatio="none">'
        f'<path d="{d}" fill="{COLOR}" fill-opacity="{OPACITY}"/></svg>'
    )
    open(OUT_SVG, "w", encoding="utf-8").write(svg)

    os.makedirs(SRC_DIR, exist_ok=True)
    kept = os.path.join(SRC_DIR, "brush" + os.path.splitext(src)[1].lower())
    for old in os.listdir(SRC_DIR):
        if old.startswith("brush.") and os.path.join(SRC_DIR, old) != kept:
            os.remove(os.path.join(SRC_DIR, old))
    shutil.copy(src, kept)

    print(f"мазок:     {w}×{h}, пропорция {w / h:.1f}:1")
    print(f"точек:     {len(pts)}")
    print(f"собрано:   {OUT_SVG} ({os.path.getsize(OUT_SVG) / 1024:.1f} КБ)")
    print(f"оригинал:  {kept}")
    print("дальше:    python3 build.py и деплой темы")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("укажи файл: python3 trace-brush.py путь/к/мазку.png")
    main(sys.argv[1])
