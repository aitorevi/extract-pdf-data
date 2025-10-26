#!/bin/bash
# Script para generar PDFs de prueba en macOS
# Doble clic para ejecutar desde Finder

cd "$(dirname "$0")"

echo "========================================="
echo "  Generador de PDFs de Prueba"
echo "========================================="
echo ""

# Activar virtualenv
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtualenv activado"
else
    echo "⚠️  No se encontró virtualenv (.venv)"
fi

# Instalar reportlab si no está
python -c "import reportlab" 2>/dev/null || {
    echo "📦 Instalando reportlab..."
    pip install reportlab
}

# Ejecutar script
echo ""
python crear_pdf_prueba.py

echo ""
echo "========================================="
echo "  Presiona Enter para cerrar..."
echo "========================================="
read
