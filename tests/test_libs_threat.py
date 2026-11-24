"""Tests du modèle de menace et du plan de placement (libs/threat_lib.py).

Le modèle répond à deux questions :
  - à quelle portée l'ennemi peut-il me frapper (après son déplacement) ?
  - où me placer pour garder l'initiative quand je ne peux pas le toucher ?
"""

import unittest

import support

import libs.threat_lib as threat_lib
from leekwars_api import builder, install


def _damage_chip(name="fireBall", range_=4, damage=12):
    """Puce offensive : sert à tester la prise en compte des puces."""
    return builder.chip(
        name,
        cost=1,
        min_range=0,
        max_range=range_,
        features=[
            builder.feature(
                builder.Effect.DAMAGE,
                builder.Effect.Target.ENEMIES,
                damage,
                damage,
            )
        ],
    )


def _long_weapon(range_=10, damage=10, cost=1):
    """Arme de longue portée (pour tester le plan de placement)."""
    return builder.weapon(
        "longbow",
        cost=cost,
        min_range=0,
        max_range=range_,
        features=[
            builder.feature(
                builder.Effect.DAMAGE,
                builder.Effect.Target.ENEMIES,
                damage,
                damage,
            )
        ],
    )


class ThreatModelTest(unittest.TestCase):
    def _fight(self, me=None, enemies=None):
        fight = support.make_fight(me=me, enemies=enemies)
        install(fight)
        return fight

    def test_enemy_threat_adds_their_movement_to_their_weapon_range(self):
        fight = self._fight(
            me=builder.entity(cell=(0, 0), weapons=[support.rifle(range_=3)]),
            enemies=[
                builder.entity(cell=(5, 0), weapon=support.pistol(range_=1),
                               max_mp=6)
            ],
        )
        threat = threat_lib.enemy_threat(fight.enemies[0])

        self.assertEqual(threat["weapon"], 1)
        self.assertEqual(threat["move"], 6)
        # rayon de menace : portée + déplacement
        self.assertEqual(threat["reach"], 7)

    def test_enemy_threat_includes_the_offensive_chips(self):
        fight = self._fight(
            me=builder.entity(cell=(0, 0), weapons=[support.rifle(range_=3)]),
            enemies=[
                builder.entity(cell=(5, 0), weapon=support.pistol(range_=1),
                               chips=[_damage_chip(range_=4)], max_mp=2)
            ],
        )
        threat = threat_lib.enemy_threat(fight.enemies[0])

        self.assertEqual(threat["weapon"], 1)
        self.assertEqual(threat["chips"], 4)
        # la puce offensive est plus longue que l'arme : elle fait la zone
        self.assertEqual(threat["range"], 4)
        self.assertEqual(threat["reach"], 6)

    def test_my_reach_is_the_longest_weapon_i_can_afford(self):
        fight = self._fight(
            me=builder.entity(
                cell=(0, 0), tp=3, max_tp=3,
                weapons=[support.pistol(range_=1, cost=1),
                         support.rifle(range_=3, cost=3)],
            ),
            enemies=[builder.entity(cell=(5, 0))],
        )

        # le fusil coûte 3 PT + 1 PT d'équipement : il ne rentre pas dans
        # le budget de 3 PT -> seul le pistolet compte.
        self.assertEqual(threat_lib.my_reach(fight.me), 1)
        fight.me.tp = 10
        self.assertEqual(threat_lib.my_reach(fight.me), 3)

    def test_kite_distance_is_out_of_the_enemy_reach(self):
        # ma portée (10) permet de tirer depuis la zone sûre : on s'y
        # place (portée 1 + 6 PM = 7, marge 1 -> 8).
        fight = self._fight(
            me=builder.entity(cell=(0, 0),
                              weapons=[_long_weapon(range_=10)]),
            enemies=[
                builder.entity(cell=(5, 0), weapon=support.pistol(range_=1),
                               max_mp=6)
            ],
        )
        distance, threat = threat_lib.kite_distance(fight.me, fight.enemies[0])

        # portée 1 + 6 PM = 7 -> on se place à 8 cases
        self.assertEqual(distance, 8)
        self.assertEqual(threat["reach"], 7)
        self.assertEqual(threat["safe"], 8)

    def test_kite_distance_never_exceeds_my_own_range(self):
        # Cas limite du match nul : la zone sûre (8) est hors de ma portée
        # (3). Se garer là-bas interdirait tout tir : si l'adversaire ne
        # bouge pas, le combat finit en nul. On engage donc à portée de
        # tir.
        fight = self._fight(
            me=builder.entity(cell=(0, 0), weapons=[support.rifle(range_=3)]),
            enemies=[
                builder.entity(cell=(5, 0), weapon=support.pistol(range_=1),
                               max_mp=6)
            ],
        )
        distance, threat = threat_lib.kite_distance(fight.me, fight.enemies[0])

        self.assertEqual(threat["safe"], 8)
        self.assertEqual(distance, 3)
        self.assertLessEqual(distance, threat_lib.my_reach(fight.me))

    def test_kite_is_refused_when_the_enemy_outranges_me(self):
        # rester hors de sa portée condamnerait le combat : on reste
        # offensif.
        fight = self._fight(
            me=builder.entity(cell=(0, 0), weapons=[support.pistol(range_=1)]),
            enemies=[
                builder.entity(cell=(5, 0), weapon=support.rifle(range_=3),
                               max_mp=6)
            ],
        )
        distance, _ = threat_lib.kite_distance(fight.me, fight.enemies[0])

        self.assertIsNone(distance)

    def test_kite_is_refused_without_a_weapon(self):
        fight = self._fight(
            me=builder.entity(cell=(0, 0), weapons=[support.rifle(range_=3)]),
            enemies=[builder.entity(cell=(5, 0), max_mp=6)],
        )
        distance, _ = threat_lib.kite_distance(fight.me, fight.enemies[0])

        self.assertIsNone(distance)

    def test_kite_is_refused_against_several_enemies(self):
        # le modèle de menace (un disque autour de l'ennemi) ne vaut que
        # dans un 1c1.
        fight = self._fight(
            me=builder.entity(cell=(0, 0), weapons=[support.rifle(range_=3)]),
            enemies=[
                builder.entity(cell=(5, 0), weapon=support.pistol(range_=1),
                               max_mp=6),
                builder.entity(cell=(0, 5), weapon=support.pistol(range_=1),
                               max_mp=6),
            ],
        )
        distance, _ = threat_lib.kite_distance(fight.me, fight.enemies[0])

        self.assertIsNone(distance)

    def test_in_reach_accounts_for_their_movement(self):
        close = self._fight(
            me=builder.entity(cell=(0, 0), weapons=[support.rifle(range_=3)]),
            enemies=[
                builder.entity(cell=(5, 0), weapon=support.pistol(range_=1),
                               max_mp=6)
            ],
        )
        # distance 5 : hors de sa portée (1), mais il peut se rapprocher de
        # 6 cases et me toucher.
        self.assertTrue(threat_lib.in_reach(close.enemies[0], close.me))

        far = self._fight(
            me=builder.entity(cell=(0, 0), weapons=[support.rifle(range_=3)]),
            enemies=[
                builder.entity(cell=(8, 0), weapon=support.pistol(range_=1),
                               max_mp=6)
            ],
        )
        # à 8 cases, même son déplacement ne lui permet pas de m'atteindre
        self.assertFalse(threat_lib.in_reach(far.enemies[0], far.me))


if __name__ == "__main__":
    unittest.main()
