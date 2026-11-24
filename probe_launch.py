# @version:3.12
#
# SONDE DE DIAGNOSTIC (temporaire) : elle ne joue pas, elle *mesure*.
#
# Objectif : établir la règle réelle du moteur sur les PRÉ-REQUIS de tir :
#   - la métrique de distance (`Cell.distance()`) ;
#   - la contrainte de "tir en ligne" (`Item.launchType`) ;
#   - la portée minimale (`Item.minRange`).
#
# Protocole : à chaque tour, la sonde se place à une distance et un
# alignement connus, puis tente un tir avec l'arme LINE (machine gun) et
# avec l'arme CIRCLE (pistol) ; elle journalise le code renvoyé par le
# moteur (1 = OK, -4 = INVALID_POSITION, ...).
#
# Aucun import : la sonde n'utilise que les globaux du moteur.

#: Distances testées (métrique du moteur).
DISTANCES = [2, 3, 4]


def _cells(me, enemy):
    return me.cell.x, me.cell.y, enemy.cell.x, enemy.cell.y


def _pick(me, launch_type):
    for weapon in me.weapons:
        if getattr(weapon, "launchType", 7) == launch_type:
            return weapon
    return None


def _align(me, enemy, mode, distance):
    """Case visée : alignée (ligne/colonne) ou en diagonale de l'ennemi."""
    dx, dy = enemy.cell.x - me.cell.x, enemy.cell.y - me.cell.y
    if mode == 0:      # même ligne que l'ennemi (dx = distance)
        return enemy.cell.x + distance, enemy.cell.y
    if mode == 1:      # même colonne que l'ennemi (dy = distance)
        return enemy.cell.x, enemy.cell.y + distance
    # diagonale : |dx| = |dy| = distance / 2 (distance paire)
    step = max(1, distance // 2)
    return enemy.cell.x + step, enemy.cell.y + step


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

    turn_index = Fight.turn
    mode = turn_index % 3
    distance = DISTANCES[turn_index % len(DISTANCES)]

    # 1. se placer
    tx, ty = _align(me, enemy, mode, distance)
    me.moveToward(Field.cellFromXY(tx, ty), me.mp)

    # 2. tirer avec l'arme LINE, puis avec l'arme CIRCLE (témoin)
    _shoot(me, _pick(me, 1), enemy, "LINE")
    _shoot(me, _pick(me, 7), enemy, "CIRCLE")
