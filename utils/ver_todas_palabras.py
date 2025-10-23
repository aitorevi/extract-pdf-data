"""
Script simple para ver TODAS las palabras de un PDF con sus coordenadas.
"""

import pdfplumber
import sys

def mostrar_todas_palabras(pdf_path):
    """Muestra todas las palabras del PDF con sus coordenadas."""

    with pdfplumber.open(pdf_path) as pdf:
        pagina = pdf.pages[0]

        print(f"\n{'='*80}")
        print(f"PDF: {pdf_path}")
        print(f"Dimensiones: {pagina.width} x {pagina.height} puntos")
        print(f"{'='*80}\n")

        # Extraer palabras con coordenadas
        palabras = pagina.extract_words()

        print(f"Total de palabras encontradas: {len(palabras)}\n")
        print(f"{'#':<5} {'Texto':<35} {'x0':<10} {'top':<10} {'x1':<10} {'bottom':<10}")
        print("-" * 85)

        for i, palabra in enumerate(palabras, 1):
            texto = palabra['text'][:33]  # Truncar si es muy largo
            print(f"{i:<5} {texto:<35} {palabra['x0']:<10.1f} {palabra['top']:<10.1f} {palabra['x1']:<10.1f} {palabra['bottom']:<10.1f}")

        print(f"\n{'='*80}")
        print(f"Total: {len(palabras)} palabras")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = input("Ruta del PDF: ").strip()

    try:
        mostrar_todas_palabras(pdf_path)
    except Exception as e:
        print(f"Error: {e}")
