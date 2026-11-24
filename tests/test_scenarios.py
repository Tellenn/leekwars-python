"""Tests de bout en bout : `main.turn()` sur des scénarios de combat.

Ces tests vérifient le comportement observable de l'IA (PV, TP, PM,
journal), pas les détails internes du moteur de décision.
"""

import unittest

import support

from leekwars_api import builder


class TurnScenarioTest(unittest.TestCase):
    def test_ai_equips_a_weapon_and_shoots_the_enemy(self):
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        main = support.load_main(fight)

        main.turn()

        self.assertIsNotNone(fight.me.weapon)
        self.assertLess(fight.enemies[0].life, 100)
        self.assertTrue(any("equipping" in line for line in fight.logs))

    def test_ai_moves_closer_when_nothing_is_in_range(self):
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1, range_=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(5, 5))],
        )
        main = support.load_main(fight)

        main.turn()

        # l'IA s'est rapprochée (le journal le confirme), puis a tiré ;
        # elle replie ensuite en fuyant, donc on ne compare pas la distance
        # finale.
        self.assertTrue(any("moving closer" in line for line in fight.logs))
        self.assertLess(fight.enemies[0].life, 100)

    def test_ai_heals_when_the_heal_ratio_beats_the_damage_ratio(self):
        # 40 PV de soin pour 1 PT  >  10 dégâts pour 1 PT
        fight = support.make_fight(
            me=builder.entity(
                life=10, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
                chips=[support.heal_chip(amount=40, cost=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        main = support.load_main(fight)

        main.turn()

        # le soin passe en premier (meilleur ratio), l'attaque continue
        # ensuite avec les PT restants
        self.assertEqual(fight.me.life, 50)
        self.assertLess(fight.enemies[0].life, 100)
        heal_index = next(i for i, line in enumerate(fight.logs)
                          if "Casting heal chip" in line)
        shot_index = next(i for i, line in enumerate(fight.logs)
                          if "Shot #" in line)
        self.assertLess(heal_index, shot_index)

    def test_ai_prefers_the_attack_when_it_is_more_profitable(self):
        fight = support.make_fight(
            me=builder.entity(
                life=10, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=30, cost=1)],
                chips=[support.heal_chip(amount=5, cost=3)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        main = support.load_main(fight)

        main.turn()

        self.assertLess(fight.enemies[0].life, 100)
        self.assertEqual(fight.me.life, 10)

    def test_ai_logs_a_profitability_report(self):
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
                chips=[support.heal_chip(amount=20, cost=2)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        main = support.load_main(fight)

        main.turn()

        self.assertTrue(any("Profitability report" in line
                            for line in fight.logs))
        self.assertTrue(any("Strength" in line for line in fight.logs))

    def test_ai_tries_to_break_the_line_of_sight_at_the_end_of_the_turn(self):
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        main = support.load_main(fight)

        main.turn()

        # La fuite consomme des PM (l'IA s'est déplacée pour casser la vue).
        self.assertLess(fight.me.mp, 10)

    def test_turn_without_enemy_is_a_no_op(self):
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
            ),
            enemies=[],
        )
        main = support.load_main(fight)

        main.turn()

        self.assertTrue(any("No enemy" in line for line in fight.logs))
        self.assertEqual(fight.me.tp, 10)


if __name__ == "__main__":
    unittest.main()
