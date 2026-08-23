#!/usr/bin/env python3
# triage_errores_via.py — clasifica los XX del ciclo VIA por poblacion y tipo de error
import re, csv
from pathlib import Path

LOG = Path.home() / "municipal-intel/logs_via_full.log"
CSV = Path.home() / "municipal-intel/dashboard/data/csv/poblacion-municipal-espana-1996-2025.csv"

pob = {}
for r in csv.DictReader(open(CSV)):
    if r["anyo"] == "2025":
        pob[r["municipio"]] = int(r["poblacion"])

tipos = {"404": [], "otra_ciudad": [], "otros": []}
for line in open(LOG):
    m = re.match(r"\s+XX (.+?)\s+(ERROR .*)$", line)
    if not m:
        continue
    nombre, err = m.groups()
    nombre = nombre.strip()
    if "404" in err:
        tipos["404"].append(nombre)
    elif "otra ciudad" in err:
        tipos["otra_ciudad"].append(nombre)
    else:
        tipos["otros"].append(nombre)

print(f"=== TRIAGE {sum(len(v) for v in tipos.values())} errores ===")
for t, lst in tipos.items():
    print(f"\n--- {t}: {len(lst)} ---")
    # ordenar por poblacion desc; los sin match de poblacion al final
    lst.sort(key=lambda n: -pob.get(n, 0))
    for n in lst[:20]:
        print(f"  {pob.get(n, 0):>7}  {n}")
    if len(lst) > 20:
        restantes = [pob.get(n, 0) for n in lst[20:]]
        print(f"  ... y {len(lst)-20} mas (max pob {max(restantes) if restantes else 0})")

grandes = sorted((n for lst in tipos.values() for n in lst if pob.get(n, 0) >= 50000),
                 key=lambda n: -pob[n])
print(f"\n=== RESCATABLES potenciales (>=50k hab): {len(grandes)} ===")
for n in grandes:
    print(f"  {pob[n]:>7}  {n}")
