# AGENTS.md — Guide de travail pour les agents (et les humains) sur ce dépôt

> Dépôt de l'IA **Leek Wars** écrite en Python.
> L'IA est **importée dans l'éditeur Leek Wars** (arbre de fichiers git du site)
> et s'exécute dans le bac à sable du moteur de jeu.
> Ici, on développe **hors site** : on rejoue le SDK du jeu avec un mock
> local pour tester la logique de décision.

---

## 1. Deux zones, jamais mélangées

| Zone | Dossiers | Déployé sur le site ? |
|---|---|---|
| **Code de l'IA** | `Kepo_solo.py`, `libs/` | ✅ oui — c'est ce que le moteur exécute |
| **Outillage local** | `leekwars_api/`, `tests/`, `tools/`, `docs/` | ❌ non — local uniquement |

### Invariants (à ne jamais enfreindre)

1. **Aucun import local-only dans le code de l'IA.**
   `Kepo_solo.py` et `libs/*` ne doivent jamais importer `leekwars_api`, `pytest`,
   `unittest`, ni quoi que ce soit d'autre que la stdlib autorisée par le
   bac à sable Leek Wars.
   → `python3 tools/build_dist.py` échoue si la règle est violée.
2. **Pas de module standard « système » dans le code de l'IA.**
   Le bac à sable bloque disque/réseau : `os`, `sys`, `subprocess`, `socket`,
   `pathlib`, `urllib`, `importlib` sont interdits (liste dans
   `tools/build_dist.py`). Seuls les modules **internes au projet**
   (`libs.*`) sont importables en plus de la stdlib pure.
3. **Pas de `print()`** dans le code de l'IA : le journal de combat passe par
   `libs.logs_lib.log()` (→ `Debug.log`). `print()` fonctionne sur le site
   mais n'est pas lisible dans le rapport de fin de combat de la même façon.
4. **Le point d'entrée reste `Kepo_solo.py` à la racine**, avec une fonction
   `turn()`. Le corps du module est évalué **une seule fois** (les variables
   de module persistent d'un tour à l'autre), `turn()` est rejoué à chaque
   tour.
5. **Toute modification d'une formule de jeu doit être**
   (a) justifiée par une page de l'encyclopédie (voir §6),
   (b) couverte par un test,
   (c) signalée dans le tableau « Écarts connus » (§8) jusqu'à correction.
6. **Comments et docstrings en français**, code et identifiants en anglais
   (snake_case). Les noms d'API Leek Wars restent verbatim
   (`useWeapon`, `relativeShield`, …).

---

## 2. Commandes

```bash
make test        # python3 -m unittest discover -s tests -v  (zéro dépendance)
make lint        # ruff check .            (optionnel : pip install -e '.[dev]')
make typecheck   # pyright                 (optionnel)
make check       # test + lint + typecheck
make dist        # assemble dist/leekwars/ (Kepo_solo.py + libs/) pour l'import site
make docs-sync   # rafraîchit docs/encyclopedia/ depuis le site Leek Wars
```

Les tests n'utilisent **que** `unittest` (stdlib) : ils sont exécutables
avec `python3 -m unittest` comme avec `pytest` si celui-ci est installé.
Aucune installation réseau n'est nécessaire pour `make test`.

---

## 3. Architecture du code de l'IA

```
Kepo_solo.py          point d'entrée : turn() →/logique
libs/constants_lib.py   constantes de jeu (types d'effets, groupes, CRITICAL_FACTOR)
libs/analysis_lib.py    parsing d'équipement → dégâts/soins/buffs attendus
libs/decision_lib.py    options possibles, scoring value/TP, exécution du plan
libs/equipment_lib.py   choix de l'arme de départ
libs/logs_lib.py        écriture dans le journal de combat (Debug.log)
libs/threat_lib.py      portée ennemie (arme + PM) → zone de menace, plan de placement
```

### Profil de jeu : DPS brut

L'IA de Kepo est un **dps brut** : le build est centré sur la **force**
(dégâts), la protection viendra plus tard (résistance / sagesse en stats).

Conséquences sur le code :

- le score de décision est dominé par les **dégâts attendus** (force + crits
  − boucliers ennemi) ;
- la **valeur d'une attaque** est celle du *tour* : (dégâts + vol de vie) par
  tir × **nombre de tirs réellement possibles** (`weapon_uses()` : le plafond
  `maxUses` du moteur et les PT disponibles), et son score est cette valeur
  rapportée aux PT **réellement dépensés** (équipement + tirs) ;
- un **soin** n'est choisi que si on **ne peut pas faire autant de
  dégâts** : la comparaison se fait sur les **valeurs**, pas sur les
  rapports (30 de dégâts valent mieux que 25 de soin, même si le soin est
  moins cher en PT). Le soin ne passe donc pas devant un tir, et il ne
  reste jouable qu'avec les PT qui ne permettent plus de tirer (ou s'il
  **sauve notre mort** : `decision_lib.heal_saves_life()` → `MANDATORY`) ;
- le **buff part AVANT les tirs** (`decision_lib.buff_plan()`) : il
  multiplie tous les tirs du tour et des tours suivants. Sa valeur
  (`decision_lib.buff_gain()`) est l'**écart de PV restants entre la
  branche « buffée » et la branche « sans buff »**, simulées sur
  l'horizon du buff ;
- **une cible faible se tue, elle ne se buff pas** : si l'ennemi meurt
  dans les deux branches, la valeur du buff est 0 (il ne serait qu'un tir
  perdu) ; le buff n'est lancé que s'il rapproche la mort de l'ennemi ;
- l'**horizon du buff** est sa durée (`parts["buff_turns"]`) : la puce
  « Protéines » (+80-100 force, 2 tours) continue d'amplifier les tirs du
  tour suivant. Un buff de N tours agit pendant le tour où il est joué
  **et les N-1 tours suivants** (fr/Effets : il disparaît au début du
  N-ième tour suivant) ;
- **un buff déjà joué n'est pas rejoué** tant que son effet est actif
  (`decision_lib.buff_still_active()`) : il est **relancé** quand la puce
  est de nouveau disponible (cooldown expiré) et que le plan le juge à
  nouveau rentable ;
- le **buff « un tour avant »** (`decision_lib.prep_buff()`) : quand on
  n'a pas pu tirer (l'ennemi est hors de portée), nos PT sont inutilisés ;
  on lance alors le buff s'il est **plus rentable que d'attendre
  l'ouverture du tour suivant** (cette fois-ci le buff ne couvre qu'un
  tour de tir au lieu de deux) ;
- une **puce en cooldown** (`Chip.currentCooldown`) n'est pas proposée : le
  moteur la refuse (`Fight.Use.INVALID_COOLDOWN`) ;
- la **classification d'un effet** repose sur son *type*, pas sur son masque
  de cibles : le catalogue utilise le masque 31 pour les soins comme pour les
  attaques, un masque 30 pour les buffs sur soi ;
- la **fuite de fin de tour** est optionnelle : `HIDE_AFTER_ATTACK` dans
  `Kepo_solo.py`. `False` (défaut) = DPS pur, on garde le tempo offensif ;
  `True` = comportement « shoot and hide ». Un test verrouille les deux
  comportements ;
- les **puces de bouclier** sont modélisées et jouées en **ouverture de
  tour** (`decision_lib.shield_plan()`) : le bouclier n'est pas un « ratio »,
  c'est de la survie. Un build force (Kepo) n'a aucune protection, donc
  l'armure est posée **avant les tirs dès qu'elle est prête** (plus de
  cooldown), même si son rapport valeur/PT est moins bon que celui d'un
  tir — sauf si l'on peut tuer l'ennemi : autant le finir dans ce cas.
  - **le bouclier absolu bloque un montant par COUP** (fr/Résistance :
    `Final = Base * (1 - BouclierRelatif/100) - BouclierAbsolu`, appliqué
    à chaque coup) : sa valeur dépend donc du nombre de coups que
    l'ennemi nous inflige — `maxUses` × effets de dégâts de son arme
    (`threat_lib.hits_per_turn()`). Exemple : le Casque (+15, 2 tours)
    contre un ennemi au pistolet (4 coups/tour) bloque 60 PV par tour,
    soit 120 PV sur ses deux tours ;
  - la **valeur** du bouclier = les dégâts qu'il empêche pendant toute sa
    durée (`decision_lib.shield_value()`), sur la même échelle « dégâts »
    que les armes. Les dégâts de l'ennemi ne sont pas modélisés : ils sont
    **mesurés** d'un tour à l'autre (`decision_lib.begin_turn()` compare
    nos PV de la fin du tour précédent à nos PV actuels) ;
  - un bouclier qui **évite notre mort** passe avant tout (`MANDATORY`) ;
    un bouclier inutile (l'ennemi ne fait presque pas de dégâts, ou on
    peut le tuer) est laissé de côté : on garde le tempo offensif ;
  - exception : si le bouclier nous laisserait **sans aucun tir**
    (`decision_lib.can_still_shoot()`), on ne le joue que s'il sauve
    notre mort ;
  - **armure « un tour avant »** (`decision_lib.prep_shield()`) : quand on
    ne peut pas tirer mais que l'ennemi va nous atteindre au tour suivant
    (il est dans sa zone de menace), on pose le bouclier tout de suite,
    pour encaisser son premier coup protégé. C'est l'équivalent du
    « buff un tour avant » pour l'armure. L'armure d'ouverture ne joue ce
    rôle que si l'on **peut** tirer (on va encaisser des coups) ;
- la **portée de l'ennemi est modélisée** (`libs/threat_lib.py`) : sa zone
  de menace est le disque de rayon `portée de son arme + ses PM` centré sur
  sa case. Quand on ne peut pas le toucher, on se place **hors de cette
  zone** : il ne pourra pas nous toucher même après son déplacement, et on
  le touche au tour suivant (on garde l'initiative). Ce plan n'existe que
  si **notre portée domine la sienne** — sinon rester hors de sa portée
  condamnerait le combat, et l'IA reste offensive (rapprochement simple).
  Le modèle ne vaut qu'en **1c1** (`threat_lib.single_enemy()`).

Flux d'un tour (`ai.turn()`) :

1. `Fight.getNearestEnemy()` — pas d'ennemi → sortie.
2. `decision_lib.begin_turn()` — mesure des dégâts reçus au tour précédent.
3. `equipment_lib.equip_starting_weapon()` — équipe la meilleure arme
   (ratio dégâts/PT) si aucune n'est en main.
4. `decision_lib.attack()` — **armure d'ouverture d'abord** (le bouclier
   est de la survie, pas un ratio : il est posé avant les tirs dès qu'il
   est prêt), puis **buff d'ouverture** (s'il est rentable), puis boucle :
   on **re-score** toutes les options à chaque itération (les PV, les PT
   et les boucliers changent), on exécute la meilleure (attaque / soin /
   buff / bouclier), on mesure les dégâts réels vs attendus.
5. Si rien n'était à portée : `decision_lib.approach()` — le plan dépend
   de ce qui bloque (`decision_lib.firing_blocker()`) :
   - **trop près** (portée minimale) : on recule jusqu'à la case de tir ;
   - **pas aligné** (arme « en ligne ») : on se place sur la ligne de la
     cible (`moveTowardLine`) ;
   - **ligne de vue coupée** : on se rapproche ;
   - **trop loin** : on se rapproche de la case de tir ; en 1c1 on se
     place hors de la zone de menace de l'ennemi
     (`threat_lib.kite_distance()`), sinon on se rapproche simplement ;
   puis on rejoue le calcul (la rentabilité change avec la distance).
6. Si on n'a toujours pas pu tirer : `decision_lib.prep_shield()` puis
   `decision_lib.prep_buff()` — armure « un tour avant » (l'ennemi va nous
   frapper au tour suivant : on pose le bouclier maintenant) puis buff
   « un tour avant » (les PT sont inutilisés, le tour suivant sera
   amplifié) s'il bat l'attente de l'ouverture du tour suivant.
7. `decision_lib.hide()` — **seulement si `HIDE_AFTER_ATTACK`** (par défaut
   on ne fuit pas : Kepo est un DPS). La fuite est **sautee** si l'ennemi
   ne peut pas nous atteindre (hors de sa zone de menace) : elle ne ferait
   que perdre nos PM et l'initiative.
8. `decision_lib.end_turn()` — mémorise nos PV (base de la mesure du tour
   suivant).

### Politique de journal

Le rapport de combat est lu après coup : il ne doit pas être noyé.

| Bloc | Fréquence | Contenu |
|---|---|---|
| identité | **une fois par combat** | nom de l'IA, force/agilité/sagesse/science, multiplicateur de dégâts, inventaire (effets parsés), équipement ignoré |
| état | chaque tour | PV de l'ennemi, boucliers, PV manquants, **notre propre bouclier** (`shield R/A`) |
| rentabilité | chaque tour | une ligne : `objet valeur/PT=score` par option encore jouable — pour une arme, la **valeur du tour** (tirs possibles × dégâts) et les PT **réellement dépensés** (équipement + tirs, plafonnés par `maxUses`) ; pour un buff, le gain estimé sur sa **durée** |
| actions | chaque action | une ligne : tir (dégâts réels **vs dégâts attendus hors vol de vie**), refus du moteur nommé (`refused (MAX_USES)`), soin, buff (avec la force avant/après), bouclier, changement d'arme | ⚠️ la distance d'un tir qui **tue** la cible est journalisée après sa mort (sa case a changé) : elle ne reflète plus la portée |
| ouverture | chaque tour qui le mérite | `Opening shield:` (armure posée avant les tirs : tours de survie gagnés, dégâts bloqués, `sauve la mort` si elle évite la mort) et `Opening buff:` (buff de force joué avant les tirs) |
| positionnement | chaque repositionnement | portée ennemie + zone de menace, distance visée, distance obtenue (`Kiting:` / `Position:`) |

Mécanique : `libs/logs_lib.log_once(clé, message)` n'écrit qu'une fois par
combat (réarmé automatiquement quand le compteur de tours repart de zéro ;
`logs_lib.reset()` le force dans les tests). Le nom affiché vient de
`libs/logs_lib.AI_NAME` — à aligner avec le nom du fichier d'entrée.

### Pré-requis de tir (multi-arme)

Une arme ne vaut que si elle peut **toucher** la cible maintenant
(`analysis_lib.can_hit()`) :

1. **la portée** : `minRange <= Cell.distance() <= maxRange` — la distance
   du moteur est `|dx| + |dy|` (une diagonale de 2 cases vaut 4) ;
2. **la ligne de vue** : seulement si l'objet l'exige (`Item.needsLos`) ;
3. **la contrainte de visée** (`Item.launchType`) : une arme `LINE` ne
   tire que sur sa ligne ou sa colonne, une arme `DIAGONAL` qu'en
   diagonale.

Le choix de l'arme du tour suit ces règles :

- chaque arme équipée est une option (`decision_lib.build_options()`) ;
  l'arme en main ne coûte rien, les autres coûtent **1 PT**
  (`setWeapon`) ;
- une option hors de portée / non alignée vaut **0** : on ne propose
  jamais un tir que le moteur refusera ;
- le score est `valeur / PT` (le changement d'arme est inclus dans le
  ratio) ;
- après un changement d'arme, le coût des autres armes est remis à jour
  (`refresh_switch_flags()`) — les ré-équiper coûte de nouveau 1 PT ;
- si le moteur refuse le changement d'arme, l'IA **ne tire pas** avec
  l'arme qu'elle a en main (`decision_lib.execute()`).

**Échelle de décision** : tout est comparé en `valeur / PT`
(le coût d'équipement d'une arme — 1 PT — est inclus dans le ratio) :

- attaque : dégâts attendus / PT (force, crits, boucliers ennemi) ;
- soin : `min(soin attendu, PV manquants) / PT` (amplifié par la sagesse,
  l'overheal vaut 0) ;
- buff : dégâts supplémentaires estimés sur le reste du tour / PT.

---

## 4. Le mock du SDK (`leekwars_api/`)

Contrat complet : **`docs/leekwars_mock_spec.md`**.
Implémentation : `leekwars_api/` (constantes `Effect.Type/Target/Modifier`
avec les **valeurs numériques exactes** du jeu, `Cell`, `Entity`, `Me`,
`Weapon`, `Chip`, `Feature`, `Fight`, `Debug`, `Field`, `Registers`,
`System`, `builder`).

Principe : le moteur Leek Wars injecte `Fight`, `Effect`, `Debug`, … comme
globaux. Le mock fait pareil, en les installant dans `builtins` :

```python
from leekwars_api import builder, install

fight = builder.make_fight(
    me=builder.entity(strength=100, agility=50, life=100, cell=(0, 0)),
    enemies=[builder.entity(life=60, max_life=60, cell=(2, 0))],
)
install(fight)          # -> builtins.Fight, builtins.Effect, ...

import Kepo_solo        # Kepo_solo.py lit Fight.me au niveau module
ai.turn()
```

Points d'attention :

- `install()` **avant** `import Kepo_solo` (ou `importlib.reload(ai)` si le
  module a déjà été importé : `me` y est figé au niveau module).
- Le mock applique les **vraies formules** du jeu (force, crit, boucliers,
  sagesse, science, TP/PM, portées, ligne de vue) : les tests valident la
  même arithmétique que le serveur.
- L'aléa passe par `fight.rng` (`random.Random(seed)`) → tests
  déterministes. `make_fight(seed=…)` fixe la graine.
- `fight.logs` contient tout ce qui est passé par `Debug.log` → assertions
  possibles sur le journal de l'IA.

---

## 5. Écrire un test

```python
import importlib
import unittest

from leekwars_api import builder, install


class ScenarioTest(unittest.TestCase):
    def test_ai_kills_the_enemy(self):
        fight = builder.make_fight(
            me=builder.entity(strength=100, life=100, cell=(0, 0),
                              weapons=[builder.weapon(
                                  "pistol", cost=1, max_range=1,
                                  features=[builder.feature(
                                      Effect.DAMAGE,
                                      Effect.Target.ENEMIES,
                                      10, 10)])]),
            enemies=[builder.entity(life=20, max_life=20, cell=(1, 0))],
        )
        install(fight)
        ai = importlib.import_module("Kepo_solo")
        importlib.reload(ai)

        ai.turn()

        self.assertEqual(fight.enemies[0].life, 0)
```

`Effect` est un **global** (installé dans `builtins` par le mock, comme le
fait le moteur du site) : on l'utilise sans import dans les tests.

Règles :

- Un test = un comportement observable (PV, PT, actions, journal).
- Préfère des **valeurs nommagees** (variables locales) à des nombres
  magiques : le test doit rester lisible quand les formules changent.
- Les formules du jeu se testent **dans le mock** ; les tests de `libs/`
  testent la **décision** de l'IA. Ne pas re-tester la règle du jeu dans
  `tests/test_libs_*.py`.

---

## 6. Formules de jeu (source de vérité)

Snapshots locaux : `docs/encyclopedia/*.md` (source : API du site,
`https://leekwars.com/api/encyclopedia/get/fr/<page>`).
Stubs officiels de l'API : `docs/leekwars-api.d.ts` (TypeScript) et
`stubs/__builtins__.pyi` (Python).
Récapitulatif de l'API Python : **`docs/leekwars-api-python.md`**.

| Effet | Formule | Source |
|---|---|---|
| Force | `DegatsFinaux = Base * (1 + Force / 100)` | `docs/encyclopedia/force.md` |
| Coup critique | `P = Agilité / 1000`, multiplicateur `1.3` | `docs/encyclopedia/agilite.md` |
| Boucliers | `Final = Base * (1 - BouclierRelatif/100) - BouclierAbsolu` (plancher 0) — **appliqué à chaque coup** : le bouclier absolu est retiré autant de fois que l'arme fait de coups | `docs/encyclopedia/resistance.md` |
| Ignorent les boucliers | poisons, renvoi de dégâts, dégâts nova | `docs/encyclopedia/resistance.md` |
| Sagesse | `SoinsFinaux = Base * (1 + Sagesse / 100)` (plafonné aux PV max) | `docs/encyclopedia/sagesse.md` |
| Vol de vie | `SoinsParVolDeVie = DegatsFinaux * Sagesse / 1000` | `docs/encyclopedia/vol_de_vie.md` |
| Science | amplifie les buffs `BUFF_*` (pas les `RAW_*`) | `docs/encyclopedia/effets.md` |
| Effets | 59 types + masques de cibles (`ENEMIES=1`, `ALLIES=2`, `CASTER=4`, `NON_SUMMONS=8`, `SUMMONS=16`) | `docs/encyclopedia/effets.md` |
| Armes : coût et plafond | `Item.cost` = PT par utilisation, `Item.maxUses` = utilisations **par tour** (compteur `Entity.itemUses()`), dégâts de base = `value1 + rand(0..value2)` | mesuré sur le moteur (combat de test #54910256 : pistol `cost=3`, `maxUses=4` → 4 tirs puis refus) |
| Puces : données et masques | `chip/get-all` : `value1`/`value2` → `Feature.minValue`/`maxValue` (= value1, value1+value2), `turns` = durée de l'effet, `cooldown` = tours de recharge, `effects[].id` = type d'effet (`Effect.Type`) | catalogue du site (`api/chip/get-all`) + journal de combat (le tiret affiche « damage: 15.0-20.0 », soit min/max) |
| Masques de cibles | 31 = ENNEMIS\|ALLIES\|CASTER\|NON_SUMMONS\|SUMMONS (armes, soins), 30 = ALLIES\|CASTER\|NON_SUMMONS\|SUMMONS (buffs sur soi), 26 = sans CASTER (buffs d'alliés) | catalogue du site (`api/chip/get-all`) |
| Puce « Protéines » (id 8) | `RAW_BUFF_STRENGTH` (38) 80-100, 2 tours, 3 PT, cooldown 3 — buff **brut** (pas amplifié par la science) | catalogue du site (`api/chip/get-all`) |
| Durée d'un buff | un buff de N tours agit pendant le tour où il est joué **et les N-1 tours suivants** (il disparaît au début du N-ième tour suivant) ; les effets perdent 1 tour au début du tour de leur lanceur | fr/Effets (« un boost de N tours disparaît au début du N-ième tour suivant de son lanceur ») |
| Érosion | les dégâts subis réduisent la **vie maximum** : 5 % des dégâts classiques, 10 % du poison, +10 % sur un coup critique ; les boucliers atténuent l'érosion | `docs/encyclopedia/erosion.md` |
| Ligne de vue | `Item.needsLos` : la plupart des armes l'exigent, 11 puces du catalogue frappent sans (trébuchet, étincelle, repiquage, picquant…) | `docs/leekwars-api-python.md` + données du jeu (`weapon/get-all`, `chip/get-all`) |
| Contrainte de visée | `Item.launchType` : `LINE` = 1 (« ne peut tirer qu'en ligne » → la cible doit être sur la même **ligne ou colonne** que le tireur), `DIAGONAL` = 2 (cible en diagonale), `CIRCLE` = 7 (aucune contrainte) | fr/Armes (« la machine gun ne peut tirer qu'en ligne », « la bazooka ne marche qu'en diagonale ») + mesuré sur le moteur (combat #54913377 : une cible en diagonale exacte fait refuser le tir d'une arme LINE) |
| Distance | le moteur compte la portée avec `Cell.distance()` : **|dx| + |dy|** (une diagonale de 2 cases vaut 4) — c'est la métrique à utiliser pour toute comparaison de portée | mesuré sur le moteur : #54913368 (deux cases décalées de (19, -6) sont à 25 cases) ; #54913442 (tir refusé en (7, -2) — manhattan 9, chebyshev 7 — malgré une vue dégagée ; tirs acceptés en (5, 0) et (-3, -4), manhattan ≤ 7) — le **mock est aligné** sur cette métrique (cf. §8, #27) |

---

## 7. Contraintes Leek Wars (à respecter)

- **Langage** : Python **3.12** (GraalPy), fichiers `.py`. Un seul point
  d'entrée : la fonction `turn()`.
- **Le corps du module est évalué UNE SEULE FOIS** (variables de module
  persistantes), puis **le moteur rejoue `turn()` à chaque tour**. →
  Ne pas appeler `turn()` à la fin de `Kepo_solo.py` (tir en double au tour 1).
  Si le module ne définit pas `turn()`, c'est le module entier qui est
  rejoué chaque tour.
- **Imports** : seuls les fichiers de l'IA sont accessibles ; un module est
  cherché dans le dossier du fichier d'entrée, puis à la racine. Les dossiers
  de package doivent contenir `__init__.py` ; pas de tiret dans les noms de
  fichiers ; pas d'import circulaire.
- **Bac à sable** : pas de disque, pas de réseau, pas de threads ; horloge
  figée ; `random` pré-initialisé par la graine du combat ; budget
  d'opérations et de mémoire **par tour** (`System.maxOperations`) : un
  dépassement interrompt le tour (limite « statements » ≈ 20 M, profondeur
  d'AST 5000).
- **Taille des fichiers** : `System.fileRead` est plafonné à **64 KiB par
  fichier** et **256 KiB au total** → garder les modules de l'IA petits
  (`make dist` affiche les tailles).
- **Quotas de l'éditeur** : taille totale et nombre de fichiers de l'IA sont
  limités → `make dist` ne dépose que `Kepo_solo.py` + `libs/`.
- **Arborescence git** : l'éditeur Leek Wars est un dépôt git (clone, pull,
  push, commit, branches) → le dépôt GitHub peut être importé tel quel.
  Attention : **l'IA doit vivre dans un dossier**, pas à la racine du dépôt
  importé → cloner le dépôt dans un dossier, ou pointer l'IA sur le
  sous-dossier qui contient `Kepo_solo.py`.
  `make dist` reste utile pour copier un sous-ensemble à la main.
- **Multi-langages** : une IA peut être en Python, JS, TS ou LeekScript et
  combattre les IA des autres langages.

### Deux façons de tester en local

| Approche | Fidélité | Coût |
|---|---|---|
| **Mock `leekwars_api/`** (par défaut ici) | les formules du jeu sont appliquées, mais pas le moteur complet (pas d'IA adverse, pas de carte réelle) | faible |
| **Générateur officiel** (`leek-wars-generator`, Java/Docker) — rejoue une IA contre de vraies IA et de vraies cartes | maximale | élevé (Java 25 + Gradle) |

Le port Python communautaire `Traual/leekwars-generator-python` rejoue les
mêmes scénarios avec la même graine : utile pour confronter le mock au
moteur réel quand un résultat est suspect.

Mode d'emploi : **`docs/local-runner.md`** (scénario de duel prêt à l'emploi
dans `scenarios/duel.json`).

### Stubs de typage

- `stubs/__builtins__.pyi` : copie des stubs Python officiels (montés en
  `builtins` par l'éditeur) → `pyright` résout `Fight`, `Effect`, `Weapon`…
  en local. Configuré via `stubPath` dans `pyproject.toml`.
- `docs/leekwars-api.d.ts` : les stubs TypeScript officiels (mêmes
  signatures, en `.ts`), extraits du bundle de l'éditeur.

---

## 8. Écarts connus (à traiter, avec tests)

| # | Problème | Où | Statut |
|---|---|---|---|
| 1 | `libs/logs_lib.py` vs import `libs.log_lib` : le code importait un module inexistant (`ImportError` sur le site) | `libs/decision_lib.py` | **corrigé** (import unifié sur `libs.logs_lib`) |
| 2 | `analysis_lib.expected_damage()` lisait le global `Fight.me` au lieu de l'entité passée → non testable, faux si l'entité ≠ `me` | `libs/analysis_lib.py` | **corrigé** (paramètre `attacker`, défaut `Fight.me`) |
| 3 | `HEAL_TYPES` ignorait `Effect.RAW_HEAL` (57), qui n'est **pas** amplifié par la sagesse | `libs/constants_lib.py` | **corrigé** (bucket `heal_flat` séparé) |
| 4 | `LIFE_DAMAGE` = % des PV **du lanceur** (traité comme un montant plat) | `libs/analysis_lib.py` | **corrigé** (conversion au parsing, avec les PV max du lanceur) |
| 5 | `NOVA_DAMAGE` retire des **PV maximum** (traité comme des dégâts plats sur les PV courants) | `libs/analysis_lib.py` | **corrigé** (bucket `nova_raw`, amplifié par la science, ignore les boucliers) |
| 6 | `SCIENCE_AMPLIFIED` incomplet : il manquait `BUFF_AGILITY`, `BUFF_RESISTANCE`, `BUFF_WISDOM` | `libs/constants_lib.py` | **corrigé** |
| 7 | Le vol de vie (sagesse) n'était pas modélisé dans les dégâts attendus | `libs/analysis_lib.py` | **corrigé** (`expected_lifesteal`, ajouté à la valeur d'une attaque) |
| 8 | `buff_value()` : hypothèse « la puissance ajoute des dégâts plats par tir » (à confirmer en jeu) | `libs/decision_lib.py` | hypothèse assumée |
| 9 | `expected_damage` n'excluait pas la partie « flat » du multiplicateur force/crit | `libs/analysis_lib.py` | **corrigé** (le multiplicateur force/crit ne s'applique qu'à `amp_raw`) |
| 10 | `Kepo_solo.py` appelait `turn()` à la fin du module : le moteur rejoue déjà `turn()` chaque tour → tir en double au tour 1 | `Kepo_solo.py` | **corrigé** (appel retiré) — **à confirmer au premier import sur le site** |
| 11 | `Kepo_solo.py` n'est pas un nom imposé par la plateforme (le moteur exécute le fichier `aiPath` de l'IA) : c'est une convention de ce dépôt | `Kepo_solo.py` | documenté |
| 12 | `EFFECT_KILL` valait 0 dégât dans le modèle : l'IA ne choisissait jamais une arme d'exécution | `libs/analysis_lib.py` | **corrigé** (`kill` → la valeur vaut les PV restants de la cible) |
| 13 | Les actions dont le code de retour est négatif (`INVALID_POSITION`, `NOT_ENOUGH_TP`…) ne sont pas distinguées : l'IA suppose que l'action a réussi | `libs/decision_lib.py` | **corrigé** (le code de retour de `useWeapon`/`useChip` est lu : un refus est journalisé avec son nom et l'option est neutralisée pour le tour) |
| 14 | Le mock n'applique pas le « 5 % du montant retiré » sur les PV maximum (règle du jeu sur les dégâts) | `leekwars_api/fight.py` | **corrigé** (c'est l'érosion, voir #20) |
| 15 | `useChip(chip)` sans cible : une puce à dégâts visait la case du lanceur et ne touchait jamais l'ennemi | `libs/decision_lib.py` | **corrigé** (cible explicite : l'ennemi pour une puce à dégâts, le lanceur sinon) |
| 16 | Sur un build **force**, le buff de force devrait être lancé **avant** les tirs (il multiplie tous les tirs suivants) ; le scoring actuel le traite comme une option concurrente des attaques, sur un horizon d'un seul tour | `libs/decision_lib.py` | **corrigé** (`strength_buff_plan()` : le buff de force ouvre le tour s'il améliore le total de dégâts du tour) |
| 17 | La fuite de fin de tour (`HIDE_AFTER_ATTACK`) est désactivée par défaut : choix « DPS pur » | `Kepo_solo.py` | assumé — à réactiver si le build commence à lose des PV plus vite qu'il n'en inflige |
| 18 | Le plafond d'utilisations d'une arme par tour (`Item.maxUses`, compteur `Entity.itemUses()`) n'était pas modélisé : l'IA tentait une utilisation de trop (refusée par le moteur), laissait 8 à 11 TP inutilisés, surévaluait l'horizon du buff de force et classait mal les armes lentes | `libs/decision_lib.py`, `libs/equipment_lib.py` | **corrigé** (`weapon_uses()` : tirs possibles = `min(maxUses − itemUses, floor(TP/coût))` ; le score, l'horizon du buff et le choix de l'arme de départ l'utilisent) |
| 19 | Le « expected » affiché dans le journal des tirs mélange dégâts et **vol de vie** (sagesse 100 → +10 %) : le « gap » est biaisé du vol de vie | `libs/decision_lib.py` | **corrigé** (la ligne de tir compare les dégâts attendus hors vol de vie ; la ligne de rentabilité garde la valeur « dégâts + vol de vie ») |
| 20 | Le moteur **réduit les PV maximum** quand on perd de la vie (3000 → 2958 → 2918 → 2819 sur le combat de test) ; le mock gardait `maxLife` constant | `leekwars_api/fight.py` | **corrigé** (érosion : 5 % des dégâts subis, +10 % sur un coup critique, 10 % pour le poison — fr/Érosion) |
| 21 | Les boucliers du mock ne **expiraient jamais** (état permanent) alors que le moteur les porte sur des effets temporaires | `leekwars_api/fight.py` | **corrigé** (`_refresh_shields()` recalcule les boucliers depuis les effets actifs à chaque tour) |
| 22 | Les puces de bouclier étaient ignorées (« no damage, no buff, no heal ») : l'IA ne modélisait ni `RELATIVE_SHIELD` ni `ABSOLUTE_SHIELD` | `libs/analysis_lib.py`, `libs/decision_lib.py` | **corrigé** (parsing + `shield_value()` ; le bouclier est joué en ouverture de tour quand sa protection vaut au moins un tir) |
| 23 | L'IA ignorait la **ligne de vue** : elle tentait un tir que le moteur refusait (`INVALID_POSITION`) et perdait une action ; à l'inverse, les objets qui frappent **sans** ligne de vue (`needsLos = False`) doivent rester utilisables | `libs/analysis_lib.py` | **corrigé** (`in_range()` vérifie la ligne de vue seulement si l'objet l'exige) |
| 24 | L'IA ne modélisait pas la **portée de l'ennemi** : elle se rapprochait toujours (`moveToward`), donc elle entrait dans sa portée et le laissait tirer en premier | `libs/threat_lib.py`, `libs/decision_lib.py` | **corrigé** (`threat_lib` : zone de menace = portée de l'arme ennemie + ses PM ; `decision_lib.approach()` se place hors de cette zone en 1c1 quand notre portée domine la sienne) |
| 25 | La **fuite de fin de tour** partait même quand l'ennemi ne pouvait pas nous atteindre : elle jetait nos PM et annulait le positionnement « kiting » | `libs/decision_lib.py` | **corrigé** (`hide()` saute la fuite si l'ennemi est hors de sa zone de menace) |
| 26 | Hypothèses du modèle de menace : PM de l'ennemi = `maxMP` (remis à zéro à chaque tour), ligne de vue non modélisée, puces offensives ennemies prises en compte (hypothèse prudente) | `libs/threat_lib.py` | hypothèses assumées — à confronter à un combat de test |
| 27 | Le **mock** et le site ne mesurent pas les distances de la même façon : le mock compte les cases en chebyshev, le moteur compte une diagonale comme 2 cases (`2·min(dx,dy) + |dx−dy|`) → en local, l'IA peut croire à portée (ou hors de portée) d'une cible diagonale que le moteur traiterait autrement | `leekwars_api/rules.py`, `leekwars_api/cell.py` | **corrigé** — `Cell.distance()` (et `Field.distance`) utilisent la métrique du moteur (`|dx| + |dy|`, `RULES.range_distance`) ; le déplacement reste en chebyshev (`RULES.distance`, `Field.cellDistance`) — mesuré sur le moteur (combat #54913368) |
| 28 | La classification des effets d'un item reposait sur le **masque de cibles** : le catalogue du jeu utilise le masque 31 (ENNEMIS\|ALLIES\|CASTER\|…) pour les soins comme pour les attaques → le bandage du joueur était lu comme une attaque et la puce était ignorée (« Ignored (no damage, no buff, no heal, no shield) ») | `libs/analysis_lib.py` | **corrigé** — la classification se fait sur le *type* de l'effet, le masque ne sert plus qu'à savoir à QUI il s'applique (ennemi / soi) |
| 29 | Le buff de force n'était valorisé que sur le **tour courant** : un buff de plusieurs tours (puce « Protéines », +80-100 force pendant 2 tours) paraissait toujours non rentable (il fait perdre un tir) et n'était jamais joué | `libs/decision_lib.py` | **corrigé** — l'horizon est la durée du buff (`parts["buff_turns"]`), le gain est plafonné par les PV restants de l'ennemi |
| 30 | Les **cooldowns de puces** n'étaient pas modélisés : l'IA pouvait proposer une puce que le moteur refuse (`Fight.Use.INVALID_COOLDOWN`) et perdre son ouverture de tour | `libs/decision_lib.py`, `leekwars_api/fight.py` | **corrigé** — `Chip.currentCooldown` est lu, les puces en cooldown sont exclues des options ; le mock modélise le cooldown |
| 31 | Le **mock** touchait le lanceur avec ses propres attaques : le masque 31 du catalogue contient le bit CASTER, et le mock ajoutait le lanceur aux cibles de tout effet | `leekwars_api/fight.py` | **corrigé** — seuls les effets « sur soi » (soin, buff, bouclier) touchent le lanceur (mesuré sur le site : le tir du joueur ne le blesse pas) |
| 32 | Le **mock** ne rendait pas la stat d'un buff expiré (le +force restait acquis) | `leekwars_api/fight.py` | **corrigé** — les stats buffées sont recalculées à chaque tour depuis les effets actifs |
| 33 | Le **plan de buffs** était un calcul ad hoc par type de buff (la force avait un horizon sur la durée, la puissance et les TP non) et il comptait comme un gain les dégâts **au-delà de la mort** de l'ennemi : l'IA pouvait sacrifier un tir pour buff une cible qu'elle tuait sans lui | `libs/decision_lib.py` | **corrigé** — `buff_gain()` : la valeur d'un buff est l'écart de PV restants entre la branche « buffée » et la branche « sans buff » (horizon = la durée du buff) ; si l'ennemi meurt dans les deux branches, la valeur est 0 (une cible faible se tue) |
| 34 | Le buff n'était jamais joué quand l'IA **ne pouvait pas tirer** ce tour (l'ennemi hors de portée) : la décision de buff exigeait une attaque de référence à portée | `libs/decision_lib.py` | **corrigé** — `prep_buff()` : buff « un tour avant », joué seulement s'il bat l'attente de l'ouverture du tour suivant (comparaison sur le même horizon) |
| 35 | Un buff **sans cooldown** était rejoué à chaque tour, alors que son effet était encore actif (la force montait en escalier) | `libs/decision_lib.py` | **corrigé** — `buff_still_active()` : on suit les buffs joués (`_ACTIVE_BUFFS`) et on ne rejoue pas un buff dont l'effet court ; il est relancé quand la puce est de nouveau disponible |
| 36 | Hypothèses du plan de buffs : (a) le buff agit immédiatement et couvre le tour où il est joué **et** les N-1 tours suivants ; (b) au tour suivant on rejoue avec la même arme, les PT pleins et le compteur d'utilisations remis à zéro ; (c) l'ennemi se rapproche de `maxMP` cases par tour (modèle de menace) pour décider si un buff « un tour avant » sera utilisé ; (d) la puissance ajoute des dégâts plats par tir (hypothèse déjà assumée, cf. #8) | `libs/decision_lib.py` | hypothèses assumées — à confronter à un combat de test |
| 37 | Le buff de **PM** (`buff_mp`) n'est pas valorisé (il ne sert qu'au repositionnement) ; le buff de TP est valorisé comme des PT supplémentaires (tirs en plus) | `libs/decision_lib.py` | **partiel** (TP corrigé, PM à faire) |
| 38 | Le **plan de rapprochement** ne tient pas compte de la **ligne de vue** : `approach()` vise l'ennemi tout droit. Sur le combat de test #54913316, les deux poireaux (notre IA contre elle-même) sont restés 13 tours sans pouvoir tirer (ligne de vue coupée par le décor) : le rapprochement bute sur le mur et le combat dégénère en plants | `libs/decision_lib.py`, `libs/threat_lib.py` | **écart connu** — un plan de repositionnement « contourner l'obstacle » (ou au moins s'écarter quand la ligne de vue est coupée) reste à faire ; le mock n'a pas de décor, il ne peut pas le mettre en défaut |
| 39 | La **contrainte de visée** (`Item.launchType`) n'était pas modélisée : l'IA proposait des tirs que le moteur refusait (`INVALID_POSITION`) — la machine gun, le fusil à pompe, le gazeur et les lasers « ne peuvent tirer qu'en ligne », la bazooka et le neutrino « ne marchent qu'en diagonale » | `libs/analysis_lib.py`, `libs/threat_lib.py` | **corrigé** — `analysis_lib.can_hit()` (portée + ligne de vue + alignement) filtre les armes utilisables, `decision_lib.firing_blocker()` dit ce qui bloque, `decision_lib.align_move()` se place sur la ligne de la cible (`moveTowardLine`) ; mesuré sur le moteur (combat #54913377) |
| 40 | Le **coût du changement d'arme** n'était pas remis à jour après un `setWeapon` : l'IA croyait pouvoir ré-équiper gratuitement l'arme précédente (et aurait tiré avec l'arme en main en croyant tirer avec l'autre) | `libs/decision_lib.py` | **corrigé** — `refresh_switch_flags()` recalcule le coût (1 PT) de chaque arme après un changement ; `execute()` vérifie le retour de `setWeapon` et refuse de tirer si le changement est refusé |
| 41 | L'IA **se cachait même quand elle n'avait pas tiré** : en coupant la ligne de vue de la cible, elle s'interdisait tout tir ultérieur (combat #54913368 : 64 tours sans un seul tir) | `Kepo_solo.py`, `libs/decision_lib.py` | **corrigé** — la fuite (`HIDE_AFTER_ATTACK`) n'a lieu que si l'IA a réellement tiré |
| 42 | Le **plan de placement** ignorait la portée minimale et l'alignement : l'IA se parquait à une distance où aucune de ses armes ne pouvait toucher la cible, et ne cherchait pas à s'aligner | `libs/threat_lib.py`, `libs/decision_lib.py` | **corrigé** — fenêtres de tir par arme (`my_windows`), distance de tir (`firing_distance`), case de tir (`firing_cell`) ; reculer si l'ennemi est trop près, s'aligner sinon |
| 43 | L'armure (puce de bouclier) n'était jouée que si son **rapport valeur/PT** battait celui d'un tir : sur un build force sans aucune protection, l'IA restait sans bouclier jusqu'au dernier moment, et le bouclier pouvait être joué **après** des tirs (donc après avoir subi le coup) | `libs/decision_lib.py` | **corrigé** — `shield_plan()` : l'armure est jouée en **ouverture de tour**, avant les tirs, **dès qu'elle est prête** (plus de cooldown), sauf si l'on peut tuer l'ennemi ; `can_still_shoot()` interdit de se retrouver sans aucun tir (sauf si le bouclier sauve la mort) |
| 44 | Le **bouclier absolu** bloque un montant fixe **par coup**, mais le modèle le comptait **par tour** : la protection réelle d'une puce comme le Casque (+15) était sous-estimée d'autant de fois que l'ennemi nous frappait (pistolet : 4 coups/tour, machine gun : 9) | `libs/decision_lib.py`, `libs/threat_lib.py` | **corrigé** — `threat_lib.hits_per_turn()` (maxUses × effets de dégâts de l'arme adverse) et `shield_protection()` : la valeur du bouclier = les dégâts empêchés × la durée |
| 45 | La valeur d'un tour de survie reste approchée : `damage_per_turn()` estime le nombre de tirs par `TP / coût` sans tenir compte du plafond `maxUses`, et l'hypothèse « un dégât empêché = un dégât infligé » ne donne aucune valeur aux PV économisés quand le nombre de tours ne change pas | `libs/decision_lib.py` | hypothèse assumée — à confronter à un combat de test |
| 46 | L'armure n'était posée qu'**après** avoir encaissé le coup de l'ennemi : on ne pouvait pas s'armer avant le premier contact, quand l'ennemi approche hors de notre portée | `libs/decision_lib.py`, `Kepo_solo.py` | **corrigé** — `prep_shield()` : armure « un tour avant » (comme `prep_buff()` pour les buffs) : si on ne peut pas tirer et que l'ennemi est dans sa zone de menace, on pose le bouclier pour encaisser son prochain coup protégé ; l'armure d'ouverture ne joue ce rôle que si l'on peut tirer |
| 47 | Le rapport de combat ne montrait **pas notre propre bouclier** : impossible de vérifier après coup si un coup encaissé était protégé (ni de mesurer l'effet de l'armure) | `libs/decision_lib.py` | **corrigé** — la ligne d'état affiche `me X/Y HP (missing Z, shield R/A)` |
| 48 | Le **soin** était choisi sur son rapport `PV/PT` : un soin bon marché (27 PV pour 2 PT) pouvait voler la place d'un tir à 45 PV, alors que faire 30 de dégâts vaut mieux que 25 de soin | `libs/decision_lib.py` | **corrigé** — le soin n'est proposé que si on ne peut pas faire autant de dégâts que le soin vaut (comparaison sur les **valeurs**, plus sur les rapports) ; exception : le soin qui **sauve notre mort** passe avant tout (`MANDATORY`) |
| 49 | Le **bouclier absolu de la cible** était retiré **une fois par tir** au lieu d'**une fois par coup** : contre une cible avec 17 de bouclier, la machine gun (3 coups) était surestimée de 73 % (80 de dégâts au lieu de 46) — mesuré sur le moteur (combat #54914966 : 39 et 63 dégâts réels pour 80 attendus) | `libs/analysis_lib.py` | **corrigé** — `analyse_equipment()` garde un coup par effet de dégâts (`damage_hits`) et `hit_damage()` applique le bouclier à chaque coup (fr/Résistance) |

---

## 9. Workflow de livraison

1. Modifier le code de l'IA (`Kepo_solo.py`, `libs/`).
2. `make test` — la suite doit passer (aucun test cassé, aucun test
   supprimé pour faire passer).
3. Si la modification touche une formule : mettre à jour le snapshot
   (`make docs-sync`) et le tableau §8.
4. Commit : message en français, préfixe `feat:` / `fix:` / `test:` /
   `docs:` / `refactor:`. Un commit = une intention.
5. `make dist` puis copier `dist/leekwars/` dans l'éditeur Leek Wars (ou
   re-cloner le dépôt via le panneau git de l'éditeur).
   **Déploiement par git (le plus propre)** : `git push` sur GitHub, puis
   `git pull` côté site. L'API du site accepte la clé API pour le pull :
   `POST https://leekwars.com/api/git/pull` avec
   `{"folder": "github", "rebase": false}` → le pull peut donc être
   déclenché par l'agent, sans passer par l'éditeur. Attention :
   `git/status`, `git/remotes` et `git/diff` refusent en revanche la clé
   API (`wrong_token` : ils exigent la session web de l'éditeur). Le
   dossier `github/` du site est un clone du dépôt : y écrire des
   fichiers à la main (`ai/write`) laisse l'arbre git modifié et fait
   échouer le pull suivant — ne pas le faire, passer par le push.
6. **Vérification runtime — obligatoire après chaque implémentation.**
   Déployer le code (`make dist` + copie dans l'éditeur, ou synchronisation
   git du dépôt du site), puis **jouer un combat de test avec ce code
   déployé** et lire le journal de combat (`Debug.log` → rapport de fin de
   combat).
   - Via le MCP Leek Wars : `list_test_scenarios` →
     `start_test_fight({scenario_id, ai_id})` →
     `get_fight({fight_id, include_logs: true})`.
   - Ou dans l'arène de test du site (combat non classé).

   On vérifie qu'il n'y a **aucune erreur de runtime** :
   - l'IA démarre (« Booting up … ») et joue des tours ;
   - aucune exception dans le journal (le traceback y apparaît si le code
     lève : `AttributeError`, `IndexError`, import manquant…) ;
   - les lignes attendues sont présentes (état, rentabilité, actions) et
     pas de boucle « No usable option anymore » ;
   - les dégâts réels restent dans l'intervalle prévu par le modèle.

   Le mock ne remplace pas ce test : il n'applique ni les contraintes du
   bac à sable ni les règles du moteur. Un code qui passe `make test` mais
   plante sur le site n'est **pas** validé.
7. Confronter les dégâts attendus aux dégâts réels (journal du combat) et
   corriger le modèle si l'écart est systématique (pas du bruit de
   dés).

---

## 10. Glossaire

| Terme | Signification |
|---|---|
| PT / TP | points de tour : chaque action coûte des PT |
| PM / MP | points de mouvement : chaque case parcourue coûte 1 PM |
| Poireau | l'entité contrôlée par l'IA (`Fight.me`) |
| Bouclier relatif | réduit les dégâts d'un pourcentage |
| Bouclier absolu | réduit les dégâts d'un montant fixe |
| Vol de vie | part des dégâts convertie en soins (amplifié par la sagesse) |
| `libs/` | dossier des bibliothèques de l'IA (importées en `libs.xxx`) |
| Mock | implémentation locale du SDK du jeu, utilisée uniquement par les tests |
