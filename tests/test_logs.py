"""Tests de la politique de journalisation (`libs/logs_lib.py`)."""

import unittest

import support

from leekwars_api import builder, install

import libs.logs_lib as logs_lib


class LogOnceTest(unittest.TestCase):
    def setUp(self):
        self.fight = support.make_fight()
        install(self.fight)
        logs_lib.reset()

    def test_log_once_writes_only_the_first_time(self):
        logs_lib.log_once("key", "first")
        logs_lib.log_once("key", "second")

        self.assertEqual(len(self.fight.logs), 1)
        self.assertIn("first", self.fight.logs[0])

    def test_log_once_keys_are_independent(self):
        logs_lib.log_once("a", "A")
        logs_lib.log_once("b", "B")

        self.assertEqual(len(self.fight.logs), 2)

    def test_reset_rearms_the_once_blocks(self):
        logs_lib.log_once("key", "first")
        logs_lib.reset()
        logs_lib.log_once("key", "again")

        self.assertEqual(len(self.fight.logs), 2)

    def test_log_can_be_silenced(self):
        logs_lib.ENABLED = False
        try:
            logs_lib.log("nothing")
            logs_lib.log_once("key", "nothing")
        finally:
            logs_lib.ENABLED = True

        self.assertEqual(len(self.fight.logs), 0)


class LogPolicyTest(unittest.TestCase):
    """Politique de journal : l'en-tête une fois, le rapport à chaque tour."""

    def _fight(self):
        return support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                strength=100, cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
                chips=[support.heal_chip(amount=20, cost=2)],
            ),
            enemies=[builder.entity(life=500, max_life=500, cell=(1, 0))],
        )

    def test_header_is_written_once_and_report_every_turn(self):
        fight = self._fight()
        ai = support.load_ai(fight)

        ai.turn()
        ai.turn()

        headers = [line for line in fight.logs if "Kepo_solo | strength" in line]
        reports = [line for line in fight.logs if "Profitability:" in line]

        self.assertEqual(len(headers), 1)
        self.assertGreaterEqual(len(reports), 2)

    def test_the_report_stays_compact(self):
        fight = self._fight()
        ai = support.load_ai(fight)

        ai.turn()

        reports = [line for line in fight.logs if "Profitability:" in line]
        self.assertEqual(len(reports), 1)
        # une seule ligne, avec une entrée par option utilisable
        self.assertIn("pistol", reports[0])
        self.assertIn("bandage", reports[0])

    def test_the_items_breakdown_is_written_once(self):
        fight = self._fight()
        ai = support.load_ai(fight)

        ai.turn()
        ai.turn()

        items = [line for line in fight.logs if line.startswith("[AI] Items:")]
        self.assertEqual(len(items), 1)


if __name__ == "__main__":
    unittest.main()
