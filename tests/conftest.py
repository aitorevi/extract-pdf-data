"""
Fixtures compartidas para todos los tests.
"""
import pytest
import os
import json
from pathlib import Path


@pytest.fixture
def project_root():
    """Devuelve la ruta raíz del proyecto."""
    return Path(__file__).parent.parent


@pytest.fixture
def facturas_dir(project_root):
    """Devuelve la ruta del directorio de facturas."""
    return project_root / "facturas"


@pytest.fixture
def plantillas_dir(project_root):
    """Devuelve la ruta del directorio de plantillas."""
    return project_root / "plantillas"


@pytest.fixture
def resultados_dir(project_root):
    """Devuelve la ruta del directorio de resultados."""
    return project_root / "resultados"


@pytest.fixture
def temp_facturas_dir(tmp_path):
    """Crea un directorio temporal para facturas de test."""
    facturas = tmp_path / "facturas"
    facturas.mkdir()
    return facturas


@pytest.fixture
def temp_plantillas_dir(tmp_path):
    """Crea un directorio temporal para plantillas de test."""
    plantillas = tmp_path / "plantillas"
    plantillas.mkdir()
    return plantillas


@pytest.fixture
def temp_resultados_dir(tmp_path):
    """Crea un directorio temporal para resultados de test."""
    resultados = tmp_path / "resultados"
    resultados.mkdir()
    return resultados


@pytest.fixture
def plantilla_valida():
    """Devuelve una plantilla válida de ejemplo."""
    return {
        "proveedor_id": "TEST_001",
        "nombre_proveedor": "Proveedor Test",
        "identificadores": ["TEST", "PROVEEDOR TEST"],
        "campos": [
            {
                "nombre": "numero_factura",
                "tipo": "texto",
                "x0": 100,
                "top": 100,
                "x1": 200,
                "bottom": 120
            },
            {
                "nombre": "fecha",
                "tipo": "fecha",
                "x0": 100,
                "top": 130,
                "x1": 200,
                "bottom": 150
            },
            {
                "nombre": "total",
                "tipo": "numerico",
                "x0": 100,
                "top": 160,
                "x1": 200,
                "bottom": 180
            }
        ]
    }


@pytest.fixture
def plantilla_invalida():
    """Devuelve una plantilla inválida para tests de error."""
    return {
        "proveedor_id": "INVALID",
        # Falta nombre_proveedor
        "campos": []  # Sin campos
    }


@pytest.fixture
def datos_factura_ejemplo():
    """Devuelve datos de factura de ejemplo para tests de exportación."""
    return [
        {
            "Archivo": "factura_001.pdf",
            "Proveedor": "Proveedor Test",
            "Numero_Factura": "FAC-001",
            "Fecha": "2025-01-23",
            "Base_Imponible": 100.00,
            "IVA": 21.00,
            "Total": 121.00,
            "Fecha_Procesamiento": "2025-01-23 12:00:00"
        },
        {
            "Archivo": "factura_002.pdf",
            "Proveedor": "Proveedor Test 2",
            "Numero_Factura": "FAC-002",
            "Fecha": "2025-01-24",
            "Base_Imponible": 200.00,
            "IVA": 42.00,
            "Total": 242.00,
            "Fecha_Procesamiento": "2025-01-23 12:01:00"
        }
    ]


@pytest.fixture
def sample_plantilla_file(temp_plantillas_dir, plantilla_valida):
    """Crea un archivo de plantilla de ejemplo."""
    plantilla_path = temp_plantillas_dir / "test_plantilla.json"
    with open(plantilla_path, 'w', encoding='utf-8') as f:
        json.dump(plantilla_valida, f, indent=2)
    return plantilla_path


# Markers personalizados para facilitar ejecución selectiva de tests
def pytest_configure(config):
    """Configuración personalizada de pytest."""
    config.addinivalue_line(
        "markers", "unit: marca un test como test unitario"
    )
    config.addinivalue_line(
        "markers", "integration: marca un test como test de integración"
    )
    config.addinivalue_line(
        "markers", "slow: marca un test como lento"
    )
    config.addinivalue_line(
        "markers", "smoke: marca un test como smoke test"
    )
