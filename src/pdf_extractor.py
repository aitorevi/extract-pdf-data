"""
Extractor principal de datos de facturas PDF usando pdfplumber y plantillas JSON.
Implementa la lógica de extracción de datos según coordenadas predefinidas.
"""

import pdfplumber
import json
import pandas as pd
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional


class PDFExtractor:
    # Mapeo de nombres de campos en plantillas a nombres de columnas estándar
    MAPEO_CAMPOS = {
        'num-factura': 'NumFactura',
        'numero-factura': 'NumFactura',
        'fecha-factura': 'FechaFactura',
        'fecha': 'FechaFactura',
        'fecha-vto': 'FechaVto',
        'fecha-vencimiento': 'FechaVto',
        'fecha-pago': 'FechaPago',
        'base': 'Base',
        'base-imponible': 'Base',
        'comision-paypal': 'ComPaypal',
        'com-paypal': 'ComPaypal',
    }

    def __init__(self, directorio_facturas: str = "facturas", directorio_plantillas: str = "plantillas",
                 trimestre: str = "", año: str = ""):
        """
        Inicializa el extractor de PDF.

        Args:
            directorio_facturas (str): Directorio donde están las facturas PDF
            directorio_plantillas (str): Directorio donde están las plantillas JSON
            trimestre (str): Trimestre fiscal (Q1, Q2, Q3, Q4)
            año (str): Año fiscal
        """
        self.directorio_facturas = directorio_facturas
        self.directorio_plantillas = directorio_plantillas
        self.plantillas_cargadas = {}
        self.resultados = []
        self.trimestre = trimestre
        self.año = año

    def cargar_plantillas(self) -> bool:
        """
        Carga todas las plantillas JSON disponibles.

        Returns:
            bool: True si se cargaron plantillas exitosamente
        """
        plantillas_encontradas = 0

        if not os.path.exists(self.directorio_plantillas):
            print(f"Error: Directorio de plantillas no existe: {self.directorio_plantillas}")
            return False

        for archivo in os.listdir(self.directorio_plantillas):
            if archivo.endswith('.json'):
                ruta_plantilla = os.path.join(self.directorio_plantillas, archivo)
                try:
                    with open(ruta_plantilla, 'r', encoding='utf-8') as f:
                        plantilla = json.load(f)

                    # Validar estructura básica de la plantilla
                    if self.validar_plantilla(plantilla):
                        proveedor_id = plantilla.get('proveedor_id', archivo)
                        self.plantillas_cargadas[proveedor_id] = plantilla
                        plantillas_encontradas += 1
                        print(f"OK Plantilla cargada: {archivo} -> {plantilla.get('nombre_proveedor', proveedor_id)}")
                    else:
                        print(f"WARN Plantilla invalida: {archivo}")

                except Exception as e:
                    print(f"Error cargando plantilla {archivo}: {e}")

        print(f"\nTotal plantillas cargadas: {plantillas_encontradas}")
        return plantillas_encontradas > 0

    def validar_plantilla(self, plantilla: Dict) -> bool:
        """
        Valida que una plantilla tenga la estructura correcta.

        Args:
            plantilla (Dict): Plantilla a validar

        Returns:
            bool: True si la plantilla es válida
        """
        campos_requeridos = ['proveedor_id', 'nombre_proveedor', 'campos']

        # Verificar campos principales
        for campo in campos_requeridos:
            if campo not in plantilla:
                print(f"Campo requerido faltante: {campo}")
                return False

        # Verificar estructura de campos
        if not isinstance(plantilla['campos'], list):
            print("El campo 'campos' debe ser una lista")
            return False

        for i, campo in enumerate(plantilla['campos']):
            if not isinstance(campo, dict):
                print(f"Campo {i} no es un diccionario")
                return False

            campos_campo = ['nombre', 'coordenadas', 'tipo']
            for subcampo in campos_campo:
                if subcampo not in campo:
                    print(f"Campo {i} falta subcampo: {subcampo}")
                    return False

            # Validar coordenadas
            if not isinstance(campo['coordenadas'], list) or len(campo['coordenadas']) != 4:
                print(f"Campo {i} tiene coordenadas inválidas")
                return False

        return True

    def identificar_proveedor(self, ruta_pdf: str) -> Optional[str]:
        """
        Identifica el proveedor de una factura PDF.

        Estrategias:
        1. Por nombre de archivo
        2. Por contenido del PDF (buscar texto identificativo)

        Args:
            ruta_pdf (str): Ruta al archivo PDF

        Returns:
            Optional[str]: ID del proveedor identificado o None
        """
        nombre_archivo = os.path.basename(ruta_pdf).lower()

        # Estrategia 1: Por nombre de archivo
        for proveedor_id, plantilla in self.plantillas_cargadas.items():
            nombre_proveedor = plantilla.get('nombre_proveedor', '').lower()

            # Buscar coincidencias en el nombre del archivo
            palabras_clave = nombre_proveedor.split()
            for palabra in palabras_clave:
                if len(palabra) > 3 and palabra in nombre_archivo:
                    print(f"Proveedor identificado por archivo: {proveedor_id}")
                    return proveedor_id

        # Estrategia 2: Por contenido del PDF
        try:
            with pdfplumber.open(ruta_pdf) as pdf:
                if pdf.pages:
                    texto_pagina = pdf.pages[0].extract_text() or ""
                    texto_pagina = texto_pagina.lower()

                    for proveedor_id, plantilla in self.plantillas_cargadas.items():
                        nombre_proveedor = plantilla.get('nombre_proveedor', '').lower()

                        # Buscar el nombre del proveedor en el contenido
                        palabras_clave = nombre_proveedor.split()
                        coincidencias = sum(1 for palabra in palabras_clave if len(palabra) > 3 and palabra in texto_pagina)

                        if coincidencias >= len(palabras_clave) // 2:  # Al menos 50% de coincidencias
                            print(f"Proveedor identificado por contenido: {proveedor_id}")
                            return proveedor_id

        except Exception as e:
            print(f"Error leyendo PDF para identificación: {e}")

        print(f"⚠ No se pudo identificar proveedor para: {os.path.basename(ruta_pdf)}")
        return None

    def extraer_datos_factura(self, ruta_pdf: str, proveedor_id: str) -> Dict[str, Any]:
        """
        Extrae datos de una factura usando su plantilla correspondiente.

        Args:
            ruta_pdf (str): Ruta al archivo PDF
            proveedor_id (str): ID del proveedor

        Returns:
            Dict[str, Any]: Datos extraídos de la factura
        """
        if proveedor_id not in self.plantillas_cargadas:
            raise ValueError(f"Plantilla no encontrada para proveedor: {proveedor_id}")

        plantilla = self.plantillas_cargadas[proveedor_id]

        # Inicializar con nombres de columnas estándar (todos vacíos por defecto)
        datos_factura = {
            'CIF': proveedor_id,  # CIF del proveedor
            'FechaFactura': '',
            'Trimestre': self.trimestre,
            'Año': self.año,
            'FechaVto': '',
            'NumFactura': '',
            'FechaPago': '',
            'Base': '',
            'ComPaypal': '',
        }

        # Metadatos adicionales (para uso interno, con prefijo _)
        datos_factura['_Archivo'] = os.path.basename(ruta_pdf)
        datos_factura['_Proveedor_Nombre'] = plantilla.get('nombre_proveedor', '')
        datos_factura['_Fecha_Procesamiento'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            with pdfplumber.open(ruta_pdf) as pdf:
                if not pdf.pages:
                    raise Exception("PDF sin páginas")

                # Procesar primera página (asumimos datos en primera página)
                pagina = pdf.pages[0]

                for campo in plantilla['campos']:
                    nombre_campo_plantilla = campo['nombre']
                    coordenadas = campo['coordenadas']
                    tipo_campo = campo.get('tipo', 'texto')

                    try:
                        # Extraer texto usando coordenadas (bbox)
                        bbox = tuple(coordenadas)  # (x1, y1, x2, y2)
                        area_recortada = pagina.crop(bbox)
                        texto_extraido = area_recortada.extract_text()

                        # Limpiar y procesar según tipo
                        valor_procesado = self.procesar_campo(texto_extraido, tipo_campo)

                        # Mapear nombre de campo de plantilla a nombre de columna estándar
                        nombre_columna = self.MAPEO_CAMPOS.get(nombre_campo_plantilla, nombre_campo_plantilla)

                        # Solo actualizar si es un campo estándar
                        if nombre_columna in datos_factura:
                            datos_factura[nombre_columna] = valor_procesado
                            print(f"  {nombre_columna}: {valor_procesado}")
                        else:
                            # Campo no estándar, guardarlo con prefijo _ para metadatos
                            datos_factura[f'_{nombre_campo_plantilla}'] = valor_procesado
                            print(f"  {nombre_campo_plantilla} (no estándar): {valor_procesado}")

                    except Exception as e:
                        print(f"  Error extrayendo {nombre_campo_plantilla}: {e}")
                        nombre_columna = self.MAPEO_CAMPOS.get(nombre_campo_plantilla, nombre_campo_plantilla)
                        if nombre_columna in datos_factura:
                            datos_factura[nombre_columna] = "ERROR"

        except Exception as e:
            print(f"Error procesando PDF {ruta_pdf}: {e}")
            datos_factura['_Error'] = str(e)

        return datos_factura

    def procesar_campo(self, texto_crudo: str, tipo_campo: str) -> str:
        """
        Procesa y limpia un campo extraído según su tipo.

        Args:
            texto_crudo (str): Texto extraído del PDF
            tipo_campo (str): Tipo de campo (texto, fecha, numerico)

        Returns:
            str: Valor procesado y limpio
        """
        if not texto_crudo:
            return ""

        texto_limpio = texto_crudo.strip()

        if tipo_campo == "numerico":
            return self.limpiar_numerico(texto_limpio)
        elif tipo_campo == "fecha":
            return self.limpiar_fecha(texto_limpio)
        else:  # texto
            return self.limpiar_texto(texto_limpio)

    def limpiar_texto(self, texto: str) -> str:
        """Limpia campos de texto."""
        # Remover caracteres especiales problemáticos
        texto = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto)
        # Normalizar espacios
        texto = re.sub(r'\s+', ' ', texto)
        return texto.strip()

    def limpiar_fecha(self, texto: str) -> str:
        """Limpia y normaliza campos de fecha."""
        texto = self.limpiar_texto(texto)

        # Patrones comunes de fecha
        patrones_fecha = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',  # DD/MM/YYYY o DD-MM-YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD o YYYY-MM-DD
            r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}',  # DD de MMMM de YYYY
        ]

        for patron in patrones_fecha:
            match = re.search(patron, texto)
            if match:
                return match.group()

        return texto  # Devolver original si no se reconoce patrón

    def limpiar_numerico(self, texto: str) -> str:
        """Limpia y normaliza campos numéricos."""
        # Remover caracteres no numéricos excepto puntos, comas y signos
        texto_limpio = re.sub(r'[^\d.,+-]', '', texto)

        # Manejar formato europeo (1.234,56) vs americano (1,234.56)
        if ',' in texto_limpio and '.' in texto_limpio:
            # Si hay ambos, asumir formato europeo si la coma está después del punto
            if texto_limpio.rfind(',') > texto_limpio.rfind('.'):
                # Formato europeo: 1.234,56
                texto_limpio = texto_limpio.replace('.', '').replace(',', '.')
            else:
                # Formato americano: 1,234.56
                texto_limpio = texto_limpio.replace(',', '')
        elif ',' in texto_limpio:
            # Solo coma - podría ser decimal europeo o separador de miles
            partes = texto_limpio.split(',')
            if len(partes) == 2 and len(partes[1]) <= 2:
                # Probablemente decimal: 123,45
                texto_limpio = texto_limpio.replace(',', '.')
            else:
                # Probablemente separador de miles: 1,234
                texto_limpio = texto_limpio.replace(',', '')

        # Validar que es un número válido
        try:
            float(texto_limpio)
            return texto_limpio
        except ValueError:
            return texto.strip()  # Devolver original si no se puede convertir

    def procesar_directorio_facturas(self) -> List[Dict[str, Any]]:
        """
        Procesa todas las facturas PDF en el directorio.

        Returns:
            List[Dict[str, Any]]: Lista de datos extraídos de todas las facturas
        """
        if not os.path.exists(self.directorio_facturas):
            print(f"Error: Directorio de facturas no existe: {self.directorio_facturas}")
            return []

        archivos_pdf = [f for f in os.listdir(self.directorio_facturas) if f.lower().endswith('.pdf')]

        if not archivos_pdf:
            print(f"No se encontraron archivos PDF en: {self.directorio_facturas}")
            return []

        print(f"\n=== PROCESANDO {len(archivos_pdf)} FACTURAS ===")

        resultados = []

        for archivo_pdf in archivos_pdf:
            ruta_completa = os.path.join(self.directorio_facturas, archivo_pdf)
            print(f"\nProcesando: {archivo_pdf}")

            # Identificar proveedor
            proveedor_id = self.identificar_proveedor(ruta_completa)

            if proveedor_id:
                try:
                    datos = self.extraer_datos_factura(ruta_completa, proveedor_id)
                    resultados.append(datos)
                    print(f"OK Procesado exitosamente")
                except Exception as e:
                    print(f"ERROR procesando: {e}")
                    # Agregar registro de error
                    datos_error = {
                        'Archivo': archivo_pdf,
                        'Proveedor_ID': proveedor_id,
                        'Error': str(e),
                        'Fecha_Procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    resultados.append(datos_error)
            else:
                print(f"ERROR Proveedor no identificado")
                # Agregar registro de proveedor no identificado
                datos_error = {
                    'Archivo': archivo_pdf,
                    'Proveedor_ID': 'NO_IDENTIFICADO',
                    'Error': 'Proveedor no identificado',
                    'Fecha_Procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                resultados.append(datos_error)

        self.resultados = resultados
        print(f"\n=== PROCESAMIENTO COMPLETADO ===")
        print(f"Total facturas procesadas: {len(resultados)}")

        return resultados

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Genera estadísticas del procesamiento.

        Returns:
            Dict[str, Any]: Estadísticas del procesamiento
        """
        if not self.resultados:
            return {}

        total_facturas = len(self.resultados)
        facturas_con_error = sum(1 for r in self.resultados if 'Error' in r)
        facturas_exitosas = total_facturas - facturas_con_error

        # Estadísticas por proveedor
        proveedores = {}
        for resultado in self.resultados:
            proveedor = resultado.get('Proveedor_ID', 'DESCONOCIDO')
            if proveedor not in proveedores:
                proveedores[proveedor] = {'total': 0, 'exitosos': 0, 'errores': 0}

            proveedores[proveedor]['total'] += 1
            if 'Error' in resultado:
                proveedores[proveedor]['errores'] += 1
            else:
                proveedores[proveedor]['exitosos'] += 1

        return {
            'total_facturas': total_facturas,
            'facturas_exitosas': facturas_exitosas,
            'facturas_con_error': facturas_con_error,
            'tasa_exito': round((facturas_exitosas / total_facturas) * 100, 2) if total_facturas > 0 else 0,
            'proveedores': proveedores,
            'plantillas_disponibles': len(self.plantillas_cargadas)
        }


def main():
    """Función principal para testing del extractor."""
    extractor = PDFExtractor()

    print("=== EXTRACTOR DE DATOS DE FACTURAS PDF ===")

    # Cargar plantillas
    if not extractor.cargar_plantillas():
        print("No se pudieron cargar plantillas. Verifica el directorio 'plantillas/'.")
        return

    # Procesar facturas
    resultados = extractor.procesar_directorio_facturas()

    if resultados:
        # Mostrar estadísticas
        stats = extractor.obtener_estadisticas()
        print(f"\n=== ESTADÍSTICAS ===")
        print(f"Facturas procesadas: {stats['total_facturas']}")
        print(f"Exitosas: {stats['facturas_exitosas']} ({stats['tasa_exito']}%)")
        print(f"Con errores: {stats['facturas_con_error']}")
        print(f"Plantillas disponibles: {stats['plantillas_disponibles']}")

        # Mostrar resultados de muestra
        print(f"\n=== MUESTRA DE RESULTADOS ===")
        for i, resultado in enumerate(resultados[:3]):  # Mostrar primeros 3
            print(f"\nFactura {i+1}: {resultado.get('Archivo', 'N/A')}")
            for key, value in resultado.items():
                if key != 'Archivo':
                    print(f"  {key}: {value}")


if __name__ == "__main__":
    main()