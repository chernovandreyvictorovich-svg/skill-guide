#!/usr/bin/env python3
"""
serve.py — локальный сервер для Skill-Guide с рабочими кнопками управления.

Статичная страница (file:// или онлайн-артефакт) НЕ может запускать команды на твоём
компьютере — браузер это запрещает. Этот сервер работает в твоём терминале (доступ к
файлам есть), отдаёт гид на localhost и даёт странице endpoints:
  GET  /api/ping         -> «живой» режим (страница показывает кнопки)
  POST /api/update       -> запускает «Обновить всё» в фоне, возвращает сразу
  GET  /api/update-log   -> живой лог процесса (страница опрашивает и показывает)

Слушает ТОЛЬКО 127.0.0.1. Запуск:
  python3 serve.py           (http://127.0.0.1:8777)
  python3 serve.py 9000      (свой порт)
"""
import json
import re
import secrets
import subprocess
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8777
HOME = Path.home()

# состояние текущего обновления (виден странице через /api/update-log)
UPD = {"running": False, "lines": [], "done": False, "ok": None, "updatable": None}
_LOCK = threading.Lock()
# одноразовый токен сессии: страница читает его из /api/ping (same-origin) и шлёт в /api/update.
# Чужой сайт не сможет прочитать токен (CORS) — защита от CSRF/DNS-rebinding вместе с Host-check.
TOKEN = secrets.token_urlsafe(18)


def _emit(line):
    UPD["lines"].append(line)


def _run_stream(cmd):
    """Запускает команду, построчно кладёт вывод в лог. True если успех."""
    try:
        p = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in p.stdout:
            _emit(line.rstrip("\n"))
        p.wait()
        return p.returncode == 0
    except Exception as e:
        _emit(f"ошибка: {e}")
        return False


def updatable_count():
    try:
        js = (ROOT / "data" / "skills-data.js").read_text()
        m = re.search(r"window\.SKILLS_META = (\{.*?\});", js, re.S)
        if m:
            return json.loads(m.group(1)).get("counts", {}).get("updatable", 0)
    except Exception:
        pass
    return None


def do_update_thread():
    try:
        _emit("→ Обновляю gstack (git pull)…")
        gstack = HOME / ".claude" / "skills" / "gstack"
        if (gstack / ".git").exists():
            _run_stream(["git", "-C", str(gstack), "pull", "--ff-only"])
        else:
            _emit("  gstack не найден — пропускаю")

        _emit("→ Обновляю витрины плагинов (git pull)…")
        markets = HOME / ".claude" / "plugins" / "marketplaces"
        if markets.exists():
            for mp in sorted(markets.glob("*")):
                if (mp / ".git").exists():
                    _emit(f"  • {mp.name}")
                    _run_stream(["git", "-C", str(mp), "pull", "--ff-only"])

        _emit("→ Проверяю версии заново (git fetch, до минуты)…")
        _run_stream([sys.executable, "scripts/check-updates.py"])

        _emit("→ Пересобираю каталог…")
        _run_stream([sys.executable, "scripts/usage-scan.py"])
        ok = _run_stream([sys.executable, "scripts/generate.py"])

        UPD["ok"] = ok
        UPD["updatable"] = updatable_count()
        _emit(f"✓ Готово. Обновлений осталось: {UPD['updatable']}")
    except Exception as e:
        _emit(f"ошибка: {e}")
        UPD["ok"] = False
    finally:
        UPD["done"] = True
        UPD["running"] = False


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")
        if path == "/api/ping":
            return self._json({"ok": True, "mode": "live", "token": TOKEN})
        if path == "/api/update-log":
            qs = parse_qs(urlparse(self.path).query)
            since = int(qs.get("since", ["0"])[0])
            return self._json({
                "lines": UPD["lines"][since:], "total": len(UPD["lines"]),
                "running": UPD["running"], "done": UPD["done"],
                "ok": UPD["ok"], "updatable": UPD["updatable"],
            })
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        if path == "/api/update":
            # анти-CSRF: только localhost-Host + валидный токен сессии
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
            if host not in ("127.0.0.1", "localhost", "::1"):
                return self._json({"ok": False, "error": "bad host"}, 403)
            if self.headers.get("X-SG-Token") != TOKEN:
                return self._json({"ok": False, "error": "forbidden"}, 403)
            with _LOCK:
                if UPD["running"]:
                    return self._json({"running": True})
                UPD.update(running=True, lines=[], done=False, ok=None, updatable=None)
            threading.Thread(target=do_update_thread, daemon=True).start()
            return self._json({"started": True})
        return self._json({"ok": False, "error": "unknown endpoint"}, 404)


def main():
    url = f"http://127.0.0.1:{PORT}/index.html"
    print(f"Skill-Guide живой режим:  {url}")
    print("Кнопка «Обновить всё» теперь показывает живой лог. Ctrl+C — остановить.")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
