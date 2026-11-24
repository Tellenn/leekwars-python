# @version:3.12
#
# SONDE DE DIAGNOSTIC : elle ne joue pas, elle *mesure*.
#
# Objectif : déterminer la MÉTRIQUE de portée du moteur.
#
# `Cell.distance()` vaut |dx| + |dy| (mesuré au combat #54913368), mais
# le moteur a accepté un tir de pistolet (portée 7) à une distance de 9
# (combat #54913431) : le contrôle de portée du moteur utilise donc une
# autre métrique. On tire à chaque tour et on journalise (dx, dy) et le
# code du moteur : les refus tracent la frontière.
#
# La sonde ne sert qu'à la mesure : elle est copiée temporairement à la
# place de `Kepo_solo.py`, poussée, puis le journal du combat de test est
# lu (voir tools/probe_launch.py pour le même principe).
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

    # On se place à une distance connue : une fois sur la rangée de
    # l'ennemi, une fois en diagonale (les deux splits de la distance).
    index = Fight.turn
    step = 4 + (index % 4)  # 4..7
    if index % 2 == 0:
        target_x = enemy.cell.x + step
        target_y = enemy.cell.y
    else:
        target_x = enemy.cell.x + step
        target_y = enemy.cell.y + step
    cell = Field.cellFromXY(target_x, target_y)
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
