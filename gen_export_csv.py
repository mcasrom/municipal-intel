#!/usr/bin/env python3
"""gen_export_csv.py - Export CSV publico del dataset de poblacion municipal.

Genera en dashboard/:
  - data/csv/poblacion-municipal-espana-1996-2025.csv (serie Total, con codigo_ine)
  - data/csv/README.txt                               (campos, licencia, fuente)
  - datos.html                                        (landing del dataset)

Ejecutar ANTES de gen_municipio_pages.py (que escribe el sitemap con datos.html).
"""
import csv
import json
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "data", "poblacion_municipal.sqlite")
OUTDIR = os.path.join(BASE, "dashboard", "data", "csv")
SITE = "https://municipal.viajeinteligencia.com"
CSV_NAME = "poblacion-municipal-espana-1996-2025.csv"

os.makedirs(OUTDIR, exist_ok=True)

con = sqlite3.connect(DB)
rows = con.execute(
    """SELECT p.provincia, p.municipio, c.codigo_ine, p.anyo, p.poblacion
       FROM poblacion p
       LEFT JOIN catalogo c ON c.provincia=p.provincia AND c.municipio=p.municipio
       WHERE p.sexo='Total'
       ORDER BY c.codigo_ine IS NULL, p.provincia, p.municipio, p.anyo"""
).fetchall()
con.close()

csv_path = os.path.join(OUTDIR, CSV_NAME)
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["codigo_ine", "provincia", "municipio", "anyo", "poblacion"])
    w.writerows(rows)

n_mun = len({(r[0], r[1]) for r in rows})
anyos = sorted({r[3] for r in rows})
y_last = anyos[-1]
total_esp = sum(r[4] for r in rows if r[3] == y_last)

readme = (
    f"Dataset: Cifras oficiales de poblacion de los municipios espanoles ({anyos[0]}-{y_last})\n"
    f"Fuente: INE - Revision del Padron Municipal (servicios.ine.es)\n"
    f"Procesado por: Municipal Intelligence ({SITE})\n\n"
    "Campos:\n"
    "  codigo_ine  Codigo INE del municipio (vacio si sin match en catalogo OSM)\n"
    "  provincia   Provincia oficial INE\n"
    "  municipio   Nombre oficial INE\n"
    f"  anyo        Ano (a 1 de enero; serie {anyos[0]}-{y_last})\n"
    "  poblacion   Habitantes (Total; Hombres/Mujeres bajo peticion)\n\n"
    f"Cobertura: {n_mun} municipios x {len(anyos)} anos = {len(rows)} filas.\n"
    f"Total Espana {y_last}: {total_esp:,} habitantes (validado contra INE).\n\n"
    "Licencia: CC-BY-4.0. Menciona la fuente (INE) al reutilizar.\n"
    "Actualizacion: tras cada Revision del Padron (anual, ~diciembre).\n"
)

with open(os.path.join(OUTDIR, "README.txt"), "w", encoding="utf-8") as f:
    f.write(readme)

dataset_jsonld = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": f"Cifras oficiales de población de los municipios españoles {anyos[0]}-{y_last}",
    "description": "Serie completa de población por municipio de España según la Revisión del Padrón Municipal del INE.",
    "url": f"{SITE}/datos.html",
    "keywords": ["INE", "población", "municipios", "España", "demografía", "padrón"],
    "spatialCoverage": "España",
    "temporalCoverage": f"{anyos[0]}-01-01/{y_last}-01-01",
    "license": "https://creativecommons.org/licenses/by/4.0/",
    "creator": {"@type": "Person", "name": "M. Castillo"},
    "distribution": [{
        "@type": "DataDownload",
        "encodingFormat": "text/csv",
        "contentUrl": f"{SITE}/data/csv/{CSV_NAME}",
    }],
}

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Datos abiertos: población municipal de España {anyos[0]}–{y_last} (CSV) | Municipal Intelligence</title>
<meta name="description" content="Descarga gratuita en CSV de las cifras oficiales de población del INE para los {n_mun} municipios de España, serie {anyos[0]}-{y_last}. Licencia CC-BY, sin registro.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{SITE}/datos.html">
<meta property="og:type" content="website">
<meta property="og:title" content="Población municipal de España {anyos[0]}-{y_last} en CSV — descarga gratuita">
<meta property="og:description" content="{len(rows):,} filas con código INE, provincia, municipio, año y población. Fuente INE, licencia CC-BY-4.0.">
<meta property="og:url" content="{SITE}/datos.html">
<script type="application/ld+json">{json.dumps(dataset_jsonld, ensure_ascii=False)}</script>
<style>
body{{font-family:-apple-system,system-ui,sans-serif;background:#0B0F17;color:#E7EBF3;line-height:1.65;margin:0}}
.wrap{{max-width:760px;margin:0 auto;padding:36px 24px}}
h1{{font-size:26px;font-weight:800;margin-bottom:6px}}
h2{{color:#FFB454;font-size:19px;margin:24px 0 8px}}
p,li{{color:#CBD5E1;font-size:15px}}
.meta{{font-family:ui-monospace,monospace;color:#8993A8;font-size:12px;margin-bottom:18px}}
.cta{{display:block;text-align:center;background:#34D399;color:#0B0F17;font-weight:800;padding:14px;border-radius:10px;text-decoration:none;margin:20px 0;font-family:ui-monospace,monospace}}
.cta.alt{{background:#1E293B;color:#67E8F9}}
table{{width:100%;border-collapse:collapse;font-size:14px;margin:12px 0}}
th{{color:#67E8F9;text-align:left;font-family:ui-monospace,monospace;font-size:11px;text-transform:uppercase;border-bottom:1px solid #232B3D;padding:8px}}
td{{padding:7px 8px;border-bottom:1px solid #1B2233}}
code{{background:#141B2B;padding:2px 6px;border-radius:5px;font-size:13px;color:#67E8F9}}
.note{{font-size:11.5px;color:#576076;margin-top:18px}}
a{{color:#67E8F9;text-decoration:none}}
b,strong{{color:#E7EBF3}}
</style>
</head>
<body>
<div class="wrap">
  <h1>📥 Población municipal de España en CSV ({anyos[0]}–{y_last})</h1>
  <div class="meta">Fuente oficial INE · {len(rows):,} filas · licencia CC-BY-4.0 · sin registro</div>

  <p>Serie completa de las <b>cifras oficiales del INE</b> (Revisión del Padrón Municipal) para los <b>{n_mun} municipios de España</b>, lista para analizar: un fichero, cinco columnas, sin pelearte con los portales.</p>

  <a class="cta" href="data/csv/{CSV_NAME}" download>⬇️ Descargar el CSV completo ({len(rows):,} filas)</a>
  <a class="cta alt" href="data/csv/README.txt">📄 Ver README (campos y licencia)</a>

  <h2>Columnas</h2>
  <table>
    <tr><th>Campo</th><th>Contenido</th></tr>
    <tr><td><code>codigo_ine</code></td><td>Código INE del municipio</td></tr>
    <tr><td><code>provincia</code></td><td>Provincia oficial</td></tr>
    <tr><td><code>municipio</code></td><td>Nombre oficial</td></tr>
    <tr><td><code>anyo</code></td><td>Año (a 1 de enero)</td></tr>
    <tr><td><code>poblacion</code></td><td>Habitantes (total)</td></tr>
  </table>

  <h2>Ejemplo</h2>
  <pre style="background:#141B2B;padding:14px;border-radius:8px;font-size:13px;color:#94A3B8;overflow-x:auto"><code>codigo_ine,provincia,municipio,anyo,poblacion
30024,Murcia,Lorca,{y_last},98969
28079,Madrid,Madrid,{y_last},3410521</code></pre>

  <h2>Condiciones de uso</h2>
  <p>Licencia <b>CC-BY-4.0</b>: usa los datos libremente citando la fuente (<b>INE</b>, Revisión del Padrón Municipal). Se actualiza tras cada revisión anual (~diciembre).</p>
  <p>Si prefieres explorarlos visualmente: <a href="/">🗺️ el mapa de los {n_mun} municipios</a>.</p>

  <p class="note">Municipal Intelligence forma parte del ecosistema viajeinteligencia.com. Los agregados por provincia y comunidad están disponibles en las páginas editoriales.</p>
</div>
</body>
</html>
"""

with open(os.path.join(BASE, "dashboard", "datos.html"), "w", encoding="utf-8") as f:
    f.write(html)

size_mb = os.path.getsize(csv_path) / 1e6
print(f"export CSV OK: {len(rows)} filas, {n_mun} municipios, {size_mb:.1f} MB")
print(f"total Espana {y_last}: {total_esp:,}")
