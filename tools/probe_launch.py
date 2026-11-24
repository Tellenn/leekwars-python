# @version:3.12
#
# SONDE DE DIAGNOSTIC : elle ne joue pas, elle *mesure*.
#
# Objectif : établir la règle réelle du moteur sur les PRÉ-REQUIS de tir :
#   - la métrique de distance (`Cell.distance()`) ;
#   - la contrainte de "tir en ligne" (`Item.launchType`) ;
#   - la portée minimale (`Item.minRange`).
#
# Utilisation : ce fichier n'est pas une IA de jeu, c'est une sonde. Pour
# la lancer sur le site, on la copie temporairement à la place de
# `Kepo_solo.py` (le moteur n'exécute que le point d'entrée du dossier de
# l'IA), on pousse, on lance un combat de test, on lit le journal, puis on
# restaure `Kepo_solo.py`.
#
# Protocole : à chaque tour, la sonde se place sur une géométrie connue
# (même ligne / même colonne / diagonale exacte) par rapport à l'ennemi,
# puis tente un tir avec l'arme LINE (machine gun) ; elle journalise le
# code renvoyé par le moteur (1 = OK, -4 = INVALID_POSITION, ...).
#
# Résultats obtenus (à l'époque) :
#   - `Cell.distance()` = |dx| + |dy| (le mock a été aligné dessus) ;
#   - une arme LINE refuse une cible en diagonale exacte (-4) ;
#   - une arme LINE touche une cible sur la même ligne ou la même colonne.
#
# Aucun import : la sonde n'utilise que les globaux du moteur.

#: Géométries testées, dans l'ordre : (dx, dy) visés par rapport à l'ennemi.
GEOMETRIES = [
    ("ROW", 2, 0),      # même ligne que l'ennemi
    ("COL", 0, 2),      # même colonne
    ("DIAG", 2, 2),     # diagonale exacte
]


def _pick(me, launch_type):
    for weapon in me.weapons:
        if getattr(weapon, "launchType", 7) == launch_type:
            return weapon
    return None


def _shoot(me, weapon, enemy, label):
    if weapon is None:
        Debug.log(f"probe: {label}: no weapon")
        return
    if me.weapon is not weapon:
        me.setWeapon(weapon)
    code = me.useWeapon(enemy)
    Debug.log(f"probe: {label} code={code} tp={me.tp} "
              f"dx={enemy.cell.x - me.cell.x} dy={enemy.cell.y - me.cell.y} "
              f"dist={me.cell.distance(enemy.cell)}")


def turn():
    me = Fight.me
    enemy = Fight.getNearestEnemy()
    if enemy is None:
        Debug.log("probe: no enemy")
        return

    name, dx, dy = GEOMETRIES[Fight.turn % len(GEOMETRIES)]
    # Case visée : à (dx, dy) de l'ennemi.
    tx = enemy.cell.x + dx
    ty = enemy.cell.y + dy
    me.moveToward(Field.cellFromXY(tx, ty), me.mp)

    got_dx = enemy.cell.x - me.cell.x
    got_dy = enemy.cell.y - me.cell.y
    if got_dx != dx or got_dy != dy:
        Debug.log(f"probe: {name} not reached (dx={got_dx} dy={got_dy})")
        return
    _shoot(me, _pick(me, 1), enemy, f"LINE/{name}")
