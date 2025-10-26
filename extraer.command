#!/bin/bash
# Script para ejecutar extracción de facturas en macOS
# Doble clic para ejecutar desde Finder

cd "$(dirname "$0")"

echo "========================================="
echo "  Extractor de Datos de Facturas PDF"
echo "========================================="
echo ""

# Activar virtualenv
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtualenv activado"
else
    echo "⚠️  No se encontró virtualenv (.venv)"
fi

# Ejecutar extracción
echo ""
echo "📄 Iniciando extracción de facturas..."
echo ""
python scripts/extraer.py

echo ""
echo "========================================="
echo "  Proceso finalizado"
echo "========================================="
echo "Presiona Enter para cerrar..."
read
