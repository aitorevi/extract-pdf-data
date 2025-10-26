#!/bin/bash
# Script para probar extracción multipágina en macOS
# Doble clic para ejecutar desde Finder

cd "$(dirname "$0")"

echo "========================================="
echo "  Test Extracción Multipágina"
echo "========================================="
echo ""

# Activar virtualenv
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtualenv activado"
else
    echo "⚠️  No se encontró virtualenv (.venv)"
fi

# Ejecutar tests
echo ""
python test_extraccion_multipagina.py

echo ""
echo "========================================="
echo "  Presiona Enter para cerrar..."
echo "========================================="
read
