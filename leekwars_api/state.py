"""État global du mock Leek Wars.

Sur le site, le moteur injecte `Fight`, `Debug`, `Field`, ... dans le scope de
l'IA. En local, le mock fait de même via `leekwars_api.install()`. Certains
objets (Cell.get, Debug.log, Field) ont besoin de retrouver le combat courant :
ce module centralise cette référence, sans dépendre d'aucun autre module du
mock (et donc sans import circulaire).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:  # pragma: no cover - uniquement pour les annotations
    from .fight import Fight

# Combat actif : posé par builder.make_fight() puis par install().
_ACTIVE_FIGHT: Optional["Fight"] = None


def set_fight(fight: Optional["Fight"]) -> None:
    """Définit (ou efface) le combat actif du processus."""
    global _ACTIVE_FIGHT
    _ACTIVE_FIGHT = fight


def get_fight() -> Optional["Fight"]:
    """Renvoie le combat actif, ou None s'il n'y en a pas."""
    return _ACTIVE_FIGHT


def require_fight() -> "Fight":
    """Renvoie le combat actif ou lève une erreur explicite."""
    if _ACTIVE_FIGHT is None:
        raise RuntimeError(
            "Aucun combat actif : appelle builder.make_fight() ou install(fight) "
            "avant d'utiliser l'API Leek Wars."
        )
    return _ACTIVE_FIGHT


def reset() -> None:
    """Oublie le combat actif (utilisé par les tests et `uninstall`)."""
    global _ACTIVE_FIGHT
    _ACTIVE_FIGHT = None


# Petit utilitaire partagé : convertir n'importe quelle valeur en id entier.
def as_int(value: Any) -> Optional[int]:
    """Convertit une valeur en entier si possible, sinon None."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return None
