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
import libs.threat_lib as threat_lib  # type: ignore

# Pyright fix: re-read the modules as "Any" (see IMPORT NOTE in Kepo_solo.py)
analysis_lib = globals()["analysis_lib"]
logs_lib = globals()["logs_lib"]
threat_lib = globals()["threat_lib"]

#: Utiliser les puces de bouclier (défensif). La décision reste pilotée par
#: le modèle : le bouclier n'est joué que s'il évite la mort ou achète des
#: tours de survie (coûteux en TP).
USE_SHIELD_CHIPS = True

#: Se placer hors de la portée de l'ennemi quand on ne peut pas le toucher
#: (1c1) : on garde l'initiative, on touche au tour suivant, lui ne peut
#: pas nous toucher. Voir libs/threat_lib.py.
USE_KITING = True

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


def weapon_uses(me, o, budget=None):
    # Nombre de tirs possibles de cette arme sur le tour : budget de PT et
    # plafond `maxUses` (le moteur refuse la (maxUses + 1)-e utilisation).
    if budget is None:
        budget = me.tp - o["switch"]
    cost = o["cost"]
    if cost <= 0:
        return 0
    uses = budget // cost
    left = analysis_lib.remaining_uses(o["obj"], me)
    if left is not None and left < uses:
        uses = left
    return max(0, uses)


def attack_value(me, o, enemy):
    # Valeur d'une attaque sur le tour : (dégâts + vol de vie) par tir ×
    # nombre de tirs réellement possibles. Renvoie (valeur, score, tirs).
    #
    # Une arme est tirée autant de fois que le permettent le plafond
    # `maxUses` et les PT ; une puce est jouée **une fois** par tour.
    if o["kind"] == "chip":
        per_use = (analysis_lib.expected_damage(o["parts"], enemy, me)
                   + analysis_lib.expected_lifesteal(o["parts"], enemy, me))
        spent = o["cost"] + o["switch"]
        score = per_use / spent if spent > 0 else 0.0
        return per_use, score, 1
    uses = weapon_uses(me, o)
    if uses <= 0:
        return 0.0, 0.0, 0
    per_shot = (analysis_lib.expected_damage(o["parts"], enemy, me)
                + analysis_lib.expected_lifesteal(o["parts"], enemy, me))
    value = per_shot * uses
    spent = o["switch"] + o["cost"] * uses
    score = value / spent if spent > 0 else 0.0
    return value, score, uses


def option_spent(me, o):
    # TP réellement dépensés par l'option sur le tour : pour une arme,
    # l'équipement + tous les tirs que le plafond `maxUses` et les PT
    # permettent ; pour une puce, son coût (elle est jouée une fois).
    if o["kind"] == "weapon":
        uses = weapon_uses(me, o)
        return o["switch"] + o["cost"] * uses
    return o["cost"] + o["switch"]


def chip_on_cooldown(obj):
    # Une puce en cooldown ne peut pas être jouée : le moteur répond
    # `Fight.Use.INVALID_COOLDOWN`. On ne la propose donc pas (sinon l'IA
    # gaspille son ouverture de tour sur une action refusée).
    #
    # `Chip.currentCooldown` est le cooldown restant pour le lanceur ;
    # l'attribut peut manquer (anciens runtimes) -> puce considérée prête.
    cooldown = getattr(obj, "currentCooldown", 0)
    try:
        cooldown = int(cooldown)
    except (TypeError, ValueError):
        cooldown = 0
    return cooldown > 0


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
            "on_cooldown": False,
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
            "on_cooldown": chip_on_cooldown(chip),
            "has_damage": parts["amp_raw"] > 0 or parts["flat_sub"] > 0
                          or parts["nova_raw"] > 0 or parts["kill"],
            "is_buff": has_buff,
            "is_heal": parts["heal_raw"] > 0,
            "is_shield": parts["shield_relative"] > 0
                         or parts["shield_absolute"] > 0,
        })

    usable = []
    for o in options:
        if o["on_cooldown"]:
            continue  # puce en cooldown : le moteur la refuserait
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
        if o["kind"] == "chip" and o["used"]:
            continue
        if not analysis_lib.in_range(o["obj"], me, enemy):
            continue
        value, score, uses = attack_value(me, o, enemy)
        if score > best_score:
            best_score = score
            best = o
    return best


def buff_value(me, o, reference_attack, enemy):
    # Valeur estimée d'un buff de force / de puissance / de TP, sur
    # l'échelle "valeur / TP".
    #
    # Le buff de force est valorisé sur toute sa durée (voir
    # strength_buff_gain) : c'est la même estimation que celle qui décide
    # du buff d'ouverture, donc le journal reste cohérent.
    if reference_attack == None:
        return 0
    if o["parts"]["buff_strength"] > 0:
        return strength_buff_gain(me, o, reference_attack, enemy)

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
    shots = weapon_uses(me, reference_attack, budget=budget)
    if shots <= 0:
        return 0

    value = 0
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
    # HORIZON : la durée du buff (`parts["buff_turns"]`), pas seulement le
    # tour courant. Un buff qui dure plusieurs tours (puce "Protéines" :
    # +80-100 force pendant 2 tours) continue d'amplifier les tirs des
    # tours suivants : ne compter que le tour courant le rendait
    # systématiquement non rentable (il nous fait perdre un tir pour rien),
    # et l'IA n'utilisait jamais la puce.
    #
    # Le gain est plafonné par les PV restants de l'ennemi : des dégâts
    # au-delà de sa mort ne valent rien.
    attack_cost = reference["cost"] + reference["switch"]
    if attack_cost <= 0:
        return 0
    shots_without = int(me.tp / attack_cost)
    shots_with = int((me.tp - buff_option["cost"]) / attack_cost)
    # Plafond d'utilisations par tour : on ne peut pas tirer plus que
    # `maxUses` fois, même si les PT permettraient plus de tirs.
    cap = analysis_lib.remaining_uses(reference["obj"], me)
    if cap is not None:
        shots_without = min(shots_without, cap)
        shots_with = min(shots_with, cap)
    if shots_with <= 0:
        return 0  # le buff supprimerait tous les tirs
    damage = analysis_lib.expected_damage(reference["parts"], enemy, me)
    if damage <= 0:
        return 0
    boost = buff_option["parts"]["buff_strength"]
    amplified = damage * (100 + me.strength + boost) / (100 + me.strength)

    # Tour courant : le buff peut nous coûter un tir.
    value = shots_with * amplified - shots_without * damage

    # Tours suivants : le buff reste actif. Au tour suivant, l'arme est
    # déjà équipée (pas de PT d'équipement) et les PT sont pleins.
    extra_turns = buff_option["parts"]["buff_turns"] - 1
    if extra_turns > 0 and reference["cost"] > 0:
        next_shots = int(me.tp / reference["cost"])
        if cap is not None:
            next_shots = min(next_shots, cap)
        if next_shots > 0:
            extra = next_shots * extra_turns * (amplified - damage)
            remaining = enemy.life - shots_with * amplified
            if extra > remaining:
                extra = remaining
            if extra > 0:
                value += extra
    return value


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
    if o["kind"] == "chip" and o.get("on_cooldown"):
        return 0, 0  # le moteur refuserait l'action
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
        # soignent aussi le lanceur : fr/Sagesse), multipliés par le
        # nombre de tirs réellement possibles (plafond maxUses + PT).
        value, score, uses = attack_value(me, o, enemy)
        return score, value
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
    cooling = []
    for o in options:
        label = str(o["obj"])
        if o["has_damage"] or o["is_buff"] or o["is_heal"] or o["is_shield"]:
            details = "; ".join(o["parts"]["details"])
            items.append(f"{label} [{details}]" if details else label)
        elif o.get("on_cooldown"):
            cooling.append(label)
        else:
            ignored.append(label)
    if items:
        logs_lib.log_once("items", "Items: " + " ; ".join(items))
    if cooling:
        logs_lib.log_once("cooling", "On cooldown: " + ", ".join(cooling))
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
        spent = option_spent(me, o)
        if spent <= 0:
            continue
        if o["kind"] == "chip" and o["used"]:
            continue  # puce déjà jouée ce tour : plus une option
        score, value = option_score(me, o, usable, enemy)
        if value >= MANDATORY:
            lines.append(f"{o['obj']} (sauve la mort)/{spent}TP=inf")
        else:
            lines.append(f"{o['obj']} {value:.1f}/{spent}TP={score:.1f}")
    logs_lib.log("Profitability: " + (" ; ".join(lines) if lines else "none"))


def use_code_name(code):
    # Nom lisible d'un code de refus d'action (`Fight.Use.*`) : le moteur
    # renvoie un code négatif quand l'action est impossible (plafond
    # d'utilisations, PT insuffisants, ligne de vue coupée...).
    if code >= 0:
        return "OK"
    use = getattr(Fight, "Use", None)
    if use is not None:
        for name in dir(use):
            if name.startswith("_"):
                continue
            if getattr(use, name) == code:
                return name
    return f"code {code}"


def drop_option(o):
    # L'option est inutilisable pour ce tour : on neutralise ses dégâts.
    o["parts"]["amp_raw"] = 0
    o["parts"]["flat_sub"] = 0
    o["parts"]["nova_raw"] = 0
    o["parts"]["kill"] = False


def execute(me, o, enemy, shot):
    # Performs the chosen action.
    # Returns (was_attack, code) where `code` is the engine's return code
    # (negative = action refused).
    #
    # La cible de la puce est explicite : l'ennemi pour une puce à dégâts,
    # le lanceur pour une puce de soin ou de buff (sans cible, la puce
    # viserait la case du lanceur et ne toucherait personne).
    if o["kind"] == "weapon":
        if o["switch"] > 0:
            logs_lib.log(f"Switch: {o['obj']} (1 TP included in the score)")
            me.setWeapon(o["obj"])  # costs 1 TP
            o["switch"] = 0
        code = me.useWeapon(enemy)
        return True, code
    life_before = me.life
    strength_before = me.strength
    code = me.useChip(o["obj"], enemy if o["has_damage"] else me)
    o["used"] = True
    if code < 0:
        logs_lib.log(f"Chip: {o['obj']}: refused "
                     f"({use_code_name(code)})")
    elif o["is_heal"]:
        logs_lib.log(f"Heal: {o['obj']} (+{me.life - life_before:.1f} HP)")
    elif o["is_shield"] and not o["has_damage"]:
        details = "; ".join(o["parts"]["details"])
        logs_lib.log(f"Shield: {o['obj']} [{details}]")
    elif o["is_buff"]:
        details = "; ".join(o["parts"]["details"])
        # La force réelle après le buff est journalisée : sur le site, le
        # buff modifie la stat du poireau (c'est ce que l'IA relit au tour
        # suivant pour estimer ses dégâts).
        logs_lib.log(f"Buff: {o['obj']} [{details}] "
                     f"(strength {strength_before:g} -> {me.strength:g})")
    else:
        logs_lib.log(f"Chip: {o['obj']} -> enemy {enemy.life} HP")
    return False, code


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
        duration = opening_buff["parts"]["buff_turns"]
        duration_text = f"{duration} turn(s)" if duration > 0 else "instant"
        logs_lib.log(f"Opening buff: {opening_buff['obj']} "
                     f"(+{opening_buff['parts']['buff_strength']:.0f} strength, "
                     f"~+{buff_gain:.0f} dmg, {duration_text})")
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
        # Attendue AVANT le tir : les dégâts attendus (force, crits,
        # boucliers), hors vol de vie (le vol de vie est un soin, pas
        # des dégâts : le comparer aux dégâts réels fausserait l'écart).
        expected = analysis_lib.expected_damage(best["parts"], enemy, me)
        was_attack, code = execute(me, best, enemy, shot)

        if was_attack:
            damage_dealt = life_before - enemy.life
            if code < 0:
                # Action refusée par le moteur (plafond d'utilisations, PT
                # insuffisants, ligne de vue coupée, position invalide) :
                # l'option est inutilisable pour ce tour.
                logs_lib.log(f"Shot #{shot} ({best['obj']}): refused "
                             f"({use_code_name(code)}) at distance "
                             f"{me.cell.distance(enemy.cell)} "
                             f"(range {best['obj'].maxRange})")
                drop_option(best)
            elif damage_dealt > 0:
                did_hit = True
                gap = damage_dealt - expected
                logs_lib.log(f"Shot #{shot} ({best['obj']}): {damage_dealt} dmg "
                             f"(expected {expected:.1f}, gap {gap:.1f}) "
                             f"at distance {me.cell.distance(enemy.cell)} "
                             f"(range {best['obj'].maxRange}) "
                             f"-> enemy {enemy.life} HP")
            else:
                # Tir sans dégât : l'action a réussi (zone qui ne couvre
                # pas la cible, arme sans ligne de vue qui frappe dans le
                # vide...). L'option reste valable, on ne la neutralise pas.
                logs_lib.log(f"Shot #{shot} ({best['obj']}): 0 dmg "
                             f"(expected {expected:.1f})")
        if was_attack:
            shot += 1
    return did_hit


def approach(me, enemy):
    """Se positionne quand aucune attaque n'a été possible.

    Deux comportements :
      - 1c1 et ma portée domine celle de l'ennemi : on se place hors de
        sa portée (même APRÈS son déplacement), pour garder l'initiative
        (on touche au tour suivant, lui ne peut pas nous toucher) ;
      - sinon : on se rapproche simplement (comportement historique).

    Dans les deux cas le rapport est écrit : la distance visée et la
    distance obtenue (le terrain peut empêcher d'y arriver).
    """
    distance, threat = threat_lib.kite_distance(me, enemy)
    if USE_KITING and distance is not None:
        safe = threat.get("safe", distance)
        logs_lib.log(f"Kiting: enemy reach {threat['reach']} "
                     f"(range {threat['range']} + {threat['move']} MP), "
                     f"my reach {threat_lib.my_reach(me)} "
                     f"-> target distance {distance} (safe {safe})")
        before = me.cell.distance(enemy.cell)
        spent = threat_lib.apply_kite(me, enemy, distance)
        after = me.cell.distance(enemy.cell)
        logs_lib.log(f"Position: me ({me.cell.x},{me.cell.y}) enemy "
                     f"({enemy.cell.x},{enemy.cell.y}) | distance "
                     f"{before} -> {after} (target {distance}), "
                     f"{spent} MP spent")
        return
    logs_lib.log(f"Nothing in range: enemy reach {threat['reach']} "
                 f"(range {threat['range']} + {threat['move']} MP), "
                 f"my reach {threat_lib.my_reach(me)} "
                 f"-> moving closer and rerunning")
    me.moveToward(enemy)


def hide(me, enemy):
    # Break line of sight by moving away (max 5 attempts).
    if not threat_lib.in_reach(enemy, me):
        # Hors de sa portée (même après son déplacement) : la fuite ne
        # servirait qu'à perdre l'initiative (et nos PM).
        logs_lib.log("Out of enemy reach: no need to hide")
        return
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
