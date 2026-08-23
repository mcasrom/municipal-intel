#!/usr/bin/env python3
# iv_vaciado.py — Índice de Vaciamiento (IV) v0: componente demográfico puro
# IV = 100 · clamp(-(ΔPoblación 10 años)/0.15, 0, 1)
# v1 añadirá: envejecimiento (25%), saldo vegetativo (20%), paro vs provincia (20%) — ver PROPUESTAS
import json, sqlite3, math
from pathlib import Path

BASE = Path.home() / "municipal-intel"
DB = BASE / "data/poblacion_municipal.sqlite"
OUT = BASE / "dashboard/data/via/vaciado.json"
UMBRAL_LOSING = 0.15   # pérdida del 15% en 10 años => score 1.0
CAP_PROY = 0.40

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
rows = con.execute("""
    SELECT provincia, municipio,
           MAX(CASE WHEN anyo=2015 THEN poblacion END),
           MAX(CASE WHEN anyo=2025 THEN poblacion END),
           MAX(CASE WHEN anyo=1996 THEN poblacion END)
    FROM poblacion WHERE sexo='Total'
    GROUP BY provincia, municipio HAVING COUNT(*) >= 11
""").fetchall()
con.close()

res = []
for prov, mun, p15, p25, p96 in rows:
    if not p15 or not p25 or p15 < 1000:      # sin serie o pueblo minúsculo: fuera
        continue
    d10 = (p25 - p15) / p15
    iv = round(100 * clamp(-d10 / UMBRAL_LOSING))
    # proyección simple 2040 con el ritmo decenal, limitada a ±CAP_PROY
    ritmo = max(-CAP_PROY, min(CAP_PROY * 0.6, d10)) / 10
    p2040 = int(p25 * (1 + ritmo) ** 15)
    res.append({
        "provincia": prov, "municipio": mun, "pob_2025": p25,
        "d10_pct": round(d10 * 100, 1),
        "iv": iv,
        "categoria": ("vaciado critico" if iv >= 60 else
                      "riesgo alto" if iv >= 40 else
                      "tension demografica" if iv >= 20 else "estable"),
        "p2040_proyectada": p2040,
        "_p96": p96,
    })

res.sort(key=lambda x: (-x["iv"], x["pob_2025"]))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "fecha_generado": __import__("datetime").datetime.utcnow().isoformat(),
    "metodologia": "IV v0 = solo componente poblacional (Δ10 años, -15%=>100). "
                   "v1 sumara envejecimiento+saldo vegetativo+paro (ver docs/PROPUESTAS-datos-gob.md)",
    "total_evaluados": len(res),
    "municipios": [{k: v for k, v in r.items() if k != "_p96"} for r in res],
}, ensure_ascii=False, indent=1))

n_cat = {}
for r in res:
    n_cat[r["categoria"]] = n_cat.get(r["categoria"], 0) + 1
print(f"evaluados: {len(res)} municipios con serie 2015-2025")
print("por categoria:", json.dumps(n_cat, ensure_ascii=False))
print("\nTOP-15 VACIADOS (entre municipios >=1000 hab hoy):")
big = [r for r in res if r["pob_2025"] >= 1000]
for r in big[:15]:
    print(f"  {r['iv']:3} IV | {r['municipio']:24} ({r['provincia'][:14]:14}) {r['d10_pct']:+6.1f}%  2025:{r['pob_2025']:6} -> 2040~{r['p2040_proyectada']}")
