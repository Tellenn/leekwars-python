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


def _crow(a, b) -> int:
    """Distance « à vol d'oiseau » : |dx| + |dy| (métrique des portées).

    C'est la métrique du moteur pour les portées d'armes et de puces
    (`Cell.distance()` sur le site) : une diagonale de 2 cases y vaut 4.
    Elle est DIFFÉRENTE de la distance de déplacement (Chebyshev : une
    diagonale de 2 cases vaut 2 PM).

    Mesuré sur le moteur (combat de test #54913368) : deux cases décalées
    de (19, -6) sont à 25 cases de distance, pas 19.
    """
    ax, ay = _coords(a)
    bx, by = _coords(b)
    return abs(ax - bx) + abs(ay - by)


class RULES:
    """Constantes et formules du jeu.

    `RULES.distance(a, b)` prend deux objets possédant `.x` et `.y` (des
    cellules) et renvoie la distance **de déplacement** en cases
    (convention Leek Wars : le déplacement se fait en 8 directions, donc
    distance de Chebyshev).

    `RULES.range_distance(a, b)` renvoie la distance **de portée** (celle
    de `Cell.distance()` sur le site) : |dx| + |dy|. Les portées d'armes et
    de puces sont vérifiées avec cette métrique, pas avec celle du
    déplacement.
    """

    #: Multiplicateur d'un coup critique (encyclopédie FR/Agilité).
    CRITICAL_FACTOR: float = 1.3
    #: Diviseur du vol de vie : `degats * sagesse / LIFE_STEAL_DIVISOR`.
    LIFE_STEAL_DIVISOR: int = 1000
    #: Diviseur de la probabilité de critique : `agilite / CRITICAL_DIVISOR`.
    CRITICAL_DIVISOR: int = 1000

    #: Diviseur des pourcentages (force, sagesse, science, résistance...).
    PERCENT_DIVISOR: int = 100

    # --- Érosion (encyclopédie FR/Érosion, MAJ 1.98) --------------------
    #: Part des dégâts classiques retirés à la vie maximum.
    EROSION_DAMAGE: float = 0.05
    #: Part des dégâts de poison retirés à la vie maximum.
    EROSION_POISON: float = 0.10
    #: Bonus d'érosion appliqué aux coups critiques.
    EROSION_CRITICAL_BONUS: float = 0.10

    #: Distance en cases (Chebyshev), pour le déplacement. Attribut
    #: fonction pour rester modifiable.
    distance = staticmethod(_chebyshev)
    #: Distance de portée (|dx| + |dy|), comme `Cell.distance()` du site.
    range_distance = staticmethod(_crow)


def distance(a, b) -> int:
    """Raccourci pratique vers la règle de distance courante."""
    return int(RULES.distance(a, b))
