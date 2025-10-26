#!/bin/bash
# Script para ejecutar todos los tests en macOS
# Doble clic para ejecutar desde Finder

cd "$(dirname "$0")"

echo "========================================="
echo "  EJECUTAR TODOS LOS TESTS"
echo "========================================="
echo ""

# Activar virtualenv
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtualenv activado"
else
    echo "⚠️  No se encontró virtualenv (.venv)"
fi

echo ""
echo "🧪 Ejecutando suite de tests..."
echo ""

# Ejecutar tests de extracción multipágina
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python tests/test_multipagina_extraccion.py
TEST1_EXIT=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python tests/test_manejo_errores.py
TEST2_EXIT=$?

echo ""
echo "========================================="
echo "  RESUMEN FINAL"
echo "========================================="

if [ $TEST1_EXIT -eq 0 ] && [ $TEST2_EXIT -eq 0 ]; then
    echo "✅ TODOS LOS TESTS PASARON"
    EXIT_CODE=0
else
    echo "❌ ALGUNOS TESTS FALLARON"
    EXIT_CODE=1
fi

echo ""
echo "Presiona Enter para cerrar..."
read

exit $EXIT_CODE
