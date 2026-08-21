import json, unicodedata, sqlite3

# Catalogo de municipios: cruce poblacion INE (sqlite) x OSM (ref:ine + centro)
# Uso: python3 ine_catalog_build.py overpass_municipios.json poblacion_municipal.sqlite

PROV_CODE = {1:'Álava',2:'Albacete',3:'Alicante',4:'Almería',5:'Ávila',6:'Badajoz',7:'Baleares',
 8:'Barcelona',9:'Burgos',10:'Cáceres',11:'Cádiz',12:'Castellón',13:'Ciudad Real',14:'Córdoba',
 15:'A Coruña',16:'Cuenca',17:'Girona',18:'Granada',19:'Guadalajara',20:'Gipuzkoa',21:'Huelva',
 22:'Huesca',23:'Jaén',24:'León',25:'Lleida',26:'La Rioja',27:'Lugo',28:'Madrid',29:'Málaga',
 30:'Murcia',31:'Navarra',32:'Ourense',33:'Asturias',34:'Palencia',35:'Las Palmas',36:'Pontevedra',
 37:'Salamanca',38:'Santa Cruz de Tenerife',39:'Cantabria',40:'Segovia',41:'Sevilla',42:'Soria',
 43:'Tarragona',44:'Teruel',45:'Toledo',46:'Valencia',47:'Valladolid',48:'Bizkaia',49:'Zamora',
 50:'Zaragoza',51:'Ceuta',52:'Melilla'}
ART_LEAD = ('la ','el ','los ','las ','l\'','els ','les ','es ','o ','os ','as ','a ','sa ','ses ')
ART_TAIL = (' els',' les',' es',' sa',' ses',' la',' el',' los',' las',' a',' o',' as',' os'," l'")

def clean(s):
    return ' '.join(unicodedata.normalize('NFD', s).encode('ascii','ignore').decode().lower().replace('-',' ').split())

def variants(name):
    base = clean(name); vs = set()
    def push(x):
        x = ' '.join(x.split())
        if x: vs.add(x)
    push(base)
    for art in ART_LEAD:
        if base.startswith(art): push(base[len(art):])
    for art in ART_TAIL:
        if base.endswith(',' + art): push(base[:-(len(art)+1)])
    if base.endswith(' de'): push(base[:-3])
    for part in base.split('/'):
        p = ' '.join(part.split()); push(p)
        for art in ART_LEAD:
            if p.startswith(art): push(p[len(art):])
    return vs

def main(overpass_json, db):
    d = json.load(open(overpass_json))
    osm = {}
    for e in d['elements']:
        t = e.get('tags', {})
        rine = t.get('ref:ine','')
        if not rine: continue
        prov = PROV_CODE.get(int(rine[:2]))
        if not prov: continue
        for k in ('name:es','name','name:ca','name:eu','name:gl','name:ga','alt_name','official_name'):
            v = t.get(k)
            if not v: continue
            for nn in v.split(';'):
                nn = nn.strip()
                if nn:
                    for vv in variants(nn):
                        osm.setdefault((prov, vv), []).append({'code': rine[:5],
                            'lat': e.get('center',{}).get('lat'), 'lon': e.get('center',{}).get('lon'), 'name': nn})
    con = sqlite3.connect(db)
    rows = con.execute("SELECT DISTINCT provincia, municipio FROM poblacion").fetchall()
    matches = {}; no = []
    for prov, muni in rows:
        hit = None
        for v in variants(muni):
            if (prov, v) in osm: hit = osm[(prov, v)][0]; break
        if hit: matches[(prov, muni)] = hit
        else: no.append((prov, muni))
    con.execute("DROP TABLE IF EXISTS catalogo")
    con.execute("""CREATE TABLE catalogo (provincia TEXT, municipio TEXT, codigo_ine TEXT,
      lat REAL, lon REAL, osm_name TEXT, PRIMARY KEY (provincia, municipio))""")
    for (prov, muni), info in matches.items():
        con.execute("INSERT INTO catalogo VALUES (?,?,?,?,?,?)",
                    (prov, muni, info['code'], info['lat'], info['lon'], info['name']))
    con.commit()
    print(f"catalogo: {len(matches)}/{len(rows)} ({len(matches)/len(rows)*100:.2f}%)")
    print("sin match:", len(no))
    for u in no: print("   ", u)
    con.close()

if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2])
