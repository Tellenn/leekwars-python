# @version:3.12
#
# IA "Kepo solo" - point d'entrée (entry point).
#
# PROFIL DE JEU : DPS BRUT. Le build de Kepo est centré sur la FORCE
# (dégâts) ; la protection viendra plus tard (résistance / sagesse).
# Conséquences sur le code :
#   - le score de décision est dominé par les dégâts attendus
#     (force + crits - boucliers ennemi) ;
#   - le soin n'est choisi que si son ratio PV/PT bat le ratio dégâts/PT ;
#   - les buffs de force sont valorisés (ils multiplient tous les tirs
#     suivants du tour).
#
# Structure follows the encyclopedia fr/Python advice: with turn(), the file
# body is evaluated once (imports, persistent state), then turn() is run by
# the engine at every turn.
#
# DO NOT call turn() at the end of this file: the engine already replays it
# at each turn, an explicit call would fire an extra turn at body-evaluation
# time (see AGENTS.md §8, gap #10).
#
# All libraries live in the "libs" folder of the Leek Wars drive:
#   libs/constants_lib.py, libs/logs_lib.py, libs/analysis_lib.py,
#   libs/decision_lib.py, libs/equipment_lib.py
#
# IMPORT NOTE: the editor's type stubs don't declare the "libs" package, so
# Pyright flags the import as unresolved and members as unknown. Runtime is
# unaffected; "# type: ignore" silences these false positives. A local copy of
# the official stubs is available in stubs/__builtins__.pyi for local
# checking.
#
# Decision flow per turn:
#   0. equip a weapon if none held (best damage/TP ratio)
#   1. find nearest enemy
#   2. loop: pick the best value/TP option among attacks, buffs and HEALS,
#      execute it (a heal wins exactly when its heal/TP ratio beats the
#      best damage/TP ratio, as specified; heal is wisdom-amplified and
#      clamped to missing HP)
#   3. if nothing was in range, move closer and rerun
#   4. optionally break line of sight (see HIDE_AFTER_ATTACK)

import libs.logs_lib as logs_lib  # type: ignore
import libs.equipment_lib as equipment_lib  # type: ignore
import libs.decision_lib as decision_lib  # type: ignore

# Comportement de fin de tour.
#   False : DPS pur (défaut) — on reste à portée et on garde le tempo
#           offensif. C'est le choix de Kepo : build centré sur la force,
#           la protection viendra plus tard.
#   True  : comportement "shoot and hide" — on tire puis on fuit (casse la
#           ligne de vue). Utile si le build perd des PV plus vite qu'il
#           n'en inflige.
HIDE_AFTER_ATTACK = False

me = Fight.me


def turn():
    enemy = Fight.getNearestEnemy()

    if enemy == None:
        logs_lib.log("No enemy detected")
        return

    # Step 0: have a weapon in hand from the start
    equipment_lib.equip_starting_weapon(me, enemy)

    did_hit = decision_lib.attack(me, enemy)

    # If nothing was in range, move closer and rerun the calculation:
    # profitability may change once at the right distance.
    if not did_hit and me.mp > 0:
        logs_lib.log("Nothing in range, moving closer and rerunning")
        me.moveToward(enemy)
        did_hit = decision_lib.attack(me, enemy)

    # Finally, optionally try to break line of sight with the enemy.
    if HIDE_AFTER_ATTACK:
        decision_lib.hide(me, enemy)
