#!/usr/bin/env python3
# gen_alquiler_asequible.py — genera "Dónde es más asequible alquilar en [Comunidad]" para todas las CCAA con >=8 municipios
import sqlite3, statistics, unicodedata, re
from pathlib import Path

BASE = Path.home() / "municipal-intel"
DB = BASE / "dashboard/data/via/via.db"

PROV2CA = {
    "Álava": "País Vasco", "Albacete": "Castilla-La Mancha", "Alicante": "C. Valenciana",
    "Almería": "Andalucía", "Ávila": "Castilla y León", "Badajoz": "Extremadura",
    "Baleares": "Baleares", "Barcelona": "Cataluña", "Burgos": "Castilla y León",
    "Cáceres": "Extremadura", "Cádiz": "Andalucía", "Cantabria": "Cantabria",
    "Castellón": "C. Valenciana", "Ciudad Real": "Castilla-La Mancha", "Córdoba": "Andalucía",
    "Cuenca": "Castilla-La Mancha", "Girona": "Cataluña", "Granada": "Andalucía",
    "Guadalajara": "Castilla-La Mancha", "Gipuzkoa": "País Vasco", "Huelva": "Andalucía",
    "Huesca": "Aragón", "Jaén": "Andalucía", "La Rioja": "La Rioja", "León": "Castilla y León",
    "Lleida": "Cataluña", "Lugo": "Galicia", "Madrid": "Madrid", "Málaga": "Andalucía",
    "Murcia": "Murcia", "Navarra": "Navarra", "Ourense": "Galicia", "Asturias": "Asturias",
    "Palencia": "Castilla y León", "Palmas, Las": "Canarias", "Pontevedra": "Galicia",
    "Salamanca": "Castilla y León", "Segovia": "Castilla y León", "Sevilla": "Andalucía",
    "Soria": "Castilla y León", "Tarragona": "Cataluña", "Santa Cruz de Tenerife": "Canarias",
    "Teruel": "Aragón", "Toledo": "Castilla-La Mancha", "Valencia": "C. Valenciana",
    "Valladolid": "Castilla y León", "Bizkaia": "País Vasco", "Zamora": "Castilla y León",
    "Zaragoza": "Aragón",
}

def slug(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-").replace("--", "-")

def main():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT municipio, provincia, eur_m2_mediana, anuncios FROM via_index "
        "WHERE fecha=(SELECT MAX(fecha) FROM via_index) AND eur_m2_mediana>0").fetchall()
    con.close()

    by_ca = {}
    for m, p, e, a in rows:
        ca = PROV2CA.get(p)
        if ca:
            by_ca.setdefault(ca, []).append((m, p, e, a))

    fecha = "2026-08-23"
    generadas = 0
    for ca in sorted(by_ca):
        munis = by_ca[ca]
        munis = [r for r in munis if r[2] > 0]
        munis.sort(key=lambda x: -x[2])
        if len(munis) < 8:
            print(f"skip {ca}: solo {len(munis)}")
            continue

        valores = [r[2] for r in munis]
        mediana = statistics.median(valores)
        min_m = munis[-1]; max_m = munis[0]
        top10 = munis[:10]
        bot8 = munis[-8:]

        def bar_row(m, e, a, mx):
            w = max(4, round(e / mx * 100))
            return (f'<div class="row"><span class="lab">{m}</span>'
                    f'<div class="track"><div style="width:{w}%;background:var(--accent)"></div></div>'
                    f'<b class="n">{e:.2f} €/m²</b><span class="a">{a} anunc</span></div>')

        mx = valores[0]
        top_html = "".join(bar_row(m, e, a, mx) for m, p, e, a in top10)
        bot_html = "".join(bar_row(m, e, a, mx) for m, p, e, a in bot8)

        kpis = f'''
<div class="kpis">
  <div class="kpi"><b>{min_m[2]:.2f} €/m²</b><span>más barato · {min_m[0]}</span></div>
  <div class="kpi"><b>{max_m[2]:.2f} €/m²</b><span>más caro · {max_m[0]}</span></div>
  <div class="kpi"><b>{mediana:.2f} €/m²</b><span>mediana {ca}</span></div>
  <div class="kpi"><b>{max_m[2]/min_m[2]:.1f}×</b><span>diferencia caro/barato</span></div>
  <div class="kpi"><b>{len(munis)}</b><span>municipios con dato</span></div>
</div>'''

        url = f"https://municipal.viajeinteligencia.com/alquiler-asequible-{slug(ca)}.html"
        html = f'''<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dónde es más asequible alquilar en {ca} · €/m² hoy | Municipal Intelligence</title>
<meta name="description" content="Precio real del alquiler por municipio en {ca}: €/m² mediana de anuncios activos. De {min_m[2]:.2f} €/m² ({min_m[0]}) a {max_m[2]:.2f} €/m² ({max_m[0]}) — {len(munis)} municipios con datos, actualizado {fecha}.">
<link rel="canonical" href="{url}">
<meta property="og:title" content="Dónde es más asequible alquilar en {ca}">
<meta property="og:description" content="{len(munis)} municipios · de {min_m[2]:.2f} a {max_m[2]:.2f} €/m² · {fecha}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"Dónde es más asequible alquilar en {ca}","url":"{url}"}}</script>
<style>
:root{{--bg:#F4F6FB;--panel:#FFFFFF;--line:#D6DDEA;--text:#16202E;--text2:#33415C;--dim:#5B6B84;--faint:#8A97AC;--accent:#d97706;--accent2:#16a34a}}
[data-theme="dark"]{{--bg:#0d1117;--panel:#161b22;--line:#21262d;--text:#e6edf3;--text2:#c9d1d9;--dim:#8b949e;--faint:#6e7681;--accent:#f59e0b;--accent2:#3fb950}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.65;transition:background .2s,color .2s}}
.wrap{{max-width:760px;margin:0 auto;padding:28px 20px 60px}}
.top{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:18px}}
h1{{font-size:24px;font-weight:800;letter-spacing:-.02em}}
.meta{{font-size:11px;color:var(--faint);font-family:ui-monospace,monospace;margin-bottom:16px}}
.toggle{{display:inline-flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;color:var(--dim);background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:5px 12px;user-select:none}}
.intro{{font-size:14.5px;color:var(--text2);margin-bottom:16px}}
.intro b{{color:var(--accent)}}
.kpis{{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}}
.kpi{{flex:1;min-width:120px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
.kpi b{{font-size:1.35em;display:block;color:var(--accent)}}
.kpi span{{color:var(--dim);font-size:.8em}}
h2{{font-size:16px;margin:26px 0 10px;color:var(--accent)}}
.row{{display:flex;align-items:center;gap:10px;padding:5px 0;font-size:13px}}
.lab{{flex:0 0 30%;color:var(--text2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.track{{flex:1;background:var(--line);border-radius:4px;height:12px;overflow:hidden}}
.n{{flex:0 0 84px;text-align:right;font-variant-numeric:tabular-nums}}
.a{{flex:0 0 64px;color:var(--faint);font-size:11px;text-align:right}}
.cta{{display:block;margin:26px auto 0;padding:13px 24px;background:var(--accent);color:#fff;font-weight:700;border-radius:8px;text-align:center;text-decoration:none;max-width:380px}}
.foot{{margin-top:30px;font-size:11px;color:var(--faint);text-align:center}}
.kofi{{display:inline-block;margin-top:14px;background:#29ABE0;color:#fff;font-weight:700;padding:9px 16px;border-radius:8px;text-decoration:none;font-size:13px}}
.note{{margin-top:16px;font-size:11px;color:var(--faint);text-align:center}}
</style>
<script>
function toggleTheme(){{var t=document.documentElement.getAttribute('data-theme');document.documentElement.setAttribute('data-theme',t==='dark'?'':'dark');localStorage.setItem('theme',t==='dark'?'light':'dark');}}
(function(){{var s=localStorage.getItem('theme');if(s==='dark')document.documentElement.setAttribute('data-theme','dark');}})();
</script>
</head><body>
<div class="wrap">
  <div class="top">
    <h1>🌍 Dónde es más asequible alquilar en {ca}</h1>
    <div class="toggle" onclick="toggleTheme()">🌓 Tema</div>
  </div>
  <div class="meta">Índice VIA · €/m² mediana de anuncios activos · actualizado {fecha} · fuente pisos.com</div>
  <p class="intro">En {ca} alquilar un piso cuesta de media <b>{mediana:.2f} €/m²</b>. La diferencia entre el municipio más barato (<b>{min_m[0]}, {min_m[2]:.2f} €/m²</b>) y el más caro (<b>{max_m[0]}, {max_m[2]:.2f} €/m²</b>) es de <b>{max_m[2]/min_m[2]:.1f}×</b>. Datos reales de anuncios en alquiler, no estimaciones.</p>
  {kpis}
  <h2>🟠 Los más caros</h2>
  {top_html}
  <h2>🟢 Dónde es más asequible (los más baratos)</h2>
  {bot_html}
  <a class="cta" href="/alquiler.html">Ver el ranking completo de España →</a>
  <div class="foot">Municipal Intelligence · fuentes: INE + anuncios de alquiler públicos (pisos.com) · sin datos inventados</div>
  <div style="text-align:center"><a class="kofi" href="https://ko-fi.com/m_castillo" target="_blank" rel="noopener noreferrer">☕ Apóyame en Ko-fi</a></div>
  <div class="note">Los precios son la mediana de los anuncios activos (€/m²). Un piso de 80 m² en {min_m[0]} costaría ≈ {min_m[2]*80:.0f} €/mes; en {max_m[0]}, ≈ {max_m[2]*80:.0f} €/mes.</div>
</div>
</body></html>
'''
        out = BASE / f"dashboard/alquiler-asequible-{slug(ca)}.html"
        out.write_text(html)
        generadas += 1
        print(f"OK {ca:20} {len(munis):3d} municipios -> {out.name}")

    print(f"\ntotal generadas: {generadas}")

if __name__ == "__main__":
    main()
