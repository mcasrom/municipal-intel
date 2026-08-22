# Municipal Intelligence

Mapa de la población oficial de los **8.132 municipios de España** (INE 1996-2025)
con **fichas de transparencia municipal** (Lorca y Málaga) y detección de posibles
troceados de contratos. Datos oficiales, trazables, sin inventar.

**En vivo**: https://municipal.viajeinteligencia.com

## Qué ofrece
- **Mapa interactivo** (Leaflet, PWA instalable y offline) de los 8.132 municipios:
  buscador sin acentos, rankings (crecen/caen/mayores), comparador, deep-link
  (`?m=codigo`) y botón de compartir.
- **8.109 fichas estáticas por municipio** (`/municipio/{slug}.html`): población
  2025, evolución 1996-2025 (SVG), ranking, variaciones 1/5/10 años, JSON-LD.
- **103 páginas editoriales** (`/editorial/…`): "Municipios que más crecen /
  se despueblan" (nacional + por provincia), "más poblados" — SEO long-tail.
- **Fichas de transparencia municipal**:
  - **Lorca** (`/ficha_lorca.html`): 26.704 contratos menores (2019-2026) y 52
    formales, troceado, renta (INE Atlas), estructura de edad (Censo 2021).
  - **Málaga** (`/ficha_malaga.html`): 1.976 contratos menores (2024-2026) vía
    datos.gob.es, troceado, renta y edad.
- **RSS** (`/rss.xml`) con rankings · **Alertas por email** ("avísame si cambia"
    en cada municipio) · **Metodología** (`/acerca.html`).

## Datos y fuentes
- **INE** — Cifras oficiales de población de los municipios españoles (Revisión
  del Padrón Municipal), serie 1996-2025. API: `servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{id_tabla}`.
- **INE Atlas de renta** — renta media por municipio (tabla por provincia).
- **INE Censo 2021** — estructura de edad por municipio (API SDC21).
- **OpenStreetMap / Overpass** — coordenadas (`admin_centre`) y códigos INE (`ref:ine`).
- **transparencia.lorca.es** — contratos de Lorca (PDF trimestrales) y formales.
- **datos.gob.es / datosabiertos.malaga.eu** — contratos menores del Ayuntamiento de Málaga.

## Arquitectura
- **Datos**: `data/poblacion_municipal.sqlite` (tablas `poblacion` y `catalogo`).
- **Generadores** (estáticos, sin backend, en `update.sh` con cron diario 05:30 UTC):
  - `gen_map.py` → mapa + rankings + comparador + PWA.
  - `gen_municipio_pages.py` → 8.109 fichas por municipio + sitemap.
  - `gen_editorial_pages.py` → 103 páginas editoriales long-tail.
  - `gen_ficha_municipio.py` → **generador generalizado** de fichas de transparencia
    (config-driven: cualquier ayuntamiento + su dataset) — genera Lorca y Málaga.
  - `gen_rss.py` · `gen_acerca.py`.
  - Ingesta: `ine_pobmunicipal_ingest.py`, `lorca_menores_ingest.py`,
    `lorca_ingest.py`, `malaga_ingest.py`, `ine_catalog_build.py`.
  - `municipal_alert_api.py` → API de alertas por email (stdlib + Resend, puerto 8201).
- **Servir**: estático + nginx + certbot (patrón de transparencia_osint).

## Reglas del proyecto
- Datos fiables y trazables primero. Sin inventar. Fecha y fuente de cada dato
  visibles. Pendientes señalados explícitamente.

## Roadmap (ver WAYAHEAD.md para el detalle)
- [x] P0.5 dataset INE población municipal 1996-2025 (8.132 municipios)
- [x] P1 catálogo con códigos INE + coordenadas (admin_centre)
- [x] P2 mapa + buscador + rankings + comparador + deep-link + compartir
- [x] P3 transparencia municipal: Lorca + Málaga (generador generalizado)
- [x] SEO: JSON-LD, 8.109 fichas estáticas, 103 editoriales, sitemap 8.113 URLs, llms.txt
- [x] PWA (manifest + service worker, instalable y offline)
- [x] RSS + alertas por email
- [ ] Añadir más ayuntamientos al generador (Madrid/Barcelona/Valencia)
- [ ] Edad/sexo del Padrón (el Censo 2021 cubre la estructura de edad)
- [ ] Precio vivienda compra municipal → proyecto alquimetria (crawl Registradores)
- [ ] GSC: enviar sitemap (8.113 URLs) — propiedad registrada

© 2026 M. Castillo — datos abiertos INE + OpenStreetMap. Repositorio del ecosistema: https://www.viajeinteligencia.com
