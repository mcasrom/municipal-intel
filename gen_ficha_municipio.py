import json, sqlite3, os
from collections import defaultdict

DBP = "data/poblacion_municipal.sqlite"
if not os.path.exists(DBP): DBP = "poblacion_municipal.sqlite"

# CONFIG: un ayuntamiento + su dataset de contratos (y datos opcionales)
AYUNTAMIENTOS = [
    {
        "codigo": "30024", "nombre": "Lorca", "provincia": "Murcia",
        "ccaa": "Región de Murcia", "fuente_contratos": "Portal de Transparencia del Ayuntamiento (transparencia.lorca.es)",
        "contratos": "lorca_menores.json", "formales": "lorca_contratos.json",
        "renta": {"neta_persona": 11470, "neta_hogar": 35178, "mediana_uc": 15750, "capital": 13906, "capital_nombre": "Murcia", "anyo": 2022},
        "edad": {"g1": 17481, "g2": 63675, "g3": 14574,
                 "sexo": {"Menos de 16": {"H": 9099, "M": 8382}, "16-64": {"H": 33492, "M": 30183}, "65 o más": {"H": 6396, "M": 8178}}},
        "periodo_menores": "2019-2026", "intel": True,
    },
    {
        "codigo": "29067", "nombre": "Málaga", "provincia": "Málaga",
        "ccaa": "Andalucía", "fuente_contratos": "datos.gob.es (datosabiertos.malaga.eu)",
        "contratos": "malaga_menores.json", "formales": None,
        "renta": {"neta_persona": 13847, "neta_hogar": 36640, "mediana_uc": None, "capital": None, "capital_nombre": None, "anyo": 2022},
        "edad": {"g1": 91371, "g2": 381255, "g3": 105441, "sexo": None},
        "periodo_menores": "2024-2026", "intel": False,
    },
]

def pct(a, b): return round((a - b) / b * 100, 1) if b else None
def fmt_e(n):
    return "—" if n is None else "%s" % format(int(round(n)), ",").replace(",", ".")

def edad_bar(g):
    t = g["g1"] + g["g2"] + g["g3"]
    p1, p2, p3 = g["g1"]/t*100, g["g2"]/t*100, g["g3"]/t*100
    return ('<div style="margin:10px 0"><div style="display:flex;height:18px;border-radius:5px;overflow:hidden">'
            '<div style="width:%.1f%%;background:#38bdf8"></div><div style="width:%.1f%%;background:#6366f1"></div><div style="width:%.1f%%;background:#f87171"></div></div>'
            '<div style="display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;margin-top:4px">'
            '<span>≤15: %.1f%%</span><span>16-64: %.1f%%</span><span>65+: %.1f%%</span></div></div>'
            % (p1, p2, p3, p1, p2, p3))

def generan_ficha(a):
    con = sqlite3.connect(DBP)
    serie = con.execute("SELECT anyo, poblacion FROM poblacion WHERE municipio=? AND sexo='Total' ORDER BY anyo", (a["nombre"],)).fetchall()
    h25 = con.execute("SELECT poblacion FROM poblacion WHERE municipio=? AND sexo='Hombres' AND anyo=2025", (a["nombre"],)).fetchone()
    m25 = con.execute("SELECT poblacion FROM poblacion WHERE municipio=? AND sexo='Mujeres' AND anyo=2025", (a["nombre"],)).fetchone()
    rank = con.execute("SELECT COUNT(*)+1 FROM poblacion WHERE anyo=2025 AND sexo='Total' AND poblacion > (SELECT poblacion FROM poblacion WHERE municipio=? AND anyo=2025 AND sexo='Total')", (a["nombre"],)).fetchone()[0]
    rank_prov = con.execute("""SELECT COUNT(*)+1 FROM poblacion p JOIN catalogo c USING(provincia,municipio)
      WHERE p.anyo=2025 AND p.sexo='Total' AND p.provincia=(SELECT provincia FROM catalogo WHERE municipio=?) AND p.poblacion >
      (SELECT poblacion FROM poblacion WHERE municipio=? AND anyo=2025 AND sexo='Total')""", (a["nombre"], a["nombre"])).fetchone()[0]
    con.close()
    p25 = serie[-1][1]; p96 = serie[0][1]; var = pct(p25, p96)

    menores = json.load(open(a["contratos"]))
    m = [x for x in menores if x["importe"] and x["importe"] <= 40000]
    for x in m:
        x["empresa"] = x.get("adjudicatario") or x.get("razon") or "—"
    by = defaultdict(list)
    for x in m: by[x["empresa"]].append(x)
    top_num = sorted(by.items(), key=lambda kv: -len(kv[1]))[:12]
    top_imp = sorted(by.items(), key=lambda kv: -sum(i["importe"] for i in kv[1]))[:10]
    total_gasto = sum(x["importe"] for x in m)

    formales = None
    if a.get("formales"):
        formales = json.load(open(a["formales"]))

    # tablas
    row_num = ""
    for i, (ad, items) in enumerate(top_num, 1):
        tot = sum(x["importe"] for x in items)
        row_num += "<tr><td>%d</td><td>%s</td><td class='r'><b>%d</b></td><td class='r'>%s €</td><td class='r'>%s €</td></tr>" % (i, ad, len(items), fmt_e(tot), fmt_e(tot/len(items)))
    row_imp = ""
    for i, (ad, items) in enumerate(top_imp, 1):
        tot = sum(x["importe"] for x in items)
        row_imp += "<tr><td>%d</td><td>%s</td><td class='r'><b>%s €</b></td><td class='r'>%d</td></tr>" % (i, ad, fmt_e(tot), len(items))
    row_form = ""
    if formales:
        for c in formales[:15]:
            imp = fmt_e(c["importe"]) + " €" if c["importe"] else "—"
            row_form += "<tr><td>%s</td><td>%s</td><td>%s</td><td class='r'>%s</td><td>%s</td><td>%s</td></tr>" % (c["expediente"], c["objeto"][:80], c["procedimiento"], imp, c["adjudicatario"][:40], c["estado"])

    flag = [(ad, len(items)) for ad, items in top_num if len(items) >= 10]
    alerta = ""
    if flag:
        alerta = ("<div class='alert'><b>Posible troceado:</b> proveedores con volumen alto de contratos menores en %s — %s. Contratos de importe bajo repetidos es el patrón clásico de fraccionamiento del gasto.</div>"
                  % (a["periodo_menores"], ", ".join("<b>%d</b> a %s" % (n, ad) for ad, n in flag[:6])))

    # edad
    edad_html = ""
    if a.get("edad"):
        e = a["edad"]
        t = e["g1"] + e["g2"] + e["g3"]
        edad_html = edad_bar(e)
        if e.get("sexo"):
            rows = "".join("<tr><td>%s</td><td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td></tr>" % (
                gr, fmt_e(sx["H"]), fmt_e(sx["M"]), fmt_e(e["g1"] if gr=="Menos de 16" else (e["g2"] if gr=="16-64" else e["g3"])))
                for gr, sx in e["sexo"].items())
            edad_html += "<h3 style='font-size:14px;margin:10px 0 6px'>Sexo por grupo de edad (Censo 2021)</h3><table><tr><th>Grupo</th><th class='r'>Hombres</th><th class='r'>Mujeres</th><th class='r'>Total</th></tr>" + rows + "</table>"

    # renta
    renta_html = ""
    if a.get("renta"):
        r = a["renta"]
        kpis = "<div class='grid'><div class='kpi'><b>%s €</b><span>renta neta/persona (%d)</span></div><div class='kpi'><b>%s €</b><span>renta neta/hogar</span></div>" % (fmt_e(r["neta_persona"]), r["anyo"], fmt_e(r["neta_hogar"]))
        if r.get("mediana_uc"):
            kpis += "<div class='kpi'><b>%s €</b><span>mediana por UC</span></div>" % fmt_e(r["mediana_uc"])
        if r.get("capital"):
            kpis += "<div class='kpi'><b>%s €</b><span>%s capital (renta/persona)</span></div>" % (fmt_e(r["capital"]), r["capital_nombre"])
        kpis += "</div>"
        renta_html = "<h2>Renta de los hogares (INE · Atlas de distribución de renta)</h2>" + kpis

    slug = a["nombre"].lower().replace("á","a").replace("á","a").replace("á","a").replace("á","a")
    ficha_name = "ficha_" + slug + ".html"

    HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>@@NOMBRE@@ · Municipal Intelligence</title>
<meta name="description" content="Ficha de inteligencia municipal de @@NOMBRE@@: población INE 1996-2025 y contratos del Ayuntamiento con detección de posibles troceados.">
<link rel="canonical" href="https://municipal.viajeinteligencia.com/@@FICHA@@">
<link rel="icon" type="image/png" href="icon-192.png">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Dataset","name":"@@NOMBRE@@: población y contratos del Ayuntamiento",
"description":"Población oficial de @@NOMBRE@@ (INE 1996-2025) y contratos menores del Ayuntamiento con análisis de anomalías.",
"url":"https://municipal.viajeinteligencia.com/@@FICHA@@","license":"https://creativecommons.org/licenses/by/4.0/",
"spatialCoverage":{"@type":"Place","name":"@@NOMBRE@@","address":{"@type":"PostalAddress","addressCountry":"ES","addressRegion":"@@PROV@@}}}
</script>
<style>
:root{--bg:#0f172a;--card:#1e293b;--fg:#e2e8f0;--mut:#94a3b8;--acc:#38bdf8;--rojo:#f87171;--verde:#4ade80}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg);line-height:1.6}
.wrap{max-width:960px;margin:0 auto;padding:22px}
h1{font-size:26px}
h2{font-size:17px;color:var(--acc);margin:24px 0 10px;border-bottom:1px solid #334155;padding-bottom:6px}
.mut{color:var(--mut);font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:14px 0}
.kpi{background:var(--card);border-radius:10px;padding:14px}
.kpi b{display:block;font-size:21px}
.kpi span{font-size:11px;color:var(--mut)}
.pos{color:var(--verde)}.neg{color:var(--rojo)}
table{width:100%;border-collapse:collapse;font-size:13px;background:var(--card);border-radius:8px;overflow:hidden}
th{background:#0f172a;color:var(--mut);text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase}
td{padding:8px 10px;border-top:1px solid #1e293b}
td.r{text-align:right}
.alert{background:#7f1d1d;border:1px solid #b91c1c;border-radius:8px;padding:12px 14px;margin:12px 0}
.alert b{color:#fca5a5}
.src{font-size:10px;color:var(--mut);margin-top:30px;line-height:1.6}
a{color:var(--acc)}
</style></head><body><div class="wrap">

<h1>@@NOMBRE@@ <span class="mut">· Municipal Intelligence</span></h1>
<div class="mut">Ayuntamiento de @@NOMBRE@@ · @@CCAA@@ · código INE @@COD@@ · datos trazables (INE + @@FUENTE@@)</div>

<h2>Población (INE, Revisión del Padrón)</h2>
<div class="grid">
  <div class="kpi"><b>@@P25@@</b><span>habitantes (2025)</span></div>
  <div class="kpi"><b>@@P96@@</b><span>en 1996</span></div>
  <div class="kpi"><b class="@@SIGN@@">@@VAR@@</b><span>variación 1996 → 2025</span></div>
  <div class="kpi"><b>@@RANK@@º</b><span>rank nacional · @@RANKPROV@@º de su provincia</span></div>
</div>
<div class="grid">
  <div class="kpi"><b>@@H25@@</b><span>hombres (2025)</span></div>
  <div class="kpi"><b>@@M25@@</b><span>mujeres (2025)</span></div>
  <div class="kpi"><b>@@H25PCT@@</b><span>% hombres</span></div>
</div>
@@RENTA@@

<h2>Estructura de edad <span style="color:#94a3b8;font-size:13px">(Censo 2021)</span></h2>
@@EDAD_AVISO@@
@@EDAD@@

<h2>Contratos menores del Ayuntamiento (@@PERIODO@@)</h2>
<div class="grid">
  <div class="kpi"><b>@@NMEN@@</b><span>contratos menores</span></div>
  <div class="kpi"><b>@@GASTO@@ €</b><span>gasto menor (con importe)</span></div>
@@NFOR_KPI@@
</div>
@@ALERTA@@
<h2>Proveedores por número de contratos menores</h2>
<table><tr><th>#</th><th>Proveedor</th><th class="r">Contratos</th><th class="r">Importe</th><th class="r">Media</th></tr>@@ROWS_NUM@@</table>
<h2>Proveedores por importe</h2>
<table><tr><th>#</th><th>Proveedor</th><th class="r">Importe</th><th class="r">Contratos</th></tr>@@ROWS_IMP@@</table>
@@FORMALES@@

<div class="src">Fuentes: INE · Cifras oficiales de población (Revisión del Padrón Municipal), población a 01/01/2025 publicada el 11/12/2025 · INE Atlas de renta (2022) · Censo 2021 (estructura de edad, decenal; próximo 2031) · contratos: @@FUENTE@@. Los importes >40.000 € se excluyen del análisis de menores. Sin datos inventados. © 2026 M. Castillo.</div>
</div></body></html>"""

    T = {
        "@@NOMBRE@@": a["nombre"], "@@CCAA@@": a["ccaa"], "@@COD@@": a["codigo"],
        "@@FUENTE@@": a["fuente_contratos"], "@@FICHA@@": ficha_name,
        "@@PROV@@": a["provincia"], "@@P25@@": fmt_e(p25), "@@P96@@": fmt_e(p96),
        "@@SIGN@@": "pos" if var >= 0 else "neg", "@@VAR@@": ("+" if var >= 0 else "") + str(var),
        "@@RANK@@": str(rank), "@@RANKPROV@@": str(rank_prov),
        "@@H25@@": fmt_e(h25[0] if h25 else 0), "@@M25@@": fmt_e(m25[0] if m25 else 0),
        "@@H25PCT@@": ("%.1f%%" % (h25[0]/(h25[0]+m25[0])*100)) if h25 and m25 else "—",
        "@@RENTA@@": renta_html, "@@EDAD@@": edad_html,
        "@@EDAD_AVISO@@": ('<div style="background:#7f1d1d;border:1px solid #b91c1c;border-radius:8px;padding:10px 12px;margin:10px 0;font-size:12px"><b style="color:#fca5a5">Aviso:</b> el desglose por edad procede del <b>Censo 2021</b> (decenal; el siguiente es <b>2031</b>). La población total y evolución son del <b>Padrón 2025</b>.</div>' if a.get("edad") else ""),
        "@@NMEN@@": str(len(m)), "@@GASTO@@": fmt_e(total_gasto),
        "@@NFOR_KPI@@": ('<div class="kpi"><b>%s</b><span>contratos formales</span></div>' % len(formales)) if formales else "",
        "@@ALERTA@@": alerta, "@@ROWS_NUM@@": row_num, "@@ROWS_IMP@@": row_imp,
        "@@FORMALES@@": ('<h2>Contratos formales (publicados actualmente)</h2><table><tr><th>Exp.</th><th>Objeto</th><th>Proced.</th><th class="r">Importe</th><th>Adjudicatario</th><th>Estado</th></tr>' + row_form + "</table>") if formales else "",
        "@@PERIODO@@": a["periodo_menores"],
    }
    html = HTML
    for k, v in T.items():
        html = html.replace(k, str(v))
    with open(os.path.join("dashboard", ficha_name), "w", encoding="utf-8") as f:
        f.write(html)
    print("OK", ficha_name, "|", len(html)//1024, "KB | menores:", len(m), "| gasto:", fmt_e(total_gasto))
    return a

if __name__ == "__main__":
    # lorca_intel.json (panel lateral del mapa, solo para Lorca)
    import sqlite3 as _sq
    for a in AYUNTAMIENTOS:
        if a.get("intel"):
            con = _sq.connect(DBP)
            p25 = con.execute("SELECT poblacion FROM poblacion WHERE municipio=? AND anyo=2025 AND sexo='Total'", (a["nombre"],)).fetchone()
            p96 = con.execute("SELECT poblacion FROM poblacion WHERE municipio=? AND anyo=1996 AND sexo='Total'", (a["nombre"],)).fetchone()
            rk = con.execute("SELECT COUNT(*)+1 FROM poblacion WHERE anyo=2025 AND sexo='Total' AND poblacion > (SELECT poblacion FROM poblacion WHERE municipio='Lorca' AND anyo=2025 AND sexo='Total')").fetchone()[0]
            con.close()
            p25 = p25[0] if p25 else 0; p96 = p96[0] if p96 else 0
            menores = [x for x in json.load(open(a["contratos"])) if x["importe"] and x["importe"] <= 40000]
            by = defaultdict(list)
            for x in menores: by[x.get("adjudicatario") or x.get("razon")].append(x)
            top = sorted(by.items(), key=lambda kv: -len(kv[1]))[:8]
            _var = pct(p25, p96)
            intel = {
                "n": a["nombre"], "p25": fmt_e(p25), "var": ("+" if _var >= 0 else "") + str(_var),
                "rank": rk, "nmen": len(menores),
                "gasto": fmt_e(sum(x["importe"] for x in menores)),
                "nfor": len(json.load(open(a["formales"]))) if a.get("formales") else 0,
                "conc": "—", "alerta": [{"n": ad, "c": len(items)} for ad, items in top if len(items) >= 10][:5],
                "top": [{"n": ad, "c": len(items), "imp": fmt_e(sum(x["importe"] for x in items))} for ad, items in top],
                "renta": {"neta_persona": a["renta"]["neta_persona"], "neta_hogar": a["renta"]["neta_hogar"], "murcia_capital": a["renta"].get("capital"), "anyo": a["renta"]["anyo"]},
                "edad": {"g1": a["edad"]["g1"], "g2": a["edad"]["g2"], "g3": a["edad"]["g3"]},
            }
            with open("dashboard/data/lorca_intel.json", "w") as f:
                json.dump(intel, f, ensure_ascii=False)
            print("lorca_intel.json generado")

if __name__ == "__main__":
    for a in AYUNTAMIENTOS:
        generan_ficha(a)
    print("fichas generadas:", len(AYUNTAMIENTOS))
