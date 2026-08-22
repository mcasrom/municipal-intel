import urllib.request, re, os, json, sqlite3

# Ingesta de contratos menores del Ayuntamiento de Málaga (datos.gob.es)
# 11 trimestres: 2023-Q4 a 2026-Q2. Ficheros XLSX/ODS en datosabiertos.malaga.eu

DATASETS = [
    "l01290672-contratos-menores-4-trimestre-2023-ayuntamiento-de-malaga",
    "l01290672-contratos-menores-1-trimestre-2024-ayuntamiento-de-malaga",
    "l01290672-contratos-menores-2-trimestre-2024-ayuntamiento-de-malaga",
    "l01290672-contratos-menores-3-trimestre-2024-ayuntamiento-de-malaga",
    "l01290672-contratos-menores-4-trimestre-2024-ayuntamiento-de-malaga",
    "l01290672-contratos-menores-1-trimestre-2025-ayuntamiento-de-malaga",
    "l01290672-contratos-menores-2-trimestre-2025-ayuntamiento-de-malaga",
    "l01290672-contratos-menores-3-trimestre-2025-ayuntamiento-de-malaga",
    "l01290672-contratos-menores-4-trimestre-2025-ayuntamiento-de-malaga",
    "l01290672-contratos-menores-1er-trimestre-2026-ayuntamiento-de-malaga",
    "l01290672-contratos-menores-2o-trimestre-2026-ayuntamiento-de-malaga",
]

def fetch(u):
    req = urllib.request.Request(u, headers={"User-Agent": "municipal-intel/0.1"})
    return urllib.request.urlopen(req, timeout=60).read()

def parse_xlsx(data, url):
    import io
    if url.endswith(".ods"):
        import pandas
        df = pandas.read_excel(io.BytesIO(data), engine="odf", header=None)
        out = []
        for _, r in df.iterrows():
            nro = str(r[0]).strip() if pandas.notna(r[0]) else ""
            if not nro.startswith("20") or "/MEN/" not in nro:
                continue
            objeto = str(r[2]).strip() if pandas.notna(r[2]) else ""
            importe_s = str(r[5]).strip() if pandas.notna(r[5]) else ""
            cif = str(r[6]).strip() if pandas.notna(r[6]) else ""
            ad = str(r[8]).strip() if pandas.notna(r[8]) else ""
            dur = str(r[10]).strip() if pandas.notna(r[10]) else ""
            importe = None
            if "€" in importe_s:
                try:
                    importe = float(importe_s.replace("€", "").replace(".", "").replace(",", ".").strip())
                except ValueError:
                    importe = None
            out.append({"expediente": nro, "objeto": objeto, "importe": importe,
                        "cif": cif, "adjudicatario": ad, "duracion": dur})
        return out
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    out = []
    for r in rows:
        nro = str(r[0]).strip() if r[0] else ""
        if not nro.startswith("20") or "/MEN/" not in nro:
            continue
        objeto = str(r[2]).strip() if r[2] else ""
        importe_s = str(r[5]).strip() if r[5] else ""
        cif = str(r[6]).strip() if r[6] else ""
        ad = str(r[8]).strip() if r[8] else ""
        dur = str(r[10]).strip() if r[10] else ""
        importe = None
        if "€" in importe_s:
            try:
                importe = float(importe_s.replace("€", "").replace(".", "").replace(",", ".").strip())
            except ValueError:
                importe = None
        out.append({"expediente": nro, "objeto": objeto, "importe": importe,
                    "cif": cif, "adjudicatario": ad, "duracion": dur})
    return out

os.makedirs("malaga_pdf", exist_ok=True)
todos = []
for ds in DATASETS:
    # sacar URL del fichero desde la pagina del dataset
    try:
        page = fetch("https://datos.gob.es/es/catalogo/" + ds).decode("utf-8", "ignore")
        links = re.findall(r'href="(https?://datosabiertos\.malaga\.eu[^\"]*\.(?:xlsx|ods|zip)[^\"]*)"', page, re.I)
        if not links:
            print(f"  {ds[:30]}: SIN fichero")
            continue
        url = links[0]
        fname = os.path.join("malaga_pdf", ds.split("-")[2] + "_" + re.search(r"(\dTR|MENORES)[^/]*\.(xlsx|ods)", url).group(0) if re.search(r"(\dTR|MENORES)[^/]*\.(xlsx|ods)", url) else "x")
        # nombre simple: trimestre_anio
        m = re.search(r"(\d)(?:o|er)?-?trimestre-(\d{4})", ds)
        nombre = f"{m.group(2)}_Q{m.group(1)}" if m else ds[:20]
        data = fetch(url)
        regs = parse_xlsx(data, url)
        for r in regs:
            r["periodo"] = nombre
            todos.append(r)
        print(f"  OK {nombre}: {len(regs)} contratos ({url.split('/')[-1]})")
    except Exception as e:
        print(f"  ERR {ds[:30]}: {e}")

print("\nTOTAL Malaga menores:", len(todos))
with open("malaga_menores.json", "w", encoding="utf-8") as f:
    json.dump(todos, f, ensure_ascii=False, indent=1)
print("guardado: malaga_menores.json")
