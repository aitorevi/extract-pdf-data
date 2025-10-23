"""
Script simplificado para el editor de plantillas.
Uso: python scripts/editor.py o doble clic en editor.bat
"""
import os
import sys

if __name__ == "__main__":
    print("Iniciando editor de plantillas...\n")

    # Cambiar al directorio raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    # Ejecutar el editor de plantillas
    os.system("python src/editor_plantillas.py")
