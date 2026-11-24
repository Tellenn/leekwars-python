# decision_lib.py
# Decision engine: builds the list of usable options (attacks, buffs, heals),
# scores them per TP spent and executes the plan.
#
# Priorities per iteration (all compared on the same "value / TP" scale):
#   - attack  : expected damage / TP (strength, crits, enemy shields)
#   - heal    : min(expected heal, missing HP) / TP  -- wisdom-amplified
#               (a heal beats an attack only if its TP ratio is higher,
#                exactly as requested; overheal counts for 0)
#   - buff    : estimated extra damage it enables / TP
#
# All libraries live in the "libs" folder of the Leek Wars drive: use
# absolute package imports (libs.xxx).
#
# DATA SHAPE REMINDER: analysis functions (expected_damage, expected_heal,
# expected_lifesteal) take the PARSED EFFECTS dict (option["parts"]), never
# the full option, and the caster as their last argument.

import libs.analysis_lib as analysis_lib  # type: ignore
import libs.logs_lib as logs_lib  # type: ignore

# Pyright fix: re-read the modules as "Any" (see IMPORT NOTE in Kepo_solo.py)
analysis_lib = globals()["analysis_lib"]
logs_lib = globals()["logs_lib"]


def build_options(me):
    # One option = dict with "kind", "obj", "cost", "switch" (+1 TP to equip
    # a weapon not held, 0 for a chip), parsed "parts" and flags:
    # has_damage / is_buff / is_heal / used.
    options = []
    for weapon in analysis_lib.defensive_list(me, "weapons"):
        sw = 0
        if me.weapon != weapon:
            sw = 1
        parts = analysis_lib.analyse_equipment(me, weapon)
        options.append({
            "kind": "weapon", "obj": weapon, "cost": weapon.cost,
            "switch": sw, "parts": parts, "used": False,
            "has_damage": parts["amp_raw"] > 0 or parts["flat_sub"] > 0
                          or parts["nova_raw"] > 0 or parts["kill"],
            "is_buff": False, "is_heal": False
        })
    for chip in analysis_lib.defensive_list(me, "chips"):
        parts = analysis_lib.analyse_equipment(me, chip)
        has_buff = (parts["buff_strength"] > 0 or parts["buff_power"] > 0
                    or parts["buff_tp"] > 0)
        options.append({
            "kind": "chip", "obj": chip, "cost": chip.cost, "switch": 0,
            "parts": parts, "used": False,
            "has_damage": parts["amp_raw"] > 0 or parts["flat_sub"] > 0
                          or parts["nova_raw"] > 0 or parts["kill"],
            "is_buff": has_buff,
            "is_heal": parts["heal_raw"] > 0
        })

    usable = []
    for o in options:
        if o["has_damage"] or o["is_buff"] or o["is_heal"]:
            usable.append(o)
    return usable, options


def best_attack_now(me, usable, enemy):
    # Best attackable option right now, used as the reference to estimate
    # the value of buffs. Returns None if no attack is usable.
    best = None
    best_score = 0
    for o in usable:
        if not o["has_damage"]:
            continue
        total_cost = o["cost"] + o["switch"]
        if total_cost <= 0 or me.tp < total_cost:
            continue
        if o["kind"] == "chip" and o["used"]:
            continue
        if not analysis_lib.in_range(o["obj"], me, enemy):
            continue
        exp = analysis_lib.expected_damage(o["parts"], enemy, me)
        if exp / total_cost > best_score:
            best_score = exp / total_cost
            best = o
    return best


def buff_value(me, o, reference_attack, enemy):
    # Estimated extra damage granted by a buff chip for the REST OF THE TURN
    # (horizon approximation: longer-lasting buffs are undervalued).
    if reference_attack == None:
        return 0
    ref = reference_attack["parts"]
    ref_gross = ref["amp_raw"] * analysis_lib.force_crit_multiplier(me) \
        + ref["flat_sub"]
    ref_net = analysis_lib.expected_damage(ref, enemy, me)
    shield_factor = 1
    if ref_gross > 0:
        shield_factor = ref_net / ref_gross
        if shield_factor < 0:
            shield_factor = 0

    budget = me.tp - o["cost"] - reference_attack["switch"]
    if budget < 0 or reference_attack["cost"] <= 0:
        return 0
    shots = int(budget / reference_attack["cost"])

    value = 0
    if o["parts"]["buff_strength"] > 0:
        gain_per_shot = (analysis_lib.expected_damage(ref, enemy, me)
                         * o["parts"]["buff_strength"] / (100 + me.strength))
        value += shots * gain_per_shot
    if o["parts"]["buff_power"] > 0:
        # ASSUMPTION: power adds flat damage per shot (to be confirmed in game)
        value += shots * o["parts"]["buff_power"] * shield_factor
    if o["parts"]["buff_tp"] > 0:
        extra_shots = int(o["parts"]["buff_tp"] / reference_attack["cost"])
        value += extra_shots * analysis_lib.expected_damage(ref, enemy, me)
    return value


def heal_value(me, o):
    # Wisdom-amplified heal (fr/Sagesse), clamped to the missing HP:
    # overhealing has zero value at decision time.
    heal = analysis_lib.expected_heal(o["parts"], me)
    missing = analysis_lib.missing_life(me)
    if heal > missing:
        return missing
    return heal


def strength_buff_gain(me, buff_option, reference, enemy):
    # Gain de dégâts apporté par un buff de force lancé AVANT les tirs.
    #
    # Sans buff :   shots_without * dégâts_par_tir
    # Avec buff :   shots_with    * dégâts_par_tir_amplifié
    #
    # Le buff consomme des PT : il peut repousser un tir. Il ne vaut le coup
    # que si le total avec buff dépasse le total sans buff.
    #
    # Horizon : les tirs du tour uniquement. Un buff de force dure souvent
    # plusieurs tours, donc la vraie valeur est plus haute : la règle est
    # conservatrice (elle peut refuser un buff qui serait rentable sur la
    # durée). À revoir si le build devient 'force + buff permanent'.
    attack_cost = reference["cost"] + reference["switch"]
    if attack_cost <= 0:
        return 0
    shots_without = int(me.tp / attack_cost)
    shots_with = int((me.tp - buff_option["cost"]) / attack_cost)
    if shots_with <= 0:
        return 0  # le buff supprimerait tous les tirs
    damage = analysis_lib.expected_damage(reference["parts"], enemy, me)
    if damage <= 0:
        return 0
    boost = buff_option["parts"]["buff_strength"]
    amplified = damage * (100 + me.strength + boost) / (100 + me.strength)
    return shots_with * amplified - shots_without * damage


def strength_buff_plan(me, usable, enemy):
    # Sur un build "force", le buff de force doit partir AVANT les tirs :
    # il multiplie tous les tirs suivants du tour.
    #
    # Renvoie (option de buff, gain de dégâts estimé) ou (None, 0).
    reference = best_attack_now(me, usable, enemy)
    if reference == None:
        return None, 0
    best = None
    best_gain = 0
    for o in usable:
        if o["kind"] != "chip" or o["used"]:
            continue
        if not o["is_buff"] or o["parts"]["buff_strength"] <= 0:
            continue
        if o["cost"] > me.tp:
            continue
        gain = strength_buff_gain(me, o, reference, enemy)
        if gain > best_gain:
            best_gain = gain
            best = o
    return best, best_gain


def option_score(me, o, usable, enemy):
    # Common scale: value / TP (equip cost included).
    total_cost = o["cost"] + o["switch"]
    if total_cost <= 0 or me.tp < total_cost:
        return 0, 0
    if o["kind"] == "chip" and o["used"]:
        return 0, 0
    if o["is_heal"]:
        value = heal_value(me, o)
    elif o["is_buff"]:
        value = buff_value(me, o, best_attack_now(me, usable, enemy), enemy)
    else:
        if not analysis_lib.in_range(o["obj"], me, enemy):
            return 0, 0
        # Dégâts attendus + vol de vie (les dégâts dépendant de la force
        # soignent aussi le lanceur : fr/Sagesse).
        value = (analysis_lib.expected_damage(o["parts"], enemy, me)
                 + analysis_lib.expected_lifesteal(o["parts"], enemy, me))
    return value / total_cost, value


def log_report(me, usable, options, enemy):
    if not logs_lib.ENABLED:
        return
    rel, absolu = analysis_lib.shields(enemy)
    m = analysis_lib.force_crit_multiplier(me)
    logs_lib.log(f"Strength {me.strength}, agility {me.agility} "
                 f"(crit: {me.agility / 10}% chance of x1.3), "
                 f"wisdom {me.wisdom}, science {me.science}")
    logs_lib.log(f"Multiplier on classic damage: x{m}")
    logs_lib.log(f"Enemy current shields: relative {rel}, absolute {absolu}")
    logs_lib.log(f"My missing HP: {analysis_lib.missing_life(me)}")
    logs_lib.log(f"Equipment read: "
                 f"{len(analysis_lib.defensive_list(me, 'weapons'))} weapon(s), "
                 f"{len(analysis_lib.defensive_list(me, 'chips'))} chip(s)")
    logs_lib.log("=== Profitability report (value / TP, equip cost included) ===")
    for o in usable:
        total_cost = o["cost"] + o["switch"]
        if total_cost <= 0:
            continue
        score, value = option_score(me, o, usable, enemy)
        tag = "heal" if o["is_heal"] else ("buff" if o["is_buff"] else o["kind"])
        logs_lib.log(f"{tag} {o['obj']} : value {value} for {total_cost} TP "
                     f"({o['cost']} use + {o['switch']} to equip) "
                     f"=> score {score} [{'; '.join(o['parts']['details'])}]")
    ignored = []
    for o in options:
        if not o["has_damage"] and not o["is_buff"] and not o["is_heal"]:
            ignored.append(str(o["obj"]))
    if len(ignored) > 0:
        logs_lib.log("Equipment ignored (no immediate damage, no offensive "
                     "buff, no heal): " + ", ".join(ignored))


def execute(me, o, enemy, shot):
    # Performs the chosen action. Returns True if it was a weapon attack.
    #
    # La cible de la puce est explicite : l'ennemi pour une puce à dégâts,
    # le lanceur pour une puce de soin ou de buff (sans cible, la puce
    # viserait la case du lanceur et ne toucherait personne).
    if o["kind"] == "weapon":
        if o["switch"] > 0:
            logs_lib.log(f"Switching weapon to {o['obj']} "
                         f"(1 TP included in the score)")
            me.setWeapon(o["obj"])  # costs 1 TP
            o["switch"] = 0
        logs_lib.log(f"Shot #{shot} with {o['obj']} (enemy HP before: "
                     f"{enemy.life})")
        me.useWeapon(enemy)
        return True
    me.useChip(o["obj"], enemy if o["has_damage"] else me)
    o["used"] = True
    if o["is_heal"]:
        logs_lib.log(f"Casting heal chip {o['obj']} (value "
                     f"{heal_value(me, o)})")
    elif o["is_buff"]:
        logs_lib.log(f"Casting buff chip {o['obj']}")
    else:
        logs_lib.log(f"Casting chip {o['obj']} (enemy HP before: "
                     f"{enemy.life})")
    return False


def attack(me, enemy):
    # Main loop: repeatedly pick the best-scored option (heal can win here
    # when its heal/TP ratio beats the best damage/TP ratio) and execute it.
    # Real vs expected damage is measured after each shot.
    usable, all_options = build_options(me)

    # Build "force" : le buff de force part AVANT les tirs, il multiplie
    # tous les tirs du tour (et les suivants, si le buff dure).
    opening_buff, buff_gain = strength_buff_plan(me, usable, enemy)
    if opening_buff != None:
        logs_lib.log(f"Opening with the strength buff {opening_buff['obj']} "
                     f"(+{opening_buff['parts']['buff_strength']} strength, "
                     f"estimated gain {buff_gain} damage this turn)")
        execute(me, opening_buff, enemy, 0)

    log_report(me, usable, all_options, enemy)
    did_hit = False
    shot = 0
    while enemy.life > 0:
        best = None
        best_score = 0
        best_value = 0
        for o in usable:
            score, value = option_score(me, o, usable, enemy)
            if score > best_score:
                best_score = score
                best = o
                best_value = value
        if best == None:
            logs_lib.log(f"No usable option anymore (TP left: {me.tp})")
            break

        life_before = enemy.life
        was_attack = execute(me, best, enemy, shot)

        if was_attack:
            damage_dealt = life_before - enemy.life
            if damage_dealt > 0:
                did_hit = True
                gap = damage_dealt - best_value
                logs_lib.log(f"=> {damage_dealt} real damage (expected: "
                             f"{best_value}, gap {gap}, enemy HP: "
                             f"{enemy.life})")
            else:
                # Abnormal case (max uses reached, cooldown...):
                # drop this option for this turn.
                logs_lib.log(f"=> 0 real damage, option {best['obj']} dropped")
                best["parts"]["amp_raw"] = 0
                best["parts"]["flat_sub"] = 0
                best["parts"]["nova_raw"] = 0
                best["parts"]["kill"] = False
        else:
            logs_lib.log(f"=> action done (enemy HP: {enemy.life}, "
                         f"my HP: {me.life})")
        shot += 1
    return did_hit


def hide(me, enemy):
    # Break line of sight by moving away (max 5 attempts).
    tries = 0
    while tries < 5:
        if not me.cell.lineOfSight(enemy.cell):
            logs_lib.log(f"Hidden after {tries} move(s), line of sight broken")
            break
        if me.mp <= 0:
            logs_lib.log(f"Not enough MP to break line of sight ({tries} "
                         f"move(s))")
            break
        me.moveAwayFrom(enemy, me.mp)
        tries += 1
