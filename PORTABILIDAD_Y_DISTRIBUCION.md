# Guía de Portabilidad y Distribución

Esta guía explica las diferentes opciones para hacer que el proyecto funcione de manera sencilla en cualquier ordenador Windows, sin complicaciones de instalación.

---

## Contexto del Problema

**Situación actual:**
- El proyecto requiere Python 3.8+
- Necesita múltiples dependencias: pdfplumber, pandas, openpyxl, pdf2image, Pillow
- Requiere Poppler (binarios externos)
- La instalación manual es compleja y propensa a errores

**Objetivo:**
Simplificar el despliegue para que cualquier usuario pueda usar la aplicación sin conocimientos técnicos.

---

## Opción 1: Ejecutable Standalone (.exe) con PyInstaller

### Descripción
Convierte todo el proyecto Python en un único archivo ejecutable (.exe) que incluye Python, todas las dependencias y Poppler.

### Ventajas
- ✓ **Máxima simplicidad:** Solo doble clic en el .exe
- ✓ **No requiere Python instalado** en el PC
- ✓ **Todas las dependencias incluidas** (incluido Poppler)
- ✓ **Ideal para usuarios finales** sin conocimientos técnicos
- ✓ **Portable:** Copiar el .exe a cualquier PC y funciona

### Desventajas
- ✗ Archivo grande (100-200 MB aproximadamente)
- ✗ **Cada actualización requiere regenerar el .exe completo**
- ✗ Tiempo de compilación: 2-5 minutos cada vez
- ✗ Menos flexible para desarrollo activo
- ✗ Antivirus pueden marcar falsos positivos

### Cuándo usar
- Distribución a usuarios finales
- Versión estable del proyecto
- Pocas actualizaciones esperadas
- Usuarios sin Python instalado

### Implementación

#### Paso 1: Instalar PyInstaller
```bash
pip install pyinstaller
```

#### Paso 2: Crear el ejecutable del editor
```bash
pyinstaller --name="Editor_Plantillas" ^
            --onefile ^
            --windowed ^
            --add-data "poppler;poppler" ^
            --add-data "plantillas;plantillas" ^
            --add-data "facturas;facturas" ^
            --icon="icon.ico" ^
            src/editor_plantillas.py
```

#### Paso 3: Crear el ejecutable principal
```bash
pyinstaller --name="ExtractorPDF" ^
            --onefile ^
            --console ^
            --add-data "poppler;poppler" ^
            --add-data "plantillas;plantillas" ^
            --add-data "facturas;facturas" ^
            src/main.py
```

#### Paso 4: Distribuir
Los ejecutables estarán en la carpeta `dist/`:
- `Editor_Plantillas.exe` - Para crear/editar plantillas
- `ExtractorPDF.exe` - Para procesar facturas

**Distribución final:**
```
MiProyecto/
├── Editor_Plantillas.exe
├── ExtractorPDF.exe
├── plantillas/
├── facturas/
└── README.txt
```

### Personalización avanzada

**Archivo de configuración `.spec`:**
Puedes crear un archivo de configuración avanzado para más control:

```python
# editor.spec
a = Analysis(['src/editor_plantillas.py'],
             pathex=[],
             binaries=[],
             datas=[('poppler', 'poppler'),
                    ('plantillas', 'plantillas')],
             hiddenimports=['pdfplumber', 'pdf2image'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Editor_Plantillas',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='icon.ico')
```

Luego compilar con:
```bash
pyinstaller editor.spec
```

---

## Opción 2: Script de Instalación Automático

### Descripción
Un script batch (.bat) que verifica e instala automáticamente todas las dependencias.

### Ventajas
- ✓ Instalación en un solo paso
- ✓ Más ligero que .exe
- ✓ Fácil actualización del código fuente
- ✓ Verificación automática de dependencias

### Desventajas
- ✗ Requiere Python preinstalado
- ✗ Requiere conexión a internet (para pip install)
- ✗ Usuarios deben ejecutar el instalador primero

### Cuándo usar
- Desarrollo activo
- Usuarios con Python instalado
- Actualizaciones frecuentes del código

### Implementación

**Archivo: `install.bat`**
```batch
@echo off
echo ============================================================
echo   INSTALADOR AUTOMATICO - Extractor PDF Data
echo ============================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado
    echo Descarga Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Python detectado correctamente
python --version

REM Actualizar pip
echo.
echo [2/3] Actualizando pip...
python -m pip install --upgrade pip --quiet

REM Instalar dependencias
echo.
echo [3/3] Instalando dependencias...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Fallo en la instalacion
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   INSTALACION COMPLETADA EXITOSAMENTE
echo ============================================================
echo.
echo Puedes ejecutar el proyecto con:
echo   - editor.bat (para crear/editar plantillas)
echo   - python -m src.main (para procesar facturas)
echo.
pause
```

**Archivo: `verify_install.bat`**
```batch
@echo off
echo Verificando instalacion...
python -c "import pdfplumber, pandas, openpyxl, pdf2image, PIL; print('Todas las dependencias OK')"
if errorlevel 1 (
    echo.
    echo Hay dependencias faltantes. Ejecuta install.bat
    pause
    exit /b 1
)
echo Instalacion verificada correctamente!
pause
```

---

## Opción 3: Entorno Virtual Portable

### Descripción
Empaqueta Python + todas las dependencias en una carpeta autocontenida que puede copiarse a cualquier PC.

### Ventajas
- ✓ **Completamente portable** (copiar carpeta = funciona)
- ✓ No afecta al Python del sistema
- ✓ Versión de Python controlada
- ✓ Fácil actualización del código
- ✓ No requiere internet después de la primera instalación

### Desventajas
- ✗ Carpeta grande (500 MB - 1 GB)
- ✗ Instalación inicial más lenta
- ✗ Específico para Windows (no cross-platform)

### Cuándo usar
- Distribución interna (empresa/equipo)
- Sin acceso a internet en PCs destino
- Necesitas control total del entorno
- Múltiples usuarios con el mismo setup

### Implementación

**Archivo: `setup_portable.bat`**
```batch
@echo off
echo ============================================================
echo   CREANDO ENTORNO PORTABLE
echo ============================================================

REM Crear entorno virtual
echo [1/4] Creando entorno virtual...
python -m venv venv_portable

REM Activar entorno
echo [2/4] Activando entorno...
call venv_portable\Scripts\activate.bat

REM Actualizar pip
echo [3/4] Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias
echo [4/4] Instalando dependencias...
pip install -r requirements.txt

echo.
echo ============================================================
echo   ENTORNO PORTABLE CREADO
echo ============================================================
echo.
echo Ahora puedes copiar toda esta carpeta a otro PC
echo Para usar: ejecuta RUN_EDITOR.bat o RUN_MAIN.bat
pause
```

**Archivo: `RUN_EDITOR.bat`**
```batch
@echo off
call venv_portable\Scripts\activate.bat
python scripts\editor.py
pause
```

**Archivo: `RUN_MAIN.bat`**
```batch
@echo off
call venv_portable\Scripts\activate.bat
python -m src.main
pause
```

---

## Opción 4: Launcher Inteligente con Auto-Setup (RECOMENDADO PARA DESARROLLO)

### Descripción
Un launcher que detecta automáticamente si falta algo y lo instala, combinando lo mejor de todas las opciones anteriores.

### Ventajas
- ✓ **Detección automática** de dependencias
- ✓ **Instalación automática** si falta algo
- ✓ **Doble clic** para usar (como un .exe)
- ✓ **Actualizaciones fáciles** (solo copiar archivos .py)
- ✓ **Entorno aislado** (venv)
- ✓ **Portable** (copiar carpeta completa)

### Desventajas
- ✗ Primera ejecución más lenta (crea venv)
- ✗ Requiere Python instalado
- ✗ Carpeta más grande que solo código fuente

### Cuándo usar
- **IDEAL PARA DESARROLLO ACTIVO**
- Equipo de desarrollo
- Frecuentes actualizaciones
- Balance entre simplicidad y flexibilidad

### Implementación

**Archivo: `EDITOR.bat`**
```batch
@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   EDITOR DE PLANTILLAS - Auto Launcher
echo ============================================================

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    echo Instala Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verificar si existe entorno virtual
if not exist "venv\" (
    echo.
    echo [AUTO-SETUP] Entorno virtual no encontrado
    echo [AUTO-SETUP] Creando entorno virtual...
    python -m venv venv

    echo [AUTO-SETUP] Instalando dependencias...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet

    echo [AUTO-SETUP] Configuracion completada!
    echo.
) else (
    call venv\Scripts\activate.bat
)

REM Verificar dependencias
python -c "import pdfplumber" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [AUTO-SETUP] Dependencias faltantes detectadas
    echo [AUTO-SETUP] Instalando...
    pip install -r requirements.txt --quiet
    echo [AUTO-SETUP] Dependencias instaladas!
    echo.
)

REM Ejecutar editor
python scripts\editor.py

deactivate
pause
```

**Archivo: `EJECUTAR.bat`**
```batch
@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   EXTRACTOR PDF - Auto Launcher
echo ============================================================

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    pause
    exit /b 1
)

REM Verificar/crear entorno virtual
if not exist "venv\" (
    echo [AUTO-SETUP] Creando entorno...
    python -m venv venv
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
) else (
    call venv\Scripts\activate.bat
)

REM Ejecutar aplicación principal
python -m src.main

deactivate
pause
```

**Archivo: `UPDATE.bat`**
```batch
@echo off
echo ============================================================
echo   ACTUALIZAR DEPENDENCIAS
echo ============================================================

if not exist "venv\" (
    echo ERROR: Entorno virtual no encontrado
    echo Ejecuta EDITOR.bat primero
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Actualizando pip...
python -m pip install --upgrade pip

echo Actualizando dependencias...
pip install -r requirements.txt --upgrade

echo.
echo Actualizacion completada!
deactivate
pause
```

---

## Opción 5: Docker Container (Avanzado)

### Descripción
Empaqueta toda la aplicación en un contenedor Docker con interfaz gráfica.

### Ventajas
- ✓ Máximo aislamiento
- ✓ Cross-platform (Windows, Linux, Mac)
- ✓ Reproducibilidad perfecta
- ✓ Fácil escalado

### Desventajas
- ✗ Requiere Docker instalado
- ✗ Complejidad adicional
- ✗ Interfaz gráfica requiere configuración especial en Windows
- ✗ Curva de aprendizaje

### Cuándo usar
- Entorno empresarial con infraestructura Docker
- Necesitas ejecutar en servidores
- Múltiples plataformas

### Implementación

**Archivo: `Dockerfile`**
```dockerfile
FROM python:3.8-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    poppler-utils \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Comando por defecto
CMD ["python", "-m", "src.main"]
```

**Archivo: `docker-compose.yml`**
```yaml
version: '3.8'

services:
  extractor:
    build: .
    volumes:
      - ./facturas:/app/facturas
      - ./plantillas:/app/plantillas
      - ./exports:/app/exports
    environment:
      - DISPLAY=${DISPLAY}
    network_mode: host
```

**Uso:**
```bash
docker-compose up
```

---

## Comparación de Opciones

| Característica | EXE | Script Install | Venv Portable | Auto-Launcher | Docker |
|----------------|-----|----------------|---------------|---------------|--------|
| Simplicidad uso | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★★ | ★★☆☆☆ |
| Actualizaciones | ★☆☆☆☆ | ★★★★★ | ★★★★☆ | ★★★★★ | ★★★★☆ |
| Portabilidad | ★★★★★ | ★★☆☆☆ | ★★★★★ | ★★★★☆ | ★★★☆☆ |
| Tamaño | ★★☆☆☆ | ★★★★★ | ★★☆☆☆ | ★★★☆☆ | ★★☆☆☆ |
| Req. técnicos | ★★★★★ | ★★☆☆☆ | ★★★☆☆ | ★★☆☆☆ | ★☆☆☆☆ |
| Desarrollo | ★☆☆☆☆ | ★★★★☆ | ★★★☆☆ | ★★★★★ | ★★★★☆ |

---

## Recomendaciones por Escenario

### Para Desarrollo Activo
**Opción 4: Auto-Launcher**
- Mejor balance flexibilidad/simplicidad
- Actualizaciones frecuentes sin problemas
- Experiencia de usuario simple

### Para Distribución a Usuarios Finales
**Opción 1: Ejecutable (.exe)**
- Máxima simplicidad para el usuario
- No requiere conocimientos técnicos
- Versión estable y probada

### Para Equipo Interno con Python
**Opción 2: Script de Instalación**
- Ligero y rápido
- Fácil de mantener
- Control total del código

### Para Distribución sin Internet
**Opción 3: Entorno Virtual Portable**
- Funciona offline completamente
- Copiar carpeta = funciona
- Ideal para instalaciones aisladas

### Para Infraestructura Empresarial
**Opción 5: Docker**
- Escalabilidad
- Integración con CI/CD
- Entornos reproducibles

---

## Próximos Pasos

1. **Evaluar el escenario de uso** principal del proyecto
2. **Elegir la opción** que mejor se adapte
3. **Implementar** siguiendo las instrucciones de esta guía
4. **Probar** en diferentes PCs
5. **Documentar** el proceso de instalación para usuarios

---

## Recursos Adicionales

- **PyInstaller docs:** https://pyinstaller.org/en/stable/
- **Python venv:** https://docs.python.org/3/library/venv.html
- **Docker Python:** https://hub.docker.com/_/python
- **Poppler Windows:** https://github.com/oschwartz10612/poppler-windows

---

## Notas Técnicas

### Problema con tkinter en PyInstaller
Si el .exe no muestra ventanas:
```bash
pyinstaller --hidden-import=PIL._tkinter_finder --windowed src/editor_plantillas.py
```

### Reducir tamaño del .exe
```bash
pyinstaller --onefile --windowed --upx-dir=C:\upx src/editor_plantillas.py
```
(Requiere descargar UPX: https://upx.github.io/)

### Evitar falsos positivos de antivirus
- Firma digital del ejecutable
- Usar `--noupx` si UPX causa problemas
- Reportar el hash del .exe a vendors de antivirus

---

**Fecha:** 2025-10-28
**Versión:** 1.0
**Proyecto:** Extract PDF Data
