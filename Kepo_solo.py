# @version:3.12
#
# SONDE DE DIAGNOSTIC : elle ne joue pas, elle *mesure*.
#
# Objectif : déterminer la MÉTRIQUE de portée du moteur.
#
# `Cell.distance()` vaut |dx| + |dy| (mesuré au combat #54913368), mais
# le moteur a accepté un tir de pistolet (portée 7) à une distance de 9
# (combat #54913431) : le contrôle de portée du moteur utilise donc une
# autre métrique.
#
# Pour trancher, la sonde se place en DIAGONALE de l'ennemi (dx = dy ≈ 5) :
#   - chebyshev = 5  -> accepté si le moteur compte les cases ;
#   - manhattan = 10 -> refusé si le moteur compte |dx| + |dy| ;
#   - euclidien = 7,07 -> refusé si le moteur compte la distance réelle.
# Elle journalise (dx, dy) et le code du moteur à chaque tir.
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

    # Diagonale de 5 cases : on alterne le sens pour trouver une vue
    # dégagée.
    index = Fight.turn
    step = 4 + (index % 3)  # 4..6
    sign = 1 if (index // 3) % 2 == 0 else -1
    cell = Field.cellFromXY(enemy.cell.x + step * sign,
                             enemy.cell.y + step * sign)
    if cell is not None:
        me.moveToward(cell, me.mp)

    code = me.useWeapon(enemy)
    dx = enemy.cell.x - me.cell.x
    dy = enemy.cell.y - me.cell.y
    Debug.log(f"probe: code={code} dx={dx} dy={dy} "
              f"cheb={max(abs(dx), abs(dy))} man={abs(dx) + abs(dy)} "
              f"d2={dx * dx + dy * dy} range={pistol.maxRange} "
              f"r2={pistol.maxRange * pistol.maxRange} "
              f"los={me.cell.lineOfSight(enemy.cell)}")
