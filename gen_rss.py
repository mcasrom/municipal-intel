import json, os, datetime, html

# Genera dashboard/rss.xml con los rankings (crec/dec/may) y las paginas principales.
# Items enlazan a las fichas estaticas por municipio. Reusable en el cron de update.

OUT = os.path.join("dashboard", "rss.xml")
rank = json.load(open(os.path.join("dashboard", "data", "rankings.json")))
slugmap = json.load(open(os.path.join("dashboard", "data", "municipio_slugs.json")))
base = "https://municipal.viajeinteligencia.com"
fecha = datetime.date.today().isoformat()

def muni_url(c):
    sl = slugmap.get(c, "")
    return base + "/municipio/" + (sl + ".html" if sl else "")

def it(titulo, url, desc):
    d = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    return ("<item><title>%s</title><link>%s</link><guid isPermaLink=\"true\">%s</guid>"
            "<pubDate>%s</pubDate><description>%s</description></item>"
            % (html.escape(titulo), url, url, d, html.escape(desc)))

items = []
items.append(it("Población de los 8.132 municipios de España (INE 2025) · Mapa",
                base + "/", "Mapa interactivo: evolución 1996-2025, rankings y comparador."))
items.append(it("Transparencia del Ayuntamiento de Lorca: contratos y troceado",
                base + "/ficha_lorca.html", "Contratos menores 2019-2026, formales, renta y estructura de edad."))

# municipios que mas crecen (2016-2025)
for x in rank.get("crec", [])[:15]:
    url = muni_url(x["c"])
    items.append(it("%s (%s): +%.1f%% de población 2016-2025" % (x["n"], x["p"], x["g"]),
                    url, "Creció +%.1f%% en 10 años (2016-2025). Población 2025: %s hab. Datos INE." % (x["g"], format(x["po"], ","))))
# municipios que mas caen
for x in rank.get("dec", [])[:15]:
    url = muni_url(x["c"])
    items.append(it("%s (%s): %.1f%% de pérdida de población 2016-2025" % (x["n"], x["p"], abs(x["g"])),
                    url, "Perdió el %.1f%% de su población en 10 años (2016-2025). Datos INE." % abs(x["g"])))
# mayores municipios
for x in rank.get("may", [])[:10]:
    url = muni_url(x["c"])
    items.append(it("%s (%s): %s habitantes (2025)" % (x["n"], x["p"], format(x["po"], ",")),
                    url, "Uno de los municipios más poblados de España. Datos INE 2025."))

rss = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>Municipal Intelligence · Población de los municipios de España</title>
<link>%s</link>
<description>Población oficial de los 8.132 municipios de España (INE 1996-2025): rankings de crecimiento y descenso, mayores municipios y ficha de transparencia de Lorca.</description>
<language>es</language>
<lastBuildDate>%s</lastBuildDate>
<atom:link href="%s/rss.xml" rel="self" type="application/rss+xml"/>
%s
</channel>
</rss>""" % (base, fecha, base, "\n".join(items))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(rss)
print("rss.xml generado:", len(items), "items |", os.path.getsize(OUT), "bytes")
