"""Règles numériques du jeu, centralisées et modifiables.

Sources : encyclopédie FR Leek Wars (Force, Agilité, Résistance, Sagesse,
Vol de vie, Effets). Ces constantes sont exposées via `leekwars_api.RULES`
pour qu'un test ou une expérience puisse les ajuster sans toucher au reste du
mock.
"""

from __future__ import annotations

from typing import Tuple


def _coords(value) -> Tuple[int, int]:
    """Extrait `(x, y)` d'une cellule ou d'un couple de coordonnées."""
    if hasattr(value, "x") and hasattr(value, "y"):
        return value.x, value.y
    return value[0], value[1]


def _chebyshev(a, b) -> int:
    """Distance de Chebyshev entre deux positions (déplacement 8 directions)."""
    ax, ay = _coords(a)
    bx, by = _coords(b)
    return max(abs(ax - bx), abs(ay - by))


class RULES:
    """Constantes et formules du jeu.

    `RULES.distance(a, b)` prend deux objets possédant `.x` et `.y` (des
    cellules) et renvoie la distance en cases, convention Leek Wars : le
    déplacement se fait en 8 directions, donc distance de Chebyshev.
    """

    #: Multiplicateur d'un coup critique (encyclopédie FR/Agilité).
    CRITICAL_FACTOR: float = 1.3
    #: Diviseur du vol de vie : `degats * sagesse / LIFE_STEAL_DIVISOR`.
    LIFE_STEAL_DIVISOR: int = 1000
    #: Diviseur de la probabilité de critique : `agilite / CRITICAL_DIVISOR`.
    CRITICAL_DIVISOR: int = 1000

    #: Diviseur des pourcentages (force, sagesse, science, résistance...).
    PERCENT_DIVISOR: int = 100

    #: Distance en cases (Chebyshev). Attribut fonction pour rester modifiable.
    distance = staticmethod(_chebyshev)


def distance(a, b) -> int:
    """Raccourci pratique vers la règle de distance courante."""
    return int(RULES.distance(a, b))
