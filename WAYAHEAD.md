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
- **Siguiente dato municipal a cazar**: códigos INE de municipio (join de la
  relación de municipios y sus códigos del INE) y coordenadas (Overpass).
- PLACSP: WebSphere/dojo (crawl duro, P0 en transparencia_osint).

## Datos que YA tenemos (reutilizar)
- Contratos Región de Murcia 2023 (transparencia_osint) — contexto regional.
- Población municipal INE 1996-2025 (este repo) — núcleo demográfico.

## Roadmap
- [x] P0.5: dataset INE población municipal 1996-2025 (8.132 municipios).
- [ ] P1: catálogo municipios (códigos INE + coords) — Overpass o codmun INE.
- [ ] P2: página / con buscador + mapa Leaflet.
- [ ] P3: ficha municipio: población (serie + variación), luego contratos del
      ayuntamiento (PLACSP export manual o crawl) y finanzas (Facturas CARM).
- [ ] P4: indicadores + cambios + comparador.
- Patrón: Postgres + API ligera + estático (como transparencia_osint).

## Regla
- Datos fiables y trazables primero. No inventar. Señalar claramente lo pendiente.
