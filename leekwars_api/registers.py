"""Registres persistants (`Registers`).

Sur le site, les registres survivent d'un combat à l'autre. Le mock reproduit
cette persistance **au niveau du processus** : un dictionnaire de module.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class Registers:
    """Namespace `Registers` du SDK."""

    #: Stockage persistant : clé -> valeur texte.
    _values: Dict[str, str] = {}

    @classmethod
    def get(cls, key: str) -> Optional[str]:
        """Valeur du registre `key`, ou None."""
        return cls._values.get(str(key))

    @classmethod
    def set(cls, key: str, value: Any) -> bool:
        """Écrit un registre (valeur convertie en texte). Toujours accepté."""
        cls._values[str(key)] = str(value)
        return True

    @classmethod
    def delete(cls, key: str) -> None:
        """Supprime un registre."""
        cls._values.pop(str(key), None)

    @classmethod
    def all(cls) -> Dict[str, str]:
        """Copie de tous les registres."""
        return dict(cls._values)

    @classmethod
    def clear(cls) -> None:
        """Vide les registres (utilisé par les tests)."""
        cls._values.clear()


__all__ = ["Registers"]
