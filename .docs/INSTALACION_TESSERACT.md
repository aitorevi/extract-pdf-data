# Instalación de Tesseract OCR en Windows

## Paso 1: Descargar Tesseract

Descarga el instalador desde GitHub:
- **URL**: https://github.com/UB-Mannheim/tesseract/wiki
- **Archivo recomendado**: `tesseract-ocr-w64-setup-5.x.x.xxxx.exe` (64-bit)

O descarga directamente desde:
- https://digi.bib.uni-mannheim.de/tesseract/

## Paso 2: Instalar

1. Ejecuta el instalador descargado
2. **IMPORTANTE**: Durante la instalación, asegúrate de seleccionar:
   - ✅ **Spanish language data** (datos de idioma español)
   - ✅ Instalar en la ruta por defecto: `C:\Program Files\Tesseract-OCR\`

## Paso 3: Agregar al PATH (Opcional pero recomendado)

### Opción A: Durante la instalación
- Marca la casilla "Add Tesseract to PATH"

### Opción B: Manual
1. Abre "Variables de entorno del sistema"
2. Edita la variable "Path"
3. Agrega: `C:\Program Files\Tesseract-OCR\`

## Paso 4: Verificar instalación

Abre una nueva terminal (PowerShell o CMD) y ejecuta:

```bash
tesseract --version
```

Deberías ver algo como:
```
tesseract 5.x.x
 leptonica-1.x.x
  ...
```

## Paso 5: Verificar desde Python

```bash
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

Si no funciona automáticamente, configura la ruta manualmente en el código:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Troubleshooting

### Error: "tesseract is not installed or it's not in your PATH"

**Solución 1**: Reinicia la terminal después de instalar

**Solución 2**: Configura la ruta manualmente en Python:
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Error: "Failed to load language 'spa'"

**Solución**: Reinstala Tesseract y asegúrate de seleccionar "Spanish language data" durante la instalación

## Verificación Final

Después de instalar, ejecuta en tu proyecto:

```bash
python -c "import pytesseract; from pdf2image import convert_from_path; print('OCR ready!')"
```

Si no hay errores, estás listo para usar OCR.
