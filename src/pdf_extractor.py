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
from src.utils.data_cleaners import DataCleaner


class PDFExtractor:
    # Mapeo de nombres de campos en plantillas a nombres de columnas estándar
    MAPEO_CAMPOS = {
        # Campos principales (capturados del PDF)
        'FechaFactura': 'FechaFactura',
        'FechaVto': 'FechaVto',
        'NumFactura': 'NumFactura',
        'Base': 'Base',
        # Compatibilidad con nombres antiguos
        'num-factura': 'NumFactura',
        'numero-factura': 'NumFactura',
        'fecha-factura': 'FechaFactura',
        'fecha': 'FechaFactura',
        'fecha-vto': 'FechaVto',
        'fecha-vencimiento': 'FechaVto',
        'base': 'Base',
        'base-imponible': 'Base',
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
        self.errores = []  # Lista separada para registrar errores de extracción
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
                        # Usar nombre de archivo sin extensión como identificador
                        proveedor_id = os.path.splitext(archivo)[0]
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
        campos_requeridos = ['nombre_proveedor', 'campos']

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
        Identifica el proveedor de una factura PDF usando campos de identificación capturados.

        Estrategias:
        1. Extrae CIF y Nombre de las coordenadas de identificación de cada plantilla
        2. Compara con coincidencia del 85% para nombre (permite variaciones)
        3. CIF debe coincidir exactamente si está presente

        Args:
            ruta_pdf (str): Ruta al archivo PDF

        Returns:
            Optional[str]: ID del proveedor identificado o None
        """
        try:
            with pdfplumber.open(ruta_pdf) as pdf:
                if not pdf.pages:
                    print(f"⚠ PDF sin páginas: {os.path.basename(ruta_pdf)}")
                    return None

                pagina = pdf.pages[0]

                # Probar cada plantilla
                for proveedor_id, plantilla in self.plantillas_cargadas.items():
                    print(f"  Probando plantilla: {proveedor_id}")

                    # Extraer campos de identificación de esta plantilla
                    cif_extraido = None
                    nombre_extraido = None

                    for campo in plantilla.get('campos', []):
                        if not campo.get('es_identificacion', False):
                            continue

                        nombre_campo = campo['nombre']
                        coordenadas = campo['coordenadas']

                        try:
                            bbox = tuple(coordenadas)
                            area_recortada = pagina.crop(bbox)
                            texto = area_recortada.extract_text() or ""
                            texto = texto.strip().lower()

                            if nombre_campo == 'CIF_Identificacion':
                                cif_extraido = texto
                                print(f"    CIF extraído: {cif_extraido}")
                            elif nombre_campo == 'Nombre_Identificacion':
                                nombre_extraido = texto
                                print(f"    Nombre extraído: {nombre_extraido}")
                        except Exception as e:
                            print(f"    Error extrayendo {nombre_campo}: {e}")

                    # Validar coincidencias - CUALQUIERA de las dos sirve
                    cif_plantilla = plantilla.get('cif_proveedor', '').strip().lower()
                    nombre_plantilla = plantilla.get('nombre_proveedor', '').strip().lower()

                    # Opción 1: Verificar CIF (debe coincidir exactamente)
                    if cif_extraido and cif_plantilla:
                        if cif_extraido == cif_plantilla:
                            print(f"OK Proveedor identificado por CIF: {proveedor_id}")
                            return proveedor_id
                        else:
                            print(f"    CIF no coincide: extraido='{cif_extraido}' vs plantilla='{cif_plantilla}'")

                    # Opción 2: Verificar Nombre (85% de coincidencia)
                    if nombre_extraido and nombre_plantilla:
                        coincidencia = self._calcular_similitud(nombre_extraido, nombre_plantilla)
                        print(f"    Similitud nombre: {coincidencia:.1f}%")

                        if coincidencia >= 85.0:
                            print(f"OK Proveedor identificado por nombre ({coincidencia:.1f}% coincidencia): {proveedor_id}")
                            return proveedor_id

        except Exception as e:
            print(f"Error identificando proveedor: {e}")

        print(f"AVISO: No se pudo identificar proveedor para: {os.path.basename(ruta_pdf)}")
        return None

    def _calcular_similitud(self, texto1: str, texto2: str) -> float:
        """
        Calcula el porcentaje de similitud entre dos textos.
        Ignora puntuación y espacios extras.

        Args:
            texto1: Primer texto
            texto2: Segundo texto

        Returns:
            float: Porcentaje de similitud (0-100)
        """
        import re

        # Normalizar textos: minúsculas, quitar puntuación y espacios extras
        def normalizar(texto):
            texto = texto.lower().strip()
            # Quitar puntuación
            texto = re.sub(r'[.,;:!?¿¡()\[\]{}"\'-]', '', texto)
            # Normalizar espacios
            texto = re.sub(r'\s+', ' ', texto).strip()
            return texto

        t1 = normalizar(texto1)
        t2 = normalizar(texto2)

        # Si son exactamente iguales
        if t1 == t2:
            return 100.0

        # Contar caracteres coincidentes en la misma posición
        min_len = min(len(t1), len(t2))
        max_len = max(len(t1), len(t2))

        if max_len == 0:
            return 0.0

        coincidencias = sum(1 for i in range(min_len) if t1[i] == t2[i])

        # Penalizar diferencia de longitud
        similitud = (coincidencias / max_len) * 100

        return similitud

    def _procesar_campos_auxiliares(self, datos_extraidos: dict) -> dict:
        """
        Procesa campos auxiliares y aplica cálculos automáticos.

        Los campos auxiliares se usan para cálculos pero NO se exportan al Excel.
        Por ejemplo, "Portes" se suma a "Base" y luego se elimina.

        Args:
            datos_extraidos (dict): Datos extraídos del PDF (pueden incluir campos auxiliares)

        Returns:
            dict: Datos procesados (sin campos auxiliares)
        """
        # Si existe "Portes", sumarlo a "Base"
        if "Portes" in datos_extraidos and datos_extraidos["Portes"]:
            try:
                # Convertir a float
                base = float(datos_extraidos.get("Base", 0))
                portes_str = str(datos_extraidos["Portes"]).strip()

                # Si Portes está vacío, no hacer nada
                if portes_str and portes_str != "":
                    portes = float(portes_str)

                    # Sumar solo si Portes > 0
                    if portes > 0:
                        nueva_base = base + portes
                        datos_extraidos["Base"] = str(nueva_base)
                        print(f"  ℹ️  Base ajustada: {base} + {portes} (Portes) = {nueva_base}")
            except (ValueError, TypeError) as e:
                print(f"  ⚠️  No se pudo sumar Portes a Base: {e}")

        # Eliminar campos auxiliares antes de exportar
        if "Portes" in datos_extraidos:
            del datos_extraidos["Portes"]

        return datos_extraidos

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
        # Solo los 9 campos requeridos por el usuario
        datos_factura = {
            'CIF': plantilla.get('cif_proveedor', ''),  # CIF del proveedor desde la plantilla
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

                campos_extraidos_exitosamente = 0

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
                            if valor_procesado and valor_procesado != "":
                                datos_factura[nombre_columna] = valor_procesado
                                campos_extraidos_exitosamente += 1
                                print(f"  {nombre_columna}: {valor_procesado}")
                            else:
                                print(f"  {nombre_columna}: (vacío)")
                        else:
                            # Campo no estándar, guardarlo con prefijo _ para metadatos
                            datos_factura[f'_{nombre_campo_plantilla}'] = valor_procesado
                            print(f"  {nombre_campo_plantilla} (no estándar): {valor_procesado}")

                    except Exception as e:
                        print(f"  Error extrayendo {nombre_campo_plantilla}: {e}")
                        nombre_columna = self.MAPEO_CAMPOS.get(nombre_campo_plantilla, nombre_campo_plantilla)
                        if nombre_columna in datos_factura:
                            datos_factura[nombre_columna] = "ERROR"

                # Validar que se extrajeron datos útiles
                if campos_extraidos_exitosamente == 0:
                    raise Exception("No se pudo extraer ningún campo válido - posible error en plantilla o PDF no compatible")

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
        """Limpia campos de texto. Usa DataCleaner.clean_text()."""
        return DataCleaner.clean_text(texto)

    def limpiar_fecha(self, texto: str) -> str:
        """
        Limpia y normaliza campos de fecha al formato DD/MM/YYYY.
        Usa DataCleaner.clean_date().

        Args:
            texto (str): Texto que contiene una fecha

        Returns:
            str: Fecha en formato DD/MM/YYYY o texto original si no se reconoce
        """
        return DataCleaner.clean_date(texto)

    def limpiar_numerico(self, texto: str) -> str:
        """Limpia y normaliza campos numéricos. Usa DataCleaner.clean_numeric()."""
        return DataCleaner.clean_numeric(texto)

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
        # Set para detectar duplicados: (CIF, NumFactura, FechaFactura)
        facturas_procesadas = set()

        for archivo_pdf in archivos_pdf:
            ruta_completa = os.path.join(self.directorio_facturas, archivo_pdf)
            print(f"\nProcesando: {archivo_pdf}")

            # Identificar proveedor
            proveedor_id = self.identificar_proveedor(ruta_completa)

            if proveedor_id:
                try:
                    # Usar método multipágina que extrae de la última página de cada factura
                    lista_datos = self.extraer_datos_factura_multipagina(ruta_completa, proveedor_id)

                    # Procesar cada factura extraída del PDF
                    for datos in lista_datos:
                        # Procesar campos auxiliares (ej: sumar Portes a Base)
                        datos = self._procesar_campos_auxiliares(datos)

                        # Verificar duplicados usando CIF + NumFactura + FechaFactura
                        clave_duplicado = (
                            datos.get('CIF', ''),
                            datos.get('NumFactura', ''),
                            datos.get('FechaFactura', '')
                        )

                        if clave_duplicado in facturas_procesadas:
                            print(f"WARN Factura duplicada detectada (CIF: {datos.get('CIF')}, Num: {datos.get('NumFactura')}, Fecha: {datos.get('FechaFactura')})")
                            # Marcar como duplicado en metadatos
                            datos['_Duplicado'] = True
                            datos['_Motivo_Duplicado'] = f"Ya existe factura con mismo CIF, NumFactura y FechaFactura"
                        else:
                            facturas_procesadas.add(clave_duplicado)
                            datos['_Duplicado'] = False

                        resultados.append(datos)

                    print(f"OK Procesado exitosamente ({len(lista_datos)} factura(s))")
                except Exception as e:
                    print(f"ERROR procesando: {e}")
                    # Registrar en log de errores, NO en resultados
                    error_registro = {
                        'Archivo': archivo_pdf,
                        'Pagina': 'N/A',
                        'Error': f'Error al procesar factura: {str(e)}',
                        'Proveedor': proveedor_id,
                        'Fecha_Procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.errores.append(error_registro)
            else:
                print(f"ERROR Proveedor no identificado")
                # Registrar en log de errores, NO en resultados
                error_registro = {
                    'Archivo': archivo_pdf,
                    'Pagina': 'N/A',
                    'Error': 'Proveedor no identificado - no hay plantilla que coincida',
                    'Proveedor': 'NO_IDENTIFICADO',
                    'Fecha_Procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.errores.append(error_registro)

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
        facturas_con_error = sum(1 for r in self.resultados if '_Error' in r)
        facturas_duplicadas = sum(1 for r in self.resultados if r.get('_Duplicado', False))
        facturas_exitosas = total_facturas - facturas_con_error - facturas_duplicadas

        # Estadísticas por proveedor
        proveedores = {}
        for resultado in self.resultados:
            proveedor = resultado.get('_Proveedor_ID', 'DESCONOCIDO')
            if proveedor not in proveedores:
                proveedores[proveedor] = {'total': 0, 'exitosos': 0, 'errores': 0}

            proveedores[proveedor]['total'] += 1
            if '_Error' in resultado:
                proveedores[proveedor]['errores'] += 1
            else:
                proveedores[proveedor]['exitosos'] += 1

        return {
            'total_facturas': total_facturas,
            'facturas_exitosas': facturas_exitosas,
            'facturas_duplicadas': facturas_duplicadas,
            'facturas_con_error': facturas_con_error,
            'tasa_exito': round((facturas_exitosas / total_facturas) * 100, 2) if total_facturas > 0 else 0,
            'proveedores': proveedores,
            'plantillas_disponibles': len(self.plantillas_cargadas)
        }

    # ==================== MÉTODOS PARA SOPORTE MULTIPÁGINA ====================

    def extraer_num_factura_de_pagina(self, pagina, plantilla: Dict) -> Optional[str]:
        """
        Extrae el número de factura de una página específica según la plantilla.

        Args:
            pagina: Objeto página de pdfplumber
            plantilla (Dict): Plantilla del proveedor

        Returns:
            Optional[str]: Número de factura o None si no se encuentra
        """
        # Buscar el campo NumFactura en la plantilla
        for campo in plantilla.get('campos', []):
            nombre_campo = campo['nombre']

            # Verificar si es el campo NumFactura (puede estar con varios nombres)
            nombre_mapeado = self.MAPEO_CAMPOS.get(nombre_campo, nombre_campo)

            if nombre_mapeado == 'NumFactura':
                try:
                    coordenadas = campo['coordenadas']
                    bbox = tuple(coordenadas)
                    area_recortada = pagina.crop(bbox)
                    texto_extraido = area_recortada.extract_text()

                    if texto_extraido:
                        # Limpiar y procesar el número de factura
                        num_factura = self.limpiar_texto(texto_extraido)

                        # Validar que no sea texto basura
                        if num_factura and self._es_numfactura_valido(num_factura):
                            return num_factura
                        else:
                            return None

                except Exception as e:
                    print(f"Error extrayendo NumFactura de página: {e}")
                    return None

        # No se encontró campo NumFactura en la plantilla
        return None

    def _es_numfactura_valido(self, num_factura: str) -> bool:
        """
        Valida si un texto extraído como NumFactura es realmente válido.

        Args:
            num_factura (str): Texto extraído como número de factura

        Returns:
            bool: True si es válido, False si es texto basura
        """
        if not num_factura or len(num_factura.strip()) == 0:
            return False

        # Convertir a minúsculas para comparar
        texto_lower = num_factura.lower()

        # Palabras que indican que NO es un número de factura válido
        palabras_invalidas = [
            'esta página',
            'página',
            'continuación',
            'continua',
            'sigue',
            'ver página',
            'página siguiente',
            'total',
            'subtotal',
            'n/a',
            'sin número'
        ]

        # Si contiene alguna palabra inválida, no es válido
        for palabra in palabras_invalidas:
            if palabra in texto_lower:
                return False

        return True

    def agrupar_paginas_por_factura(self, paginas_data: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Agrupa páginas por número de factura.

        Args:
            paginas_data (List[Dict]): Lista de diccionarios con info de cada página
                                       Cada dict debe tener: 'pagina_num', 'NumFactura'

        Returns:
            Dict[str, List[Dict]]: Diccionario con NumFactura como clave y lista de páginas como valor
                                   Las páginas sin NumFactura se agrupan bajo 'ERROR_SIN_NUMFACTURA'
        """
        grupos = {}

        for pagina_info in paginas_data:
            num_factura = pagina_info.get('NumFactura')

            # Si no hay NumFactura o está vacío, agrupar como error
            if not num_factura or num_factura.strip() == '':
                if 'ERROR_SIN_NUMFACTURA' not in grupos:
                    grupos['ERROR_SIN_NUMFACTURA'] = []
                grupos['ERROR_SIN_NUMFACTURA'].append(pagina_info)
            else:
                # Agrupar por NumFactura
                if num_factura not in grupos:
                    grupos[num_factura] = []
                grupos[num_factura].append(pagina_info)

        return grupos

    def obtener_ultima_pagina_factura(self, paginas_grupo: List[Dict]) -> Dict:
        """
        Obtiene la última página de un grupo de páginas de una factura.

        Args:
            paginas_grupo (List[Dict]): Lista de páginas de una misma factura

        Returns:
            Dict: Información de la última página
        """
        if not paginas_grupo:
            return {}

        # La última página es la que tiene el pagina_num más alto
        return paginas_grupo[-1]

    def extraer_datos_factura_multipagina(self, ruta_pdf: str, proveedor_id: str) -> List[Dict[str, Any]]:
        """
        Extrae datos de todas las facturas en un PDF que puede tener múltiples páginas.

        Soporta:
        - Una factura en una página (comportamiento actual)
        - Una factura en múltiples páginas → extrae de la última página
        - Múltiples facturas en un PDF → extrae cada una de su última página

        Args:
            ruta_pdf (str): Ruta al archivo PDF
            proveedor_id (str): ID del proveedor

        Returns:
            List[Dict[str, Any]]: Lista de datos extraídos (una entrada por factura)
        """
        if proveedor_id not in self.plantillas_cargadas:
            raise ValueError(f"Plantilla no encontrada para proveedor: {proveedor_id}")

        plantilla = self.plantillas_cargadas[proveedor_id]
        facturas_extraidas = []

        try:
            with pdfplumber.open(ruta_pdf) as pdf:
                if not pdf.pages:
                    raise Exception("PDF sin páginas")

                # Paso 1: Extraer NumFactura de cada página
                print(f"  Analizando {len(pdf.pages)} página(s)...")
                paginas_data = []

                for i, pagina in enumerate(pdf.pages):
                    num_factura = self.extraer_num_factura_de_pagina(pagina, plantilla)
                    paginas_data.append({
                        'pagina_num': i,
                        'NumFactura': num_factura,
                        'page_obj': pagina
                    })
                    if num_factura:
                        print(f"    Página {i+1}: NumFactura = {num_factura}")
                    else:
                        print(f"    Página {i+1}: NumFactura no encontrado (ERROR)")

                # Paso 2: Agrupar páginas por NumFactura
                grupos = self.agrupar_paginas_por_factura(paginas_data)

                # Paso 3: Extraer datos de la última página de cada factura
                for num_factura, paginas_grupo in grupos.items():
                    # Manejar páginas con error - NO añadir a resultados, solo registrar en errores
                    if num_factura == 'ERROR_SIN_NUMFACTURA':
                        for pagina_info in paginas_grupo:
                            error_registro = {
                                'Archivo': os.path.basename(ruta_pdf),
                                'Pagina': pagina_info['pagina_num'] + 1,
                                'Error': 'Página sin NumFactura detectado',
                                'Proveedor': plantilla.get('nombre_proveedor', ''),
                                'Fecha_Procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            self.errores.append(error_registro)
                            print(f"    ERROR: Página {pagina_info['pagina_num'] + 1} sin NumFactura - registrado en log de errores")
                        continue

                    # Obtener última página del grupo
                    ultima_pagina_info = self.obtener_ultima_pagina_factura(paginas_grupo)
                    pagina = ultima_pagina_info['page_obj']
                    num_pagina = ultima_pagina_info['pagina_num']

                    print(f"  Extrayendo factura '{num_factura}' de página {num_pagina + 1} ({len(paginas_grupo)} página(s) total)")

                    # Extraer datos de la última página
                    datos_factura = {
                        'CIF': plantilla.get('cif_proveedor', ''),
                        'FechaFactura': '',
                        'Trimestre': self.trimestre,
                        'Año': self.año,
                        'FechaVto': '',
                        'NumFactura': num_factura,
                        'FechaPago': '',
                        'Base': '',
                        'ComPaypal': '',
                    }

                    # Metadatos adicionales
                    datos_factura['_Archivo'] = os.path.basename(ruta_pdf)
                    datos_factura['_Proveedor_Nombre'] = plantilla.get('nombre_proveedor', '')
                    datos_factura['_Pagina'] = num_pagina + 1
                    datos_factura['_Total_Paginas'] = len(paginas_grupo)
                    datos_factura['_Fecha_Procesamiento'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    campos_extraidos_exitosamente = 0

                    # Extraer todos los campos de la última página
                    for campo in plantilla['campos']:
                        nombre_campo_plantilla = campo['nombre']
                        coordenadas = campo['coordenadas']
                        tipo_campo = campo.get('tipo', 'texto')

                        try:
                            bbox = tuple(coordenadas)
                            area_recortada = pagina.crop(bbox)
                            texto_extraido = area_recortada.extract_text()

                            # Limpiar y procesar según tipo
                            valor_procesado = self.procesar_campo(texto_extraido, tipo_campo)

                            # Mapear nombre de campo
                            nombre_columna = self.MAPEO_CAMPOS.get(nombre_campo_plantilla, nombre_campo_plantilla)

                            # Actualizar si es un campo estándar
                            if nombre_columna in datos_factura:
                                if valor_procesado and valor_procesado != "":
                                    datos_factura[nombre_columna] = valor_procesado
                                    campos_extraidos_exitosamente += 1
                            else:
                                # Campo no estándar
                                datos_factura[f'_{nombre_campo_plantilla}'] = valor_procesado

                        except Exception as e:
                            print(f"    Error extrayendo {nombre_campo_plantilla}: {e}")
                            nombre_columna = self.MAPEO_CAMPOS.get(nombre_campo_plantilla, nombre_campo_plantilla)
                            if nombre_columna in datos_factura:
                                datos_factura[nombre_columna] = "ERROR"

                    # Validar que se extrajeron datos útiles (además del NumFactura)
                    if campos_extraidos_exitosamente <= 1:  # Solo NumFactura no cuenta
                        print(f"    ADVERTENCIA: Pocos campos extraídos ({campos_extraidos_exitosamente})")

                    facturas_extraidas.append(datos_factura)

        except Exception as e:
            print(f"Error procesando PDF multipágina {ruta_pdf}: {e}")
            # Registrar error en log de errores, NO en resultados
            error_registro = {
                'Archivo': os.path.basename(ruta_pdf),
                'Pagina': 'N/A',
                'Error': f'Error al procesar PDF: {str(e)}',
                'Proveedor': plantilla.get('nombre_proveedor', '') if proveedor_id in self.plantillas_cargadas else 'N/A',
                'Fecha_Procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.errores.append(error_registro)

        return facturas_extraidas


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