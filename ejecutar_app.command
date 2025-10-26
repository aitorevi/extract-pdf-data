#!/bin/bash
# Script para ejecutar la aplicación principal en macOS
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

# Ejecutar aplicación
echo ""
python src/main.py

echo ""
echo "========================================="
echo "  Aplicación cerrada"
echo "========================================="
echo "Presiona Enter para cerrar..."
read
