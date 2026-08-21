import json, re, os, subprocess, urllib.request, html as htmlmod

BASE = "https://transparencia.lorca.es/contratos-menores/pdf"
PDF_DIR = "lorca_pdf"

def fetch(path, binary=False):
    from urllib.parse import quote
    url = BASE + "/" + quote(path.lstrip("/"))
    req = urllib.request.Request(url, headers={"User-Agent": "municipal-intel/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def descargar_todos():
    html = urllib.request.urlopen(urllib.request.Request(
        "https://transparencia.lorca.es/contratos-menores/",
        headers={"User-Agent": "municipal-intel/0.1"}), timeout=30).read().decode("latin-1")
    pdfs = sorted(set(re.findall(r'href="([^"]*(?:Contratos|contratos|trimestre|Publicacion)[^"]*\.pdf)"', html)))
    ok = 0
    for p in pdfs:
        name = os.path.basename(p)
        year = re.search(r"20\d{2}", p).group(0)
        dest = os.path.join(PDF_DIR, year + "_" + name.replace(" ", "_"))
        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            ok += 1
            continue
        try:
            data = fetch("/" + year + "/" + p.split("/")[-1])
            open(dest, "wb").write(data)
            ok += 1
        except Exception as e:
            print("  ERROR", p, e)
    print("PDFs descargados:", ok, "de", len(pdfs))
    return pdfs

def parse_pdf(pdf):
    txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
    registros = []
    CIF = re.compile(r"^([A-Z][0-9]{8})\s+(.+)$")
    # formato actual (2024-2026): punto = decimal, SIN separador de miles: "48278.97 €"
    IMPORTE_EUR = re.compile(r"(\d+(?:\.\d{2})?)\s*[€]\s*(.*)$")
    # formato antiguo (2019-2023): coma = decimal, sin simbolo: "296,93 25/09/2019"
    IMPORTE_OLD = re.compile(r"(\d+[.,]\d{2})\s+\d{1,2}/\d{1,2}/\d{4}")
    # sufijos de forma societaria para separar razon de objeto
    EMP = re.compile(r"(.+?)\s*((?:S\.L\.U\.?|S\.A\.U\.?|S\.L\.C\.?|S\.C\.?O?O?P?\.?|C\.B\.|S\.L\.|S\.A\.|L\.T\.D\.?|Y OTROS|E\.I\.|C\.S\.|S\.L\.B\.|S\.COOP)\b|$)", re.I)
    lineas = txt.splitlines()
    i = 0
    while i < len(lineas):
        m = CIF.match(lineas[i].strip())
        if not m:
            i += 1
            continue
        cif = m.group(1)
        resto = m.group(2).strip()
        importe = dur = None
        objeto_lines = []
        mi = IMPORTE_EUR.search(resto)
        if mi:
            cuerpo = resto[:mi.start()].strip()
            importe = float(mi.group(1))
            dur = mi.group(2).strip()
            i += 1
        else:
            cuerpo = resto
            j = i + 1
            while j < len(lineas):
                lj = lineas[j].strip()
                mj = IMPORTE_EUR.search(lj)
                if mj:
                    importe = float(mj.group(1))
                    dur = mj.group(2).strip()
                    j += 1
                    break
                if re.match(r"^[A-Z][0-9]{8}\s+", lj):
                    break
                if lj:
                    objeto_lines.append(lj)
                j += 1
            i = j
        # separar razon de objeto
        em = EMP.match(cuerpo)
        if em and em.group(2):
            razon = (em.group(1) + " " + em.group(2)).strip()
            objeto_txt = cuerpo[em.end():].strip()
        else:
            razon = cuerpo
            objeto_txt = ""
        objeto = (" ".join(objeto_lines) + " " + objeto_txt).strip()
        # formato antiguo: importe en el objeto sin €
        if importe is None:
            mo = IMPORTE_OLD.search(objeto)
            if mo:
                try:
                    importe = float(mo.group(1).replace(",", "."))
                except ValueError:
                    importe = None
        if razon:
            registros.append({"cif": cif, "razon": razon, "objeto": objeto,
                              "importe": importe, "duracion": dur})
    return registros

if __name__ == "__main__":
    os.makedirs(PDF_DIR, exist_ok=True)
    descargar_todos()
    todos = []
    for f in sorted(os.listdir(PDF_DIR)):
        if not f.endswith(".pdf"):
            continue
        regs = parse_pdf(os.path.join(PDF_DIR, f))
        m_year = re.search(r"(20\d{2})", f)
        anyo = m_year.group(1) if m_year else "?"
        for r in regs:
            r["periodo"] = anyo + "/" + f
            todos.append(r)
        print(f"  {f}: {len(regs)} contratos")
    print("TOTAL menores parseados:", len(todos))
    with open("lorca_menores.json", "w", encoding="utf-8") as fh:
        json.dump(todos, fh, ensure_ascii=False, indent=1)
    print("guardado: lorca_menores.json")
