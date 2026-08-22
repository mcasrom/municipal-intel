import json, sqlite3, os, re, unicodedata
from PIL import Image, ImageDraw, ImageFont

DBP = "data/poblacion_municipal.sqlite"
if not os.path.exists(DBP): DBP = "poblacion_municipal.sqlite"
OUT = os.path.join("dashboard", "ogm")
os.makedirs(OUT, exist_ok=True)
con = sqlite3.connect(DBP)

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# trazado de espana
raw = open("spain_path.txt").read()
def parse_path(d):
    pols = []; cur = []
    for m in re.finditer(r"([MLZ])\s*(-?\d+\.?\d*)\s*,?\s*(-?\d+\.?\d*)", d):
        c, x, y = m.group(1), float(m.group(2)), float(m.group(3))
        if c == "M":
            if cur: pols.append(cur)
            cur = [(x, y)]
        elif c == "L": cur.append((x, y))
        elif c == "Z":
            if cur: pols.append(cur)
            cur = []
    if cur: pols.append(cur)
    return [p for p in pols if len(p) > 2 and all(0 <= x <= 520 and 0 <= y <= 560 for x, y in p)]
main = parse_path(raw)

def draw_spain(d, scale, ox, oy, fill):
    for p in main:
        d.polygon([(ox + x*scale, oy + y*scale) for x, y in p], fill=fill)

def gradient(w, h, top, bot):
    img = Image.new("RGB", (w, h)); dd = ImageDraw.Draw(img)
    for y in range(h):
        t = y/h
        dd.line([(0, y), (w, y)], fill=tuple(int(top[i]+(bot[i]-top[i])*t) for i in range(3)))
    return img

def pct(a, b): return round((a-b)/b*100, 1) if b else None

# seleccionar municipios para OG dinamico
rows = con.execute("""SELECT c.municipio, c.provincia, c.codigo_ine, c.lat, c.lon, p25.poblacion, p96.poblacion
    FROM catalogo c
    JOIN poblacion p25 ON p25.provincia=c.provincia AND p25.municipio=c.municipio AND p25.anyo=2025 AND p25.sexo='Total'
    JOIN poblacion p96 ON p96.provincia=c.provincia AND p96.municipio=c.municipio AND p96.anyo=1996 AND p96.sexo='Total'
    WHERE p25.poblacion >= 500""").fetchall()
con.close()
data = [{"n": n, "p": prov, "c": code, "la": lat, "lo": lon, "p25": p25, "p96": p96, "g": pct(p25, p96), "diff": p25 - p96}
        for n, prov, code, lat, lon, p25, p96 in rows if pct(p25, p96) is not None]

# top crec + top dec + top may (deduplicado)
seleccion = {}
for x in sorted(data, key=lambda x: -x["diff"])[:80]: seleccion[x["c"]] = x
for x in sorted(data, key=lambda x: x["diff"])[:80]: seleccion[x["c"]] = x
for x in sorted(data, key=lambda x: -x["g"])[:40]: seleccion[x["c"]] = x
for x in sorted(data, key=lambda x: x["g"])[:40]: seleccion[x["c"]] = x
for x in sorted(data, key=lambda x: -x["p25"])[:20]: seleccion[x["c"]] = x
print("municipios con OG dinamico:", len(seleccion))

W, H = 1200, 630
mapping = {}
for code, x in seleccion.items():
    g = x["g"]
    if g <= -10:
        titular = "TU PUEBLO HA PERDIDO EL %s%% DE SU POBLACIÓN" % abs(round(g))
        sub = "desde 1996"
        color_titulo = (248, 113, 113)
    elif g >= 50:
        titular = "TU PUEBLO CASI DUPLICA SU POBLACIÓN"
        sub = "(+%s%% desde 1996)" % round(g)
        color_titulo = (74, 222, 128)
    else:
        titular = "TU PUEBLO: %+s%% EN 30 AÑOS" % round(g)
        sub = "evolución 1996-2025"
        color_titulo = (56, 189, 248)
    img = gradient(W, H, (11, 18, 32), (30, 41, 59))
    d = ImageDraw.Draw(img)
    scale = 0.62; ox = W - 520*scale - 70; oy = (H - 560*scale)/2
    draw_spain(d, scale, ox, oy, (56, 189, 248))
    px, py = ox + x["lo"]*0 + 300*scale, oy + 385*scale
    # el pin no es exacto (viewBox espana); usar lat/lon aproximado del viewBox
    px = ox + (300 + (x["lo"]+3.5)*8)*scale
    py = oy + (385 - (x["la"]-40)*9)*scale
    d.ellipse([px-10, py-10, px+10, py+10], fill=(239, 68, 68), outline=(255, 255, 255), width=3)
    f1 = ImageFont.truetype(FONT_B, 46); f2 = ImageFont.truetype(FONT_R, 32); f3 = ImageFont.truetype(FONT_R, 26)
    d.text((60, 70), titular, font=f1, fill=color_titulo)
    d.text((60, 140), sub, font=f2, fill=(148, 163, 184))
    d.text((60, 240), "%s (%s)" % (x["n"], x["p"]), font=f2, fill=(226, 232, 240))
    d.text((60, 290), "%s habitantes (2025) · %s en 1996" % (format(x["p25"], ","), format(x["p96"], ",")), font=f3, fill=(148, 163, 184))
    d.text((60, 540), "municipal.viajeinteligencia.com · INE 01/01/2025", font=ImageFont.truetype(FONT_R, 22), fill=(100, 116, 139))
    f = os.path.join(OUT, code + ".png")
    img.save(f)
    mapping[code] = "ogm/" + code + ".png"

with open(os.path.join("dashboard", "data", "og_dinamico.json"), "w") as f:
    json.dump(mapping, f)
print("og dinamico generado:", len(mapping), "imagenes")
