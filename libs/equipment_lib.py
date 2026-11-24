# equipment_lib.py
# Equipment management: ratio-based starter weapon choice.

# All libraries live in the "libs" folder of the Leek Wars drive: use
# absolute package imports (libs.xxx).

import libs.analysis_lib as analysis_lib
import libs.logs_lib as logs_lib


def equip_starting_weapon(me, enemy):
    # At fight start: if no weapon in hand, equip the one with the best
    # expected damage / TP ratio (equip cost is 1 TP for all, so ranking by
    # use-cost ratio is the right long-term order).
    if me.weapon != None:
        return
    if me.tp < 1:
        logs_lib.log("Not enough TP to equip a weapon at start")
        return
    best = None
    best_score = 0
    for weapon in analysis_lib.defensive_list(me, "weapons"):
        parts = analysis_lib.analyse_equipment(me, weapon)
        if parts["amp_raw"] <= 0 and parts["flat_sub"] <= 0 \
                and parts["nova_raw"] <= 0 and not parts["kill"]:
            continue  # skip weapons with no immediate damage
        d = analysis_lib.expected_damage(parts, enemy, me)
        if weapon.cost > 0 and d / weapon.cost > best_score:
            best_score = d / weapon.cost
            best = weapon
    if best != None:
        logs_lib.log(f"Start: equipping {best} (best damage/TP ratio, 1 TP)")
        me.setWeapon(best)
    else:
        logs_lib.log("No weapon available to equip")
