"""
Módulo para organizar archivos PDF procesados según su estado:
- Facturas procesadas exitosamente → organizadas por fecha (mes) y proveedor
- PDFs duplicados → carpeta de duplicados por trimestre
- PDFs con errores → clasificados por tipo de error (posible factura vs no factura)
"""

import os
import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pdfplumber


# Palabras clave para detectar si un PDF sin plantilla podría ser una factura
PALABRAS_FACTURA = [
    'factura', 'invoice', 'bill', 'receipt',
    'cif', 'nif', 'vat', 'tax',
    'iva', 'base imponible', 'total', 'subtotal',
    'fecha factura', 'número factura', 'numero factura',
    'proveedor', 'cliente', 'supplier', 'customer',
    'importe', 'amount', 'precio', 'price'
]

# Umbral de palabras clave para considerar que es una factura
UMBRAL_PALABRAS_FACTURA = 3


class PDFOrganizer:
    """
    Clase para organizar PDFs procesados en carpetas según su estado y resultado.
    Mantiene un índice de facturas procesadas por trimestre para detectar duplicados.
    """

    def __init__(self, directorio_base: str = "facturas"):
        """
        Inicializa el organizador de PDFs.

        Args:
            directorio_base: Directorio raíz donde están las facturas (default: "facturas")
        """
        self.directorio_base = Path(directorio_base)
        self.directorio_procesadas = self.directorio_base / "procesadas"
        self.directorio_indices = self.directorio_procesadas / "indices"
        self.directorio_duplicados = self.directorio_base / "duplicados"
        self.directorio_errores = self.directorio_base / "errores"
        self.directorio_logs = Path("logs")

        # Crear estructura de carpetas si no existe
        self._crear_estructura_carpetas()

    def _crear_estructura_carpetas(self):
        """Crea la estructura de carpetas necesaria para organizar los PDFs"""
        # Carpetas principales
        self.directorio_procesadas.mkdir(parents=True, exist_ok=True)
        self.directorio_indices.mkdir(parents=True, exist_ok=True)
        self.directorio_duplicados.mkdir(parents=True, exist_ok=True)
        self.directorio_errores.mkdir(parents=True, exist_ok=True)
        self.directorio_logs.mkdir(parents=True, exist_ok=True)

        # Subcarpetas de errores
        (self.directorio_errores / "sin_plantilla_posible_factura").mkdir(parents=True, exist_ok=True)
        (self.directorio_errores / "probablemente_no_factura").mkdir(parents=True, exist_ok=True)

    def cargar_indice(self, año: int, trimestre: str) -> Dict:
        """
        Carga el índice de facturas de un trimestre específico.

        Args:
            año: Año del trimestre (ej: 2025)
            trimestre: Trimestre (1T, 2T, 3T, 4T)

        Returns:
            Diccionario con el índice de facturas del trimestre
        """
        archivo_indice = self.directorio_indices / f"indice_{año}_{trimestre}.json"

        if archivo_indice.exists():
            try:
                with open(archivo_indice, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ ADVERTENCIA: Error al cargar índice {archivo_indice}: {e}")
                return self._crear_indice_vacio(año, trimestre)
        else:
            return self._crear_indice_vacio(año, trimestre)

    def _crear_indice_vacio(self, año: int, trimestre: str) -> Dict:
        """Crea un índice vacío para un trimestre"""
        return {
            "trimestre": trimestre,
            "año": año,
            "facturas": []
        }

    def guardar_indice(self, año: int, trimestre: str, datos: Dict):
        """
        Guarda el índice de facturas de un trimestre.

        Args:
            año: Año del trimestre
            trimestre: Trimestre (1T, 2T, 3T, 4T)
            datos: Diccionario con los datos del índice
        """
        archivo_indice = self.directorio_indices / f"indice_{año}_{trimestre}.json"

        try:
            with open(archivo_indice, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"❌ ERROR: No se pudo guardar índice {archivo_indice}: {e}")

    def es_duplicado(self, cif_proveedor: str, fecha_factura: str,
                    num_factura: str, año: int, trimestre: str) -> Optional[Dict]:
        """
        Verifica si una factura ya existe en el índice del trimestre.

        Args:
            cif_proveedor: CIF del proveedor
            fecha_factura: Fecha de la factura (formato YYYY-MM-DD o DD/MM/YYYY)
            num_factura: Número de factura
            año: Año del trimestre
            trimestre: Trimestre (1T, 2T, 3T, 4T)

        Returns:
            Diccionario con info de la factura existente si es duplicado, None si no existe
        """
        indice = self.cargar_indice(año, trimestre)

        # Normalizar fecha para comparación
        fecha_normalizada = self._normalizar_fecha(fecha_factura)

        for factura in indice.get("facturas", []):
            if (factura.get("cif_proveedor") == cif_proveedor and
                self._normalizar_fecha(factura.get("fecha_factura", "")) == fecha_normalizada and
                factura.get("num_factura") == num_factura):
                return factura

        return None

    def _normalizar_fecha(self, fecha: str) -> str:
        """
        Normaliza una fecha a formato YYYY-MM-DD para comparación.

        Args:
            fecha: Fecha en formato DD/MM/YYYY o YYYY-MM-DD

        Returns:
            Fecha en formato YYYY-MM-DD
        """
        if not fecha:
            return ""

        # Si ya está en formato YYYY-MM-DD
        if '-' in fecha and len(fecha.split('-')[0]) == 4:
            return fecha

        # Si está en formato DD/MM/YYYY
        if '/' in fecha:
            try:
                parts = fecha.split('/')
                if len(parts) == 3:
                    return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            except:
                pass

        return fecha

    def agregar_al_indice(self, año: int, trimestre: str, info_factura: Dict):
        """
        Agrega una nueva factura al índice del trimestre.

        Args:
            año: Año del trimestre
            trimestre: Trimestre (1T, 2T, 3T, 4T)
            info_factura: Diccionario con información de la factura
        """
        indice = self.cargar_indice(año, trimestre)
        indice["facturas"].append(info_factura)
        self.guardar_indice(año, trimestre, indice)

    def analizar_contenido_pdf(self, pdf_path: str) -> Tuple[bool, int]:
        """
        Analiza el contenido de un PDF para determinar si parece una factura.
        Busca palabras clave relacionadas con facturas.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Tupla (es_probable_factura, num_palabras_encontradas)
        """
        palabras_encontradas = 0

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Analizar todas las páginas (máximo 5 para no ser muy lento)
                for i, pagina in enumerate(pdf.pages[:5]):
                    texto = pagina.extract_text()
                    if texto:
                        texto_lower = texto.lower()

                        # Contar palabras clave encontradas
                        for palabra in PALABRAS_FACTURA:
                            if palabra.lower() in texto_lower:
                                palabras_encontradas += 1

                        # Si ya encontramos suficientes palabras, no seguir buscando
                        if palabras_encontradas >= UMBRAL_PALABRAS_FACTURA:
                            break
        except Exception as e:
            print(f"⚠️ ADVERTENCIA: Error al analizar contenido de {pdf_path}: {e}")

        es_probable_factura = palabras_encontradas >= UMBRAL_PALABRAS_FACTURA
        return es_probable_factura, palabras_encontradas

    def calcular_hash_md5(self, archivo_path: str) -> str:
        """
        Calcula el hash MD5 de un archivo.

        Args:
            archivo_path: Ruta al archivo

        Returns:
            Hash MD5 en formato hexadecimal
        """
        md5_hash = hashlib.md5()
        try:
            with open(archivo_path, "rb") as f:
                # Leer en chunks para archivos grandes
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except IOError as e:
            print(f"⚠️ ADVERTENCIA: Error al calcular hash de {archivo_path}: {e}")
            return ""

    def mover_pdf(self, origen: str, destino: str) -> bool:
        """
        Mueve un archivo PDF de origen a destino.
        Si el destino ya existe, agrega un sufijo numérico.

        Args:
            origen: Ruta del archivo origen
            destino: Ruta del archivo destino

        Returns:
            True si se movió correctamente, False si hubo error
        """
        try:
            destino_path = Path(destino)

            # Crear directorio destino si no existe
            destino_path.parent.mkdir(parents=True, exist_ok=True)

            # Si el destino ya existe, agregar sufijo
            if destino_path.exists():
                contador = 2
                nombre_sin_ext = destino_path.stem
                extension = destino_path.suffix

                while destino_path.exists():
                    nuevo_nombre = f"{nombre_sin_ext}_{contador}{extension}"
                    destino_path = destino_path.parent / nuevo_nombre
                    contador += 1

            # Mover archivo
            shutil.move(origen, str(destino_path))
            return True
        except Exception as e:
            print(f"❌ ERROR: No se pudo mover {origen} a {destino}: {e}")
            return False

    def registrar_operacion(self, tipo: str, nombre_archivo: str,
                          origen: str, destino: str, detalles: str = ""):
        """
        Registra una operación de movimiento de archivo en el log.

        Args:
            tipo: Tipo de operación (EXITO, DUPLICADO, ERROR_POSIBLE_FACTURA, etc.)
            nombre_archivo: Nombre del archivo procesado
            origen: Directorio de origen
            destino: Directorio de destino
            detalles: Información adicional sobre la operación
        """
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        archivo_log = self.directorio_logs / f"file_operations_{datetime.now().strftime('%Y%m%d')}.log"

        mensaje = f"{fecha_hora} | {tipo} | {nombre_archivo} | {origen} → {destino}"
        if detalles:
            mensaje += f" | {detalles}"
        mensaje += "\n"

        try:
            with open(archivo_log, 'a', encoding='utf-8') as f:
                f.write(mensaje)
        except IOError as e:
            print(f"⚠️ ADVERTENCIA: No se pudo escribir en log: {e}")

    def organizar_pdf(self, pdf_path: str, resultado_extraccion: Optional[Dict] = None) -> str:
        """
        Organiza un PDF según el resultado de su procesamiento.

        Args:
            pdf_path: Ruta al archivo PDF original
            resultado_extraccion: Diccionario con los datos extraídos de la factura
                                 o None si hubo error en la extracción

        Returns:
            Ruta final donde se movió el archivo
        """
        pdf_path = Path(pdf_path)
        nombre_archivo = pdf_path.name

        # Caso 1: Extracción exitosa
        if resultado_extraccion and not resultado_extraccion.get('_Error'):
            return self._organizar_factura_exitosa(pdf_path, resultado_extraccion)

        # Caso 2: Error de extracción
        else:
            return self._organizar_pdf_error(pdf_path, resultado_extraccion)

    def _organizar_factura_exitosa(self, pdf_path: Path, resultado: Dict) -> str:
        """
        Organiza una factura procesada exitosamente.
        Verifica duplicados y organiza por fecha (mes) y proveedor.
        """
        nombre_archivo = pdf_path.name

        # Extraer datos necesarios
        cif_proveedor = resultado.get('CIF', '')
        fecha_factura = resultado.get('FechaFactura', '')
        num_factura = resultado.get('NumFactura', '')
        trimestre = resultado.get('Trimestre', '')
        año = resultado.get('Año', '')
        nombre_proveedor = resultado.get('_Proveedor_Nombre', resultado.get('_NombreProveedor', 'Desconocido'))

        # Normalizar nombre del proveedor para carpeta (sin espacios ni caracteres raros)
        nombre_proveedor_carpeta = self._normalizar_nombre_proveedor(nombre_proveedor)

        # Verificar si es duplicado
        duplicado = self.es_duplicado(cif_proveedor, fecha_factura, num_factura,
                                     int(año), trimestre)

        if duplicado:
            # Es un duplicado real - mover a carpeta de duplicados
            destino_dir = self.directorio_duplicados / str(año) / trimestre
            destino = destino_dir / nombre_archivo

            if self.mover_pdf(str(pdf_path), str(destino)):
                detalles = f"CIF: {cif_proveedor}, Fecha: {fecha_factura}, NumFactura: {num_factura}"
                self.registrar_operacion("DUPLICADO", nombre_archivo,
                                       str(pdf_path.parent), str(destino_dir), detalles)
                print(f"  📋 Duplicado detectado: {nombre_archivo} → {destino_dir}")
                return str(destino)

        else:
            # Factura nueva - organizar por fecha (mes) y proveedor
            # Extraer mes de la fecha
            mes = self._extraer_mes_de_fecha(fecha_factura)

            destino_dir = self.directorio_procesadas / str(año) / mes / nombre_proveedor_carpeta
            destino = destino_dir / nombre_archivo

            if self.mover_pdf(str(pdf_path), str(destino)):
                # Agregar al índice
                info_factura = {
                    "cif_proveedor": cif_proveedor,
                    "fecha_factura": self._normalizar_fecha(fecha_factura),
                    "num_factura": num_factura,
                    "nombre_archivo": nombre_archivo,
                    "ruta_completa": str(destino),
                    "fecha_procesamiento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "hash_md5": self.calcular_hash_md5(str(destino))
                }
                self.agregar_al_indice(int(año), trimestre, info_factura)

                detalles = f"Proveedor: {nombre_proveedor}, CIF: {cif_proveedor}"
                self.registrar_operacion("EXITO", nombre_archivo,
                                       str(pdf_path.parent), str(destino_dir), detalles)
                print(f"  ✓ Organizado: {nombre_archivo} → {destino_dir}")
                return str(destino)

        return str(pdf_path)

    def _organizar_pdf_error(self, pdf_path: Path, resultado: Optional[Dict]) -> str:
        """
        Organiza un PDF que tuvo error en la extracción.
        Clasifica según si parece una factura o no.
        """
        nombre_archivo = pdf_path.name

        # Analizar contenido para clasificar
        es_probable_factura, num_palabras = self.analizar_contenido_pdf(str(pdf_path))

        if es_probable_factura:
            # Parece una factura pero sin plantilla
            destino_dir = self.directorio_errores / "sin_plantilla_posible_factura"
            destino = destino_dir / nombre_archivo
            tipo_log = "ERROR_POSIBLE_FACTURA"
            detalles = f"{num_palabras} palabras clave detectadas"
            print(f"  ⚠️ Posible factura sin plantilla: {nombre_archivo} → {destino_dir}")
        else:
            # Probablemente no es una factura
            destino_dir = self.directorio_errores / "probablemente_no_factura"
            destino = destino_dir / nombre_archivo
            tipo_log = "ERROR_NO_FACTURA"
            detalles = f"Solo {num_palabras} palabras clave encontradas"
            print(f"  ❌ Probablemente no es factura: {nombre_archivo} → {destino_dir}")

        if self.mover_pdf(str(pdf_path), str(destino)):
            self.registrar_operacion(tipo_log, nombre_archivo,
                                   str(pdf_path.parent), str(destino_dir), detalles)
            return str(destino)

        return str(pdf_path)

    def _normalizar_nombre_proveedor(self, nombre: str) -> str:
        """
        Normaliza el nombre del proveedor para usar como nombre de carpeta.
        Elimina caracteres especiales y espacios.
        """
        if not nombre or nombre.strip() == "":
            return "Desconocido"

        # Reemplazar espacios por guiones bajos
        nombre = nombre.replace(' ', '_')
        # Eliminar caracteres no permitidos en nombres de carpeta
        caracteres_permitidos = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        nombre = ''.join(c for c in nombre if c in caracteres_permitidos)
        return nombre if nombre else "Desconocido"

    def _extraer_mes_de_fecha(self, fecha: str) -> str:
        """
        Extrae el mes de una fecha en formato DD/MM/YYYY o YYYY-MM-DD.

        Args:
            fecha: Fecha en formato DD/MM/YYYY o YYYY-MM-DD

        Returns:
            Mes en formato MM (ej: "01", "12")
        """
        if not fecha:
            return "00"

        try:
            # Formato DD/MM/YYYY
            if '/' in fecha:
                parts = fecha.split('/')
                if len(parts) == 3:
                    return parts[1].zfill(2)

            # Formato YYYY-MM-DD
            if '-' in fecha:
                parts = fecha.split('-')
                if len(parts) == 3:
                    return parts[1].zfill(2)
        except:
            pass

        return "00"
