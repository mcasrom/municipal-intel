#!/usr/bin/env python3
# gen_alquiler_page.py — genera dashboard/alquiler.html desde dashboard/data/via/via.db
# Página pública del Índice VIA: €/m² mediana por municipio (fuente: anuncios activos pisos.com)
import sqlite3, json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.home() / "municipal-intel"
DB = BASE / "dashboard/data/via/via.db"
OUT = BASE / "dashboard/alquiler.html"

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
rows = con.execute("""
    SELECT municipio, provincia, anuncios, eur_m2_mediana, p25, p75, alq_mediana_80m2
    FROM via_index
    WHERE fecha = (SELECT MAX(fecha) FROM via_index)
    ORDER BY eur_m2_mediana DESC
""").fetchall()
meta = con.execute("SELECT MAX(fecha), COUNT(*) FROM via_index").fetchone()
con.close()

# población 2025 desde la BD principal (otro fichero sqlite)
POB = BASE / "data/poblacion_municipal.sqlite"
con2 = sqlite3.connect(f"file:{POB}?mode=ro", uri=True)
pob_map = {m: p for m, p in con2.execute(
    "SELECT municipio, MAX(poblacion) FROM poblacion WHERE anyo='2025' AND sexo='Total' GROUP BY municipio")}
con2.close()

rows = [r + (pob_map.get(r[0]),) for r in rows]

if not rows:
    raise SystemExit("sin datos en via_index aun")

fecha = meta[0]
filas = "\n".join(
    f"<tr><td class='rk'>{i+1}</td><td><b>{m}</b><span class='prov'>{prov}</span></td>"
    f"<td class='num'>{eur:.2f} €</td><td class='num'>{alq:,} €</td>".replace(",", ".") +
    f"<td class='num'>{p25:.1f}–{p75:.1f}</td><td class='num muted'>{an}</td></tr>"
    for i, (m, prov, an, eur, p25, p75, alq, pob) in enumerate(rows)
)

top, bot = rows[0], rows[-1]
html = f"""<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Índice VIA: precio del alquiler hoy por municipio | Municipal Intelligence</title>
<meta name="description" content="Precio real del alquiler hoy: €/m² mediana de anuncios activos en {meta[1]} municipios españoles. Actualizado semanalmente con previsión de tendencia.">
<link rel="canonical" href="https://municipal.viajeinteligencia.com/alquiler.html">
<meta property="og:title" content="Índice VIA — alquiler hoy por municipio">
<meta property="og:description" content="{len(rows)} municipios · €/m² mediana de anuncios activos · {fecha}">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Dataset","name":"Índice VIA: precio del alquiler por municipio de España",
"description":"Mediana de €/m² y alquiler típico (80 m²) calculada sobre anuncios activos de la semana en {len(rows)} municipios.",
"url":"https://municipal.viajeinteligencia.com/alquiler.html",
"license":"https://creativecommons.org/licenses/by/4.0/",
"temporalCoverage":"{fecha}/P1W","spatialCoverage":"España",
"creator":{{"@type":"Organization","name":"Municipal Intelligence","url":"https://municipal.viajeinteligencia.com"}}}}
</script>
<style>
body{{font-family:system-ui,sans-serif;margin:0;background:#0d1117;color:#e6edf3}}
header{{padding:24px 20px;border-bottom:1px solid #21262d}}
h1{{margin:0 0 6px;font-size:1.45em}} .sub{{color:#8b949e;font-size:.95em}}
main{{max-width:900px;margin:0 auto;padding:16px}}
.kpis{{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}}
.kpi{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:12px 18px}}
.kpi b{{font-size:1.3em;display:block}} .kpi span{{color:#8b949e;font-size:.82em}}
table{{width:100%;border-collapse:collapse;font-size:.93em;margin-top:10px}}
th{{text-align:left;color:#8b949e;font-weight:600;padding:8px 10px;border-bottom:1px solid #30363d;position:sticky;top:0;background:#0d1117}}
td{{padding:8px 10px;border-bottom:1px solid #1b2129}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}} .rk{{color:#8b949e;width:34px}}
.prov{{color:#8b949e;display:block;font-size:.8em}} .muted{{color:#6e7681}}
.note{{color:#8b949e;font-size:.83em;margin-top:18px;line-height:1.5}}
a{{color:#58a6ff;text-decoration:none}}
</style></head><body>
<header><h1>🏘️ Índice VIA — precio del alquiler <u>hoy</u></h1>
<div class="sub">€/m² mediana de anuncios activos esta semana · {len(rows)} municipios · actualizado {fecha} · <a href="/">← explorador municipal</a> · <a href="/datos.html">dataset población</a></div></header>
<main>
<div class="kpis">
<div class="kpi"><b>{top[3]:.2f} €/m²</b><span>más caro: {top[0]}</span></div>
<div class="kpi"><b>{bot[3]:.2f} €/m²</b><span>más barato: {bot[0]}</span></div>
<div class="kpi"><b>{sum(r[3] for r in rows)/len(rows):.2f} €/m²</b><span>media del índice</span></div>
</div>
<table><thead><tr><th>#</th><th>Municipio</th><th style="text-align:right">€/m² mediana</th><th style="text-align:right">80 m²/mes</th><th style="text-align:right">rango p25–p75</th><th style="text-align:right">anuncios</th></tr></thead>
<tbody>{filas}</tbody></table>
<p class="note"><b>Metodología:</b> mediana de €/m² sobre anuncios activos en pisos.com durante la última semana
(mínimo 5 anuncios para publicar dato; rango intercuartílico p25–p75 como dispersión).
El índice refleja precios <i>de oferta</i>, no transacciones cerradas. Fuente de población: INE.
Licencia CC BY 4.0 · Municipal Intelligence · previsión a 30 días disponible cuando la serie acumule 4 semanas.</p>
</main></body></html>"""

OUT.write_text(html, encoding="utf-8")
print(f"OK alquiler.html: {len(rows)} municipios, fecha={fecha}")
