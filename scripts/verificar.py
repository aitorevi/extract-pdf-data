"""
Script simplificado para verificar la estructura del proyecto.
Uso: python scripts/verificar.py o doble clic en verificar.bat
"""
import sys
import os

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import FacturaExtractorApp

if __name__ == "__main__":
    app = FacturaExtractorApp()
    app.mostrar_banner()

    print("Verificando estructura del proyecto...\n")

    if app.verificar_estructura_proyecto():
        print("\nOK Todo listo para procesar facturas!")
        print("\nProximos pasos:")
        print("  1. Coloca tus PDFs en la carpeta 'facturas/'")
        print("  2. Crea plantillas con: python scripts/editor.py (o doble clic en editor.bat)")
        print("  3. Extrae datos con: python scripts/extraer.py (o doble clic en extraer.bat)")
    else:
        print("\nERROR Hay problemas que debes resolver antes de continuar.")
        sys.exit(1)
