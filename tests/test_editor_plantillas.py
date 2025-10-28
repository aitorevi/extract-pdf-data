"""
Tests para el módulo editor_plantillas.py - Editor GUI de plantillas.

Nota: Este módulo es una aplicación GUI con tkinter, por lo que muchos tests
requieren moclear componentes visuales. Nos enfocamos en:
1. Lógica de negocio (procesamiento de datos, validaciones)
2. Generación de JSON de plantillas
3. Carga de plantillas existentes
4. Inicialización sin mostrar GUI
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from src.editor_plantillas import EditorPlantillas, CAMPOS_IDENTIFICACION, CAMPOS_PREDEFINIDOS


class TestCamposConstantes:
    """Tests para constantes de campos predefinidos."""

    def test_campos_identificacion_definidos(self):
        """Test que CAMPOS_IDENTIFICACION tiene los campos correctos."""
        assert len(CAMPOS_IDENTIFICACION) == 2

        nombres = [c['nombre'] for c in CAMPOS_IDENTIFICACION]
        assert 'CIF_Identificacion' in nombres
        assert 'Nombre_Identificacion' in nombres

        # Verificar estructura
        for campo in CAMPOS_IDENTIFICACION:
            assert 'nombre' in campo
            assert 'tipo' in campo
            assert 'descripcion' in campo

    def test_campos_predefinidos_definidos(self):
        """Test que CAMPOS_PREDEFINIDOS tiene los campos correctos."""
        assert len(CAMPOS_PREDEFINIDOS) == 4

        nombres = [c['nombre'] for c in CAMPOS_PREDEFINIDOS]
        assert 'FechaFactura' in nombres
        assert 'FechaVto' in nombres
        assert 'NumFactura' in nombres
        assert 'Base' in nombres

        # Verificar estructura
        for campo in CAMPOS_PREDEFINIDOS:
            assert 'nombre' in campo
            assert 'tipo' in campo


@pytest.mark.unit
class TestEditorPlantillasInit:
    """Tests para inicialización de EditorPlantillas."""

    @patch('src.editor_plantillas.pdfplumber.open')
    @patch('src.editor_plantillas.tk.Tk')
    def test_init_sin_plantilla_existente(self, mock_tk, mock_pdf_open):
        """Test inicialización sin plantilla existente."""
        # Mock PDF
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.width = 595  # A4 width
        mock_page.height = 842  # A4 height
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        # Mock Tk
        mock_root = MagicMock()
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080
        mock_tk.return_value = mock_root

        # Crear editor
        editor = EditorPlantillas("test.pdf")

        # Verificar inicialización
        assert editor.pdf_path == "test.pdf"
        assert editor.pdf_width == 595
        assert editor.pdf_height == 842
        assert editor.plantilla_cargada is None

        # Verificar que todos los campos están inicializados en None
        assert 'CIF_Identificacion' in editor.campos
        assert 'Nombre_Identificacion' in editor.campos
        assert 'FechaFactura' in editor.campos
        assert 'NumFactura' in editor.campos
        assert 'Base' in editor.campos

        # Todos deberían ser None al inicio
        assert editor.campos['CIF_Identificacion'] is None
        assert editor.campos['FechaFactura'] is None

    @patch('src.editor_plantillas.pdfplumber.open')
    @patch('src.editor_plantillas.tk.Tk')
    def test_init_con_plantilla_existente(self, mock_tk, mock_pdf_open):
        """Test inicialización con plantilla existente."""
        # Mock PDF
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.width = 595
        mock_page.height = 842
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        # Mock Tk
        mock_root = MagicMock()
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080
        mock_tk.return_value = mock_root

        # Plantilla existente
        plantilla_existente = {
            "nombre_proveedor": "Test Provider",
            "cif_proveedor": "B12345678",
            "campos": [
                {
                    "nombre": "CIF_Identificacion",
                    "coordenadas": [100, 50, 300, 70],
                    "tipo": "texto"
                },
                {
                    "nombre": "FechaFactura",
                    "coordenadas": [100, 100, 200, 120],
                    "tipo": "fecha"
                },
                {
                    "nombre": "NumFactura",
                    "coordenadas": [100, 150, 200, 170],
                    "tipo": "texto"
                }
            ]
        }

        # Crear editor con plantilla
        editor = EditorPlantillas("test.pdf", plantilla_existente)

        # Verificar que se cargaron las coordenadas (ahora son dicts con coordenadas y página)
        assert editor.plantilla_cargada == plantilla_existente
        assert editor.campos['CIF_Identificacion']['coordenadas'] == [100, 50, 300, 70]
        assert editor.campos['CIF_Identificacion']['pagina'] == 0  # página 1 se convierte a índice 0
        assert editor.campos['FechaFactura']['coordenadas'] == [100, 100, 200, 120]
        assert editor.campos['FechaFactura']['pagina'] == 0
        assert editor.campos['NumFactura']['coordenadas'] == [100, 150, 200, 170]
        assert editor.campos['NumFactura']['pagina'] == 0

        # Campos no en la plantilla deben ser None
        assert editor.campos['Base'] is None

    @patch('src.editor_plantillas.pdfplumber.open')
    @patch('src.editor_plantillas.tk.Tk')
    def test_init_configura_dimensiones_ventana(self, mock_tk, mock_pdf_open):
        """Test que inicialización configura correctamente las dimensiones de ventana."""
        # Mock PDF
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.width = 595
        mock_page.height = 842
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        # Mock Tk con pantalla pequeña
        mock_root = MagicMock()
        mock_root.winfo_screenwidth.return_value = 1024
        mock_root.winfo_screenheight.return_value = 768
        mock_tk.return_value = mock_root

        editor = EditorPlantillas("test.pdf")

        # Verificar que se llamó geometry con dimensiones apropiadas
        # La ventana debe ser 1400x900 o menos dependiendo del tamaño de pantalla
        mock_root.geometry.assert_called_once()
        call_args = mock_root.geometry.call_args[0][0]
        assert 'x' in call_args  # Formato: "WIDTHxHEIGHT+X+Y"


@pytest.mark.unit
class TestEditorPlantillasGuardar:
    """Tests para el método guardar_plantilla."""

    @patch('src.editor_plantillas.pdfplumber.open')
    @patch('src.editor_plantillas.tk.Tk')
    def test_guardar_plantilla_valida_campos_obligatorios(self, mock_tk, mock_pdf_open, capsys):
        """Test que guardar_plantilla valida campos obligatorios."""
        # Mock PDF
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.width = 595
        mock_page.height = 842
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        # Mock Tk
        mock_root = MagicMock()
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080
        mock_tk.return_value = mock_root

        # Crear editor con ALGUNOS campos pero no todos
        editor = EditorPlantillas("test.pdf")
        editor.campos['CIF_Identificacion'] = [50, 50, 250, 70]
        editor.campos['FechaFactura'] = [100, 100, 200, 120]
        # Faltan FechaVto, NumFactura y Base

        # Mock messagebox.askyesno para simular que usuario cancela
        with patch('src.editor_plantillas.messagebox.askyesno', return_value=False):
            editor.guardar_plantilla()

        # Verificar que se imprimió mensaje de campos obligatorios faltantes y guardado cancelado
        captured = capsys.readouterr()
        assert "Faltan campos obligatorios" in captured.out
        assert "Guardado cancelado" in captured.out

    @patch('src.editor_plantillas.pdfplumber.open')
    @patch('src.editor_plantillas.tk.Tk')
    def test_guardar_plantilla_sin_campos_identificacion(self, mock_tk, mock_pdf_open, capsys):
        """Test que advertencia se muestra si no hay campos de identificación."""
        # Mock PDF
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.width = 595
        mock_page.height = 842
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        # Mock Tk
        mock_root = MagicMock()
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080
        mock_tk.return_value = mock_root

        # Crear editor SIN campos de identificación pero CON todos los campos de datos
        editor = EditorPlantillas("test.pdf")
        editor.campos['FechaFactura'] = {'coordenadas': [100, 100, 200, 120], 'pagina': 0}
        editor.campos['FechaVto'] = {'coordenadas': [100, 150, 200, 170], 'pagina': 0}
        editor.campos['NumFactura'] = {'coordenadas': [100, 200, 200, 220], 'pagina': 0}
        editor.campos['Base'] = {'coordenadas': [100, 250, 200, 270], 'pagina': 0}

        # Mock messagebox y simpledialog para capturar advertencia
        with patch('src.editor_plantillas.messagebox.showwarning') as mock_warning:
            with patch('src.editor_plantillas.simpledialog.askstring', side_effect=['TestProvider', 'B12345678', 'test_provider']):
                with patch('builtins.open', mock_open()):
                    with patch('os.makedirs'):
                        editor.guardar_plantilla()

            # Verificar que se mostró advertencia sobre campos de identificación
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0]
            assert 'identificación' in call_args[0].lower() or 'identificación' in call_args[1].lower()


@pytest.mark.unit
class TestEditorPlantillasCargar:
    """Tests para cargar plantillas."""

    @patch('src.editor_plantillas.pdfplumber.open')
    @patch('src.editor_plantillas.tk.Tk')
    @patch('src.editor_plantillas.filedialog.askopenfilename')
    def test_cargar_plantilla_actualiza_campos(self, mock_filedialog, mock_tk, mock_pdf_open):
        """Test que cargar plantilla actualiza los campos correctamente."""
        # Mock PDF
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.width = 595
        mock_page.height = 842
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        # Mock Tk
        mock_root = MagicMock()
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080
        mock_tk.return_value = mock_root

        # Crear editor
        editor = EditorPlantillas("test.pdf")

        # Mock filedialog para retornar un archivo
        mock_filedialog.return_value = "test_plantilla.json"

        # Plantilla a cargar
        plantilla_json = {
            "nombre_proveedor": "Provider Test",
            "cif_proveedor": "B99999999",
            "campos": [
                {"nombre": "CIF_Identificacion", "coordenadas": [10, 10, 100, 30], "tipo": "texto"},
                {"nombre": "FechaFactura", "coordenadas": [10, 50, 100, 70], "tipo": "fecha"}
            ]
        }

        # Mock open para leer el JSON
        with patch('builtins.open', mock_open(read_data=json.dumps(plantilla_json))):
            # Mock método que redibuja (requiere canvas)
            editor.redibujar_campos = Mock()
            editor.actualizar_lista_campos = Mock()

            # Cargar plantilla
            editor.cargar_plantilla()

        # Verificar que se cargaron las coordenadas
        assert editor.campos['CIF_Identificacion'] == [10, 10, 100, 30]
        assert editor.campos['FechaFactura'] == [10, 50, 100, 70]


@pytest.mark.unit
class TestEditorPlantillasSeleccion:
    """Tests para selección y captura de campos."""

    @patch('src.editor_plantillas.pdfplumber.open')
    @patch('src.editor_plantillas.tk.Tk')
    def test_seleccionar_campo_para_captura(self, mock_tk, mock_pdf_open):
        """Test que seleccionar campo para captura actualiza el estado."""
        # Mock PDF
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.width = 595
        mock_page.height = 842
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        # Mock Tk
        mock_root = MagicMock()
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080
        mock_tk.return_value = mock_root

        # Crear editor
        editor = EditorPlantillas("test.pdf")
        editor.label_seleccionado = Mock()  # Mock del label

        # Seleccionar campo
        editor.seleccionar_campo_para_captura("FechaFactura")

        # Verificar que el campo seleccionado cambió
        assert editor.campo_seleccionado == "FechaFactura"

        # Verificar que se actualizó el label
        editor.label_seleccionado.config.assert_called()
        call_args = editor.label_seleccionado.config.call_args
        assert "FechaFactura" in str(call_args)


@pytest.mark.integration
class TestEditorPlantillasIntegracion:
    """Tests de integración para flujos completos."""

    @patch('src.editor_plantillas.pdfplumber.open')
    @patch('src.editor_plantillas.tk.Tk')
    def test_flujo_crear_plantilla_desde_cero(self, mock_tk, mock_pdf_open, tmp_path):
        """Test flujo completo: crear plantilla desde cero."""
        # Mock PDF
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.width = 595
        mock_page.height = 842
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        # Mock Tk
        mock_root = MagicMock()
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080
        mock_tk.return_value = mock_root

        # Crear editor
        editor = EditorPlantillas("test.pdf")

        # Simular captura de TODOS los campos (ahora con estructura de página)
        editor.campos['CIF_Identificacion'] = {'coordenadas': [50, 30, 200, 50], 'pagina': 0}
        editor.campos['Nombre_Identificacion'] = {'coordenadas': [50, 60, 200, 80], 'pagina': 0}
        editor.campos['FechaFactura'] = {'coordenadas': [50, 100, 150, 120], 'pagina': 0}
        editor.campos['FechaVto'] = {'coordenadas': [50, 130, 150, 150], 'pagina': 0}
        editor.campos['NumFactura'] = {'coordenadas': [200, 100, 300, 120], 'pagina': 0}
        editor.campos['Base'] = {'coordenadas': [200, 130, 300, 150], 'pagina': 0}

        # Guardar plantilla con todos los campos
        with patch('src.editor_plantillas.simpledialog.askstring', side_effect=['TestProvider', 'B11111111', 'test_provider']):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('os.makedirs'):
                    editor.root.destroy = Mock()
                    editor.guardar_plantilla()

        # Verificar que se llamó a write (archivo JSON se guardó)
        mock_file.assert_called()


# Tests para funciones standalone si las hay
@pytest.mark.unit
class TestFuncionesAuxiliares:
    """Tests para funciones auxiliares del módulo."""

    def test_main_ejecutable(self):
        """Test que main() es llamable (aunque no lo ejecutemos)."""
        from src.editor_plantillas import main
        assert callable(main)
