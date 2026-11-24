"""Cellules du terrain et résolution des cibles « Cell | Entity | id ».

Convention Leek Wars :

* une carte est un carré de `size x size` cases ;
* l'id d'une case vaut `y * size + x` ;
* la distance se mesure en 8 directions (Chebyshev), règle centralisée dans
  `leekwars_api.RULES.distance`.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple

from . import state
from .rules import RULES

if TYPE_CHECKING:  # pragma: no cover - annotations uniquement
    from .entity import Entity
    from .items import Item
    from .field import Field

CellLike = "Cell | Entity | int"


class _CellType:
    """Contenu d'une case (`Cell.Type.*`)."""

    EMPTY = 0
    PLAYER = 1
    ENTITY = 2
    OBSTACLE = 3


def as_cell(value, field: Optional["Field"] = None) -> Optional["Cell"]:
    """Convertit `Cell | Entity | id` en `Cell` (None si impossible).

    Les entités sont acceptées via leur attribut `.cell`. Les entiers sont
    interprétés comme des ids de cases du terrain fourni, ou à défaut du
    combat actif.
    """
    if isinstance(value, Cell):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        target_field = field
        if target_field is None:
            fight = state.get_fight()
            target_field = fight.field if fight is not None else None
        if target_field is None:
            return None
        return target_field.get_cell_by_id(value)
    # Duck typing : toute entité possède un attribut `cell`.
    cell = getattr(value, "cell", None)
    if isinstance(cell, Cell):
        return cell
    return None


class Cell:
    """Une case du terrain."""

    Type = _CellType

    def __init__(self, field: Optional["Field"], x: int, y: int) -> None:
        self.field = field
        self.x = int(x)
        self.y = int(y)
        self.obstacle = False
        self.entity: Optional["Entity"] = None
        #: Effet/décor éventuel (non utilisé par le mock, présent pour l'API).
        self._content_override: Optional[int] = None

    # ------------------------------------------------------------------
    # Identité et contenu
    # ------------------------------------------------------------------
    @property
    def id(self) -> int:
        """Id de la case : `y * taille + x`."""
        size = self.field.size if self.field is not None else 0
        return self.y * size + self.x

    @property
    def hasEntity(self) -> bool:
        """Une entité occupe-t-elle la case ?"""
        return self.entity is not None

    @property
    def empty(self) -> bool:
        """La case est-elle libre (ni obstacle, ni entité) ?"""
        return not self.obstacle and self.entity is None

    @property
    def content(self) -> int:
        """Contenu de la case (`Cell.Type.*`)."""
        if self._content_override is not None:
            return self._content_override
        if self.obstacle:
            return _CellType.OBSTACLE
        if self.entity is not None:
            return _CellType.ENTITY
        return _CellType.EMPTY

    # ------------------------------------------------------------------
    # Distances et chemins
    # ------------------------------------------------------------------
    def distance(self, target) -> int:
        """Distance en cases (Chebyshev) jusqu'à une case/entité/id."""
        other = as_cell(target, self.field)
        if other is None:
            return -1
        return int(RULES.distance(self, other))

    def pathLength(self, target, ignoredCells: Optional[Iterable] = None) -> int:
        """Longueur du plus court chemin, ou -1 si la cible est inatteignable."""
        other = as_cell(target, self.field)
        if other is None:
            return -1
        path = _bfs(self, other, self._blocked_cells(ignoredCells))
        if path is None:
            return -1
        return len(path) - 1

    def path(self, target, ignoredCells: Optional[Iterable] = None) -> List["Cell"]:
        """Chemin de cases jusqu'à la cible (cible incluse), ou liste vide."""
        other = as_cell(target, self.field)
        if other is None:
            return []
        path = _bfs(self, other, self._blocked_cells(ignoredCells))
        if path is None:
            return []
        # Le chemin renvoyé par le jeu part de la case suivante, cible incluse.
        return path[1:]

    def _blocked_cells(self, ignored: Optional[Iterable]) -> set:
        """Cases infranchissables : obstacles + cases explicitement ignorées."""
        blocked = set()
        for cell in self.field.cells if self.field is not None else ():
            if cell.obstacle:
                blocked.add((cell.x, cell.y))
        if ignored is not None:
            for value in ignored:
                cell = as_cell(value, self.field)
                if cell is not None:
                    blocked.add((cell.x, cell.y))
        return blocked

    # ------------------------------------------------------------------
    # Ligne de vue
    # ------------------------------------------------------------------
    def lineOfSight(self, target, ignoredEntities=None) -> bool:
        """Ligne de vue approximée.

        Les entités ne bloquent pas la vue (contrat du mock) ; seuls les
        obstacles bloquent. `ignoredEntities` est accepté pour compatibilité
        mais sans effet supplémentaire.
        """
        del ignoredEntities  # les entités ne bloquent jamais la vue ici
        other = as_cell(target, self.field)
        if other is None or self.field is None:
            return True
        dx = other.x - self.x
        dy = other.y - self.y
        steps = max(abs(dx), abs(dy))
        if steps <= 1:
            return True
        # Échantillonnage de la droite ; approximation suffisante pour un mock.
        for i in range(1, steps):
            x = round(self.x + dx * i / steps)
            y = round(self.y + dy * i / steps)
            cell = self.field.get_cell(x, y)
            if cell is not None and cell.obstacle:
                return False
        return True

    def onSameLine(self, target) -> bool:
        """Les deux cases sont-elles sur la même ligne ou la même colonne ?"""
        other = as_cell(target, self.field)
        if other is None:
            return False
        return self.x == other.x or self.y == other.y

    # ------------------------------------------------------------------
    # Accès global
    # ------------------------------------------------------------------
    @staticmethod
    def get(cell_id: int) -> Optional["Cell"]:
        """Case d'id `cell_id` du combat actif, ou None."""
        fight = state.get_fight()
        if fight is None:
            return None
        return fight.field.get_cell_by_id(cell_id)

    def __repr__(self) -> str:
        return f"Cell({self.x}, {self.y})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Cell)
            and self.x == other.x
            and self.y == other.y
            and self.field is other.field
        )

    def __hash__(self) -> int:
        return hash((id(self.field), self.x, self.y))


def _bfs(
    start: "Cell", goal: "Cell", blocked: set
) -> Optional[List["Cell"]]:
    """Parcours en largeur 8 directions ; renvoie le chemin complet ou None."""
    if start.field is None or goal.field is None:
        return None
    field = start.field
    if (start.x, start.y) == (goal.x, goal.y):
        return [start]
    queue: deque[Tuple[int, int]] = deque([(start.x, start.y)])
    parents: dict[Tuple[int, int], Optional[Tuple[int, int]]] = {
        (start.x, start.y): None
    }
    while queue:
        x, y = queue.popleft()
        for sx in (-1, 0, 1):
            for sy in (-1, 0, 1):
                if sx == 0 and sy == 0:
                    continue
                nx, ny = x + sx, y + sy
                if (nx, ny) in parents:
                    continue
                cell = field.get_cell(nx, ny)
                if cell is None:
                    continue
                is_goal = (nx, ny) == (goal.x, goal.y)
                if not is_goal and ((nx, ny) in blocked or cell.obstacle):
                    continue
                parents[(nx, ny)] = (x, y)
                if is_goal:
                    return _rebuild(field, parents, (nx, ny))
                queue.append((nx, ny))
    return None


def _rebuild(
    field: "Field",
    parents: dict,
    end: Tuple[int, int],
) -> List["Cell"]:
    """Reconstruit un chemin depuis la table des parents."""
    path: List["Cell"] = []
    current: Optional[Tuple[int, int]] = end
    while current is not None:
        cell = field.get_cell(*current)
        if cell is None:
            break
        path.append(cell)
        current = parents[current]
    path.reverse()
    return path


__all__ = ["Cell", "as_cell"]
