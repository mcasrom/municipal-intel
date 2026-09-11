# Editorial replicable: Alquiler + Población

## Formato que disparó el pico 30/08
\`municipios-pierden-poblacion-alquiler-sube.html\` — 39 hits, correlacionó
dos datasets: Via (alquiler €/m2, 289 municipios) + poblacion 1996-2025.

## Plantilla replicable (1/semana)
**Titulo**: "{N} municipios donde el alquiler sube X% mientras pierden población"
**Datos**: JOIN via_index (eur_m2_mediana) + poblacion (variacion 2015-2025)
**Criterio**: municipios con eur_m2 >15€ Y poblacion -5% en 10 años
**Visual**: scatter (x=poblacion delta, y=eur_m2) + tabla top 10
**CTA**: link a /mapa-alquiler.html y a cada ficha /municipio/{slug}.html

## Próximos 4 editoriales sugeridos
1. Donde el alquiler es más barato y la población crece (inversa)
2. Capitales vs pueblo: brecha de alquiler 2025
3. Coste de 80m2/mes por provincia (ranking)
4. Municipios con dato oficial vs oferta (contraste SERPAVI)

## Producción
Fuente: gen_editorial_pages.py — añadir nuevo template.
