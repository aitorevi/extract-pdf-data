#!/bin/bash
# Script para abrir editor de plantillas en macOS
# Doble clic para ejecutar desde Finder

cd "$(dirname "$0")"

echo "========================================="
echo "  Editor de Plantillas PDF"
echo "========================================="
echo ""

# Activar virtualenv
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtualenv activado"
else
    echo "⚠️  No se encontró virtualenv (.venv)"
fi

# Ejecutar editor
echo ""
echo "🎨 Abriendo editor de plantillas..."
echo ""
python src/editor_plantillas.py

echo ""
echo "========================================="
echo "  Editor cerrado"
echo "========================================="
echo "Presiona Enter para cerrar..."
read
