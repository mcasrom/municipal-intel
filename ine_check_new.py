import json, os, urllib.request, datetime

# Detecta si el INE ha publicado un año de población más reciente que 2025
# (Revisión del Padrón Municipal). Anual: nuevo año ~diciembre.
# Si hay año nuevo, avisa (la re-ingesta completa la haríamos con la URL nueva).
# exit 0 = sin cambios, exit 1 = año nuevo detectado

TABLE_MURCIA = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/2883"

def main():
    req = urllib.request.Request(TABLE_MURCIA, headers={"User-Agent": "municipal-intel/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    max_year = 0
    for row in d:
        for dd in row.get("Data", []):
            if dd.get("Anyo", 0) > max_year:
                max_year = dd["Anyo"]
    # último año en nuestra BD
    db_year = 2025
    if os.path.exists("data/poblacion_municipal.sqlite"):
        import sqlite3
        con = sqlite3.connect("data/poblacion_municipal.sqlite")
        db_year = con.execute("SELECT MAX(anyo) FROM poblacion").fetchone()[0] or db_year
        con.close()
    print(f"INE año máximo: {max_year} | BD año máximo: {db_year}")
    if max_year > db_year:
        print(f"ATENCIÓN: INE tiene {max_year}, la BD tiene {db_year}. Re-ingesta manual requerida: "
              f"python3 ine_pobmunicipal_ingest.py && python3 ine_catalog_build.py ingest/overpass_municipios.json data/poblacion_municipal.sqlite")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
