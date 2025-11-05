"""
Módulo de extracción de datos de facturas usando LLMs (GPT-4o).

Este módulo proporciona extracción automática de datos de facturas
sin necesidad de plantillas con coordenadas. Se usa como fallback
cuando no existe plantilla o cuando la plantilla falla.
"""

import os
import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime
from pdf2image import convert_from_path
import platform

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class LLMExtractor:
    """
    Extractor de datos de facturas usando modelos LLM (GPT-4o).

    Características:
    - No requiere plantillas con coordenadas
    - Adaptación automática a cualquier formato de factura
    - Soporte para facturas en español
    - Extracción de campos estándar del sistema
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Inicializa el extractor LLM.

        Args:
            api_key: API key de OpenAI. Si no se proporciona, se busca en variable de entorno OPENAI_API_KEY
            model: Modelo a usar ('gpt-4o-mini' recomendado por costo/calidad)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI no está instalado. Instala con: pip install openai"
            )

        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "API key de OpenAI no encontrada. "
                "Proporciona api_key o establece variable de entorno OPENAI_API_KEY"
            )

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

        # Configurar ruta de Poppler (necesario para pdf2image)
        sistema = platform.system()
        if sistema == "Darwin":  # macOS
            self.poppler_path = "/opt/homebrew/bin"
        elif sistema == "Windows":
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.poppler_path = os.path.join(project_root, "poppler", "Library", "bin")
        else:
            self.poppler_path = None

    def extraer_datos(self, ruta_pdf: str) -> Dict[str, Any]:
        """
        Extrae datos de una factura PDF usando LLM.

        Args:
            ruta_pdf: Ruta al archivo PDF de la factura

        Returns:
            Diccionario con los datos extraídos en formato estándar:
            {
                'CIF': str,
                'FechaFactura': str (DD/MM/YYYY),
                'Trimestre': str,
                'Año': str,
                'FechaVto': str (DD/MM/YYYY),
                'NumFactura': str,
                'FechaPago': str,
                'Base': str,
                'ComPaypal': str,
                '_metodo': 'llm',
                '_confianza': float (0-1),
                '_modelo': str
            }

        Raises:
            Exception: Si hay error en la extracción
        """
        print(f"[LLM] Extrayendo datos de: {os.path.basename(ruta_pdf)}")

        try:
            # Paso 1: Convertir PDF a imagen (GPT-4o vision necesita imagen)
            imagenes = convert_from_path(
                ruta_pdf,
                dpi=150,  # Suficiente para LLM
                first_page=1,
                last_page=1,  # Solo primera página
                poppler_path=self.poppler_path
            )

            if not imagenes:
                raise Exception("No se pudo convertir PDF a imagen")

            imagen = imagenes[0]

            # Paso 2: Convertir imagen a base64
            from io import BytesIO
            buffer = BytesIO()
            imagen.save(buffer, format='PNG')
            imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # Paso 3: Preparar prompt optimizado
            prompt = self._crear_prompt_extraccion()

            # Paso 4: Llamar a API de OpenAI
            print(f"[LLM] Llamando a {self.model}...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto extractor de datos de facturas. Respondes ÚNICAMENTE con JSON válido, sin explicaciones adicionales."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{imagen_base64}",
                                    "detail": "high"  # Alta resolución para mejor lectura
                                }
                            }
                        ]
                    }
                ],
                temperature=0,  # Máxima reproducibilidad
                max_tokens=1000
            )

            # Paso 5: Parsear respuesta JSON
            contenido = response.choices[0].message.content.strip()

            # Limpiar posibles marcadores de código markdown
            if contenido.startswith('```json'):
                contenido = contenido[7:]  # Remover ```json
            if contenido.startswith('```'):
                contenido = contenido[3:]  # Remover ```
            if contenido.endswith('```'):
                contenido = contenido[:-3]  # Remover ```
            contenido = contenido.strip()

            datos = json.loads(contenido)

            # Paso 6: Validar y normalizar datos
            datos_normalizados = self._normalizar_datos(datos, ruta_pdf)

            # Agregar metadatos del LLM
            datos_normalizados['_metodo'] = 'llm'
            datos_normalizados['_modelo'] = self.model
            datos_normalizados['_confianza'] = self._calcular_confianza(datos_normalizados)

            print(f"[LLM] ✓ Extracción completada (confianza: {datos_normalizados['_confianza']:.2f})")

            return datos_normalizados

        except json.JSONDecodeError as e:
            print(f"[LLM] ✗ Error parseando JSON: {e}")
            print(f"[LLM] Respuesta recibida: {contenido[:200]}...")
            raise Exception(f"LLM retornó JSON inválido: {e}")

        except Exception as e:
            print(f"[LLM] ✗ Error en extracción: {e}")
            raise

    def _crear_prompt_extraccion(self) -> str:
        """Crea el prompt optimizado para extracción de facturas."""
        return """Extrae la siguiente información de esta factura española y devuélvela en formato JSON:

{
  "CIF": "CIF o NIF del proveedor/emisor de la factura (ej: B12345678)",
  "NombreProveedor": "Nombre o razón social del proveedor",
  "FechaFactura": "Fecha de la factura en formato DD/MM/YYYY",
  "NumFactura": "Número de factura completo (ej: F-2025/001, FAC123, etc.)",
  "Base": "Base imponible SIN IVA (solo número, sin símbolos)",
  "FechaVto": "Fecha de vencimiento en formato DD/MM/YYYY (o cadena vacía si no existe)",
  "Total": "Importe total CON IVA (para validación, opcional)"
}

REGLAS IMPORTANTES:
1. Devuelve SOLO el JSON, sin texto adicional antes o después
2. Si un campo no existe o no se puede leer, usa cadena vacía ""
3. Para Base: extrae SOLO el número, sin €, sin moneda, sin puntos de miles
4. Para fechas: SIEMPRE formato DD/MM/YYYY (ej: 15/10/2025)
5. Si la fecha está en formato texto (ej: "1 de octubre de 2025"), conviértela a DD/MM/YYYY
6. NumFactura: incluye prefijos, barras, guiones (todo el identificador completo)
7. CIF: debe ser el del EMISOR (proveedor), no el del cliente/destinatario
8. Valores numéricos: solo dígitos y punto decimal (ej: "1234.56", no "1.234,56 €")

EJEMPLO DE RESPUESTA:
{
  "CIF": "B98765432",
  "NombreProveedor": "Distribuciones ABC S.L.",
  "FechaFactura": "15/10/2025",
  "NumFactura": "F-2025/0158",
  "Base": "1250.00",
  "FechaVto": "15/11/2025",
  "Total": "1512.50"
}"""

    def _normalizar_datos(self, datos: Dict[str, Any], ruta_pdf: str) -> Dict[str, Any]:
        """
        Normaliza los datos extraídos al formato estándar del sistema.

        Args:
            datos: Datos crudos del LLM
            ruta_pdf: Ruta del PDF (para logging)

        Returns:
            Datos en formato estándar con todos los campos requeridos
        """
        # Extraer año y calcular trimestre de la fecha
        fecha_factura = datos.get('FechaFactura', '')
        año = ''
        trimestre = ''

        if fecha_factura and '/' in fecha_factura:
            try:
                # Formato DD/MM/YYYY
                partes = fecha_factura.split('/')
                if len(partes) == 3:
                    dia, mes, año_str = partes
                    año = año_str
                    mes_num = int(mes)

                    # Calcular trimestre
                    if mes_num <= 3:
                        trimestre = '1'
                    elif mes_num <= 6:
                        trimestre = '2'
                    elif mes_num <= 9:
                        trimestre = '3'
                    else:
                        trimestre = '4'
            except:
                pass

        # Construir datos normalizados
        datos_normalizados = {
            'CIF': datos.get('CIF', '').strip().upper(),
            'FechaFactura': fecha_factura,
            'Trimestre': trimestre,
            'Año': año,
            'FechaVto': datos.get('FechaVto', ''),
            'NumFactura': datos.get('NumFactura', '').strip(),
            'FechaPago': '',  # No se extrae por LLM (campo interno)
            'Base': datos.get('Base', '').strip(),
            'ComPaypal': '',  # No se extrae por LLM (campo interno)

            # Metadatos adicionales
            '_NombreProveedor': datos.get('NombreProveedor', ''),
            '_Total': datos.get('Total', ''),
            '_Archivo': os.path.basename(ruta_pdf),
        }

        return datos_normalizados

    def _calcular_confianza(self, datos: Dict[str, Any]) -> float:
        """
        Calcula un score de confianza (0-1) basado en campos completos.

        Args:
            datos: Datos extraídos

        Returns:
            Score de confianza entre 0 y 1
        """
        # Campos críticos que deben estar presentes
        campos_criticos = ['CIF', 'FechaFactura', 'NumFactura', 'Base']
        campos_completos = sum(1 for campo in campos_criticos if datos.get(campo))

        # Campos opcionales que suman puntos bonus
        campos_opcionales = ['FechaVto', '_NombreProveedor', 'Trimestre', 'Año']
        campos_opcionales_completos = sum(1 for campo in campos_opcionales if datos.get(campo))

        # Score: 70% por críticos, 30% por opcionales
        score_critico = (campos_completos / len(campos_criticos)) * 0.7
        score_opcional = (campos_opcionales_completos / len(campos_opcionales)) * 0.3

        return score_critico + score_opcional


def extraer_con_llm(ruta_pdf: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Función de conveniencia para extraer datos usando LLM.

    Args:
        ruta_pdf: Ruta al PDF de la factura
        api_key: API key de OpenAI (opcional, se busca en variable de entorno)

    Returns:
        Diccionario con datos extraídos

    Raises:
        Exception: Si hay error en la extracción
    """
    extractor = LLMExtractor(api_key=api_key)
    return extractor.extraer_datos(ruta_pdf)
