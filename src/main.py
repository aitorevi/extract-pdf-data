"""
Script principal para la aplicación de extracción de datos de facturas PDF.
Proporciona una interfaz de línea de comandos para ejecutar todo el workflow.
"""

import os
import sys
import argparse
from typing import Optional, List
from src.pdf_extractor import PDFExtractor
from src.excel_exporter import ExcelExporter


class FacturaExtractorApp:
    def __init__(self):
        """Inicializa la aplicación principal."""
        self.pdf_extractor = None
        self.exporter = None

    def mostrar_banner(self):
        """Muestra el banner de la aplicación."""
        print("=" * 60)
        print("    EXTRACTOR DE DATOS DE FACTURAS PDF")
        print("    Versión 1.0 - Aplicación Local")
        print("=" * 60)
        print()

    def verificar_estructura_proyecto(self) -> bool:
        """
        Verifica que la estructura del proyecto esté correcta.

        Returns:
            bool: True si la estructura es correcta
        """
        directorios_requeridos = ['facturas', 'plantillas', 'resultados']
        problemas = []

        for directorio in directorios_requeridos:
            if not os.path.exists(directorio):
                try:
                    os.makedirs(directorio)
                    print(f"OK Directorio creado: {directorio}/")
                except Exception as e:
                    problemas.append(f"No se pudo crear {directorio}/: {e}")

        # Verificar plantillas
        if os.path.exists('plantillas'):
            plantillas = [f for f in os.listdir('plantillas') if f.endswith('.json')]
            if not plantillas:
                problemas.append("No se encontraron plantillas JSON en plantillas/")
        else:
            problemas.append("Directorio plantillas/ no existe")

        # Verificar facturas
        if os.path.exists('facturas'):
            facturas = [f for f in os.listdir('facturas') if f.lower().endswith('.pdf')]
            if not facturas:
                print("WARN No se encontraron archivos PDF en facturas/")
        else:
            problemas.append("Directorio facturas/ no existe")

        if problemas:
            print("ERROR Problemas encontrados:")
            for problema in problemas:
                print(f"   - {problema}")
            return False

        print("OK Estructura del proyecto verificada correctamente")
        return True

    def modo_coordenadas(self):
        """Ejecuta el modo de extracción de coordenadas."""
        print("\n=== MODO: EDITOR DE PLANTILLAS ===")
        print("Este modo te permite crear y editar plantillas de forma visual")
        print()

        try:
            import subprocess
            subprocess.run([sys.executable, "src/editor_plantillas.py"])
        except Exception as e:
            print(f"Error ejecutando editor de plantillas: {e}")

    def modo_procesamiento(self, auto_export: bool = True, formato_salida: str = "todos"):
        """
        Ejecuta el modo de procesamiento completo.

        Args:
            auto_export (bool): Si exportar automáticamente después de procesar
            formato_salida (str): Formato de salida (excel, csv, json, todos)
        """
        print("\n=== MODO: PROCESAMIENTO DE FACTURAS ===")

        # Solicitar información fiscal al usuario
        print("\nDatos fiscales para la exportación:")
        trimestre_input = input("Ingresa el trimestre (1, 2, 3 o 4): ").strip()
        año = input("Ingresa el año (ej: 2025): ").strip()

        # Validar entrada de trimestre (solo acepta 1, 2, 3 o 4)
        if trimestre_input in ['1', '2', '3', '4']:
            trimestre = f"{trimestre_input}T"
            print(f"✓ Trimestre: {trimestre}")
        else:
            print(f"ERROR: Trimestre '{trimestre_input}' no válido. Debe ser 1, 2, 3 o 4.")
            return False

        # Validar entrada de año
        if not año.isdigit() or len(año) != 4:
            print(f"ERROR: Año '{año}' no válido. Debe ser un año de 4 dígitos (ej: 2025).")
            return False

        print(f"✓ Año: {año}")

        # Inicializar extractor con datos fiscales
        self.pdf_extractor = PDFExtractor(trimestre=trimestre, año=año)

        # Cargar plantillas
        print("\nCargando plantillas...")
        if not self.pdf_extractor.cargar_plantillas():
            print("ERROR: No se pudieron cargar plantillas.")
            print("   Usa el modo 'coordenadas' para crear plantillas primero.")
            return False

        # Procesar facturas
        print("\nProcesando facturas...")
        resultados = self.pdf_extractor.procesar_directorio_facturas()

        if not resultados:
            print("ERROR No se procesaron facturas. Verifica que haya archivos PDF en facturas/")
            return False

        # Mostrar estadísticas
        stats = self.pdf_extractor.obtener_estadisticas()
        self.mostrar_estadisticas(stats)

        # Mostrar errores si existen
        if self.pdf_extractor.errores:
            print(f"\n⚠️  ERRORES DE EXTRACCIÓN: {len(self.pdf_extractor.errores)}")
            print("   (Ver archivo ERRORES.xlsx para detalles)")

        # Exportar si está habilitado
        if auto_export:
            # Pasar también los errores para generar el Excel de debug
            return self.exportar_resultados(resultados, self.pdf_extractor.errores, formato_salida)

        return True

    def mostrar_estadisticas(self, stats: dict):
        """Muestra las estadísticas del procesamiento."""
        print(f"\n=== RESUMEN DEL PROCESAMIENTO ===")
        print(f"Total facturas: {stats['total_facturas']}")
        print(f"Procesadas exitosamente: {stats['facturas_exitosas']} ({stats['tasa_exito']}%)")
        print(f"Duplicadas (excluidas): {stats['facturas_duplicadas']}")
        print(f"Con errores: {stats['facturas_con_error']}")
        print(f"Plantillas usadas: {stats['plantillas_disponibles']}")

        if stats['proveedores']:
            print(f"\n=== DETALLE POR PROVEEDOR ===")
            for proveedor, data in stats['proveedores'].items():
                print(f"{proveedor}: {data['exitosos']}/{data['total']} exitosas")

    def exportar_resultados(self, resultados: List[dict], errores: List[dict] = None, formato: str = "todos") -> bool:
        """
        Exporta los resultados en el formato especificado.

        Args:
            resultados (List[dict]): Datos a exportar
            errores (List[dict]): Errores de extracción
            formato (str): Formato de exportación

        Returns:
            bool: True si la exportación fue exitosa
        """
        print(f"\n=== EXPORTANDO RESULTADOS ===")

        try:
            self.exporter = ExcelExporter(resultados, errores or [])

            archivos_generados = {}

            if formato == "excel" or formato == "todos":
                # Excel principal: solo las 9 columnas requeridas
                archivos_generados['excel'] = self.exporter.exportar_excel_formateado()
                # Excel completo: con todos los metadatos para debugging
                archivos_generados['excel_debug'] = self.exporter.exportar_excel_completo()

            if formato == "csv" or formato == "todos":
                archivos_generados['csv'] = self.exporter.exportar_csv()

            if formato == "json" or formato == "todos":
                archivos_generados['json'] = self.exporter.exportar_json()

            if formato == "todos":
                archivos_generados['excel_basico'] = self.exporter.exportar_excel_basico()

            print(f"\nOK Exportación completada:")
            for tipo, ruta in archivos_generados.items():
                print(f"   {tipo}: {ruta}")

            return True

        except Exception as e:
            print(f"ERROR durante la exportación: {e}")
            return False

    def modo_ayuda(self):
        """Muestra la ayuda completa de la aplicación."""
        print("\n=== GUÍA DE USO ===")
        print()
        print("1. PREPARAR EL ENTORNO:")
        print("   - Instala las dependencias: pip install -r requirements.txt")
        print("   - Coloca archivos PDF en la carpeta 'facturas/'")
        print()
        print("2. CREAR PLANTILLAS (primera vez):")
        print("   python main.py coordenadas")
        print("   - Convierte PDF a imagen o usa imagen existente")
        print("   - Selecciona campos con el ratón")
        print("   - Define nombre y tipo de cada campo")
        print("   - Guarda la plantilla JSON")
        print()
        print("3. PROCESAR FACTURAS:")
        print("   python main.py procesar")
        print("   - Extrae datos de todos los PDFs")
        print("   - Genera archivos Excel, CSV y JSON")
        print()
        print("4. OPCIONES AVANZADAS:")
        print("   python main.py procesar --formato excel  # Solo Excel")
        print("   python main.py procesar --formato csv    # Solo CSV")
        print("   python main.py procesar --no-auto-export # Sin exportar")
        print()
        print("5. ESTRUCTURA DE ARCHIVOS:")
        print("   facturas/       - PDFs a procesar")
        print("   plantillas/     - Plantillas JSON por proveedor")
        print("   resultados/     - Archivos de salida")
        print("   imagenes_muestra/ - Imágenes de referencia")
        print()

    def ejecutar_cli(self):
        """Ejecuta la interfaz de línea de comandos."""
        parser = argparse.ArgumentParser(
            description="Extractor de datos de facturas PDF",
            epilog="Usa 'python main.py ayuda' para más información"
        )

        subparsers = parser.add_subparsers(dest='comando', help='Comandos disponibles')

        # Comando coordenadas
        parser_coord = subparsers.add_parser('coordenadas', help='Extraer coordenadas de campos')

        # Comando procesar
        parser_proc = subparsers.add_parser('procesar', help='Procesar facturas')
        parser_proc.add_argument('--formato', choices=['excel', 'csv', 'json', 'todos'],
                                default='todos', help='Formato de salida')
        parser_proc.add_argument('--no-auto-export', action='store_true',
                                help='No exportar automáticamente')

        # Comando ayuda
        parser_help = subparsers.add_parser('ayuda', help='Mostrar guía de uso')

        # Comando verificar
        parser_verify = subparsers.add_parser('verificar', help='Verificar estructura del proyecto')

        args = parser.parse_args()

        # Mostrar banner
        self.mostrar_banner()

        # Si no hay comando, mostrar ayuda
        if not args.comando:
            parser.print_help()
            return

        # Verificar estructura (excepto para ayuda)
        if args.comando != 'ayuda':
            if not self.verificar_estructura_proyecto():
                print("\nERROR Corrige los problemas antes de continuar.")
                return

        # Ejecutar comando
        if args.comando == 'coordenadas':
            self.modo_coordenadas()

        elif args.comando == 'procesar':
            auto_export = not args.no_auto_export
            self.modo_procesamiento(auto_export, args.formato)

        elif args.comando == 'ayuda':
            self.modo_ayuda()

        elif args.comando == 'verificar':
            print("OK Verificación completada.")

    def ejecutar_interactivo(self):
        """Ejecuta la interfaz interactiva."""
        self.mostrar_banner()

        # Verificar estructura
        if not self.verificar_estructura_proyecto():
            print("\nERROR Corrige los problemas antes de continuar.")
            return

        while True:
            print("\n=== MENÚ PRINCIPAL ===")
            print("1. Extraer coordenadas de campos")
            print("2. Procesar facturas")
            print("3. Mostrar ayuda")
            print("4. Verificar estructura")
            print("5. Salir")
            print()

            opcion = input("Selecciona una opción (1-5): ").strip()

            if opcion == "1":
                self.modo_coordenadas()

            elif opcion == "2":
                print("\nFormatos de salida:")
                print("1. Todos (Excel, CSV, JSON)")
                print("2. Solo Excel")
                print("3. Solo CSV")
                print("4. Solo JSON")

                formato_opcion = input("Selecciona formato (1-4): ").strip()
                formato_map = {"1": "todos", "2": "excel", "3": "csv", "4": "json"}
                formato = formato_map.get(formato_opcion, "todos")

                self.modo_procesamiento(auto_export=True, formato_salida=formato)

            elif opcion == "3":
                self.modo_ayuda()

            elif opcion == "4":
                self.verificar_estructura_proyecto()

            elif opcion == "5":
                print("Hasta luego!")
                break

            else:
                print("Opción no válida. Intenta de nuevo.")


def main():
    """Función principal."""
    app = FacturaExtractorApp()

    # Si hay argumentos de línea de comandos, usar CLI
    if len(sys.argv) > 1:
        app.ejecutar_cli()
    else:
        # Sin argumentos, usar modo interactivo
        app.ejecutar_interactivo()


if __name__ == "__main__":
    main()