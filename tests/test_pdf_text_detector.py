"""
Tests para el módulo utils/pdf_text_detector.py - Detección de texto en PDFs.

Este módulo prueba las funciones de detección de texto extraíble y corrupto en PDFs.
"""

import pytest
from src.utils.pdf_text_detector import tiene_texto_corrupto_cid


@pytest.mark.unit
class TestDeteccionTextoCID:
    """Tests para detección de códigos CID en texto extraído."""

    def test_texto_corrupto_cid_simple(self):
        """Test con texto completamente corrupto con CID."""
        texto = "(cid:24)(cid:1)(cid:23)(cid:1)(cid:21)(cid:25)(cid:22)(cid:25)(cid:21)(cid:25)"
        assert tiene_texto_corrupto_cid(texto) is True

    def test_texto_normal_sin_cid(self):
        """Test con texto normal sin códigos CID."""
        texto = "Factura número 12345 del 20/10/2025"
        assert tiene_texto_corrupto_cid(texto) is False

    def test_texto_mixto_bajo_umbral(self):
        """Test con texto mayormente normal con pocos CID."""
        # Solo 1 CID en 50+ caracteres = ~2% (debajo del umbral de 10%)
        texto = "Factura normal con texto legible (cid:1) y más contenido normal aquí"
        assert tiene_texto_corrupto_cid(texto) is False

    def test_texto_mixto_sobre_umbral(self):
        """Test con texto con muchos CID (sobre el umbral)."""
        # 5 CID en ~20 caracteres = 25% (sobre el umbral de 10%)
        texto = "(cid:1)(cid:2)(cid:3)(cid:4)(cid:5) texto normal"
        assert tiene_texto_corrupto_cid(texto) is True

    def test_texto_vacio(self):
        """Test con string vacío."""
        assert tiene_texto_corrupto_cid("") is False

    def test_texto_solo_espacios(self):
        """Test con solo espacios."""
        assert tiene_texto_corrupto_cid("   ") is False

    def test_umbral_personalizado(self):
        """Test con umbral personalizado."""
        # 2 CID en 20 caracteres = 10%
        texto = "(cid:1)(cid:2) texto normal aquí"

        # Con umbral de 5%, debería detectarse como corrupto
        assert tiene_texto_corrupto_cid(texto, umbral_porcentaje=5.0) is True

        # Con umbral de 15%, no debería detectarse
        assert tiene_texto_corrupto_cid(texto, umbral_porcentaje=15.0) is False

    def test_cid_con_numeros_largos(self):
        """Test con CID que tienen números de varios dígitos."""
        texto = "(cid:1234)(cid:5678)(cid:999)"
        assert tiene_texto_corrupto_cid(texto) is True

    def test_fecha_corrupta_cid(self):
        """Test con fecha corrupta como en el caso real."""
        texto = "(cid:21)(cid:22)(cid:23)(cid:24)(cid:22)(cid:23)(cid:21)(cid:22)(cid:21)(cid:25)"
        assert tiene_texto_corrupto_cid(texto) is True

    def test_cif_corrupto_cid(self):
        """Test con CIF corrupto como en el caso real."""
        texto = "(cid:1)(cid:5)� (cid:25)!(cid:22) ,&(cid:1)"
        assert tiene_texto_corrupto_cid(texto) is True


@pytest.mark.unit
class TestDeteccionTextoCIDEdgeCases:
    """Tests de casos extremos para detección de CID."""

    def test_cid_sin_numero(self):
        """Test con patrón similar a CID pero sin número (no debería detectarse)."""
        texto = "(cid:) normal text here"
        assert tiene_texto_corrupto_cid(texto) is False

    def test_cid_malformado(self):
        """Test con CID malformado (no debería detectarse)."""
        texto = "(cid 123) normal text"
        assert tiene_texto_corrupto_cid(texto) is False

    def test_texto_con_parentesis_normales(self):
        """Test con paréntesis normales que no son CID."""
        texto = "Factura (12345) emitida el día (20/10/2025)"
        assert tiene_texto_corrupto_cid(texto) is False

    def test_umbral_cero(self):
        """Test con umbral de 0% (cualquier CID debería detectarse)."""
        texto = "Mucho texto normal aquí con contenido legible (cid:1) y más texto"
        assert tiene_texto_corrupto_cid(texto, umbral_porcentaje=0.0) is True

    def test_umbral_cien(self):
        """Test con umbral de 100% (nunca debería detectarse)."""
        texto = "(cid:1)(cid:2)(cid:3)(cid:4)(cid:5)"
        # Incluso con 100% de CID, con umbral de 100% no se detecta
        assert tiene_texto_corrupto_cid(texto, umbral_porcentaje=100.0) is False
