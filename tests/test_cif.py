"""
Tests para el Value Object CIF (Código de Identificación Fiscal).

Tests que cubren:
- Saneamiento: trim, quitar guiones, barras, espacios
- Normalización a mayúsculas
- Validación de formato
- Comparación de CIFs
"""

import pytest
from src.utils.cif import CIF


class TestCIFSaneamiento:
    """Tests para el saneamiento de CIFs."""

    def test_cif_sin_espacios(self):
        """CIF sin espacios se mantiene igual (normalizado a mayúsculas)."""
        cif = CIF("E98530876")
        assert cif.value == "E98530876"

    def test_cif_con_espacios_inicio_fin(self):
        """CIF con espacios al inicio y fin se limpia."""
        cif = CIF("  E98530876  ")
        assert cif.value == "E98530876"

    def test_cif_con_espacios_medio(self):
        """CIF con espacios en medio se eliminan."""
        cif = CIF("E 9 8 5 3 0 8 7 6")
        assert cif.value == "E98530876"

    def test_cif_con_guiones(self):
        """CIF con guiones se eliminan."""
        cif = CIF("E-98530876")
        assert cif.value == "E98530876"

        cif2 = CIF("E-9853-0876")
        assert cif2.value == "E98530876"

    def test_cif_con_barras(self):
        """CIF con barras se eliminan."""
        cif = CIF("E/98530876")
        assert cif.value == "E98530876"

        cif2 = CIF("E/9853/0876")
        assert cif2.value == "E98530876"

    def test_cif_mixto_guiones_barras_espacios(self):
        """CIF con combinación de guiones, barras y espacios."""
        cif = CIF(" E-98530/876 ")
        assert cif.value == "E98530876"

    def test_cif_minusculas(self):
        """CIF en minúsculas se normaliza a mayúsculas."""
        cif = CIF("e98530876")
        assert cif.value == "E98530876"

    def test_cif_mixto_mayusculas_minusculas(self):
        """CIF con mezcla de mayúsculas y minúsculas."""
        cif = CIF("e98530876")
        assert cif.value == "E98530876"


class TestCIFValidacion:
    """Tests para la validación de formato de CIFs."""

    def test_cif_valido_letra_8_digitos(self):
        """CIF válido: una letra seguida de 8 dígitos."""
        cif = CIF("E98530876")
        assert cif.is_valid()

    def test_cif_valido_9_digitos(self):
        """CIF válido: 9 dígitos (algunos formatos de NIF)."""
        cif = CIF("12345678Z")
        assert cif.is_valid()

    def test_cif_invalido_solo_letras(self):
        """CIF inválido: solo letras."""
        cif = CIF("ABCDEFGHI")
        assert not cif.is_valid()

    def test_cif_invalido_solo_numeros(self):
        """CIF inválido: solo números (sin letra)."""
        cif = CIF("123456789")
        assert not cif.is_valid()

    def test_cif_invalido_muy_corto(self):
        """CIF inválido: demasiado corto."""
        cif = CIF("E123")
        assert not cif.is_valid()

    def test_cif_invalido_muy_largo(self):
        """CIF inválido: demasiado largo."""
        cif = CIF("E123456789012")
        assert not cif.is_valid()

    def test_cif_vacio(self):
        """CIF vacío es inválido."""
        cif = CIF("")
        assert not cif.is_valid()
        assert cif.value == ""


class TestCIFComparacion:
    """Tests para la comparación de CIFs."""

    def test_igualdad_cifras_identicas(self):
        """Dos CIFs con el mismo valor son iguales."""
        cif1 = CIF("E98530876")
        cif2 = CIF("E98530876")
        assert cif1 == cif2

    def test_igualdad_con_formato_diferente(self):
        """CIFs con formato diferente pero mismo valor normalizado son iguales."""
        cif1 = CIF("E98530876")
        cif2 = CIF("E-98530876")
        cif3 = CIF("  e98530876  ")
        assert cif1 == cif2
        assert cif1 == cif3
        assert cif2 == cif3

    def test_desigualdad(self):
        """CIFs diferentes no son iguales."""
        cif1 = CIF("E98530876")
        cif2 = CIF("B12345678")
        assert cif1 != cif2

    def test_comparacion_con_string(self):
        """Se puede comparar CIF con string directamente."""
        cif = CIF("E98530876")
        assert cif == "E98530876"
        assert cif == "E-98530876"
        assert cif == "  e98530876  "
        assert cif != "B12345678"


class TestCIFRepresentacion:
    """Tests para la representación string del CIF."""

    def test_str_representation(self):
        """Representación string del CIF."""
        cif = CIF("E-98530876")
        assert str(cif) == "E98530876"

    def test_repr_representation(self):
        """Representación repr del CIF."""
        cif = CIF("E98530876")
        assert repr(cif) == "CIF('E98530876')"


class TestCIFCasosEspeciales:
    """Tests para casos especiales y edge cases."""

    def test_cif_con_caracteres_especiales(self):
        """CIF con caracteres especiales se sanean."""
        cif = CIF("E*98530876#")
        # Solo letras y números se mantienen
        assert cif.value == "E98530876"

    def test_cif_none(self):
        """CIF None se trata como string vacío."""
        cif = CIF(None)
        assert cif.value == ""
        assert not cif.is_valid()

    def test_cif_con_saltos_de_linea(self):
        """CIF con saltos de línea se limpian."""
        cif = CIF("E98530876\n")
        assert cif.value == "E98530876"

    def test_cif_con_tabs(self):
        """CIF con tabulaciones se limpian."""
        cif = CIF("E\t98530876")
        assert cif.value == "E98530876"
