#!/usr/bin/env python3
# prueba_slugs_via.py — para cada ciudad fallida >=50k, prueba candidatos y verifica titulo
import re, csv, json, time, unicodedata
from pathlib import Path
import urllib.request

CSV = Path.home() / "municipal-intel/dashboard/data/csv/poblacion-municipal-espana-1996-2025.csv"
LOG = Path.home() / "municipal-intel/logs_via_full.log"
OUT = Path.home() / "scripts/slugs_rescatados.json"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"}

pob = {}
for r in csv.DictReader(open(CSV)):
    if r["anyo"] == "2025":
        pob[r["municipio"]] = int(r["poblacion"])

fallidas = set()
for line in open(LOG):
    m = re.match(r"\s+XX (.+?)\s+ERROR", line)
    if m:
        fallidas.add(m.group(1).strip())
grandes = [n for n in fallidas if pob.get(n, 0) >= 50000]
grandes.sort(key=lambda n: -pob[n])

def base_slug(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def candidatos(nombre):
    cands = []
    # articulo final INE -> prefijo: "Coruna, A" -> "a-coruna"
    mm = re.match(r"^(.*?),\s*(L'|El|La|Los|Las|A|O|Os|As)$", nombre, re.I)
    if mm:
        cands.append(base_slug(f"{mm.group(2)}-{mm.group(1)}"))
        cands.append(base_slug(mm.group(1)))
    else:
        cands.append(base_slug(nombre))
    # bilingue con barra: probar cada parte
    if "/" in nombre:
        for parte in nombre.split("/"):
            p = base_slug(parte)
            if p and p not in cands:
                cands.append(p)
    extras = {
        "hospitalet-de-llobregat-l": ["l-hospitalet-de-llobregat", "lhospitalet-de-llobregat"],
        "vitoria-gasteiz": ["vitoria-gasteiz", "vitoria"],
        "jerez-de-la-frontera": ["jerez"],
        "san-sebastian": ["san-sebastian", "donostia-san-sebastian"],
        "vila-real": ["vila-real", "villarreal"],
        "sagunt-sagunto": ["sagunto", "sagunt"],
        "alcoi-alcoy": ["alcoy", "alcoi"],
        "elx-elche": ["elche", "elx"],
        "pamplona-iruna": ["pamplona", "iruna"],
        "santa-lucia-de-tirajana": ["santa-lucia-de-tirajana"],
        "san-bartolome-de-tirajana": ["san-bartolome-de-tirajana"],
    }
    for k, v in extras.items():
        if base_slug(nombre) == k:
            cands = v + [c for c in cands if c not in v]
    vistos, out = set(), []
    for c in cands:
        if c and c not in vistos:
            vistos.add(c)
            out.append(c)
    return out[:4]

rescatados, sin_solucion = {}, []
for n in grandes:
    token = base_slug(n.split("/")[0].split(",")[0])[:8]
    hallado = None
    for c in candidatos(n):
        url = f"https://www.pisos.com/alquiler/pisos-{c}/"
        try:
            req = urllib.request.Request(url, headers=UA)
            html = urllib.request.urlopen(req, timeout=15).read(60000).decode("utf-8", "replace")
            tmatch = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
            titulo = unicodedata.normalize("NFD", (tmatch.group(1) if tmatch else "").lower()).encode("ascii", "ignore").decode()
            if token in titulo:
                hallado = c
                break
        except Exception:
            pass
        time.sleep(2)
    if hallado:
        rescatados[n] = hallado
        print(f"RESCATADO  {n} -> {hallado}")
    else:
        sin_solucion.append(n)
        print(f"SIN PAGINA {n}")
    time.sleep(2)

OUT.write_text(json.dumps({"rescatados": rescatados, "sin_pagina": sin_solucion}, ensure_ascii=False, indent=1))
print(f"\ntotal rescatados={len(rescatados)} sin_pagina={len(sin_solucion)} -> {OUT}")
