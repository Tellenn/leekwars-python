"""Tests de `libs/decision_lib.py` : options, scoring, exécution du plan."""

import unittest

import support

from leekwars_api import builder, install

import libs.decision_lib as decision_lib


class BuildOptionsTest(unittest.TestCase):
    def setUp(self):
        self.fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(), support.rifle()],
                chips=[support.heal_chip(), support.strength_chip()],
            ),
            enemies=[builder.entity(life=50, max_life=50, cell=(1, 0))],
        )
        install(self.fight)
        self.me = self.fight.me
        self.enemy = self.fight.enemies[0]

    def test_weapon_option_costs_one_tp_to_equip(self):
        usable, options = decision_lib.build_options(self.me)
        weapons = [o for o in options if o["kind"] == "weapon"]

        self.assertEqual(len(weapons), 2)
        self.assertTrue(all(o["switch"] == 1 for o in weapons))

    def test_equipped_weapon_costs_nothing_to_equip(self):
        self.me.setWeapon(self.me.weapons[0])
        usable, options = decision_lib.build_options(self.me)
        equipped = [o for o in options if o["obj"] is self.me.weapons[0]]

        self.assertEqual(equipped[0]["switch"], 0)

    def test_chips_are_free_to_equip(self):
        usable, options = decision_lib.build_options(self.me)
        chips = [o for o in options if o["kind"] == "chip"]

        self.assertEqual(len(chips), 2)
        self.assertTrue(all(o["switch"] == 0 for o in chips))

    def test_equipment_without_damage_buff_or_heal_is_not_usable(self):
        useless = builder.weapon(
            "bâton",
            cost=1,
            features=[
                builder.feature(
                    Effect.BUFF_AGILITY,
                    Effect.Target.CASTER,
                    5, 5,
                )
            ],
        )
        self.me.weapons.append(useless)
        usable, options = decision_lib.build_options(self.me)

        self.assertNotIn(useless, [o["obj"] for o in usable])
        self.assertIn(useless, [o["obj"] for o in options])

    def test_heal_chip_is_flagged_as_heal_and_strength_chip_as_buff(self):
        usable, options = decision_lib.build_options(self.me)
        heal = [o for o in options if o["obj"].name == "bandage"][0]
        buff = [o for o in options if o["obj"].name == "tonique"][0]

        self.assertTrue(heal["is_heal"])
        self.assertFalse(heal["is_buff"])
        self.assertTrue(buff["is_buff"])
        self.assertFalse(buff["is_heal"])


class OptionScoreTest(unittest.TestCase):
    def setUp(self):
        self.fight = support.make_fight(
            me=builder.entity(
                life=50, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
                chips=[support.heal_chip(amount=30, cost=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        install(self.fight)
        self.me = self.fight.me
        self.enemy = self.fight.enemies[0]

    def test_attack_score_is_expected_damage_per_tp(self):
        usable, options = decision_lib.build_options(self.me)
        weapon = [o for o in options if o["kind"] == "weapon"][0]

        score, value = decision_lib.option_score(self.me, weapon, usable,
                                                 self.enemy)

        # 10 dégâts / (1 PT d'usage + 1 PT d'équipement) = 5
        self.assertEqual(value, 10)
        self.assertEqual(score, 5)

    def test_heal_score_is_clamped_to_missing_life(self):
        usable, options = decision_lib.build_options(self.me)
        heal = [o for o in options if o["obj"].name == "bandage"][0]

        score, value = decision_lib.option_score(self.me, heal, usable,
                                                 self.enemy)

        # 50 PV manquants, soin de 30 pour 1 PT -> 30
        self.assertEqual(value, 30)
        self.assertEqual(score, 30)

    def test_option_is_unusable_without_enough_tp(self):
        self.me.tp = 0
        usable, options = decision_lib.build_options(self.me)
        weapon = [o for o in options if o["kind"] == "weapon"][0]

        score, value = decision_lib.option_score(self.me, weapon, usable,
                                                 self.enemy)

        self.assertEqual(score, 0)
        self.assertEqual(value, 0)

    def test_out_of_range_weapon_scores_zero(self):
        # l'ennemi est à 5 cases, l'arme porte à 1 case
        far_enemy = builder.entity(life=100, max_life=100, cell=(5, 5))
        usable, options = decision_lib.build_options(self.me)
        weapon = [o for o in options if o["kind"] == "weapon"][0]

        score, value = decision_lib.option_score(self.me, weapon, usable,
                                                 far_enemy)

        self.assertEqual(score, 0)


class AttackLoopTest(unittest.TestCase):
    def test_attack_loop_kills_the_enemy_and_reports_real_damage(self):
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
            ),
            enemies=[builder.entity(life=25, max_life=25, cell=(1, 0))],
        )
        install(fight)
        me = fight.me
        enemy = fight.enemies[0]

        did_hit = decision_lib.attack(me, enemy)

        self.assertTrue(did_hit)
        self.assertEqual(enemy.life, 0)
        self.assertTrue(any("Shot #" in line for line in fight.logs))

    def test_attack_loop_spends_tp(self):
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        install(fight)
        me = fight.me
        enemy = fight.enemies[0]

        decision_lib.attack(me, enemy)

        self.assertLess(me.tp, 10)

    def test_no_usable_option_is_reported(self):
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[],
                chips=[],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        install(fight)

        did_hit = decision_lib.attack(fight.me, fight.enemies[0])

        self.assertFalse(did_hit)
        self.assertTrue(any("No usable option" in line for line in fight.logs))


if __name__ == "__main__":
    unittest.main()
