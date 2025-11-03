"""
Script de prueba para verificar la instalación y funcionalidad del OCR.

Uso:
    python test_ocr.py
    python test_ocr.py "ruta/al/pdf.pdf"
"""

import sys
from src.utils.pdf_text_detector import diagnosticar_pdf
from src.utils.ocr_engine import OCREngine, diagnosticar_ocr


def main():
    print("=" * 60)
    print("  TEST DE OCR - Tesseract")
    print("=" * 60)
    print()

    # 1. Verificar instalación de Tesseract
    print("1. Verificando instalación de Tesseract...")
    ocr = OCREngine()

    if ocr.is_available():
        print("   ✓ Tesseract está instalado y funcional")
        try:
            import pytesseract
            version = pytesseract.get_tesseract_version()
            print(f"   Version: {version}")
            print(f"   Ruta: {ocr.tesseract_cmd or 'En PATH del sistema'}")
        except Exception as e:
            print(f"   Error obteniendo version: {e}")
    else:
        print("   ✗ Tesseract NO está instalado")
        print()
        print("   Por favor, instala Tesseract siguiendo las instrucciones en:")
        print("   .docs/INSTALACION_TESSERACT.md")
        print()
        return

    print()

    # 2. Probar con un PDF si se proporciona
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"2. Analizando PDF: {pdf_path}")
        print()

        # Diagnosticar si tiene texto
        print("   a) Detectando si tiene texto extraible...")
        diagnostico = diagnosticar_pdf(pdf_path)
        print(f"      Numero de paginas: {diagnostico['num_paginas']}")
        print(f"      Paginas con texto: {len(diagnostico['paginas_con_texto'])}")
        print(f"      Paginas sin texto: {len(diagnostico['paginas_sin_texto'])}")
        print(f"      Porcentaje con texto: {diagnostico['porcentaje_texto']:.1f}%")

        if diagnostico['paginas_sin_texto']:
            print()
            print("   b) Probando OCR en primera pagina sin texto...")
            pagina_ocr = diagnostico['paginas_sin_texto'][0]
            resultado_ocr = diagnosticar_ocr(pdf_path, pagina_ocr)

            print(f"      Palabras extraidas por OCR: {resultado_ocr['num_palabras']}")
            print(f"      Confianza promedio: {resultado_ocr['confianza_promedio']:.1f}%")
            print()
            print(f"      Primeros 500 caracteres extraidos:")
            print("      " + "-" * 50)
            if resultado_ocr['texto_extraido']:
                for linea in resultado_ocr['texto_extraido'].split('\n'):
                    print(f"      {linea}")
            else:
                print("      (sin texto)")
            print("      " + "-" * 50)
        else:
            print()
            print("   Todas las paginas tienen texto extraible")
            print("   No es necesario usar OCR para este PDF")

    else:
        print("2. Uso:")
        print("   python test_ocr.py \"ruta/al/pdf.pdf\"")
        print()
        print("   Prueba con el PDF de Galvez y Selles:")
        print("   python test_ocr.py \"documentos/por_procesar/2025-10-01_093033_FRA SEPT TIENDAS ZULIMA.pdf\"")

    print()
    print("=" * 60)
    print("  Test completado")
    print("=" * 60)


if __name__ == "__main__":
    main()
