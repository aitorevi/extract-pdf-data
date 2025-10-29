"""
Value Object para CIF (Código de Identificación Fiscal).

Encapsula la lógica de saneamiento, normalización y validación de CIFs.
Inmutable y con comparación por valor.
"""

import re
from typing import Optional


class CIF:
    """
    Value Object para CIF (Código de Identificación Fiscal).

    Funcionalidades:
    - Saneamiento automático: elimina espacios, guiones, barras y caracteres especiales
    - Normalización: convierte a mayúsculas
    - Validación: verifica formato válido (letra + 8 dígitos o 8 dígitos + letra)
    - Comparación por valor
    - Inmutable

    Formatos válidos de CIF/NIF:
    - Letra + 8 dígitos (ej: E98530876)
    - 8 dígitos + letra (ej: 12345678Z)

    Examples:
        >>> cif = CIF("E-98530876")
        >>> str(cif)
        'E98530876'
        >>> cif.is_valid()
        True
        >>> cif == "E98530876"
        True
    """

    def __init__(self, valor: Optional[str]):
        """
        Crea un CIF a partir de un string.

        Args:
            valor: String con el CIF (puede contener espacios, guiones, barras, etc.)
        """
        self._value = self._sanitize(valor)

    @property
    def value(self) -> str:
        """Retorna el valor saneado y normalizado del CIF."""
        return self._value

    def _sanitize(self, valor: Optional[str]) -> str:
        """
        Sanea y normaliza el CIF.

        Pasos:
        1. Convertir None a string vacío
        2. Eliminar espacios, guiones, barras y caracteres especiales
        3. Mantener solo letras y dígitos
        4. Convertir a mayúsculas

        Args:
            valor: String crudo con el CIF

        Returns:
            CIF saneado y normalizado
        """
        if valor is None:
            return ""

        # Convertir a string y normalizar espacios/saltos de línea
        valor_str = str(valor).strip()

        # Eliminar todos los caracteres excepto letras y dígitos
        # Esto elimina: espacios, guiones, barras, asteriscos, etc.
        valor_limpio = re.sub(r'[^A-Za-z0-9]', '', valor_str)

        # Normalizar a mayúsculas
        return valor_limpio.upper()

    def is_valid(self) -> bool:
        """
        Valida que el CIF tenga un formato correcto.

        Formatos válidos:
        - Letra + 8 dígitos (ej: E98530876)
        - 8 dígitos + letra (ej: 12345678Z)
        - Total: 9 caracteres

        Returns:
            True si el formato es válido, False en caso contrario
        """
        if not self._value or len(self._value) != 9:
            return False

        # Patrón 1: Letra + 8 dígitos (ej: E98530876)
        patron1 = r'^[A-Z]\d{8}$'

        # Patrón 2: 8 dígitos + letra (ej: 12345678Z)
        patron2 = r'^\d{8}[A-Z]$'

        return bool(re.match(patron1, self._value) or re.match(patron2, self._value))

    def __eq__(self, other) -> bool:
        """
        Compara dos CIFs por valor.

        Soporta comparación con otro CIF o con un string.

        Args:
            other: Otro CIF o string para comparar

        Returns:
            True si los valores son iguales (después de sanear)
        """
        if isinstance(other, CIF):
            return self._value == other._value
        elif isinstance(other, str):
            # Permitir comparación directa con strings
            other_cif = CIF(other)
            return self._value == other_cif._value
        return False

    def __ne__(self, other) -> bool:
        """Compara dos CIFs por desigualdad."""
        return not self.__eq__(other)

    def __str__(self) -> str:
        """Representación string del CIF."""
        return self._value

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"CIF('{self._value}')"

    def __hash__(self) -> int:
        """Hash del CIF para poder usarlo en sets y dicts."""
        return hash(self._value)
