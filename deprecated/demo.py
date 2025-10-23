"""
Script de demostración para la aplicación de extracción de facturas PDF.
Crea datos de ejemplo y demuestra el flujo completo.
"""

import os
import json
from datetime import datetime
from pdf_extractor import PDFExtractor
from excel_exporter import ExcelExporter


def crear_facturas_demo():
    """Crea facturas de demostración en la carpeta facturas/."""
    print("=== CREANDO DATOS DE DEMOSTRACIÓN ===")

    # Crear directorio si no existe
    os.makedirs("facturas", exist_ok=True)

    # Información de archivos demo (simulados)
    archivos_demo = [
        "factura_suministros_a_001.pdf",
        "factura_suministros_a_002.pdf",
        "factura_proveedor_b_001.pdf",
        "factura_ejemplo_003.pdf"
    ]

    for archivo in archivos_demo:
        ruta_archivo = os.path.join("facturas", archivo)
        if not os.path.exists(ruta_archivo):
            # Crear archivo placeholder
            with open(ruta_archivo, 'w') as f:
                f.write(f"# Archivo demo: {archivo}\n")
                f.write("# Reemplaza con facturas PDF reales para usar la aplicación\n")

    print(f"OK {len(archivos_demo)} archivos demo creados en facturas/")
    return archivos_demo


def crear_plantilla_demo():
    """Crea una plantilla de demostración."""
    print("=== CREANDO PLANTILLA DE DEMOSTRACIÓN ===")

    os.makedirs("plantillas", exist_ok=True)

    plantilla_demo = {
        "proveedor_id": "DEMO_001",
        "nombre_proveedor": "Suministros Demo S.L.",
        "imagen_referencia": "imagenes_muestra/demo_factura.png",
        "dpi_imagen": 300,
        "campos": [
            {
                "nombre": "NIF_Proveedor",
                "coordenadas": [100.0, 750.0, 200.0, 770.0],
                "tipo": "texto",
                "coordenadas_pixeles": [400, 100, 800, 140]
            },
            {
                "nombre": "Fecha_Factura",
                "coordenadas": [400.0, 720.0, 500.0, 740.0],
                "tipo": "fecha",
                "coordenadas_pixeles": [1600, 150, 2000, 190]
            },
            {
                "nombre": "Numero_Factura",
                "coordenadas": [400.0, 740.0, 500.0, 760.0],
                "tipo": "texto",
                "coordenadas_pixeles": [1600, 100, 2000, 140]
            },
            {
                "nombre": "Total_Factura",
                "coordenadas": [450.0, 100.0, 550.0, 120.0],
                "tipo": "numerico",
                "coordenadas_pixeles": [1800, 2000, 2200, 2040]
            },
            {
                "nombre": "Base_Imponible",
                "coordenadas": [350.0, 120.0, 450.0, 140.0],
                "tipo": "numerico",
                "coordenadas_pixeles": [1400, 1960, 1800, 2000]
            },
            {
                "nombre": "IVA",
                "coordenadas": [450.0, 120.0, 520.0, 140.0],
                "tipo": "numerico",
                "coordenadas_pixeles": [1800, 1960, 2080, 2000]
            }
        ]
    }

    ruta_plantilla = "plantillas/demo_proveedor.json"
    with open(ruta_plantilla, 'w', encoding='utf-8') as f:
        json.dump(plantilla_demo, f, ensure_ascii=False, indent=4)

    print(f"OK Plantilla demo creada: {ruta_plantilla}")
    return ruta_plantilla


def crear_datos_demo():
    """Crea datos de demostración simulados."""
    print("=== CREANDO DATOS DE DEMOSTRACIÓN ===")

    datos_demo = [
        {
            "Archivo": "factura_suministros_a_001.pdf",
            "Proveedor_ID": "DEMO_001",
            "Proveedor_Nombre": "Suministros Demo S.L.",
            "NIF_Proveedor": "B12345678",
            "Fecha_Factura": "15/03/2024",
            "Numero_Factura": "FAC-2024-001",
            "Total_Factura": "1234.56",
            "Base_Imponible": "1020.30",
            "IVA": "214.26",
            "Fecha_Procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "Archivo": "factura_suministros_a_002.pdf",
            "Proveedor_ID": "DEMO_001",
            "Proveedor_Nombre": "Suministros Demo S.L.",
            "NIF_Proveedor": "B12345678",
            "Fecha_Factura": "20/03/2024",
            "Numero_Factura": "FAC-2024-002",
            "Total_Factura": "856.33",
            "Base_Imponible": "708.00",
            "IVA": "148.33",
            "Fecha_Procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "Archivo": "factura_proveedor_b_001.pdf",
            "Proveedor_ID": "NO_IDENTIFICADO",
            "Proveedor_Nombre": "",
            "Error": "Proveedor no identificado - plantilla no disponible",
            "Fecha_Procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            "Archivo": "factura_ejemplo_003.pdf",
            "Proveedor_ID": "DEMO_001",
            "Proveedor_Nombre": "Suministros Demo S.L.",
            "NIF_Proveedor": "B12345678",
            "Fecha_Factura": "ERROR",
            "Numero_Factura": "FAC-2024-003",
            "Total_Factura": "ERROR_PDF",
            "Base_Imponible": "ERROR_PDF",
            "IVA": "ERROR_PDF",
            "Error": "Archivo PDF corrupto o ilegible",
            "Fecha_Procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]

    print(f"OK {len(datos_demo)} registros de datos demo preparados")
    return datos_demo


def ejecutar_demo_exportacion():
    """Ejecuta la demostración de exportación."""
    print("\n=== DEMOSTRACIÓN DE EXPORTACIÓN ===")

    # Crear datos demo
    datos = crear_datos_demo()

    # Crear directorio de resultados
    os.makedirs("resultados", exist_ok=True)

    # Crear exportador
    exporter = ExcelExporter(datos, directorio_salida="resultados")

    # Exportar en todos los formatos
    print("\nExportando en todos los formatos...")
    resultados = exporter.exportar_todo("demo")

    print(f"\nOK Demostración completada. Archivos generados:")
    for formato, ruta in resultados.items():
        if ruta:
            print(f"   {formato}: {ruta}")

    return resultados


def mostrar_instrucciones():
    """Muestra las instrucciones para usar la aplicación real."""
    print("\n" + "=" * 60)
    print("    INSTRUCCIONES PARA USO REAL")
    print("=" * 60)
    print()
    print("1. PREPARAR FACTURAS REALES:")
    print("   - Reemplaza los archivos .pdf en facturas/ con facturas reales")
    print("   - Pueden ser de cualquier proveedor")
    print()
    print("2. CREAR PLANTILLAS PARA TUS PROVEEDORES:")
    print("   - Ejecuta: python coordinate_extractor.py")
    print("   - O usa: python main.py coordenadas")
    print("   - Selecciona campos en una factura de muestra")
    print("   - Guarda las plantillas JSON")
    print()
    print("3. PROCESAR TUS FACTURAS:")
    print("   - Ejecuta: python main.py procesar")
    print("   - La aplicación identificará proveedores automáticamente")
    print("   - Se generarán archivos Excel, CSV y JSON")
    print()
    print("4. ARCHIVOS NECESARIOS:")
    print("   facturas/       - Tus archivos PDF")
    print("   plantillas/     - Plantillas JSON (una por proveedor)")
    print("   resultados/     - Archivos de salida generados")
    print()
    print("5. PERSONALIZACIÓN:")
    print("   - Edita las plantillas JSON para ajustar coordenadas")
    print("   - Agrega nuevos campos en las plantillas")
    print("   - Modifica los tipos de campo (texto, fecha, numerico)")
    print()


def main():
    """Función principal de la demostración."""
    print("=" * 60)
    print("    DEMOSTRACIÓN - EXTRACTOR DE FACTURAS PDF")
    print("=" * 60)

    # Crear estructura demo
    crear_facturas_demo()
    crear_plantilla_demo()

    # Ejecutar demo de exportación
    ejecutar_demo_exportacion()

    # Mostrar instrucciones
    mostrar_instrucciones()

    print("\nOK Demostración completada.")
    print("  Revisa la carpeta 'resultados/' para ver los archivos generados.")
    print("  Usa 'python main.py' para ejecutar la aplicación completa.")


if __name__ == "__main__":
    main()