"""Constantes `Effect` du SDK Leek Wars.

Deux usages cohabitent comme dans l'API réelle :

* `Effect.Type`, `Effect.Target`, `Effect.Modifier` sont des namespaces de
  constantes (masques binaires, combinables avec `|` et testables avec `&`) ;
* les mêmes constantes sont aussi accessibles directement sur `Effect`
  (`Effect.DAMAGE`, ...), parce que le code de l'IA écrit `Effect.DAMAGE`.

Valeurs numériques : encyclopédie FR « Effets » (snapshot
`docs/encyclopedia/effets.md`). Les types 60 à 64 de l'encyclopédie ne font
pas partie du contrat du mock (59 types).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

#: Types d'effets : nom -> valeur, dans l'ordre de l'encyclopédie.
_TYPE_VALUES: Dict[str, int] = {
    "DAMAGE": 1,
    "HEAL": 2,
    "BUFF_STRENGTH": 3,
    "BUFF_AGILITY": 4,
    "RELATIVE_SHIELD": 5,
    "ABSOLUTE_SHIELD": 6,
    "BUFF_MP": 7,
    "BUFF_TP": 8,
    "DEBUFF": 9,
    "TELEPORT": 10,
    "INVERT": 11,
    "BOOST_MAX_LIFE": 12,
    "POISON": 13,
    "SUMMON": 14,
    "RESURRECT": 15,
    "KILL": 16,
    "SHACKLE_MP": 17,
    "SHACKLE_TP": 18,
    "SHACKLE_STRENGTH": 19,
    "DAMAGE_RETURN": 20,
    "BUFF_RESISTANCE": 21,
    "BUFF_WISDOM": 22,
    "ANTIDOTE": 23,
    "SHACKLE_MAGIC": 24,
    "AFTEREFFECT": 25,
    "VULNERABILITY": 26,
    "ABSOLUTE_VULNERABILITY": 27,
    "LIFE_DAMAGE": 28,
    "STEAL_ABSOLUTE_SHIELD": 29,
    "NOVA_DAMAGE": 30,
    "RAW_BUFF_MP": 31,
    "RAW_BUFF_TP": 32,
    "POISON_TO_SCIENCE": 33,
    "DAMAGE_TO_ABSOLUTE_SHIELD": 34,
    "DAMAGE_TO_STRENGTH": 35,
    "NOVA_DAMAGE_TO_MAGIC": 36,
    "RAW_ABSOLUTE_SHIELD": 37,
    "RAW_BUFF_STRENGTH": 38,
    "RAW_BUFF_MAGIC": 39,
    "RAW_BUFF_SCIENCE": 40,
    "RAW_BUFF_AGILITY": 41,
    "RAW_BUFF_RESISTANCE": 42,
    "PROPAGATION": 43,
    "RAW_BUFF_WISDOM": 44,
    "NOVA_VITALITY": 45,
    "ATTRACT": 46,
    "SHACKLE_AGILITY": 47,
    "SHACKLE_WISDOM": 48,
    "REMOVE_SHACKLES": 49,
    "MOVED_TO_MP": 50,
    "PUSH": 51,
    "RAW_BUFF_POWER": 52,
    "REPEL": 53,
    "RAW_RELATIVE_SHIELD": 54,
    "ALLY_KILLED_TO_AGILITY": 55,
    "KILL_TO_TP": 56,
    "RAW_HEAL": 57,
    "CRITICAL_TO_HEAL": 58,
    "ADD_STATE": 59,
    "TOTAL_DEBUFF": 60,
    "STEAL_LIFE": 61,
    "MULTIPLY_STATS": 62,
    "DAMAGE_TO_RESISTANCE": 63,
    "SUPERINFECTION": 64,
    "RAW_SHACKLE_STRENGTH": 65,
}

#: Alias historiques : même valeur que leur type canonique.
_TYPE_ALIASES: Dict[str, str] = {
    "BUFF_FORCE": "BUFF_STRENGTH",
}

#: Cibles affectées par un effet (masque binaire).
_TARGET_VALUES: Dict[str, int] = {
    "NOT_CASTER": 0,
    "ENEMIES": 1,
    "ALLIES": 2,
    "CASTER": 4,
    "NON_SUMMONS": 8,
    "SUMMONS": 16,
    "ALWAYS_CASTER": 32,
}

#: Modificateurs d'effet (masque binaire).
_MODIFIER_VALUES: Dict[str, int] = {
    "STACKABLE": 1,
    "MULTIPLIED_BY_TARGETS": 2,
    "ON_CASTER": 4,
    "NOT_REPLACEABLE": 8,
    "IRREDUCTIBLE": 16,
}


class _Constants:
    """Namespace minimal : les constantes sont posées en attributs de classe."""


class Type(_Constants):
    """Types d'effets (`Effect.Type.DAMAGE`, ...)."""


class Target(_Constants):
    """Masque des entités affectées (`Effect.Target.ENEMIES`, ...)."""


class Modifier(_Constants):
    """Masque des modificateurs d'effet (`Effect.Modifier.STACKABLE`, ...)."""


for _name, _value in _TYPE_VALUES.items():
    setattr(Type, _name, _value)
for _name, _value in _TARGET_VALUES.items():
    setattr(Target, _name, _value)
for _name, _value in _MODIFIER_VALUES.items():
    setattr(Modifier, _name, _value)


class Effect:
    """Un effet, actif sur une entité ou lancé par un item.

    Le tableau `raw` suit le format du jeu :
    `[type, value, caster_id, turns, critical, item_id, target_id, modifiers]`.
    Les attributs typés donnent les mêmes informations sous forme d'objets.
    """

    #: Namespaces de constantes (assignés après la définition de la classe).
    Type = Type
    Target = Target
    Modifier = Modifier

    def __init__(
        self,
        raw: Optional[List[Any]] = None,
        *,
        type: int = 0,
        value: float = 0,
        caster: Any = None,
        turns: int = 0,
        critical: bool = False,
        item: Any = None,
        target: Any = None,
        modifiers: int = 0,
    ) -> None:
        if raw is not None:
            # Reconstruit les attributs depuis le tableau brut du jeu.
            self.raw: List[Any] = list(raw)
            self.type = int(raw[0])
            self.value = raw[1]
            self.caster = None if raw[2] is None else raw[2]
            self.turns = int(raw[3])
            self.critical = bool(raw[4])
            self.item = None if raw[5] is None else raw[5]
            self.target = None if raw[6] is None else raw[6]
            self.modifiers = int(raw[7]) if len(raw) > 7 else 0
            return

        self.type = int(type)
        self.value = value
        self.caster = caster
        self.turns = int(turns)
        self.critical = bool(critical)
        self.item = item
        self.target = target
        self.modifiers = int(modifiers)
        self.raw = [
            self.type,
            self.value,
            getattr(caster, "id", caster),
            self.turns,
            self.critical,
            getattr(item, "id", item),
            getattr(target, "id", target),
            self.modifiers,
        ]

    @staticmethod
    def getAll() -> List[int]:
        """Liste des ids de types d'effets existants."""
        return sorted(_TYPE_VALUES.values())

    def __repr__(self) -> str:
        return f"Effect(type={self.type}, value={self.value}, turns={self.turns})"

    # Reste du contrat : `raw` est un tableau mutable côté jeu.
    def to_raw(self) -> List[Any]:
        """Renvoie une copie du tableau brut."""
        return list(self.raw)


# Le code de l'IA écrit `Effect.DAMAGE` : on duplique les constantes de type
# directement sur la classe Effect, comme le fait le moteur du site.
for _name, _value in _TYPE_VALUES.items():
    setattr(Effect, _name, _value)

# Alias : `Effect.BUFF_FORCE` vaut `Effect.BUFF_STRENGTH` (3).
for _alias, _canonical in _TYPE_ALIASES.items():
    setattr(Type, _alias, getattr(Type, _canonical))
    setattr(Effect, _alias, getattr(Effect, _canonical))


def type_name(value: int) -> str:
    """Nom lisible d'un type d'effet (utile aux journaux de test)."""
    for name, candidate in _TYPE_VALUES.items():
        if candidate == value:
            return name
    return f"TYPE_{value}"


#: Effets qui s'appliquent au lanceur (soin, buff, bouclier) : ils le
#: touchent même si la case visée est vide. Un effet offensif ne touche
#: JAMAIS le lanceur : sur le site, le tir du joueur ne le blesse pas (le
#: masque "31" des armes du catalogue contient le bit CASTER, mais la zone
#: d'effet ne contient que la case visée).
_SELF_EFFECT_NAMES = (
    "HEAL", "RAW_HEAL", "BOOST_MAX_LIFE", "NOVA_VITALITY",
    "BUFF_STRENGTH", "BUFF_AGILITY", "BUFF_RESISTANCE", "BUFF_WISDOM",
    "BUFF_TP", "BUFF_MP",
    "RAW_BUFF_STRENGTH", "RAW_BUFF_AGILITY", "RAW_BUFF_RESISTANCE",
    "RAW_BUFF_WISDOM", "RAW_BUFF_MAGIC", "RAW_BUFF_SCIENCE",
    "RAW_BUFF_POWER", "RAW_BUFF_TP", "RAW_BUFF_MP",
    "RELATIVE_SHIELD", "ABSOLUTE_SHIELD",
    "RAW_RELATIVE_SHIELD", "RAW_ABSOLUTE_SHIELD",
)

_SELF_EFFECTS = {_TYPE_VALUES[name] for name in _SELF_EFFECT_NAMES}


def is_self_effect(effect_type: int) -> bool:
    """L'effet s'applique-t-il au lanceur (soin, buff, bouclier) ?"""
    return effect_type in _SELF_EFFECTS


__all__ = ["Effect", "Type", "Target", "Modifier", "type_name",
           "is_self_effect"]
