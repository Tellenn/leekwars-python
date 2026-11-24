"""Mock local du SDK Leek Wars.

Le moteur du site injecte `Fight`, `Effect`, `Debug`, ... comme globaux. Le
mock reproduit ce mécanisme en liant les mêmes noms dans `builtins` :

    from leekwars_api import install, builder
    fight = builder.make_fight(me=builder.entity(), enemies=[...])
    install(fight)
    import Kepo_solo      # Kepo_solo.py lit Fight.me au niveau module

Ce package est réservé aux tests : il ne doit jamais être importé par le code
de l'IA (`Kepo_solo.py`, `libs/*`).
"""

from __future__ import annotations

import builtins
import math
from typing import Any, Dict, Optional

from . import builder, state
from .cell import Cell
from .debug import Debug
from .effect import Effect
from .entity import Entity, Leek, Me
from .fight import Fight
from .field import Field
from .items import Chip, Feature, Item, Weapon
from .registers import Registers
from .rules import RULES
from .system import System

#: Noms injectés dans `builtins` par `install`.
_BINDING_NAMES = (
    "Fight",
    "Effect",
    "Debug",
    "Field",
    "Registers",
    "System",
    "Weapon",
    "Chip",
    "Cell",
    "Entity",
    "Me",
    "Leek",
    "Item",
    "Feature",
    "Math",
)

#: Valeurs précédentes des noms liés (pour restaurer dans `uninstall`).
_SAVED_BINDINGS: Dict[str, Any] = {}


def _bindings(fight: Fight) -> Dict[str, Any]:
    """Construit le dictionnaire des noms à injecter dans `builtins`."""
    return {
        "Fight": fight,
        "Effect": Effect,
        "Debug": Debug,
        "Field": fight.field,
        "Registers": Registers,
        "System": System,
        "Weapon": Weapon,
        "Chip": Chip,
        "Cell": Cell,
        "Entity": Entity,
        "Me": Me,
        "Leek": Leek,
        "Item": Item,
        "Feature": Feature,
        # Le contrat n'exige pas `Math` : la stdlib suffit.
        "Math": math,
    }


def install(fight: Optional[Fight] = None) -> Fight:
    """Lie les noms du SDK dans `builtins` et renvoie le combat lié.

    Sans argument, reprend le dernier combat construit par `make_fight`.
    """
    if fight is None:
        current = state.get_fight()
        if current is None:
            raise RuntimeError(
                "install() sans combat : construis d'abord un combat avec "
                "leekwars_api.builder.make_fight()."
            )
        fight = current
    elif not isinstance(fight, Fight):
        raise TypeError("install() attend un objet Fight.")

    state.set_fight(fight)
    for name, value in _bindings(fight).items():
        _SAVED_BINDINGS.setdefault(name, getattr(builtins, name, _MISSING))
        setattr(builtins, name, value)
    return fight


class _Missing:
    """Sentinelle : le nom n'existait pas dans `builtins` avant l'install."""


_MISSING = _Missing()


def uninstall() -> None:
    """Retire les bindings posés par `install` et restaure l'état précédent."""
    for name in _BINDING_NAMES:
        previous = _SAVED_BINDINGS.pop(name, _MISSING)
        if previous is _MISSING:
            if hasattr(builtins, name):
                delattr(builtins, name)
        else:
            setattr(builtins, name, previous)
    state.reset()


__all__ = [
    "install",
    "uninstall",
    "builder",
    "RULES",
    "Fight",
    "Effect",
    "Debug",
    "Field",
    "Registers",
    "System",
    "Weapon",
    "Chip",
    "Cell",
    "Entity",
    "Me",
    "Leek",
    "Item",
    "Feature",
]
