# analysis_lib.py
# Equipment analysis: parses weapon/chip features, computes expected damage
# (strength, crits, enemy shields), expected healing (wisdom), lifesteal
# (vol de vie) and estimated buff value.
#
# Formulas: encyclopedia fr/Force, fr/Agilite, fr/Resistance, fr/Sagesse,
# fr/Effets (snapshots locaux : docs/encyclopedia/).
#
# All libraries live in the "libs" folder of the Leek Wars drive: use
# absolute package imports (libs.xxx).

from libs.constants_lib import (
    DAMAGE_NAMES, FORCE_AMPLIFIED, SHIELDED_FLAT, SCIENCE_DAMAGE,
    INSTANT_KILL, STRENGTH_BUFFS, POWER_BUFFS, TP_BUFFS, MP_BUFFS,
    HEAL_TYPES, RAW_HEAL_TYPES, SCIENCE_AMPLIFIED, CRITICAL_FACTOR,
    RELATIVE_SHIELD_TYPES, ABSOLUTE_SHIELD_TYPES, SHIELD_AMPLIFIED,
)

# Shape of the parsed effects ("parts" dict), consumed by expected_* :
#   amp_raw    : raw sum of force-amplified damage (EFFECT_DAMAGE)
#   flat_sub   : raw sum of shielded flat damage (EFFECT_LIFE_DAMAGE, already
#                converted from "% of caster life" to a flat amount)
#   nova_raw   : raw sum of nova damage (EFFECT_NOVA_DAMAGE, science-amplified,
#                ignores shields)
#   kill       : True if the item kills instantly (EFFECT_KILL)
#   heal_raw   : raw sum of wisdom-amplified healing
#   heal_flat  : raw sum of non-amplified healing (EFFECT_RAW_HEAL)
#   buff_*     : buff amounts (already science-amplified when applicable)
#   buff_turns : duration of the buff effect (in turns, 0 if not a buff)
#   shield_relative : % of damage blocked (fr/Résistance), 0 if none
#   shield_absolute : flat damage blocked (fr/Résistance), 0 if none
#   shield_turns    : duration of the shield effect (in turns)
#   details    : human readable breakdown, used in the fight log


def defensive_list(entity, attribute_name):
    # Tolerant read of attributes absent from editor type stubs (Pyright
    # "Never" issue): getattr avoids AttributeError, None -> empty list.
    value = getattr(entity, attribute_name, [])
    if value == None:
        return []
    return value


def force_crit_multiplier(entity):
    # strength: base * (1 + strength / 100)
    # crits: expectation = agility/1000 chance of x1.3
    m = 1 + entity.strength / 100
    m = m * (1 + entity.agility / 1000 * (CRITICAL_FACTOR - 1))
    return m


def science_multiplier(entity, effect_type):
    # Some buff/heal types are amplified by science (cf. fr/Effets)
    if effect_type in SCIENCE_AMPLIFIED:
        return 1 + entity.science / 100
    return 1


def wisdom_multiplier(entity):
    # Heals are amplified by wisdom: base * (1 + wisdom / 100) (fr/Sagesse)
    return 1 + entity.wisdom / 100


def analyse_equipment(entity, obj):
    # Parse the immediate effects of a weapon/chip into damage parts, buff
    # sums and heal sums.
    #
    # Classification (fr/Effets) : c'est le TYPE de l'effet qui dit ce
    # qu'il fait ; le masque de cibles dit à QUI il s'applique.
    #   - EFFECT_DAMAGE             -> force-amplified, shields apply
    #   - EFFECT_LIFE_DAMAGE        -> % of the CASTER's life, shields apply
    #   - EFFECT_NOVA_DAMAGE        -> max HP removal, science, no shields
    #   - EFFECT_KILL               -> instant death
    #   - EFFECT_HEAL/BOOST_MAX_LIFE-> wisdom-amplified healing
    #   - EFFECT_RAW_HEAL           -> healing, NOT amplified
    #
    # Le masque seul ne suffit pas : les puces du jeu utilisent le masque
    # "31" (ENNEMIS|ALLIES|CASTER|NON_SUMMONS|SUMMONS) y compris pour les
    # soins (le bandage a le masque 31). Classer sur le masque seul faisait
    # passer une puce de soin pour une attaque : l'IA ignorait alors le
    # bandage ("Ignored (no damage, no buff, no heal, no shield)").
    amp_raw = 0       # force-amplified damage raw sum
    flat_sub = 0      # shielded flat damage (already converted to an amount)
    nova_raw = 0      # nova damage raw sum (science-amplified, no shields)
    kill = False      # instant kill effect
    heal_raw = 0      # wisdom-amplified heal raw sum
    heal_flat = 0     # non-amplified heal raw sum
    buff_strength = 0
    buff_power = 0
    buff_tp = 0
    buff_mp = 0
    buff_turns = 0    # durée du buff (en tours), 0 si ce n'est pas un buff
    shield_relative = 0
    shield_absolute = 0
    shield_turns = 0
    details = []

    for f in obj.features:
        avg = (f.minValue + f.maxValue) / 2
        # Masque de cibles de l'effet (fr/Effets).
        hits_enemies = bool(f.targets & Effect.Target.ENEMIES)
        # Les soins, boucliers et buffs ne nous concernent que si le masque
        # contient le lanceur (le masque 26 de la puce "Popcorn" ne cible
        # que les alliés : ce n'est pas une option pour nous).
        hits_caster = bool(f.targets & Effect.Target.CASTER)

        if f.type in FORCE_AMPLIFIED and hits_enemies:
            amp_raw += avg
            details.append(f"{DAMAGE_NAMES[f.type]}: {f.minValue}-"
                           f"{f.maxValue}")
        elif f.type in SHIELDED_FLAT and hits_enemies:
            # fr/Effets : "Retire des PV selon un pourcentage de la vie
            # du lanceur" -> the percentage is applied to the caster's
            # maximum life.
            amount = entity.maxLife * avg / 100
            flat_sub += amount
            details.append(f"{DAMAGE_NAMES[f.type]}: {avg}% of "
                           f"{entity.maxLife} life = {amount}")
        elif f.type in SCIENCE_DAMAGE and hits_enemies:
            nova_raw += avg
            details.append(f"{DAMAGE_NAMES[f.type]}: {f.minValue}-"
                           f"{f.maxValue}")
        elif f.type in INSTANT_KILL and hits_enemies:
            kill = True
            details.append("instant kill")
        elif f.type in DAMAGE_NAMES and hits_enemies:
            # Poison: amplified by magic and ignores shields -> not
            # modelled yet, but reported so the log stays honest.
            details.append(f"{DAMAGE_NAMES[f.type]}: {f.minValue}-"
                           f"{f.maxValue} (not modelled)")
        elif f.type in HEAL_TYPES and hits_caster:
            heal_raw += avg
            details.append(f"heal: {f.minValue}-{f.maxValue}")
        elif f.type in RAW_HEAL_TYPES and hits_caster:
            heal_flat += avg
            details.append(f"raw heal: {f.minValue}-{f.maxValue}")
        elif f.type in RELATIVE_SHIELD_TYPES + ABSOLUTE_SHIELD_TYPES \
                and hits_caster:
            # fr/Résistance : le bouclier relatif réduit un pourcentage
            # des dégâts, le bouclier absolu un montant fixe. Les effets
            # non RAW sont amplifiés par la résistance du lanceur.
            amount = avg
            if f.type in SHIELD_AMPLIFIED:
                amount = amount * (1 + entity.resistance / 100)
            if f.type in RELATIVE_SHIELD_TYPES:
                shield_relative += amount
                details.append(f"+{amount:.1f}% relative shield")
            else:
                shield_absolute += amount
                details.append(f"+{amount:.1f} absolute shield")
            if f.turns > shield_turns:
                shield_turns = f.turns
        elif f.type in (STRENGTH_BUFFS + POWER_BUFFS + TP_BUFFS + MP_BUFFS) \
                and hits_caster:
            amplified = avg * science_multiplier(entity, f.type)
            if f.type in STRENGTH_BUFFS:
                buff_strength += amplified
                details.append(f"+{amplified} strength")
            elif f.type in POWER_BUFFS:
                buff_power += amplified
                details.append(f"+{amplified} power (flat/shot)")
            elif f.type in TP_BUFFS:
                buff_tp += amplified
                details.append(f"+{amplified} TP")
            elif f.type in MP_BUFFS:
                buff_mp += amplified
                details.append(f"+{amplified} MP")
            # Durée du buff : la puce "Protéines" (+force) dure 2 tours, un
            # buff de 1 tour ne change rien à l'horizon de la décision.
            if f.turns > buff_turns:
                buff_turns = f.turns

    return {
        "amp_raw": amp_raw, "flat_sub": flat_sub, "nova_raw": nova_raw,
        "kill": kill,
        "heal_raw": heal_raw, "heal_flat": heal_flat,
        "buff_strength": buff_strength, "buff_power": buff_power,
        "buff_tp": buff_tp, "buff_mp": buff_mp, "buff_turns": buff_turns,
        "shield_relative": shield_relative,
        "shield_absolute": shield_absolute,
        "shield_turns": shield_turns,
        "details": details
    }


def shields(target):
    # Target's current shields (confirmed in game: relativeShield /
    # absoluteShield).
    return target.relativeShield, target.absoluteShield


def shielded_damage(base, target):
    # fr/Résistance : final = base * (1 - relatif / 100) - absolu
    # (le résultat ne descend jamais sous 0).
    rel, absolu = shields(target)
    final = base * (1 - rel / 100) - absolu
    if final < 0:
        final = 0
    return final


def expected_damage(o, target, attacker=None):
    # Expected damage dealt to 'target' by 'attacker' (default: Fight.me).
    #
    # The force/crit multiplier is read NOW so a strength buff cast this
    # turn benefits immediately to the following shots.
    if attacker == None:
        attacker = Fight.me
    body = shielded_damage(
        o["amp_raw"] * force_crit_multiplier(attacker) + o["flat_sub"],
        target)
    # Nova damage: amplified by science and ignores shields (fr/Résistance).
    nova = o["nova_raw"] * (1 + attacker.science / 100)
    total = body + nova
    if o["kill"]:
        # Instant execution: every remaining life point falls.
        total = target.life
    if total > target.life:
        total = target.life
    return total


def expected_heal(o, caster=None):
    # Wisdom-amplified heal (fr/Sagesse):
    # SoinsFinaux = base * (1 + wisdom / 100).
    # EFFECT_RAW_HEAL is not amplified by wisdom.
    if caster == None:
        caster = Fight.me
    return o["heal_raw"] * wisdom_multiplier(caster) + o["heal_flat"]


def expected_lifesteal(o, target, attacker=None):
    # Vol de vie (fr/Sagesse) : part of the force-dependent damage dealt
    # (after shields) is converted into life for the caster.
    #   SoinsParVolDeVie = DegatsFinaux * Sagesse / 1000
    # Only force-dependent damage gives lifesteal.
    if attacker == None:
        attacker = Fight.me
    body = shielded_damage(
        o["amp_raw"] * force_crit_multiplier(attacker), target)
    return body * attacker.wisdom / 1000


def missing_life(entity):
    return entity.maxLife - entity.life


def remaining_uses(item, me):
    # Utilisations encore possibles de l'objet ce tour.
    #
    # `Item.maxUses` est le nombre d'utilisations autorisées **par tour**
    # (le moteur refuse la suivante avec le code MAX_USES) et
    # `Entity.itemUses(item)` le compteur d'utilisations déjà faites.
    # None = pas de plafond.
    max_uses = getattr(item, "maxUses", 0)
    if max_uses <= 0:
        return None
    return max(0, max_uses - me.itemUses(item))


def in_range(obj, me, target):
    # Portée de l'objet, et ligne de vue *seulement si l'objet l'exige* :
    # certaines puces (trébuchet, étincelle, repiquage...) frappent sans
    # ligne de vue (`Item.needsLos`), d'autres (lance-flammes, Flamme...)
    # l'exigent. Sans cette distinction, l'IA gaspille une action sur un
    # tir que le moteur refuse (ligne de vue coupée).
    #
    # La distance est celle de l'API (`Cell.distance()`) : c'est la
    # métrique du moteur pour le contrôle de portée (une diagonale y
    # compte 2 cases) — mesuré en combat de test #54912618 : le fusil
    # (portée 7) est accepté à distance 7, la puce (portée 5) refusée.
    d = me.cell.distance(target.cell)
    if d < obj.minRange or d > obj.maxRange:
        return False
    if getattr(obj, "needsLos", True):
        if not me.cell.lineOfSight(target.cell):
            return False
    return True
