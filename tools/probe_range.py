# @version:3.12
#
# SONDE DE DIAGNOSTIC : elle ne joue pas, elle *mesure*.
#
# Objectif : déterminer la MÉTRIQUE de portée du moteur (chebyshev ?
# manhattan ? euclidienne ?).
#
# `Cell.distance()` vaut |dx| + |dy| (mesuré au combat #54913368), mais
# le moteur a accepté un tir de pistolet (portée 7) à une distance de 9
# (combat #54913431) : le contrôle de portée du moteur utilise donc une
# autre métrique.
#
# Pour trancher sans confondre avec la ligne de vue, la sonde se place en
# DIAGONALE de l'ennemi (dx = dy ≈ 4-6) et ne tire que si :
#   - toutes les cases du rectangle entre les deux sont libres
#     (donc AUCUNE ligne de vue possible n'est coupée) ;
#   - `Cell.lineOfSight()` confirme la vue.
# Alors, pour une portée de 7 :
#   - chebyshev = 5   -> accepté si le moteur compte les cases ;
#   - euclidien = 7,07 -> refusé si le moteur compte la distance réelle ;
#   - manhattan = 10  -> refusé si le moteur compte |dx| + |dy|.
#
# La sonde ne sert qu'à la mesure : elle est copiée temporairement à la
# place de `Kepo_solo.py`, poussée, puis le journal du combat de test est
# lu (même principe que tools/probe_launch.py).
#
# Aucun import : la sonde n'utilise que les globaux du moteur.


def _pick_pistol(me):
    """L'arme « circle » de plus grande portée (aucune contrainte de visée)."""
    best = None
    for weapon in me.weapons:
        if getattr(weapon, "launchType", 7) != 7:
            continue
        if best is None or weapon.maxRange > best.maxRange:
            best = weapon
    return best


def _rectangle_is_clear(me, enemy):
    """Aucune case du rectangle entre les deux entités n'est un obstacle."""
    obstacles = Field.getObstacles()
    x0, x1 = me.cell.x, enemy.cell.x
    y0, y1 = me.cell.y, enemy.cell.y
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0
    for cell in obstacles:
        if x0 <= cell.x <= x1 and y0 <= cell.y <= y1:
            return False
    return True


def turn():
    me = Fight.me
    enemy = Fight.getNearestEnemy()
    if enemy is None:
        Debug.log("probe: no enemy")
        return

    pistol = _pick_pistol(me)
    if pistol is None:
        Debug.log("probe: no circle weapon")
        return
    if me.weapon is not pistol:
        me.setWeapon(pistol)

    # On vise une case en diagonale de l'ennemi (4 à 6 cases).
    index = Fight.turn
    step = 5 + (index % 3)  # 5..7
    sign = 1 if (index // 3) % 2 == 0 else -1
    cell = Field.cellFromXY(enemy.cell.x + step * sign,
                             enemy.cell.y + step * sign)
    if cell is not None:
        me.moveToward(cell, me.mp)

    dx = enemy.cell.x - me.cell.x
    dy = enemy.cell.y - me.cell.y
    clear = _rectangle_is_clear(me, enemy)
    los = me.cell.lineOfSight(enemy.cell)
    code = me.useWeapon(enemy)
    Debug.log(f"probe: code={code} dx={dx} dy={dy} "
              f"cheb={max(abs(dx), abs(dy))} man={abs(dx) + abs(dy)} "
              f"d2={dx * dx + dy * dy} range={pistol.maxRange} "
              f"r2={pistol.maxRange * pistol.maxRange} "
              f"los={los} clear={clear}")
