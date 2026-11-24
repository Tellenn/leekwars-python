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
    #
    # Les armes qui peuvent *toucher* la cible maintenant passent devant :
    # une arme hors de portée (ou qui ne peut tirer qu'en ligne alors que
    # la cible n'est pas alignée) ne vaut rien ce tour, même si ses
    # dégâts sont supérieurs.
    if me.weapon != None:
        return
    if me.tp < 1:
        logs_lib.log("Not enough TP to equip a weapon at start")
        return
    best = None
    best_score = 0
    best_can_hit = False
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
        score = value / spent
        # Une arme qui peut toucher la cible est prioritaire (le score ne
        # sert alors qu'à départager les armes qui peuvent tirer).
        can_hit = analysis_lib.can_hit(weapon, me, enemy)
        if can_hit:
            if not best_can_hit or score > best_score:
                best = weapon
                best_score = score
                best_can_hit = True
        elif not best_can_hit and score > best_score:
            best = weapon
            best_score = score
    if best != None:
        can_hit = analysis_lib.can_hit(best, me, enemy)
        reason = "can hit" if can_hit else "best damage/TP ratio"
        logs_lib.log(f"Start: equipping {best} ({reason}, 1 TP)")
        me.setWeapon(best)
    else:
        logs_lib.log("No weapon available to equip")
