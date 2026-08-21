# Municipal Intelligence — WAYAHEAD

## Objetivo
Ficha de inteligencia municipal (Lorca primero): "qué está pasando en este
municipio y qué dicen los datos públicos sobre él". Fuentes trazables,
sin inventar causalidad.

## ESTADO (21/Ago) — INE ROTO YA NO
- **INE población municipal: FUNCIONA** (API servicios.ine.es).
  - Operación: "Cifras oficiales de población de los municipios españoles:
    Revisión del Padrón Municipal" (padre=525, detalle municipal por provincia).
  - Endpoint: `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{id_tabla}`
    con id por provincia (Murcia=2883, Madrid=2881, ... 52 tablas).
  - Dataset ingerido: **8.132 municipios (oficiales) + 4 disueltos**, serie
    1996-2025 (29 años, 1997 no publicado), 706.128 filas, total/sexo.
  - VALIDADO: Lorca 2025=98.969 (69.045 en 1996), Murcia capital 479.405,
    total España 01/01/2025=49.114.494, municipios por provincia == oficial INE.
  - Detección de agregados (filas provinciales que duplican el total):
    valor 2025 == suma del resto => excluir (12 filas). Disueltos
    (Cesuras/Oza dos Ríos -> Oza-Cesuras, Cerdedo/Cotobade -> Cerdedo-Cotobade)
    aportan 0 desde la fusión: se conservan para la serie histórica.
  - Datos: data/poblacion_municipal.sqlite (tabla poblacion:
    provincia, municipio, sexo, anyo, poblacion).
- PLACSP: WebSphere/dojo (crawl duro, P0 en transparencia_osint).

## Datos que YA tenemos (reutilizar)
- Contratos Región de Murcia 2023 (transparencia_osint) — contexto regional.
- Población municipal INE 1996-2025 (este repo) — núcleo demográfico.

## ESTADO CATÁLOGO (21/Ago) — P1 HECHO
- Catálogo de municipios: 8.109 municipios con código INE + coordenadas (Overpass
  ref:ine + centro). Validado spot-check 17/17 contra códigos oficiales (Lorca 30024,
  Madrid 28079, València 46250...). Cobertura 99,7% de la población 2025.
  - Consulta Overpass: relation boundary=administrative admin_level=8 area España,
    out tags center -> ref:ine (código INE), centroide.
  - Cruce con población por (provincia, nombre normalizado: artículos gallegos/catalanes
    "O/As/Les", bilingües "/", apóstrofos). Match EXACTO solamente (sin fuzzy).
  - Tabla catalogo (provincia, municipio, codigo_ine, lat, lon, osm_name).
  - PENDIENTE-catalogo.md: 27 sin match (4 disueltos sin OSM + 23 con nombre OSM
    distinto: Torredelcampo/Torre del Campo, Noáin (Valle de Elorz)/Noain...).
    Resolver con codmun INE para 100%.
- Reproducible: ingest/overpass_municipios.json (OSM crudo) + ingest/ine_catalog_build.py.

## ESTADO MAPA (21/Ago) — P2 HECHO Y DESPLEGADO
- **https://municipal.viajeinteligencia.com** EN VIVO (estático, nginx + certbot
  Let's Encrypt, DNS Cloudflare gris -> pasar a naranja).
  - Mapa Leaflet de España: 8.109 municipios, 5 clases de población (leyenda),
    renderer canvas. Buscador con autocompletado (nombre o código INE).
  - Clic -> panel con KPIs (2025, 1996, Δ%) + sparkline 1996-2025 + texto de
    crecimiento. Nota de fuentes (INE + OSM/Overpass). Sin cookies.
  - Datos cacheados (max-age 3600) + gzip (series.json 2,7MB -> 752KB).
  - Generador reproducible: gen_map.py (lee sqlite -> dashboard/).
  - Deploy: /home/deploy/municipal-intel/dashboard + vhost nginx
    municipal.viajeinteligencia.com + certbot. Commit fbd6145.

## ESTADO SEO ESTRUCTURAL (21/Ago) — PÁGINAS + JSON-LD
- JSON-LD: Dataset en index + Dataset/GovernmentService en ficha_lorca.
- **300 páginas estáticas por municipio** (`/municipio/{slug}.html`): capitales de
  provincia + top población 2025. Cada ficha: H1, KPIs (2025/1996/Δ%), rank
  nacional, variaciones 1/5/10 años, SVG de evolución, serie completa en <details>
  (texto indexable), JSON-LD Dataset, canonical/OG. Enlace cruzado: mapa →
  ficha (top 300) y Lorca → ficha de transparencia.
- **Sitemap 303 URLs** (mapa + ficha Lorca + acerca + 300 municipios).
- Corrección del análisis externo: "sitemap será 1 URL" = FALSO (son 303 tras
  este trabajo; antes 3). El resto del análisis (SPA pobre en texto, sin JSON-LD,
  sin URLs por municipio, Lorca mal enmarcado) = CIERTO y corregido aquí.
- Pendiente del análisis: separar landing mapa vs transparencia Lorca; OG dinámico
  por municipio ("tu pueblo perdió el 30%"); cruce con Alquimetría (población +
  alquiler); extender más allá de los 300 municipios.

## ACTUALIZACIÓN PROGRAMADA (21/Ago) — CRON DIARIO 05:30 UTC
- update.sh: detecta trimestres nuevos de contratos de Lorca (lorca_check_new.py,
  compara PDFs publicados vs ingeridos; re-ingesta si hay nuevos) + detecta año
  nuevo del INE (ine_check_new.py, Revisión del Padrón ~diciembre; avisa si hay
  re-ingesta manual) + regenera el sitio (map, ficha, 300 páginas, sitemap, acerca).
- Cron: `30 5 * * * /home/deploy/municipal-intel/update.sh`. Log: logs/update.log.
- Health: municipal ya en ecosystem-healthcheck.sh (cada 5 min, alerta Telegram).
- MEDICIÓN: los scripts KPI son host-agnósticos → municipal y alquimetría ya se
  miden (municipal 67 IPs humanas, alquimetría 26 IPs el 21/Ago). Nota: ambos en
  naranja → el total de requests sale infraestimado (Cloudflare cachea assets),
  pero las IPs humanas se capturan bien.

## EMBUDO / LORCA (21/Ago) — SEPARACIÓN DE PÚBLICOS
- Aplicado el comentario del análisis: la meta-description y el H1 del mapa ya NO
  mezclan "8.132 municipios" con "transparencia de Lorca" — el mapa es solo
  población nacional; la ficha_lorca.html es la landing SEO de Lorca (title/meta
  propios). El overlay de bienvenida separa ambos: mapa nacional + "Caso de
  estudio · Transparencia del Ayuntamiento de Lorca" como bloque distinto con su
  CTA.

## POLÍTICA DE RETENCIÓN DE DATOS (21/Ago)
- Logs de acceso (el único dato infinito): logrotate diario, 14 días, comprimido.
- Datos de la app (~100MB, +~15MB/año): SIN rotación — los contratos de Lorca y la
  población son el producto (inteligencia histórica) y la trazabilidad es regla.
  Disco 17G libre = años de margen.
- Limpieza opcional futura: archivar lorca_pdf viejos (comprimidos) y VACUUM del
  sqlite. No necesario hoy.

## Roadmap
- [x] P0.5: dataset INE población municipal 1996-2025 (8.132 municipios).
- [x] P1: catálogo municipios (códigos INE + coords) — 8.109 municipios (99,7%).
- [x] P2: mapa Leaflet + buscador + sparkline — DESPLEGADO.
- [x] P3 (parcial): ficha de transparencia de Lorca (contratos + troceado + renta).
- [x] SEO: JSON-LD + 300 fichas estáticas + sitemap 303 URLs.
- [ ] P3: ficha municipio: contratos del ayuntamiento (PLACSP export manual o
      crawl) y finanzas (Facturas CARM). Población ya en la ficha del mapa.
- [ ] P4: indicadores + cambios + comparador (rankings, variaciones interanuales).
- Patrón: estático generado + nginx (como transparencia_osint y alquimetria).
