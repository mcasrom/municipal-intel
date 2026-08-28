#!/usr/bin/env python3
"""via_mivau_health.py - Verifica que el backfill semanal MIVAU (via_mivau) y la
regeneracion de la pagina de alquiler no hayan fallado.

Detecta DOS fallos de la cadena semanal (dom 06:40):
  1. Frustracion de via_mivau: el log logs_via_mivau.log contiene Traceback/ERROR.
  2. Pagina stale: dashboard/alquiler.html no se regenera desde hace MAX_AGE_DAYS
     (el cron encadena via_mivau && gen_alquiler_page; si via_mivau falla o el cron
     no corre, la pagina queda vieja).

Alerta por Telegram SOLO cuando se detecta la condicion de fallo (con dedup por mtime
ya notificado, para no spamear la misma condicion semanas seguidas). Sin fallo -> OK.
Uso en cron: 5 7 * * 0 cd /home/deploy/municipal-intel && python3 scripts/via_mivau_health.py
"""
import os
import sys
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # municipal-intel
LOG = os.path.join(REPO, "logs_via_mivau.log")
PAGE = os.path.join(REPO, "dashboard", "alquiler.html")
STATE = os.path.join(REPO, "logs", "via_mivau_health.state")
MAX_AGE_DAYS = 8  # cron semanal; avisamos si la pagina lleva >8 dias sin regenerarse
TELEGRAM_ENV = "/home/deploy/nearme-osint/.env"


def age_of(path):
    try:
        return time.time() - os.path.getmtime(path)
    except OSError:
        return None


def _load_tg_env():
    token = chat = None
    try:
        for line in open(TELEGRAM_ENV):
            line = line.strip()
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip()
            elif line.startswith("TELEGRAM_CHAT_ID="):
                chat = line.split("=", 1)[1].strip()
    except OSError:
        pass
    return token, chat


def telegram_send(text):
    token, chat = _load_tg_env()
    if not token or not chat:
        return False
    try:
        url = "https://api.telegram.org/bot%s/sendMessage" % token
        data = urllib.parse.urlencode({
            "chat_id": chat, "text": text,
            "disable_web_page_preview": "true",
        }).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print("telegram send fallo: %s" % e)
        return False


def read_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {}


def write_state(state):
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print("no se pudo escribir state: %s" % e)


def main():
    problems = []

    page_age = age_of(PAGE)
    if page_age is None:
        problems.append("alquiler.html NO existe")
    elif page_age > MAX_AGE_DAYS * 86400:
        problems.append("alquiler.html no se regenera hace %.1f dias (cron semanal fallo?" % (page_age / 86400))

    log_fail = False
    if os.path.exists(LOG):
        try:
            with open(LOG, encoding="utf-8", errors="replace") as f:
                content = f.read()
            if "Traceback" in content or "\nERROR" in content or "\nError" in content:
                log_fail = True
                problems.append("logs_via_mivau.log contiene un error (Traceback/ERROR)")
        except OSError:
            pass

    if not problems:
        print("[%s] OK via_mivau" % datetime.now(timezone.utc).isoformat())
        write_state({})
        return 0

    # dedup: notificar una vez por CONDICION concreta y estable (no por edad en segundos,
    # que cambia cada ejecucion). base la clave en mtime del log de error o de la pagina.
    log_mtime = os.path.getmtime(LOG) if os.path.exists(LOG) else None
    page_mtime = os.path.getmtime(PAGE) if page_age is not None else None
    if "Traceback" in (open(LOG, encoding="utf-8", errors="replace").read() if os.path.exists(LOG) else "") :
        key = "log:%s" % log_mtime
    elif page_age is None:
        key = "page-missing"
    else:
        key = "page:%s" % page_mtime
    state = read_state()
    if state.get("notified_key") == key:
        print("[%s] fallo ya notificado, skip" % datetime.now(timezone.utc).isoformat())
        return 0

    text = "⚠️ municipal-intel: verificación semanal via_mivau\n- " + "\n- ".join(problems)
    ok = telegram_send(text)
    write_state({"notified_key": key, "at": datetime.now(timezone.utc).isoformat()})
    print("[%s] %s %s" % (datetime.now(timezone.utc).isoformat(), "ENVIADO" if ok else "NODEDUP", " | ".join(problems)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
