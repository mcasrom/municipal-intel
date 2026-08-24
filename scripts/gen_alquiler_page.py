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
# --- KPI gráfico: barras top 8 caros + bottom 8 baratos ---
def _bar(m, eur, mx):
    w = max(4, round(eur / mx * 100))
    return (f'<div class="bar-row"><span class="bar-lab">{m}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{w}%"></div></div>'
            f'<span class="bar-val">{eur:.2f}</span></div>')
_mx = max(r[3] for r in rows)
_caros = "".join(_bar(r[0], r[3], _mx) for r in rows[:8])
_baratos = "".join(_bar(r[0], r[3], _mx) for r in rows[-8:])
chart = (f'<div class="legend">🟠 Los 8 más caros</div>{_caros}'
         f'<div class="legend" style="margin-top:12px">🟢 Los 8 más baratos</div>{_baratos}')
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
:root{{--bg:#F4F6FB;--panel:#FFFFFF;--line:#D6DDEA;--text:#16202E;--text2:#33415C;--dim:#5B6B84;--faint:#8A97AC;--accent:#d97706;--accent2:#16a34a;--link:#0366d6}}
[data-theme="dark"]{{--bg:#0d1117;--panel:#161b22;--line:#21262d;--text:#e6edf3;--text2:#c9d1d9;--dim:#8b949e;--faint:#6e7681;--accent:#f59e0b;--accent2:#3fb950;--link:#58a6ff}}
*{{box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;margin:0;background:var(--bg);color:var(--text);line-height:1.65;transition:background .2s,color .2s}}
header{{padding:24px 20px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
h1{{margin:0 0 6px;font-size:1.45em}} .sub{{color:var(--dim);font-size:.92em}}
.toggle{{display:inline-flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;color:var(--dim);background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:6px 14px;user-select:none}}
.toggle:hover{{border-color:var(--accent)}}
main{{max-width:920px;margin:0 auto;padding:16px}}
.kpis{{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}}
.kpi{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 18px;min-width:150px}}
.kpi b{{font-size:1.3em;display:block;color:var(--accent)}} .kpi span{{color:var(--dim);font-size:.82em}}
table{{width:100%;border-collapse:collapse;font-size:.93em;margin-top:10px}}
th{{text-align:left;color:var(--dim);font-weight:600;padding:8px 10px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg)}}
td{{padding:8px 10px;border-bottom:1px solid var(--line)}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}} .rk{{color:var(--faint);width:34px}}
.prov{{color:var(--dim);display:block;font-size:.8em}} .muted{{color:var(--faint)}}
.note{{color:var(--dim);font-size:.85em;margin-top:20px;line-height:1.55;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
a{{color:var(--link);text-decoration:none}}
.kofi{{display:inline-block;margin-top:16px;background:#29ABE0;color:#fff;font-weight:700;padding:9px 16px;border-radius:8px;text-decoration:none;font-size:13px}}
.search{{width:100%;max-width:460px;margin:18px auto 6px;display:block;padding:11px 16px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:14px}}
.search:focus{{outline:none;border-color:var(--accent)}}
table{{width:100%;border-collapse:collapse;font-size:.93em;margin-top:10px}}
td,th{{padding:8px 10px}}
.chart{{display:flex;flex-direction:column;gap:6px;margin:18px 0}}
.bar-row{{display:flex;align-items:center;gap:10px;font-size:13px}}
.bar-lab{{flex:0 0 150px;color:var(--text2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.bar-track{{flex:1;background:var(--line);border-radius:4px;height:16px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:4px;background:linear-gradient(90deg,var(--accent),var(--accent2))}}
.bar-val{{flex:0 0 90px;text-align:right;font-variant-numeric:tabular-nums;font-weight:600}}
.legend{{font-size:12px;color:var(--dim);margin:6px 0 2px}}
.comunidades{{margin:20px 0;padding:14px;background:var(--panel);border:1px solid var(--line);border-radius:10px}}
.comunidades b{{display:block;margin-bottom:8px}}
.comunidades a{{color:var(--accent);text-decoration:none;margin:4px 10px 4px 0;display:inline-block}}
</style>
<script>
function toggleTheme(){{var t=document.documentElement.getAttribute('data-theme');document.documentElement.setAttribute('data-theme',t==='dark'?'':'dark');localStorage.setItem('theme',t==='dark'?'light':'dark');}}
(function(){{var s=localStorage.getItem('theme');if(s==='dark')document.documentElement.setAttribute('data-theme','dark');}})();
</script>
</head><body>
<header style="text-align:center;flex-direction:column;align-items:center"><div>
<h1>🏘️ Índice VIA — precio del alquiler <u>hoy</u></h1>
<div class="sub">€/m² mediana de anuncios activos esta semana · {len(rows)} municipios · actualizado {fecha} · <a href="/">← explorador municipal</a> · <a href="/datos.html">dataset población</a></div></div>
<div class="toggle" onclick="toggleTheme()">🌓 Tema</div></header>
<main>
<div class="kpis">
<div class="kpi"><b>{top[3]:.2f} €/m²</b><span>más caro: {top[0]}</span></div>
<div class="kpi"><b>{bot[3]:.2f} €/m²</b><span>más barato: {bot[0]}</span></div>
<div class="kpi"><b>{sum(r[3] for r in rows)/len(rows):.2f} €/m²</b><span>media del índice</span></div>
</div>
<h2 style="font-size:15px;margin:24px 0 6px;color:var(--accent)">📊 Más caros y más baratos (€/m²)</h2>
<div class="chart">{chart}</div>
<input class="search" id="search" placeholder="🔍 Busca tu municipio (ej: Lorca, Jerez, Hospitalet...)">
<p style="font-size:12px;color:var(--faint);text-align:center;margin:4px 0 10px" id="count"></p><table id="tabla" class="munis"><thead><tr><th>#</th><th>Municipio</th><th style="text-align:right">€/m² mediana</th><th style="text-align:right">80 m²/mes</th><th style="text-align:right">rango p25–p75</th><th style="text-align:right">anuncios</th></tr></thead>
<tbody>{filas}</tbody></table>
<p class="note"><b>Metodología:</b> mediana de €/m² sobre anuncios activos en pisos.com durante la última semana
(mínimo 5 anuncios para publicar dato; rango intercuartílico p25–p75 como dispersión).
El índice refleja precios <i>de oferta</i>, no transacciones cerradas. Fuente de población: INE.
Licencia CC BY 4.0 · Municipal Intelligence · previsión a 30 días disponible cuando la serie acumule 4 semanas.</p>
<div class="comunidades"><b>🌍 Dónde es más asequible alquilar por comunidad:</b>
<a href="/alquiler-asequible-andalucia.html">Andalucía</a><a href="/alquiler-asequible-baleares.html">Baleares</a><a href="/alquiler-asequible-c-valenciana.html">C. Valenciana</a><a href="/alquiler-asequible-canarias.html">Canarias</a><a href="/alquiler-asequible-castilla-y-leon.html">Castilla y León</a><a href="/alquiler-asequible-castilla-la-mancha.html">Castilla-La Mancha</a><a href="/alquiler-asequible-cataluna.html">Cataluña</a><a href="/alquiler-asequible-galicia.html">Galicia</a><a href="/alquiler-asequible-madrid.html">Madrid</a><a href="/alquiler-asequible-murcia.html">Murcia</a><a href="/alquiler-asequible-pais-vasco.html">País Vasco</a></div>
<div style="text-align:center"><a class="kofi" href="https://ko-fi.com/m_castillo" target="_blank" rel="noopener noreferrer">☕ Apóyame en Ko-fi</a></div>
</main>"""

JS_BUSCADOR = """
<script>
(function() {
  var input = document.getElementById('search');
  var table = document.getElementById('tabla');
  var count = document.getElementById('count');
  if (!input || !table) return;
  var rows = Array.prototype.slice.call(table.tBodies[0].rows);
  function filtro() {
    var q = input.value.toLowerCase().trim();
    var vis = 0;
    rows.forEach(function(r) {
      var ok = !q || r.cells[1].textContent.toLowerCase().indexOf(q) >= 0;
      r.style.display = ok ? '' : 'none';
      if (ok) vis++;
    });
    if (count) count.textContent = q ? vis + ' de ' + rows.length + ' municipios' : rows.length + ' municipios';
  }
  input.addEventListener('input', filtro);
  filtro();
})();
</script>
</body></html>"""

html = html + JS_BUSCADOR

OUT.write_text(html, encoding="utf-8")
print(f"OK alquiler.html: {len(rows)} municipios, fecha={fecha}")
