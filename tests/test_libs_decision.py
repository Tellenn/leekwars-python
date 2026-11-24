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


class ShieldDecisionTest(unittest.TestCase):
    """Puces de bouclier : mesure des dégâts reçus et arbitrage."""

    def setUp(self):
        decision_lib.reset_state()

    def tearDown(self):
        decision_lib.reset_state()

    def _fight(self, life=100, chip=None, enemy_life=100):
        fight = support.make_fight(
            me=builder.entity(
                life=life, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
                chips=[chip] if chip else [],
            ),
            enemies=[builder.entity(life=enemy_life, max_life=enemy_life,
                                    cell=(1, 0))],
        )
        install(fight)
        return fight

    def test_shield_chip_is_flagged_and_usable(self):
        fight = self._fight(chip=support.shield_chip(relative=50))
        usable, options = decision_lib.build_options(fight.me)
        shield = [o for o in options if o["obj"].name == "forteresse"][0]

        self.assertTrue(shield["is_shield"])
        self.assertIn(shield, usable)

    def test_incoming_damage_is_measured_between_turns(self):
        fight = self._fight()
        me = fight.me
        decision_lib.begin_turn(me)
        decision_lib.end_turn(me)

        me.take_damage(40)  # l'ennemi nous frappe pendant son tour
        incoming = decision_lib.begin_turn(me)

        self.assertEqual(incoming, 40)

    def test_no_shield_is_used_without_a_known_incoming_damage(self):
        # Tour 1 : on ne sait pas encore ce que l'ennemi inflige.
        fight = self._fight(chip=support.shield_chip(relative=50))
        me = fight.me
        decision_lib.begin_turn(me)

        decision_lib.attack(me, fight.enemies[0])

        self.assertFalse(any("Shield:" in line for line in fight.logs))

    def test_shield_is_played_when_it_avoids_death(self):
        # 5 PV restants, l'ennemi frappe 35 : sans bouclier on meurt ce tour,
        # avec 90 % de bouclier on survit.
        fight = self._fight(life=40, chip=support.shield_chip(relative=90))
        me = fight.me
        enemy = fight.enemies[0]
        decision_lib.begin_turn(me)
        decision_lib.end_turn(me)
        me.take_damage(35)
        decision_lib.begin_turn(me)

        decision_lib.attack(me, enemy)

        self.assertTrue(any("Shield:" in line for line in fight.logs))
        self.assertGreater(me.relativeShield, 0)
        self.assertTrue(me.alive)

    def test_shield_is_not_played_when_we_win_without_it(self):
        # On tue l'ennemi avant d'être mort : la survie ne vaut rien.
        fight = self._fight(life=100, enemy_life=20,
                            chip=support.shield_chip(relative=50))
        me = fight.me
        enemy = fight.enemies[0]
        decision_lib.begin_turn(me)
        decision_lib.end_turn(me)
        me.take_damage(10)
        decision_lib.begin_turn(me)

        decision_lib.attack(me, enemy)

        self.assertFalse(any("Shield:" in line for line in fight.logs))

    def test_incoming_damage_is_reported_in_the_state_line(self):
        fight = self._fight()
        me = fight.me
        decision_lib.begin_turn(me)
        decision_lib.end_turn(me)
        me.take_damage(12)
        decision_lib.begin_turn(me)

        decision_lib.attack(me, fight.enemies[0])

        self.assertTrue(any("incoming 12" in line for line in fight.logs))

    def test_a_life_saving_shield_is_reported_as_mandatory(self):
        fight = self._fight(life=40, chip=support.shield_chip(relative=90))
        me = fight.me
        enemy = fight.enemies[0]
        decision_lib.begin_turn(me)
        decision_lib.end_turn(me)
        me.take_damage(35)
        decision_lib.begin_turn(me)

        decision_lib.attack(me, enemy)

        self.assertTrue(any("(sauve la mort)" in line
                            for line in fight.logs))


if __name__ == "__main__":
    unittest.main()
