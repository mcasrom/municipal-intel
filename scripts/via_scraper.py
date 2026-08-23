#!/usr/bin/env python3
# via_scraper.py — Índice VIA: €/m² alquiler por municipio (fuente: pisos.com)
# Sprint F / H1.2 · politeness 4s±1 · lock flock · validación estricta de ciudad
import re, csv, json, html as ihtml, sqlite3, statistics, random, subprocess, sys, time, os
from pathlib import Path
from urllib.request import Request, urlopen
from datetime import datetime, timezone

BASE = Path.home() / "municipal-intel"
CSV_POB = BASE / "dashboard/data/csv/poblacion-municipal-espana-1996-2025.csv"
DB_PATH = BASE / "dashboard/data/via/via.db"
JSON_OUT = BASE / "dashboard/data/via/index.json"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
      "Accept-Language": "es-ES,es;q=0.9"}
MIN_POB, MAX_PAGS, MIN_ANUNCIOS = 20000, 2, 5
STOPWORDS = {"de", "del", "la", "el", "los", "las"}
# municipios sin pagina propia en pisos.com (verificado 23/Ago): no gastar peticiones
SKIP = {"Palmas de Gran Canaria, Las", "Santa Coloma de Gramenet"}
# slug y token esperado cuando la normalización automática no basta
MANUAL = {
    "Castelló de la Plana": ("castellon", "castello"),
    "Palmas de Gran Canaria, Las": ("las-palmas-de-gran-canaria", "palmas"),
    "Alacant/Alicante": ("alicante", "alicante"),
}

RE_PRECIO = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d{3,5})\s*€")
RE_M2 = re.compile(r"(\d{2,4})\s*m²")
RE_TITULO = re.compile(r"<title>([^<]*)</title>", re.I)


def normaliza(s: str) -> str:
    s = s.lower()
    for a, b in [("á", "a"), ("é", "e"), ("è", "e"), ("í", "i"), ("ó", "o"), ("ò", "o"),
                 ("ú", "u"), ("ü", "u"), ("ñ", "n"), ("ç", "c"), ("à", "a"), ("ì", "i"), ("ù", "u"),
                 ("â", "a"), ("ê", "e"), ("î", "i"), ("ô", "o"), ("û", "u"), ("ë", "e"), ("ï", "i")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9-]+", "", re.sub(r"\s+", "-", s.strip()))


def tokens_clave(nombre: str) -> str:
    palabras = [p for p in normaliza(nombre).split("-") if p not in STOPWORDS]
    return " ".join(palabras)


def get(url: str, reintentos=2) -> str:
    for i in range(reintentos + 1):
        try:
            req = Request(url, headers=UA)
            return ihtml.unescape(urlopen(req, timeout=25).read().decode("utf-8", "ignore"))
        except Exception:
            if i == reintentos:
                raise
            time.sleep(8 * (i + 1))


def extraer(html_txt: str):
    pares = []
    for b in re.split(r'class="ad-preview__title"', html_txt)[1:]:
        p, m = RE_PRECIO.search(b), RE_M2.search(b)
        if p and m:
            precio, m2 = float(p.group(1).replace(".", "")), int(m.group(1))
            if 200 <= precio <= 5000 and 20 <= m2 <= 300:
                r = precio / m2
                if 3 <= r <= 40:
                    pares.append((precio, m2, round(r, 2)))
    return pares


def scrape_ciudad(nombre: str):
    slug, expect = MANUAL.get(nombre, (normaliza(nombre), None))
    expect = expect or tokens_clave(nombre).replace(" ", "-").replace("-", " ")
    todos, paginas_usadas = [], 0
    for n in range(1, MAX_PAGS + 1):
        url = f"https://www.pisos.com/alquiler/pisos-{slug}/" if n == 1 else f"https://www.pisos.com/alquiler/pisos-{slug}/{n}/"
        h = get(url)
        t = (RE_TITULO.search(h) or [None, ""])[1].lower()
        if n == 1 and expect.split()[0] not in normaliza(t):
            raise ValueError(f"slug apunta a otra ciudad: {t.strip()[:60]}")
        pares = extraer(h)
        todos += pares
        paginas_usadas = n
        if len(pares) < 10:
            break
        time.sleep(4 + random.uniform(0, 1))
    if len(todos) < MIN_ANUNCIOS:
        return None, slug, paginas_usadas
    ratios = sorted(r for _, _, r in todos)
    med = statistics.median(ratios)
    return {
        "anuncios": len(todos), "eur_m2_mediana": round(med, 2),
        "p25": round(ratios[len(ratios)//4], 2), "p75": round(ratios[3*len(ratios)//4], 2),
        "alq_mediana_80m2": int(round(med * 80)),
    }, slug, paginas_usadas


def municipios_objetivo():
    out = []
    for r in csv.DictReader(open(CSV_POB)):
        if r["anyo"] == "2025" and int(r["poblacion"]) >= MIN_POB:
            out.append((r["codigo_ine"], r["provincia"], r["municipio"], int(r["poblacion"])))
    return sorted(out, key=lambda x: -x[3])


def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("""CREATE TABLE IF NOT EXISTS via_index (
        fecha TEXT, codigo_ine TEXT, municipio TEXT, provincia TEXT, slug TEXT,
        anuncios INTEGER, eur_m2_mediana REAL, p25 REAL, p75 REAL, alq_mediana_80m2 REAL,
        PRIMARY KEY(fecha, codigo_ine))""")
    db.execute("""CREATE TABLE IF NOT EXISTS via_runs (
        fecha TEXT, ok INTEGER, sin_datos INTEGER, errores INTEGER, duracion_s REAL, PRIMARY KEY(fecha))""")

    munis = municipios_objetivo()
    if limit:
        munis = munis[:limit]
    print(f"[{fecha}] inicio: {len(munis)} municipios >= {MIN_POB} hab")
    t0, ok, sin_datos, errores, resultados = time.time(), 0, 0, 0, []
    for ine, prov, nombre, pob in munis:
        if nombre in SKIP:
            sin_datos += 1
            continue
        try:
            res, slug, pags = scrape_ciudad(nombre)
            time.sleep(4 + random.uniform(0, 1))
            if res:
                db.execute("INSERT OR REPLACE INTO via_index VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (fecha, ine, nombre, prov, slug, res["anuncios"], res["eur_m2_mediana"],
                            res["p25"], res["p75"], res["alq_mediana_80m2"]))
                resultados.append({"ine": ine, "nombre": nombre, "poblacion": pob, "slug": slug, **res})
                ok += 1
                print(f"  OK {nombre:28} {res['eur_m2_mediana']:6.2f} €/m² ({res['anuncios']} anunc, {pags} pág)")
            else:
                sin_datos += 1
                print(f"  -- {nombre:28} sin datos suficientes")
        except Exception as e:
            errores += 1
            print(f"  XX {nombre:28} ERROR {type(e).__name__}: {str(e)[:60]}")
    dur = round(time.time() - t0)
    db.execute("INSERT OR REPLACE INTO via_runs VALUES (?,?,?,?,?)", (fecha, ok, sin_datos, errores, dur))
    db.commit()
    JSON_OUT.write_text(json.dumps({"fecha": fecha, "generado": datetime.now(timezone.utc).isoformat(),
                                    "total_ok": ok, "municipios": sorted(resultados, key=lambda x: -x["poblacion"])},
                                   ensure_ascii=False, indent=1))
    print(f"[FIN] ok={ok} sin_datos={sin_datos} errores={errores} duración={dur//60}m{dur%60}s")
    gen = BASE / "scripts/gen_alquiler_page.py"
    if gen.exists():
        r = subprocess.run([sys.executable, str(gen)], capture_output=True, text=True)
        print("[pagina]", r.stdout.strip() or r.stderr.strip()[-120:])


if __name__ == "__main__":
    fd = os.open("/tmp/via.lock", os.O_CREAT | os.O_RDWR)
    try:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("[SKIP] ya hay una ejecución en curso"); sys.exit(0)
    main()
