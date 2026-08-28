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
- **8.109 páginas estáticas por municipio (TODOS)** (`/municipio/{slug}.html`): capitales de
  provincia + top población 2025. Cada ficha: H1, KPIs (2025/1996/Δ%), rank
  nacional, variaciones 1/5/10 años, SVG de evolución, serie completa en <details>
  (texto indexable), JSON-LD Dataset, canonical/OG. Enlace cruzado: mapa →
  ficha (top 300) y Lorca → ficha de transparencia.
- **Sitemap 8.112 URLs** (mapa + ficha Lorca + acerca + 300 municipios).
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

## KPI GRÁFICO (sprint en curso) — maximizar uso
- Feedback usuario: "más impacto visual observar un KPI gráfico". Convertir los KPIs
  numéricos del panel lateral del mapa y la ficha de Lorca en visualizaciones:
  1) Estructura de edad → barra apilada horizontal (3 grupos, H/M en dos tonos).
  2) Evolución 1996-2025 → gráfico de área (línea + relleno degradado).
  3) Crecimiento 1/5/10 años → mini-barras verdes/rojas por signo.
  4) Transparencia Lorca → barras visuales por proveedor (troceado de un vistazo).
  5) Ranking → barra de posición en España.
- Se mantienen los números (datos fiables) convertidos en SVG/Canvas (gen_map.py + gen_lorca_ficha.py).

## PRÓXIMO SPRINT — EXPANDIR LA FICHA DE TRANSPARENCIA A OTROS AYUNTAMIENTOS
- Lorca fue la prueba de concepto (validado el pipeline completo). Pipeline listo y replicable.
- 1) Generalizar gen_lorca_ficha.py → gen_ficha_municipio.py (parametrizado por municipio +
     sus contratos; el parser de PDFs ya es genérico).
- 2) Localizar ayuntamientos con portal de transparencia de la MISMA plantilla que Lorca
     (publican "Relación de contratos menores" trimestral en el mismo formato PDF) → parser
     casi sin cambios. El trabajo es LOCALIZAR portales compatibles, no el código.
- 3) Vía alternativa: datasets de contratos municipales en datos.gob.es / portales regionales
     (patrón transparencia_osint).

## ANÁLISIS EXTERNO REVISADO (21/Ago) — CERTEZA/FALSEDAD + SPRINTS
- Verificado contra el estado real: los POSITIVOS del análisis son ciertos; los NEGATIVOS
  estaban DESACTUALIZADOS (el análisis precedió al sprint SEO): meta/og ya diferenciadas,
  JSON-LD presente, 8.109 páginas estáticas, sitemap 8.112 URLs, vitrinas actualizadas.
- CIERTOS pendientes: llms.txt (404, gap de consistencia), contenido editorial long-tail,
  ficha Lorca = solo 1 municipio (piloto), nombre en inglés (marca), gobernanza de anomalías.
- PARCIAL-FALSO: Overpass runtime — el mapa usa JSON estático; Overpass solo en re-ingesta anual.

## SPRINT A (en curso) — QUICK WINS SEO
- [x] llms.txt para municipal (consistencia con el ecosistema) — HECHO, 200 (fix del 301).
- [x] title/meta con "2025 (INE)" + intención de búsqueda — HECHO.

## SPRINT B (21/Ago) — SEO LONG-TAIL HECHO
- [x] 103 páginas editoriales desde los datos (gen_editorial_pages.py):
      nacional (quiénes más crecen / más se despueblan / más poblados, top-50) +
      por provincia (crecen y se despueblan, top-10, ≥1.000 hab en 2016).
      Indexables (H1 con keyword, meta, canonical, JSON-LD no, tabla con enlaces a las
      fichas de municipio). Sitemap actualizado (+103 URLs). Enlace "Tendencias" en el pie.
      gen_editorial_pages.py en el cron (update.sh).

## SPRINT C (pendiente) — PRODUCTO
- [x] **ALERTAS (Sprint C 2/2, 21/Ago)**: municipal-alert-api (stdlib, puerto 8201, pm2):
      POST /api/alerta (suscripción, doble opt-in vía Resend), /confirmar, /baja,
      /notificar (interno, X-Alert-Secret; detecta cambio de población/ranking/contratos).
      Formulario "Avísame si cambian" en las 8.109 páginas + ficha Lorca. nginx /api/ → 8201.
      update.sh llama a /notificar tras regenerar. SEGURIDAD: data/alerts.env NO al repo
      (.gitignore); push rechazado por secreto → filter-branch limpió el historial local.
- [ ] (completado) RSS + alertas del Sprint C.
- [ ] Isolation Forest en contratos menores para automatizar el troceado a escala.

## SPRINT D (en WAYAHEAD)
- [ ] Extender transparencia a otros ayuntamientos; distribución "España vaciada"
      (X/Mastodon/Bluesky; HN/Reddit problemáticos por experiencia).

## SESIÓN 21/Ago — CERRADA (retomar mañana)
- Sprint A (llms.txt + title/meta) HECHO. Sprint B (103 editoriales long-tail) HECHO.
- Sprint C (RSS + alertas municipales) HECHO (fix envío: User-Agent en Resend; seguridad env).
- Último commit: b7322b6.
- PRÓXIMO (Sprint D): extender transparencia a otros ayuntamientos (generalizar
  gen_lorca_ficha.py → gen_ficha_municipio.py; localizar portales de la misma plantilla
  que Lorca; vía datos.gob.es) + distribución (posts/datos.gob.es listos) + OG dinámico.

## DECISIÓN ESTRATÉGICA (21/Ago) — EL PROBLEMA ES EL ALCANCE, NO LA FRECUENCIA
- Conclusión del usuario (correcta): publicar a diario no sirve si nadie nos ve en
  X/Mastodon/Bluesky. El problema es el ALCANCE (reach), no la frecuencia.
- Sin seguidores no hay reach orgánico en ninguna red. La distribución social sin
  audiencia = gritar en el vacío.
- Los únicos canales que dan descubrimiento SIN audiencia previa:
  1) SEO (Google/Bing) — lento (semanas) pero el único escalable sin seguidores.
  2) datos.gob.es (directorio) — descubrimiento real para proyectos de datos.
  3) El gancho viral puntual (el post de nearme dio 39+6 clics reales SIN audiencia:
     la X los mostró por hashtags/búsqueda) — señal de que un hook fuerte llega solo.
- ACCIÓN (no más posts por posts): priorizar SEO + datos.gob.es; los posts sociales
  SOLO cuando haya un hook real y para validar (no como canal principal).

## SPRINT D — SEGUNDA FICHA DE TRANSPARENCIA: MÁLAGA (22/Ago) ✅
- Via datos.gob.es (camino B, mas robusto que cazar la plantilla del portal de Lorca):
  datasets "Contratos Menores [trimestre] · Ayuntamiento de Málaga" (datosabiertos.malaga.eu).
- Ingesta: malaga_ingest.py (parser ROBUSTO header-driven: detecta la fila de columnas por
  nombre, maneja XLSX y ODS, importe con € o numero plano, cap 40.000 € para menores).
- Datos: 1.976 contratos menores (2024-Q1 a 2026-Q2), 100% con importe y adjudicatario.
- ficha_malaga.html: poblacion (599.063 en 2025), renta 13.847 €/persona (2022, Atlas),
  estructura de edad (Censo 2021), troceado (top proveedores), gasto 15,07 M€.
- Enlace desde /municipio/malaga.html + sitemap (8.113 URLs).
- Commit aeca312. PRÓXIMO: generalizar gen_ficha_municipio.py (un solo generador para
  cualquier ayuntamiento + su dataset) y añadir el parser de Malaga al cron de update.

## GENERADOR GENERALIZADO (22/Ago) ✅
- gen_ficha_municipio.py: config-driven (AYUNTAMIENTOS list). Un generador para cualquier
  ayuntamiento + su dataset de contratos (campo empresa = adjudicatario o razon; menores
  cap 40.000 €; troceado; renta/edad/formales opcionales; lorca_intel.json si intel:True).
- Reemplaza gen_lorca_ficha.py y gen_ficha_malaga.py (deprecados). update.sh usa el nuevo.
- Para añadir un ayuntamiento nuevo: (1) dataset en datos.gob.es/portal, (2) ingestar al
  formato {expediente, objeto, importe, cif, empresa, duracion, periodo}, (3) fila en
  AYUNTAMIENTOS. El parser de Málaga (XLSX/ODS header-driven) sirve de plantilla.
- PRÓXIMO: añadir Madrid/Barcelona/Valencia (grandes gastadores en datos.gob.es) al CONFIG.

## FIX MÓVIL — PWA REAL (22/Ago) ✅
- Bug: en ≤700px la side window (bottom sheet) cubría media pantalla y no se podía
  cerrar; junto al top dejaban el mapa en una franja. Arreglado (commit 6633654):
  en móvil la side window está OCULTA por defecto (mapa a pantalla completa); solo
  aparece como bottom sheet (42vh) al seleccionar un municipio, y el cierre (×) la
  elimina del todo. Top compacto en móvil (título, buscador, sin línea de fechas).
- La PWA es real en smartphone: el mapa es el protagonista, la ficha es contextual.

## HITO 22/Ago — OG DINÁMICO + TOGGLE + CONSISTENCIA ✅
- **OG dinámico** (234 imágenes compartibles): crecen/despueblan/mayores por cambio
  absoluto + % (Yebes +95%, Calañas -44%, Lorca, Madrid...). gen_og_dinamico.py, og:image
  por ficha (fallback genérico). Commit 99b4574.
- **Toggle claro/oscuro** en las 8.109 fichas (template, CSS variables + JS vanilla +
  localStorage). Fix: emoji real en textContent (las entidades HTML se veían &h127 literal).
  Commit bf3733a.
- **Consistencia**: quitar la referencia a Alquimetría del acerca de municipal (declarada
  FRAUDE, on hold). Commit 1e116a0. LECCIÓN: al declarar un servicio fraude, limpiar TODAS
  sus referencias cruzadas, no solo la vitrina.
- **Scouting expansión (honesto)**: Madrid/Barcelona/Valencia NO publican contratos recientes
  de forma accesible (Barcelona 2014-2022, Madrid portal bloqueado, Valencia solo regional).
  La expansión queda LIMITADA POR DATOS (no forzar con obsoletos = lección alquimetría).
  El generador está listo (1 línea en CONFIG cuando haya dato reciente).

## CHECKLIST DE DESARROLLO (obligatoria, 22/Ago) — evita descuidos
Antes de dar una tarea por cerrada, verificar TODAS:
1) **Destino de archivos**: los generados van a `dashboard/`, NUNCA a la raíz del repo
   (revisar rutas de scp/escritura; los datos lorca_*/malaga_menores.json sí van en raíz).
2) **Cron**: todo generador nuevo se añade a `update.sh` EN EL ORDEN de dependencias
   (ej. gen_og_dinamico ANTES de gen_municipio_pages, porque las páginas leen su mapping).
3) **Declarar un servicio fraude/on-hold**: limpiar TODAS sus referencias — vitrina
   (index+ecosistema+ItemList), healthcheck, enlaces cruzados en OTROS servicios.
4) **Higiene final**: `git status` limpio, sin ficheros sueltos en raíz, `git ls-files`
   revisado, y el generado servido verificado (curl 200 + contenido esperado).
5) **Datos**: nunca forzar datos obsoletos para "completar" una ficha (lección alquimetría);
   si la fuente es antigua, documentarlo y NO publicar como si fuera actual.
6) **Procesos en segundo plano**: lanzar con pm2 (no setsid/nohup que mueren al cerrar ssh),
   y limpiar el proceso al terminar.

## Roadmap
- [x] P0.5: dataset INE población municipal 1996-2025 (8.132 municipios).
- [x] P1: catálogo municipios (códigos INE + coords) — 8.109 municipios (99,7%).
- [x] P2: mapa Leaflet + buscador + sparkline — DESPLEGADO.
- [x] P3 (parcial): ficha de transparencia de Lorca (contratos + troceado + renta).
- [x] SEO: JSON-LD + 300 fichas estáticas + sitemap 8.112 URLs.
- [ ] P3: ficha municipio: contratos del ayuntamiento (PLACSP export manual o
      crawl) y finanzas (Facturas CARM). Población ya en la ficha del mapa.
- [ ] P4: indicadores + cambios + comparador (rankings, variaciones interanuales).
- Patrón: estático generado + nginx (como transparencia_osint y alquimetria).

## SPRINT E (22/Ago) — PLANIFICADO: credibilidad, visual, cobertura
Análisis completo en el repo local del portátil: 220826_municipal-analisis-sprint-E.md.
GAPS VERIFICADOS (22/Ago):
1. SIN CSV descargable — el guest post lo promete y datos.gob.es lo exige (claim falso hoy).
2. KPI gráfico a medias (los 5 visuales del feedback no implementados).
3. Comparador sin permalink indexable (/comparar/a-vs-b.html = long-tail perdido).
4. 27 municipios fuera de mapa/fichas (catálogo 99,7%).
5. Renta solo en Lorca/Málaga; sin malla interna geográfica.
6. OG dinámico limitado a 234 imágenes.
PLAN (orden recomendado):
- P0 (medio día): E1 gen_export_csv.py (CSV nacional completo + README + página /datos.html,
  en update.sh tras ingestas) -> E2 alta en datos.gob.es con URL real -> E3 GSC + IndexNow
  para editoriales/OG nuevas.
- P1 (1-2 días): E4 KPI gráfico (edad apilada, área evolución, mini-barras ±, barras
  proveedores, barra ranking; en gen_municipio_pages + gen_ficha_municipio) · E5 comparador
  permalink estático con pares semilla · E6 OG dinámico top-1.000 + top movers %.
- P2 (1-2 días): E7 catálogo 100% vía codmun INE oficial (cierra los 27) · E8 renta Atlas INE
  municipal en TODAS las fichas ("renta [pueblo]" = volumen SEO real) · E9 bloque "Cercanos"
  (<=15 km, 5 enlaces, coords del catálogo) en cada ficha (~40k enlaces internos nuevos).
- P3 (backlog): E10 scouting CARM (Murcia capital/Cartagena; regla anti-alquimetría:
  solo 2024-2026 accesible; generador listo = 1 línea CONFIG) · E11 Isolation Forest
  cuando haya >=3 ayuntamientos.
- Quick win: loop viral en alertas (post-confirmación -> "comparte tu pueblo" con og:image).
REGLA: nada se distribuye (guest post/datos.gob.es) hasta cerrar E1 (el claim CSV debe ser verdad).
BACKUP: todos los repos del ecosistema tienen remoto GitHub (auditoría 22/Ago: 21 repos mcasrom/*,
municipal-intel 0 commits pendientes de push).

## SPRINT E — E1 HECHO (22/Ago): EXPORT CSV PUBLICO ✅
- gen_export_csv.py: dashboard/data/csv/poblacion-municipal-espana-1996-2025.csv
  (235.376 filas = 8.136 municipios x 29 anos, Total; codigo_ine via catalogo LEFT JOIN,
  NULLS LAST), README.txt (campos/licencia CC-BY-4.0/fuente INE) y landing datos.html
  (JSON-LD Dataset con DataDownload, canonical, OG).
- VALIDADO: total Espana 2025 = 49.114.494 (== validacion INE del P1).
- gen_municipio_pages.py: datos.html anadido a la base del sitemap (8.114 URLs).
- update.sh: gen_export_csv.py primero en la regeneracion (cron 05:30).
- VERIFICADO en vivo: /datos.html 200, CSV 9,1 MB raw (~2,3 MB gzip), README 200.
- NOTA OPERATIVA: gen_municipio_pages tarda ~20 min en el VPS; lanzar siempre
  desacoplado (nohup/setsid o pm2) — una sesion ssh muerta se llevo la primera
  corrida sin escribir sitemap. El CSV se versiona (cambia solo cuando cambia el INE).
- SIGUIENTE: E2 (alta en datos.gob.es apuntando al CSV real) -> E3 (IndexNow/GSC).

## Hito: 2ª fuente de alquiler MIVAU (reemplaza a Fotocasa) + etiquetado — 28/Ago
- **Problema**: fuente Fotocasa bloqueada (HTTP 403 anti-bot). Quedaban 3 filas legadas.
- **Solución**: `scripts/via_mivau.py` — fuente oficial MIVAU (Serpavi) del índice de alquiler.
  CSV público `https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP001_01.csv`
  (~38MB, separador `;`, **COD_POSTAL = código INE**). `ELEMENTO=PRECIO` (€/mes) /
  `SUPERFICIE` (m²); `TIPO_MEDIDA=MEDIANA/PERCENT25/PERCENT75`.
  - €/m² = PRECIO del percentil / **SUPERFICIE MEDIANA** (denominador común → garantiza
    p25<=mediana<=p75, 0 violaciones). NO usar la superficie del propio percentil (invertía orden).
  - Cache 24h en `/tmp/vdp001_01.csv`; `INSERT OR REPLACE` solo municipios no cubiertos
    (check `anuncios>=5 OR slug LIKE 'mivau_%'`); slug `mivau_<ine>`, anuncios=-1,
    alq=renta mediana real. Lock propio `/tmp/via_mivau.lock`.
  - Backfill: `via_index` 292→**431 municipios** (289 pisos + 3 fotocasa legados + 139 MIVAU
    2024), 0 duplicados INE, 0 violaciones, Cangas (36008) vía `INE_MANUAL`.
- **Etiquetado honesto de fuentes** (`gen_alquiler_page.py`): se usa el campo `slug` como
  marcador (`mivau_` → "oficial SERPAVI/MIVAU contratos cerrados 2024"; resto → "anuncios
  activos pisos.com + pocos legados fotocasa"). KPIs/gráficos solo sobre filas de oferta.
  Página: "431 municipios (292 anuncios activos, 139 dato oficial 2024)".
- **Cron semanal** (domingo 06:40): via_scraper.py → via_mivau.py + gen_alquiler_page.py.
- **Publicación en redes** (mecanismo descubierto común al ecosistema, ver WAYAHEAD nearme):
  `social-poster/publish_{bluesky,mastodon}.py` vía `270826_auto_post.py` local. X manual 140.
- **Vía paralela**: petición SER a datos.gob.es de precios de alquiler €/m² (estado Asignado,
  M. Vivienda) — lenta/manual, en paralelo.

## Hito: Verificación semanal de via_mivau con alerta Telegram (28/Ago)
- **Motivo**: el backfill semanal (dom 06:40) y la regeneración de la página podían fallar
  sin que nadie se enterara durante 7 días.
- **Implementado**: `scripts/via_mivau_health.py` (python3 de sistema, solo stdlib). Detecta:
  (1) `alquiler.html` sin regenerar hace >8 días (la cadena `via_mivau && gen_alquiler_page`
  regenera el archivo; si via_mivau falla o el cron no corre, queda stale) y
  (2) `logs_via_mivau.log` con Traceback/ERROR.
- **Notificación**: Telegram (reutiliza `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` del .env de
  nearme, patrón de pm2_health.py). **Dedup por condición estable** (mtime del log de error o
  de la página), para no spamear el mismo fallo semanas seguidas. Sin fallo → OK silencioso.
- **Cron**: `5 7 * * 0` (dom 07:05, 25 min tras el backfill). Log: logs_via_mivau_health.log.
  Backups crontab: /tmp/cron_backup_before_mivau_health_20260828.txt (server).
- **Probado**: condicion normal OK; fallo simulado (Traceback en log) → ENVIADO y dedup
  (2a ejecucion skip); limpio el log de prueba. Commit propio.
