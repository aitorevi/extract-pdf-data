"""
Script para probar la funcionalidad de extracción multipágina.
Procesa los PDFs de prueba generados y muestra los resultados.
"""

from src.pdf_extractor import PDFExtractor
import os


def probar_pdf(extractor, pdf_filename, descripcion):
    """
    Procesa un PDF y muestra los resultados.

    Args:
        extractor: Instancia de PDFExtractor
        pdf_filename: Nombre del archivo PDF
        descripcion: Descripción del caso de prueba
    """
    print("\n" + "="*70)
    print(f"  {descripcion}")
    print("="*70)

    pdf_path = os.path.join("facturas", pdf_filename)

    if not os.path.exists(pdf_path):
        print(f"❌ Archivo no encontrado: {pdf_path}")
        print("   Ejecuta primero: python crear_pdf_prueba.py")
        return

    print(f"\n📄 Procesando: {pdf_filename}")

    try:
        # Extraer datos usando el nuevo método multipágina
        facturas = extractor.extraer_datos_factura_multipagina(pdf_path, 'test_provider')

        print(f"\n✅ Extraídas {len(facturas)} factura(s)\n")

        # Mostrar resultados
        for i, factura in enumerate(facturas, 1):
            num_factura = factura.get('NumFactura', 'N/A')
            base = factura.get('Base', 'N/A')
            pagina = factura.get('_Pagina', 'N/A')
            total_paginas = factura.get('_Total_Paginas', 'N/A')
            error = factura.get('_Error', None)

            print(f"--- Factura {i} ---")
            print(f"  NumFactura: {num_factura}")
            print(f"  Base: {base}")
            print(f"  Extraída de página: {pagina}")
            print(f"  Total páginas de esta factura: {total_paginas}")

            if error:
                print(f"  ⚠️  ERROR: {error}")

            # Mostrar todos los campos estándar
            campos_estandar = ['CIF', 'FechaFactura', 'Trimestre', 'Año', 'FechaVto', 'FechaPago', 'ComPaypal']
            for campo in campos_estandar:
                valor = factura.get(campo, '')
                if valor:
                    print(f"  {campo}: {valor}")

            print()

    except Exception as e:
        print(f"❌ Error procesando PDF: {e}")


def main():
    print("\n" + "="*70)
    print("  🧪 PRUEBA DE EXTRACCIÓN MULTIPÁGINA")
    print("="*70)

    # Verificar que existen los archivos de prueba
    if not os.path.exists("facturas") or not os.path.exists("plantillas/test_provider.json"):
        print("\n⚠️  No se encontraron los archivos de prueba.")
        print("   Ejecuta primero: python crear_pdf_prueba.py\n")
        return

    # Crear extractor
    extractor = PDFExtractor(trimestre="Q1", año="2025")

    # Cargar plantillas
    print("\n📋 Cargando plantillas...")
    if not extractor.cargar_plantillas():
        print("❌ No se pudieron cargar las plantillas")
        return

    # Caso 1: Una factura en una página
    probar_pdf(
        extractor,
        "test_1factura_1pagina.pdf",
        "CASO 1: Una factura en una página"
    )

    # Caso 2: Una factura en tres páginas
    probar_pdf(
        extractor,
        "test_1factura_3paginas.pdf",
        "CASO 2: Una factura en tres páginas"
    )

    # Caso 3: Tres facturas individuales
    probar_pdf(
        extractor,
        "test_3facturas_1pagina.pdf",
        "CASO 3: Tres facturas, una página cada una"
    )

    # Caso 4: Caso mixto
    probar_pdf(
        extractor,
        "test_mixto.pdf",
        "CASO 4: Múltiples facturas con diferentes números de páginas"
    )

    # Caso 5: PDF con error
    probar_pdf(
        extractor,
        "test_error_sin_numfactura.pdf",
        "CASO 5: PDF con página sin NumFactura (ERROR esperado)"
    )

    print("\n" + "="*70)
    print("  ✅ PRUEBA COMPLETADA")
    print("="*70)
    print("\n💡 Observaciones:")
    print("   - Las facturas multipágina se extraen de su ÚLTIMA página")
    print("   - Cada factura se identifica por su NumFactura único")
    print("   - Las páginas sin NumFactura se marcan como ERROR")
    print("   - El método mantiene compatibilidad con PDFs de 1 página")
    print()


if __name__ == "__main__":
    main()
