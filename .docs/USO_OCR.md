# Uso de OCR para PDFs Escaneados

## Resumen
El sistema ahora soporta automáticamente PDFs escaneados (sin texto extraíble) usando Tesseract OCR.

## ¿Cuándo se usa OCR?
El OCR se activa **automáticamente** cuando:
- Un PDF no tiene texto extraíble (imagen escaneada)
- Tesseract está instalado en el sistema

**No necesitas hacer nada especial** - el sistema detecta y usa OCR transparentemente.

## Instalación Previa Necesaria

### 1. Tesseract OCR
Sigue las instrucciones en `.docs/INSTALACION_TESSERACT.md`:
- Descarga e instala Tesseract desde: https://github.com/UB-Mannheim/tesseract/wiki
- Durante la instalación, selecciona "Spanish language data" (opcional pero recomendado)
- Instala en: `C:\Program Files\Tesseract-OCR\`

### 2. Dependencias Python
Ya instaladas:
```bash
pip install pytesseract pdf2image pillow
```

## Uso Automático

### Procesar facturas normalmente:
```python
from src.pdf_extractor import PDFExtractor

# Crear extractor
extractor = PDFExtractor(trimestre='4T', año='2025')
extractor.cargar_plantillas()

# Procesar carpeta (incluye PDFs escaneados automáticamente)
extractor.procesar_carpeta()
```

El sistema:
1. ✅ Detecta si cada PDF tiene texto extraíble
2. ✅ Si NO tiene texto → Usa OCR automáticamente
3. ✅ Si tiene texto → Usa extracción directa (más rápida)
4. ✅ Todo transparente para el usuario

## Verificar Instalación

### Test rápido:
```bash
python test_ocr.py "ruta/al/pdf_escaneado.pdf"
```

Esto te mostrará:
- Si Tesseract está instalado
- Si el PDF tiene texto extraíble
- Texto extraído por OCR
- Confianza promedio del OCR

### Test con tu PDF:
```bash
python test_ocr.py "documentos/por_procesar/2025-10-01_093033_FRA SEPT TIENDAS ZULIMA.pdf"
```

## Rendimiento

### Tiempos aproximados:
- **Extracción directa**: ~0.1 segundos/página
- **Con OCR**: ~2-5 segundos/página (20-50x más lento)

### Optimización:
El OCR solo se aplica a PDFs escaneados, no a todos los PDFs.

## Indicadores Visuales

Cuando procesas PDFs, verás mensajes como:

```
Procesando: factura_escaneada.pdf
  [OCR] PDF sin texto extraíble, usando OCR...
  Probando plantilla: galvez_y_selles_asesores
    CIF extraído (OCR): B-97.834.865 -> normalizado: B97834865
    Nombre extraído (OCR): galvez y selles asesores, s.l.
OK Proveedor identificado por CIF: galvez_y_selles_asesores
```

## Metadatos

Los datos extraídos incluyen metadatos que indican si se usó OCR:
- `_UsaOCR`: True/False (indica si se aplicó OCR)

## Troubleshooting

### "tesseract is not installed"
- Solución: Instala Tesseract siguiendo `.docs/INSTALACION_TESSERACT.md`

### "Unable to get page count. Is poppler installed?"
- Ya resuelto: El proyecto incluye poppler en `poppler/Library/bin/`

### OCR extrae texto incorrecto
- El OCR funciona mejor con:
  - Imágenes de alta resolución
  - Texto claro y legible
  - Buen contraste
- Puedes ajustar el DPI en `ocr_engine.py` (default: 300)

### Performance lento
- Normal: OCR es 20-50x más lento que extracción directa
- Solo se usa para PDFs escaneados
- Mejoras futuras: Cache de resultados OCR

## Ejemplos Exitosos

### PDF Escaneado de Galvez y Selles
```python
from src.pdf_extractor import PDFExtractor

extractor = PDFExtractor(trimestre='4T', año='2025')
extractor.cargar_plantillas()

# Este PDF está escaneado - OCR se usa automáticamente
pdf = "documentos/por_procesar/2025-10-01_093033_FRA SEPT TIENDAS ZULIMA.pdf"
proveedor = extractor.identificar_proveedor(pdf)
# Resultado: "galvez_y_selles_asesores" ✅
```

## Próximas Mejoras

- [ ] Soporte para múltiples idiomas
- [ ] Preprocessing de imágenes (mejora calidad OCR)
- [ ] Cache de resultados OCR
- [ ] OCR paralelo para múltiples PDFs
- [ ] Métricas de precisión por proveedor

## Referencias
- Documentación arquitectura: `.docs/OCR_IMPLEMENTATION.md`
- Instalación Tesseract: `.docs/INSTALACION_TESSERACT.md`
- Test de OCR: `test_ocr.py`
