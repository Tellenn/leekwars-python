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
#   - shield  : survival gained, valued as the damage we could still deal
#               in the extra turns of life it buys (see shield_value)
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

#: Utiliser les puces de bouclier (défensif). La décision reste pilotée par
#: le modèle : le bouclier n'est joué que s'il évite la mort ou achète des
#: tours de survie (coûteux en TP).
USE_SHIELD_CHIPS = True

#: Valeur « infinie » : un bouclier qui évite la mort doit passer avant
#: n'importe quelle autre option.
MANDATORY = 1e9

# --- État du combat -------------------------------------------------------
# Le corps du module n'est évalué qu'une fois : ces variables persistent
# d'un tour à l'autre (cf. AGENTS.md §7).
#
# _LAST_LIFE     : nos PV à la fin de notre tour précédent.
# _INCOMING      : dégâts subis pendant le tour de l'ennemi (mesure).
_LAST_LIFE = None
_INCOMING = 0.0


def begin_turn(me):
    """Mesure les dégâts reçus depuis la fin de notre tour précédent.

    L'IA ne modélise pas les dégâts de l'ennemi : on les *observe*. Au
    début d'un tour, la différence entre nos PV de la fin du tour
    précédent et nos PV actuels est ce que l'ennemi nous a coûté.
    """
    global _INCOMING
    if _LAST_LIFE is not None:
        taken = _LAST_LIFE - me.life
        _INCOMING = taken if taken > 0 else 0.0
    return _INCOMING


def end_turn(me):
    """Mémorise nos PV à la fin du tour (base de mesure du tour suivant)."""
    global _LAST_LIFE
    _LAST_LIFE = me.life


def reset_state():
    """Oublie l'historique du combat (nouveau combat, tests)."""
    global _LAST_LIFE, _INCOMING
    _LAST_LIFE = None
    _INCOMING = 0.0


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
            "is_buff": False, "is_heal": False, "is_shield": False
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
            "is_heal": parts["heal_raw"] > 0,
            "is_shield": parts["shield_relative"] > 0
                         or parts["shield_absolute"] > 0,
        })

    usable = []
    for o in options:
        if o["has_damage"] or o["is_buff"] or o["is_heal"] or o["is_shield"]:
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


def damage_per_turn(me, usable, enemy):
    # Dégâts que l'on peut infliger dans un tour : sert à valoriser la
    # survie (un tour gagné = un tour de dégâts).
    best = best_attack_now(me, usable, enemy)
    if best == None:
        return 0.0
    per_shot = analysis_lib.expected_damage(best["parts"], enemy, me)
    cost = best["cost"] + best["switch"]
    if cost <= 0:
        return 0.0
    return per_shot * int(me.tp / cost)


def blocked_damage(incoming, relative, absolute):
    # Dégâts-stoppés par un bouclier (fr/Résistance) :
    # bloqué = dégâts * (relatif / 100) + absolu, plafonné aux dégâts.
    if incoming <= 0:
        return 0.0
    blocked = incoming * relative / 100 + absolute
    if blocked > incoming:
        blocked = incoming
    return blocked


def _ceil_div(x, y):
    # Division entière arrondie au supérieur (x / y, y > 0).
    if y <= 0:
        return 999
    k = int(x / y)
    if x > k * y:
        k += 1
    return max(k, 1)


def turns_to_death(life, incoming, blocked=0.0, duration=0):
    # Nombre de tours avant de mourir (1 = on meurt pendant ce tour).
    # `blocked` : dégâts-stoppés par tour tant que le bouclier tient.
    # `duration` : durée du bouclier en tours (0 = pas de bouclier).
    if incoming <= 0:
        return 999
    reduced = incoming - blocked
    if reduced < 0:
        reduced = 0.0
    duration = duration if duration > 0 else 1
    shielded_total = duration * reduced
    if life <= shielded_total:
        if reduced <= 0:
            return 999
        return _ceil_div(life, reduced)
    return duration + _ceil_div(life - shielded_total, incoming)


def shield_value(me, o, usable, enemy):
    # Valeur d'une puce de bouclier, sur l'échelle "valeur / TP".
    #
    # On ne modélise pas les dégâts de l'ennemi : on les mesure (voir
    # begin_turn). Le bouclier est valorisé par les tours de survie
    # qu'il achète, convertis en dégâts que l'on pourra encore infliger.
    #
    # HYPOTHÈSE : 1 tour de survie supplémentaire = 1 tour de dégâts
    # (le jeu ne donne pas de valeur absolue aux PV).
    if not USE_SHIELD_CHIPS:
        return 0.0
    incoming = _INCOMING
    if incoming <= 0:
        return 0.0
    parts = o["parts"]
    blocked = blocked_damage(incoming, parts["shield_relative"],
                              parts["shield_absolute"])
    if blocked <= 0:
        return 0.0
    duration = parts["shield_turns"] if parts["shield_turns"] > 0 else 1
    life = me.life
    death_without = turns_to_death(life, incoming)
    death_with = turns_to_death(life, incoming, blocked, duration)
    extra = death_with - death_without
    if extra <= 0:
        return 0.0
    # Mort imminente : le bouclier nous sauve, il passe avant tout.
    if life <= incoming:
        return MANDATORY
    # Si l'on tue l'ennemi avant de mourir, la survie supplémentaire ne
    # vaut rien : on garde le tempo offensif.
    per_turn = damage_per_turn(me, usable, enemy)
    if per_turn <= 0:
        return 0.0
    if _ceil_div(enemy.life, per_turn) <= death_without:
        return 0.0
    return extra * per_turn


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
    elif o["is_shield"] and not o["has_damage"]:
        value = shield_value(me, o, usable, enemy)
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


def log_identity(me, options):
    # Bloc "une fois par combat" : nom de l'IA, stats propres, équipement.
    # Écrit avant la première action pour refléter les stats de départ.
    if not logs_lib.ENABLED:
        return

    weapons = analysis_lib.defensive_list(me, "weapons")
    chips = analysis_lib.defensive_list(me, "chips")
    m = analysis_lib.force_crit_multiplier(me)
    logs_lib.log_once(
        "header",
        f"{logs_lib.AI_NAME} | strength {me.strength} "
        f"(crit {me.agility / 10}%), wisdom {me.wisdom}, science {me.science}"
        f" | damage x{m:.2f} | {len(weapons)} weapon(s), {len(chips)} chip(s)")

    items = []
    ignored = []
    for o in options:
        label = str(o["obj"])
        if o["has_damage"] or o["is_buff"] or o["is_heal"] or o["is_shield"]:
            details = "; ".join(o["parts"]["details"])
            items.append(f"{label} [{details}]" if details else label)
        else:
            ignored.append(label)
    if items:
        logs_lib.log_once("items", "Items: " + " ; ".join(items))
    if ignored:
        logs_lib.log_once("ignored",
                          "Ignored (no damage, no buff, no heal, no shield): "
                          + ", ".join(ignored))


def log_report(me, usable, options, enemy):
    # Journal de combat, à chaque tour : état du combat et rapport de
    # rentabilité, en une ligne par option.
    if not logs_lib.ENABLED:
        return

    rel, absolu = analysis_lib.shields(enemy)
    incoming = _INCOMING
    incoming_text = f" | incoming {incoming:.0f}" if incoming > 0 else ""
    logs_lib.log(f"Enemy {enemy.life} HP (shields {rel}/{absolu}) | "
                 f"me {me.life}/{me.maxLife} HP "
                 f"(missing {analysis_lib.missing_life(me)})"
                 f"{incoming_text}")

    lines = []
    for o in usable:
        total_cost = o["cost"] + o["switch"]
        if total_cost <= 0:
            continue
        if o["kind"] == "chip" and o["used"]:
            continue  # puce déjà jouée ce tour : plus une option
        score, value = option_score(me, o, usable, enemy)
        if value >= MANDATORY:
            lines.append(f"{o['obj']} (sauve la mort)/{total_cost}TP=inf")
        else:
            lines.append(f"{o['obj']} {value:.1f}/{total_cost}TP={score:.1f}")
    logs_lib.log("Profitability: " + (" ; ".join(lines) if lines else "none"))


def execute(me, o, enemy, shot):
    # Performs the chosen action. Returns True if it was a weapon attack.
    #
    # La cible de la puce est explicite : l'ennemi pour une puce à dégâts,
    # le lanceur pour une puce de soin ou de buff (sans cible, la puce
    # viserait la case du lanceur et ne toucherait personne).
    if o["kind"] == "weapon":
        if o["switch"] > 0:
            logs_lib.log(f"Switch: {o['obj']} (1 TP included in the score)")
            me.setWeapon(o["obj"])  # costs 1 TP
            o["switch"] = 0
        me.useWeapon(enemy)
        return True
    life_before = me.life
    me.useChip(o["obj"], enemy if o["has_damage"] else me)
    o["used"] = True
    if o["is_heal"]:
        logs_lib.log(f"Heal: {o['obj']} (+{me.life - life_before:.1f} HP)")
    elif o["is_shield"] and not o["has_damage"]:
        details = "; ".join(o["parts"]["details"])
        logs_lib.log(f"Shield: {o['obj']} [{details}]")
    elif o["is_buff"]:
        details = "; ".join(o["parts"]["details"])
        logs_lib.log(f"Buff: {o['obj']} [{details}]")
    else:
        logs_lib.log(f"Chip: {o['obj']} -> enemy {enemy.life} HP")
    return False


def attack(me, enemy):
    # Main loop: repeatedly pick the best-scored option (heal can win here
    # when its heal/TP ratio beats the best damage/TP ratio) and execute it.
    # Real vs expected damage is measured after each shot.
    usable, all_options = build_options(me)

    # Bloc d'identité : une fois par combat (écrit avant toute action, pour
    # que les stats affichées soient celles de départ).
    log_identity(me, all_options)

    # Build "force" : le buff de force part AVANT les tirs, il multiplie
    # tous les tirs du tour (et les suivants, si le buff dure).
    opening_buff, buff_gain = strength_buff_plan(me, usable, enemy)
    if opening_buff != None:
        logs_lib.log(f"Opening buff: {opening_buff['obj']} "
                     f"(+{opening_buff['parts']['buff_strength']:.0f} strength, "
                     f"~+{buff_gain:.0f} dmg this turn)")
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
                logs_lib.log(f"Shot #{shot} ({best['obj']}): {damage_dealt} dmg "
                             f"(expected {best_value:.1f}, gap {gap:.1f}) "
                             f"-> enemy {enemy.life} HP")
            else:
                # Abnormal case (max uses reached, cooldown...):
                # drop this option for this turn.
                logs_lib.log(f"Shot #{shot} ({best['obj']}): no damage, "
                             f"option dropped")
                best["parts"]["amp_raw"] = 0
                best["parts"]["flat_sub"] = 0
                best["parts"]["nova_raw"] = 0
                best["parts"]["kill"] = False
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
