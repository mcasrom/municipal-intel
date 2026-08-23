# 💡 PROPUESTAS — Productos sobre datos .gob.es (bitácora de evaluación)
Creado 23/Ago/2026 · para seguimiento junto a SEGUIMIENTO.md · estado: PROPUESTA
> 🛡️ Este documento vive TAMBIÉN en ~/municipal-intel/docs/ (server, respaldado en GitHub).
> Si se pierde este chat: leer WAYAHEAD.md del server + este archivo + SEGUIMIENTO.md local.

## 🚩 HITOS (marcar fecha al completar)
### P3 Optimizador PVPC
- [ ] H3.1 MVP: mejor franja 24h desde ESIOS (nearme ya lee REE)
- [ ] H3.2 aviso Telegram/push
- [ ] H3.3 tarjeta en www + ecosistema

### P2 España Vaciada Radar
- [ ] H2.1 Fórmula índice vaciamiento definida y documentada
- [ ] H2.2 Ingest paro SEPE municipal (mensual)
- [ ] H2.3 Sección "proyección 2040" en fichas municipales
- [ ] H2.4 Mapa nacional + página índice

### P1 Índice VIA (radar alquiler)
- [x] H1.0 Test viabilidad fuente — SUPERADO 23/Ago (pisos.com OK; idealista/fotocasa/habitaclia bloquean)
- [x] H1.1 Prototipo medición €/m² — 23/Ago (p1_pisos_probe.py; Madrid 17,65 · BCN 19,86 · Val 14,08 · Cuenca 7,85)
- [ ] H1.2 Scraper completo: ~140 municipios >20k hab × 2-3 páginas, rate 4s
- [ ] H1.3 SQLite serie semanal + cron dominical con lock
- [ ] H1.4 Página pública índice (/alquiler o integrado en municipal)
- [ ] H1.5 Bloque "Alquiler hoy" en las 8.113 fichas municipales ← valor añadido linkable
- [ ] H1.6 Previsión 30 días (requiere 4-8 semanas de serie acumulada)

---

## ⚠️ REGLA DE ORO (lección Alquimetria)
> **Alquimetria murió** por ofrecer precios históricos (2024) sin valor presente.
> El usuario quiere **precio para alquilar HOY** y **previsión del PRÓXIMO MES**.
>
> **Toda propuesta debe pasar este filtro antes de construirse:**
> ✅ ¿Puedo mostrar un dato del mes en curso?
> ✅ ¿Puedo dar una tendencia/previsión a 30 días justificada?
> ❌ Si solo hay histórico viejo → NO construir (o etiquetarlo como contexto, nunca como oferta principal)

---

## 📊 TABLA RESUMEN (puntuación 1–5 por eje · total /20)

| # | Propuesta | Demanda | Frescura | Previsión | Sinergia infra | Esfuerzo⁻ | TOTAL | Estado |
|---|---|---|---|---|---|---|---|---|
| P1 | 🏠 Radar de Alquiler EN VIVO (resurrección de Alquimetria bien hecha) | 5 | 4* | 4 | 3 | 2 | **18*** | ⭐ flagship si el scraper aguanta |
| P2 | 📉 España Vaciada Radar + proyección 2040 | 4 | 5 | 4 | 5 | 5 | **18** | ⭐ quick win — infra ya existe |
| P3 | ⚡ Optimizador PVPC doméstico ("¿cuándo pongo la lavadora?") | 4 | 5 | 5 | 5 | 5 | **19** | ⭐ más fácil + más fresco |
| P4 | 🔥 Historial de riesgo incendios por municipio | 4 | 5 | 3 | 5 | 4 | **17** | estacionalidad brutal |
| P5 | 🗺️ ¿Dónde puedo permitirme vivir? (sueldo→mapa) | 5 | 3 | 3 | 5 | 3 | **16** | depende de P1 para ser fresco |
| P6 | 🏖️ Termómetro de presión turística | 4 | 4 | 3 | 4 | 3 | **14** | ángulo periodístico fuerte |
| P7 | 💼 Mapa de oportunidades laboral (SEPE × jobs radar) | 3 | 5 | 4 | 4 | 4 | **16** | mensual garantizado |
| P8 | ⚖️ Comparador coste de vida real (IBI+luz+alquiler) | 4 | 3 | 2 | 4 | 3 | **12** | IBI anual OK, alquiler hereda problema |
| P9 | 🌫️ Tu aire, tus años (histórico calidad aire por CP) | 3 | 5 | 3 | 4 | 4 | **15** | nicho salud creciente |

*Frescura de P1 condicionada a que el scraper de portales funcione (ver riesgo).

---

## FICHAS DETALLADAS

### P1 🏠 RADAR DE ALQUILER EN VIVO — *la resurrección correcta de Alquimetria*
- **Qué**: índice propio €/m² por municipio **actualizado semanal** desde portales (idealista, fotocasa, habitaclia) + **previsión a 30 días** (modelo estacional + momentum). Publicado como "Índice VIA" (Viaje Inteligencia Alquiler).
- **Usuario**: quien busca piso hoy — precio real de anuncios activos, no media fiscal del año pasado.
- **Datos**: scraping propio (anuncios activos = frescura real) + contraste con Sistema estatal MITMA/AEAT (trimestral/anual, como validación, nunca como titular).
- **Previsión 30d**: serie propia acumulada + estacionalidad mensual conocida del mercado.
- **MVP**: 10 provincias top → 1 página/municipio reutilizando plantilla de municipal-intel.
- **Riesgos**: bloqueos anti-scraping (Cloudflare ya nos bloqueó headless una vez), legal (datos públicos agregados + citar fuente, sin reproducir fichas individuales). *Si el scraper muere, el producto muere — igual que Alquimetria. Probar viabilidad ANTES de prometer nada.*
- **KPI éxito**: % municipios con índice <7 días de antigüedad ≥90%.

### P2 📉 ESPAÑA VACIADA RADAR
- **Qué**: índice de vaciamiento por municipio (población -%, edad media ↑, saldo vegetativo −, paro) + **proyección 2040**. Mapa nacional + ficha por municipio.
- **Por qué funciona**: tema mediático permanente; tenemos el 80% de los datos YA en producción (municipal-intel).
- **Datos**: INE población (nuestro CSV 235k filas) + MIR/SEPE paro municipal + INE nacimientos/defunciones.
- **Previsión**: extrapolación demográfica simple por municipio (metodología publicada = credibilidad).
- **Esfuerzo**: BAJO — es una capa nueva sobre lo existente. Backlinks: prensa local lo citará.
- **KPI**: primeras 5 citas de prensa local en 60 días.

### P3 ⚡ OPTIMIZADOR PVPC — *"¿cuándo pongo la lavadora esta semana?"*
- **Qué**: mejor franja horaria de las próximas 24–72h según tu consumo típico + aviso Telegram/push cuando toque.
- **Frescura PERFECTA**: PVPC se publica día adelantado → previsión real, no estimación.
- **Datos**: REE/ESIOS (nearme ya lee cada 15 min) + calendario festivos/nacionales.
- **Esfuerzo**: BAJO. SEO: búsquedas constantes de "precio luz mañana".
- **KPI**: usuarios recurrentes semanales (retención > visitas únicas).

### P4 🔥 RIESGO INCENDIOS HISTÓRICO POR MUNICIPIO
- **Qué**: mapa 20 años de focos FIRMS + superficie quemada + clima → score de riesgo por municipio + seguro/vivienda como caso de uso.
- **Momento**: tras las olas 2025-26, búsquedas de "riesgo incendios mi zona" disparadas.
- **Datos**: NASA FIRMS (ya integrado en nearme, solo añadir archivo) + MITECO área quemada + AEMET.
- **KPI**: pico estacional + base estable de fichas municipales indexadas.

### P5 🗺️ ¿DÓNDE PUEDO PERMITIRME VIVIR?
- **Qué**: metes sueldo bruto → mapa de municipios donde alquiler ≤30% renta. Heatmap nacional.
- **Dependencia**: necesita P1 funcionando para cumplir Regla de Oro (los datos oficiales van con 1–2 años de retraso → solo sirven como capa "contexto oficial").
- **Decisión sugerida**: NO construir hasta validar P1.

### P6 🏖️ TERMÓMETRO DE PRESIÓN TURÍSTICA
- **Qué**: % viviendas turísticas sobre parque por municipio/barrio + rentabilidad temporal vs habitual (brecha = incentivo a convertir).
- **Datos**: Registro Estatal VUT (mensual) + AEAT estadística viviendas IRPF (rentabilidad bruta por modalidad — nueva, granular) + catastro.
- **Ángulo**: cada polémica turística = tráfico. Prensa local/nacional citará mapas.

### P7 💼 MAPA DE OPORTUNIDADES LABORAL
- **Qué**: paro registrado municipal (SEPE, **mensual**) vs ofertas activas del radar jobs → "ratio oportunidad" por provincia/municipio.
- **Sinergia**: alimenta y alimenta-se de oi-career-radar.

### P8 ⚖️ COMPARADOR COSTE DE VIDA REAL
- **Qué**: X vs Y: alquiler (P1) + IBI medio (catastro) + luz (REE) + transporte.
- **IBI anual = aceptable** (impuesto no cambia cada mes); el resto depende de P1.

### P9 🌫️ TU AIRE, TUS AÑOS
- **Qué**: histórico + tendencia anual de calidad del aire por estación/código postal, con lenguaje salud ("días limpios al año en tu zona").
- **Datos**: MITECO 620 estaciones + OpenAQ (ya en nearme).

---

## 🎯 ORDEN RECOMENDADO (con la Regla de Oro aplicada)
1. **P3 PVPC** — 2–3 días de trabajo, frescura total, sinergia nearme. Victoria rápida.
2. **P2 Vaciada Radar** — 1 semana, infra existente, backlinks prensa. Victoria estratégica.
3. **P4 Incendios** — aprovechar cola de la temporada; archivo FIRMS ya accesible.
4. **P1 Radar Alquiler** — probar viabilidad del scraper en 10 municipios ANTES de comprometerse. Si pasa la prueba → flagship absoluto (y P5/P8 se desbloquean solos).

## 🏃 SPRINT F (aprobado pendiente ejecución)
### F-A = H1.2 scraper VIA completo
- Universo: municipios ≥20k hab de NUESTRO CSV INE 2025 (~150)
- Slug pisos.com: minúsculas sin tildes, espacios→"-"; validar h1 contiene nombre; fallos a log
- Paginación: descubrir patrón (?pagina=N), máx 3 pág/ciudad · rate 4s · retry ×2 · flock
- Cron dominical 06:00 (~30 min ciclo) → SQLite via_index + JSON
- Publicar solo con ≥5 anuncios; aceptación: ≥80% municipios válidos primer ciclo
- PASO 0: validar 10 slugs difíciles (A Coruña, San Sebastián…)

### F-B = H2.1 fórmula IV (Índice de Vaciamiento 0-100)
- IV = 35·ΔPob10a + 25·envejecimiento + 20·saldo_vegetativo + 20·paro_vs_provincia
- s₁: pérdida ≥15%/10a → 1.0 (YA en nuestro CSV) · s₂: %65+ vs media nacional (ingest futura)
- s₃: saldo vegetativo INE anual · s₄: SEPE mensual (llega con H2.2)
- Umbrales: ≥60 crítico / 40-60 alto / 20-40 tensión / <20 estable
- Proyección 2040: P·(1+Δ/10)^15 cap±40% etiquetada "proyección simple"
- MVP hoy: IV con s₁+s₃ → top-50 ranking + sanity check (Soria/Teruel/Asturias rural)

## Registro de decisiones
| Fecha | Decisión |
|---|---|
| 23/Ago | Documento creado. Ninguna propuesta aprobada aún — esperar review del usuario |
| 23/Ago | **TEST P1 SUPERADO**: prototipo p1_pisos_probe.py mide €/m² mediana en vivo desde pisos.com (único portal grande sin bloqueo; idealista=fotocasa=habitaclia=rentalia 403/DataDome incluso con Chrome headless). Resultados realistas: Madrid 17,65 · BCN 19,86 · Val 14,08 · Cuenca 7,85 €/m² (~20 anuncios válidos/página). Script en ~/Desktop/demo/. Pendiente construir: paginación, ~140 municipios >20k hab, DB semanal, previsión 30d tras acumular serie |
| 23/Ago | Diagnóstico news: parón percibido = efecto domingo (768 art sábado vs ~950 diario); sistema OK. Tarea menor: revisar 4 feeds muertos desde 31/jul (Al Jazeera, Anadolu, Al-Monitor, The National) + añadir redirect de logs al cron run.sh |
