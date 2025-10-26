"""
Script para crear PDFs de prueba para testing de funcionalidad multipágina.
Genera PDFs con diferentes escenarios:
1. Una factura en una página
2. Una factura en tres páginas
3. Tres facturas en un PDF (páginas individuales)
4. Caso mixto: múltiples facturas, algunas con múltiples páginas
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os


def crear_pagina_factura(c, num_factura, pagina_num, total_paginas, base=None):
    """
    Dibuja una página de factura con datos en posiciones específicas.

    Args:
        c: Canvas de reportlab
        num_factura: Número de factura (ej: "FAC-001")
        pagina_num: Número de página actual (1-indexed)
        total_paginas: Total de páginas de esta factura
        base: Base imponible (solo en última página)
    """
    # Coordenadas estándar para campos (compatibles con plantilla)
    # NumFactura: x=100, y=700, width=100, height=20
    # Base: x=100, y=600, width=100, height=20

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "FACTURA DE PRUEBA")

    # Número de factura (siempre presente en todas las páginas)
    c.setFont("Helvetica", 10)
    c.drawString(100, 720, "Número de Factura:")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 700, num_factura)

    # Indicador de página
    c.setFont("Helvetica", 10)
    c.drawString(100, 670, f"Página {pagina_num} de {total_paginas}")

    # Base imponible (solo en última página)
    if base is not None:
        c.setFont("Helvetica", 10)
        c.drawString(100, 620, "Base Imponible:")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, 600, base)
    else:
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(100, 600, "(continuación...)")

    # Datos adicionales de ejemplo
    c.setFont("Helvetica", 9)
    c.drawString(100, 550, "Proveedor: Test Provider S.L.")
    c.drawString(100, 535, "CIF: B12345678")
    c.drawString(100, 520, "Fecha Factura: 15/01/2025")
    c.drawString(100, 505, "Fecha Vto: 15/02/2025")

    # Contenido de relleno para simular factura real
    y_pos = 450
    c.setFont("Helvetica", 8)
    c.drawString(100, y_pos, "--- Detalle de servicios ---")

    for i in range(1, 10):
        y_pos -= 15
        c.drawString(110, y_pos, f"Servicio {i + (pagina_num-1)*10}: Descripción del servicio...")
        c.drawString(400, y_pos, "100.00 EUR")

    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(100, 50, f"Generado automáticamente para testing - {num_factura}")


def crear_pdf_una_factura_una_pagina():
    """Caso 1: Una factura en una página."""
    filename = "facturas/test_1factura_1pagina.pdf"
    os.makedirs("facturas", exist_ok=True)

    c = canvas.Canvas(filename, pagesize=letter)
    crear_pagina_factura(c, "FAC-001", 1, 1, base="500.00")
    c.save()

    print(f"✅ Creado: {filename}")
    print("   - 1 factura (FAC-001)")
    print("   - 1 página")
    print("   - Base: 500.00 en página 1")


def crear_pdf_una_factura_tres_paginas():
    """Caso 2: Una factura en tres páginas."""
    filename = "facturas/test_1factura_3paginas.pdf"
    os.makedirs("facturas", exist_ok=True)

    c = canvas.Canvas(filename, pagesize=letter)

    # Página 1 y 2: sin base
    crear_pagina_factura(c, "FAC-002", 1, 3, base=None)
    c.showPage()

    crear_pagina_factura(c, "FAC-002", 2, 3, base=None)
    c.showPage()

    # Página 3: con base (última página)
    crear_pagina_factura(c, "FAC-002", 3, 3, base="1250.75")

    c.save()

    print(f"✅ Creado: {filename}")
    print("   - 1 factura (FAC-002)")
    print("   - 3 páginas")
    print("   - Base: 1250.75 en página 3 (última)")


def crear_pdf_tres_facturas_individuales():
    """Caso 3: Tres facturas diferentes, una página cada una."""
    filename = "facturas/test_3facturas_1pagina.pdf"
    os.makedirs("facturas", exist_ok=True)

    c = canvas.Canvas(filename, pagesize=letter)

    # Factura 1
    crear_pagina_factura(c, "FAC-003", 1, 1, base="300.00")
    c.showPage()

    # Factura 2
    crear_pagina_factura(c, "FAC-004", 1, 1, base="450.50")
    c.showPage()

    # Factura 3
    crear_pagina_factura(c, "FAC-005", 1, 1, base="600.25")

    c.save()

    print(f"✅ Creado: {filename}")
    print("   - 3 facturas (FAC-003, FAC-004, FAC-005)")
    print("   - 1 página cada una")
    print("   - Bases: 300.00, 450.50, 600.25")


def crear_pdf_caso_mixto():
    """Caso 4: Múltiples facturas con diferentes números de páginas."""
    filename = "facturas/test_mixto.pdf"
    os.makedirs("facturas", exist_ok=True)

    c = canvas.Canvas(filename, pagesize=letter)

    # Factura FAC-006: 2 páginas
    crear_pagina_factura(c, "FAC-006", 1, 2, base=None)
    c.showPage()
    crear_pagina_factura(c, "FAC-006", 2, 2, base="800.00")
    c.showPage()

    # Factura FAC-007: 1 página
    crear_pagina_factura(c, "FAC-007", 1, 1, base="150.00")
    c.showPage()

    # Factura FAC-008: 3 páginas
    crear_pagina_factura(c, "FAC-008", 1, 3, base=None)
    c.showPage()
    crear_pagina_factura(c, "FAC-008", 2, 3, base=None)
    c.showPage()
    crear_pagina_factura(c, "FAC-008", 3, 3, base="2500.99")

    c.save()

    print(f"✅ Creado: {filename}")
    print("   - 3 facturas:")
    print("     * FAC-006: 2 páginas, Base: 800.00 en página 2")
    print("     * FAC-007: 1 página, Base: 150.00 en página 1")
    print("     * FAC-008: 3 páginas, Base: 2500.99 en página 3")


def crear_pdf_con_error():
    """Caso 5: PDF con una página sin NumFactura (para testing de errores)."""
    filename = "facturas/test_error_sin_numfactura.pdf"
    os.makedirs("facturas", exist_ok=True)

    c = canvas.Canvas(filename, pagesize=letter)

    # Página 1: Factura normal
    crear_pagina_factura(c, "FAC-009", 1, 1, base="100.00")
    c.showPage()

    # Página 2: Sin número de factura (ERROR)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "PÁGINA SIN NÚMERO DE FACTURA")
    c.setFont("Helvetica", 10)
    c.drawString(100, 700, "Esta página no tiene NumFactura en la posición esperada")
    c.drawString(100, 680, "Debería generar un ERROR")
    c.showPage()

    # Página 3: Otra factura normal
    crear_pagina_factura(c, "FAC-010", 1, 1, base="200.00")

    c.save()

    print(f"✅ Creado: {filename}")
    print("   - 3 páginas:")
    print("     * Página 1: FAC-009 (OK)")
    print("     * Página 2: Sin NumFactura (ERROR)")
    print("     * Página 3: FAC-010 (OK)")


def crear_plantilla_test():
    """Crea una plantilla JSON compatible con los PDFs de prueba."""
    import json

    plantilla = {
        "nombre_proveedor": "Test Provider S.L.",
        "cif_proveedor": "B12345678",
        "campos_identificacion": {
            "cif": [50, 535, 150, 550],
            "nombre": [50, 550, 250, 565]
        },
        "campos": [
            {
                "nombre": "NumFactura",
                "coordenadas": [100, 700, 200, 720],
                "tipo": "texto"
            },
            {
                "nombre": "Base",
                "coordenadas": [100, 600, 200, 620],
                "tipo": "numerico"
            },
            {
                "nombre": "FechaFactura",
                "coordenadas": [100, 520, 250, 535],
                "tipo": "fecha"
            },
            {
                "nombre": "FechaVto",
                "coordenadas": [100, 505, 250, 520],
                "tipo": "fecha"
            }
        ]
    }

    os.makedirs("plantillas", exist_ok=True)
    filename = "plantillas/test_provider.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(plantilla, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Creada plantilla: {filename}")
    print("   - Proveedor: Test Provider S.L.")
    print("   - CIF: B12345678")
    print("   - Campos: NumFactura, Base, FechaFactura, FechaVto")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  GENERADOR DE PDFs DE PRUEBA - Soporte Multipágina")
    print("="*60 + "\n")

    # Instalar reportlab si no está disponible
    try:
        import reportlab
    except ImportError:
        print("⚠️  Instalando reportlab...")
        import subprocess
        subprocess.check_call(["pip", "install", "reportlab"])
        print("✅ reportlab instalado\n")

    # Crear PDFs de prueba
    crear_pdf_una_factura_una_pagina()
    print()

    crear_pdf_una_factura_tres_paginas()
    print()

    crear_pdf_tres_facturas_individuales()
    print()

    crear_pdf_caso_mixto()
    print()

    crear_pdf_con_error()
    print()

    # Crear plantilla compatible
    crear_plantilla_test()

    print("\n" + "="*60)
    print("  ✅ GENERACIÓN COMPLETADA")
    print("="*60)
    print("\nArchivos creados:")
    print("  📄 facturas/test_1factura_1pagina.pdf")
    print("  📄 facturas/test_1factura_3paginas.pdf")
    print("  📄 facturas/test_3facturas_1pagina.pdf")
    print("  📄 facturas/test_mixto.pdf")
    print("  📄 facturas/test_error_sin_numfactura.pdf")
    print("  📋 plantillas/test_provider.json")
    print("\n💡 Para probar, ejecuta:")
    print("   python test_extraccion_multipagina.py")
    print()
