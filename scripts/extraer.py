"""
Script simplificado para extraer datos de facturas.
Uso: python scripts/extraer.py o doble clic en extraer.bat
"""
import sys
import os

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import FacturaExtractorApp

if __name__ == "__main__":
    app = FacturaExtractorApp()
    app.mostrar_banner()

    # Verificar estructura
    if not app.verificar_estructura_proyecto():
        sys.exit(1)

    # Ejecutar procesamiento
    print("\nIniciando extracción de facturas...\n")
    exito = app.modo_procesamiento(auto_export=True, formato_salida="todos")

    if exito:
        print("\n✓ Extracción completada exitosamente!")
        print("  Revisa la carpeta 'resultados/' para ver los archivos generados.")
    else:
        print("\n✗ Hubo problemas durante la extracción.")
        sys.exit(1)
