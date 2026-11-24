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
    #
    # Le classement tient compte du plafond d'utilisations par tour
    # (`Item.maxUses`) : une arme lente (9 PT, 1 tir par tour) est moins
    # Throughput qu'une arme rapide, même si son ratio par tir est meilleur.
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
        cost = weapon.cost
        if cost <= 0:
            continue
        d = analysis_lib.expected_damage(parts, enemy, me)
        # 1 PT pour équiper, le reste pour les tirs.
        uses = (me.tp - 1) // cost
        left = analysis_lib.remaining_uses(weapon, me)
        if left is not None and left < uses:
            uses = left
        if uses <= 0:
            continue
        value = d * uses
        spent = 1 + cost * uses
        if value / spent > best_score:
            best_score = value / spent
            best = weapon
    if best != None:
        logs_lib.log(f"Start: equipping {best} (best damage/TP ratio, 1 TP)")
        me.setWeapon(best)
    else:
        logs_lib.log("No weapon available to equip")
