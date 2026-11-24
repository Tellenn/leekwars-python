"""Tests du plan de buffs (`libs/decision_lib.py`).

Un buff est une puce qui augmente une stat (force, puissance, TP). Le plan
est jugé à l'aune de son effet observable : l'IA joue-t-elle la puce, quand,
et la force (ou les dégâts attendus) augmente-t-elle vraiment ?

Références du jeu (voir AGENTS.md §6) :
  - puce « Protéines » : +80-100 force brute pendant 2 tours, 3 PT,
    3 tours de cooldown ;
  - un buff de N tours agit le tour où il est joué et les N-1 suivants ;
  - degats = base * (1 + force / 100) -> 17 dégâts à 110 de force = 35,7.
"""

import unittest

import support

from leekwars_api import builder

#: Personnage type des scénarios de buff (AGENTS.md, profil DPS force).
BASE_STRENGTH = 110
WEAPON_DAMAGE = 17
WEAPON_COST = 3
WEAPON_RANGE = 7


def _make_battle(*, enemy_life, chip=None, mp=3, weapon=None,
                 enemy_cell=(3, 0), me_life=175):
    """Construit le scénario de référence : un poireau force face à une
    cible plus ou moins résistante, à portée de l'arme de test."""
    if chip is None:
        chip = support.protein_chip()
    if weapon is None:
        weapon = support.pistol(
            damage=WEAPON_DAMAGE, cost=WEAPON_COST, range_=WEAPON_RANGE)
    return support.make_fight(
        me=builder.entity(
            life=me_life, max_life=me_life, tp=10, max_tp=10,
            mp=mp, max_mp=mp, strength=BASE_STRENGTH, cell=(0, 0),
            weapons=[weapon], chips=[chip],
        ),
        enemies=[builder.entity(
            life=enemy_life, max_life=enemy_life, cell=enemy_cell)],
    )


def _buff_lines(logs):
    """Lignes de « Buff: » (buff effectivement joué).

    Attention : « Opening buff: » et « Prep buff: » ne contiennent pas
    « Buff: » (majuscule), donc ils ne polluent pas ce filtre.
    """
    return [line for line in logs if "Buff: " in line]


def _shot_lines(logs):
    return [line for line in logs if "Shot #" in line]


class BuffPlanTest(unittest.TestCase):
    """Comportement du plan de buffs, du plus simple au plus subtil."""

    def test_a_weak_target_is_not_buffed(self):
        """L'ennemi meurt au tour suivant dans les deux branches : le buff
        ne rapproche pas sa mort, il ne ferait que perdre un tir."""
        fight = _make_battle(enemy_life=150)
        ai = support.load_ai(fight)

        ai.turn()

        # Le buff ne rapproche pas la mort (l'ennemi meurt dans les deux
        # branches simulées) : aucun « Buff: » et la force reste de base.
        self.assertEqual(_buff_lines(fight.logs), [])
        self.assertEqual(fight.me.strength, BASE_STRENGTH)
        # Les tirs partent sans buff : 3 x (17 * 2,10) = 3 x 35,7.
        self.assertEqual(len(_shot_lines(fight.logs)), 3)
        self.assertAlmostEqual(fight.enemies[0].life, 150 - 3 * 35.7,
                               places=4)

    def test_a_resistant_target_gets_the_opening_buff_before_the_shots(self):
        """Face à une cible résistante, le buff ouvre le tour, avant les tirs."""
        fight = _make_battle(enemy_life=600)
        ai = support.load_ai(fight)

        ai.turn()

        self.assertTrue(_buff_lines(fight.logs))
        # Le buff d'ouverture est joué AVANT le premier tir.
        buff_index = next(i for i, line in enumerate(fight.logs)
                          if "Buff: " in line)
        shot_index = next(i for i, line in enumerate(fight.logs)
                          if "Shot #" in line)
        self.assertLess(buff_index, shot_index)
        # La force est bien augmentée par la puce.
        self.assertGreater(fight.me.strength, BASE_STRENGTH)
        # On pouvait tirer ce tour : pas de buff « un tour avant ».
        self.assertFalse(any("Prep buff: " in line for line in fight.logs))

    def test_the_protein_buff_still_boosts_the_next_turn(self):
        """« Protéines » dure 2 tours : la force reste buffée et les tirs
        du tour suivant sont amplifiés."""
        fight = _make_battle(enemy_life=600)
        ai = support.load_ai(fight)

        ai.turn()
        buffed_strength = fight.me.strength
        self.assertGreater(buffed_strength, BASE_STRENGTH)

        fight.next_turn()
        turn_two_start = len(fight.logs)
        ai.turn()
        turn_two_logs = fight.logs[turn_two_start:]

        # Le buff est encore actif : force inchangée, pas de nouvelle puce.
        self.assertEqual(fight.me.strength, buffed_strength)
        self.assertEqual(_buff_lines(turn_two_logs), [])
        # Les tirs du tour suivant sont amplifiés par la force buffée :
        # degats = 17 * (1 + force / 100).
        expected = WEAPON_DAMAGE * (1 + fight.me.strength / 100)
        shots = _shot_lines(turn_two_logs)
        self.assertTrue(shots)
        for line in shots:
            self.assertIn(f"expected {expected:.1f}", line)

    def test_the_buff_is_not_replayed_while_active_then_relaunched(self):
        """Sans cooldown, le buff n'est pas empilé : il est relancé quand
        son effet a expiré (et que la puce est disponible)."""
        fight = _make_battle(
            enemy_life=600, chip=support.protein_chip(cooldown=0))
        ai = support.load_ai(fight)

        ai.turn()
        buffed_strength = fight.me.strength
        self.assertGreater(buffed_strength, BASE_STRENGTH)
        self.assertEqual(len(_buff_lines(fight.logs)), 1)

        # Tour 2 : l'effet court encore -> pas de relance.
        fight.next_turn()
        turn_two_start = len(fight.logs)
        ai.turn()
        turn_two_logs = fight.logs[turn_two_start:]
        self.assertEqual(_buff_lines(turn_two_logs), [])
        self.assertEqual(fight.me.strength, buffed_strength)

        # Tour 3 : l'effet a expiré -> la force est revenue à sa base, la
        # puce est rejouable et le plan la juge encore rentable.
        fight.next_turn()
        turn_three_start = len(fight.logs)
        ai.turn()
        turn_three_logs = fight.logs[turn_three_start:]
        self.assertTrue(_buff_lines(turn_three_logs))
        self.assertGreater(fight.me.strength, BASE_STRENGTH)
        self.assertEqual(len(_buff_lines(fight.logs)), 2)

    def test_a_buff_one_turn_early_is_cast_when_it_beats_waiting(self):
        """Hors de portée, le buff est lancé « un tour avant » s'il est plus
        rentable que d'attendre l'ouverture du tour suivant."""
        # 1 PM : le déplacement est bloqué ; arme à 8 PT, portée 1 :
        # impossible de tirer ce tour.
        fight = _make_battle(
            enemy_life=600, mp=1, enemy_cell=(5, 0),
            weapon=support.pistol(damage=WEAPON_DAMAGE, cost=8, range_=1),
        )
        ai = support.load_ai(fight)

        ai.turn()

        self.assertTrue(any("Prep buff: " in line for line in fight.logs))
        self.assertTrue(_buff_lines(fight.logs))
        self.assertGreater(fight.me.strength, BASE_STRENGTH)
        # Aucun tir n'était possible : le buff consomme les PT autrement.
        self.assertEqual(_shot_lines(fight.logs), [])

    def test_waiting_is_better_than_an_early_buff_that_costs_no_shot(self):
        """Si le buff ne déplace aucun tir au tour suivant, mieux vaut
        attendre l'ouverture du tour suivant : pas de « Prep buff »."""
        # 1 PT seulement : le lancer maintenant ne coûte aucun tir au
        # tour suivant (il reste un tir dans les deux plans).
        fight = _make_battle(
            enemy_life=600, mp=1, enemy_cell=(5, 0),
            chip=support.protein_chip(cost=1, cooldown=0),
            weapon=support.pistol(damage=WEAPON_DAMAGE, cost=8, range_=1),
        )
        ai = support.load_ai(fight)

        ai.turn()

        self.assertFalse(any("Prep buff: " in line for line in fight.logs))
        self.assertEqual(_buff_lines(fight.logs), [])
        self.assertEqual(fight.me.strength, BASE_STRENGTH)

    def test_a_one_turn_buff_is_not_worth_the_shot_it_replaces(self):
        """Un buff d'un seul tour n'amplifie que le tour courant : il ne
        vaut pas le tir qu'il fait perdre."""
        fight = _make_battle(
            enemy_life=600, chip=support.protein_chip(turns=1))
        ai = support.load_ai(fight)

        ai.turn()

        self.assertEqual(_buff_lines(fight.logs), [])
        self.assertEqual(fight.me.strength, BASE_STRENGTH)

    def test_the_buff_is_not_replayed_while_the_chip_is_on_cooldown(self):
        """Même effet expiré, la puce en cooldown n'est pas rejouée ; elle
        l'est dès que le cooldown est écoulé."""
        fight = _make_battle(
            enemy_life=600, chip=support.protein_chip(cooldown=3))
        ai = support.load_ai(fight)

        # Tour 1 : le buff part.
        ai.turn()
        self.assertEqual(len(_buff_lines(fight.logs)), 1)
        self.assertGreater(fight.me.strength, BASE_STRENGTH)

        # Tour 2 : effet encore actif.
        fight.next_turn()
        turn_two_start = len(fight.logs)
        ai.turn()
        self.assertEqual(_buff_lines(fight.logs[turn_two_start:]), [])
        self.assertGreater(fight.me.strength, BASE_STRENGTH)

        # Tour 3 : effet expiré, mais la puce est encore en cooldown (1).
        fight.next_turn()
        turn_three_start = len(fight.logs)
        ai.turn()
        self.assertEqual(_buff_lines(fight.logs[turn_three_start:]), [])
        self.assertEqual(fight.me.strength, BASE_STRENGTH)
        self.assertEqual(len(_buff_lines(fight.logs)), 1)

        # Tour 4 : cooldown écoulé et buff toujours rentable -> relance.
        fight.next_turn()
        turn_four_start = len(fight.logs)
        ai.turn()
        self.assertTrue(_buff_lines(fight.logs[turn_four_start:]))
        self.assertGreater(fight.me.strength, BASE_STRENGTH)
        self.assertEqual(len(_buff_lines(fight.logs)), 2)


if __name__ == "__main__":
    unittest.main()
