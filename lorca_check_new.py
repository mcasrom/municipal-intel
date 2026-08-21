import json, os, re, urllib.request

# Detecta trimestres nuevos de contratos menores del Ayuntamiento de Lorca.
# Si hay PDFs nuevos (respecto a los ya ingeridos en lorca_menores.json), re-ingesta.
# exit 0 = sin cambios, exit 1 = hubo cambios (para update.sh)

BASE = "https://transparencia.lorca.es"
INGEST = os.path.join(os.path.dirname(__file__), "lorca_menores_ingest.py")

def main():
    req = urllib.request.Request(BASE + "/contratos-menores/", headers={"User-Agent": "municipal-intel/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("latin-1")
    pdfs = sorted(set(re.findall(r'href="([^"]*(?:Contratos|contratos|trimestre|Publicacion)[^"]*\.pdf)"', html)))
    # ya ingeridos: periodos en lorca_menores.json
    ingeridos = set()
    # ficheros ya descargados (incluso si parsean 0)
    if os.path.isdir("lorca_pdf"):
        for f in os.listdir("lorca_pdf"):
            if f.endswith(".pdf"):
                ingeridos.add(f)
    if os.path.exists("lorca_menores.json"):
        try:
            d = json.load(open("lorca_menores.json"))
            for x in d:
                per = x.get("periodo", "")
                if "/" in per:
                    ingeridos.add(per.split("/", 1)[1])  # nombre de fichero (anyo/nombre.pdf)
        except Exception:
            pass
    # normalizar nombres de fichero a lo que produce el ingest
    nuevos = []
    for p in pdfs:
        year = re.search(r"20\d{2}", p).group(0)
        name = year + "_" + p.split("/")[-1].replace(" ", "_")
        if name not in ingeridos:
            nuevos.append(p)
    print("PDFs publicados:", len(pdfs), "| ingeridos:", len(ingeridos), "| nuevos:", len(nuevos))
    if not nuevos:
        return 0
    print("NUEVOS trimestres:", nuevos)
    import subprocess, sys
    subprocess.run([sys.executable, INGEST], check=True)
    print("re-ingesta de menores completada")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
