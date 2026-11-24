"""Constructeurs pratiques pour les tests (`builder`).

Exemple :

    from leekwars_api import install, builder
    fight = builder.make_fight(
        me=builder.entity(strength=100, weapons=[builder.weapon(...)]),
        enemies=[builder.entity(cell=(2, 0))],
    )
    install(fight)
"""

from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence, Tuple

from . import state
from .cell import Cell
from .effect import Effect
from .entity import Entity, Me
from .fight import Fight
from .items import Chip, Feature, Weapon


def feature(
    type: int,
    targets: int,
    min_value: float = 0,
    max_value: float = 0,
    turns: int = 0,
    modifiers: int = 0,
) -> Feature:
    """Construit une `Feature` (potentiel d'un item)."""
    return Feature(
        type=type,
        min_value=min_value,
        max_value=max_value,
        turns=turns,
        targets=targets,
        modifiers=modifiers,
    )


def weapon(
    name: str,
    cost: int = 1,
    min_range: int = 0,
    max_range: int = 1,
    features: Iterable[Feature] = (),
    max_uses: int = 0,
    needs_los: bool = True,
    inline: bool = False,
    failure: int = 0,
    id: Optional[int] = None,
) -> Weapon:
    """Construit une arme (enregistrée dans le catalogue global)."""
    return Weapon(
        id=id,
        name=name,
        cost=cost,
        min_range=min_range,
        max_range=max_range,
        features=features,
        max_uses=max_uses,
        needs_los=needs_los,
        inline=inline,
        failure=failure,
    )


def chip(
    name: str,
    cost: int = 1,
    min_range: int = 0,
    max_range: int = 1,
    features: Iterable[Feature] = (),
    max_uses: int = 0,
    needs_los: bool = True,
    inline: bool = False,
    failure: int = 0,
    id: Optional[int] = None,
) -> Chip:
    """Construit une puce (enregistrée dans le catalogue global)."""
    return Chip(
        id=id,
        name=name,
        cost=cost,
        min_range=min_range,
        max_range=max_range,
        features=features,
        max_uses=max_uses,
        needs_los=needs_los,
        inline=inline,
        failure=failure,
    )


def entity(
    *,
    name: str = "leek",
    life: float = 100,
    max_life: float = 100,
    tp: int = 10,
    max_tp: int = 10,
    mp: int = 10,
    max_mp: int = 10,
    strength: int = 0,
    agility: int = 0,
    wisdom: int = 0,
    resistance: int = 0,
    science: int = 0,
    magic: int = 0,
    power: int = 0,
    level: int = 1,
    cell: Any = (0, 0),
    weapons: Iterable[Weapon] = (),
    chips: Iterable[Chip] = (),
    weapon: Optional[Weapon] = None,
    relative_shield: float = 0,
    absolute_shield: float = 0,
    side: int = 1,
    id: Optional[int] = None,
) -> Entity:
    """Construit une entité non placée (la position est posée par make_fight).

    `weapon` : arme déjà équipée (utile pour les ennemis : l'IA ne gère
    que son propre équipement, pas celui des autres).
    """
    entity_obj = Entity(
        id=id,
        name=name,
        life=life,
        max_life=max_life,
        tp=tp,
        max_tp=max_tp,
        mp=mp,
        max_mp=max_mp,
        strength=strength,
        agility=agility,
        wisdom=wisdom,
        resistance=resistance,
        science=science,
        magic=magic,
        power=power,
        level=level,
        weapons=weapons,
        chips=chips,
        relative_shield=relative_shield,
        absolute_shield=absolute_shield,
        side=side,
    )
    if weapon is not None:
        # Un ennemi est déjà équipé : on ne lui facture pas le PT.
        entity_obj.weapon = weapon
        if weapon not in entity_obj.weapons:
            entity_obj.weapons.append(weapon)
    else:
        # Une entité commence sans arme en main : l'IA doit équiper (1 PT).
        entity_obj.weapon = None
    # Position souhaitée, convertie en case au moment de make_fight.
    entity_obj._cell_xy = _cell_coordinates(cell)  # type: ignore[attr-defined]
    entity_obj.cell = None
    return entity_obj


def make_fight(
    *,
    me: Entity,
    enemies: Iterable[Entity] = (),
    allies: Iterable[Entity] = (),
    map_size: int = 12,
    seed: int = 0,
) -> Fight:
    """Construit un combat, place les entités et active le terrain."""
    fight = Fight(map_size=map_size, seed=seed)
    state.set_fight(fight)

    main_entity = _as_me(me)
    main_entity.side = me.side
    main_entity.fight = fight
    fight.register_entity(main_entity)
    _place(fight, main_entity)
    fight.me = main_entity

    for ally in allies:
        ally.side = main_entity.side
        ally.teamID = ally.side
        fight.register_entity(ally)
        _place(fight, ally)

    enemy_side = main_entity.side + 1
    for enemy in enemies:
        if enemy.side == main_entity.side:
            enemy.side = enemy_side
        enemy.teamID = enemy.side
        fight.register_entity(enemy)
        _place(fight, enemy)

    return fight


def _as_me(entity_obj: Entity) -> Me:
    """Transforme une `Entity` en `Me` (copie des attributs)."""
    if isinstance(entity_obj, Me):
        return entity_obj
    me = Me()
    me.__dict__.update(entity_obj.__dict__)
    return me


def _cell_coordinates(cell: Any) -> Tuple[int, int]:
    """Extrait des coordonnées d'une case, d'un couple ou d'un id."""
    if isinstance(cell, Cell):
        return cell.x, cell.y
    if isinstance(cell, (tuple, list)) and len(cell) >= 2:
        return int(cell[0]), int(cell[1])
    if isinstance(cell, int):
        fight = state.get_fight()
        if fight is not None:
            target = fight.field.get_cell_by_id(cell)
            if target is not None:
                return target.x, target.y
    return 0, 0


def _place(fight: Fight, entity_obj: Entity) -> None:
    """Place une entité à sa position souhaitée, ou sur la première libre."""
    wanted = getattr(entity_obj, "_cell_xy", (0, 0))
    cell = fight.field.get_cell(wanted[0], wanted[1])
    if cell is None or not cell.empty:
        cell = next((c for c in fight.field.cells if c.empty), None)
    if cell is None:
        raise RuntimeError("Plus aucune case libre sur le terrain.")
    entity_obj.cell = None
    fight.field.move_entity(entity_obj, cell)


__all__ = ["make_fight", "entity", "weapon", "chip", "feature", "Effect"]
