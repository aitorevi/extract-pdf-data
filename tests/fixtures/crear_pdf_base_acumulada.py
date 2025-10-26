"""
Crea un PDF de prueba con una factura de 3 páginas donde la Base se acumula.
- Página 1: Base = 250.00 (parcial página 1)
- Página 2: Base = 650.00 (250 + 400 de página 2)
- Página 3: Base = 1125.50 (250 + 400 + 475.50 de página 3) <- TOTAL CORRECTO
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os

def crear_pdf_base_acumulada():
    """Crea un PDF con base acumulada en 3 páginas."""

    # Configuración
    output_path = "facturas/test_base_acumulada.pdf"
    os.makedirs("facturas", exist_ok=True)

    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Datos de la factura
    num_factura = "FAC-BASE-001"
    fecha_factura = "15/01/2025"
    fecha_vto = "15/02/2025"
    cif = "B12345678"
    proveedor = "Test Provider S.L."

    # Valores parciales de cada página
    parcial_pag1 = 250.00
    parcial_pag2 = 400.00
    parcial_pag3 = 475.50

    # Bases acumuladas
    base_pag1 = parcial_pag1
    base_pag2 = parcial_pag1 + parcial_pag2
    base_pag3 = parcial_pag1 + parcial_pag2 + parcial_pag3  # Total correcto

    # ==================== PÁGINA 1 ====================
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "FACTURA")

    c.setFont("Helvetica", 10)
    # CIF en coordenadas que la plantilla reconoce [117.04, 246.4, 179.52, 259.6]
    c.drawString(117, height - 260, cif)
    # Proveedor en coordenadas que la plantilla reconoce [146.08, 229.68, 224.4, 243.76]
    c.drawString(146, height - 244, proveedor)

    # Campos de la plantilla
    # NumFactura en coordenadas [88.88, 80.08, 159.28, 98.56]
    c.drawString(90, height - 99, num_factura)
    # FechaFactura en coordenadas [161.92, 261.36, 216.48, 273.68]
    c.drawString(162, height - 274, fecha_factura)
    # FechaVto en coordenadas [145.2, 277.2, 199.76, 288.64]
    c.drawString(146, height - 289, fecha_vto)

    # Base acumulada página 1
    c.setFont("Helvetica-Bold", 11)
    # Base en coordenadas [90.64, 176.88, 146.08, 198]
    c.drawString(91, height - 198, f"{base_pag1:.2f}")

    # Contenido de la página 1 (más abajo para no interferir con coordenadas)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, height - 4.5*inch, "CONCEPTOS - PÁGINA 1")

    c.setFont("Helvetica", 10)
    c.drawString(1*inch, height - 4.8*inch, "Artículo A - Cantidad: 5 - Precio: 50.00€")
    c.drawString(1*inch, height - 5.0*inch, "Parcial Página 1: 250.00€")

    # Indicador de continuación
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(3*inch, 0.8*inch, "Continúa en página siguiente...")
    c.drawString(3.5*inch, 0.6*inch, "Página 1 de 3")

    c.showPage()

    # ==================== PÁGINA 2 ====================
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "FACTURA (continuación)")

    c.setFont("Helvetica", 10)
    # CIF en coordenadas que la plantilla reconoce
    c.drawString(117, height - 260, cif)
    # Proveedor en coordenadas que la plantilla reconoce
    c.drawString(146, height - 244, proveedor)

    # Campos de la plantilla
    # NumFactura en coordenadas [88.88, 80.08, 159.28, 98.56]
    c.drawString(90, height - 99, num_factura)
    # FechaFactura en coordenadas [161.92, 261.36, 216.48, 273.68]
    c.drawString(162, height - 274, fecha_factura)
    # FechaVto en coordenadas [145.2, 277.2, 199.76, 288.64]
    c.drawString(146, height - 289, fecha_vto)

    # Base acumulada página 2
    c.setFont("Helvetica-Bold", 11)
    # Base en coordenadas [90.64, 176.88, 146.08, 198]
    c.drawString(91, height - 198, f"{base_pag2:.2f}")

    # Contenido de la página 2 (más abajo para no interferir con coordenadas)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, height - 4.5*inch, "CONCEPTOS - PÁGINA 2")

    c.setFont("Helvetica", 10)
    c.drawString(1*inch, height - 4.8*inch, "Artículo B - Cantidad: 8 - Precio: 50.00€")
    c.drawString(1*inch, height - 5.0*inch, "Parcial Página 2: 400.00€")

    # Indicador de continuación
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(3*inch, 0.8*inch, "Continúa en página siguiente...")
    c.drawString(3.5*inch, 0.6*inch, "Página 2 de 3")

    c.showPage()

    # ==================== PÁGINA 3 (FINAL) ====================
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "FACTURA (final)")

    c.setFont("Helvetica", 10)
    # CIF en coordenadas que la plantilla reconoce
    c.drawString(117, height - 260, cif)
    # Proveedor en coordenadas que la plantilla reconoce
    c.drawString(146, height - 244, proveedor)

    # Campos de la plantilla
    # NumFactura en coordenadas [88.88, 80.08, 159.28, 98.56]
    c.drawString(90, height - 99, num_factura)
    # FechaFactura en coordenadas [161.92, 261.36, 216.48, 273.68]
    c.drawString(162, height - 274, fecha_factura)
    # FechaVto en coordenadas [145.2, 277.2, 199.76, 288.64]
    c.drawString(146, height - 289, fecha_vto)

    # Base TOTAL (acumulada de las 3 páginas)
    c.setFont("Helvetica-Bold", 14)
    # Base en coordenadas [90.64, 176.88, 146.08, 198]
    c.drawString(91, height - 198, f"{base_pag3:.2f}")

    # Contenido de la página 3 (más abajo para no interferir con coordenadas)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, height - 4.5*inch, "CONCEPTOS - PÁGINA 3")

    c.setFont("Helvetica", 10)
    c.drawString(1*inch, height - 4.8*inch, "Artículo C - Cantidad: 9.51 - Precio: 50.00€")
    c.drawString(1*inch, height - 5.0*inch, "Parcial Página 3: 475.50€")

    c.setFont("Helvetica", 10)
    c.drawString(1*inch, height - 5.5*inch, "Resumen:")
    c.drawString(1*inch, height - 5.7*inch, f"  - Página 1: {parcial_pag1:.2f}€")
    c.drawString(1*inch, height - 5.9*inch, f"  - Página 2: {parcial_pag2:.2f}€")
    c.drawString(1*inch, height - 6.1*inch, f"  - Página 3: {parcial_pag3:.2f}€")
    c.drawString(1*inch, height - 6.3*inch, f"  ────────────────")
    c.drawString(1*inch, height - 6.5*inch, f"  TOTAL: {base_pag3:.2f}€")

    # Indicador de página final
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(3.5*inch, 0.6*inch, "Página 3 de 3 - FIN")

    c.save()

    print(f"✓ PDF creado: {output_path}")
    print(f"\nValores de Base por página:")
    print(f"  Página 1: {base_pag1:.2f}€ (parcial)")
    print(f"  Página 2: {base_pag2:.2f}€ (acumulado parcial)")
    print(f"  Página 3: {base_pag3:.2f}€ (TOTAL CORRECTO) ✓")
    print(f"\nEl sistema debería extraer: {base_pag3:.2f}€")

if __name__ == "__main__":
    crear_pdf_base_acumulada()
