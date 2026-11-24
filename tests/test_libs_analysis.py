"""Tests de `libs/analysis_lib.py` : parsing d'équipement et valeurs attendues.

Les formules testées ici sont celles de l'encyclopédie FR du jeu
(`docs/encyclopedia/`), pas une réimplémentation : le mock (`leekwars_api/`)
applique déjà les règles du serveur, ces tests vérifient que l'IA **modélise**
correctement ces mêmes règles.
"""

import unittest

import support

from leekwars_api import builder, install

import libs.analysis_lib as analysis_lib
import libs.constants_lib as constants_lib


class AnalyseEquipmentTest(unittest.TestCase):
    """Classification des effets d'une arme / d'une puce."""

    def setUp(self):
        install(support.make_fight())

    def test_damage_is_force_amplified(self):
        weapon = support.pistol(damage=10)
        parts = analysis_lib.analyse_equipment(builder.entity(), weapon)

        self.assertEqual(parts["amp_raw"], 10)
        self.assertEqual(parts["flat_sub"], 0)
        self.assertEqual(parts["nova_raw"], 0)
        self.assertFalse(parts["kill"])

    def test_life_damage_is_a_percentage_of_caster_max_life(self):
        # fr/Effets : EFFECT_LIFE_DAMAGE retire un pourcentage de la vie du
        # lanceur (et n'est pas amplifié par la force).
        caster = builder.entity(max_life=200)
        weapon = builder.weapon(
            "drain",
            cost=1,
            features=[
                builder.feature(
                    Effect.LIFE_DAMAGE,
                    Effect.Target.ENEMIES,
                    10, 10,
                )
            ],
        )
        parts = analysis_lib.analyse_equipment(caster, weapon)

        self.assertEqual(parts["amp_raw"], 0)
        self.assertEqual(parts["flat_sub"], 20)  # 10 % de 200 PV

    def test_nova_damage_has_its_own_bucket(self):
        # fr/Effets : les dégâts nova retirent des PV *maximum* et sont
        # amplifiés par la science (pas par la force).
        weapon = builder.weapon(
            "nova",
            cost=1,
            features=[
                builder.feature(
                    Effect.NOVA_DAMAGE,
                    Effect.Target.ENEMIES,
                    12, 12,
                )
            ],
        )
        parts = analysis_lib.analyse_equipment(builder.entity(), weapon)

        self.assertEqual(parts["amp_raw"], 0)
        self.assertEqual(parts["nova_raw"], 12)

    def test_kill_is_modelled_as_instant_death(self):
        weapon = builder.weapon(
            "fauchet",
            cost=5,
            features=[
                builder.feature(
                    Effect.KILL,
                    Effect.Target.ENEMIES,
                    0, 0,
                )
            ],
        )
        parts = analysis_lib.analyse_equipment(builder.entity(), weapon)

        self.assertTrue(parts["kill"])

    def test_heal_is_wisdom_amplified_and_raw_heal_is_not(self):
        heal = support.heal_chip(amount=15)
        raw = support.raw_heal_chip(amount=15)

        heal_parts = analysis_lib.analyse_equipment(builder.entity(), heal)
        raw_parts = analysis_lib.analyse_equipment(builder.entity(), raw)

        self.assertEqual(heal_parts["heal_raw"], 15)
        self.assertEqual(heal_parts["heal_flat"], 0)
        self.assertEqual(raw_parts["heal_raw"], 0)
        self.assertEqual(raw_parts["heal_flat"], 15)

    def test_strength_buff_is_science_amplified_but_raw_is_not(self):
        caster = builder.entity(science=100)
        amplified = analysis_lib.analyse_equipment(caster, support.strength_chip(20))
        raw = analysis_lib.analyse_equipment(caster, support.raw_strength_chip(20))

        self.assertEqual(amplified["buff_strength"], 40)  # 20 * (1 + 100/100)
        self.assertEqual(raw["buff_strength"], 20)       # variante RAW : pas amplifiée

    def test_damage_targeting_allies_is_not_counted_as_damage(self):
        weapon = builder.weapon(
            "ami",
            cost=1,
            features=[
                builder.feature(
                    Effect.DAMAGE,
                    Effect.Target.ALLIES,
                    10, 10,
                )
            ],
        )
        parts = analysis_lib.analyse_equipment(builder.entity(), weapon)

        self.assertEqual(parts["amp_raw"], 0)
        self.assertEqual(parts["flat_sub"], 0)
        self.assertEqual(parts["nova_raw"], 0)


class ShieldAnalysisTest(unittest.TestCase):
    """Boucliers (fr/Résistance) : relatif en %, absolu en montant."""

    def setUp(self):
        install(support.make_fight())

    def test_relative_shield_is_parsed_with_its_duration(self):
        parts = analysis_lib.analyse_equipment(
            builder.entity(), support.shield_chip(relative=10, turns=3))

        self.assertEqual(parts["shield_relative"], 10)
        self.assertEqual(parts["shield_absolute"], 0)
        self.assertEqual(parts["shield_turns"], 3)

    def test_absolute_shield_is_parsed(self):
        parts = analysis_lib.analyse_equipment(
            builder.entity(), support.shield_chip(relative=0, absolute=25))

        self.assertEqual(parts["shield_relative"], 0)
        self.assertEqual(parts["shield_absolute"], 25)

    def test_shield_is_amplified_by_resistance_but_raw_is_not(self):
        caster = builder.entity(resistance=100)
        amplified = analysis_lib.analyse_equipment(
            caster, support.shield_chip(relative=10))
        raw_chip = builder.chip(
            "mur",
            cost=2,
            features=[
                builder.feature(
                    Effect.RAW_RELATIVE_SHIELD,
                    Effect.Target.CASTER,
                    10, 10, turns=2,
                )
            ],
        )
        raw = analysis_lib.analyse_equipment(caster, raw_chip)

        self.assertEqual(amplified["shield_relative"], 20)  # 10 * (1 + 100/100)
        self.assertEqual(raw["shield_relative"], 10)       # variante RAW

    def test_shield_is_not_counted_as_damage_nor_as_a_buff(self):
        parts = analysis_lib.analyse_equipment(
            builder.entity(), support.shield_chip(relative=10))

        self.assertEqual(parts["amp_raw"], 0)
        self.assertEqual(parts["buff_strength"], 0)
        self.assertEqual(parts["heal_raw"], 0)


class ExpectedDamageTest(unittest.TestCase):
    """Dégâts attendus : force, crits, boucliers, nova, kill."""

    def setUp(self):
        install(support.make_fight())

    def test_force_multiplies_damage(self):
        parts = {"amp_raw": 10, "flat_sub": 0, "nova_raw": 0, "kill": False}
        attacker = builder.entity(strength=100)
        target = builder.entity(life=100, max_life=100)

        self.assertEqual(analysis_lib.expected_damage(parts, target, attacker), 20)

    def test_crit_is_an_expectation_on_agility(self):
        # P(crit) = agilité / 1000, multiplicateur 1.3
        parts = {"amp_raw": 10, "flat_sub": 0, "nova_raw": 0, "kill": False}
        attacker = builder.entity(agility=1000)
        target = builder.entity(life=100, max_life=100)

        self.assertAlmostEqual(
            analysis_lib.expected_damage(parts, target, attacker), 13.0
        )

    def test_relative_and_absolute_shields_are_applied(self):
        # fr/Résistance : final = base * (1 - relatif/100) - absolu
        parts = {"amp_raw": 10, "flat_sub": 0, "nova_raw": 0, "kill": False}
        attacker = builder.entity()
        target = builder.entity(life=100, max_life=100,
                                relative_shield=50, absolute_shield=3)

        self.assertAlmostEqual(
            analysis_lib.expected_damage(parts, target, attacker), 2.0
        )

    def test_damage_never_goes_below_zero(self):
        parts = {"amp_raw": 10, "flat_sub": 0, "nova_raw": 0, "kill": False}
        attacker = builder.entity()
        target = builder.entity(life=100, max_life=100, absolute_shield=50)

        self.assertEqual(analysis_lib.expected_damage(parts, target, attacker), 0)

    def test_nova_damage_ignores_shields_and_is_science_amplified(self):
        parts = {"amp_raw": 0, "flat_sub": 0, "nova_raw": 10, "kill": False}
        attacker = builder.entity(science=100)
        target = builder.entity(life=100, max_life=100,
                                relative_shield=90, absolute_shield=50)

        self.assertEqual(analysis_lib.expected_damage(parts, target, attacker), 20)

    def test_kill_worths_the_target_remaining_life(self):
        parts = {"amp_raw": 0, "flat_sub": 0, "nova_raw": 0, "kill": True}
        attacker = builder.entity()
        target = builder.entity(life=42, max_life=100)

        self.assertEqual(analysis_lib.expected_damage(parts, target, attacker), 42)

    def test_expected_damage_defaults_to_fight_me(self):
        # Rétro-compatibilité : sans argument, l'attaquant est Fight.me.
        fight = support.make_fight(
            me=builder.entity(strength=100, life=100, max_life=100, cell=(0, 0)),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        install(fight)
        parts = {"amp_raw": 10, "flat_sub": 0, "nova_raw": 0, "kill": False}

        self.assertEqual(
            analysis_lib.expected_damage(parts, fight.enemies[0]), 20
        )


class ExpectedLifestealTest(unittest.TestCase):
    """Vol de vie (fr/Sagesse) : part des dégâts dépendant de la force
    convertie en soins pour le lanceur."""

    def setUp(self):
        install(support.make_fight())

    def test_lifesteal_is_a_tenth_of_the_damage_with_100_wisdom(self):
        parts = {"amp_raw": 100, "flat_sub": 0, "nova_raw": 0, "kill": False}
        attacker = builder.entity(wisdom=100)
        target = builder.entity(life=500, max_life=500)

        self.assertAlmostEqual(
            analysis_lib.expected_lifesteal(parts, target, attacker), 10.0
        )

    def test_lifesteal_uses_the_damage_after_shields(self):
        parts = {"amp_raw": 100, "flat_sub": 0, "nova_raw": 0, "kill": False}
        attacker = builder.entity(wisdom=100)
        target = builder.entity(life=500, max_life=500, relative_shield=50)

        self.assertAlmostEqual(
            analysis_lib.expected_lifesteal(parts, target, attacker), 5.0
        )

    def test_flat_damage_gives_no_lifesteal(self):
        # Seuls les dégâts dépendant de la force donnent du vol de vie.
        parts = {"amp_raw": 0, "flat_sub": 100, "nova_raw": 0, "kill": False}
        attacker = builder.entity(wisdom=100)
        target = builder.entity(life=500, max_life=500)

        self.assertEqual(
            analysis_lib.expected_lifesteal(parts, target, attacker), 0
        )


class ExpectedHealTest(unittest.TestCase):
    def setUp(self):
        install(support.make_fight())

    def test_heal_is_amplified_by_wisdom(self):
        parts = {"heal_raw": 15, "heal_flat": 0}
        caster = builder.entity(wisdom=100)

        self.assertEqual(analysis_lib.expected_heal(parts, caster), 30)

    def test_raw_heal_is_not_amplified(self):
        parts = {"heal_raw": 0, "heal_flat": 15}
        caster = builder.entity(wisdom=100)

        self.assertEqual(analysis_lib.expected_heal(parts, caster), 15)


class InRangeTest(unittest.TestCase):
    def test_range_is_checked_against_the_cell_distance(self):
        weapon = support.pistol(range_=2)
        # les entités doivent être placées dans un combat pour avoir une case
        fight = support.make_fight(
            me=builder.entity(cell=(0, 0)),
            enemies=[builder.entity(cell=(2, 0)), builder.entity(cell=(5, 0))],
        )
        me = fight.me
        close, far = fight.enemies

        self.assertTrue(analysis_lib.in_range(weapon, me, close))
        self.assertFalse(analysis_lib.in_range(weapon, me, far))

    def test_range_uses_the_api_distance(self):
        # Le moteur contrôle la portée avec `Cell.distance()` (une
        # diagonale y compte 2 cases) : l'IA doit utiliser la même
        # métrique, sinon elle tire et se fait refuser (mesuré en combat
        # de test #54912618 : le fusil (portée 7) accepté à distance 7,
        # la puce (portée 5) refusée).
        weapon = support.pistol(range_=2)
        fight = support.make_fight(
            me=builder.entity(cell=(0, 0)),
            enemies=[builder.entity(cell=(2, 0))],
        )
        me = fight.me
        enemy = fight.enemies[0]

        # la métrique de l'API peut être plus grande que la distance
        # droite (déplacement en diagonale) : l'IA suit l'API.
        me.cell.distance = lambda target: 5

        self.assertFalse(analysis_lib.in_range(weapon, me, enemy))


class ConstantsTest(unittest.TestCase):
    def test_science_amplified_covers_every_science_buff(self):
        # fr/Effets : BUFF_STRENGTH, BUFF_AGILITY, BUFF_RESISTANCE,
        # BUFF_WISDOM, BUFF_TP et BUFF_MP sont amplifiés par la science.
        for effect in (
            Effect.BUFF_STRENGTH,
            Effect.BUFF_AGILITY,
            Effect.BUFF_RESISTANCE,
            Effect.BUFF_WISDOM,
            Effect.BUFF_TP,
            Effect.BUFF_MP,
        ):
            self.assertIn(effect, constants_lib.SCIENCE_AMPLIFIED)

    def test_raw_variants_are_never_amplified(self):
        for effect in (
            Effect.RAW_BUFF_STRENGTH,
            Effect.RAW_BUFF_POWER,
            Effect.RAW_BUFF_TP,
            Effect.RAW_BUFF_MP,
        ):
            self.assertNotIn(effect, constants_lib.SCIENCE_AMPLIFIED)


if __name__ == "__main__":
    unittest.main()
