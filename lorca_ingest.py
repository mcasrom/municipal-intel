import json, re, urllib.request, html as htmlmod

BASE = "https://transparencia.lorca.es"

def fetch(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "municipal-intel/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("latin-1")

def limpiar(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = htmlmod.unescape(s)
    return " ".join(s.split())

def scrape_formales():
    html = fetch("/todos-contratos/")
    tabla = re.search(r"<table.*?</table>", html, re.S)
    if not tabla:
        return []
    filas = re.findall(r"<tr[^>]*>(.*?)</tr>", tabla.group(0), re.S)
    out = []
    for f in filas[1:]:
        celdas = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", f, re.S)
        vals = [limpiar(c) for c in celdas]
        if not vals or len(vals) < 9:
            continue
        importe = re.sub(r"[\s\xa0\u0080]+", "", vals[4].replace(".", "").replace(",", "."))
        try:
            importe = float(importe)
        except ValueError:
            importe = None
        out.append({
            "expediente": vals[0], "objeto": vals[1], "procedimiento": vals[2],
            "tipo": vals[3], "importe": importe, "fecha_pres": vals[5],
            "lotes": vals[6], "estado": vals[7], "adjudicatario": vals[8],
            "duracion": vals[10] if len(vals) > 10 else "",
        })
    return out

if __name__ == "__main__":
    contratos = scrape_formales()
    print("contratos formales:", len(contratos))
    for c in contratos[:5]:
        print("  ", c["expediente"], "|", c["adjudicatario"][:35], "|", c["importe"], "|", c["estado"])
    with open("lorca_contratos.json", "w", encoding="utf-8") as f:
        json.dump(contratos, f, ensure_ascii=False, indent=1)
    print("guardado: lorca_contratos.json")
