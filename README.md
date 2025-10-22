# Extractor de Datos de Facturas PDF

Aplicación local para extraer datos de facturas en PDF y exportarlos a Excel/CSV.

## Instalación

```bash
pip install -r requirements.txt
```

## Estructura del Proyecto

```
extract-pdf-data/
├── facturas/              # PDFs de facturas a procesar
├── plantillas/            # Archivos JSON con coordenadas por proveedor
├── imagenes_muestra/      # Imágenes de muestra para obtener coordenadas
├── coordinate_extractor.py # Herramienta para obtener coordenadas con OpenCV
├── pdf_extractor.py       # Lógica principal de extracción
├── main.py               # Script principal
└── requirements.txt
```

## Uso

1. **Obtener coordenadas**: Usar `coordinate_extractor.py` para definir campos en facturas
2. **Crear plantillas**: Definir archivos JSON en `/plantillas/`
3. **Procesar facturas**: Ejecutar `main.py` para extraer datos y generar Excel

## Workflow

1. Convertir PDF a imagen de alta resolución
2. Usar coordinate_extractor.py para obtener coordenadas de campos
3. Crear plantilla JSON para cada proveedor
4. Procesar facturas con pdf_extractor.py
5. Exportar resultados a Excel/CSV