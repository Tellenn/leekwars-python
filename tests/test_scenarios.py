"""Tests de bout en bout : `ai.turn()` sur des scénarios de combat.

Ces tests vérifient le comportement observable de l'IA (PV, TP, PM,
journal), pas les détails internes du moteur de décision.
"""

import unittest

import support

from leekwars_api import builder

import libs.decision_lib as decision_lib


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
        ai = support.load_ai(fight)

        ai.turn()

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
        ai = support.load_ai(fight)

        ai.turn()

        # l'IA s'est rapprochée (le journal le confirme), puis a tiré ;
        # elle replie ensuite en fuyant, donc on ne compare pas la distance
        # finale.
        self.assertTrue(any("moving closer" in line for line in fight.logs))
        self.assertLess(fight.enemies[0].life, 100)

    def test_ai_heals_only_when_it_cannot_deal_more_damage(self):
        # Soin de 40 PV pour 1 PT, mais l'arme ne fait que 1 dégât par
        # tir : on ne peut pas faire autant de dégâts que de soin, donc on
        # soigne.
        fight = support.make_fight(
            me=builder.entity(
                life=10, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=1, cost=1)],
                chips=[support.heal_chip(amount=40, cost=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        ai = support.load_ai(fight)

        ai.turn()

        self.assertEqual(fight.me.life, 50)
        heal_index = next(i for i, line in enumerate(fight.logs)
                          if "Heal: " in line)
        shot_index = next(i for i, line in enumerate(fight.logs)
                          if "Shot #" in line)
        self.assertLess(heal_index, shot_index)

    def test_ai_does_not_heal_before_shooting(self):
        # Le même soin de 40 PV, mais l'arme fait 10 dégâts par tir (90
        # de dégâts par tour) : mieux vaut frapper que soigner. Le soin
        # peut encore être joué à la fin du tour avec les PT restants,
        # quand il ne reste plus assez de dégâts à faire.
        fight = support.make_fight(
            me=builder.entity(
                life=10, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
                chips=[support.heal_chip(amount=40, cost=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        ai = support.load_ai(fight)

        ai.turn()

        self.assertLess(fight.enemies[0].life, 100)
        shot_index = next(i for i, line in enumerate(fight.logs)
                          if "Shot #" in line)
        heal_index = next(i for i, line in enumerate(fight.logs)
                          if "Heal: " in line)
        self.assertLess(shot_index, heal_index)

    def test_ai_heals_to_save_its_life(self):
        # L'ennemi a frappé 30 PV : il nous en reste 10, le soin (40 PV)
        # nous sauve, il passe avant tout.
        fight = support.make_fight(
            me=builder.entity(
                life=40, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
                chips=[support.heal_chip(amount=40, cost=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        ai = support.load_ai(fight)
        me = fight.me
        decision_lib.begin_turn(me)
        decision_lib.end_turn(me)
        me.take_damage(30)  # l'ennemi nous a frappé
        decision_lib.begin_turn(me)

        ai.turn()

        self.assertEqual(fight.me.life, 50)
        self.assertTrue(any("(sauve la mort)" in line
                            for line in fight.logs))

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
        ai = support.load_ai(fight)

        ai.turn()

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
        ai = support.load_ai(fight)

        ai.turn()

        self.assertTrue(any("Profitability:" in line
                            for line in fight.logs))
        self.assertTrue(any("Kepo_solo | strength" in line for line in fight.logs))

    def test_ai_tries_to_break_the_line_of_sight_at_the_end_of_the_turn(self):
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        ai = support.load_ai(fight)
        ai.HIDE_AFTER_ATTACK = True

        ai.turn()

        # La fuite consomme des PM (l'IA s'est déplacée pour casser la vue).
        self.assertLess(fight.me.mp, 10)

    def test_ai_uses_a_damage_chip_against_the_enemy(self):
        # une puce à dégâts doit viser l'ennemi (sinon elle vise la case du
        # lanceur et ne touche personne)
        damage_chip = builder.chip(
            "fireBall",
            cost=1,
            min_range=0,
            max_range=3,
            features=[builder.feature(
                Effect.DAMAGE,
                Effect.Target.ENEMIES,
                12, 12,
            )],
        )
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=1, cost=3)],
                chips=[damage_chip],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        ai = support.load_ai(fight)

        ai.turn()

        # la puce (12 dégâts pour 1 PT) est plus rentable que l'arme
        # (1 dégât pour 3 PT) -> elle est utilisée sur l'ennemi
        self.assertLessEqual(fight.enemies[0].life, 88)
        self.assertTrue(any("Chip: " in line for line in fight.logs))

    def test_ai_casts_the_strength_buff_before_shooting(self):
        # Build force : le buff de force part en premier, il amplifie tous
        # les tirs du tour.
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                strength=100, cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
                chips=[support.strength_chip(amount=100, cost=1)],
            ),
            enemies=[builder.entity(life=500, max_life=500, cell=(1, 0))],
        )
        ai = support.load_ai(fight)

        ai.turn()

        buff_index = next(i for i, line in enumerate(fight.logs)
                          if "Buff: " in line)
        shot_index = next(i for i, line in enumerate(fight.logs)
                          if "Shot #" in line)
        self.assertLess(buff_index, shot_index)
        # la force augmentée est prise en compte dans les tirs suivants
        self.assertEqual(fight.me.strength, 200)

    def test_ai_does_not_cast_a_strength_buff_that_would_replace_the_shots(self):
        # 1 PT de buff, 1 PT par tir : le buff supprimerait tous les tirs.
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=2, max_tp=2, mp=10, max_mp=10,
                strength=100, cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
                chips=[support.strength_chip(amount=100, cost=1)],
            ),
            enemies=[builder.entity(life=500, max_life=500, cell=(1, 0))],
        )
        ai = support.load_ai(fight)

        ai.turn()

        self.assertEqual(fight.me.strength, 100)
        self.assertFalse(any("Buff: " in line
                             for line in fight.logs))

    def test_ai_casts_the_protein_chip_even_if_it_costs_a_shot(self):
        # Puce "Protéines" : +80-100 force pendant 2 tours, 3 PT.
        # Le buff nous fait perdre un tir AU TOUR, mais il amplifie aussi
        # les tirs du tour suivant : l'IA doit le jouer.
        fight = support.make_fight(
            me=builder.entity(
                life=175, max_life=175, tp=10, max_tp=10, mp=3, max_mp=3,
                strength=110, cell=(0, 0),
                weapons=[support.pistol(damage=17, cost=3, range_=7)],
                chips=[support.protein_chip()],
            ),
            enemies=[builder.entity(life=600, max_life=600, cell=(3, 0))],
        )
        ai = support.load_ai(fight)

        ai.turn()

        # le buff est passé (force augmentée) et il est passé AVANT les tirs
        self.assertGreater(fight.me.strength, 110)
        buff_index = next(i for i, line in enumerate(fight.logs)
                           if "Buff: " in line)
        shot_index = next(i for i, line in enumerate(fight.logs)
                          if "Shot #" in line)
        self.assertLess(buff_index, shot_index)

    def test_ai_does_not_cast_a_one_turn_strength_buff_that_costs_a_shot(self):
        # Même situation, mais un buff d'un seul tour : il n'amplifie que
        # les tirs du tour, il ne vaut pas le tir perdu.
        fight = support.make_fight(
            me=builder.entity(
                life=175, max_life=175, tp=10, max_tp=10, mp=3, max_mp=3,
                strength=110, cell=(0, 0),
                weapons=[support.pistol(damage=17, cost=3, range_=7)],
                chips=[support.protein_chip(turns=1)],
            ),
            enemies=[builder.entity(life=600, max_life=600, cell=(3, 0))],
        )
        ai = support.load_ai(fight)

        ai.turn()

        self.assertEqual(fight.me.strength, 110)
        self.assertFalse(any("Buff: " in line
                             for line in fight.logs))

    def test_ai_does_not_play_a_chip_that_is_on_cooldown(self):
        # La puce "Protéines" a 3 tours de cooldown : le moteur la refuse
        # (INVALID_COOLDOWN), l'IA ne doit pas tenter de la jouer.
        chip = support.protein_chip()
        chip.currentCooldown = 2
        fight = support.make_fight(
            me=builder.entity(
                life=175, max_life=175, tp=10, max_tp=10, mp=3, max_mp=3,
                strength=110, cell=(0, 0),
                weapons=[support.pistol(damage=17, cost=3, range_=7)],
                chips=[chip],
            ),
            enemies=[builder.entity(life=600, max_life=600, cell=(3, 0))],
        )
        ai = support.load_ai(fight)

        ai.turn()

        self.assertEqual(fight.me.strength, 110)
        self.assertFalse(any("Buff: " in line
                             for line in fight.logs))
        self.assertFalse(any("refused" in line
                             for line in fight.logs))

    def test_ai_uses_a_heal_chip_with_the_game_target_mask(self):
        # Le bandage du catalogue a le masque 31 (il contient le bit
        # ENNEMIS) : l'IA doit quand même le voir comme un soin.
        fight = support.make_fight(
            me=builder.entity(
                life=40, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=3)],
                chips=[support.game_heal_chip(amount=25, cost=2)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        ai = support.load_ai(fight)

        ai.turn()

        self.assertEqual(fight.me.life, 65)  # 40 + 25 PV de soin
        self.assertTrue(any("Heal: " in line for line in fight.logs))

    def test_ai_can_stay_in_range_instead_of_fleeing(self):
        # Kepo_solo est un DPS brut : la fuite de fin de tour est optionnelle
        # (HIDE_AFTER_ATTACK).
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(1, 0))],
        )
        ai = support.load_ai(fight)
        ai.HIDE_AFTER_ATTACK = False

        ai.turn()

        # aucune fuite : les PM sont restés intacts
        self.assertEqual(fight.me.mp, 10)

    def test_turn_without_enemy_is_a_no_op(self):
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(damage=10, cost=1)],
            ),
            enemies=[],
        )
        ai = support.load_ai(fight)

        ai.turn()

        self.assertTrue(any("No enemy" in line for line in fight.logs))
        self.assertEqual(fight.me.tp, 10)


class KitingScenarioTest(unittest.TestCase):
    """Positionnement « kiting » : hors de la portée de l'ennemi (1c1)."""

    def test_ai_engages_instead_of_camping_out_of_the_enemy_reach(self):
        # Ma portée (3) domine celle de l'ennemi (1) : sa zone de menace
        # est portée + ses 6 PM = 7 cases. Mais la zone sûre (8 cases) est
        # HORS de ma portée : m'y parquer interdirait tout tir (match nul
        # si l'adversaire ne bouge pas). On engage donc à portée de tir.
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(5, 5),
                weapons=[support.rifle(range_=3, damage=30, cost=3)],
            ),
            enemies=[
                builder.entity(life=100, max_life=100, cell=(5, 9),
                               weapon=support.pistol(range_=1), max_mp=6)
            ],
        )
        ai = support.load_ai(fight)

        ai.turn()

        # le plan de placement annonce la distance 3 (et non 8)
        self.assertTrue(any("target distance 3" in line
                            for line in fight.logs))
        # on a engagé : l'ennemi est touché
        self.assertLess(fight.enemies[0].life, 100)

    def test_ai_stays_out_of_the_enemy_reach_when_its_range_allows_it(self):
        # Ma portée (10) domine la zone sûre (portée 1 + 6 PM + marge = 8) :
        # je me place à 8 cases, hors de sa portée, et je tire quand même.
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.rifle(range_=10, damage=30, cost=3)],
            ),
            enemies=[
                builder.entity(life=100, max_life=100, cell=(11, 0),
                               weapon=support.pistol(range_=1), max_mp=6)
            ],
        )
        ai = support.load_ai(fight)

        ai.turn()

        distance = fight.me.cell.distance(fight.enemies[0].cell)
        self.assertEqual(distance, 8)
        # hors de sa portée : il ne m'a pas touché, et j'ai tiré
        self.assertLess(fight.enemies[0].life, 100)
        self.assertTrue(any("Kiting:" in line for line in fight.logs))
        # la fuite de fin de tour est inutile (hors de sa portée) : les PM
        # restants prouvent qu'elle n'a pas eu lieu (3 PM pour se placer).
        self.assertEqual(fight.me.mp, 7)

    def test_ai_hits_the_enemy_from_out_of_its_reach(self):
        # Zone de menace : portée 1 + 1 PM = 2 -> distance sûre 3, et ma
        # portée est 3 : je me place à 3 et je tire.
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(5, 5),
                weapons=[support.rifle(range_=3, damage=30, cost=3)],
            ),
            enemies=[
                builder.entity(life=100, max_life=100, cell=(5, 9),
                               weapon=support.pistol(range_=1), max_mp=1)
            ],
        )
        ai = support.load_ai(fight)

        ai.turn()

        distance = fight.me.cell.distance(fight.enemies[0].cell)
        self.assertEqual(distance, 3)
        self.assertLess(fight.enemies[0].life, 100)

    def test_ai_closes_in_when_the_enemy_outranges_it(self):
        # Sa portée (3) domine la mienne (1) : rester hors de sa portée
        # condamnerait le combat, on reste offensif.
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(5, 5),
                weapons=[support.pistol(range_=1, damage=10, cost=1)],
            ),
            enemies=[
                builder.entity(life=100, max_life=100, cell=(5, 9),
                               weapon=support.rifle(range_=3), max_mp=1)
            ],
        )
        ai = support.load_ai(fight)

        ai.turn()

        self.assertFalse(any("Kiting:" in line for line in fight.logs))
        self.assertTrue(any("moving closer" in line for line in fight.logs))
        self.assertLess(fight.enemies[0].life, 100)

    def test_ai_does_not_kite_against_several_enemies(self):
        # Le modèle de menace ne vaut qu'en 1c1.
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(5, 5),
                weapons=[support.rifle(range_=3, damage=30, cost=3)],
            ),
            enemies=[
                builder.entity(life=100, max_life=100, cell=(5, 9),
                               weapon=support.pistol(range_=1), max_mp=6),
                builder.entity(life=100, max_life=100, cell=(5, 1),
                               weapon=support.pistol(range_=1), max_mp=6),
            ],
        )
        ai = support.load_ai(fight)

        ai.turn()

        self.assertFalse(any("Kiting:" in line for line in fight.logs))
        self.assertTrue(any("moving closer" in line for line in fight.logs))


class MultiWeaponScenarioTest(unittest.TestCase):
    """Scénarios de bout en bout avec deux armes équipées."""

    def test_ai_switches_to_the_long_weapon_and_shoots(self):
        # Le pistolet (portée 1) ne peut pas toucher la cible (à 4 cases) :
        # l'IA doit prendre le fusil (portée 5) et tirer.
        pistol = support.pistol(range_=1, damage=10, cost=1)
        rifle = support.rifle(range_=5, damage=30, cost=3)
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[pistol, rifle],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(4, 0))],
        )
        ai = support.load_ai(fight)
        fight.me.setWeapon(pistol)

        ai.turn()

        self.assertIs(fight.me.weapon, rifle)
        self.assertTrue(any("Switch:" in line for line in fight.logs))
        self.assertLess(fight.enemies[0].life, 100)

    def test_ai_starts_with_a_weapon_that_can_hit(self):
        # La machine gun est plus rentable mais ne tire qu'en ligne : on
        # commence par le pistolet, qui peut toucher la cible.
        machine_gun = support.line_weapon(range_=6, damage=30, cost=1)
        pistol = support.pistol(range_=6, damage=10, cost=1)
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[machine_gun, pistol],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(3, 3))],
        )
        ai = support.load_ai(fight)

        ai.turn()

        self.assertIs(fight.me.weapon, pistol)
        self.assertTrue(any("can hit" in line for line in fight.logs))

    def test_ai_aligns_itself_to_shoot_a_line_weapon(self):
        # La machine gun « ne peut tirer qu'en ligne » : l'IA doit se
        # placer sur la ligne de la cible avant de tirer.
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.line_weapon(range_=6, damage=30, cost=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(3, 3))],
        )
        ai = support.load_ai(fight)

        ai.turn()

        # l'IA s'est alignée (ou s'est rapprochée) et a tiré
        self.assertTrue(any("Aligning" in line for line in fight.logs))
        self.assertLess(fight.enemies[0].life, 100)

    def test_ai_does_not_hide_when_it_could_not_shoot(self):
        # Se cacher sans avoir tiré garantit qu'on ne pourra plus tirer
        # du tout : l'IA garde sa position d'attaque.
        fight = support.make_fight(
            me=builder.entity(
                life=100, max_life=100, tp=10, max_tp=10, mp=10, max_mp=10,
                cell=(0, 0),
                weapons=[support.pistol(range_=1, damage=10, cost=1)],
            ),
            enemies=[builder.entity(life=100, max_life=100, cell=(4, 0),
                                    weapon=support.pistol(range_=1), max_mp=6)],
        )
        ai = support.load_ai(fight)
        ai.HIDE_AFTER_ATTACK = True

        ai.turn()

        self.assertFalse(any("Hidden after" in line for line in fight.logs))


if __name__ == "__main__":
    unittest.main()
