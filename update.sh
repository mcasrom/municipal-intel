#!/usr/bin/env bash
# update.sh — Municipal Intelligence: chequeo de datos + regeneración programada
# - Lorca: detecta trimestres de contratos menores nuevos (transparencia.lorca.es)
# - INE: detecta si hay un año de población más reciente (Revisión del Padrón, anual)
# - Regenera el sitio (idempotente y barato)
# Cron sugerido: 30 5 * * * /home/deploy/municipal-intel/update.sh >> /home/deploy/municipal-intel/logs/update.log 2>&1
set -u
cd /home/deploy/municipal-intel
mkdir -p logs
LOG=logs/update.log
echo "" >> "$LOG"
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG"

echo "-- Lorca: trimestres nuevos?" >> "$LOG"
python3 lorca_check_new.py >> "$LOG" 2>&1
LORCA_CHANGED=$?

echo "-- INE: año nuevo?" >> "$LOG"
python3 ine_check_new.py >> "$LOG" 2>&1
INE_CHANGED=$?

echo "-- regeneración del sitio" >> "$LOG"
python3 gen_map.py >> "$LOG" 2>&1
python3 gen_lorca_ficha.py >> "$LOG" 2>&1
python3 gen_municipio_pages.py >> "$LOG" 2>&1
python3 gen_acerca.py >> "$LOG" 2>&1
python3 gen_rss.py >> "$LOG" 2>&1
echo "regenerado OK (lorca_cambios=$LORCA_CHANGED ine_cambios=$INE_CHANGED)" >> "$LOG"
