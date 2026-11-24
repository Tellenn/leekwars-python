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
import libs.constants_lib as constants_lib  # type: ignore

# Pyright fix: re-read the module as "Any" (see IMPORT NOTE in Kepo_solo.py)
analysis_lib = globals()["analysis_lib"]
constants_lib = globals()["constants_lib"]

#: Contraintes de visée (`Item.launchType`) : reprises de
#: `libs/constants_lib.py` (le module est relu comme "Any", on évite donc
#: un import croisé).
LAUNCH_TYPE_LINE = 1
LAUNCH_TYPE_DIAGONAL = 2
LAUNCH_TYPE_CIRCLE = 7

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


def item_min_range(item):
    # Portée offensive minimale d'un item (0 si inconnue).
    return max(0, getattr(item, "minRange", 0) or 0)


def offensive_items(entity):
    # Les objets offensifs de l'entité (arme + puces offensives).
    items = []
    weapon = getattr(entity, "weapon", None)
    if weapon is not None:
        parts = analysis_lib.analyse_equipment(entity, weapon)
        if is_offensive(parts):
            items.append(weapon)
    for chip in analysis_lib.defensive_list(entity, "chips"):
        parts = analysis_lib.analyse_equipment(entity, chip)
        if is_offensive(parts):
            items.append(chip)
    return items


def hits_per_turn(entity):
    """Nombre de coups que l'entité peut nous infliger par tour.

    Une arme peut servir plusieurs fois par tour (`Item.maxUses`) et chaque
    usage peut contenir plusieurs effets de dégâts (la machine gun : 3
    projectiles par tir) : le nombre de coups est le produit des deux.

    C'est ce nombre qui rend le **bouclier absolu** model'sable : il bloque
    un montant fixe *par coup* (fr/Résistance), pas par tour.

    Sans arme connue (ou sans plafond d'usages), on suppose un coup par
    tour : c'est l'hypothèse prudente (on sous-estime la protection).
    """
    weapon = getattr(entity, "weapon", None)
    if weapon is None:
        return 1
    uses = analysis_lib.max_uses(weapon)
    if uses is None:
        uses = 1  # pas de plafond : on ne compte qu'un usage
    shots = 0
    for feature in getattr(weapon, "features", []):
        if feature.type in constants_lib.FORCE_AMPLIFIED:
            shots += 1
    if shots <= 0:
        shots = 1
    return max(1, uses * shots)


def enemy_threat(enemy):
    """Décrit ce que l'ennemi peut nous faire subir.

    Renvoie un dict :
        range  : portée offensive max de l'ennemi (arme + puces)
        weapon : portée de l'arme équipée (0 s'il n'en a pas)
        chips  : portée des puces offensives
        move   : PM dont l'ennemi dispose pour se déplacer
        reach  : rayon de menace (portée + déplacement)
        min    : distance minimale à laquelle l'ennemi peut nous toucher
                 (la portée minimale de son arme : le fusil, par exemple,
                 ne tire pas à moins de 7 cases)
        windows : fenêtres de menace (min, max + déplacement) : on peut
                  nous toucher si on est dans l'une d'elles
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
    windows = []
    for item in offensive_items(enemy):
        windows.append((item_min_range(item), item_range(item) + move))
    return {
        "range": offensive,
        "weapon": weapon_range,
        "chips": chip_range,
        "move": move,
        "reach": offensive + move,
        "min": min([w[0] for w in windows]) if windows else 0,
        "windows": windows,
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


def my_windows(me):
    """Fenêtres de portée des armes offensives abordables : [(min, max)].

    Une arme ne peut toucher la cible que dans sa fenêtre : le fusil, par
    exemple, ne tire qu'entre 7 et 9 cases (portée minimale). Ce sont ces
    fenêtres qui décident de la distance à laquelle on se place.
    """
    windows = []
    for weapon in analysis_lib.defensive_list(me, "weapons"):
        parts = analysis_lib.analyse_equipment(me, weapon)
        if not is_offensive(parts):
            continue
        cost = getattr(weapon, "cost", 0)
        switch = 0 if me.weapon is weapon else 1
        if cost + switch > me.tp:
            continue  # hors de budget ce tour
        windows.append((item_min_range(weapon), item_range(weapon)))
    return windows


def firing_distance(windows, wanted):
    """La distance à laquelle se placer pour pouvoir réellement tirer.

    On cherche une distance qui appartienne à une fenêtre de tir et qui
    soit la plus proche de `wanted` (la distance « idéale », en général
    juste hors de la portée de l'ennemi). Si aucune distance n'est
    acceptable, on prend le bord de fenêtre le plus proche : mieux vaut
    tirer de trop près ou de trop loin que pas tirer du tout.
    """
    if not windows:
        return None
    for lo, hi in windows:
        if lo <= wanted <= hi:
            return wanted
    best = None
    for lo, hi in windows:
        for candidate in (lo, hi):
            if best is None or abs(candidate - wanted) < abs(best - wanted):
                best = candidate
    return best


def _sign(value):
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def firing_cell(me, enemy, weapon, distance=None):
    """Case (x, y) depuis laquelle on peut toucher l'ennemi avec `weapon`.

    Elle est :
      - à `distance` cases de l'ennemi (métrique de portée, |dx| + |dy|),
        distance recadrée dans la fenêtre de tir de l'arme ;
      - alignée selon la contrainte de visée de l'arme (`launchType`) :
        sur la rangée ou la colonne de l'ennemi pour une arme « en
        ligne », en diagonale pour une arme « en diagonale » ;
      - du côté où nous sommes déjà (on ne traverse pas l'ennemi).
    """
    if weapon is None:
        return None
    if distance is None:
        distance = me.cell.distance(enemy.cell)
    low = max(0, getattr(weapon, "minRange", 0) or 0)
    high = max(0, getattr(weapon, "maxRange", 0) or 0)
    if distance < low:
        distance = low
    elif distance > high:
        distance = high
    dir_x = _sign(me.cell.x - enemy.cell.x)
    dir_y = _sign(me.cell.y - enemy.cell.y)
    launch = getattr(weapon, "launchType", LAUNCH_TYPE_CIRCLE)
    if launch == LAUNCH_TYPE_DIAGONAL:
        # « en diagonale » : |dx| = |dy|, donc une distance paire.
        step = distance // 2
        return (enemy.cell.x + dir_x * step, enemy.cell.y + dir_y * step)
    # La distance de portée est |dx| + |dy| : on la met sur un seul axe,
    # ce qui place la case sur la rangée ou la colonne de l'ennemi (donc
    # alignée pour une arme « en ligne »).
    candidates = []
    if dir_x != 0:
        candidates.append((enemy.cell.x + dir_x * distance, enemy.cell.y))
    if dir_y != 0:
        candidates.append((enemy.cell.x, enemy.cell.y + dir_y * distance))
    if not candidates:
        return (enemy.cell.x, enemy.cell.y)
    best = candidates[0]
    best_travel = abs(best[0] - me.cell.x) + abs(best[1] - me.cell.y)
    for candidate in candidates[1:]:
        travel = abs(candidate[0] - me.cell.x) + abs(candidate[1] - me.cell.y)
        if travel < best_travel:
            best = candidate
            best_travel = travel
    return best


def in_reach(enemy, me):
    """L'ennemi peut-il nous atteindre (même après son déplacement) ?

    Rayon de menace : sa portée + ses PM (hypothèse conservatrice : le
    déplacement est compté en cases de portée).
    """
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

    La distance visée est la plus proche possible tout en restant hors de
    la zone de menace — **sans jamais dépasser notre propre portée** : se
    parquer hors de portée nous ferait attendre un adversaire immobile
    jusqu'au match nul (aucun des deux ne peut plus tirer). Quand la zone
    sûre est hors de notre portée, on engage donc (tir + échange) plutôt
    que de camper.
    """
    threat = enemy_threat(enemy)
    if not single_enemy():
        return None, threat
    if threat["range"] <= 0:
        return None, threat
    reach = my_reach(me)
    if reach <= threat["range"]:
        return None, threat
    # Distance minimale hors de sa zone de menace (sa portée + ses PM) :
    # on sort de sa portée de justesse, et on touche le tour d'après
    # (après son rapprochement, la distance redevient portée + 1).
    safe = threat["reach"] + SAFETY_MARGIN
    threat["safe"] = safe
    # ... mais on ne se parque jamais hors de notre propre portée : sinon
    # on ne tire plus et le combat finit en match nul si l'adversaire ne
    # bouge pas. Dans ce cas, on engage.
    # La distance visée doit en plus appartenir à une fenêtre de tir réelle
    # (une arme à portée minimale ne tire pas de près).
    wanted = min(safe, reach)
    distance = firing_distance(my_windows(me), wanted)
    if distance is None:
        return wanted, threat
    return distance, threat


def apply_kite(me, enemy, target_distance, weapon=None):
    """Déplace `me` vers la case de tir (dans la limite des PM).

    On vise la case de tir (à `target_distance` de l'ennemi, alignée
    selon l'arme) plutôt que l'ennemi lui-même : la distance de portée
    (|dx| + |dy|) n'est pas la distance de déplacement, et un pas en
    diagonale la fait varier de 2.

    Renvoie le nombre de PM dépensés.
    """
    before = me.mp
    current = me.cell.distance(enemy.cell)
    if current == target_distance:
        return 0
    target = firing_cell(me, enemy, weapon, target_distance)
    cell = None
    if target is not None:
        try:
            cell = Field.cellFromXY(target[0], target[1])
        except Exception:
            cell = None
    if cell is not None:
        me.moveToward(cell, me.mp)
        return before - me.mp
    # Repli : on se rapproche ou on s'éloigne de l'ennemi.
    if current > target_distance:
        steps = min(me.mp, current - target_distance)
        me.moveToward(enemy, steps)
    else:
        steps = min(me.mp, target_distance - current)
        me.moveAwayFrom(enemy, steps)
    return before - me.mp
