# Implementación de OCR para PDFs Escaneados

## Problema
Los PDFs escaneados (sin texto extraíble) no pueden ser procesados por el sistema actual porque pdfplumber no puede extraer texto de imágenes.

## Solución
Implementar OCR (Optical Character Recognition) usando Tesseract para extraer texto de PDFs escaneados.

## Arquitectura

### 1. Dependencias Necesarias

**Python:**
- `pytesseract` - Wrapper de Python para Tesseract
- `pdf2image` - Para convertir páginas PDF a imágenes ✅ (ya instalado)
- `pillow` - Manipulación de imágenes ✅ (ya instalado)

**Binarios:**
- Tesseract-OCR - Motor OCR (debe instalarse en el sistema)

### 2. Flujo de Procesamiento

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Abrir PDF con pdfplumber                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. ¿Tiene texto extraíble? (contar palabras)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │ Sí                        │ No
         ▼                           ▼
┌────────────────────┐    ┌──────────────────────────┐
│ Usar pdfplumber    │    │ Aplicar OCR:             │
│ (flujo actual)     │    │ 1. Convertir a imagen    │
└────────────────────┘    │ 2. Aplicar Tesseract     │
                          │ 3. Obtener texto + bbox  │
                          └──────────────────────────┘
                                     │
                                     ▼
                          ┌──────────────────────────┐
                          │ Extraer campos usando    │
                          │ coordenadas (igual)      │
                          └──────────────────────────┘
```

### 3. Componentes a Implementar

#### 3.1. Detector de Texto (`src/utils/pdf_text_detector.py`)
```python
def tiene_texto_extraible(pdf_page) -> bool:
    """Detecta si una página PDF tiene texto extraíble."""
    palabras = pdf_page.extract_words()
    return len(palabras) > 0
```

#### 3.2. OCR Engine (`src/utils/ocr_engine.py`)
```python
class OCREngine:
    """Motor OCR para extraer texto de PDFs escaneados."""

    def __init__(self, idioma='spa'):
        """Inicializa el motor OCR."""

    def extraer_texto_con_coordenadas(self, pdf_page):
        """Aplica OCR y retorna texto con coordenadas bbox."""

    def extraer_texto_area(self, pdf_page, bbox):
        """Aplica OCR a un área específica del PDF."""
```

#### 3.3. Integración en PDFExtractor
- Modificar `identificar_proveedor()` para usar OCR si es necesario
- Modificar `extraer_datos_factura()` para usar OCR en áreas sin texto
- Añadir flag `_UsaOCR` a metadatos para tracking

### 4. Configuración

**Archivo: `config/ocr_config.json`**
```json
{
    "ocr_enabled": true,
    "tesseract_path": "C:/Program Files/Tesseract-OCR/tesseract.exe",
    "idioma": "spa",
    "dpi": 300,
    "preprocessing": {
        "escala_grises": true,
        "binarizacion": true,
        "denoise": false
    }
}
```

### 5. Instalación

**Windows:**
```bash
# 1. Instalar Tesseract
# Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
# Instalar en: C:\Program Files\Tesseract-OCR\

# 2. Instalar pytesseract
python -m pip install pytesseract

# 3. Configurar PATH (opcional)
setx TESSERACT_PATH "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa
python -m pip install pytesseract
```

### 6. Testing

**Test Cases:**
1. PDF con texto extraíble → No usar OCR
2. PDF completamente escaneado → Usar OCR
3. PDF mixto (texto + imágenes) → Usar OCR solo donde sea necesario
4. Verificar precisión de coordenadas extraídas por OCR

### 7. Consideraciones de Performance

**Optimizaciones:**
- OCR solo en áreas específicas (bbox) en lugar de página completa
- Cache de resultados OCR para evitar reprocesar
- Procesamiento paralelo de páginas si es posible
- Umbral de confianza para texto extraído por OCR

**Trade-offs:**
- OCR es ~10-20x más lento que extracción directa
- Requiere más memoria (conversión a imagen)
- Precisión puede variar según calidad del escaneo

### 8. Roadmap

**Fase 1: MVP** ✅
- [x] Documentar arquitectura
- [ ] Instalar dependencias
- [ ] Implementar detector de texto
- [ ] Implementar OCR básico
- [ ] Integrar en flujo de identificación

**Fase 2: Refinamiento**
- [ ] Preprocessing de imágenes (mejorar calidad)
- [ ] Ajuste de parámetros Tesseract
- [ ] Cache de resultados OCR
- [ ] Métricas de precisión

**Fase 3: Optimización**
- [ ] OCR solo en áreas necesarias
- [ ] Procesamiento paralelo
- [ ] Configuración por proveedor

## Referencias
- Tesseract Documentation: https://github.com/tesseract-ocr/tesseract
- pytesseract: https://github.com/madmaze/pytesseract
- pdf2image: https://github.com/Belval/pdf2image
