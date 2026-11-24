"""Le combat (`Fight`) : terrain, entités, tours et résolution des effets.

C'est ici que vivent les vraies formules du jeu (force, critique, boucliers,
sagesse, science, vol de vie), avec un aléa entièrement piloté par
`fight.rng` afin que les tests soient déterministes.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .cell import Cell, as_cell
from .effect import Effect
from .entity import Entity, Me
from .field import Field
from .items import Chip, Feature, Item, Weapon
from .rules import RULES


class _Use:
    """Code de retour des actions (`Fight.Use.*`).

    Valeurs exactes du runtime Leek Wars : une action réussie renvoie un
    code **strictement positif** (`> 0`), une action impossible un code
    négatif. Aucune action ne lève d'exception.
    """

    FAILED = 0
    SUCCESS = 1
    CRITICAL = 2
    INVALID_TARGET = -1
    NOT_ENOUGH_TP = -2
    INVALID_COOLDOWN = -3
    INVALID_POSITION = -4
    TOO_MANY_SUMMONS = -5
    RESURRECT_INVALID_ENTITY = -6
    MAX_USES = -7
    INVALID_STATE = -8


class _FightType:
    """Type de combat (`Fight.Type.*`)."""

    SOLO = 0
    TEAM = 1
    BATTLE_ROYALE = 2
    BOSS = 3
    CHEST_HUNT = 4
    COLOSSUS = 5
    FARMER = 6
    WAR = 7


class _FightContext:
    """Contexte du combat (`Fight.Context.*`)."""

    GARDEN = 0
    CHALLENGE = 1
    TEST = 2
    TOURNAMENT = 3
    DUNGEON = 4
    CHEST_HUNT = 5
    BATTLE_ROYALE = 6


class _Boss:
    """Type de boss (`Fight.Boss.*`)."""

    NONE = 0
    EVIL_PUMPKIN = 1
    FENNEL_KING = 2
    NASU_SAMURAI = 3
    #: Variante orthographique utilisée par certains stubs.
    NASU_SAMOURAI = 3
    GRAAL = 4


class _Erosion:
    """Érosion du terrain (`Fight.Erosion.*`), valeurs minimalistes."""

    DAMAGE = 5
    POISON = 10
    CRITICAL_BONUS = 5


#: Types d'effets amplifiés par la science (encyclopédie FR/Effets).
_SCIENCE_AMPLIFIED = {
    Effect.BUFF_STRENGTH,
    Effect.BUFF_AGILITY,
    Effect.BUFF_RESISTANCE,
    Effect.BUFF_WISDOM,
    Effect.BUFF_TP,
    Effect.BUFF_MP,
}


class Fight:
    """Un combat local."""

    Use = _Use
    Type = _FightType
    Context = _FightContext
    Boss = _Boss
    Erosion = _Erosion
    #: Les constantes d'effet restent accessibles via `Fight.Effect`.
    Effect = Effect

    #: Multiplicateur d'un coup critique (1.3), exposé comme sur le site.
    CRITICAL_FACTOR = RULES.CRITICAL_FACTOR
    #: Nombre maximum de tours d'un combat (valeur du runtime officiel).
    MAX_TURNS = 64
    #: Nombre maximum d'invocations vivantes par équipe.
    SUMMON_LIMIT = 8

    def __init__(
        self,
        map_size: int = 12,
        seed: int = 0,
        fight_id: int = 0,
    ) -> None:
        self.field = Field(map_size, self)
        self.rng = random.Random(seed)
        self.turn = 0
        self.id = fight_id
        self.type = _FightType.SOLO
        self.context = _FightContext.GARDEN
        self.batched = False
        self.boss = _Boss.NONE
        self.winner = 0
        self.me: Optional[Me] = None
        self.entities: List[Entity] = []
        self.logs: List[str] = []
        self.says: List[List[Any]] = []
        #: Loadouts nommés (posés par les tests ou setLoadout).
        self.loadouts: Dict[str, Dict[str, Any]] = {}
        #: Utilisations d'items par tour : (entity_id, item_id) -> nombre.
        self._item_uses: Dict[Tuple[int, int], int] = {}

    # ------------------------------------------------------------------
    # Entités
    # ------------------------------------------------------------------
    def register_entity(self, entity: Entity) -> Entity:
        """Rattache une entité au combat (id attribué si absent)."""
        if entity.id is None:
            entity.id = len(self.entities) + 1
        entity.fight = self
        entity.leekID = entity.id
        if entity not in self.entities:
            self.entities.append(entity)
        return entity

    def get_entity(self, entity_id: int) -> Optional[Entity]:
        """Entité d'id donné, ou None."""
        for entity in self.entities:
            if entity.id == entity_id:
                return entity
        return None

    @property
    def allies(self) -> List[Entity]:
        """Alliés vivants ou morts, hors `me`."""
        if self.me is None:
            return []
        return [
            e for e in self.entities if e is not self.me and e.side == self.me.side
        ]

    @property
    def enemies(self) -> List[Entity]:
        """Ennemis (vivants ou morts)."""
        if self.me is None:
            return []
        return [e for e in self.entities if e.side != self.me.side]

    def getEnemies(self) -> List[Entity]:
        """Tous les ennemis."""
        return list(self.enemies)

    def getAllies(self) -> List[Entity]:
        """Tous les alliés (hors `me`)."""
        return list(self.allies)

    def getAliveEnemies(self) -> List[Entity]:
        """Ennemis encore en vie."""
        return [e for e in self.enemies if e.alive]

    def getAliveAllies(self) -> List[Entity]:
        """Alliés encore en vie (hors `me`)."""
        return [e for e in self.allies if e.alive]

    def getDeadEnemies(self) -> List[Entity]:
        """Ennemis morts."""
        return [e for e in self.enemies if e.dead]

    def getDeadAllies(self) -> List[Entity]:
        """Alliés morts (hors `me`)."""
        return [e for e in self.allies if e.dead]

    def getEnemiesCount(self) -> int:
        """Nombre total d'ennemis."""
        return len(self.enemies)

    def getAlliesCount(self) -> int:
        """Nombre total d'alliés (hors `me`)."""
        return len(self.allies)

    def getAliveEnemiesCount(self) -> int:
        """Nombre d'ennemis vivants."""
        return len(self.getAliveEnemies())

    def getAliveAlliesCount(self) -> int:
        """Nombre d'alliés vivants (hors `me`)."""
        return len(self.getAliveAllies())

    def getDeadEnemiesCount(self) -> int:
        """Nombre d'ennemis morts."""
        return len(self.getDeadEnemies())

    def getDeadAlliesCount(self) -> int:
        """Nombre d'alliés morts (hors `me`)."""
        return len(self.getDeadAllies())

    @property
    def alliesLife(self) -> float:
        """Somme des PV des alliés (incluant `me`)."""
        total = self.me.life if self.me is not None else 0
        return total + sum(e.life for e in self.allies if e.alive)

    @property
    def enemiesLife(self) -> float:
        """Somme des PV des ennemis."""
        return sum(e.life for e in self.enemies if e.alive)

    # ------------------------------------------------------------------
    # Recherches géométriques
    # ------------------------------------------------------------------
    def _sorted_by_distance(
        self, candidates: Iterable[Entity], origin: Optional[Cell]
    ) -> List[Entity]:
        if origin is None:
            return list(candidates)
        return sorted(
            candidates,
            key=lambda e: (
                origin.distance(e.cell) if e.cell is not None else 10**9,
                e.id if e.id is not None else 0,
            ),
        )

    def getNearestEnemy(self) -> Optional[Entity]:
        """Ennemi vivant le plus proche de `me`."""
        origin = self.me.cell if self.me is not None else None
        alive = self._sorted_by_distance(self.getAliveEnemies(), origin)
        return alive[0] if alive else None

    def getNearestAlly(self) -> Optional[Entity]:
        """Allié vivant le plus proche de `me` (hors `me`)."""
        origin = self.me.cell if self.me is not None else None
        alive = self._sorted_by_distance(self.getAliveAllies(), origin)
        return alive[0] if alive else None

    def getFarthestEnemy(self) -> Optional[Entity]:
        """Ennemi vivant le plus éloigné de `me`."""
        origin = self.me.cell if self.me is not None else None
        if origin is None:
            return None
        alive = self.getAliveEnemies()
        if not alive:
            return None
        return max(alive, key=lambda e: origin.distance(e.cell))

    def getFarthestAlly(self) -> Optional[Entity]:
        """Allié vivant le plus éloigné de `me` (hors `me`)."""
        origin = self.me.cell if self.me is not None else None
        if origin is None:
            return None
        alive = self.getAliveAllies()
        if not alive:
            return None
        return max(alive, key=lambda e: origin.distance(e.cell))

    def getNearestEnemyToCell(self, cell) -> Optional[Entity]:
        """Ennemi vivant le plus proche d'une cellule."""
        origin = as_cell(cell, self.field)
        alive = self._sorted_by_distance(self.getAliveEnemies(), origin)
        return alive[0] if alive else None

    def getNearestAllyToCell(self, cell) -> Optional[Entity]:
        """Allié vivant le plus proche d'une cellule (hors `me`)."""
        origin = as_cell(cell, self.field)
        alive = self._sorted_by_distance(self.getAliveAllies(), origin)
        return alive[0] if alive else None

    def getNearestEnemyTo(self, target) -> Optional[Entity]:
        """Alias de `getNearestEnemyToCell`."""
        return self.getNearestEnemyToCell(target)

    def getNearestAllyTo(self, target) -> Optional[Entity]:
        """Alias de `getNearestAllyToCell`."""
        return self.getNearestAllyToCell(target)

    def getAlliedTurret(self) -> Optional[Entity]:
        """Tourelle alliée, s'il y en a une."""
        for entity in self.entities:
            if (
                entity.entityType == Entity.Type.TURRET
                and self.me is not None
                and entity.side == self.me.side
            ):
                return entity
        return None

    def getEnemyTurret(self) -> Optional[Entity]:
        """Tourelle ennemie, s'il y en a une."""
        for entity in self.entities:
            if (
                entity.entityType == Entity.Type.TURRET
                and self.me is not None
                and entity.side != self.me.side
            ):
                return entity
        return None

    def getNextPlayer(self, entity=None) -> Optional[Entity]:
        """Entité suivante dans l'ordre de jeu."""
        return self._neighbour_player(entity, 1)

    def getPreviousPlayer(self, entity=None) -> Optional[Entity]:
        """Entité précédente dans l'ordre de jeu."""
        return self._neighbour_player(entity, -1)

    def _neighbour_player(self, entity, offset: int) -> Optional[Entity]:
        ordered = [e for e in self.entities if e.alive]
        if not ordered:
            return None
        reference = entity if isinstance(entity, Entity) else self.me
        if reference not in ordered:
            return ordered[0]
        index = (ordered.index(reference) + offset) % len(ordered)
        return ordered[index]

    def listen(self) -> List[List[Any]]:
        """Paroles prononcées via `say` : liste de `[entité, message]`."""
        return list(self.says)

    # ------------------------------------------------------------------
    # Ciblage
    # ------------------------------------------------------------------
    def _reachable_cells(
        self, from_cell: Optional[Cell], item: Item, target_cell: Cell
    ) -> List[Cell]:
        """Cases d'où `item` peut atteindre `target_cell`."""
        if from_cell is None:
            return []
        distance = RULES.distance(from_cell, target_cell)
        if distance < item.minRange or distance > item.maxRange:
            return []
        if item.needsLos and not from_cell.lineOfSight(target_cell):
            return []
        return [from_cell]

    def _all_stand_cells(self) -> List[Cell]:
        """Cases où une entité peut se tenir (libres)."""
        return [cell for cell in self.field.cells if cell.empty]

    def weaponCell(self, target, weapon=None, ignoredCells=None):
        """Case d'où l'arme peut toucher `target` (la plus proche de `me`)."""
        cells = self.weaponCells(target, weapon, ignoredCells)
        return cells[0] if cells else None

    def weaponCells(self, target, weapon=None, ignoredCells=None) -> List[Cell]:
        """Toutes les cases d'où l'arme peut toucher `target`."""
        item = weapon if isinstance(weapon, Weapon) else (
            Weapon.get(weapon) if isinstance(weapon, int) else (
                self.me.weapon if self.me is not None else None
            )
        )
        target_cell = as_cell(target, self.field)
        if not isinstance(item, Weapon) or target_cell is None:
            return []
        ignored = {id(as_cell(c, self.field)) for c in (ignoredCells or ())}
        reachable = []
        for cell in self._all_stand_cells():
            if id(cell) in ignored:
                continue
            if self._reachable_cells(cell, item, target_cell):
                reachable.append(cell)
        origin = self.me.cell if self.me is not None else None
        if origin is not None:
            reachable.sort(key=lambda c: (origin.distance(c), c.y, c.x))
        return reachable

    def chipCell(self, chip, target, ignoredCells=None):
        """Case d'où la puce peut toucher `target`."""
        cells = self.chipCells(chip, target, ignoredCells)
        return cells[0] if cells else None

    def chipCells(self, chip, target, ignoredCells=None) -> List[Cell]:
        """Toutes les cases d'où la puce peut toucher `target`."""
        item = Chip.get(chip) if isinstance(chip, int) else chip
        target_cell = as_cell(target, self.field)
        if not isinstance(item, Chip) or target_cell is None:
            return []
        ignored = {id(as_cell(c, self.field)) for c in (ignoredCells or ())}
        reachable = []
        for cell in self._all_stand_cells():
            if id(cell) in ignored:
                continue
            if self._reachable_cells(cell, item, target_cell):
                reachable.append(cell)
        origin = self.me.cell if self.me is not None else None
        if origin is not None:
            reachable.sort(key=lambda c: (origin.distance(c), c.y, c.x))
        return reachable

    def weaponTargets(self, cell, weapon=None) -> List[Entity]:
        """Entités touchées par l'arme sur une case."""
        item = weapon if isinstance(weapon, Weapon) else (
            Weapon.get(weapon) if isinstance(weapon, int) else (
                self.me.weapon if self.me is not None else None
            )
        )
        return self._targets_on_cell(item, cell)

    def chipTargets(self, chip, cell) -> List[Entity]:
        """Entités touchées par la puce sur une case."""
        item = Chip.get(chip) if isinstance(chip, int) else chip
        return self._targets_on_cell(item, cell)

    def _targets_on_cell(self, item, cell) -> List[Entity]:
        if not isinstance(item, Item):
            return []
        target_cell = as_cell(cell, self.field)
        if target_cell is None:
            return []
        entities = []
        for area_cell in item.effectiveArea(target_cell):
            if area_cell.entity is not None and area_cell.entity.alive:
                entities.append(area_cell.entity)
        return entities

    # ------------------------------------------------------------------
    # Tours
    # ------------------------------------------------------------------
    def next_turn(self) -> int:
        """Passe au tour suivant et réinitialise PT/PM et usages d'items."""
        self.turn += 1
        for entity in self.entities:
            entity.tp = entity.maxTP
            entity.mp = entity.maxMP
            kept = []
            for effect in entity.effects:
                effect.turns -= 1
                if effect.turns > 0:
                    kept.append(effect)
            entity.effects = kept
        self._item_uses.clear()
        return self.turn

    def item_uses(self, user: Entity, item) -> int:
        """Nombre d'utilisations d'un item par une entité ce tour."""
        if isinstance(item, int):
            item_id = item
        else:
            item_id = item.id
        return self._item_uses.get((user.id, item_id), 0)

    # ------------------------------------------------------------------
    # Résolution des items
    # ------------------------------------------------------------------
    def can_use(self, user: Entity, item: Item, cell) -> int:
        """Code `Fight.Use` indiquant si l'item est utilisable sur la case.

        Ne lève jamais d'exception : renvoie `Use.SUCCESS` ou un code négatif
        (`NOT_ENOUGH_TP`, `INVALID_POSITION`, `MAX_USES`, ...).
        """
        if not isinstance(item, Item):
            return _Use.INVALID_TARGET
        target_cell = as_cell(cell, self.field)
        if target_cell is None or user.cell is None:
            return _Use.INVALID_TARGET
        if user.tp < item.cost:
            return _Use.NOT_ENOUGH_TP
        if item.maxUses > 0 and self.item_uses(user, item) >= item.maxUses:
            return _Use.MAX_USES
        # Hors portée ou ligne de vue coupée : position invalide (code -4).
        distance = RULES.distance(user.cell, target_cell)
        if distance < item.minRange or distance > item.maxRange:
            return _Use.INVALID_POSITION
        if item.needsLos and not user.cell.lineOfSight(target_cell):
            return _Use.INVALID_POSITION
        return _Use.SUCCESS

    def use_item(self, user: Entity, item: Item, cell) -> int:
        """Utilise un item si possible, applique ses effets et renvoie un code.

        `Use.SUCCESS` (1) ou `Use.CRITICAL` (2) en cas de réussite, code
        négatif sinon. Aucune exception n'est levée pour une action refusée.
        """
        code = self.can_use(user, item, cell)
        if code != _Use.SUCCESS:
            return code
        target_cell = as_cell(cell, self.field)
        if target_cell is None:  # défense : can_use l'a déjà validée
            return _Use.INVALID_TARGET
        user.tp -= item.cost
        key = (user.id, item.id)
        self._item_uses[key] = self._item_uses.get(key, 0) + 1

        critical = self.rng.random() < user.agility / RULES.CRITICAL_DIVISOR
        for feature in item.features:
            value = self._roll(feature)
            if critical:
                value *= RULES.CRITICAL_FACTOR
            for target in self._feature_targets(user, feature, item, target_cell):
                self._apply_feature(user, feature, value, target, item, critical)
        return _Use.CRITICAL if critical else _Use.SUCCESS

    def _roll(self, feature: Feature) -> int:
        """Tire la valeur d'une feature dans [minValue, maxValue]."""
        low = int(min(feature.minValue, feature.maxValue))
        high = int(max(feature.minValue, feature.maxValue))
        return self.rng.randint(low, high)

    def _feature_targets(
        self, user: Entity, feature: Feature, item: Item, target_cell: Cell
    ) -> List[Entity]:
        """Entités effectivement touchées par une feature."""
        mask = feature.targets
        if feature.modifiers & Effect.Modifier.ON_CASTER:
            return [user]

        result: List[Entity] = []
        seen = set()
        for area_cell in item.effectiveArea(target_cell):
            entity = area_cell.entity
            if entity is None or not entity.alive or id(entity) in seen:
                continue
            if not self._matches_mask(entity, user, mask):
                continue
            result.append(entity)
            seen.add(id(entity))

        # Les effets sur le lanceur s'appliquent même si la case visée est vide
        # (ex. buff de force du Glaive : on peut taper dans le vide).
        # `ALWAYS_CASTER` (32) force aussi la cible sur le lanceur.
        caster_bits = Effect.Target.CASTER | Effect.Target.ALWAYS_CASTER
        if mask & caster_bits and id(user) not in seen:
            result.append(user)
        return result

    def _matches_mask(self, entity: Entity, user: Entity, mask: int) -> bool:
        if mask == 0:
            return True
        if entity is user:
            return bool(
                mask & (Effect.Target.CASTER | Effect.Target.ALWAYS_CASTER)
            )
        if mask & Effect.Target.ENEMIES and entity.isEnemyOf(user):
            return True
        if mask & Effect.Target.ALLIES and entity.isAllyOf(user):
            return True
        return False

    def _apply_feature(
        self,
        user: Entity,
        feature: Feature,
        value: float,
        target: Entity,
        item: Item,
        critical: bool,
    ) -> None:
        """Applique une feature à une cible (formules du jeu)."""
        effect_type = feature.type

        if effect_type == Effect.DAMAGE:
            # Force : base * (1 + force / 100), puis boucliers.
            base = value * (1 + user.strength / RULES.PERCENT_DIVISOR)
            damage = self._after_shields(base, target)
            target.take_damage(damage)
            # Vol de vie : uniquement les dégâts dépendant de la force.
            steal = damage * user.wisdom / RULES.LIFE_STEAL_DIVISOR
            if steal > 0:
                user.heal(steal)
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type == Effect.LIFE_DAMAGE:
            # Pourcentage des PV max du lanceur ; les boucliers s'appliquent.
            base = user.maxLife * value / RULES.PERCENT_DIVISOR
            target.take_damage(self._after_shields(base, target))
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type == Effect.NOVA_DAMAGE:
            # Retire des PV maximum, sans bouclier, amplifié par la science.
            amount = value * (1 + user.science / RULES.PERCENT_DIVISOR)
            target.maxLife = max(0, target.maxLife - amount)
            target.life = min(target.life, target.maxLife)
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type == Effect.KILL:
            # Retire tous les PV, sans bouclier.
            target.life = 0
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type in (Effect.HEAL, Effect.RAW_HEAL):
            amount = value
            if effect_type == Effect.HEAL:
                amount *= 1 + user.wisdom / RULES.PERCENT_DIVISOR
            target.heal(amount)
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type == Effect.BOOST_MAX_LIFE:
            amount = value * (1 + user.wisdom / RULES.PERCENT_DIVISOR)
            target.maxLife += amount
            target.life += amount
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type == Effect.NOVA_VITALITY:
            amount = value * (1 + user.science / RULES.PERCENT_DIVISOR)
            target.maxLife += amount
            target.life += amount
            self._record_effect(user, feature, value, target, item, critical)
            return

        # Buffs simples : science pour les BUFF_*, aucune pour les RAW_*.
        buffs = {
            Effect.BUFF_STRENGTH: "strength",
            Effect.BUFF_AGILITY: "agility",
            Effect.BUFF_RESISTANCE: "resistance",
            Effect.BUFF_WISDOM: "wisdom",
            Effect.RAW_BUFF_STRENGTH: "strength",
            Effect.RAW_BUFF_AGILITY: "agility",
            Effect.RAW_BUFF_RESISTANCE: "resistance",
            Effect.RAW_BUFF_WISDOM: "wisdom",
            Effect.RAW_BUFF_MAGIC: "magic",
            Effect.RAW_BUFF_SCIENCE: "science",
            Effect.RAW_BUFF_POWER: "power",
        }
        if effect_type in buffs:
            amount = value
            if effect_type in _SCIENCE_AMPLIFIED:
                amount *= 1 + user.science / RULES.PERCENT_DIVISOR
            setattr(target, buffs[effect_type], getattr(target, buffs[effect_type]) + amount)
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type in (Effect.BUFF_TP, Effect.RAW_BUFF_TP):
            amount = value
            if effect_type in _SCIENCE_AMPLIFIED:
                amount *= 1 + user.science / RULES.PERCENT_DIVISOR
            target.maxTP += amount
            target.tp += amount
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type in (Effect.BUFF_MP, Effect.RAW_BUFF_MP):
            amount = value
            if effect_type in _SCIENCE_AMPLIFIED:
                amount *= 1 + user.science / RULES.PERCENT_DIVISOR
            target.maxMP += amount
            target.mp += amount
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type in (Effect.RELATIVE_SHIELD, Effect.ABSOLUTE_SHIELD):
            # Boucliers amplifiés par la résistance du lanceur.
            amount = value * (1 + user.resistance / RULES.PERCENT_DIVISOR)
            if effect_type == Effect.RELATIVE_SHIELD:
                target.relativeShield += amount
            else:
                target.absoluteShield += amount
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type == Effect.RAW_RELATIVE_SHIELD:
            target.relativeShield += value
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type == Effect.RAW_ABSOLUTE_SHIELD:
            target.absoluteShield += value
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type == Effect.VULNERABILITY:
            target.relativeShield -= value
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type == Effect.ABSOLUTE_VULNERABILITY:
            target.absoluteShield -= value
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type in (Effect.POISON, Effect.AFTEREFFECT):
            # Amplifié par la magie, ignore les boucliers.
            amount = value * (1 + user.magic / RULES.PERCENT_DIVISOR)
            target.take_damage(amount)
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type == Effect.DAMAGE_RETURN:
            target.damageReturn += value * (1 + user.agility / RULES.PERCENT_DIVISOR)
            self._record_effect(user, feature, value, target, item, critical)
            return

        if effect_type in (Effect.SHACKLE_STRENGTH, Effect.RAW_SHACKLE_STRENGTH):
            amount = value
            if effect_type == Effect.SHACKLE_STRENGTH:
                # Entrave amplifiée par la magie du lanceur ; la variante RAW
                # (`RAW_SHACKLE_STRENGTH`) ne l'est pas.
                amount *= 1 + user.magic / RULES.PERCENT_DIVISOR
            target.strength = max(0, target.strength - amount)
            self._record_effect(user, feature, value, target, item, critical)
            return

        # Types non modélisés : on conserve au moins la trace de l'effet.
        self._record_effect(user, feature, value, target, item, critical)

    @staticmethod
    def _after_shields(base: float, target: Entity) -> float:
        """Applique les boucliers relatif puis absolu, avec plancher à 0."""
        damage = (
            base * (1 - target.relativeShield / RULES.PERCENT_DIVISOR)
            - target.absoluteShield
        )
        return max(0.0, damage)

    def _record_effect(
        self,
        user: Entity,
        feature: Feature,
        value: float,
        target: Entity,
        item: Item,
        critical: bool,
    ) -> None:
        """Enregistre un effet temporaire sur la cible."""
        if feature.turns <= 0:
            return
        effect = Effect(
            type=feature.type,
            value=value,
            caster=user,
            turns=feature.turns,
            critical=critical,
            item=item,
            target=target,
            modifiers=feature.modifiers,
        )
        target.add_effect(effect)


__all__ = ["Fight"]
