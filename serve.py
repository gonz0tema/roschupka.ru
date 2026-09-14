#!/usr/bin/env python3
"""Локальный сервер для работы над темой.

Отдаёт проект по http://localhost:4173/local/post.html
Нужен потому, что стандартный http.server падает на os.getcwd() в песочнице.
"""
import functools
import http.server
import os
import socketserver

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 4173


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Иначе браузер кеширует CSS и после правки показывает старые стили.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        if "404" in (fmt % args):
            super().log_message(fmt, *args)


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), functools.partial(Handler, directory=ROOT)) as httpd:
    print(f"http://localhost:{PORT}/local/post.html")
    httpd.serve_forever()
