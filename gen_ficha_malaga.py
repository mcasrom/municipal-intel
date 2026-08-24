import json, sqlite3, os
from collections import defaultdict

menores = json.load(open("malaga_menores.json"))
DBP = "data/poblacion_municipal.sqlite"
if not os.path.exists(DBP): DBP = "poblacion_municipal.sqlite"
con = sqlite3.connect(DBP)
serie = con.execute("SELECT anyo, poblacion FROM poblacion WHERE municipio='Málaga' AND sexo='Total' ORDER BY anyo").fetchall()
h25 = con.execute("SELECT poblacion FROM poblacion WHERE municipio='Málaga' AND sexo='Hombres' AND anyo=2025").fetchone()
m25 = con.execute("SELECT poblacion FROM poblacion WHERE municipio='Málaga' AND sexo='Mujeres' AND anyo=2025").fetchone()
rank = con.execute("""SELECT COUNT(*)+1 FROM poblacion WHERE anyo=2025 AND sexo='Total' AND poblacion >
  (SELECT poblacion FROM poblacion WHERE municipio='Málaga' AND anyo=2025 AND sexo='Total')""").fetchone()[0]
con.close()

def pct(a, b): return round((a - b) / b * 100, 1) if b else None
def fmt_e(n): return "%s" % format(int(round(n)), ",").replace(",", ".")

# renta y edad (extraidas)
renta = {"neta_persona": 13847, "neta_hogar": 36640, "anyo": 2022}
edad = None  # datos sin trazabilidad eliminados 24/Ago
t_edad = edad["g1"] + edad["g2"] + edad["g3"]

# contratos menores
m = [x for x in menores if x["importe"] and x["importe"] <= 40000]
by = defaultdict(list)
for x in m: by[x["adjudicatario"]].append(x)
top_num = sorted(by.items(), key=lambda kv: -len(kv[1]))[:12]
total_gasto = sum(x["importe"] for x in m)

p96 = serie[0][1]; p25 = serie[-1][1]; var = pct(p25, p96)

row_num = ""
for i, (ad, items) in enumerate(top_num, 1):
    tot = sum(x["importe"] for x in items)
    row_num += "<tr><td>%d</td><td>%s</td><td class='r'><b>%d</b></td><td class='r'>%s €</td><td class='r'>%s €</td></tr>" % (i, ad, len(items), fmt_e(tot), fmt_e(tot/len(items)))

flag = [(ad, len(items)) for ad, items in top_num if len(items) >= 10]
alerta = ""
if flag:
    alerta = ("<div class='alert'><b>Posible troceado:</b> proveedores con un volumen alto de contratos menores en 2024-2026 — " +
              ", ".join("<b>%d</b> a %s" % (n, a) for a, n in flag[:6]) +
              ". Contratos de importe bajo repetidos en el mismo periodo es el patrón clásico de fraccionamiento del gasto.</div>")

edadbar = ('<div style="margin:10px 0"><div style="display:flex;height:18px;border-radius:5px;overflow:hidden">'
           '<div style="width:%.1f%%;background:#38bdf8"></div><div style="width:%.1f%%;background:#6366f1"></div><div style="width:%.1f%%;background:#f87171"></div></div>'
           '<div style="display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;margin-top:4px">'
           '<span>≤15: %.1f%%</span><span>16-64: %.1f%%</span><span>65+: %.1f%%</span></div></div>'
           % (edad["g1"]/t_edad*100, edad["g2"]/t_edad*100, edad["g3"]/t_edad*100, edad["g1"]/t_edad*100, edad["g2"]/t_edad*100, edad["g3"]/t_edad*100))

HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Málaga · Municipal Intelligence</title>
<meta name="description" content="Ficha de inteligencia municipal de Málaga: población INE 1996-2025 y contratos menores del Ayuntamiento (2024-2026) con detección de posibles troceados.">
<link rel="canonical" href="https://municipal.viajeinteligencia.com/ficha_malaga.html">
<link rel="icon" type="image/png" href="icon-192.png">
<style>
:root{--bg:#0f172a;--card:#1e293b;--fg:#e2e8f0;--mut:#94a3b8;--acc:#38bdf8;--rojo:#f87171;--verde:#4ade80}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg);line-height:1.6}
.wrap{max-width:920px;margin:0 auto;padding:22px}
h1{font-size:26px}
h2{font-size:17px;color:var(--acc);margin:24px 0 10px;border-bottom:1px solid #334155;padding-bottom:6px}
.mut{color:var(--mut);font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:14px 0}
.kpi{background:var(--card);border-radius:10px;padding:14px}
.kpi b{display:block;font-size:21px}
.kpi span{font-size:11px;color:var(--mut)}
.pos{color:var(--verde)}.neg{color:var(--rojo)}
table{width:100%;border-collapse:collapse;font-size:13px;background:var(--card);border-radius:8px;overflow:hidden}
th{background:#0f172a;color:var(--mut);text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase}
td{padding:8px 10px;border-top:1px solid #1e293b}
td.r{text-align:right}
.alert{background:#7f1d1d;border:1px solid #b91c1c;border-radius:8px;padding:12px 14px;margin:12px 0}
.alert b{color:#fca5a5}
.src{font-size:10px;color:var(--mut);margin-top:30px;line-height:1.6}
a{color:var(--acc)}
</style></head><body><div class="wrap">

<h1>Málaga <span class="mut">· Municipal Intelligence</span></h1>
<div class="mut">Ayuntamiento de Málaga · Andalucía · código INE 29067 · datos trazables (INE + datos.gob.es)</div>

<h2>Población (INE, Revisión del Padrón)</h2>
<div class="grid">
  <div class="kpi"><b>@@P25@@</b><span>habitantes (2025)</span></div>
  <div class="kpi"><b>@@P96@@</b><span>en 1996</span></div>
  <div class="kpi"><b class="@@SIGN@@">@@VAR@@</b><span>variación 1996 → 2025</span></div>
  <div class="kpi"><b>@@RANK@@º</b><span>rank nacional (8.132 municipios)</span></div>
</div>
<div class="grid">
  <div class="kpi"><b>@@H25@@</b><span>hombres (2025)</span></div>
  <div class="kpi"><b>@@M25@@</b><span>mujeres (2025)</span></div>
  <div class="kpi"><b>@@RNET@@ €</b><span>renta neta/persona (2022, INE Atlas)</span></div>
  <div class="kpi"><b>@@RHOG@@ €</b><span>renta neta/hogar (2022)</span></div>
</div>

<h2>Estructura de edad <span style="color:#94a3b8;font-size:13px">(Censo 2021)</span></h2>
<div style="background:#7f1d1d;border:1px solid #b91c1c;border-radius:8px;padding:10px 12px;margin:10px 0;font-size:12px"><b style="color:#fca5a5">Aviso:</b> el desglose por edad procede del <b>Censo 2021</b> (decenal; el siguiente es <b>2031</b>). La población total y evolución son del <b>Padrón 2025</b>.</div>
@@EDADBAR@@

<h2>Contratos menores del Ayuntamiento (datos.gob.es)</h2>
<div class="grid">
  <div class="kpi"><b>@@NMEN@@</b><span>contratos menores 2024-2026</span></div>
  <div class="kpi"><b>@@GASTO@@ €</b><span>gasto menor (con importe)</span></div>
</div>
@@ALERTA@@
<h2>Proveedores por número de contratos menores (2024-2026)</h2>
<table><tr><th>#</th><th>Proveedor</th><th class="r">Contratos</th><th class="r">Importe</th><th class="r">Media</th></tr>@@ROWS@@</table>

<div class="src">Fuentes: INE · Cifras oficiales de población (Revisión del Padrón Municipal), población a 01/01/2025 publicada el 11/12/2025 · INE Atlas de renta (2022) · Censo 2021 (estructura de edad) · datos.gob.es: datasets "Contratos Menores [trimestre] · Ayuntamiento de Málaga" (datosabiertos.malaga.eu), 2024-Q1 a 2026-Q2. Los importes >40.000 € se excluyen del análisis de menores (posibles formalizados). Sin datos inventados.</div>
</div></body></html>"""

T = {"@@P25@@": fmt_e(p25), "@@P96@@": fmt_e(p96), "@@SIGN@@": "pos" if var >= 0 else "neg",
     "@@VAR@@": ("+" if var >= 0 else "") + str(var), "@@RANK@@": str(rank),
     "@@H25@@": fmt_e(h25[0] if h25 else 0), "@@M25@@": fmt_e(m25[0] if m25 else 0),
     "@@RNET@@": fmt_e(renta["neta_persona"]), "@@RHOG@@": fmt_e(renta["neta_hogar"]),
     "@@EDADBAR@@": edadbar, "@@NMEN@@": str(len(m)), "@@GASTO@@": fmt_e(total_gasto),
     "@@ALERTA@@": alerta, "@@ROWS@@": row_num}
html = HTML
for k, v in T.items():
    html = html.replace(k, str(v))
with open("dashboard/ficha_malaga.html", "w", encoding="utf-8") as f:
    f.write(html)
print("ficha_malaga.html generado:", len(html)//1024, "KB | contratos:", len(m), "| gasto:", fmt_e(total_gasto))
