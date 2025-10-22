"""
Herramienta alternativa para extraer coordenadas usando pdfplumber.
Más estable y fácil de usar que OpenCV.
"""

import pdfplumber
import json
import os
from pathlib import Path


def extraer_coordenadas_manual():
    """
    Método manual: el usuario proporciona las coordenadas viendo el PDF.
    """
    print("\n=== EXTRACTOR DE COORDENADAS MANUAL ===")
    print("\nPara obtener coordenadas, puedes:")
    print("1. Abrir el PDF en un visor (Preview, Adobe, etc.)")
    print("2. Usar la herramienta de selección de texto")
    print("3. Ver las coordenadas en la esquina del visor")
    print("\nO usar esta herramienta para ver el contenido del PDF:\n")

    pdf_path = input("Ruta del PDF: ").strip()

    if not os.path.exists(pdf_path):
        print(f"Error: No se encontró {pdf_path}")
        return

    # Mostrar información del PDF
    with pdfplumber.open(pdf_path) as pdf:
        pagina = pdf.pages[0]

        print(f"\n=== INFORMACIÓN DEL PDF ===")
        print(f"Ancho: {pagina.width} puntos")
        print(f"Alto: {pagina.height} puntos")
        print(f"\nCoordenadas PDF: origen en esquina inferior izquierda")
        print(f"X aumenta hacia la derecha (0 a {pagina.width})")
        print(f"Y aumenta hacia arriba (0 a {pagina.height})")

        # Extraer y mostrar texto para referencia
        print("\n=== TEXTO ENCONTRADO EN LA PÁGINA ===")
        texto = pagina.extract_text()
        if texto:
            lineas = texto.split('\n')[:20]  # Primeras 20 líneas
            for i, linea in enumerate(lineas, 1):
                print(f"{i:2d}. {linea}")

        print("\n" + "="*60)

    # Iniciar proceso de definición de campos
    campos = []
    nombre_plantilla = input("\nNombre de la plantilla (sin .json): ").strip()
    proveedor_id = input("ID del proveedor (ej. HBS): ").strip()
    nombre_proveedor = input("Nombre del proveedor (ej. HBS Consulting): ").strip()

    print("\n=== DEFINIR CAMPOS ===")
    print("Ingresa las coordenadas en formato PDF (x1, y1, x2, y2)")
    print("Tip: x1,y1 = esquina inferior izquierda, x2,y2 = esquina superior derecha")
    print("Escribe 'fin' como nombre de campo para terminar\n")

    while True:
        nombre_campo = input("\nNombre del campo (o 'fin' para terminar): ").strip()

        if nombre_campo.lower() == 'fin':
            break

        if not nombre_campo:
            continue

        try:
            print("Coordenadas (separadas por coma o espacio):")
            coords_str = input("x1, y1, x2, y2: ").strip()

            # Parsear coordenadas
            coords = [float(x.strip()) for x in coords_str.replace(',', ' ').split()]

            if len(coords) != 4:
                print("Error: Debes ingresar exactamente 4 coordenadas")
                continue

            tipo_campo = input("Tipo (texto/fecha/numerico) [texto]: ").strip().lower()
            tipo_campo = tipo_campo if tipo_campo in ["fecha", "numerico"] else "texto"

            campo = {
                "nombre": nombre_campo,
                "coordenadas": coords,
                "tipo": tipo_campo
            }

            campos.append(campo)
            print(f"✓ Campo '{nombre_campo}' agregado ({len(campos)} campos totales)")

        except ValueError as e:
            print(f"Error: Coordenadas inválidas. {e}")

    if not campos:
        print("\nNo se definieron campos. Saliendo...")
        return

    # Crear plantilla
    plantilla = {
        "proveedor_id": proveedor_id or "PROV_001",
        "nombre_proveedor": nombre_proveedor or "Proveedor Ejemplo",
        "pdf_referencia": pdf_path,
        "campos": campos
    }

    # Guardar plantilla
    os.makedirs("plantillas", exist_ok=True)
    ruta_plantilla = f"plantillas/{nombre_plantilla}.json"

    with open(ruta_plantilla, 'w', encoding='utf-8') as f:
        json.dump(plantilla, f, ensure_ascii=False, indent=4)

    print(f"\n✓ Plantilla guardada: {ruta_plantilla}")
    print(f"✓ Total de campos: {len(campos)}")


def extraer_con_ayuda_visual():
    """
    Usa pdfplumber para mostrar palabras con sus coordenadas.
    """
    print("\n=== EXTRACTOR CON AYUDA VISUAL ===")

    pdf_path = input("Ruta del PDF: ").strip()

    if not os.path.exists(pdf_path):
        print(f"Error: No se encontró {pdf_path}")
        return

    with pdfplumber.open(pdf_path) as pdf:
        pagina = pdf.pages[0]

        print(f"\n=== PALABRAS CON COORDENADAS ===")
        print(f"Ancho: {pagina.width}, Alto: {pagina.height}\n")

        # Extraer palabras con coordenadas
        palabras = pagina.extract_words()

        if not palabras:
            print("No se pudieron extraer palabras del PDF")
            return

        print(f"{'#':<4} {'Texto':<30} {'x0':<8} {'y0':<8} {'x1':<8} {'y1':<8}")
        print("-" * 75)

        for i, palabra in enumerate(palabras[:50], 1):  # Mostrar primeras 50 palabras
            texto = palabra['text'][:28]
            print(f"{i:<4} {texto:<30} {palabra['x0']:<8.1f} {palabra['top']:<8.1f} {palabra['x1']:<8.1f} {palabra['bottom']:<8.1f}")

        if len(palabras) > 50:
            print(f"\n... y {len(palabras) - 50} palabras más")

        print("\n" + "="*75)
        print("Usa estas coordenadas como referencia para crear tu plantilla")
        print("Nota: y0=top (parte superior), y1=bottom (parte inferior)")

        # Preguntar si quiere crear plantilla ahora
        crear = input("\n¿Crear plantilla ahora? (s/n): ").strip().lower()
        if crear == 's':
            crear_plantilla_con_palabras(pdf_path, palabras, pagina.width, pagina.height)


def crear_plantilla_con_palabras(pdf_path, palabras, ancho, alto):
    """
    Ayuda a crear una plantilla usando las palabras extraídas como referencia.
    """
    campos = []
    nombre_plantilla = input("\nNombre de la plantilla: ").strip()
    proveedor_id = input("ID del proveedor: ").strip()
    nombre_proveedor = input("Nombre del proveedor: ").strip()

    print("\n=== DEFINIR CAMPOS ===")
    print("Puedes usar:")
    print("1. Números de palabra (ej: '5' usa coordenadas de palabra #5)")
    print("2. Rango de palabras (ej: '5-8' usa desde palabra 5 hasta 8)")
    print("3. Coordenadas manuales (ej: '100 200 300 250')")
    print("Escribe 'fin' para terminar\n")

    while True:
        nombre_campo = input("\nNombre del campo (o 'fin'): ").strip()

        if nombre_campo.lower() == 'fin':
            break

        if not nombre_campo:
            continue

        try:
            entrada = input("Palabra # / Rango / Coordenadas: ").strip()

            if '-' in entrada:
                # Rango de palabras
                inicio, fin = map(int, entrada.split('-'))
                palabras_sel = palabras[inicio-1:fin]

                x0 = min(p['x0'] for p in palabras_sel)
                top_min = min(p['top'] for p in palabras_sel)
                x1 = max(p['x1'] for p in palabras_sel)
                bottom_max = max(p['bottom'] for p in palabras_sel)

                # Convertir a coordenadas PDF (origen inferior izquierdo)
                coords = [x0, alto - bottom_max, x1, alto - top_min]

            elif entrada.isdigit():
                # Palabra individual
                idx = int(entrada) - 1
                palabra = palabras[idx]

                # pdfplumber ya devuelve coordenadas en formato PDF
                # Pero usa 'top' y 'bottom' donde top es menor que bottom
                # PDF usa origen inferior izquierdo, así que:
                coords = [
                    palabra['x0'],
                    alto - palabra['bottom'],  # y1 (abajo)
                    palabra['x1'],
                    alto - palabra['top']       # y2 (arriba)
                ]

            else:
                # Coordenadas manuales
                coords = [float(x.strip()) for x in entrada.replace(',', ' ').split()]

            if len(coords) != 4:
                print("Error: Se necesitan 4 coordenadas")
                continue

            tipo_campo = input("Tipo (texto/fecha/numerico) [texto]: ").strip().lower()
            tipo_campo = tipo_campo if tipo_campo in ["fecha", "numerico"] else "texto"

            campo = {
                "nombre": nombre_campo,
                "coordenadas": coords,
                "tipo": tipo_campo
            }

            campos.append(campo)
            print(f"✓ Campo '{nombre_campo}' agregado: {coords}")

        except (ValueError, IndexError) as e:
            print(f"Error: {e}")

    if not campos:
        print("\nNo se definieron campos.")
        return

    # Crear y guardar plantilla
    plantilla = {
        "proveedor_id": proveedor_id or "PROV_001",
        "nombre_proveedor": nombre_proveedor or "Proveedor Ejemplo",
        "pdf_referencia": pdf_path,
        "campos": campos
    }

    os.makedirs("plantillas", exist_ok=True)
    ruta_plantilla = f"plantillas/{nombre_plantilla}.json"

    with open(ruta_plantilla, 'w', encoding='utf-8') as f:
        json.dump(plantilla, f, ensure_ascii=False, indent=4)

    print(f"\n✓ Plantilla guardada: {ruta_plantilla}")
    print(f"✓ Total de campos: {len(campos)}")


def main():
    """Menú principal."""
    print("=" * 60)
    print("  EXTRACTOR DE COORDENADAS - VERSIÓN MEJORADA")
    print("=" * 60)

    print("\nOpciones:")
    print("1. Método con ayuda visual (RECOMENDADO)")
    print("2. Método manual")
    print("3. Salir")

    opcion = input("\nSelecciona una opción (1-3): ").strip()

    if opcion == "1":
        extraer_con_ayuda_visual()
    elif opcion == "2":
        extraer_coordenadas_manual()
    elif opcion == "3":
        print("Saliendo...")
    else:
        print("Opción inválida")


if __name__ == "__main__":
    main()
