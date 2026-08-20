# Municipal Intelligence — WAYAHEAD

## Objetivo
Ficha de inteligencia municipal (Lorca primero): "qué está pasando en este
municipio y qué dicen los datos públicos sobre él". Fuentes trazables,
sin inventar causalidad.

## Estado (20/Ago) — datos
- Esqueleto creado (data/ingest/app + git).
- REALIDAD DE FUENTES (probado hoy):
  - INE: API/portal NO funciona (decisión del usuario: no usar INE).
  - PLACSP: WebSphere/dojo (crawl duro, P0 pendiente).
  - CARM datosabiertos: funciona para CONTRATOS (21.313 menores 2023, ya
    ingeridos en transparencia_osint) y Facturas (web app, no CSV limpio).
    Los contratos CARM son REGIONALES (consejerías), no por ayuntamiento.
  - Overpass/OSM para catálogo municipal: endpoints caídos hoy (kumi 502,
    osm.ch vacío, overpass-api 000).
- Conclusión: los datos MUNICIPALES (ayuntamiento de Lorca, población) son el
  núcleo duro. No hay fuente fácil hoy.

## Datos que YA tenemos (reutilizar)
- Contratos de la Región de Murcia 2023 (transparencia_osint) — contexto regional.
- Ficha/panel de transparencia_osint (patrón de dashboard ligero reutilizable).

## Roadmap
- [ ] P1: catálogo de municipios (códigos INE + coords) — resolver fuente de
      límites (Overpass cuando funcione, o datos.gob.es).
- [ ] P2: página / con buscador + mapa Leaflet.
- [ ] P3: fich municipio: contratos del ayuntamiento (PLACSP export manual o
      crawl), finanzas (Facturas), luego población (mirror INE cuando haya).
- [ ] P4: indicadores + cambios + comparador.
- Patrón: Postgres + API ligera + estático (como transparencia_osint).

## Regla
- Datos fiables y trazables primero. No inventar. Señalar claramente lo pendiente.
