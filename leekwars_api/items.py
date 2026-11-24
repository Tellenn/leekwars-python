"""Armes, puces et caractéristiques (`Feature`).

Un `Item` porte le coût, la portée et la liste de `Feature` (le potentiel de
l'item : dégâts, soin, buff...). `Weapon` et `Chip` en héritent, comme dans
les stubs officiels. Les items créés par `builder` sont enregistrés dans un
registre global, ce qui permet à `Weapon.get(id)` / `Chip.get(id)` de
fonctionner comme sur le site.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .cell import Cell, as_cell

ItemId = "Weapon | Chip | int"


class _Area:
    """Forme de la zone d'effet (`Item.Area.*`)."""

    SINGLE_CELL = 0
    #: Alias historique de `SINGLE_CELL`.
    POINT = 0
    CIRCLE_1 = 1
    CIRCLE_2 = 2
    CIRCLE_3 = 3
    LINE = 4
    STAR = 5
    ALL = 6
    CROSS_1 = 7


class _LaunchType:
    """Contrainte de visée (`Item.LaunchType.*`), valeurs du site."""

    LINE = 1
    DIAGONAL = 2
    STAR = 3
    STAR_INVERTED = 4
    DIAGONAL_INVERTED = 5
    LINE_INVERTED = 6
    CIRCLE = 7
    ALL = 8


#: Rayon (en cases) associé à chaque forme de zone.
_AREA_RADIUS: Dict[int, int] = {
    _Area.SINGLE_CELL: 0,
    _Area.CIRCLE_1: 1,
    _Area.CIRCLE_2: 2,
    _Area.CIRCLE_3: 3,
}


class Feature:
    """Caractéristique déclarée d'une arme ou d'une puce.

    Exemple : « 10 à 15 dégâts sur les ennemis ». `type` est une constante
    `Effect.Type`, `targets` un masque `Effect.Target`.
    """

    def __init__(
        self,
        type: int,
        min_value: float = 0,
        max_value: float = 0,
        turns: int = 0,
        targets: int = 0,
        modifiers: int = 0,
    ) -> None:
        self.type = int(type)
        self.minValue = min_value
        self.maxValue = max_value
        self.turns = int(turns)
        self.targets = int(targets)
        self.modifiers = int(modifiers)

    @property
    def raw(self) -> List[Any]:
        """Tableau brut `[type, min, max, turns, targets, modifiers]`."""
        return [
            self.type,
            self.minValue,
            self.maxValue,
            self.turns,
            self.targets,
            self.modifiers,
        ]

    def __repr__(self) -> str:
        return (
            f"Feature(type={self.type}, {self.minValue}-{self.maxValue}, "
            f"targets={self.targets})"
        )


#: Registre global des items (armes et puces), comme le catalogue du site.
_ITEMS: Dict[int, "Item"] = {}
_NEXT_ID: int = 1


def _allocate_id() -> int:
    """Attribue un id unique à un nouvel item."""
    global _NEXT_ID
    item_id = _NEXT_ID
    _NEXT_ID += 1
    return item_id


def register_item(item: "Item") -> "Item":
    """Enregistre un item dans le catalogue global."""
    global _NEXT_ID
    if item.id is None or item.id <= 0:
        item.id = _allocate_id()
    elif item.id >= _NEXT_ID:
        _NEXT_ID = item.id + 1
    _ITEMS[item.id] = item
    return item


def clear_registry() -> None:
    """Vide le catalogue (utile aux tests unitaires du mock)."""
    global _NEXT_ID
    _ITEMS.clear()
    _NEXT_ID = 1


class Item:
    """Base commune aux armes et aux puces."""

    Area = _Area
    LaunchType = _LaunchType

    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "item",
        cost: int = 1,
        min_range: int = 0,
        max_range: int = 1,
        features: Iterable[Feature] = (),
        max_uses: int = 0,
        needs_los: bool = True,
        inline: bool = False,
        failure: int = 0,
        area: int = _Area.SINGLE_CELL,
        launch_type: int = _LaunchType.CIRCLE,
    ) -> None:
        self.id = id
        self.name = name
        self.cost = int(cost)
        self.minRange = int(min_range)
        self.maxRange = int(max_range)
        self.features: List[Feature] = list(features)
        self.maxUses = int(max_uses)
        self.needsLos = bool(needs_los)
        self.inline = bool(inline)
        self.failure = int(failure)
        self.area = int(area)
        self.launchType = int(launch_type)
        register_item(self)

    # ------------------------------------------------------------------
    # Zone d'effet
    # ------------------------------------------------------------------
    def effectiveArea(self, cell, from_=None) -> List[Cell]:
        """Cases réellement touchées par l'item autour de `cell`.

        Le mock ne modélise que les zones circulaires (rayon 0 à 3) ; les
        autres formes retombent sur la case ciblée.
        """
        del from_  # la direction n'influence pas les zones circulaires
        target = as_cell(cell)
        if target is None or target.field is None:
            return []
        radius = _AREA_RADIUS.get(self.area, 0)
        if radius <= 0:
            return [target]
        cells: List[Cell] = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                candidate = target.field.get_cell(target.x + dx, target.y + dy)
                if candidate is not None:
                    cells.append(candidate)
        return cells

    # ------------------------------------------------------------------
    # Catalogue
    # ------------------------------------------------------------------
    @staticmethod
    def get(item_id: int) -> Optional["Item"]:
        """Item d'id donné (arme ou puce), ou None."""
        return _ITEMS.get(int(item_id))

    def __repr__(self) -> str:
        return self.name


class Weapon(Item):
    """Une arme."""

    def __init__(self, *args: Any, passive_features: Iterable[Feature] = (), **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.passiveFeatures: List[Feature] = list(passive_features)

    @staticmethod
    def get(weapon_id: int) -> Optional["Weapon"]:
        """Arme d'id donné, ou None si ce n'est pas une arme."""
        item = _ITEMS.get(int(weapon_id))
        return item if isinstance(item, Weapon) else None

    @staticmethod
    def getAll() -> List["Weapon"]:
        """Toutes les armes du catalogue."""
        return [item for item in _ITEMS.values() if isinstance(item, Weapon)]

    @staticmethod
    def isWeapon(value: Any) -> bool:
        """`value` est-il un id d'arme valide (ou une arme) ?"""
        if isinstance(value, Weapon):
            return True
        if isinstance(value, int):
            return isinstance(_ITEMS.get(value), Weapon)
        return False


class Chip(Item):
    """Une puce."""

    def __init__(self, *args: Any, cooldown: int = 0, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.cooldown = int(cooldown)
        self.currentCooldown = 0
        self.minScope = 0
        self.maxScope = 0
        self.bulbChips: List["Chip"] = []
        self.bulbCharacteristics: Dict[str, Any] = {}
        self.bulbStats: Dict[str, Any] = {}

    def currentCooldownOf(self, entity) -> int:
        """Cooldown restant pour une autre entité (0 dans le mock)."""
        del entity
        return 0

    @staticmethod
    def get(chip_id: int) -> Optional["Chip"]:
        """Puce d'id donné, ou None si ce n'est pas une puce."""
        item = _ITEMS.get(int(chip_id))
        return item if isinstance(item, Chip) else None

    @staticmethod
    def getAll() -> List["Chip"]:
        """Toutes les puces du catalogue."""
        return [item for item in _ITEMS.values() if isinstance(item, Chip)]

    @staticmethod
    def isChip(value: Any) -> bool:
        """`value` est-il un id de puce valide (ou une puce) ?"""
        if isinstance(value, Chip):
            return True
        if isinstance(value, int):
            return isinstance(_ITEMS.get(value), Chip)
        return False


__all__ = [
    "Item",
    "Weapon",
    "Chip",
    "Feature",
    "register_item",
    "clear_registry",
]
