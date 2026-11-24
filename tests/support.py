"""Helpers partagés par les tests (non collecté par unittest).

Fournit :
  - la mise à disposition de la racine du dépôt dans sys.path (pour
    `import Kepo_solo` et `import libs.xxx`) ;
  - `load_ai(fight)` : installe le mock puis (re)charge le module
    `Kepo_solo`, exactement comme le moteur Leek Wars évalue le point
    d'entrée ;
  - des raccourcis de construction de scénario.
"""

import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from leekwars_api import builder, install  # noqa: E402
import libs.logs_lib  # noqa: E402

# Le code de l'IA lit des globaux du SDK (Effect, Fight, Debug) **au moment
# de l'import** de ses modules (ex. libs/constants_lib.py). Sur le site ces
# globaux sont toujours présents ; en local il faut donc installer le mock
# AVANT d'importer `libs.*` -> on installe un combat par défaut dès
# l'import de ce module.
_DEFAULT_FIGHT = builder.make_fight(
    me=builder.entity(life=100, max_life=100, cell=(0, 0)),
    enemies=[builder.entity(life=50, max_life=50, cell=(1, 0))],
)
install(_DEFAULT_FIGHT)

# `libs.decision_lib` se charge APRÈS l'installation du mock : ses
# modules lisent les globaux du SDK (Effect, Fight) au moment de
# l'import.
import libs.decision_lib  # noqa: E402

# ---------------------------------------------------------------------------
# Constantes de scénario (valeurs nommées : les tests restent lisibles)
# ---------------------------------------------------------------------------

PISTOL_DAMAGE = 10          # dégâts bruts de l'arme de test
RIFLE_DAMAGE = 30           # arme "lourde", plus chère
HEAL_AMOUNT = 15            # soin brut de la puce de soin
STRENGTH_BUFF = 20          # buff de force brut

#: Masques de cibles réels du catalogue du jeu (api/chip/get-all) :
#: 31 = ENNEMIS|ALLIES|CASTER|NON_SUMMONS|SUMMONS (armes, bandage...),
#: 30 = ALLIES|CASTER|NON_SUMMONS|SUMMONS (puces de buff sur soi).
GAME_TARGETS_ALL = 31
GAME_TARGETS_SELF = 30


def load_ai(fight):
    """Installe le mock du SDK et recharge `Kepo_solo` (son `me` est figé au
    niveau module, il faut donc le recharger après chaque changement de
    scénario)."""
    install(fight)
    # nouveau combat = journal repart de zéro (le "une fois par combat"
    # des logs est réarmé)
    libs.logs_lib.reset()
    # ... et l'état de décision aussi (PV mémorisés, buffs encore actifs)
    libs.decision_lib.reset_state()
    ai = importlib.import_module("Kepo_solo")
    importlib.reload(ai)
    return ai


def pistol(range_=1, damage=PISTOL_DAMAGE, cost=1):
    """Arme de test : dégâts constants, sans modificateur."""
    return builder.weapon(
        "pistol",
        cost=cost,
        min_range=0,
        max_range=range_,
        features=[
            builder.feature(
                builder.Effect.DAMAGE,
                builder.Effect.Target.ENEMIES,
                damage,
                damage,
            )
        ],
    )


def rifle(range_=2, damage=RIFLE_DAMAGE, cost=3):
    return builder.weapon(
        "rifle",
        cost=cost,
        min_range=0,
        max_range=range_,
        features=[
            builder.feature(
                builder.Effect.DAMAGE,
                builder.Effect.Target.ENEMIES,
                damage,
                damage,
            )
        ],
    )


def heal_chip(amount=HEAL_AMOUNT, cost=2):
    """Puce de soin : effet HEAL sur le lanceur (amplifié par la sagesse)."""
    return builder.chip(
        "bandage",
        cost=cost,
        min_range=0,
        max_range=0,
        features=[
            builder.feature(
                builder.Effect.HEAL,
                builder.Effect.Target.CASTER,
                amount,
                amount,
            )
        ],
    )


def raw_heal_chip(amount=HEAL_AMOUNT, cost=2):
    """Puce de soin non amplifié par la sagesse (Effect.RAW_HEAL)."""
    return builder.chip(
        "potion",
        cost=cost,
        min_range=0,
        max_range=0,
        features=[
            builder.feature(
                builder.Effect.RAW_HEAL,
                builder.Effect.Target.CASTER,
                amount,
                amount,
            )
        ],
    )


def strength_chip(amount=STRENGTH_BUFF, cost=2):
    """Puce de buff de force (amplifiée par la science)."""
    return builder.chip(
        "tonique",
        cost=cost,
        min_range=0,
        max_range=0,
        features=[
            builder.feature(
                builder.Effect.BUFF_STRENGTH,
                builder.Effect.Target.CASTER,
                amount,
                amount,
            )
        ],
    )


def raw_strength_chip(amount=STRENGTH_BUFF, cost=2):
    """Puce de buff de force NON amplifiée par la science (Effect.RAW_BUFF_STRENGTH)."""
    return builder.chip(
        "elixir",
        cost=cost,
        min_range=0,
        max_range=0,
        features=[
            builder.feature(
                builder.Effect.RAW_BUFF_STRENGTH,
                builder.Effect.Target.CASTER,
                amount,
                amount,
            )
        ],
    )


def make_fight(me=None, enemies=None, allies=None, **kwargs):
    """Raccourci vers `builder.make_fight` avec des valeurs par défaut
   Reasonables (un poireau full vie face à un ennemi proche)."""
    if me is None:
        me = builder.entity(life=100, max_life=100, tp=10, max_tp=10,
                            mp=10, max_mp=10, cell=(0, 0))
    if enemies is None:
        enemies = [builder.entity(life=50, max_life=50, cell=(1, 0))]
    return builder.make_fight(me=me, enemies=enemies, allies=allies or [],
                              **kwargs)


def shield_chip(relative=10, absolute=0, turns=2, cost=2, name="forteresse"):
    """Puce de bouclier : effet RELATIVE_SHIELD / ABSOLUTE_SHIELD sur le
    lanceur (fr/Résistance)."""
    features = []
    if relative:
        features.append(builder.feature(
            builder.Effect.RELATIVE_SHIELD,
            builder.Effect.Target.CASTER | builder.Effect.Target.ALLIES,
            relative, relative, turns=turns,
        ))
    if absolute:
        features.append(builder.feature(
            builder.Effect.ABSOLUTE_SHIELD,
            builder.Effect.Target.CASTER | builder.Effect.Target.ALLIES,
            absolute, absolute, turns=turns,
        ))
    return builder.chip(name, cost=cost, min_range=0, max_range=0,
                        features=features)


def protein_chip(min_value=80, max_value=100, turns=2, cost=3, cooldown=3):
    """Puce "Protéines" (id 8 du catalogue) : +80-100 force brute (RAW,
    donc pas amplifiée par la science) pendant 2 tours, 3 PT, 3 tours de
    cooldown. Le masque de cibles est celui du catalogue (30)."""
    return builder.chip(
        "protein",
        cost=cost,
        min_range=0,
        max_range=4,
        features=[
            builder.feature(
                builder.Effect.RAW_BUFF_STRENGTH,
                GAME_TARGETS_SELF,
                min_value, max_value, turns=turns,
            )
        ],
        cooldown=cooldown,
    )


def game_heal_chip(amount=25, cost=2, cooldown=1):
    """Puce de soin du catalogue (bandage, id 3) : effet HEAL avec le
    masque 31 du site (il contient le bit ENNEMIS)."""
    return builder.chip(
        "bandage",
        cost=cost,
        min_range=0,
        max_range=6,
        features=[
            builder.feature(
                builder.Effect.HEAL,
                GAME_TARGETS_ALL,
                amount, amount,
            )
        ],
        cooldown=cooldown,
    )
