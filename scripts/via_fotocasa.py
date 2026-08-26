#!/usr/bin/env python3
# via_fotocasa.py — segunda fuente de alquiler: Fotocasa (precios de oferta)
# Procesa municipios sin dato de pisos.com (o con menos anuncios) y hace merge en via.db
import re, json, sqlite3, statistics, sys, time, unicodedata, subprocess, csv
from pathlib import Path

BASE = Path.home() / "municipal-intel"
VIADB = BASE / "dashboard/data/via/via.db"
CSV_POB = BASE / "dashboard/data/csv/poblacion-municipal-espana-1996-2025.csv"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
MIN_ANUNCIOS = 5
MAX_PAGS = 3  # fotocasa pagina max ~... la 1 ya suele bastar

def slug_ciudad(nombre):
    s = unicodedata.normalize("NFD", nombre).encode("ascii", "ignore").decode().lower()
    # fotocasa no quiere articulos: quitar "el/la/los/las" iniciales
    for art in ("el ", "la ", "los ", "las ", "l'"):
        if s.startswith(art):
            s = s[len(art):]
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def get(url):
    r = subprocess.run(["curl", "-s", "-A", UA, "-L", "--max-time", "20", url], capture_output=True, text=True)
    return r.stdout

def extraer_anuncios(nombre):
    """Devuelve lista de (precio, m2) de los anuncios de alquiler en fotocasa"""
    slug = slug_ciudad(nombre)
    pares = []
    for n in range(1, MAX_PAGS + 1):
        url = f"https://www.fotocasa.es/es/alquiler/viviendas/{slug}/todas-las-zonas/l" + (f"?p={n}" if n > 1 else "")
        try:
            h = get(url)
        except Exception:
            time.sleep(3)
            continue
        # cada anuncio es un objeto JSON con price.amount y features.surface
        # buscar "price":{"amount":N ... "features":{... "surface":M}
        for m in re.finditer(r'"price":\{"amount":(\d+).*?"surface":(\d+)', h):
            precio, m2 = int(m.group(1)), int(m.group(2))
            if 200 <= precio <= 5000 and 20 <= m2 <= 300:
                r = precio / m2
                if 3 <= r <= 40:
                    pares.append((precio, m2, round(r, 2)))
        if len(pares) >= 40 or n >= MAX_PAGS:
            break
        time.sleep(1.5)
    return pares

def main():
    # municipios >=20k sin dato (o con <5 anuncios) en via.db actual
    con = sqlite3.connect(VIADB)
    fecha_act = con.execute("SELECT MAX(fecha) FROM via_index").fetchone()[0]
    con_dato = set(r[0] for r in con.execute(
        "SELECT municipio FROM via_index WHERE fecha=? AND anuncios>=5", (fecha_act,)))
    # poblacion >=20k
    pob = {}
    ine = {}
    for r in csv.DictReader(open(CSV_POB)):
        if r["anyo"] == "2025":
            pob[r["municipio"]] = int(r["poblacion"])
            ine[r["municipio"]] = r["codigo_ine"]
    candidatos = [m for m, p in pob.items() if p >= 20000 and m not in con_dato]
    candidatos.sort(key=lambda x: pob[x])
    print(f"municipios >=20k sin dato de pisos.com: {len(candidatos)}")

    # test rapido limit? --limit N
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
        candidatos = candidatos[:limit]

    ok = sin_datos = errores = 0
    for nombre in candidatos:
        try:
            pares = extraer_anuncios(nombre)
            if len(pares) >= MIN_ANUNCIOS:
                valores = sorted(p[2] for p in pares)
                mediana = statistics.median(valores)
                p25 = valores[int(len(valores) * 0.25)]
                p75 = valores[int(len(valores) * 0.75)]
                alq80 = mediana * 80
                # insertar como fuente fotocasa (municipio sin codigo ine aqui; usamos el nombre)
                con.execute(
                    "INSERT OR REPLACE INTO via_index VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (fecha_act, ine.get(nombre, "FC" + str(hash(nombre) % 100000)), nombre, "", "fotocasa_" + slug_ciudad(nombre).replace("-", "_"),
                     len(pares), round(mediana, 2), round(p25, 2), round(p75, 2), round(alq80)))
                ok += 1
                print(f"  OK {nombre:30} {mediana:.2f} €/m² ({len(pares)} anunc)")
            else:
                sin_datos += 1
        except Exception as e:
            errores += 1
            print(f"  XX {nombre:30} ERROR {str(e)[:50]}")
        time.sleep(1)

    con.commit()
    con.close()
    print(f"\n[FIN] ok={ok} sin_datos={sin_datos} errores={errores}")

if __name__ == "__main__":
    main()
