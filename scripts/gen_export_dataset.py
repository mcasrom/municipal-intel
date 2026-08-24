#!/usr/bin/env python3
# gen_export_dataset.py — genera dataset combinado exportable (CSV + JSON) por municipio
# demografía (INE) + alquiler (VIA) + España Vaciada (IV) para descarga pública
import sqlite3, csv, json, io
from pathlib import Path

BASE = Path.home() / "municipal-intel"
DB = BASE / "data/poblacion_municipal.sqlite"
VIADB = BASE / "dashboard/data/via/via.db"
OUT_CSV = BASE / "dashboard/data/csv/municipal-dataset.csv"
OUT_JSON = BASE / "dashboard/data/csv/municipal-dataset.json"

# demografía por municipio (2025 + variaciones)
con = sqlite3.connect(DB)
rows = con.execute("""
  SELECT c.municipio, c.provincia, c.codigo_ine, c.lat, c.lon,
         p.poblacion
  FROM catalogo c
  JOIN poblacion p ON p.provincia=c.provincia AND p.municipio=c.municipio
  WHERE p.anyo=2025 AND p.sexo='Total'
  ORDER BY p.poblacion DESC
""").fetchall()
# serie para variaciones
def pob_anyo(prov, muni, anyo):
    r = con.execute("SELECT poblacion FROM poblacion WHERE provincia=? AND municipio=? AND anyo=? AND sexo='Total'",
                    (prov, muni, anyo)).fetchone()
    return r[0] if r else None
# alquiler (VIA)
cv = sqlite3.connect(f"file:{VIADB}?mode=ro", uri=True)
fecha = cv.execute("SELECT MAX(fecha) FROM via_index").fetchone()[0]
via = {m: (e, p25, p75, alq, an) for m, e, p25, p75, alq, an in cv.execute(
    "SELECT municipio, eur_m2_mediana, p25, p75, alq_mediana_80m2, anuncios FROM via_index WHERE fecha=?", (fecha,))}
cv.close()

# construir dataset
dataset = []
for muni, prov, code, lat, lon, pob2025 in rows:
    p1996 = pob_anyo(prov, muni, 1996)
    p2016 = pob_anyo(prov, muni, 2016)
    var1996 = round((pob2025 - p1996) / p1996 * 100, 1) if p1996 else None
    var10 = round((pob2025 - p2016) / p2016 * 100, 1) if p2016 else None
    alq = via.get(muni)
    dataset.append({
        "municipio": muni, "provincia": prov, "codigo_ine": code,
        "lat": lat, "lon": lon,
        "poblacion_2025": pob2025, "poblacion_1996": p1996,
        "var_1996_2025_pct": var1996, "var_10a_pct": var10,
        "alquiler_eur_m2": alq[0] if alq else None,
        "alquiler_p25": alq[1] if alq else None,
        "alquiler_p75": alq[2] if alq else None,
        "alquiler_80m2_mes": alq[3] if alq else None,
        "anuncios": alq[4] if alq else None,
    })

con.close()

# CSV
cols = ["municipio", "provincia", "codigo_ine", "lat", "lon", "poblacion_2025",
        "poblacion_1996", "var_1996_2025_pct", "var_10a_pct",
        "alquiler_eur_m2", "alquiler_p25", "alquiler_p75", "alquiler_80m2_mes", "anuncios"]
with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for d in dataset:
        w.writerow(d)

# JSON
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump({"fecha_alquiler": fecha, "municipios": dataset}, f, ensure_ascii=False, indent=1)

print(f"OK CSV: {OUT_CSV.name} · {len(dataset)} municipios · {len(cols)} columnas")
print(f"OK JSON: {OUT_JSON.name}")
