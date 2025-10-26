"""
Crea un PDF complejo con varias facturas, algunas de 1 página y otras multipágina.

Estructura:
- Página 1: FAC-MIX-001 (1 página) - Base: 100.00
- Páginas 2-3: FAC-MIX-002 (2 páginas) - Base en pág 2: 200.00, Base en pág 3: 500.00 (total)
- Página 4: FAC-MIX-003 (1 página) - Base: 150.00
- Páginas 5-7: FAC-MIX-004 (3 páginas) - Base acumulada, pág 7: 900.00 (total)
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def crear_pdf_mixto_complejo():
    """Crea un PDF con facturas mixtas (1 página y multipágina)."""
    output_path = "facturas/test_mixto_complejo.pdf"
    os.makedirs("facturas", exist_ok=True)

    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    cif = "B12345678"
    proveedor = "Test Provider S.L."

    # ==================== PÁGINA 1: FAC-MIX-001 (1 página) ====================
    c.drawString(117, height - 260, cif)
    c.drawString(146, height - 244, proveedor)
    c.drawString(90, height - 99, "FAC-MIX-001")
    c.drawString(162, height - 274, "15/01/2025")
    c.drawString(146, height - 289, "15/02/2025")
    c.drawString(91, height - 198, "100.00")

    c.setFont("Helvetica", 10)
    c.drawString(200, height - 400, "Factura simple de 1 página")
    c.drawString(3.5*72, 0.6*72, "Página 1")
    c.showPage()

    # ==================== PÁGINA 2: FAC-MIX-002 (página 1 de 2) ====================
    c.drawString(117, height - 260, cif)
    c.drawString(146, height - 244, proveedor)
    c.drawString(90, height - 99, "FAC-MIX-002")
    c.drawString(162, height - 274, "16/01/2025")
    c.drawString(146, height - 289, "16/02/2025")
    c.drawString(91, height - 198, "200.00")  # Parcial

    c.setFont("Helvetica", 10)
    c.drawString(200, height - 400, "FAC-MIX-002 - Página 1 de 2 (parcial)")
    c.drawString(3.5*72, 0.6*72, "Página 2 - Continúa...")
    c.showPage()

    # ==================== PÁGINA 3: FAC-MIX-002 (página 2 de 2 - ÚLTIMA) ====================
    c.drawString(117, height - 260, cif)
    c.drawString(146, height - 244, proveedor)
    c.drawString(90, height - 99, "FAC-MIX-002")
    c.drawString(162, height - 274, "16/01/2025")
    c.drawString(146, height - 289, "16/02/2025")
    c.drawString(91, height - 198, "500.00")  # TOTAL

    c.setFont("Helvetica", 10)
    c.drawString(200, height - 400, "FAC-MIX-002 - Página 2 de 2 (TOTAL)")
    c.drawString(3.5*72, 0.6*72, "Página 3 - FIN FAC-MIX-002")
    c.showPage()

    # ==================== PÁGINA 4: FAC-MIX-003 (1 página) ====================
    c.drawString(117, height - 260, cif)
    c.drawString(146, height - 244, proveedor)
    c.drawString(90, height - 99, "FAC-MIX-003")
    c.drawString(162, height - 274, "17/01/2025")
    c.drawString(146, height - 289, "17/02/2025")
    c.drawString(91, height - 198, "150.00")

    c.setFont("Helvetica", 10)
    c.drawString(200, height - 400, "Factura simple de 1 página")
    c.drawString(3.5*72, 0.6*72, "Página 4")
    c.showPage()

    # ==================== PÁGINA 5: FAC-MIX-004 (página 1 de 3) ====================
    c.drawString(117, height - 260, cif)
    c.drawString(146, height - 244, proveedor)
    c.drawString(90, height - 99, "FAC-MIX-004")
    c.drawString(162, height - 274, "18/01/2025")
    c.drawString(146, height - 289, "18/02/2025")
    c.drawString(91, height - 198, "300.00")  # Parcial

    c.setFont("Helvetica", 10)
    c.drawString(200, height - 400, "FAC-MIX-004 - Página 1 de 3")
    c.drawString(3.5*72, 0.6*72, "Página 5 - Continúa...")
    c.showPage()

    # ==================== PÁGINA 6: FAC-MIX-004 (página 2 de 3) ====================
    c.drawString(117, height - 260, cif)
    c.drawString(146, height - 244, proveedor)
    c.drawString(90, height - 99, "FAC-MIX-004")
    c.drawString(162, height - 274, "18/01/2025")
    c.drawString(146, height - 289, "18/02/2025")
    c.drawString(91, height - 198, "600.00")  # Parcial acumulado

    c.setFont("Helvetica", 10)
    c.drawString(200, height - 400, "FAC-MIX-004 - Página 2 de 3")
    c.drawString(3.5*72, 0.6*72, "Página 6 - Continúa...")
    c.showPage()

    # ==================== PÁGINA 7: FAC-MIX-004 (página 3 de 3 - ÚLTIMA) ====================
    c.drawString(117, height - 260, cif)
    c.drawString(146, height - 244, proveedor)
    c.drawString(90, height - 99, "FAC-MIX-004")
    c.drawString(162, height - 274, "18/01/2025")
    c.drawString(146, height - 289, "18/02/2025")
    c.drawString(91, height - 198, "900.00")  # TOTAL

    c.setFont("Helvetica", 10)
    c.drawString(200, height - 400, "FAC-MIX-004 - Página 3 de 3 (TOTAL)")
    c.drawString(3.5*72, 0.6*72, "Página 7 - FIN FAC-MIX-004")
    c.showPage()

    c.save()

    print(f"✓ PDF creado: {output_path}")
    print(f"\n=== ESTRUCTURA DEL PDF ===")
    print(f"Total páginas: 7")
    print(f"\nFacturas esperadas:")
    print(f"  1. FAC-MIX-001 (página 1) - Base: 100.00")
    print(f"  2. FAC-MIX-002 (páginas 2-3) - Base: 500.00 (de página 3)")
    print(f"  3. FAC-MIX-003 (página 4) - Base: 150.00")
    print(f"  4. FAC-MIX-004 (páginas 5-7) - Base: 900.00 (de página 7)")

if __name__ == "__main__":
    crear_pdf_mixto_complejo()
