"""
Test de ejemplo para verificar que pytest está configurado correctamente.
"""
import pytest


@pytest.mark.smoke
def test_pytest_works():
    """Test básico para verificar que pytest funciona."""
    assert True


@pytest.mark.smoke
def test_fixtures_work(project_root):
    """Test para verificar que las fixtures funcionan."""
    assert project_root.exists()
    assert project_root.is_dir()


@pytest.mark.unit
def test_plantilla_valida_fixture(plantilla_valida):
    """Test para verificar que la fixture de plantilla válida funciona."""
    assert "proveedor_id" in plantilla_valida
    assert "nombre_proveedor" in plantilla_valida
    assert "campos" in plantilla_valida
    assert len(plantilla_valida["campos"]) > 0


@pytest.mark.unit
def test_datos_factura_ejemplo_fixture(datos_factura_ejemplo):
    """Test para verificar que la fixture de datos de ejemplo funciona."""
    assert isinstance(datos_factura_ejemplo, list)
    assert len(datos_factura_ejemplo) > 0
    assert "Numero_Factura" in datos_factura_ejemplo[0]


@pytest.mark.unit
def test_temp_directories(temp_facturas_dir, temp_plantillas_dir, temp_resultados_dir):
    """Test para verificar que los directorios temporales se crean correctamente."""
    assert temp_facturas_dir.exists()
    assert temp_plantillas_dir.exists()
    assert temp_resultados_dir.exists()

    # Verificar que son directorios
    assert temp_facturas_dir.is_dir()
    assert temp_plantillas_dir.is_dir()
    assert temp_resultados_dir.is_dir()


@pytest.mark.parametrize("value,expected", [
    (1 + 1, 2),
    (2 * 3, 6),
    (10 - 5, 5),
])
def test_parametrize_example(value, expected):
    """Test de ejemplo usando parametrize."""
    assert value == expected
