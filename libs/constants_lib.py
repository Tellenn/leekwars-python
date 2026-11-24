# constants_lib.py
# Shared game constants: immediate effect types, buff types, formulas inputs.
#
# Sources (snapshots locaux dans docs/encyclopedia/) :
#   - fr/Effets      : liste des types d'effets et règles d'amplification
#   - fr/Force       : DegatsFinaux = Base * (1 + Force / 100)
#   - fr/Agilite     : P(crit) = Agilite / 1000, multiplicateur CRITICAL_FACTOR
#   - fr/Resistance  : Final = Base * (1 - BouclierRelatif / 100) - BouclierAbsolu
#   - fr/Sagesse     : SoinsFinaux = Base * (1 + Sagesse / 100)

CRITICAL_FACTOR = 1.3   # crit damage multiplier (encyclopedia fr/Agilite)

# --- Dégâts ---
# Dégâts amplifiés par la force (et donc par le coup critique).
FORCE_AMPLIFIED = [Effect.DAMAGE]
# Dégâts plats non amplifiés, mais subissant les boucliers.
# EFFECT_LIFE_DAMAGE retire un pourcentage de la vie du lanceur.
SHIELDED_FLAT = [Effect.LIFE_DAMAGE]
# Dégâts amplifiés par la science : les dégâts nova retirent des PV *maximum*.
SCIENCE_DAMAGE = [Effect.NOVA_DAMAGE]
# Exécution instantanée : l'ennemi meurt (PV mis à 0).
INSTANT_KILL = [Effect.KILL]
# Effets qui ignorent les boucliers (fr/Résistance : poisons, renvoi de
# dégâts, dégâts nova).
SHIELD_IGNORING = [Effect.KILL, Effect.NOVA_DAMAGE, Effect.POISON]

# --- Soins ---
# Amplifiés par la sagesse (fr/Sagesse).
HEAL_TYPES = [Effect.HEAL, Effect.BOOST_MAX_LIFE]
# Non amplifiés (EFFECT_RAW_HEAL : "Non amplifié par la sagesse").
RAW_HEAL_TYPES = [Effect.RAW_HEAL]

# --- Buffs ---
STRENGTH_BUFFS = [Effect.BUFF_STRENGTH, Effect.RAW_BUFF_STRENGTH]
POWER_BUFFS = [Effect.RAW_BUFF_POWER]
TP_BUFFS = [Effect.BUFF_TP, Effect.RAW_BUFF_TP]
MP_BUFFS = [Effect.BUFF_MP, Effect.RAW_BUFF_MP]
AGILITY_BUFFS = [Effect.BUFF_AGILITY, Effect.RAW_BUFF_AGILITY]
RESISTANCE_BUFFS = [Effect.BUFF_RESISTANCE, Effect.RAW_BUFF_RESISTANCE]
WISDOM_BUFFS = [Effect.BUFF_WISDOM, Effect.RAW_BUFF_WISDOM]

# Effets amplifiés par la science (fr/Effets : "Amplifié par la science").
# Les variantes RAW_* ne sont jamais amplifiées.
SCIENCE_AMPLIFIED = [
    Effect.BUFF_STRENGTH, Effect.BUFF_AGILITY, Effect.BUFF_RESISTANCE,
    Effect.BUFF_WISDOM, Effect.BUFF_TP, Effect.BUFF_MP,
]

# Damage types eligible for logging labels
DAMAGE_NAMES = {
    Effect.DAMAGE: "damage",
    Effect.KILL: "instant kill",
    Effect.LIFE_DAMAGE: "damage (% caster life)",
    Effect.NOVA_DAMAGE: "max HP removal",
}
