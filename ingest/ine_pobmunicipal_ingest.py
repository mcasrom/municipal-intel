import json, sqlite3, sys, time, urllib.request

PROVINCIAS = {
    2855: "Albacete", 2856: "Alicante", 2857: "Almería", 2854: "Álava", 2886: "Asturias",
    2858: "Ávila", 2859: "Badajoz", 2860: "Baleares", 2861: "Barcelona", 2905: "Bizkaia",
    2862: "Burgos", 2863: "Cáceres", 2864: "Cádiz", 2893: "Cantabria", 2865: "Castellón",
    2866: "Ciudad Real", 2901: "Córdoba", 2868: "A Coruña", 2869: "Cuenca", 2873: "Gipuzkoa",
    2870: "Girona", 2871: "Granada", 2872: "Guadalajara", 2874: "Huelva", 2875: "Huesca",
    2876: "Jaén", 2877: "León", 2878: "Lleida", 2880: "Lugo", 2881: "Madrid", 2882: "Málaga",
    2883: "Murcia", 2884: "Navarra", 2885: "Ourense", 2888: "Palencia", 2889: "Las Palmas",
    2890: "Pontevedra", 2879: "La Rioja", 2891: "Salamanca", 2892: "Santa Cruz de Tenerife",
    2894: "Segovia", 2895: "Sevilla", 2896: "Soria", 2900: "Tarragona", 2899: "Teruel",
    2902: "Toledo", 2903: "Valencia", 2904: "Valladolid", 2906: "Zamora", 2907: "Zaragoza",
    2908: "Ceuta", 2909: "Melilla",
}

BASE = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/"

def fetch(tid):
    url = BASE + str(tid)
    req = urllib.request.Request(url, headers={"User-Agent": "municipal-intel/0.1 (contact: osint)"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)

def main():
    out = {"fuente": "INE - Cifras oficiales de población de los municipios españoles (Revisión del Padrón)",
           "nota": "Serie 1996-2025. 1997 no publicado. Población a 1 de enero (1996 a 1 de mayo).",
           "fecha_descarga": time.strftime("%Y-%m-%d %H:%M:%S"),
           "provincias": {}}
    nrows = 0
    for tid, prov in PROVINCIAS.items():
        try:
            d = fetch(tid)
        except Exception as e:
            print(f"  ERROR {tid} {prov}: {e}", flush=True)
            continue
        prov_out = {"provincia": prov, "municipios": {}}
        for row in d:
            name = (row.get("Nombre") or "").strip()
            if not name:
                continue
            parts = [p.strip() for p in name.split(".")]
            muni = parts[0] if parts else ""
            sexo = parts[1] if len(parts) > 1 else "Total"
            if muni not in prov_out["municipios"]:
                prov_out["municipios"][muni] = {"Total": {}, "Hombres": {}, "Mujeres": {}}
            serie = prov_out["municipios"][muni].get(sexo)
            if serie is None:
                continue
            for dpt in row.get("Data", []):
                serie[str(dpt["Anyo"])] = dpt["Valor"]
                nrows += 1
        out["provincias"][str(tid)] = prov_out
        print(f"  OK {tid} {prov} ({len(prov_out['municipios'])} municipios)", flush=True)
        time.sleep(0.6)

    with open("data_poblacion_municipal.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"\nJSON guardado: data_poblacion_municipal.json | {nrows} valores")

if __name__ == "__main__":
    main()
