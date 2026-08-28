#!/usr/bin/env python3
# via_mivau.py — segunda fuente de alquiler: SERPAVI/MIVAU (precio oficial de contratos)
# Rellena los municipios >=20k sin dato de pisos.com (o con <5 anuncios) con el precio
# oficial por municipio del Ministerio de Vivienda (VDP001: mediana/p25/p75, €/mes y m²).
# Dato anual (último año disponible, tip. 2024) y de contratos reales, no de oferta.
#
# Fuente: https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP001_01.csv
#   Columnas: COD_PROVINCIA;PROVINCIA;COD_POSTAL;NOMBRE_MUNICIPIO;ELEMENTO;TIPO_VIVIENDA;TIPO_MEDIDA;AÑO;VALOR
#   ELEMENTO: PRECIO (€/mes) o SUPERFICIE (m²); TIPO_VIVIENDA: COLECTIVA/UNIFAMILIAR;
#   TIPO_MEDIDA: MEDIANA/PERCENT25/PERCENT75
import csv, gzip, os, re, sqlite3, subprocess, sys, time, unicodedata
from pathlib import Path
from urllib.request import Request, urlopen

BASE = Path.home() / "municipal-intel"
VIADB = BASE / "dashboard/data/via/via.db"
CSV_POB = BASE / "dashboard/data/csv/poblacion-municipal-espana-1996-2025.csv"
URL = "https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP001_01.csv"
CACHE = Path("/tmp") / "vdp001_01.csv"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"}

# Municipios >=20k cuyo codigo_ine viene vacio en el CSV de poblacion (fallo de la fuente)
# -> mapeo manual fiable (INE conocido) para que no queden fuera.
INE_MANUAL = {"Cangas": "36008"}  # Cangas (Pontevedra), 26711 hab.

MIN_POB = 20000


def descargar():
    if CACHE.exists() and time.time() - CACHE.stat().st_mtime < 86400:
        return CACHE
    req = Request(URL, headers=UA)
    with urlopen(req, timeout=180) as r:
        data = r.read()
    tmp = CACHE.with_suffix(".part")
    tmp.write_bytes(data)
    tmp.rename(CACHE)
    return CACHE


def parse_mivau(path):
    """{ine: {anio: {(ELEMENTO, TIPO_MEDIDA): valor}}} solo COLECTIVA"""
    out = {}
    for line in open(path, encoding="utf-8", errors="replace"):
        f = line.rstrip("\n").split(";")
        if len(f) < 9:
            continue
        ine, elem, tv, med, anio_s, val_s = f[2], f[4], f[5], f[6], f[7], f[8]
        if tv != "COLECTIVA" or elem not in ("PRECIO", "SUPERFICIE"):
            continue
        if med not in ("MEDIANA", "PERCENT25", "PERCENT75"):
            continue
        try:
            anio, val = int(anio_s), float(val_s)
        except ValueError:
            continue
        out.setdefault(ine, {}).setdefault(anio, {})[(elem, med)] = val
    return out


def municipios_objetivo():
    pob, ine_nombre = {}, {}
    for r in csv.DictReader(open(CSV_POB)):
        if r["anyo"] == "2025":
            pob[r["municipio"]] = int(r["poblacion"])
            ine_nombre[r["municipio"]] = r["codigo_ine"].strip() or INE_MANUAL.get(r["municipio"], "")
    return [(ine_nombre[m], m, p) for m, p in pob.items()
            if p >= MIN_POB and ine_nombre[m]]


def eur_m2_por_municipio(mivau, ine):
    """Mejor año (más reciente) con PRECIO_MEDIANA + SUPERFICIE_MEDIANA; devuelve
    dict con eur_m2 mediana/p25/p75 (mismo año) y alquiler mensual mediano, o None."""
    d = mivau.get(ine)
    if not d:
        return None
    for anio in sorted(d, reverse=True):
        m = d[anio]
        if ("PRECIO", "MEDIANA") not in m or ("SUPERFICIE", "MEDIANA") not in m:
            continue
        pm = m[("PRECIO", "MEDIANA")]          # €/mes
        sm = m[("SUPERFICIE", "MEDIANA")]      # m²
        if not sm:
            continue
        mediana = pm / sm
        # €/m²: dividir el PRECIO (€/mes) de cada percentil entre la SUPERFICIE MEDIANA
        # (denominador estable y común), garantizando p25 <= mediana <= p75.
        def _p(per):
            pp = m.get(("PRECIO", per))
            return round(pp / sm, 2) if pp else None
        return {"anio": anio, "eur_m2_mediana": round(mediana, 2),
                "p25": _p("PERCENT25"), "p75": _p("PERCENT75"),
                "alq_mediana_80m2": round(pm)}
    return None


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    con = sqlite3.connect(VIADB)
    fecha_act = con.execute("SELECT MAX(fecha) FROM via_index").fetchone()[0]
    if not fecha_act:
        print("[FIN] via.db vacia: primero corre via_scraper.py (pisos.com)")
        return
    # ya cubiertos por pisos.com (>=5) o por mivau en la fecha maxima
    cubiertos = set(r[0] for r in con.execute(
        "SELECT codigo_ine FROM via_index WHERE fecha=? AND ((anuncios>=5) OR (slug LIKE 'mivau_%'))",
        (fecha_act,)))

    print("descargando/sirviendo CSV MIVAU (cache 24h)...")
    path = descargar()
    mivau = parse_mivau(path)
    print(f"  CSV {path.name}: {sum(len(v) for v in mivau.values())} filas COLECTIVA en {len(mivau)} municipios")

    objetivos = [x for x in municipios_objetivo() if x[0] and x[0] not in cubiertos]
    objetivos.sort(key=lambda x: -x[2])
    if limit:
        objetivos = objetivos[:limit]
    print(f"municipios >=20k a rellenar con MIVAU: {len(objetivos)}  (fecha {fecha_act})")

    ok = sin_dato = 0
    for ine, nombre, p in objetivos:
        r = eur_m2_por_municipio(mivau, ine)
        if not r:
            sin_dato += 1
            print(f"  -- {nombre:28} sin dato MIVAU")
            continue
        con.execute(
            "INSERT OR REPLACE INTO via_index VALUES (?,?,?,?,?,?,?,?,?,?)",
            (fecha_act, ine, nombre, "", f"mivau_{ine}", -1,
             r["eur_m2_mediana"], r["p25"], r["p75"], r["alq_mediana_80m2"]))
        ok += 1
        print(f"  OK {nombre:28} {r['eur_m2_mediana']:6.2f} €/m² oficial {r['anio']}")
    con.commit()
    con.close()
    print(f"[FIN] ok={ok} sin_dato={sin_dato}")


if __name__ == "__main__":
    fd = os.open("/tmp/via_mivau.lock", os.O_CREAT | os.O_RDWR)
    try:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("[SKIP] ya hay una ejecución en curso"); sys.exit(0)
    main()
