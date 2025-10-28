# Instalación en Windows

## Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Paso 1: Instalar dependencias Python

Abre PowerShell o CMD en la carpeta del proyecto y ejecuta:

```bash
pip install -r requirements.txt
```

## Paso 2: Instalar Poppler (requerido para pdf2image)

**Opción A - Añadir al PATH (Recomendado):**

1. Descarga Poppler para Windows:
   - Ve a: https://github.com/oschwartz10612/poppler-windows/releases/
   - Descarga la última versión (archivo .zip)

2. Extrae el archivo ZIP en una ubicación permanente, por ejemplo:
   ```
   C:\Program Files\poppler-xx.xx.x\
   ```

3. Añade la carpeta `bin` al PATH del sistema:
   - Abre "Variables de entorno" (busca en el menú de Windows)
   - En "Variables del sistema", selecciona "Path" y haz clic en "Editar"
   - Añade una nueva entrada: `C:\Program Files\poppler-xx.xx.x\Library\bin`
   - Haz clic en "Aceptar" y reinicia PowerShell/CMD

4. Verifica la instalación:
   ```bash
   pdftoppm -v
   ```

**Opción B - Ruta manual en el código:**

Si no quieres modificar el PATH, puedes especificar la ruta de Poppler directamente en el código del editor cuando uses `pdf2image`.

## Paso 3: Verificar instalación

Ejecuta el script principal para verificar que todo funciona:

```bash
python -m src.main
```

Para el editor de plantillas:

```bash
.\editor.bat
```

## Solución de Problemas

### Error: "No module named 'pdfplumber'"
```bash
pip install pdfplumber
```

### Error: "Unable to get page count. Is poppler installed?"
- Verifica que Poppler esté instalado y en el PATH
- O especifica la ruta manualmente en el código

### Error: "tkinter not found"
- Reinstala Python asegurándote de marcar "tcl/tk and IDLE" durante la instalación
