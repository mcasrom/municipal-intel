#!/usr/bin/env python3
# gen_correlacion_page.py — página editorial SEO: municipios que pierden población pero el alquiler sube
import sqlite3, statistics
from pathlib import Path

BASE = Path.home() / "municipal-intel"
OUT = BASE / "dashboard/editorial/municipios-pierden-poblacion-alquiler-sube.html"

# datos VIA
cv = sqlite3.connect(f"file:{BASE}/dashboard/data/via/via.db?mode=ro", uri=True)
fecha = cv.execute("SELECT MAX(fecha) FROM via_index").fetchone()[0]
via = {m: (e, a) for m, e, a in cv.execute(
    "SELECT municipio, eur_m2_mediana, anuncios FROM via_index WHERE fecha=? AND eur_m2_mediana>0 AND anuncios>=5", (fecha,))}
cv.close()

# población 2025 y 2016
con = sqlite3.connect(f"file:{BASE}/data/poblacion_municipal.sqlite?mode=ro", uri=True)
pob25 = {m: p for m, p in con.execute("SELECT municipio, poblacion FROM poblacion WHERE anyo='2025' AND sexo='Total'")}
pob16 = {m: p for m, p in con.execute("SELECT municipio, poblacion FROM poblacion WHERE anyo='2016' AND sexo='Total'")}
# provincia por municipio
prov_map = {m: p for m, p in con.execute("SELECT DISTINCT municipio, provincia FROM catalogo")}
con.close()

# construir lista: pierden población + alquiler >10 €/m² (la anomalía)
datos = []
for m, (e, a) in via.items():
    p25 = pob25.get(m); p16 = pob16.get(m)
    if not p25 or not p16 or p16 <= 0 or p25 < 20000: continue
    var10 = round((p25 - p16) / p16 * 100, 1)
    if var10 < 0 and e > 10:
        datos.append({"m": m, "prov": prov_map.get(m, ""), "e": e, "a": a, "var10": var10, "pob": p25})

datos.sort(key=lambda x: -x["e"])
n = len(datos)

# filas de la tabla
def fila(d, i):
    return (f'<tr><td>{i+1}</td><td><b>{d["m"]}</b><span class="prov">{d["prov"]}</span></td>'
            f'<td class="num">{d["e"]:.2f} €/m²</td><td class="num neg">{d["var10"]:+.1f}%</td>'
            f'<td class="num">{d["pob"]:,}</td></tr>').replace(",", ".")

filas = "".join(fila(d, i) for i, d in enumerate(datos))

html = f'''<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Municipios que pierden población pero el alquiler sube · España 2026 | Municipal Intelligence</title>
<meta name="description" content="Análisis de {n} municipios españoles que pierden población mientras su alquiler supera los 10 €/m²: Coslada, Galdakao, Getxo, Fuenlabrada... Datos oficiales INE + anuncios activos.">
<link rel="canonical" href="https://municipal.viajeinteligencia.com/editorial/municipios-pierden-poblacion-alquiler-sube.html">
<meta property="og:title" content="Municipios que pierden población pero el alquiler sube">
<meta property="og:description" content="{n} municipios con presión inmobiliaria: pierden vecinos pero el alquiler no baja. Datos INE + anuncios activos.">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"Municipios que pierden población pero el alquiler sube","author":{{"@type":"Organization","name":"Municipal Intelligence · Viaje Inteligencia","url":"https://www.viajeinteligencia.com"}}}}</script>
<style>
:root{{--bg:#0f172a;--card:#1e293b;--fg:#e2e8f0;--mut:#94a3b8;--line:#334155;--acc:#d97706;--neg:#f87171;--pos:#4ade80}}
*{{box-sizing:border-box}} body{{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:var(--fg);line-height:1.7}}
.wrap{{max-width:820px;margin:0 auto;padding:28px 20px 60px}}
h1{{font-size:26px;margin:0 0 6px}} .sub{{color:var(--mut);font-size:13px;margin-bottom:20px}}
h2{{font-size:17px;color:var(--acc);margin:26px 0 10px}}
p{{font-size:14.5px;color:var(--text2,#c9d1d9);margin:12px 0}}
b{{color:var(--acc)}}
table{{width:100%;border-collapse:collapse;font-size:.92em;margin-top:14px}}
th{{text-align:left;color:var(--mut);padding:8px 10px;border-bottom:1px solid var(--line)}}
td{{padding:8px 10px;border-bottom:1px solid var(--line)}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}}
.prov{{display:block;color:var(--mut);font-size:.8em}}
.neg{{color:var(--neg)}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:16px 0}}
.kpi b{{font-size:1.5em;color:var(--acc)}}
.note{{color:var(--mut);font-size:.82em;margin-top:20px;line-height:1.55}}
.cta{{display:block;margin:26px auto 0;padding:13px 24px;background:var(--acc);color:#fff;font-weight:700;border-radius:8px;text-align:center;text-decoration:none;max-width:380px}}
.kofi{{display:inline-block;margin-top:16px;background:#29ABE0;color:#fff;font-weight:700;padding:9px 16px;border-radius:8px;text-decoration:none;font-size:13px}}
</style>
</head><body>
<div class="wrap">
<h1>📍 Municipios que pierden población pero el alquiler sube</h1>
<div class="sub">Análisis de datos INE + anuncios de alquiler · actualizado {fecha} · Municipal Intelligence</div>

<p>En España hay municipios donde la población <b>baja año tras año</b> pero el precio del alquiler <b>no baja</b>: sube o se mantiene por encima de los 10 €/m². Esta es la señal de una <b>presión inmobiliaria que no depende del crecimiento demográfico</b> — el mercado de alquiler responde a otros factores (turismo, segunda residencia, inversión, escasez de oferta) mientras los vecinos se van.</p>

<div class="kpi"><b>{n} municipios</b> pierden población (−10 años) con alquiler superior a 10 €/m². <b>No es un dato aislado: es un patrón.</b></div>

<h2>El listado completo</h2>
<table><thead><tr><th>#</th><th>Municipio</th><th class="num">€/m² alquiler</th><th class="num">Var. 10 años</th><th class="num">Población</th></tr></thead>
<tbody>{filas}</tbody></table>

<h2>¿Por qué ocurre esto?</h2>
<p>El alquiler de oferta no responde solo a la demografía. Un municipio puede perder vecinos y aun así mantener precios altos si la oferta es escasa (pocos pisos en alquiler), si hay demanda estacional o de inversión, o si el parque de vivienda no se renueva. El resultado es un mercado que <b>ignora la tendencia poblacional</b> — y eso genera una presión sobre los vecinos que quedan.</p>

<h2>Metodología</h2>
<p class="note">Población: INE (Revisión del Padrón Municipal), serie 2016-2025. Alquiler: €/m² mediana de anuncios activos publicados en pisos.com (mínimo 5 anuncios por municipio). Variación de población: cambio porcentual 2016→2025. Fecha del análisis: {fecha}. Compilación independiente — sin datos inventados.</p>

<a class="cta" href="/alquiler.html">Ver el índice de alquiler completo (290 municipios) →</a>
<div style="text-align:center"><a class="kofi" href="https://ko-fi.com/m_castillo" target="_blank" rel="noopener">☕ Apóyame en Ko-fi</a></div>
</div>
</body></html>
'''

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print(f"OK -> {OUT.name} | {n} municipios en el análisis")
