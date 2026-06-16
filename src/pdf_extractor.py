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
from src.utils.cif import CIF
from src.utils.pdf_text_detector import tiene_texto_extraible, detectar_texto_corrupto_en_pagina
from src.utils.ocr_engine import OCREngine

# Import opcional de LLM extractor (fallback si no hay plantilla o plantilla falla)
try:
    from src.utils.llm_extractor import LLMExtractor
    LLM_DISPONIBLE = True
except ImportError:
    LLM_DISPONIBLE = False
    print("AVISO: LLM extractor no disponible (instalar: pip install openai)")


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

    # CIF corporativo para validar facturas del cliente
    CIF_CORPORATIVO = "E98530876"

    @staticmethod
    def calcular_trimestre_desde_fecha(fecha: datetime) -> int:
        """
        Calcula el trimestre (1-4) a partir de una fecha.

        Args:
            fecha (datetime): Fecha a procesar

        Returns:
            int: Número de trimestre (1, 2, 3 o 4)
        """
        mes = fecha.month
        if mes <= 3:
            return 1
        elif mes <= 6:
            return 2
        elif mes <= 9:
            return 3
        else:
            return 4

    @staticmethod
    def parsear_trimestre(trimestre_str: str) -> int:
        """
        Parsea un string de trimestre a número entero.

        Args:
            trimestre_str (str): String como "1T", "2T", "Q1", "Q2" o "1", "2"

        Returns:
            int: Número de trimestre (1, 2, 3 o 4)
        """
        # Normalizar a mayúsculas
        trimestre_str = trimestre_str.upper().strip()

        # Eliminar prefijos "T" o "Q"
        trimestre_str = trimestre_str.replace("T", "").replace("Q", "")

        return int(trimestre_str)

    @staticmethod
    def formatear_trimestre(numero: int) -> str:
        """
        Formatea un número de trimestre como string numérico para Excel.

        Args:
            numero (int): Número de trimestre (1, 2, 3 o 4)

        Returns:
            str: Trimestre como número (ej: "1", "2", "3", "4")
        """
        return str(numero)

    @staticmethod
    def determinar_trimestre_para_exportacion_excel(fecha_factura: datetime,
                                                     trimestre_usuario: int,
                                                     año_usuario: int) -> Optional[tuple]:
        """
        Calcula el trimestre y año que debe aparecer en el Excel según lógica de negocio compleja.

        IMPORTANTE: Esta función implementa reglas de negocio específicas para la exportación
        a Excel y NO debe usarse para cálculos de índices o detección de duplicados.
        Para esos casos, usar calcular_trimestre_desde_fecha() que calcula el trimestre real.

        Lógica de negocio (para Excel):
        - Si la factura es del mismo año y su trimestre es <= al trimestre introducido:
          se marca con el trimestre introducido
        - Si la factura es del mismo año y su trimestre es > al trimestre introducido:
          se marca con su propio trimestre
        - Caso especial T1: Si el usuario introduce T1 de año X, las facturas del T4 del año X-1
          se marcan como T1 del año X
        - Otras facturas de años diferentes se excluyen (retorna None)

        Args:
            fecha_factura (datetime): Fecha de la factura
            trimestre_usuario (int): Trimestre introducido por el usuario (1-4)
            año_usuario (int): Año introducido por el usuario

        Returns:
            Optional[tuple]: (trimestre, año) o None si la factura debe excluirse
        """
        año_factura = fecha_factura.year
        trimestre_factura = PDFExtractor.calcular_trimestre_desde_fecha(fecha_factura)

        # Caso 1: Factura del mismo año que el introducido
        if año_factura == año_usuario:
            # Si el trimestre de la factura es <= al introducido, usar el introducido
            if trimestre_factura <= trimestre_usuario:
                return (trimestre_usuario, año_usuario)
            # Si el trimestre de la factura es >, usar su propio trimestre
            else:
                return (trimestre_factura, año_usuario)

        # Caso 2: Caso especial T1 - incluir T4 del año anterior
        elif trimestre_usuario == 1 and año_factura == (año_usuario - 1) and trimestre_factura == 4:
            return (1, año_usuario)

        # Caso 3: Facturas de otros años/trimestres se excluyen
        else:
            return None

    def __init__(self, directorio_facturas: str = "documentos/por_procesar",
                 directorio_plantillas: str = "plantillas",
                 trimestre: str = "", año: str = "", organizar_archivos: bool = True,
                 usar_llm_fallback: bool = True):
        """
        Inicializa el extractor de PDF.

        Nueva estructura (desde v2.0):
        - directorio_facturas: documentos/por_procesar/ (PDFs pendientes)
        - Resultados organizados en: documentos/procesados/
        - Reportes Excel en: documentos/reportes/

        Args:
            directorio_facturas (str): Directorio donde están las facturas PDF a procesar
                                       (default: "documentos/por_procesar")
            directorio_plantillas (str): Directorio donde están las plantillas JSON
            trimestre (str): Trimestre fiscal (1T, 2T, 3T, 4T)
            año (str): Año fiscal
            organizar_archivos (bool): Si True, organiza PDFs automáticamente después de procesar
            usar_llm_fallback (bool): Si True, usa LLM como fallback cuando no hay plantilla o falla
                                      (requiere API key de OpenAI en variable OPENAI_API_KEY)
        """
        self.directorio_facturas = directorio_facturas
        self.directorio_plantillas = directorio_plantillas
        self.plantillas_cargadas = {}
        self.indice_palabras = {}  # Índice de palabras clave por plantilla (optimización de velocidad)
        self.resultados = []
        self.errores = []  # Lista separada para registrar errores de extracción
        self.trimestre = trimestre
        self.año = año
        self.organizar_archivos = organizar_archivos
        self.usar_llm_fallback = usar_llm_fallback

        # Métricas de uso (template vs LLM)
        self.metricas = {
            'total_procesadas': 0,
            'extracciones_template': 0,
            'extracciones_llm': 0,
            'fallbacks_activados': 0,
            'proveedores_sin_plantilla': 0
        }

        # Inicializar organizador de archivos si está habilitado
        if self.organizar_archivos:
            from src.file_organizer import PDFOrganizer
            # Extraer directorio base (documentos) de la ruta de facturas
            # Ej: "documentos/por_procesar" → "documentos"
            from pathlib import Path
            directorio_base = Path(directorio_facturas).parent if "/" in directorio_facturas else "documentos"
            self.organizador = PDFOrganizer(directorio_base=str(directorio_base))
        else:
            self.organizador = None

        # Inicializar motor OCR (inglés por defecto, funciona bien para español también)
        self.ocr = OCREngine(idioma='eng')
        self.ocr_disponible = self.ocr.is_available()

        # Inicializar LLM extractor si está disponible y habilitado
        self.llm_extractor = None
        if self.usar_llm_fallback and LLM_DISPONIBLE:
            try:
                self.llm_extractor = LLMExtractor()
                print("[OK] LLM fallback habilitado (GPT-4o mini)")
            except Exception as e:
                print(f"[AVISO] No se pudo inicializar LLM fallback: {e}")
                print("   Tip: Establece variable de entorno OPENAI_API_KEY")
                self.llm_extractor = None
        elif self.usar_llm_fallback and not LLM_DISPONIBLE:
            print("[AVISO] LLM fallback solicitado pero modulo no disponible")
            print("   Instala con: pip install openai")

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

                        # Construir índice de palabras clave para búsqueda rápida
                        palabras_clave = self._extraer_palabras_clave(plantilla)
                        self.indice_palabras[proveedor_id] = palabras_clave

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

        Soporta dos tipos de campos:
        1. Campos con coordenadas fijas (tipo: texto, fecha, numerico)
        2. Campos con búsqueda por texto (tipo: busqueda_texto)

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

            # Verificar que tenga nombre y tipo
            if 'nombre' not in campo:
                print(f"Campo {i} falta subcampo: nombre")
                return False

            if 'tipo' not in campo:
                print(f"Campo {i} falta subcampo: tipo")
                return False

            tipo_campo = campo.get('tipo', '')

            # Validación específica según el tipo
            if tipo_campo == 'busqueda_texto':
                # Para búsqueda por texto: requiere patron_busqueda
                if 'patron_busqueda' not in campo:
                    print(f"Campo {i} tipo 'busqueda_texto' requiere 'patron_busqueda'")
                    return False

                # area_busqueda es opcional, pero si existe debe ser válida
                if 'area_busqueda' in campo:
                    area = campo['area_busqueda']
                    if not isinstance(area, list) or len(area) != 4:
                        print(f"Campo {i} tiene area_busqueda inválida (debe ser [x0, top, x1, bottom])")
                        return False

            else:
                # Para campos normales: requiere coordenadas
                if 'coordenadas' not in campo:
                    print(f"Campo {i} falta subcampo: coordenadas (requerido para tipo '{tipo_campo}')")
                    return False

                # Validar formato de coordenadas
                if not isinstance(campo['coordenadas'], list) or len(campo['coordenadas']) != 4:
                    print(f"Campo {i} tiene coordenadas inválidas (debe ser [x0, top, x1, bottom])")
                    return False

        return True

    def identificar_proveedor(self, ruta_pdf: str) -> Optional[str]:
        """
        Identifica el proveedor de una factura PDF usando índice de palabras clave (OPTIMIZADO).

        Nueva estrategia optimizada (10x más rápido):
        1. Extrae texto completo del PDF una sola vez
        2. Usa índice de palabras clave para filtrar candidatos (scoring rápido)
        3. Solo valida con método completo los top 3-5 candidatos más probables
        4. Compara con coincidencia del 85% para nombre o CIF exacto

        Args:
            ruta_pdf (str): Ruta al archivo PDF

        Returns:
            Optional[str]: ID del proveedor identificado o None
        """
        try:
            with pdfplumber.open(ruta_pdf) as pdf:
                if not pdf.pages:
                    print(f"[AVISO] PDF sin paginas: {os.path.basename(ruta_pdf)}")
                    return None

                pagina = pdf.pages[0]

                # Detectar si el PDF tiene texto extraíble o corrupto
                usa_ocr = False
                if not tiene_texto_extraible(pagina):
                    if self.ocr_disponible:
                        print("  [OCR] PDF sin texto extraíble, usando OCR...")
                        usa_ocr = True
                    else:
                        print("  [AVISO] PDF sin texto extraible y OCR no disponible")
                        return None
                elif detectar_texto_corrupto_en_pagina(pagina):
                    # Texto extraíble pero corrupto (códigos CID)
                    if self.ocr_disponible:
                        print("  [OCR] PDF con texto corrupto (códigos CID), usando OCR...")
                        usa_ocr = True
                    else:
                        print("  [AVISO] PDF con texto corrupto y OCR no disponible")
                        return None

                # OPTIMIZACIÓN: Extraer texto completo UNA SOLA VEZ
                if usa_ocr:
                    texto_completo = self.ocr.extraer_texto_completo(ruta_pdf, pagina_num=1)
                else:
                    texto_completo = pagina.extract_text() or ""

                texto_completo_lower = texto_completo.lower()

                # OPTIMIZACIÓN: Filtrar candidatos usando índice de palabras clave
                print(f"  Filtrando candidatos con índice de palabras clave...")
                candidatos = self._filtrar_candidatos(texto_completo_lower)

                if not candidatos:
                    print(f"  [AVISO] No se encontraron candidatos con palabras clave")
                    return None

                # Mostrar top candidatos
                print(f"  Top candidatos encontrados:")
                for i, (proveedor_id, score) in enumerate(candidatos[:5], 1):
                    print(f"    {i}. {proveedor_id} (score: {score})")

                # OPTIMIZACIÓN: Solo validar top 3-5 candidatos con método completo
                max_candidatos = 5 if len(candidatos) > 5 else len(candidatos)

                for proveedor_id, score in candidatos[:max_candidatos]:
                    print(f"  Validando plantilla: {proveedor_id} (score: {score})")

                    # Si score es 0 y no es el primer candidato, saltar
                    # (indica que no tiene palabras clave en común)
                    if score == 0 and candidatos.index((proveedor_id, score)) > 0:
                        print(f"    Saltando candidato con score 0")
                        break

                    # Validar plantilla completa
                    plantilla = self.plantillas_cargadas[proveedor_id]
                    resultado = self._validar_plantilla_identificacion(
                        pdf, ruta_pdf, proveedor_id, plantilla, usa_ocr
                    )

                    if resultado:
                        return proveedor_id

        except Exception as e:
            print(f"Error identificando proveedor: {e}")

        print(f"AVISO: No se pudo identificar proveedor para: {os.path.basename(ruta_pdf)}")
        return None

    def _validar_plantilla_identificacion(self, pdf: Any, ruta_pdf: str,
                                          proveedor_id: str, plantilla: Dict,
                                          usa_ocr: bool) -> bool:
        """
        Valida si una plantilla específica coincide con el PDF.

        Extrae campos de identificación (CIF y Nombre) y verifica coincidencias.

        Args:
            pdf: Objeto PDF de pdfplumber
            ruta_pdf: Ruta al archivo PDF
            proveedor_id: ID del proveedor a validar
            plantilla: Diccionario con información de la plantilla
            usa_ocr: Si se debe usar OCR para extracción

        Returns:
            bool: True si la plantilla coincide, False en caso contrario
        """
        pagina = pdf.pages[0]

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

                # Obtener número de página del campo (default: página 1)
                num_pagina_campo = campo.get('pagina', 1)

                # Si el campo especifica una página diferente, cargarla
                if num_pagina_campo != 1:
                    if num_pagina_campo <= len(pdf.pages):
                        pagina_identificacion = pdf.pages[num_pagina_campo - 1]
                    else:
                        pagina_identificacion = pagina
                        num_pagina_campo = 1
                else:
                    pagina_identificacion = pagina

                # Extraer texto según disponibilidad
                if usa_ocr:
                    # Usar OCR para extraer de área específica
                    texto = self.ocr.extraer_texto_area(ruta_pdf, bbox, pagina_num=num_pagina_campo)
                    texto = texto.strip()
                    metodo = "OCR"
                else:
                    # Extracción normal con pdfplumber
                    area_recortada = pagina_identificacion.crop(bbox)
                    texto = area_recortada.extract_text() or ""
                    texto = texto.strip()
                    metodo = "directo"

                    # FALLBACK: Si no se extrajo texto y OCR está disponible, intentar con OCR
                    # Esto maneja PDFs híbridos (cabecera en imagen, cuerpo en texto)
                    if not texto and self.ocr_disponible:
                        try:
                            print(f"    [FALLBACK] Área sin texto extraíble, intentando OCR...")
                            texto = self.ocr.extraer_texto_area(ruta_pdf, bbox, pagina_num=num_pagina_campo)
                            texto = texto.strip()
                            metodo = "OCR (fallback)"
                        except Exception as e_ocr:
                            print(f"    [FALLBACK] Error con OCR: {e_ocr}")

                if nombre_campo == 'CIF_Identificacion':
                    # Sanear CIF usando el Value Object
                    cif_obj = CIF(texto)
                    cif_extraido = cif_obj.value
                    print(f"    CIF extraído ({metodo}): {texto} -> normalizado: {cif_extraido}")
                elif nombre_campo == 'Nombre_Identificacion':
                    nombre_extraido = texto.lower()
                    print(f"    Nombre extraído ({metodo}): {nombre_extraido}")
            except Exception as e:
                print(f"    Error extrayendo {nombre_campo}: {e}")

        # Validar coincidencias - CUALQUIERA de las dos sirve
        # Sanear CIF de plantilla usando Value Object
        cif_plantilla_obj = CIF(plantilla.get('cif_proveedor', ''))
        cif_plantilla = cif_plantilla_obj.value
        nombre_plantilla = plantilla.get('nombre_proveedor', '').strip().lower()

        # Opción 1: Verificar CIF (debe coincidir exactamente)
        if cif_extraido and cif_plantilla:
            if cif_extraido == cif_plantilla:
                print(f"OK Proveedor identificado por CIF: {proveedor_id}")
                return True
            else:
                print(f"    CIF no coincide: extraido='{cif_extraido}' vs plantilla='{cif_plantilla}'")

        # Opción 2: Verificar Nombre (85% de coincidencia)
        if nombre_extraido and nombre_plantilla:
            coincidencia = self._calcular_similitud(nombre_extraido, nombre_plantilla)
            print(f"    Similitud nombre: {coincidencia:.1f}%")

            if coincidencia >= 85.0:
                print(f"OK Proveedor identificado por nombre ({coincidencia:.1f}% coincidencia): {proveedor_id}")
                return True

        return False

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

    def _extraer_palabras_clave(self, plantilla: Dict) -> set:
        """
        Extrae palabras clave de una plantilla para búsqueda rápida.

        Construye un conjunto de palabras clave basadas en:
        - CIF del proveedor (normalizado)
        - Palabras significativas del nombre del proveedor (> 3 caracteres)

        Args:
            plantilla: Diccionario con información de la plantilla

        Returns:
            set: Conjunto de palabras clave en minúsculas
        """
        palabras = set()

        # Agregar CIF (normalizado con Value Object)
        cif = plantilla.get('cif_proveedor', '')
        if cif:
            cif_obj = CIF(cif)
            palabras.add(cif_obj.value.lower())

        # Agregar palabras del nombre del proveedor
        nombre = plantilla.get('nombre_proveedor', '')
        if nombre:
            # Dividir por espacios y filtrar palabras cortas
            for palabra in nombre.split():
                # Solo palabras > 3 caracteres (ignora "S.L.", "S.A.", etc.)
                palabra_limpia = palabra.strip().lower()
                # Remover puntuación al final
                palabra_limpia = palabra_limpia.rstrip('.,;:')

                if len(palabra_limpia) > 3:
                    palabras.add(palabra_limpia)

        return palabras

    def _filtrar_candidatos(self, texto: str) -> List[tuple]:
        """
        Filtra candidatos usando índice de palabras clave (scoring rápido).

        Calcula un score para cada plantilla basado en cuántas palabras clave
        aparecen en el texto. Retorna lista ordenada de candidatos.

        Args:
            texto: Texto extraído del PDF (en minúsculas)

        Returns:
            List[tuple]: Lista de (proveedor_id, score) ordenada por score descendente
        """
        if not self.indice_palabras:
            # Si no hay índice, retornar todas las plantillas con score 0
            return [(proveedor_id, 0) for proveedor_id in self.plantillas_cargadas.keys()]

        # Normalizar texto: quitar puntuación y caracteres especiales
        # Esto asegura que CIFs con guiones (A-08269532) coincidan con (a08269532)
        texto_normalizado = re.sub(r'[.,;:!?¿¡()\[\]{}"\'\-/]', '', texto)
        texto_normalizado = re.sub(r'\s+', ' ', texto_normalizado).strip()

        scores = {}

        # Calcular score por cada plantilla
        for proveedor_id, palabras_clave in self.indice_palabras.items():
            score = 0

            # Contar palabras clave que aparecen en el texto normalizado
            for palabra in palabras_clave:
                if palabra in texto_normalizado:
                    score += 1

            # Solo incluir si tiene al menos 1 palabra clave
            if score > 0:
                scores[proveedor_id] = score

        # Si ningún candidato tiene score > 0, retornar todos con score 0
        if not scores:
            return [(proveedor_id, 0) for proveedor_id in self.plantillas_cargadas.keys()]

        # Ordenar por score descendente
        candidatos = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return candidatos

    def _buscar_texto_en_pdf(self, pdf_page: Any, patron_regex: str, area_busqueda: Optional[tuple] = None,
                             ruta_pdf: str = None, pagina_num: int = 1, usa_ocr: bool = False) -> Optional[str]:
        """
        Busca texto en un PDF usando expresiones regulares.

        Útil para campos que cambian de posición pero siempre tienen el mismo patrón de texto.
        Ejemplo: "Base imponible: 1234.56" puede estar en diferentes posiciones según el contenido.

        Args:
            pdf_page: Página del PDF (objeto pdfplumber page)
            patron_regex: Patrón de expresión regular para buscar
                         Ejemplo: r"Base\s*imponible[:\s]+([\\d.,]+)" captura el número después de "Base imponible:"
            area_busqueda: Tupla opcional (x0, top, x1, bottom) que limita el área de búsqueda
                          Si es None, busca en toda la página
            ruta_pdf: Ruta al PDF (necesaria si usa_ocr=True)
            pagina_num: Número de página (necesario si usa_ocr=True)
            usa_ocr: Si True, usa OCR para extraer el texto antes de buscar

        Returns:
            El primer grupo capturado del regex (entre paréntesis), o None si no encuentra coincidencia

        Ejemplo de uso en plantilla JSON:
        {
            "nombre": "Base",
            "tipo": "busqueda_texto",
            "patron_busqueda": "Base\\s*imponible[:\\s]+([\\d.,]+)",
            "area_busqueda": [0, 200, 595, 700],
            "pagina": 1
        }
        """
        try:
            # Extraer texto del área especificada o de toda la página
            if usa_ocr:
                if not ruta_pdf:
                    print("    Error: ruta_pdf es requerida para OCR en búsqueda de texto")
                    return None

                if area_busqueda:
                    # Extraer de área específica con OCR
                    texto = self.ocr.extraer_texto_area(ruta_pdf, area_busqueda, pagina_num=pagina_num)
                else:
                    # Extraer texto completo de la página con OCR
                    texto = self.ocr.extraer_texto_completo(ruta_pdf, pagina_num=pagina_num)
            else:
                # Usar pdfplumber
                if area_busqueda:
                    # Extraer de área específica
                    area_recortada = pdf_page.crop(area_busqueda)
                    texto = area_recortada.extract_text() or ""
                else:
                    # Extraer texto completo de la página
                    texto = pdf_page.extract_text() or ""

            if not texto:
                return None

            # Buscar el patrón con regex
            match = re.search(patron_regex, texto, re.IGNORECASE | re.MULTILINE)

            if match:
                # Si hay grupos capturados, devolver el primero
                if match.groups():
                    valor_encontrado = match.group(1).strip()
                    print(f"    [Búsqueda texto] Encontrado: '{valor_encontrado}' usando patrón: {patron_regex[:50]}...")
                    return valor_encontrado
                else:
                    # Si no hay grupos, devolver toda la coincidencia
                    valor_encontrado = match.group(0).strip()
                    print(f"    [Búsqueda texto] Encontrado: '{valor_encontrado}'")
                    return valor_encontrado
            else:
                print(f"    [Búsqueda texto] No se encontró coincidencia para patrón: {patron_regex[:50]}...")
                return None

        except Exception as e:
            print(f"    Error en búsqueda de texto: {e}")
            return None

    def _extraer_cif_cliente(self, pdf: Any, plantilla: Dict, ruta_pdf: str = None, usa_ocr: bool = False) -> Optional[str]:
        """
        Extrae el CIF del cliente desde el PDF usando los campos de identificación.

        Args:
            pdf: Objeto PDF de pdfplumber
            plantilla: Plantilla con campos definidos
            ruta_pdf: Ruta al archivo PDF (requerido si usa_ocr=True)
            usa_ocr: Si True, usa OCR para extraer texto

        Returns:
            CIF del cliente normalizado o None si no se encuentra
        """
        try:
            # Buscar el campo CIF_Cliente en los campos de la plantilla
            for campo in plantilla.get('campos', []):
                nombre_campo = campo.get('nombre', '')

                # Buscar específicamente el campo CIF_Cliente
                if nombre_campo == 'CIF_Cliente':
                    try:
                        pagina_num = campo.get('pagina', 1)
                        if pagina_num > len(pdf.pages):
                            continue

                        page = pdf.pages[pagina_num - 1]
                        coordenadas = campo.get('coordenadas', [])
                        if len(coordenadas) != 4:
                            continue

                        bbox = tuple(coordenadas)

                        if usa_ocr:
                            # Usar OCR para extraer texto
                            if not ruta_pdf:
                                print("    Error: ruta_pdf es requerida para OCR")
                                continue
                            texto = self.ocr.extraer_texto_area(ruta_pdf, bbox, pagina_num=pagina_num)
                        else:
                            # Extracción normal con pdfplumber
                            area_recortada = page.crop(bbox)
                            texto = area_recortada.extract_text() or ""

                        if texto:
                            # Sanear el CIF usando el Value Object
                            cif = CIF(texto.strip())
                            metodo = "OCR" if usa_ocr else "directo"
                            print(f"    CIF Cliente extraído ({metodo}): '{texto.strip()}' -> normalizado: '{cif.value}'")
                            return cif.value

                    except Exception as e:
                        print(f"    Error extrayendo CIF_Cliente: {e}")

        except Exception as e:
            print(f"Error en _extraer_cif_cliente: {e}")

        return None

    def _validar_cif_cliente(self, cif_cliente_str: Optional[str]) -> bool:
        """
        Valida que el CIF del cliente coincida con el CIF corporativo.

        Args:
            cif_cliente_str: String con el CIF del cliente extraído del PDF

        Returns:
            True si el CIF coincide con el corporativo, False en caso contrario
        """
        if not cif_cliente_str:
            print(f"    WARN: Factura sin CIF del cliente")
            return False

        cif_cliente = CIF(cif_cliente_str)
        cif_corporativo = CIF(self.CIF_CORPORATIVO)

        if not cif_cliente.is_valid():
            print(f"    WARN: CIF del cliente inválido: '{cif_cliente_str}'")
            return False

        if cif_cliente == cif_corporativo:
            print(f"    OK: CIF del cliente coincide: {cif_cliente.value}")
            return True
        else:
            print(f"    ERROR: CIF del cliente NO coincide. Extraído: '{cif_cliente.value}' vs Esperado: '{cif_corporativo.value}'")
            return False

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
                        print(f"  [INFO] Base ajustada: {base} + {portes} (Portes) = {nueva_base}")
            except (ValueError, TypeError) as e:
                print(f"  [AVISO] No se pudo sumar Portes a Base: {e}")

        # Eliminar campos auxiliares antes de exportar
        if "Portes" in datos_extraidos:
            del datos_extraidos["Portes"]

        return datos_extraidos

    def _aplicar_reglas_asignacion_trimestre_excel(self, datos_factura: Dict[str, Any]) -> None:
        """
        Aplica las reglas de negocio para asignar trimestre/año en la exportación Excel.

        IMPORTANTE: Esta función modifica Trimestre y Año SOLO para el Excel según
        reglas de negocio complejas. NO afecta a índices ni organización de archivos.

        Modifica el diccionario datos_factura in-place:
        - Actualiza campos Trimestre y Año según la lógica de negocio para Excel
        - Si la factura debe excluirse, añade campo _Error

        Args:
            datos_factura (Dict[str, Any]): Diccionario con los datos de la factura
        """
        try:
            # Parsear el trimestre del usuario (de "1T" a 1)
            trimestre_usuario = self.parsear_trimestre(self.trimestre)
            año_usuario = int(self.año)

            # Obtener la fecha de factura
            fecha_factura_str = datos_factura.get('FechaFactura', '')
            if not fecha_factura_str or fecha_factura_str == "ERROR" or fecha_factura_str == "":
                print(f"  WARN: No se pudo determinar trimestre - FechaFactura no válida")
                return

            # Parsear la fecha de factura a datetime
            fecha_factura = self._parsear_fecha_a_datetime(fecha_factura_str, año_usuario)
            if not fecha_factura:
                print(f"  WARN: No se pudo parsear FechaFactura: {fecha_factura_str}")
                return

            # Determinar el trimestre y año que debe asignarse (con lógica de negocio para Excel)
            resultado = self.determinar_trimestre_para_exportacion_excel(fecha_factura, trimestre_usuario, año_usuario)

            if resultado is None:
                # La factura debe excluirse (año diferente y no cumple caso especial T1)
                motivo = f"Factura de {fecha_factura.year} excluida - no corresponde al período solicitado ({self.trimestre} {self.año})"
                datos_factura['_Error'] = motivo
                datos_factura['_Motivo_Rechazo'] = motivo
                print(f"  WARN: {motivo}")
            else:
                # Actualizar trimestre y año según la lógica
                trimestre_asignado, año_asignado = resultado
                datos_factura['Trimestre'] = self.formatear_trimestre(trimestre_asignado)
                datos_factura['Año'] = str(año_asignado)
                print(f"  Trimestre asignado: {datos_factura['Trimestre']} {datos_factura['Año']}")

        except Exception as e:
            print(f"  Error aplicando lógica de trimestres: {e}")

    def _parsear_fecha_a_datetime(self, fecha_str: str, año_default: int) -> Optional[datetime]:
        """
        Parsea una fecha en formato string a datetime.

        Soporta formatos como: "15/01/2025", "15/01", "15-01-2025", etc.
        Si no tiene año, usa el año_default.

        Args:
            fecha_str (str): Fecha en formato string
            año_default (int): Año a usar si la fecha no lo tiene

        Returns:
            Optional[datetime]: Fecha parseada o None si hay error
        """
        if not fecha_str:
            return None

        # Limpiar la fecha
        fecha_str = fecha_str.strip()

        # Intentar varios formatos
        formatos = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%d.%m.%Y',
            '%d/%m/%y',
            '%d-%m-%y',
            '%d/%m',  # Sin año
            '%d-%m',  # Sin año
        ]

        for formato in formatos:
            try:
                fecha = datetime.strptime(fecha_str, formato)
                # Si el formato no incluye año, usar el año default
                if formato in ['%d/%m', '%d-%m']:
                    fecha = fecha.replace(year=año_default)
                # Si el año es de 2 dígitos y es > 50, asumir 19xx, sino 20xx
                elif formato in ['%d/%m/%y', '%d-%m-%y']:
                    if fecha.year > 2050:
                        fecha = fecha.replace(year=fecha.year - 100)
                return fecha
            except ValueError:
                continue

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
        # Solo los 9 campos requeridos por el usuario
        # Limpiar CIF del proveedor usando la clase CIF para eliminar guiones, puntos, etc.
        cif_proveedor_limpio = CIF(plantilla.get('cif_proveedor', '')).value

        # Convertir trimestre a formato numérico (sin "T") para Excel
        trimestre_numerico = str(self.parsear_trimestre(self.trimestre)) if self.trimestre else ''

        datos_factura = {
            'CIF': cif_proveedor_limpio,  # CIF del proveedor limpio (sin guiones ni puntos)
            'FechaFactura': '',
            'Trimestre': trimestre_numerico,
            'Año': self.año,
            'FechaVto': '',
            'NumFactura': '',
            'FechaPago': '',
            'Base': '',
            'ComPaypal': '',
            'Portes': '',  # Campo auxiliar (se suma a Base y se elimina antes de exportar)
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

                # Detectar si el PDF tiene texto extraíble o corrupto
                usa_ocr = False
                if not tiene_texto_extraible(pagina):
                    if self.ocr_disponible:
                        print("  [OCR] PDF sin texto extraíble, usando OCR para extracción...")
                        usa_ocr = True
                        datos_factura['_UsaOCR'] = True
                    else:
                        print("  [AVISO] PDF sin texto extraible y OCR no disponible")
                        raise Exception("PDF escaneado sin OCR disponible")
                elif detectar_texto_corrupto_en_pagina(pagina):
                    # Texto extraíble pero corrupto (códigos CID)
                    if self.ocr_disponible:
                        print("  [OCR] PDF con texto corrupto (códigos CID), usando OCR para extracción...")
                        usa_ocr = True
                        datos_factura['_UsaOCR'] = True
                    else:
                        print("  [AVISO] PDF con texto corrupto y OCR no disponible")
                        raise Exception("PDF con texto corrupto sin OCR disponible")
                else:
                    datos_factura['_UsaOCR'] = False

                campos_extraidos_exitosamente = 0

                for campo in plantilla['campos']:
                    nombre_campo_plantilla = campo['nombre']
                    tipo_campo = campo.get('tipo', 'texto')

                    try:
                        # Detectar si es búsqueda por texto (tipo especial)
                        if tipo_campo == 'busqueda_texto':
                            # Extraer usando búsqueda por regex
                            patron_regex = campo.get('patron_busqueda')
                            if not patron_regex:
                                print(f"  Error: Campo '{nombre_campo_plantilla}' tipo 'busqueda_texto' sin 'patron_busqueda'")
                                texto_extraido = None
                            else:
                                # Área de búsqueda opcional (si no se especifica, busca en toda la página)
                                area_busqueda = campo.get('area_busqueda')
                                if area_busqueda:
                                    area_busqueda = tuple(area_busqueda)

                                # Obtener número de página del campo (default: usar la página actual)
                                num_pagina_campo = campo.get('pagina', 1)

                                # Si el campo especifica una página diferente, cargarla
                                if num_pagina_campo != 1:
                                    # Cargar la página correcta (páginas son 0-indexed en pdfplumber)
                                    if num_pagina_campo <= len(pdf.pages):
                                        pagina_busqueda = pdf.pages[num_pagina_campo - 1]
                                    else:
                                        print(f"  Advertencia: página {num_pagina_campo} no existe, usando página 1")
                                        pagina_busqueda = pagina
                                        num_pagina_campo = 1
                                else:
                                    pagina_busqueda = pagina

                                # Realizar búsqueda por texto
                                texto_extraido = self._buscar_texto_en_pdf(
                                    pdf_page=pagina_busqueda,
                                    patron_regex=patron_regex,
                                    area_busqueda=area_busqueda,
                                    ruta_pdf=ruta_pdf,
                                    pagina_num=num_pagina_campo,
                                    usa_ocr=usa_ocr
                                )

                            # Para búsqueda de texto, determinar el tipo real para limpieza
                            # Puede especificarse como "tipo_dato" en la plantilla
                            tipo_dato = campo.get('tipo_dato', 'texto')
                            valor_procesado = self.procesar_campo(texto_extraido, tipo_dato)

                        else:
                            # Extracción normal por coordenadas
                            coordenadas = campo.get('coordenadas')
                            if not coordenadas:
                                print(f"  Error: Campo '{nombre_campo_plantilla}' sin coordenadas")
                                texto_extraido = None
                            else:
                                bbox = tuple(coordenadas)  # (x1, y1, x2, y2)

                                # Obtener número de página del campo (default: página 1)
                                num_pagina_campo = campo.get('pagina', 1)

                                # Si el campo especifica una página diferente, cargarla
                                if num_pagina_campo != 1:
                                    if num_pagina_campo <= len(pdf.pages):
                                        pagina_extraccion = pdf.pages[num_pagina_campo - 1]
                                    else:
                                        print(f"  Advertencia: página {num_pagina_campo} no existe, usando página 1")
                                        pagina_extraccion = pagina
                                        num_pagina_campo = 1
                                else:
                                    pagina_extraccion = pagina

                                if usa_ocr:
                                    # Usar OCR para extraer de área específica
                                    texto_extraido = self.ocr.extraer_texto_area(ruta_pdf, bbox, pagina_num=num_pagina_campo)
                                else:
                                    # Extracción normal con pdfplumber
                                    area_recortada = pagina_extraccion.crop(bbox)
                                    texto_extraido = area_recortada.extract_text()

                            # Limpiar y procesar según tipo
                            valor_procesado = self.procesar_campo(texto_extraido, tipo_campo)

                        # Mapear nombre de campo de plantilla a nombre de columna estándar
                        nombre_columna = self.MAPEO_CAMPOS.get(nombre_campo_plantilla, nombre_campo_plantilla)

                        # Limpieza adicional específica para NumFactura: eliminar todos los espacios
                        if nombre_columna == 'NumFactura' and valor_procesado:
                            valor_procesado = DataCleaner.clean_invoice_number(valor_procesado)

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

                # Validar que la plantilla tenga el campo CIF_Cliente definido
                tiene_campo_cif_cliente = any(
                    campo.get('nombre') == 'CIF_Cliente'
                    for campo in plantilla.get('campos', [])
                )

                if tiene_campo_cif_cliente:
                    # Solo validar si la plantilla tiene el campo CIF_Cliente
                    print("  Verificando CIF del cliente...")
                    cif_cliente = self._extraer_cif_cliente(pdf, plantilla, ruta_pdf=ruta_pdf, usa_ocr=usa_ocr)

                    # Guardar CIF del cliente como campo interno (no se exporta)
                    datos_factura['_CIF_Cliente'] = cif_cliente if cif_cliente else ""

                    # Validar CIF del cliente
                    if not self._validar_cif_cliente(cif_cliente):
                        # Marcar factura como rechazada por CIF incorrecto
                        datos_factura['_CIF_Valido'] = False
                        motivo = f"CIF del cliente no coincide con el corporativo ({self.CIF_CORPORATIVO})"
                        datos_factura['_Motivo_Rechazo'] = motivo
                        datos_factura['_Error'] = motivo  # Añadir campo _Error para que se filtre automáticamente
                        print(f"  WARN: Factura rechazada - CIF cliente incorrecto")
                    else:
                        datos_factura['_CIF_Valido'] = True
                else:
                    # Plantilla sin CIF_Cliente: permitir procesamiento sin validación
                    print(f"  INFO: Plantilla sin campo CIF_Cliente - omitiendo validación")
                    datos_factura['_CIF_Valido'] = None

                # Aplicar reglas de asignación de trimestre para Excel
                if self.trimestre and self.año:
                    self._aplicar_reglas_asignacion_trimestre_excel(datos_factura)

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

            # Variable para almacenar si se usó LLM
            uso_llm = False
            lista_datos = None

            if proveedor_id:
                try:
                    # Usar método multipágina que extrae de la última página de cada factura
                    lista_datos = self.extraer_datos_factura_multipagina(ruta_completa, proveedor_id)
                    self.metricas['extracciones_template'] += 1

                except Exception as e:
                    print(f"ERROR procesando con plantilla: {e}")

                    # FALLBACK: Intentar con LLM si está disponible
                    if self.llm_extractor:
                        print(f"  [FALLBACK] Intentando extracción con LLM...")
                        try:
                            datos_llm = self.llm_extractor.extraer_datos(ruta_completa)
                            # Agregar trimestre y año del usuario
                            datos_llm['Trimestre'] = str(self.parsear_trimestre(self.trimestre)) if self.trimestre else datos_llm.get('Trimestre', '')
                            datos_llm['Año'] = self.año if self.año else datos_llm.get('Año', '')
                            lista_datos = [datos_llm]
                            uso_llm = True
                            self.metricas['fallbacks_activados'] += 1
                            self.metricas['extracciones_llm'] += 1
                            print(f"  [FALLBACK] [OK] Extraccion con LLM exitosa")
                        except Exception as e_llm:
                            print(f"  [FALLBACK] [ERROR] Error con LLM: {e_llm}")
                            # Registrar error
                            error_registro = {
                                'Archivo': archivo_pdf,
                                'Pagina': 'N/A',
                                'Error': f'Error con plantilla Y con LLM: {str(e)} | {str(e_llm)}',
                                'Proveedor': proveedor_id,
                                'Fecha_Procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            self.errores.append(error_registro)
                            if self.organizador:
                                self.organizador.organizar_pdf(ruta_completa, None)
                            continue
                    else:
                        # Sin LLM fallback disponible, registrar error
                        error_registro = {
                            'Archivo': archivo_pdf,
                            'Pagina': 'N/A',
                            'Error': f'Error al procesar factura: {str(e)}',
                            'Proveedor': proveedor_id,
                            'Fecha_Procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        self.errores.append(error_registro)
                        if self.organizador:
                            self.organizador.organizar_pdf(ruta_completa, None)
                        continue

            else:
                # No se identificó proveedor (no hay plantilla)
                # FALLBACK: Usar LLM si está disponible
                if self.llm_extractor:
                    print(f"  Proveedor no identificado, usando LLM...")
                    try:
                        datos_llm = self.llm_extractor.extraer_datos(ruta_completa)
                        # Agregar trimestre y año del usuario
                        datos_llm['Trimestre'] = str(self.parsear_trimestre(self.trimestre)) if self.trimestre else datos_llm.get('Trimestre', '')
                        datos_llm['Año'] = self.año if self.año else datos_llm.get('Año', '')
                        lista_datos = [datos_llm]
                        uso_llm = True
                        self.metricas['proveedores_sin_plantilla'] += 1
                        self.metricas['extracciones_llm'] += 1
                        print(f"  [LLM] [OK] Extraccion exitosa (proveedor sin plantilla)")
                    except Exception as e_llm:
                        print(f"  [LLM] [ERROR] Error: {e_llm}")
                        error_registro = {
                            'Archivo': archivo_pdf,
                            'Pagina': 'N/A',
                            'Error': f'Proveedor no identificado y error con LLM: {str(e_llm)}',
                            'Proveedor': 'NO_IDENTIFICADO',
                            'Fecha_Procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        self.errores.append(error_registro)
                        if self.organizador:
                            self.organizador.organizar_pdf(ruta_completa, None)
                        continue
                else:
                    # Sin plantilla y sin LLM disponible
                    print(f"ERROR Proveedor no identificado (sin LLM fallback)")
                    error_registro = {
                        'Archivo': archivo_pdf,
                        'Pagina': 'N/A',
                        'Error': 'Proveedor no identificado - no hay plantilla que coincida',
                        'Proveedor': 'NO_IDENTIFICADO',
                        'Fecha_Procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.errores.append(error_registro)
                    if self.organizador:
                        self.organizador.organizar_pdf(ruta_completa, None)
                    continue

            # Procesar cada factura extraída (ya sea por template o LLM)
            if lista_datos:
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
                        datos['_Duplicado'] = True
                        datos['_Motivo_Duplicado'] = f"Ya existe factura con mismo CIF, NumFactura y FechaFactura"
                    else:
                        facturas_procesadas.add(clave_duplicado)
                        datos['_Duplicado'] = False

                    resultados.append(datos)
                    self.metricas['total_procesadas'] += 1

                metodo = "LLM" if uso_llm else "template"
                print(f"OK Procesado exitosamente con {metodo} ({len(lista_datos)} factura(s))")

                # Organizar archivo PDF si está habilitado
                if self.organizador:
                    datos_para_organizar = lista_datos[0] if lista_datos else None
                    self.organizador.organizar_pdf(ruta_completa, datos_para_organizar)

        self.resultados = resultados
        print(f"\n=== PROCESAMIENTO COMPLETADO ===")
        print(f"Total facturas procesadas: {len(resultados)}")

        # Mostrar métricas de uso si LLM está habilitado
        if self.usar_llm_fallback and self.metricas['total_procesadas'] > 0:
            self._mostrar_metricas()

        return resultados

    def _mostrar_metricas(self):
        """Muestra métricas de uso de templates vs LLM."""
        print(f"\n=== MÉTRICAS DE EXTRACCIÓN ===")
        print(f"Total procesadas: {self.metricas['total_procesadas']}")
        print(f"  • Con template (coordenadas): {self.metricas['extracciones_template']}")
        print(f"  • Con LLM (IA): {self.metricas['extracciones_llm']}")
        print(f"  • Fallbacks activados: {self.metricas['fallbacks_activados']}")
        print(f"  • Proveedores sin plantilla: {self.metricas['proveedores_sin_plantilla']}")

        if self.metricas['total_procesadas'] > 0:
            pct_template = (self.metricas['extracciones_template'] / self.metricas['total_procesadas']) * 100
            pct_llm = (self.metricas['extracciones_llm'] / self.metricas['total_procesadas']) * 100
            print(f"\nDistribución: {pct_template:.1f}% template | {pct_llm:.1f}% LLM")

            # Estimación de costos (asumiendo $0.0025 por factura con GPT-4o mini)
            costo_estimado = self.metricas['extracciones_llm'] * 0.0025
            print(f"Costo estimado API: ${costo_estimado:.4f}")

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

    def extraer_num_factura_de_pagina(self, pagina, plantilla: Dict, ruta_pdf: str = None,
                                       pagina_num: int = None, usa_ocr: bool = False) -> Optional[str]:
        """
        Extrae el número de factura de una página específica según la plantilla.

        Args:
            pagina: Objeto página de pdfplumber
            plantilla (Dict): Plantilla del proveedor
            ruta_pdf (str): Ruta al archivo PDF (requerido si usa_ocr=True)
            pagina_num (int): Número de página 1-indexed (requerido si usa_ocr=True)
            usa_ocr (bool): Si True, usa OCR para extraer texto

        Returns:
            Optional[str]: Número de factura o None si no se encuentra
        """
        # Buscar el campo NumFactura en la plantilla
        for campo in plantilla.get('campos', []):
            nombre_campo = campo['nombre']

            # Verificar si es el campo NumFactura (puede estar con varios nombres)
            nombre_mapeado = self.MAPEO_CAMPOS.get(nombre_campo, nombre_campo)

            if nombre_mapeado == 'NumFactura':
                # Si el campo especifica una página, solo extraer de esa página
                pagina_especifica = campo.get('pagina')
                if pagina_especifica is not None and pagina_num is not None:
                    if pagina_num != pagina_especifica:
                        # No es la página correcta, retornar None
                        return None

                try:
                    coordenadas = campo['coordenadas']
                    bbox = tuple(coordenadas)

                    if usa_ocr:
                        # Usar OCR para extraer texto
                        if not ruta_pdf or pagina_num is None:
                            print("  Error: ruta_pdf y pagina_num son requeridos para OCR")
                            return None
                        texto_extraido = self.ocr.extraer_texto_area(ruta_pdf, bbox, pagina_num=pagina_num)
                    else:
                        # Extracción normal con pdfplumber
                        area_recortada = pagina.crop(bbox)
                        texto_extraido = area_recortada.extract_text()

                    if texto_extraido:
                        # Limpiar y procesar el número de factura (eliminar todos los espacios)
                        num_factura = DataCleaner.clean_invoice_number(texto_extraido)

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
            'sin número',
            'importe',
            'ación',
            'descripción',
            'cantidad',
            'precio',
            'concepto',
            'detalle',
            'base',
            'iva',
        ]

        # Si contiene alguna palabra inválida, no es válido
        for palabra in palabras_invalidas:
            if palabra in texto_lower:
                return False

        # Validar que contenga al menos un dígito o caracteres típicos de facturas
        # Los números de factura típicamente incluyen números, letras, guiones, barras
        tiene_numero = bool(re.search(r'\d', num_factura))
        tiene_letra_o_numero = bool(re.search(r'[a-zA-Z0-9]', num_factura))

        # Debe tener al menos un número Y (letras o números)
        if not (tiene_numero and tiene_letra_o_numero):
            return False

        # Rechazar si es solo texto sin formato de factura
        # Un número de factura válido debería tener números y posiblemente letras/símbolos
        # pero no ser solo palabras sueltas
        palabras = re.findall(r'[a-záéíóúñ]{4,}', texto_lower)
        if len(palabras) > 0:
            # Si tiene palabras largas (4+ letras), probablemente no es un número de factura
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

                # Detectar si el PDF tiene texto extraíble o corrupto (usar primera página como muestra)
                usa_ocr = False
                if not tiene_texto_extraible(pdf.pages[0]):
                    if self.ocr_disponible:
                        print("  [OCR] PDF sin texto extraíble, usando OCR para extracción multipágina...")
                        usa_ocr = True
                    else:
                        print("  [AVISO] PDF sin texto extraible y OCR no disponible")
                        raise Exception("PDF escaneado sin OCR disponible")
                elif detectar_texto_corrupto_en_pagina(pdf.pages[0]):
                    # Texto extraíble pero corrupto (códigos CID)
                    if self.ocr_disponible:
                        print("  [OCR] PDF con texto corrupto (códigos CID), usando OCR para extracción...")
                        usa_ocr = True
                    else:
                        print("  [AVISO] PDF con texto corrupto y OCR no disponible")
                        raise Exception("PDF con texto corrupto sin OCR disponible")

                # Paso 1: Extraer NumFactura de cada página
                print(f"  Analizando {len(pdf.pages)} página(s)...")
                paginas_data = []

                for i, pagina in enumerate(pdf.pages):
                    num_factura = self.extraer_num_factura_de_pagina(
                        pagina, plantilla,
                        ruta_pdf=ruta_pdf,
                        pagina_num=i+1,  # 1-indexed
                        usa_ocr=usa_ocr
                    )
                    paginas_data.append({
                        'pagina_num': i,
                        'NumFactura': num_factura,
                        'page_obj': pagina
                    })
                    metodo = "OCR" if usa_ocr else "directo"
                    if num_factura:
                        print(f"    Página {i+1}: NumFactura = {num_factura} ({metodo})")
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

                    # Limpiar CIF del proveedor usando la clase CIF para eliminar guiones, puntos, etc.
                    cif_proveedor_limpio = CIF(plantilla.get('cif_proveedor', '')).value

                    # Convertir trimestre a formato numérico (sin "T") para Excel
                    trimestre_numerico = str(self.parsear_trimestre(self.trimestre)) if self.trimestre else ''

                    # Extraer datos de la última página
                    datos_factura = {
                        'CIF': cif_proveedor_limpio,  # CIF del proveedor limpio (sin guiones ni puntos)
                        'FechaFactura': '',
                        'Trimestre': trimestre_numerico,
                        'Año': self.año,
                        'FechaVto': '',
                        'NumFactura': num_factura,
                        'FechaPago': '',
                        'Base': '',
                        'ComPaypal': '',
                        'Portes': '',  # Campo auxiliar (se suma a Base y se elimina antes de exportar)
                    }

                    # Metadatos adicionales
                    datos_factura['_Archivo'] = os.path.basename(ruta_pdf)
                    datos_factura['_Proveedor_Nombre'] = plantilla.get('nombre_proveedor', '')
                    datos_factura['_Pagina'] = num_pagina + 1
                    datos_factura['_Total_Paginas'] = len(paginas_grupo)
                    datos_factura['_Fecha_Procesamiento'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    datos_factura['_UsaOCR'] = usa_ocr

                    campos_extraidos_exitosamente = 0

                    # Extraer todos los campos (respetando la página especificada en cada campo)
                    for campo in plantilla['campos']:
                        nombre_campo_plantilla = campo['nombre']
                        tipo_campo = campo.get('tipo', 'texto')

                        try:
                            # Determinar qué página usar para este campo
                            # Si el campo especifica una página, usarla; si no, usar la última página del grupo
                            pagina_campo = campo.get('pagina', None)

                            if pagina_campo is not None:
                                # El campo especifica una página específica (1-indexed)
                                if pagina_campo > len(pdf.pages) or pagina_campo < 1:
                                    print(f"    Error: Campo '{nombre_campo_plantilla}' especifica página {pagina_campo} que no existe (PDF tiene {len(pdf.pages)} páginas)")
                                    texto_extraido = None
                                    valor_procesado = ""
                                else:
                                    # Usar la página especificada
                                    pagina_a_usar = pdf.pages[pagina_campo - 1]
                                    num_pagina_a_usar = pagina_campo - 1  # 0-indexed
                            else:
                                # No especifica página, usar la última página del grupo
                                pagina_a_usar = pagina
                                num_pagina_a_usar = num_pagina

                            # Detectar si es búsqueda por texto (tipo especial)
                            if tipo_campo == 'busqueda_texto':
                                # Extraer usando búsqueda por regex
                                patron_regex = campo.get('patron_busqueda')
                                if not patron_regex:
                                    print(f"    Error: Campo '{nombre_campo_plantilla}' tipo 'busqueda_texto' sin 'patron_busqueda'")
                                    texto_extraido = None
                                else:
                                    # Área de búsqueda opcional (si no se especifica, busca en toda la página)
                                    area_busqueda = campo.get('area_busqueda')
                                    if area_busqueda:
                                        area_busqueda = tuple(area_busqueda)

                                    # Realizar búsqueda por texto
                                    texto_extraido = self._buscar_texto_en_pdf(
                                        pdf_page=pagina_a_usar,
                                        patron_regex=patron_regex,
                                        area_busqueda=area_busqueda,
                                        ruta_pdf=ruta_pdf,
                                        pagina_num=num_pagina_a_usar+1,
                                        usa_ocr=usa_ocr
                                    )

                                # Para búsqueda de texto, determinar el tipo real para limpieza
                                tipo_dato = campo.get('tipo_dato', 'texto')
                                valor_procesado = self.procesar_campo(texto_extraido, tipo_dato)

                            else:
                                # Extracción normal por coordenadas
                                coordenadas = campo.get('coordenadas')
                                if not coordenadas:
                                    print(f"    Error: Campo '{nombre_campo_plantilla}' sin coordenadas")
                                    texto_extraido = None
                                else:
                                    bbox = tuple(coordenadas)

                                    if usa_ocr:
                                        # Usar OCR para extraer de área específica
                                        texto_extraido = self.ocr.extraer_texto_area(
                                            ruta_pdf, bbox, pagina_num=num_pagina_a_usar+1
                                        )
                                    else:
                                        # Extracción normal con pdfplumber
                                        area_recortada = pagina_a_usar.crop(bbox)
                                        texto_extraido = area_recortada.extract_text()

                                # Limpiar y procesar según tipo
                                valor_procesado = self.procesar_campo(texto_extraido, tipo_campo)

                            # Mapear nombre de campo
                            nombre_columna = self.MAPEO_CAMPOS.get(nombre_campo_plantilla, nombre_campo_plantilla)

                            # Limpieza adicional específica para NumFactura: eliminar todos los espacios
                            if nombre_columna == 'NumFactura' and valor_procesado:
                                valor_procesado = DataCleaner.clean_invoice_number(valor_procesado)

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

                    # Validar que la plantilla tenga el campo CIF_Cliente definido
                    tiene_campo_cif_cliente = any(
                        campo.get('nombre') == 'CIF_Cliente'
                        for campo in plantilla.get('campos', [])
                    )

                    if tiene_campo_cif_cliente:
                        # Solo validar si la plantilla tiene el campo CIF_Cliente
                        print("    Verificando CIF del cliente...")
                        cif_cliente = self._extraer_cif_cliente(pdf, plantilla, ruta_pdf=ruta_pdf, usa_ocr=usa_ocr)

                        # Guardar CIF del cliente como campo interno (no se exporta)
                        datos_factura['_CIF_Cliente'] = cif_cliente if cif_cliente else ""

                        # Validar CIF del cliente
                        if not self._validar_cif_cliente(cif_cliente):
                            # Marcar factura como rechazada por CIF incorrecto
                            datos_factura['_CIF_Valido'] = False
                            motivo = f"CIF del cliente no coincide con el corporativo ({self.CIF_CORPORATIVO})"
                            datos_factura['_Motivo_Rechazo'] = motivo
                            datos_factura['_Error'] = motivo  # Añadir campo _Error para que se filtre automáticamente
                            print(f"    WARN: Factura rechazada - CIF cliente incorrecto")
                        else:
                            datos_factura['_CIF_Valido'] = True
                    else:
                        # Plantilla sin CIF_Cliente: permitir procesamiento sin validación
                        print(f"    INFO: Plantilla sin campo CIF_Cliente - omitiendo validación")
                        datos_factura['_CIF_Valido'] = None

                    # Aplicar reglas de asignación de trimestre para Excel
                    if self.trimestre and self.año:
                        self._aplicar_reglas_asignacion_trimestre_excel(datos_factura)

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