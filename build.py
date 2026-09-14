#!/usr/bin/env python3
"""Сборка темы Эгеи и статических страниц из локальных исходников.

Склеивает fonts.css + tokens.css + base.css в один styles/main.css,
копирует шрифты и пишет theme-info.php. Результат — папка theme/roschupka,
которую можно целиком положить в system/themes/ на сервере.

Запуск:  python3 build.py
"""
import datetime
import hashlib
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_CSS = os.path.join(ROOT, "assets", "css")
SRC_FONTS = os.path.join(ROOT, "assets", "fonts")
SRC_IMG = os.path.join(ROOT, "assets", "img")
SRC_HEADER = os.path.join(ROOT, "assets", "header.html")
SRC_NAV = os.path.join(ROOT, "assets", "nav.html")
SRC_EXTRAS = os.path.join(ROOT, "assets", "extras")
OUT_THEME = os.path.join(ROOT, "theme", "roschupka")
OUT_SITE = os.path.join(ROOT, "site")
OUT_EXTRAS = os.path.join(ROOT, "extras")

# Порядок важен: шрифты, потом токены, потом правила поверх plain.
PARTS = ["fonts.css", "tokens.css", "base.css"]

THEME_INFO = """<?php return array (

  'index' => 4,

  'display_name' => array (
    'en' => 'Roschupka',
    'ru' => 'Рощупка',
  ),

  'colors' => array (
    'background' => '#ffffff',
    'headings' => '#464848',
    'text' => '#333333',
    'link' => '#0060a0',
  ),

  'based_on' => 'plain',
  'meta_viewport' => 'width=device-width, initial-scale=1',
  'supports_dark_mode' => false,

); ?>
"""


def stamp_images(css):
    """Дописывает к картинкам в CSS отпечаток содержимого: url('../img/x.svg?v=1a2b3c4d').

    Без этого браузер продолжает показывать старый файл под тем же именем — на этом
    уже попадались: перерисованный мазок приехал на сервер, а на экране остался прежний.
    """
    def repl(m):
        rel = m.group("path")
        src = os.path.join(SRC_IMG, os.path.basename(rel))
        if not os.path.isfile(src):
            return m.group(0)
        with open(src, "rb") as f:
            stamp = hashlib.md5(f.read()).hexdigest()[:8]
        return f"url('{rel}?v={stamp}')"

    return re.sub(r"url\('(?P<path>\.\./img/[^']+)'\)", repl, css)


def build_css(parts):
    """Склеивает части в один файл и помечает картинки отпечатком."""
    chunks = [
        "/* СОБРАНО АВТОМАТИЧЕСКИ, правки здесь затрутся следующей сборкой.\n"
        "\n"
        "   Исходники: assets/css/" + ", assets/css/".join(parts) + "\n"
        "   Сборка:    python3 build.py\n"
        "\n"
        "   Почему устроено именно так — references/decisions.md\n"
        "   Как размечать тексты        — references/spec.md */\n"
    ]
    for name in parts:
        chunks.append(f"\n\n/* ═══════════ {name} ═══════════ */\n\n")
        chunks.append(open(os.path.join(SRC_CSS, name), encoding="utf-8").read())
    return stamp_images("".join(chunks))


def put_assets(dst, css):
    """Кладёт рядом со страницей её стили, шрифты и картинки.

    Шрифты дублируются в каждую цель сборки — пока целей две, это дешевле общей папки
    с путями наружу. Появится третья — вынесем в /assets/.
    """
    os.makedirs(os.path.join(dst, "styles"), exist_ok=True)
    open(os.path.join(dst, "styles", "main.css"), "w", encoding="utf-8").write(css)
    shutil.copytree(SRC_FONTS, os.path.join(dst, "fonts"))
    if os.path.isdir(SRC_IMG):
        shutil.copytree(SRC_IMG, os.path.join(dst, "img"))


def nav_html(slug):
    """Меню сайта с пометкой текущего раздела.

    Источник один на весь сайт — assets/nav.html. Раздел определяется по адресу:
    пункт, ведущий на /slug/, и есть текущий. Благодаря этому пункты не могут
    разъехаться между блогом и статическими страницами — они физически одни и те же.
    """
    html = open(SRC_NAV, encoding="utf-8").read()
    # Комментарий в исходнике — записка для себя, читателю страницы он ни к чему.
    html = re.sub(r"<!--.*?-->\s*", "", html, flags=re.S).strip()
    return re.sub(rf'(<a href="/{slug}/")', r'\1 class="is-current"', html)


def header_html(slug):
    """Шапка статической страницы: обвязка из assets/header.html плюс общее меню."""
    html = open(SRC_HEADER, encoding="utf-8").read()
    html = re.sub(r"<!--(?!#nav-->).*?-->\s*", "", html, flags=re.S).strip()
    return html.replace("<!--#nav-->", nav_html(slug))


def build_extras():
    """Расширения Эгеи: копия папки assets/extras с подстановкой меню.

    Слот header-post — единственный, куда меню попадает; остальные файлы едут как есть.
    """
    if os.path.isdir(OUT_EXTRAS):
        shutil.rmtree(OUT_EXTRAS)
    shutil.copytree(SRC_EXTRAS, OUT_EXTRAS)

    header = os.path.join(OUT_EXTRAS, "header-post.tmpl.php")
    php = open(header, encoding="utf-8").read().replace("<!--#nav-->", nav_html("blog"))
    open(header, "w", encoding="utf-8").write(php)


def build_theme():
    if os.path.isdir(OUT_THEME):
        shutil.rmtree(OUT_THEME)
    css = build_css(PARTS)
    put_assets(OUT_THEME, css)
    open(os.path.join(OUT_THEME, "theme-info.php"), "w", encoding="utf-8").write(THEME_INFO)
    return css


def build_page(slug, parts):
    src = os.path.join(ROOT, "pages", slug, "index.html")
    dst = os.path.join(OUT_SITE, slug)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)

    css = build_css(parts)
    put_assets(dst, css)

    # Отпечаток стилей в ссылке — иначе браузер держит старый файл под тем же именем.
    # Теме это не нужно: там метку ставит сама Эгея, а статическую страницу никто не метит.
    stamp = hashlib.md5(css.encode("utf-8")).hexdigest()[:8]

    page = (open(src, encoding="utf-8").read()
            .replace("<!--#header-->", header_html(slug))
            .replace("<!--#year-->", str(datetime.date.today().year))
            .replace('href="styles/main.css"', f'href="styles/main.css?v={stamp}"'))
    open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(page)
    return css


def weight(path):
    return sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, fs in os.walk(path) for f in fs
    ) / 1024


def main():
    theme_css = build_theme()
    print(f"тема:      {OUT_THEME}")
    print(f"  main.css: {len(theme_css) / 1024:.0f} КБ, всего {weight(OUT_THEME):.0f} КБ")

    page_css = build_page("gradient-generator", PARTS + ["gradient.css"])
    print(f"страница:  {os.path.join(OUT_SITE, 'gradient-generator')}")
    print(f"  main.css: {len(page_css) / 1024:.0f} КБ, всего {weight(OUT_SITE):.0f} КБ")

    build_extras()
    print(f"расширения: {OUT_EXTRAS}")
    print(f"  {len(os.listdir(OUT_EXTRAS))} файла, {weight(OUT_EXTRAS):.0f} КБ")


if __name__ == "__main__":
    main()
