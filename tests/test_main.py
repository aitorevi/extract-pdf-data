"""
Tests para el módulo main.py - Script principal de la aplicación.

Valida que:
1. FacturaExtractorApp se inicializa correctamente
2. Banner se muestra correctamente
3. Verificación de estructura del proyecto funciona
4. Modo coordenadas ejecuta el editor de plantillas
5. Modo procesamiento extrae datos y exporta
6. Estadísticas se muestran correctamente
7. Exportación en diferentes formatos funciona
8. CLI procesa argumentos correctamente
9. Modo interactivo funciona con diferentes opciones
10. Validación de inputs (trimestre, año) funciona
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO
from src.main import FacturaExtractorApp, main


class TestFacturaExtractorAppInit:
    """Tests para inicialización de la aplicación."""

    def test_init_crea_instancia_correcta(self):
        """Test que __init__ crea instancia con atributos correctos."""
        app = FacturaExtractorApp()

        assert app.pdf_extractor is None
        assert app.exporter is None

    def test_mostrar_banner_imprime_texto(self, capsys):
        """Test que mostrar_banner imprime el banner."""
        app = FacturaExtractorApp()
        app.mostrar_banner()

        captured = capsys.readouterr()
        assert "EXTRACTOR DE DATOS DE FACTURAS PDF" in captured.out
        assert "Versión 1.0" in captured.out
        assert "=" in captured.out


class TestVerificarEstructura:
    """Tests para verificación de estructura del proyecto."""

    def test_verificar_estructura_crea_directorios_faltantes(self, tmp_path, monkeypatch, capsys):
        """Test que crea directorios si no existen."""
        # Cambiar al directorio temporal
        monkeypatch.chdir(tmp_path)

        # Crear solo plantillas con un archivo JSON
        plantillas_dir = tmp_path / "plantillas"
        plantillas_dir.mkdir()
        (plantillas_dir / "test.json").touch()

        app = FacturaExtractorApp()
        resultado = app.verificar_estructura_proyecto()

        # Debe crear facturas y resultados
        assert (tmp_path / "facturas").exists()
        assert (tmp_path / "resultados").exists()
        assert resultado is True

        captured = capsys.readouterr()
        assert "Directorio creado: facturas/" in captured.out
        assert "Directorio creado: resultados/" in captured.out

    def test_verificar_estructura_detecta_falta_plantillas(self, tmp_path, monkeypatch, capsys):
        """Test que detecta cuando no hay plantillas JSON."""
        monkeypatch.chdir(tmp_path)

        # Crear directorios pero sin plantillas
        (tmp_path / "plantillas").mkdir()
        (tmp_path / "facturas").mkdir()
        (tmp_path / "resultados").mkdir()

        app = FacturaExtractorApp()
        resultado = app.verificar_estructura_proyecto()

        assert resultado is False
        captured = capsys.readouterr()
        assert "No se encontraron plantillas JSON" in captured.out

    def test_verificar_estructura_avisa_sin_pdfs(self, tmp_path, monkeypatch, capsys):
        """Test que avisa cuando no hay archivos PDF."""
        monkeypatch.chdir(tmp_path)

        # Crear estructura completa pero sin PDFs
        plantillas_dir = tmp_path / "plantillas"
        plantillas_dir.mkdir()
        (plantillas_dir / "test.json").touch()
        (tmp_path / "facturas").mkdir()
        (tmp_path / "resultados").mkdir()

        app = FacturaExtractorApp()
        resultado = app.verificar_estructura_proyecto()

        assert resultado is True  # Sigue siendo válido
        captured = capsys.readouterr()
        assert "WARN No se encontraron archivos PDF" in captured.out

    def test_verificar_estructura_con_proyecto_completo(self, tmp_path, monkeypatch, capsys):
        """Test con estructura completa y correcta."""
        monkeypatch.chdir(tmp_path)

        # Crear estructura completa
        plantillas_dir = tmp_path / "plantillas"
        plantillas_dir.mkdir()
        (plantillas_dir / "test.json").touch()

        facturas_dir = tmp_path / "facturas"
        facturas_dir.mkdir()
        (facturas_dir / "test.pdf").touch()

        (tmp_path / "resultados").mkdir()

        app = FacturaExtractorApp()
        resultado = app.verificar_estructura_proyecto()

        assert resultado is True
        captured = capsys.readouterr()
        assert "OK Estructura del proyecto verificada correctamente" in captured.out


class TestModosCoordenadas:
    """Tests para modo de extracción de coordenadas."""

    @patch('subprocess.run')
    def test_modo_coordenadas_ejecuta_editor(self, mock_run, capsys):
        """Test que modo_coordenadas ejecuta el editor de plantillas."""
        app = FacturaExtractorApp()
        app.modo_coordenadas()

        # Verificar que se llamó subprocess.run
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == sys.executable
        assert "editor_plantillas.py" in args[1]

        captured = capsys.readouterr()
        assert "MODO: EDITOR DE PLANTILLAS" in captured.out

    @patch('subprocess.run', side_effect=Exception("Test error"))
    def test_modo_coordenadas_maneja_error(self, mock_run, capsys):
        """Test que maneja errores al ejecutar el editor."""
        app = FacturaExtractorApp()
        app.modo_coordenadas()

        captured = capsys.readouterr()
        assert "Error ejecutando editor de plantillas" in captured.out


class TestModoProcesamiento:
    """Tests para modo de procesamiento de facturas."""

    @patch('builtins.input', side_effect=['1', '2025'])
    @patch('src.main.PDFExtractor')
    def test_modo_procesamiento_valida_trimestre_correcto(self, mock_extractor_class, mock_input, capsys):
        """Test que valida trimestre correcto (1-4)."""
        # Configurar mocks
        mock_extractor = MagicMock()
        mock_extractor.cargar_plantillas.return_value = True
        mock_extractor.procesar_directorio_facturas.return_value = [{'CIF': 'test'}]
        mock_extractor.obtener_estadisticas.return_value = {
            'total_facturas': 1,
            'facturas_exitosas': 1,
            'tasa_exito': 100,
            'facturas_duplicadas': 0,
            'facturas_con_error': 0,
            'plantillas_disponibles': 1,
            'proveedores': {}
        }
        mock_extractor_class.return_value = mock_extractor

        app = FacturaExtractorApp()
        resultado = app.modo_procesamiento(auto_export=False)

        assert resultado is True
        captured = capsys.readouterr()
        assert "✓ Trimestre: 1T" in captured.out
        assert "✓ Año: 2025" in captured.out

    @patch('builtins.input', side_effect=['5', '2025'])
    def test_modo_procesamiento_rechaza_trimestre_invalido(self, mock_input, capsys):
        """Test que rechaza trimestre inválido."""
        app = FacturaExtractorApp()
        resultado = app.modo_procesamiento(auto_export=False)

        assert resultado is False
        captured = capsys.readouterr()
        assert "ERROR: Trimestre '5' no válido" in captured.out

    @patch('builtins.input', side_effect=['1', 'abc'])
    def test_modo_procesamiento_rechaza_año_invalido(self, mock_input, capsys):
        """Test que rechaza año inválido."""
        app = FacturaExtractorApp()
        resultado = app.modo_procesamiento(auto_export=False)

        assert resultado is False
        captured = capsys.readouterr()
        assert "ERROR: Año 'abc' no válido" in captured.out

    @patch('builtins.input', side_effect=['1', '25'])
    def test_modo_procesamiento_rechaza_año_corto(self, mock_input, capsys):
        """Test que rechaza año de menos de 4 dígitos."""
        app = FacturaExtractorApp()
        resultado = app.modo_procesamiento(auto_export=False)

        assert resultado is False
        captured = capsys.readouterr()
        assert "ERROR: Año '25' no válido" in captured.out

    @patch('builtins.input', side_effect=['2', '2025'])
    @patch('src.main.PDFExtractor')
    def test_modo_procesamiento_falla_sin_plantillas(self, mock_extractor_class, mock_input, capsys):
        """Test cuando no se pueden cargar plantillas."""
        mock_extractor = MagicMock()
        mock_extractor.cargar_plantillas.return_value = False
        mock_extractor_class.return_value = mock_extractor

        app = FacturaExtractorApp()
        resultado = app.modo_procesamiento(auto_export=False)

        assert resultado is False
        captured = capsys.readouterr()
        assert "ERROR: No se pudieron cargar plantillas" in captured.out

    @patch('builtins.input', side_effect=['3', '2025'])
    @patch('src.main.PDFExtractor')
    def test_modo_procesamiento_falla_sin_facturas(self, mock_extractor_class, mock_input, capsys):
        """Test cuando no hay facturas para procesar."""
        mock_extractor = MagicMock()
        mock_extractor.cargar_plantillas.return_value = True
        mock_extractor.procesar_directorio_facturas.return_value = []
        mock_extractor_class.return_value = mock_extractor

        app = FacturaExtractorApp()
        resultado = app.modo_procesamiento(auto_export=False)

        assert resultado is False
        captured = capsys.readouterr()
        assert "ERROR No se procesaron facturas" in captured.out

    @patch('builtins.input', side_effect=['4', '2025'])
    @patch('src.main.PDFExtractor')
    @patch('src.main.ExcelExporter')
    def test_modo_procesamiento_exporta_automaticamente(self, mock_exporter_class, mock_extractor_class, mock_input, capsys):
        """Test que exporta automáticamente cuando auto_export=True."""
        # Configurar mock extractor
        mock_extractor = MagicMock()
        mock_extractor.cargar_plantillas.return_value = True
        mock_extractor.procesar_directorio_facturas.return_value = [{'CIF': 'test'}]
        mock_extractor.obtener_estadisticas.return_value = {
            'total_facturas': 1,
            'facturas_exitosas': 1,
            'tasa_exito': 100,
            'facturas_duplicadas': 0,
            'facturas_con_error': 0,
            'plantillas_disponibles': 1,
            'proveedores': {}
        }
        mock_extractor_class.return_value = mock_extractor

        # Configurar mock exporter
        mock_exporter = MagicMock()
        mock_exporter.exportar_excel_formateado.return_value = "test.xlsx"
        mock_exporter.exportar_excel_completo.return_value = "test_debug.xlsx"
        mock_exporter.exportar_csv.return_value = "test.csv"
        mock_exporter.exportar_json.return_value = "test.json"
        mock_exporter.exportar_excel_basico.return_value = "test_basico.xlsx"
        mock_exporter_class.return_value = mock_exporter

        app = FacturaExtractorApp()
        resultado = app.modo_procesamiento(auto_export=True, formato_salida="todos")

        assert resultado is True
        captured = capsys.readouterr()
        assert "EXPORTANDO RESULTADOS" in captured.out
        assert "OK Exportación completada" in captured.out


class TestMostrarEstadisticas:
    """Tests para mostrar estadísticas."""

    def test_mostrar_estadisticas_basicas(self, capsys):
        """Test que muestra estadísticas básicas correctamente."""
        app = FacturaExtractorApp()
        stats = {
            'total_facturas': 10,
            'facturas_exitosas': 8,
            'tasa_exito': 80,
            'facturas_duplicadas': 1,
            'facturas_con_error': 1,
            'plantillas_disponibles': 3,
            'proveedores': {}
        }

        app.mostrar_estadisticas(stats)

        captured = capsys.readouterr()
        assert "RESUMEN DEL PROCESAMIENTO" in captured.out
        assert "Total facturas: 10" in captured.out
        assert "Procesadas exitosamente: 8 (80%)" in captured.out
        assert "Duplicadas (excluidas): 1" in captured.out
        assert "Con errores: 1" in captured.out

    def test_mostrar_estadisticas_con_proveedores(self, capsys):
        """Test que muestra detalle por proveedor."""
        app = FacturaExtractorApp()
        stats = {
            'total_facturas': 5,
            'facturas_exitosas': 5,
            'tasa_exito': 100,
            'facturas_duplicadas': 0,
            'facturas_con_error': 0,
            'plantillas_disponibles': 2,
            'proveedores': {
                'proveedor1': {'total': 3, 'exitosos': 3},
                'proveedor2': {'total': 2, 'exitosos': 2}
            }
        }

        app.mostrar_estadisticas(stats)

        captured = capsys.readouterr()
        assert "DETALLE POR PROVEEDOR" in captured.out
        assert "proveedor1: 3/3 exitosas" in captured.out
        assert "proveedor2: 2/2 exitosas" in captured.out


class TestExportarResultados:
    """Tests para exportación de resultados."""

    @patch('src.main.ExcelExporter')
    def test_exportar_resultados_formato_excel(self, mock_exporter_class, capsys):
        """Test exportación solo formato Excel."""
        mock_exporter = MagicMock()
        mock_exporter.exportar_excel_formateado.return_value = "test.xlsx"
        mock_exporter.exportar_excel_completo.return_value = "test_debug.xlsx"
        mock_exporter_class.return_value = mock_exporter

        app = FacturaExtractorApp()
        resultado = app.exportar_resultados([{'CIF': 'test'}], formato="excel")

        assert resultado is True
        mock_exporter.exportar_excel_formateado.assert_called_once()
        mock_exporter.exportar_excel_completo.assert_called_once()
        mock_exporter.exportar_csv.assert_not_called()
        mock_exporter.exportar_json.assert_not_called()

    @patch('src.main.ExcelExporter')
    def test_exportar_resultados_formato_csv(self, mock_exporter_class, capsys):
        """Test exportación solo formato CSV."""
        mock_exporter = MagicMock()
        mock_exporter.exportar_csv.return_value = "test.csv"
        mock_exporter_class.return_value = mock_exporter

        app = FacturaExtractorApp()
        resultado = app.exportar_resultados([{'CIF': 'test'}], formato="csv")

        assert resultado is True
        mock_exporter.exportar_csv.assert_called_once()
        mock_exporter.exportar_excel_formateado.assert_not_called()

    @patch('src.main.ExcelExporter')
    def test_exportar_resultados_formato_json(self, mock_exporter_class, capsys):
        """Test exportación solo formato JSON."""
        mock_exporter = MagicMock()
        mock_exporter.exportar_json.return_value = "test.json"
        mock_exporter_class.return_value = mock_exporter

        app = FacturaExtractorApp()
        resultado = app.exportar_resultados([{'CIF': 'test'}], formato="json")

        assert resultado is True
        mock_exporter.exportar_json.assert_called_once()
        mock_exporter.exportar_excel_formateado.assert_not_called()

    @patch('src.main.ExcelExporter')
    def test_exportar_resultados_formato_todos(self, mock_exporter_class, capsys):
        """Test exportación todos los formatos."""
        mock_exporter = MagicMock()
        mock_exporter.exportar_excel_formateado.return_value = "test.xlsx"
        mock_exporter.exportar_excel_completo.return_value = "test_debug.xlsx"
        mock_exporter.exportar_csv.return_value = "test.csv"
        mock_exporter.exportar_json.return_value = "test.json"
        mock_exporter.exportar_excel_basico.return_value = "test_basico.xlsx"
        mock_exporter_class.return_value = mock_exporter

        app = FacturaExtractorApp()
        resultado = app.exportar_resultados([{'CIF': 'test'}], formato="todos")

        assert resultado is True
        mock_exporter.exportar_excel_formateado.assert_called_once()
        mock_exporter.exportar_excel_completo.assert_called_once()
        mock_exporter.exportar_csv.assert_called_once()
        mock_exporter.exportar_json.assert_called_once()
        mock_exporter.exportar_excel_basico.assert_called_once()

    @patch('src.main.ExcelExporter', side_effect=Exception("Export error"))
    def test_exportar_resultados_maneja_errores(self, mock_exporter_class, capsys):
        """Test que maneja errores durante la exportación."""
        app = FacturaExtractorApp()
        resultado = app.exportar_resultados([{'CIF': 'test'}], formato="excel")

        assert resultado is False
        captured = capsys.readouterr()
        assert "ERROR durante la exportación" in captured.out


class TestModoAyuda:
    """Tests para modo de ayuda."""

    def test_modo_ayuda_muestra_informacion_completa(self, capsys):
        """Test que modo_ayuda muestra toda la información."""
        app = FacturaExtractorApp()
        app.modo_ayuda()

        captured = capsys.readouterr()
        assert "GUÍA DE USO" in captured.out
        assert "PREPARAR EL ENTORNO" in captured.out
        assert "CREAR PLANTILLAS" in captured.out
        assert "PROCESAR FACTURAS" in captured.out
        assert "python main.py coordenadas" in captured.out
        assert "python main.py procesar" in captured.out


class TestEjecutarCLI:
    """Tests para interfaz de línea de comandos."""

    @patch('sys.argv', ['main.py', 'ayuda'])
    def test_cli_comando_ayuda(self, capsys):
        """Test comando ayuda en CLI."""
        app = FacturaExtractorApp()
        app.ejecutar_cli()

        captured = capsys.readouterr()
        assert "GUÍA DE USO" in captured.out

    @patch('sys.argv', ['main.py', 'verificar'])
    def test_cli_comando_verificar(self, tmp_path, monkeypatch, capsys):
        """Test comando verificar en CLI."""
        monkeypatch.chdir(tmp_path)

        # Crear estructura mínima
        plantillas_dir = tmp_path / "plantillas"
        plantillas_dir.mkdir()
        (plantillas_dir / "test.json").touch()
        (tmp_path / "facturas").mkdir()
        (tmp_path / "resultados").mkdir()

        app = FacturaExtractorApp()
        app.ejecutar_cli()

        captured = capsys.readouterr()
        assert "OK Verificación completada" in captured.out

    @patch('sys.argv', ['main.py', 'coordenadas'])
    @patch('subprocess.run')
    def test_cli_comando_coordenadas(self, mock_run, tmp_path, monkeypatch, capsys):
        """Test comando coordenadas en CLI."""
        monkeypatch.chdir(tmp_path)

        # Crear estructura mínima
        plantillas_dir = tmp_path / "plantillas"
        plantillas_dir.mkdir()
        (plantillas_dir / "test.json").touch()
        (tmp_path / "facturas").mkdir()
        (tmp_path / "resultados").mkdir()

        app = FacturaExtractorApp()
        app.ejecutar_cli()

        mock_run.assert_called_once()
        captured = capsys.readouterr()
        assert "MODO: EDITOR DE PLANTILLAS" in captured.out

    @patch('sys.argv', ['main.py'])
    def test_cli_sin_argumentos_muestra_ayuda(self, capsys):
        """Test que sin argumentos muestra el help del parser."""
        app = FacturaExtractorApp()
        app.ejecutar_cli()

        captured = capsys.readouterr()
        assert "EXTRACTOR DE DATOS DE FACTURAS PDF" in captured.out  # Banner
        # El parser.print_help() imprime la ayuda


class TestEjecutarInteractivo:
    """Tests para modo interactivo."""

    @patch('builtins.input', side_effect=['5'])  # Salir
    def test_interactivo_opcion_salir(self, mock_input, tmp_path, monkeypatch, capsys):
        """Test opción salir en modo interactivo."""
        monkeypatch.chdir(tmp_path)

        # Crear estructura mínima
        plantillas_dir = tmp_path / "plantillas"
        plantillas_dir.mkdir()
        (plantillas_dir / "test.json").touch()
        (tmp_path / "facturas").mkdir()
        (tmp_path / "resultados").mkdir()

        app = FacturaExtractorApp()
        app.ejecutar_interactivo()

        captured = capsys.readouterr()
        assert "MENÚ PRINCIPAL" in captured.out
        assert "Hasta luego!" in captured.out

    @patch('builtins.input', side_effect=['3', '5'])  # Ayuda, luego Salir
    def test_interactivo_opcion_ayuda(self, mock_input, tmp_path, monkeypatch, capsys):
        """Test opción ayuda en modo interactivo."""
        monkeypatch.chdir(tmp_path)

        # Crear estructura mínima
        plantillas_dir = tmp_path / "plantillas"
        plantillas_dir.mkdir()
        (plantillas_dir / "test.json").touch()
        (tmp_path / "facturas").mkdir()
        (tmp_path / "resultados").mkdir()

        app = FacturaExtractorApp()
        app.ejecutar_interactivo()

        captured = capsys.readouterr()
        assert "GUÍA DE USO" in captured.out

    @patch('builtins.input', side_effect=['4', '5'])  # Verificar, luego Salir
    def test_interactivo_opcion_verificar(self, mock_input, tmp_path, monkeypatch, capsys):
        """Test opción verificar en modo interactivo."""
        monkeypatch.chdir(tmp_path)

        # Crear estructura mínima
        plantillas_dir = tmp_path / "plantillas"
        plantillas_dir.mkdir()
        (plantillas_dir / "test.json").touch()
        (tmp_path / "facturas").mkdir()
        (tmp_path / "resultados").mkdir()

        app = FacturaExtractorApp()
        app.ejecutar_interactivo()

        captured = capsys.readouterr()
        assert "OK Estructura del proyecto verificada correctamente" in captured.out

    @patch('builtins.input', side_effect=['1', '5'])  # Coordenadas, luego Salir
    @patch('subprocess.run')
    def test_interactivo_opcion_coordenadas(self, mock_run, mock_input, tmp_path, monkeypatch, capsys):
        """Test opción coordenadas en modo interactivo."""
        monkeypatch.chdir(tmp_path)

        # Crear estructura mínima
        plantillas_dir = tmp_path / "plantillas"
        plantillas_dir.mkdir()
        (plantillas_dir / "test.json").touch()
        (tmp_path / "facturas").mkdir()
        (tmp_path / "resultados").mkdir()

        app = FacturaExtractorApp()
        app.ejecutar_interactivo()

        mock_run.assert_called_once()
        captured = capsys.readouterr()
        assert "MODO: EDITOR DE PLANTILLAS" in captured.out

    @patch('builtins.input', side_effect=['9', '5'])  # Opción inválida, luego Salir
    def test_interactivo_opcion_invalida(self, mock_input, tmp_path, monkeypatch, capsys):
        """Test opción inválida en modo interactivo."""
        monkeypatch.chdir(tmp_path)

        # Crear estructura mínima
        plantillas_dir = tmp_path / "plantillas"
        plantillas_dir.mkdir()
        (plantillas_dir / "test.json").touch()
        (tmp_path / "facturas").mkdir()
        (tmp_path / "resultados").mkdir()

        app = FacturaExtractorApp()
        app.ejecutar_interactivo()

        captured = capsys.readouterr()
        assert "Opción no válida" in captured.out


class TestMainFunction:
    """Tests para la función main()."""

    @patch('sys.argv', ['main.py', 'ayuda'])
    def test_main_con_argumentos_usa_cli(self, capsys):
        """Test que con argumentos usa modo CLI."""
        main()

        captured = capsys.readouterr()
        assert "EXTRACTOR DE DATOS DE FACTURAS PDF" in captured.out
        assert "GUÍA DE USO" in captured.out

    @patch('sys.argv', ['main.py'])
    @patch('builtins.input', side_effect=['5'])  # Salir inmediatamente
    def test_main_sin_argumentos_usa_interactivo(self, mock_input, tmp_path, monkeypatch, capsys):
        """Test que sin argumentos usa modo interactivo."""
        monkeypatch.chdir(tmp_path)

        # Crear estructura mínima
        plantillas_dir = tmp_path / "plantillas"
        plantillas_dir.mkdir()
        (plantillas_dir / "test.json").touch()
        (tmp_path / "facturas").mkdir()
        (tmp_path / "resultados").mkdir()

        main()

        captured = capsys.readouterr()
        assert "MENÚ PRINCIPAL" in captured.out
        assert "Hasta luego!" in captured.out
