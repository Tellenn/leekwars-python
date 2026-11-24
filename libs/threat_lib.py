# threat_lib.py
# Menace ennemie et plan de placement (« kiting »).
#
# OBJECTIF
#   Savoir à quelle portée un ennemi peut nous frapper *après* son
#   déplacement, et se placer hors de cette portée tout en restant
#   capable de le toucher au tour suivant : on garde l'initiative.
#
# MODÈLE (hypothèses explicites)
#   - la portée offensive d'un ennemi est la `maxRange` de son arme
#     équipée ; les puces offensives qu'il possède sont également prises en
#     compte (hypothèse prudente : il peut les jouer à la place de son
#     arme) ;
#   - l'ennemi dispose de `maxMP` PM par tour (les PM sont remis à zéro
#     au début de son tour) : il peut se rapprocher d'autant de cases
#     avant de tirer ;
#   - sa zone de menace est donc le disque de rayon `portée + PM` centré
#     sur sa case ; une case hors de ce disque est « sûre » ;
#   - la ligne de vue n'est pas modélisée : un obstacle coupe le tir, mais
#     l'ennemi peut se déplacer pour la rétablir (hypothèse prudente) ;
#   - je ne peux construire ce plan que si MA portée domine la sienne :
#     sinon rester hors de sa portée condamnerait le combat (je ne
#     pourrais plus jamais l'atteindre).
#
# Le modèle ne s'applique qu'en 1c1 : avec plusieurs ennemis, la zone de
# menace n'est plus un disque autour d'un point, et l'IA garde son
# comportement historique (rapprochement simple).
#
# All libraries live in the "libs" folder of the Leek Wars drive: use
# absolute package imports (libs.xxx).

import libs.analysis_lib as analysis_lib  # type: ignore

# Pyright fix: re-read the module as "Any" (see IMPORT NOTE in Kepo_solo.py)
analysis_lib = globals()["analysis_lib"]

#: Marge de sécurité : on sort de la zone de menace d'une case, pour ne
#: pas être à la limite (et pour que le tir adverse soit refusé).
SAFETY_MARGIN = 1


def is_offensive(parts):
    # L'objet inflige-t-il des dégâts ?
    return (parts["amp_raw"] > 0 or parts["flat_sub"] > 0
            or parts["nova_raw"] > 0 or parts["kill"])


def item_range(item):
    # Portée offensive maximale d'un item (0 si portée inconnue).
    return max(0, getattr(item, "maxRange", 0) or 0)


def enemy_threat(enemy):
    """Décrit ce que l'ennemi peut nous faire subir.

    Renvoie un dict :
        range  : portée offensive max de l'ennemi (arme + puces)
        weapon : portée de l'arme équipée (0 s'il n'en a pas)
        chips  : portée des puces offensives
        move   : PM dont l'ennemi dispose pour se déplacer
        reach  : rayon de menace (portée + déplacement)
    """
    weapon = getattr(enemy, "weapon", None)
    weapon_range = item_range(weapon) if weapon is not None else 0
    chip_range = 0
    for chip in analysis_lib.defensive_list(enemy, "chips"):
        parts = analysis_lib.analyse_equipment(enemy, chip)
        if is_offensive(parts):
            chip_range = max(chip_range, item_range(chip))
    move = max(0, getattr(enemy, "maxMP", 0) or 0)
    offensive = max(weapon_range, chip_range)
    return {
        "range": offensive,
        "weapon": weapon_range,
        "chips": chip_range,
        "move": move,
        "reach": offensive + move,
    }


def single_enemy():
    """Le combat est-il un 1c1 (un seul ennemi vivant) ?

    C'est la seule configuration où la zone de menace est un disque
    autour de l'ennemi.
    """
    return len(Fight.getAliveEnemies()) <= 1


def my_reach(me):
    """Portée offensive max dont je dispose (armes abordables seulement).

    Les puces offensives sont ignorées : elles ne se jouent qu'une fois par
    tour, on ne peut pas bâtir un plan de combat sur elles.
    """
    best = 0
    for weapon in analysis_lib.defensive_list(me, "weapons"):
        parts = analysis_lib.analyse_equipment(me, weapon)
        if not is_offensive(parts):
            continue
        cost = getattr(weapon, "cost", 0)
        switch = 0 if me.weapon is weapon else 1
        if cost + switch > me.tp:
            continue  # hors de budget ce tour
        best = max(best, item_range(weapon))
    return best


def in_reach(enemy, me):
    """L'ennemi peut-il nous atteindre (même après son déplacement) ?"""
    threat = enemy_threat(enemy)
    distance = me.cell.distance(enemy.cell)
    return distance <= threat["reach"]


def kite_distance(me, enemy):
    """Distance à laquelle se placer pour garder l'initiative.

    Renvoie (distance_cible, menace) ; (None, menace) si le plan n'est pas
    applicable :
      - combat à plusieurs ennemis (le modèle ne s'applique qu'en 1c1) ;
      - l'ennemi n'a rien pour me frapper (pas de menace) ;
      - ma portée ne domine pas la sienne : hors de sa portée, je ne
        pourrais plus jamais l'atteindre, on reste offensif.
    """
    threat = enemy_threat(enemy)
    if not single_enemy():
        return None, threat
    if threat["range"] <= 0:
        return None, threat
    if my_reach(me) <= threat["range"]:
        return None, threat
    # Distance minimale hors de sa zone de menace (sa portée + ses PM) :
    # on sort de sa portée de justesse, et on touche le tour d'après
    # (après son rapprochement, la distance redevient portée + 1).
    return threat["reach"] + SAFETY_MARGIN, threat


def apply_kite(me, enemy, target_distance):
    """Déplace `me` vers la distance cible (dans la limite des PM).

    Renvoie le nombre de PM dépensés.
    """
    before = me.mp
    current = me.cell.distance(enemy.cell)
    if current == target_distance:
        return 0
    if current > target_distance:
        # Trop loin : on se rapproche (sans jamais entrer dans sa zone).
        steps = min(me.mp, current - target_distance)
        me.moveToward(enemy, steps)
    else:
        # Trop près : on se replie hors de sa portée.
        steps = min(me.mp, target_distance - current)
        me.moveAwayFrom(enemy, steps)
    return before - me.mp
