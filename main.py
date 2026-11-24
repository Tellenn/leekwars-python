# @version:3.12
#
# AI "Shoot and hide" - main file (entry point).
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
# the official stubs is available in stubs/leekwars.pyi for local checking.
#
# Decision flow per turn:
#   0. equip a weapon if none held (best damage/TP ratio)
#   1. find nearest enemy
#   2. loop: pick the best value/TP option among attacks, buffs and HEALS,
#      execute it (a heal wins exactly when its heal/TP ratio beats the
#      best damage/TP ratio, as specified; heal is wisdom-amplified and
#      clamped to missing HP)
#   3. if nothing was in range, move closer and rerun
#   4. finally try to break line of sight with the enemy

import libs.logs_lib as logs_lib  # type: ignore
import libs.equipment_lib as equipment_lib  # type: ignore
import libs.decision_lib as decision_lib  # type: ignore

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

    # Whatever happens, then try to break line of sight
    decision_lib.hide(me, enemy)
