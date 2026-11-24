"""Entités du combat (`Entity`, `Me`, `Leek`).

Les attributs reprennent les noms de l'API du site (`maxLife`, `maxTP`,
`relativeShield`, ...). `Me` ajoute les actions de l'IA (déplacement,
utilisation d'armes et de puces) ; les règles de résolution (portée, ligne de
vue, application des effets) vivent dans `fight.py`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, List, Optional

from .cell import Cell, as_cell
from .items import Chip, Feature, Item, Weapon
from .rules import RULES

if TYPE_CHECKING:  # pragma: no cover - annotations uniquement
    from .effect import Effect
    from .fight import Fight


class _EntityType:
    """Genre d'entité (`Entity.Type.*`)."""

    LEEK = 0
    BULB = 1
    TURRET = 2
    CHEST = 3
    MOB = 4
    PLANT = 5


class _Stat:
    """Caractéristiques adressables via `Entity.Stat.*`."""

    LIFE = 0
    STRENGTH = 1
    AGILITY = 2
    WISDOM = 3
    RESISTANCE = 4
    SCIENCE = 5
    MAGIC = 6
    POWER = 7
    TP = 8
    MP = 9
    LEVEL = 10


class Entity:
    """Une entité du combat (poireau, bulbe, tourelle...)."""

    Type = _EntityType
    Stat = _Stat

    def __init__(
        self,
        *,
        id: Optional[int] = None,
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
        cell: Optional[Cell] = None,
        weapons: Iterable[Weapon] = (),
        chips: Iterable[Chip] = (),
        relative_shield: float = 0,
        absolute_shield: float = 0,
        side: int = 1,
        entity_type: int = _EntityType.LEEK,
    ) -> None:
        self.id = id
        self.name = name
        self.life = life
        self.maxLife = max_life
        self.tp = tp
        self.maxTP = max_tp
        self.mp = mp
        self.maxMP = max_mp
        self.strength = strength
        self.agility = agility
        self.wisdom = wisdom
        self.resistance = resistance
        self.science = science
        self.magic = magic
        self.power = power
        self.level = level
        self.cell: Optional[Cell] = cell
        self.weapon: Optional[Weapon] = None
        self.weapons: List[Weapon] = list(weapons)
        self.chips: List[Chip] = list(chips)
        self.absoluteShield = absolute_shield
        self.relativeShield = relative_shield
        self.damageReturn = 0
        self.components: List[int] = []
        self.effects: List["Effect"] = []
        self.launchedEffects: List["Effect"] = []
        self.passiveEffects: List[Feature] = []
        self.states: List[int] = []
        self.summons: List["Entity"] = []
        self.summoner: Optional["Entity"] = None
        self.summoned = False
        self.isStatic = entity_type in (_EntityType.TURRET, _EntityType.CHEST)
        self.side = side
        self.teamID = side
        self.leekID = id
        self.entityType = entity_type
        self.frequency = 0
        self.cores = 0
        self.ram = 0
        self.birthTurn = 0
        self.turnOrder = 0
        self.awakeningZone = 0
        self.plantTriggers: List["Entity"] = []
        self.teamName = ""
        self.compositionName = ""
        self.farmerID = 0
        self.farmerName = ""
        self.farmerCountry = ""
        self.aiID = 0
        self.aiName = ""
        self.aiPath: Optional[str] = None
        #: Combat auquel l'entité appartient (posé par make_fight).
        self.fight: Optional["Fight"] = None

    # ------------------------------------------------------------------
    # État
    # ------------------------------------------------------------------
    @property
    def alive(self) -> bool:
        """L'entité est-elle encore en vie ?"""
        return self.life > 0

    @property
    def dead(self) -> bool:
        """L'entité est-elle morte ?"""
        return not self.alive

    def heal(self, amount: float) -> None:
        """Rend des PV sans dépasser les PV maximum."""
        self.life = min(self.maxLife, self.life + amount)

    def take_damage(self, amount: float, erosion_rate: float = 0.0) -> float:
        """Retire des PV et renvoie le montant réellement perdu.

        `erosion_rate` : part des dégâts perdus retirée à la vie maximum
        (fr/Érosion : 5 % des dégâts classiques, 10 % du poison).
        """
        loss = min(self.life, max(0, amount))
        self.life -= loss
        if erosion_rate > 0 and loss > 0:
            self.maxLife = max(0, self.maxLife - loss * erosion_rate)
        return loss

    def add_effect(self, effect: "Effect") -> None:
        """Ajoute un effet actif (durée décrémentée par `Fight.next_turn`)."""
        self.effects.append(effect)

    # ------------------------------------------------------------------
    # Relations et géométrie
    # ------------------------------------------------------------------
    def isAlly(self) -> bool:
        """L'entité est-elle dans le camp de `Fight.me` ?"""
        fight = self.fight
        if fight is None or fight.me is None:
            return True
        return self.side == fight.me.side

    def isEnemy(self) -> bool:
        """L'entité est-elle dans le camp adverse ?"""
        return not self.isAlly()

    def isAllyOf(self, other: "Entity") -> bool:
        """Même camp qu'une autre entité donnée."""
        return self.side == other.side

    def isEnemyOf(self, other: "Entity") -> bool:
        """Camp opposé à une autre entité donnée."""
        return self.side != other.side

    def distance(self, target) -> int:
        """Distance en cases jusqu'à une cellule, une entité ou un id."""
        if self.cell is None:
            return -1
        other = as_cell(target, self.cell.field)
        if other is None:
            return -1
        return int(RULES.distance(self.cell, other))

    def stat(self, stat: int) -> float:
        """Valeur d'une caractéristique par sa constante `Entity.Stat.*`."""
        mapping = {
            _Stat.LIFE: self.life,
            _Stat.STRENGTH: self.strength,
            _Stat.AGILITY: self.agility,
            _Stat.WISDOM: self.wisdom,
            _Stat.RESISTANCE: self.resistance,
            _Stat.SCIENCE: self.science,
            _Stat.MAGIC: self.magic,
            _Stat.POWER: self.power,
            _Stat.TP: self.tp,
            _Stat.MP: self.mp,
            _Stat.LEVEL: self.level,
        }
        return mapping.get(stat, 0)

    @staticmethod
    def get(entity_id: int) -> Optional["Entity"]:
        """Entité d'id donné dans le combat actif, ou None."""
        from . import state

        fight = state.get_fight()
        if fight is None:
            return None
        return fight.get_entity(entity_id)

    def __repr__(self) -> str:
        return f"{self.name}#{self.id}"


class Leek(Entity):
    """Un poireau (aucun comportement spécifique dans le mock)."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("entity_type", _EntityType.LEEK)
        super().__init__(**kwargs)


class Me(Entity):
    """L'entité pilotée par l'IA, avec les actions de combat."""

    # ------------------------------------------------------------------
    # Déplacement
    # ------------------------------------------------------------------
    def _require_fight(self) -> "Fight":
        if self.fight is None:
            raise RuntimeError(
                "Cette entité n'est rattachée à aucun combat : "
                "utilise builder.make_fight()."
            )
        return self.fight

    def moveToward(self, target, mp: Optional[int] = None) -> int:
        """Se rapproche de `target` en dépensant au plus `mp` PM.

        Le déplacement est glouton, en 8 directions, et s'arrête à une case de
        la cible (on ne peut pas occuper sa case). Renvoie les PM dépensés.
        """
        fight = self._require_fight()
        destination = as_cell(target, fight.field)
        if destination is None or self.cell is None or self.isStatic:
            return 0
        budget = min(self.mp if mp is None else int(mp), self.mp)
        spent = 0
        while spent < budget:
            if RULES.distance(self.cell, destination) <= 1:
                break
            dx = _sign(destination.x - self.cell.x)
            dy = _sign(destination.y - self.cell.y)
            moved = False
            # Diagonale d'abord, puis les deux axes séparément.
            for step_x, step_y in ((dx, dy), (dx, 0), (0, dy)):
                if step_x == 0 and step_y == 0:
                    continue
                candidate = fight.field.get_cell(
                    self.cell.x + step_x, self.cell.y + step_y
                )
                if candidate is None or not candidate.empty:
                    continue
                if RULES.distance(candidate, destination) >= RULES.distance(
                    self.cell, destination
                ):
                    continue
                fight.field.move_entity(self, candidate)
                spent += 1
                moved = True
                break
            if not moved:
                break
        self.mp -= spent
        return spent

    def moveAwayFrom(self, target, mp: Optional[int] = None) -> int:
        """S'éloigne de `target` en dépensant au plus `mp` PM."""
        fight = self._require_fight()
        origin = as_cell(target, fight.field)
        if origin is None or self.cell is None or self.isStatic:
            return 0
        budget = min(self.mp if mp is None else int(mp), self.mp)
        spent = 0
        while spent < budget:
            current = RULES.distance(self.cell, origin)
            best: Optional[Cell] = None
            best_distance = current
            equal: Optional[Cell] = None
            for step_x in (-1, 0, 1):
                for step_y in (-1, 0, 1):
                    if step_x == 0 and step_y == 0:
                        continue
                    candidate = fight.field.get_cell(
                        self.cell.x + step_x, self.cell.y + step_y
                    )
                    if candidate is None or not candidate.empty:
                        continue
                    distance = RULES.distance(candidate, origin)
                    if distance > best_distance:
                        best_distance = distance
                        best = candidate
                    elif distance == current and equal is None:
                        equal = candidate
            # À défaut de case strictement plus éloignée (coin de carte),
            # on accepte une case latérale qui ne rapproche pas.
            if best is None:
                best = equal
            if best is None:
                break
            fight.field.move_entity(self, best)
            spent += 1
        self.mp -= spent
        return spent

    def moveTowardCells(self, cells: Iterable, mp: Optional[int] = None) -> int:
        """Se rapproche de la cellule la plus proche d'une liste."""
        target = self._nearest_cell(cells)
        return 0 if target is None else self.moveToward(target, mp)

    def moveTowardEntities(self, entities: Iterable, mp: Optional[int] = None) -> int:
        """Se rapproche de l'entité la plus proche d'une liste."""
        return self.moveTowardCells(entities, mp)

    def moveTowardLine(self, a, b, mp: Optional[int] = None) -> int:
        """Se rapproche d'une ligne (approximation : l'extrémité la plus proche)."""
        return self.moveTowardCells((a, b), mp)

    def moveAwayFromCells(self, cells: Iterable, mp: Optional[int] = None) -> int:
        """S'éloigne de la cellule la plus proche d'une liste."""
        target = self._nearest_cell(cells)
        return 0 if target is None else self.moveAwayFrom(target, mp)

    def moveAwayFromEntities(self, entities: Iterable, mp: Optional[int] = None) -> int:
        """S'éloigne de l'entité la plus proche d'une liste."""
        return self.moveAwayFromCells(entities, mp)

    def moveAwayFromLine(self, a, b, mp: Optional[int] = None) -> int:
        """S'éloigne d'une ligne (approximation : l'extrémité la plus proche)."""
        return self.moveAwayFromCells((a, b), mp)

    def _nearest_cell(self, values: Iterable) -> Optional[Cell]:
        """Cellule la plus proche parmi une liste de cellules/entités/ids."""
        if self.cell is None:
            return None
        best: Optional[Cell] = None
        best_distance = 0
        for value in values:
            cell = as_cell(value, self.cell.field)
            if cell is None:
                continue
            distance = RULES.distance(self.cell, cell)
            if best is None or distance < best_distance:
                best = cell
                best_distance = distance
        return best

    # ------------------------------------------------------------------
    # Équipement
    # ------------------------------------------------------------------
    def setWeapon(self, weapon) -> bool:
        """Équipe une arme ; coûte 1 PT (sauf si elle est déjà en main)."""
        fight = self._require_fight()
        target = Weapon.get(weapon) if isinstance(weapon, int) else weapon
        if not isinstance(target, Weapon):
            return False
        if target is self.weapon:
            return True
        if target not in self.weapons:
            return False
        if self.tp < 1:
            return False
        self.tp -= 1
        self.weapon = target
        return True

    def itemUses(self, item) -> int:
        """Nombre d'utilisations d'un item pendant le tour courant."""
        return self._require_fight().item_uses(self, item)

    def setLoadout(self, loadout, changeStats: bool = True) -> bool:
        """Change l'équipement courant (mock : loadouts en mémoire)."""
        del changeStats
        fight = self._require_fight()
        if isinstance(loadout, str):
            data = fight.loadouts.get(loadout)
            if data is None:
                return False
            loadout = data
        weapons = loadout.get("weapons", []) if isinstance(loadout, dict) else []
        chips = loadout.get("chips", []) if isinstance(loadout, dict) else []
        self.weapons = [w for w in (Weapon.get(i) for i in weapons) if w is not None]
        self.chips = [c for c in (Chip.get(i) for i in chips) if c is not None]
        self.weapon = self.weapons[0] if self.weapons else None
        return True

    def getInventory(self) -> Optional[dict]:
        """Inventaire du poireau (non modélisé par le mock)."""
        return None

    # ------------------------------------------------------------------
    # Armes et puces
    # ------------------------------------------------------------------
    def useWeapon(self, target):
        """Utilise l'arme équipée sur une entité."""
        fight = self._require_fight()
        if self.weapon is None:
            return fight.Use.INVALID_STATE
        cell = as_cell(target, fight.field)
        if cell is None:
            return fight.Use.INVALID_TARGET
        return fight.use_item(self, self.weapon, cell)

    def useWeaponOnCell(self, cell):
        """Utilise l'arme équipée sur une case."""
        fight = self._require_fight()
        if self.weapon is None:
            return fight.Use.INVALID_STATE
        return fight.use_item(self, self.weapon, cell)

    def useChip(self, chip, target=None):
        """Utilise une puce.

        Sans cible explicite : les puces offensives visent l'ennemi le plus
        proche, les autres se visent elles-mêmes (comportement attendu par
        `libs/decision_lib.py`, qui appelle `me.useChip(chip)`).
        """
        fight = self._require_fight()
        item = Chip.get(chip) if isinstance(chip, int) else chip
        if not isinstance(item, Chip):
            return fight.Use.INVALID_TARGET
        if target is None:
            if any(f.targets & fight.Effect.Target.ENEMIES for f in item.features):
                target = fight.getNearestEnemy()
            else:
                target = self
        cell = as_cell(target, fight.field) if target is not None else None
        if cell is None:
            return fight.Use.INVALID_TARGET
        return fight.use_item(self, item, cell)

    def useChipOnCell(self, chip, cell):
        """Utilise une puce sur une case précise."""
        fight = self._require_fight()
        item = Chip.get(chip) if isinstance(chip, int) else chip
        if not isinstance(item, Chip):
            return fight.Use.INVALID_TARGET
        return fight.use_item(self, item, cell)

    # ------------------------------------------------------------------
    # Prédicats d'utilisation
    # ------------------------------------------------------------------
    def canUseWeapon(self, target, weapon=None) -> bool:
        """Peut-on utiliser l'arme (équipée ou fournie) sur `target` ?

        L'ordre historique `canUseWeapon(weapon, target)` reste accepté quand
        le premier argument est un objet arme.
        """
        fight = self._require_fight()
        if isinstance(target, Weapon) and not isinstance(weapon, Weapon):
            target, weapon = weapon, target
        item = self.weapon if weapon is None else (
            Weapon.get(weapon) if isinstance(weapon, int) else weapon
        )
        if not isinstance(item, Weapon):
            return False
        cell = as_cell(target, fight.field)
        if cell is None:
            return False
        return fight.can_use(self, item, cell) == fight.Use.SUCCESS

    def canUseWeaponOnCell(self, cell, weapon=None) -> bool:
        """Peut-on utiliser l'arme sur une case ?"""
        return self.canUseWeapon(cell, weapon)

    def canUseChip(self, chip, target) -> bool:
        """Peut-on utiliser la puce sur `target` ?"""
        fight = self._require_fight()
        item = Chip.get(chip) if isinstance(chip, int) else chip
        cell = as_cell(target, fight.field)
        if not isinstance(item, Chip) or cell is None:
            return False
        return fight.can_use(self, item, cell) == fight.Use.SUCCESS

    def canUseChipOnCell(self, chip, cell) -> bool:
        """Peut-on utiliser la puce sur une case ?"""
        return self.canUseChip(chip, cell)

    # ------------------------------------------------------------------
    # Divers
    # ------------------------------------------------------------------
    def say(self, message: Any) -> bool:
        """Prononce un message (visible via `fight.says`)."""
        fight = self._require_fight()
        fight.says.append([self, str(message)])
        return True

    def lama(self) -> None:
        """Fait dire « lama » à l'entité."""
        self.say("lama")

    def resurrect(self, target, cell, chip=None):
        """Ressuscite une entité (PV max divisés par deux, PV au quart)."""
        fight = self._require_fight()
        entity = fight.get_entity(target) if isinstance(target, int) else target
        if not isinstance(entity, Entity) or entity.alive:
            return fight.Use.RESURRECT_INVALID_ENTITY
        destination = as_cell(cell, fight.field)
        if destination is None or not destination.empty:
            return fight.Use.INVALID_POSITION
        entity.maxLife = entity.maxLife / 2
        entity.life = entity.maxLife / 2
        fight.field.move_entity(entity, destination)
        return fight.Use.SUCCESS

    def summon(self, chip, cell, callback, name: Optional[str] = None):
        """Invoque un bulbe (version minimale du mock)."""
        fight = self._require_fight()
        destination = as_cell(cell, fight.field)
        if destination is None or not destination.empty:
            return fight.Use.INVALID_POSITION
        living_summons = sum(1 for e in fight.entities if e.summoned and e.alive)
        if living_summons >= fight.SUMMON_LIMIT:
            return fight.Use.TOO_MANY_SUMMONS
        bulb = Entity(
            name=name or "bulb",
            life=50,
            max_life=50,
            side=self.side,
            entity_type=_EntityType.BULB,
        )
        bulb.summoned = True
        bulb.summoner = self
        bulb.fight = fight
        self.summons.append(bulb)
        fight.register_entity(bulb)
        fight.field.move_entity(bulb, destination)
        callback()
        return fight.Use.SUCCESS


def _sign(value: int) -> int:
    """Signe d'un entier (-1, 0 ou 1)."""
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


__all__ = ["Entity", "Me", "Leek"]
