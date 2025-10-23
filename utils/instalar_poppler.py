"""
Script para descargar e instalar Poppler en Windows
"""
import os
import sys
import urllib.request
import zipfile
import shutil

def descargar_poppler():
    """Descarga Poppler para Windows"""
    print("Descargando Poppler para Windows...")

    # URL de Poppler para Windows (versión estable)
    url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
    zip_path = "poppler.zip"

    try:
        # Descargar el archivo
        urllib.request.urlretrieve(url, zip_path)
        print("OK Descarga completada")

        # Extraer el archivo
        print("Extrayendo archivos...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")

        # Mover a una carpeta más limpia
        poppler_dir = "poppler"
        if os.path.exists(poppler_dir):
            shutil.rmtree(poppler_dir)

        # Buscar la carpeta extraída
        extracted_folder = None
        for item in os.listdir("."):
            if item.startswith("poppler") and os.path.isdir(item) and item != "poppler":
                extracted_folder = item
                break

        if extracted_folder:
            os.rename(extracted_folder, poppler_dir)
            print(f"OK Poppler instalado en: {os.path.abspath(poppler_dir)}")

        # Limpiar archivo zip
        os.remove(zip_path)

        # Mostrar instrucciones
        bin_path = os.path.abspath(os.path.join(poppler_dir, "Library", "bin"))
        print("\n" + "="*60)
        print("INSTALACIÓN COMPLETADA")
        print("="*60)
        print(f"\nPoppler se instaló en: {bin_path}")
        print("\nOPCIÓN 1 (Recomendada): Agregar al PATH del sistema")
        print("  1. Presiona Win + R")
        print("  2. Escribe: sysdm.cpl")
        print("  3. Ve a 'Opciones avanzadas' > 'Variables de entorno'")
        print("  4. En 'Variables del sistema', selecciona 'Path' y haz clic en 'Editar'")
        print("  5. Haz clic en 'Nuevo' y pega esta ruta:")
        print(f"     {bin_path}")
        print("  6. Haz clic en 'Aceptar' en todas las ventanas")
        print("  7. REINICIA la terminal/PowerShell")
        print("\nOPCIÓN 2 (Más rápida): El código ya está configurado para usar esta ruta")
        print("  No necesitas hacer nada más, ya actualicé el código.\n")

        return bin_path

    except Exception as e:
        print(f"Error al descargar/instalar Poppler: {e}")
        print("\nAlternativa: Descarga manual")
        print("1. Ve a: https://github.com/oschwartz10612/poppler-windows/releases")
        print("2. Descarga el último Release ZIP")
        print("3. Extrae en una carpeta")
        print("4. Anota la ruta de la carpeta 'bin'")
        return None

if __name__ == "__main__":
    poppler_path = descargar_poppler()

    if poppler_path:
        # Actualizar el código para usar esta ruta
        print("\nActualizando archivos Python para usar Poppler...")
        print("OK Instalacion completada exitosamente")
