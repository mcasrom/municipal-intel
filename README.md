# Municipal Intelligence

Mapa de la población oficial de los **8.132 municipios de España** (INE 1996-2025)
con la **ficha de transparencia del Ayuntamiento de Lorca** (contratos menores,
formales y anomalías) como prueba de concepto local.

**En vivo**: https://municipal.viajeinteligencia.com

## Qué ofrece
- **Mapa interactivo** (Leaflet) de los 8.132 municipios: población, evolución,
  rankings (crecen/caen/mayores), comparador de dos municipios y buscador.
- **Fichas estáticas por municipio** (`/municipio/{slug}.html`): las 300 mayores
  (capitales de provincia + top población) con ficha HTML indexable, SVG de
  evolución y serie completa.
- **Ficha de transparencia de Lorca** (`/ficha_lorca.html`): 26.704 contratos
  menores (2019-2026) y 52 formales del Ayuntamiento, con alerta de troceado
  (296 contratos a un mismo proveedor) y renta de los hogares (INE Atlas).
- **Metodología y fuentes** (`/acerca.html`): fecha de los datos, fuentes,
  limpieza y licencias.

## Datos y fuentes
- **INE** — Cifras oficiales de población de los municipios españoles (Revisión
  del Padrón Municipal), serie 1996-2025. API: `servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{id_tabla}`.
- **INE Atlas de renta** — renta media por municipio (tabla por provincia).
- **OpenStreetMap / Overpass** — coordenadas (nodo `admin_centre`) y códigos
  INE (`ref:ine`).
- **transparencia.lorca.es** — contratos menores (PDF trimestrales) y formales.

## Arquitectura
- **Datos**: `data/poblacion_municipal.sqlite` (tablas `poblacion` y `catalogo`).
- **Generadores** (estáticos, sin backend):
  - `gen_map.py` → mapa + rankings + comparador.
  - `gen_municipio_pages.py` → 300 fichas por municipio + sitemap.
  - `gen_lorca_ficha.py` → ficha de transparencia de Lorca + resumen para el mapa.
  - `gen_acerca.py` → metodología y fuentes.
  - Ingesta: `ine_pobmunicipal_ingest.py`, `lorca_menores_ingest.py`,
    `lorca_ingest.py`, `ine_catalog_build.py`.
- **Servir**: estático + nginx + certbot (patrón de transparencia_osint).

## Reglas del proyecto
- Datos fiables y trazables primero. Sin inventar. Fecha y fuente de cada dato
  visibles. Pendientes señalados explícitamente.

## Roadmap (ver WAYAHEAD.md para el detalle)
- [x] P0.5 dataset INE población municipal 1996-2025 (8.132 municipios)
- [x] P1 catálogo con códigos INE + coordenadas (admin_centre)
- [x] P2 mapa + buscador + rankings + comparador
- [x] P3(parcial) ficha de transparencia de Lorca (contratos + troceado + renta)
- [x] SEO: JSON-LD (Dataset/GovernmentService), 300 fichas estáticas, sitemap
- [ ] Extender la ficha de transparencia a otros ayuntamientos (parser listo)
- [ ] Edad/sexo por municipio (INE) — pendiente de localizar tabla
- [ ] Precio vivienda compra municipal → proyecto alquimetria (crawl Registradores)

© 2026 M. Castillo — datos abiertos INE + OpenStreetMap. Repositorio del ecosistema: https://www.viajeinteligencia.com
