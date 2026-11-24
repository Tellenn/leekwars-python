"""Terrain de combat (`Field`).

`install()` lie dans `builtins` l'**instance** de terrain du combat courant,
comme le moteur du site expose le namespace `Field`. Les méthodes acceptent
indifféremment une `Cell`, une `Entity` ou un id de case.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Iterable, List, Optional

from .cell import Cell, as_cell
from .rules import RULES

if TYPE_CHECKING:  # pragma: no cover - annotations uniquement
    from .fight import Fight


class _FieldType:
    """Forme du terrain (`Field.Type.*`)."""

    SQUARE = 0
    CIRCLE = 1
    CROSS = 2


class Field:
    """Carte carrée `size x size`, sans obstacle par défaut."""

    Type = _FieldType
    #: Forme du terrain courante.
    type = _FieldType.SQUARE

    def __init__(self, size: int = 12, fight: Optional["Fight"] = None) -> None:
        self.size = int(size)
        self.fight = fight
        self.cells: List[Cell] = [
            Cell(self, x, y) for y in range(self.size) for x in range(self.size)
        ]
        self._by_id = {cell.id: cell for cell in self.cells}

    # ------------------------------------------------------------------
    # Accès aux cases
    # ------------------------------------------------------------------
    def get_cell(self, x: int, y: int) -> Optional[Cell]:
        """Case aux coordonnées données, ou None hors carte."""
        if 0 <= x < self.size and 0 <= y < self.size:
            return self.cells[y * self.size + x]
        return None

    def get_cell_by_id(self, cell_id: int) -> Optional[Cell]:
        """Case d'id donné, ou None si l'id est invalide."""
        return self._by_id.get(int(cell_id))

    def cellFromXY(self, x: int, y: int) -> Optional[Cell]:
        """Alias de `get_cell` (nom de l'API du site)."""
        return self.get_cell(int(x), int(y))

    def getObstacles(self) -> List[Cell]:
        """Toutes les cases obstruées."""
        return [cell for cell in self.cells if cell.obstacle]

    def all_cells(self) -> List[Cell]:
        """Toutes les cases de la carte."""
        return list(self.cells)

    # ------------------------------------------------------------------
    # Géométrie
    # ------------------------------------------------------------------
    def distance(self, a, b) -> int:
        """Distance à vol d'oiseau (métrique des portées : |dx| + |dy|)."""
        first = as_cell(a, self)
        second = as_cell(b, self)
        if first is None or second is None:
            return -1
        return int(RULES.range_distance(first, second))

    def cellDistance(self, a, b) -> int:
        """Distance en cases (Chebyshev) : la distance de déplacement."""
        first = as_cell(a, self)
        second = as_cell(b, self)
        if first is None or second is None:
            return -1
        return int(RULES.distance(first, second))

    def euclideanDistance(self, a, b) -> float:
        """Distance réelle (à vol d'oiseau)."""
        first = as_cell(a, self)
        second = as_cell(b, self)
        if first is None or second is None:
            return -1.0
        return math.hypot(first.x - second.x, first.y - second.y)

    def pathLength(self, a, b, ignoredCells: Optional[Iterable] = None) -> int:
        """Longueur du plus court chemin, ou -1 si inatteignable."""
        first = as_cell(a, self)
        second = as_cell(b, self)
        if first is None or second is None:
            return -1
        return first.pathLength(second, ignoredCells)

    def lineOfSight(self, a, b, ignoredEntities=None) -> bool:
        """Ligne de vue entre deux cases (obstacles uniquement)."""
        first = as_cell(a, self)
        second = as_cell(b, self)
        if first is None or second is None:
            return False
        return first.lineOfSight(second, ignoredEntities)

    def onSameLine(self, a, b) -> bool:
        """Les deux cases partagent-elles une ligne ou une colonne ?"""
        first = as_cell(a, self)
        second = as_cell(b, self)
        if first is None or second is None:
            return False
        return first.onSameLine(second)

    def path(self, a, b, ignoredCells: Optional[Iterable] = None) -> List[Cell]:
        """Chemin de cases entre deux positions."""
        first = as_cell(a, self)
        second = as_cell(b, self)
        if first is None or second is None:
            return []
        return first.path(second, ignoredCells)

    # ------------------------------------------------------------------
    # Déplacement d'entités (utilisé par Fight / Me)
    # ------------------------------------------------------------------
    def move_entity(self, entity, destination: Cell) -> bool:
        """Déplace une entité vers `destination` si la case est libre."""
        if destination.obstacle or destination.entity is not None:
            return False
        if entity.cell is not None:
            entity.cell.entity = None
        destination.entity = entity
        entity.cell = destination
        return True

    def place_entity(self, entity, x: int, y: int) -> bool:
        """Place une entité sur la case `(x, y)`."""
        cell = self.get_cell(x, y)
        if cell is None:
            return False
        return self.move_entity(entity, cell)

    def __repr__(self) -> str:
        return f"Field({self.size}x{self.size})"


__all__ = ["Field"]
