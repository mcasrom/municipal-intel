"""Municipal Alert API - avisame si mi municipio cambia. Solo stdlib, sin dependencias.
POST /api/alerta            {"email": "x@y.z", "codigo": "30024"}  -> suscribe (confirma por email)
GET  /api/alerta/confirmar  ?token=...                            -> activa
GET  /api/alerta/baja       ?email=...&codigo=...                 -> da de baja
POST /api/alerta/notificar  (header X-Alert-Secret)               -> envia avisos a activos cuyo dato cambio
Puerto: 8201. Cron de update llama a /notificar tras regenerar.
"""
import json, os, re, sqlite3, secrets, datetime, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = "/home/deploy/municipal-intel"
DB = os.path.join(BASE, "data", "alerts.db")

# cargar data/alerts.env si existe (RESEND_API_KEY, RESEND_FROM, ALERT_SECRET)
_envf = os.path.join(BASE, "data", "alerts.env")
if os.path.exists(_envf):
    for _l in open(_envf):
        _l = _l.strip()
        if "=" in _l and not _l.startswith("#"):
            k, v = _l.split("=", 1)
            os.environ.setdefault(k, v)

RESEND_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM", "Municipal <onboarding@resend.dev>")
SECRET = os.environ.get("ALERT_SECRET", "cambia-me")
PORT = 8201

def db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS alertas (
        email TEXT, codigo TEXT, token TEXT, activo INTEGER DEFAULT 0,
        last_value TEXT, creado TEXT DEFAULT (datetime('now')),
        PRIMARY KEY(email, codigo))""")
    return con

def send_email(to, subject, html):
    if not RESEND_KEY:
        return False
    body = json.dumps({"from": RESEND_FROM, "to": [to], "subject": subject, "html": html}).encode()
    req = urllib.request.Request("https://api.resend.com/emails", data=body, method="POST",
        headers={"Authorization": "Bearer " + RESEND_KEY, "Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 municipal-alert-api/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception:
        return False

def valor_actual(codigo):
    """Valor actual del municipio para detectar cambios (poblacion 2025, y contratos para Lorca)."""
    try:
        con = sqlite3.connect(os.path.join(BASE, "data", "poblacion_municipal.sqlite"))
        r = con.execute("SELECT p.poblacion FROM poblacion p JOIN catalogo c USING(provincia, municipio) "
                        "WHERE c.codigo_ine=? AND p.anyo=2025 AND p.sexo='Total'", (codigo,)).fetchone()
        con.close()
        v = str(int(r[0])) if r else "0"
    except Exception:
        v = "0"
    if codigo == "30024":  # Lorca: anadir numero de contratos menores (cambia cada trimestre)
        try:
            n = sum(1 for _ in open(os.path.join(BASE, "lorca_menores.json"), "r"))
            v += "/" + str(n)
        except Exception:
            pass
    return v

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        return json.loads(self.rfile.read(n).decode()) if n else {}
    def do_POST(self):
        if self.path == "/api/alerta":
            try:
                b = self._body()
                email = (b.get("email") or "").strip().lower()
                codigo = (b.get("codigo") or "").strip()
            except Exception:
                return self._send(400, {"error": "json invalido"})
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                return self._send(400, {"error": "email invalido"})
            if not re.match(r"^\d{5}$", codigo):
                return self._send(400, {"error": "codigo invalido"})
            token = secrets.token_urlsafe(16)
            con = db()
            con.execute("INSERT OR REPLACE INTO alertas(email, codigo, token, activo) VALUES (?,?,?,0)", (email, codigo, token))
            con.commit(); con.close()
            link = "https://municipal.viajeinteligencia.com/api/alerta/confirmar?token=" + token
            send_email(email, "Confirma tu alerta de municipio",
                "<p>Confirma que quieres recibir un aviso cuando cambien los datos de tu municipio:</p>"
                "<p><a href='" + link + "'>Confirmar alerta</a></p>"
                "<p>Si no has sido tú, ignora este email.</p>")
            return self._send(200, {"ok": True, "msg": "Revisa tu email para confirmar"})
        if self.path == "/api/alerta/notificar":
            if self.headers.get("X-Alert-Secret") != SECRET:
                return self._send(401, {"error": "no autorizado"})
            con = db()
            subs = con.execute("SELECT email, codigo, last_value FROM alertas WHERE activo=1").fetchall()
            enviadas = []
            for email, codigo, last in subs:
                cur = valor_actual(codigo)
                if last is None or last != cur:
                    send_email(email, "Cambios en tu municipio",
                        "<p>Los datos de tu municipio (código " + codigo + ") han cambiado.</p>"
                        "<p><a href='https://municipal.viajeinteligencia.com/'>Ver en el mapa</a></p>"
                        "<p><a href='https://municipal.viajeinteligencia.com/api/alerta/baja?email=" + email + "&codigo=" + codigo + "'>Darme de baja</a></p>")
                    con.execute("UPDATE alertas SET last_value=? WHERE email=? AND codigo=?", (cur, email, codigo))
                    enviadas.append(email + "/" + codigo)
            con.commit(); con.close()
            return self._send(200, {"ok": True, "enviadas": enviadas})
        return self._send(404, {"error": "no"})
    def do_GET(self):
        if self.path.startswith("/api/alerta/confirmar"):
            import urllib.parse
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            token = (q.get("token") or [""])[0]
            con = db()
            cur = con.execute("UPDATE alertas SET activo=1, last_value=? WHERE token=? AND activo=0",
                              (valor_actual("00000") if False else None, token))
            con.commit(); changed = cur.rowcount; con.close()
            body = ("<h2>Alerta activada</h2><p>Recibirás un aviso cuando cambien los datos de tu municipio.</p>" if changed
                    else "<h2>Enlace no válido</h2>")
            b = body.encode()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
            return
        if self.path.startswith("/api/alerta/baja"):
            import urllib.parse
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            email = (q.get("email") or [""])[0].lower(); codigo = (q.get("codigo") or [""])[0]
            con = db()
            con.execute("UPDATE alertas SET activo=0 WHERE email=? AND codigo=?", (email, codigo))
            con.commit(); con.close()
            b = b"<h2>Te has dado de baja</h2>"
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
            return
        self._send(404, {"error": "no"})

if __name__ == "__main__":
    print("municipal-alert-api en :" + str(PORT))
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
