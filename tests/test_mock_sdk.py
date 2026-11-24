"""Tests unitaires du mock local du SDK Leek Wars (`leekwars_api/`).

Ces tests vérifient les règles du jeu appliquées par le mock : injection des
globaux, distances et lignes de vue, dégâts (force, boucliers), soins
(sagesse), buffs (science), coûts/portées/limites d'utilisation et
déplacements. Ils ne testent pas la logique de l'IA (`libs/`).
"""

from __future__ import annotations

import builtins
import importlib
import inspect
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from leekwars_api import builder, install, uninstall  # noqa: E402
from leekwars_api.effect import Effect  # noqa: E402
from leekwars_api.fight import Fight as FightClass  # noqa: E402


def damage_weapon(
    damage: float = 10,
    *,
    cost: int = 1,
    min_range: int = 0,
    max_range: int = 10,
    max_uses: int = 0,
    name: str = "laser",
):
    """Arme à dégâts constants (aucun aléa de valeur)."""
    return builder.weapon(
        name,
        cost=cost,
        min_range=min_range,
        max_range=max_range,
        max_uses=max_uses,
        features=[
            builder.feature(
                Effect.DAMAGE,
                Effect.Target.ENEMIES,
                damage,
                damage,
            )
        ],
    )


class MockSdkTestCase(unittest.TestCase):
    """Base : nettoie les bindings et les modules entre les tests."""

    def setUp(self) -> None:
        uninstall()
        sys.modules.pop("Kepo_solo", None)

    def tearDown(self) -> None:
        uninstall()
        sys.modules.pop("Kepo_solo", None)


class EffectConstantsTest(MockSdkTestCase):
    """Contrat des constantes : accès direct sur `Effect` + namespaces."""

    #: Valeurs exactes de l'encyclopédie FR « Effets » utilisées par l'IA.
    DIRECT_TYPES = {
        "DAMAGE": 1,
        "HEAL": 2,
        "BUFF_STRENGTH": 3,
        "BUFF_AGILITY": 4,
        "BUFF_MP": 7,
        "BUFF_TP": 8,
        "BOOST_MAX_LIFE": 12,
        "KILL": 16,
        "BUFF_RESISTANCE": 21,
        "BUFF_WISDOM": 22,
        "LIFE_DAMAGE": 28,
        "NOVA_DAMAGE": 30,
        "RAW_BUFF_MP": 31,
        "RAW_BUFF_TP": 32,
        "RAW_BUFF_STRENGTH": 38,
        "RAW_BUFF_POWER": 52,
        "RAW_HEAL": 57,
        "TOTAL_DEBUFF": 60,
        "STEAL_LIFE": 61,
        "MULTIPLY_STATS": 62,
        "DAMAGE_TO_RESISTANCE": 63,
        "SUPERINFECTION": 64,
        "RAW_SHACKLE_STRENGTH": 65,
    }

    def test_each_type_is_available_directly_on_effect(self):
        for name, value in self.DIRECT_TYPES.items():
            self.assertEqual(getattr(Effect, name), value, name)

    def test_type_namespace_mirrors_the_direct_constants(self):
        for name, value in self.DIRECT_TYPES.items():
            self.assertEqual(getattr(Effect.Type, name), value, name)

    def test_buff_force_is_an_alias_of_buff_strength(self):
        self.assertEqual(Effect.BUFF_FORCE, 3)
        self.assertEqual(Effect.BUFF_FORCE, Effect.BUFF_STRENGTH)
        self.assertEqual(Effect.Type.BUFF_FORCE, Effect.Type.BUFF_STRENGTH)

    def test_target_and_modifier_namespaces_exist(self):
        self.assertEqual(Effect.Target.NOT_CASTER, 0)
        self.assertEqual(Effect.Target.ENEMIES, 1)
        self.assertEqual(Effect.Target.ALLIES, 2)
        self.assertEqual(Effect.Target.CASTER, 4)
        self.assertEqual(Effect.Target.NON_SUMMONS, 8)
        self.assertEqual(Effect.Target.SUMMONS, 16)
        self.assertEqual(Effect.Target.ALWAYS_CASTER, 32)
        self.assertEqual(Effect.Modifier.STACKABLE, 1)
        self.assertEqual(Effect.Modifier.MULTIPLIED_BY_TARGETS, 2)
        self.assertEqual(Effect.Modifier.ON_CASTER, 4)
        self.assertEqual(Effect.Modifier.NOT_REPLACEABLE, 8)
        self.assertEqual(Effect.Modifier.IRREDUCTIBLE, 16)

    def test_targets_are_bitwise_combinable_and_testable(self):
        # Mode d'emploi du code de l'IA : feature.targets & Effect.Target.X.
        mask = Effect.Target.ALLIES | Effect.Target.CASTER
        self.assertTrue(mask & Effect.Target.ALLIES)
        self.assertTrue(mask & Effect.Target.CASTER)
        self.assertFalse(mask & Effect.Target.ENEMIES)

        feature = builder.feature(
            Effect.HEAL, Effect.Target.ALLIES | Effect.Target.CASTER, 10, 15
        )
        self.assertTrue(feature.targets & Effect.Target.ALLIES)
        self.assertTrue(feature.targets & Effect.Target.CASTER)
        self.assertFalse(feature.targets & Effect.Target.ENEMIES)

    def test_get_all_returns_the_65_types(self):
        values = Effect.getAll()
        self.assertEqual(len(values), 65)
        self.assertEqual(sorted(values), list(range(1, 66)))
        self.assertIn(Effect.RAW_HEAL, values)
        self.assertIn(Effect.RAW_SHACKLE_STRENGTH, values)


class UseCodesTest(MockSdkTestCase):
    """`Fight.Use` : valeurs exactes et codes retournés par les actions."""

    def test_use_codes_have_the_exact_runtime_values(self):
        fight = builder.make_fight(
            me=builder.entity(cell=(0, 0)),
            enemies=[builder.entity(cell=(1, 0))],
        )
        install(fight)
        expected = {
            "FAILED": 0,
            "SUCCESS": 1,
            "CRITICAL": 2,
            "INVALID_TARGET": -1,
            "NOT_ENOUGH_TP": -2,
            "INVALID_COOLDOWN": -3,
            "INVALID_POSITION": -4,
            "TOO_MANY_SUMMONS": -5,
            "RESURRECT_INVALID_ENTITY": -6,
            "MAX_USES": -7,
            "INVALID_STATE": -8,
        }
        for name, value in expected.items():
            self.assertEqual(getattr(FightClass.Use, name), value, name)
            # Même namespace accessible depuis l'instance liée dans builtins.
            self.assertEqual(getattr(builtins.Fight.Use, name), value, name)

    def test_successful_action_returns_a_positive_code(self):
        weapon = damage_weapon(10, cost=1, max_range=10)
        fight = builder.make_fight(
            me=builder.entity(weapons=[weapon], cell=(0, 0)),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        install(fight)
        fight.me.setWeapon(weapon)

        result = fight.me.useWeapon(fight.getNearestEnemy())

        self.assertGreater(result, 0)  # idiome `if me.useWeapon(e) > 0`
        self.assertEqual(result, FightClass.Use.SUCCESS)
        self.assertIsInstance(result, int)

    def test_failure_returns_a_code_without_raising(self):
        weapon = damage_weapon(10, cost=20, max_range=1)
        fight = builder.make_fight(
            me=builder.entity(weapons=[weapon], cell=(0, 0), tp=10),
            enemies=[builder.entity(cell=(5, 0))],
        )
        install(fight)
        fight.me.setWeapon(weapon)
        enemy = fight.getNearestEnemy()

        # Pas assez de PT : -2, pas d'exception.
        self.assertEqual(fight.me.useWeapon(enemy), FightClass.Use.NOT_ENOUGH_TP)
        self.assertLess(fight.me.useWeapon(enemy), 0)

    def test_out_of_range_returns_invalid_position(self):
        weapon = damage_weapon(10, cost=1, max_range=2)
        fight = builder.make_fight(
            me=builder.entity(weapons=[weapon], cell=(0, 0)),
            enemies=[builder.entity(cell=(5, 0))],
        )
        install(fight)
        fight.me.setWeapon(weapon)

        self.assertEqual(
            fight.me.useWeapon(fight.getNearestEnemy()),
            FightClass.Use.INVALID_POSITION,
        )

    def test_no_line_of_sight_returns_invalid_position(self):
        weapon = damage_weapon(10, cost=1, max_range=2)
        fight = builder.make_fight(
            me=builder.entity(weapons=[weapon], cell=(0, 0)),
            enemies=[builder.entity(cell=(2, 0))],
        )
        install(fight)
        fight.me.setWeapon(weapon)
        # La cible reste à portée (2 cases), mais un obstacle coupe la vue.
        fight.field.cellFromXY(1, 0).obstacle = True

        self.assertEqual(
            fight.me.useWeapon(fight.getNearestEnemy()),
            FightClass.Use.INVALID_POSITION,
        )

    def test_max_uses_returns_minus_seven(self):
        weapon = damage_weapon(10, cost=1, max_range=10, max_uses=1)
        fight = builder.make_fight(
            me=builder.entity(weapons=[weapon], cell=(0, 0)),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        install(fight)
        fight.me.setWeapon(weapon)
        enemy = fight.getNearestEnemy()
        fight.me.useWeapon(enemy)

        self.assertEqual(fight.me.useWeapon(enemy), FightClass.Use.MAX_USES)

    def test_critical_is_reported_and_multiplies_the_effect(self):
        # Agilité 1000 => probabilité de critique de 100 %.
        weapon = damage_weapon(10, cost=1, max_range=10)
        fight = builder.make_fight(
            me=builder.entity(agility=1000, weapons=[weapon], cell=(0, 0)),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        install(fight)
        fight.me.setWeapon(weapon)
        enemy = fight.getNearestEnemy()

        result = fight.me.useWeapon(enemy)

        self.assertEqual(result, FightClass.Use.CRITICAL)
        self.assertGreater(result, 0)
        self.assertEqual(enemy.life, 87)  # 10 * 1.3 = 13 dégâts

    def test_can_use_helpers_are_booleans(self):
        weapon = damage_weapon(10, cost=1, max_range=10)
        fight = builder.make_fight(
            me=builder.entity(weapons=[weapon], cell=(0, 0)),
            enemies=[builder.entity(cell=(1, 0))],
        )
        install(fight)
        enemy = fight.getNearestEnemy()

        result = fight.me.canUseWeapon(enemy, weapon)
        self.assertIsInstance(result, bool)
        self.assertTrue(result)


class FightConstantsTest(MockSdkTestCase):
    def test_constants_and_namespaces(self):
        fight = builder.make_fight(
            me=builder.entity(cell=(0, 0)),
            enemies=[builder.entity(cell=(1, 0))],
        )
        install(fight)

        self.assertEqual(FightClass.CRITICAL_FACTOR, 1.3)
        self.assertEqual(FightClass.MAX_TURNS, 64)
        self.assertEqual(FightClass.SUMMON_LIMIT, 8)
        self.assertEqual(fight.CRITICAL_FACTOR, 1.3)

        # Les namespaces exposent des constantes entières minimalistes.
        for namespace in (
            FightClass.Type,
            FightClass.Context,
            FightClass.Boss,
            FightClass.Erosion,
        ):
            values = [
                value
                for name, value in vars(namespace).items()
                if not name.startswith("_")
            ]
            self.assertTrue(values, namespace.__name__)
            self.assertTrue(all(isinstance(value, int) for value in values))

        self.assertEqual(FightClass.Type.SOLO, 0)
        self.assertEqual(FightClass.Type.TEAM, 1)
        self.assertEqual(FightClass.Type.BATTLE_ROYALE, 2)
        self.assertTrue(hasattr(FightClass.Erosion, "DAMAGE"))
        self.assertTrue(hasattr(FightClass.Erosion, "POISON"))
        self.assertTrue(hasattr(FightClass.Erosion, "CRITICAL_BONUS"))

    def test_item_area_and_launch_type_are_exposed(self):
        from leekwars_api.items import Item

        weapon = builder.weapon("test", max_range=1)
        self.assertEqual(weapon.area, Item.Area.SINGLE_CELL)
        self.assertEqual(weapon.launchType, Item.LaunchType.CIRCLE)
        self.assertIsInstance(Item.Area.CIRCLE_2, int)
        self.assertIsInstance(Item.LaunchType.STAR, int)


class BuilderSignatureTest(MockSdkTestCase):
    """Les signatures du builder sont un contrat pour les tests de l'IA."""

    def _parameters(self, function):
        return [
            (name, parameter.default)
            for name, parameter in inspect.signature(function).parameters.items()
        ]

    def test_weapon_and_chip_signatures(self):
        expected = [
            ("name", inspect.Parameter.empty),
            ("cost", 1),
            ("min_range", 0),
            ("max_range", 1),
            ("features", ()),
            ("max_uses", 0),
            ("needs_los", True),
            ("inline", False),
            ("failure", 0),
            ("id", None),
        ]
        self.assertEqual(self._parameters(builder.weapon), expected)
        self.assertEqual(self._parameters(builder.chip), expected)

    def test_feature_signature(self):
        self.assertEqual(
            self._parameters(builder.feature),
            [
                ("type", inspect.Parameter.empty),
                ("targets", inspect.Parameter.empty),
                ("min_value", 0),
                ("max_value", 0),
                ("turns", 0),
                ("modifiers", 0),
            ],
        )

    def test_entity_signature(self):
        expected_names = [
            "name",
            "life",
            "max_life",
            "tp",
            "max_tp",
            "mp",
            "max_mp",
            "strength",
            "agility",
            "wisdom",
            "resistance",
            "science",
            "magic",
            "power",
            "level",
            "cell",
            "weapons",
            "chips",
            "weapon",
            "relative_shield",
            "absolute_shield",
            "side",
            "id",
        ]
        signature = inspect.signature(builder.entity)
        self.assertEqual(list(signature.parameters), expected_names)
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )
        self.assertEqual(signature.parameters["cell"].default, (0, 0))
        self.assertEqual(signature.parameters["side"].default, 1)

    def test_make_fight_signature(self):
        signature = inspect.signature(builder.make_fight)
        self.assertEqual(
            list(signature.parameters), ["me", "enemies", "allies", "map_size", "seed"]
        )
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )
        self.assertEqual(signature.parameters["enemies"].default, ())
        self.assertEqual(signature.parameters["allies"].default, ())
        self.assertEqual(signature.parameters["map_size"].default, 12)
        self.assertEqual(signature.parameters["seed"].default, 0)


class InstallTest(MockSdkTestCase):
    def test_install_exposes_globals_and_main_reads_fight_me(self):
        weapon = damage_weapon(10, max_range=10)
        fight = builder.make_fight(
            me=builder.entity(weapons=[weapon], cell=(0, 0)),
            enemies=[builder.entity(cell=(2, 0))],
        )

        returned = install(fight)
        self.assertIs(returned, fight)
        self.assertIs(builtins.Fight, fight)
        self.assertIs(builtins.Effect, Effect)
        self.assertTrue(hasattr(builtins, "Debug"))
        self.assertIs(builtins.Field, fight.field)

        ai = importlib.import_module("Kepo_solo")
        self.assertIs(ai.me, fight.me)

        uninstall()
        self.assertFalse(hasattr(builtins, "Fight"))
        self.assertFalse(hasattr(builtins, "Effect"))


class CellTest(MockSdkTestCase):
    def _fight(self):
        fight = builder.make_fight(
            me=builder.entity(cell=(0, 0)),
            enemies=[builder.entity(cell=(2, 0))],
        )
        install(fight)
        return fight

    def test_distance_is_chebyshev(self):
        fight = self._fight()
        enemy = fight.getNearestEnemy()
        diagonal = fight.field.cellFromXY(2, 2)
        self.assertEqual(fight.me.cell.distance(enemy.cell), 2)
        self.assertEqual(fight.me.cell.distance(diagonal), 2)
        self.assertEqual(fight.me.distance(enemy), 2)

    def test_line_of_sight_is_blocked_by_an_obstacle_only(self):
        fight = self._fight()
        enemy = fight.getNearestEnemy()
        middle = fight.field.cellFromXY(1, 0)

        middle.obstacle = True
        self.assertFalse(fight.me.cell.lineOfSight(enemy.cell))

        middle.obstacle = False
        self.assertTrue(fight.me.cell.lineOfSight(enemy.cell))

    def test_cell_get_resolves_the_current_field(self):
        fight = self._fight()
        cell = fight.field.cellFromXY(3, 4)
        self.assertIs(builtins.Cell.get(cell.id), cell)


class WeaponDamageTest(MockSdkTestCase):
    def test_use_weapon_costs_tp_and_applies_force_and_shields(self):
        weapon = damage_weapon(10, cost=2, max_range=10)
        fight = builder.make_fight(
            me=builder.entity(strength=100, weapons=[weapon], tp=10, cell=(0, 0)),
            enemies=[
                builder.entity(
                    life=100,
                    max_life=100,
                    cell=(2, 0),
                    relative_shield=50,
                    absolute_shield=3,
                )
            ],
        )
        install(fight)
        self.assertTrue(fight.me.setWeapon(weapon))  # 1 PT
        tp_before = fight.me.tp
        enemy = fight.getNearestEnemy()

        result = fight.me.useWeapon(enemy)

        # 10 * (1 + 100/100) = 20 ; 20 * (1 - 50/100) - 3 = 7.
        self.assertEqual(result, FightClass.Use.SUCCESS)
        self.assertEqual(fight.me.tp, tp_before - 2)
        self.assertEqual(enemy.life, 93)

    def test_nova_damage_removes_max_life_and_ignores_shields(self):
        nova = builder.weapon(
            "nova",
            cost=1,
            max_range=10,
            features=[
                builder.feature(
                    Effect.NOVA_DAMAGE, Effect.Target.ENEMIES, 5, 5
                )
            ],
        )
        fight = builder.make_fight(
            me=builder.entity(weapons=[nova], cell=(0, 0)),
            enemies=[
                builder.entity(
                    life=80,
                    max_life=100,
                    cell=(1, 0),
                    relative_shield=90,
                    absolute_shield=50,
                )
            ],
        )
        install(fight)
        fight.me.setWeapon(nova)
        enemy = fight.getNearestEnemy()

        self.assertEqual(fight.me.useWeapon(enemy), FightClass.Use.SUCCESS)

        self.assertEqual(enemy.maxLife, 95)
        self.assertEqual(enemy.life, 80)

    def test_erosion_shrinks_max_life_by_five_percent_of_the_damage(self):
        # fr/Érosion : 5 % des dégâts subis sont retirés à la vie maximum.
        weapon = damage_weapon(10, cost=2, max_range=10)
        fight = builder.make_fight(
            me=builder.entity(strength=100, weapons=[weapon], tp=10, cell=(0, 0)),
            enemies=[builder.entity(life=100, max_life=100, cell=(2, 0))],
        )
        install(fight)
        fight.me.setWeapon(weapon)
        enemy = fight.getNearestEnemy()

        fight.me.useWeapon(enemy)

        # 10 * (1 + 100/100) = 20 de dégâts -> 5 % d'érosion.
        self.assertEqual(enemy.life, 80)
        self.assertAlmostEqual(enemy.maxLife, 99.0)

    def test_erosion_is_computed_on_the_damage_actually_taken(self):
        # Les boucliers atténuent l'érosion (elle porte sur les dégâts subis).
        weapon = damage_weapon(10, cost=2, max_range=10)
        fight = builder.make_fight(
            me=builder.entity(strength=100, weapons=[weapon], tp=10, cell=(0, 0)),
            enemies=[
                builder.entity(
                    life=100, max_life=100, cell=(2, 0),
                    relative_shield=50,
                )
            ],
        )
        install(fight)
        fight.me.setWeapon(weapon)
        enemy = fight.getNearestEnemy()

        fight.me.useWeapon(enemy)

        # 20 de dégâts, 50 % de bouclier relatif -> 10 subis -> 0,5 d'érosion.
        self.assertEqual(enemy.life, 90)
        self.assertAlmostEqual(enemy.maxLife, 99.5)

    def test_kill_ignores_shields(self):
        kill = builder.weapon(
            "fauchet",
            cost=1,
            max_range=10,
            features=[
                builder.feature(Effect.KILL, Effect.Target.ENEMIES, 0, 0)
            ],
        )
        fight = builder.make_fight(
            me=builder.entity(weapons=[kill], cell=(0, 0)),
            enemies=[
                builder.entity(
                    life=80,
                    max_life=100,
                    cell=(1, 0),
                    relative_shield=100,
                    absolute_shield=100,
                )
            ],
        )
        install(fight)
        fight.me.setWeapon(kill)

        fight.me.useWeapon(fight.getNearestEnemy())

        self.assertEqual(fight.enemies[0].life, 0)


class HealAndBuffTest(MockSdkTestCase):
    def test_heal_is_wisdom_amplified_and_capped_at_max_life(self):
        heal = builder.chip(
            "bandage",
            cost=1,
            min_range=0,
            max_range=0,
            features=[
                builder.feature(Effect.HEAL, Effect.Target.CASTER, 10, 10)
            ],
        )
        fight = builder.make_fight(
            me=builder.entity(
                life=50, max_life=100, wisdom=100, chips=[heal], tp=10, cell=(0, 0)
            ),
            enemies=[builder.entity(cell=(5, 0))],
        )
        install(fight)

        fight.me.useChip(heal)
        # 10 * (1 + 100/100) = 20 PV rendus.
        self.assertEqual(fight.me.life, 70)

        fight.me.useChip(heal)
        self.assertEqual(fight.me.life, 90)

        fight.me.useChip(heal)
        self.assertEqual(fight.me.life, 100)  # plafonné aux PV max

    def test_strength_buff_is_science_amplified_but_raw_is_not(self):
        buff = builder.chip(
            "tonique",
            cost=1,
            features=[
                builder.feature(
                    Effect.BUFF_STRENGTH, Effect.Target.CASTER, 10, 10
                )
            ],
        )
        raw = builder.chip(
            "elixir",
            cost=1,
            features=[
                builder.feature(
                    Effect.RAW_BUFF_STRENGTH, Effect.Target.CASTER, 10, 10
                )
            ],
        )
        fight = builder.make_fight(
            me=builder.entity(science=100, chips=[buff, raw], cell=(0, 0)),
            enemies=[builder.entity(cell=(5, 0))],
        )
        install(fight)

        fight.me.useChip(buff)
        self.assertEqual(fight.me.strength, 20)  # 10 * (1 + 100/100)

        fight.me.useChip(raw)
        self.assertEqual(fight.me.strength, 30)  # RAW : +10 seulement


class UsageRulesTest(MockSdkTestCase):
    def _fight_with_weapon(self, weapon, enemy_cell=(1, 0), **me_kwargs):
        fight = builder.make_fight(
            me=builder.entity(weapons=[weapon], cell=(0, 0), **me_kwargs),
            enemies=[builder.entity(life=100, max_life=100, cell=enemy_cell)],
        )
        install(fight)
        fight.me.setWeapon(weapon)
        return fight

    def test_out_of_range_is_refused_without_spending_tp(self):
        weapon = damage_weapon(10, cost=1, max_range=2)
        fight = self._fight_with_weapon(weapon, enemy_cell=(5, 0))
        enemy = fight.getNearestEnemy()
        tp_before = fight.me.tp

        result = fight.me.useWeapon(enemy)

        self.assertEqual(result, FightClass.Use.INVALID_POSITION)
        self.assertEqual(fight.me.tp, tp_before)
        self.assertEqual(enemy.life, 100)

    def test_min_range_is_refused(self):
        weapon = damage_weapon(10, cost=1, min_range=3, max_range=5)
        fight = self._fight_with_weapon(weapon, enemy_cell=(2, 0))
        enemy = fight.getNearestEnemy()
        tp_before = fight.me.tp

        result = fight.me.useWeapon(enemy)

        self.assertEqual(result, FightClass.Use.INVALID_POSITION)
        self.assertEqual(fight.me.tp, tp_before)

    def test_not_enough_tp_is_refused(self):
        weapon = damage_weapon(10, cost=20, max_range=10)
        fight = self._fight_with_weapon(weapon, enemy_cell=(1, 0), tp=10)
        enemy = fight.getNearestEnemy()
        tp_before = fight.me.tp

        result = fight.me.useWeapon(enemy)

        self.assertEqual(result, FightClass.Use.NOT_ENOUGH_TP)
        self.assertEqual(fight.me.tp, tp_before)
        self.assertEqual(enemy.life, 100)

    def test_max_uses_per_turn_is_respected(self):
        weapon = damage_weapon(10, cost=1, max_range=10, max_uses=1)
        fight = self._fight_with_weapon(weapon)
        enemy = fight.getNearestEnemy()
        tp_before = fight.me.tp

        first = fight.me.useWeapon(enemy)
        # Après une utilisation, le premier tir a coûté 1 PT.
        self.assertEqual(first, FightClass.Use.SUCCESS)
        self.assertEqual(fight.me.tp, tp_before - 1)
        self.assertEqual(fight.me.itemUses(weapon), 1)

        second = fight.me.useWeapon(enemy)

        self.assertEqual(second, FightClass.Use.MAX_USES)
        self.assertEqual(fight.me.tp, tp_before - 1)
        self.assertEqual(enemy.life, 90)

        fight.next_turn()
        self.assertEqual(fight.me.itemUses(weapon), 0)
        self.assertEqual(fight.me.tp, fight.me.maxTP)


class MovementTest(MockSdkTestCase):
    def test_move_toward_spends_mp_and_gets_closer(self):
        fight = builder.make_fight(
            me=builder.entity(cell=(0, 0), mp=10, max_mp=10),
            enemies=[builder.entity(cell=(5, 0))],
        )
        install(fight)
        enemy = fight.getNearestEnemy()

        spent = fight.me.moveToward(enemy)

        # De (0,0) à (4,0) : 4 cases, on s'arrête à distance 1.
        self.assertEqual(spent, 4)
        self.assertEqual(fight.me.mp, 6)
        self.assertEqual((fight.me.cell.x, fight.me.cell.y), (4, 0))
        self.assertEqual(fight.me.distance(enemy), 1)


class TargetSelectionTest(MockSdkTestCase):
    def test_nearest_enemy_is_the_closest_one(self):
        fight = builder.make_fight(
            me=builder.entity(cell=(0, 0)),
            enemies=[
                builder.entity(name="loin", cell=(6, 0)),
                builder.entity(name="proche", cell=(2, 0)),
            ],
        )
        install(fight)

        nearest = fight.getNearestEnemy()

        self.assertEqual(nearest.name, "proche")
        self.assertEqual(fight.enemies[0].name, "loin")
        self.assertEqual(fight.getEnemiesCount(), 2)


if __name__ == "__main__":
    unittest.main()
