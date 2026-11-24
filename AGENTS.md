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
- un **soin** n'est choisi que si son ratio `PV/PT` bat le ratio
  `dégâts/PT` de la meilleure attaque (le soin n'est pas une priorité) ;
- le **buff de force part AVANT les tirs** (`strength_buff_plan()`) : il
  multiplie tous les tirs du tour. Il n'est lancé que si le total de dégâts
  avec buff dépasse le total sans buff (le buff peut repousser un tir) ;
- la **fuite de fin de tour** est optionnelle : `HIDE_AFTER_ATTACK` dans
  `Kepo_solo.py`. `False` (défaut) = DPS pur, on garde le tempo offensif ;
  `True` = comportement « shoot and hide ». Un test verrouille les deux
  comportements ;
- les **puces de bouclier** sont modélisées mais restent marginales : la
  valeur d'un bouclier = les tours de survie qu'il achète, convertis en
  dégâts encore infligables (`decision_lib.shield_value()`). Les dégâts
  de l'ennemi ne sont pas modélisés : ils sont **mesurés** d'un tour à
  l'autre (`decision_lib.begin_turn()` compare nos PV de la fin du tour
  précédent à nos PV actuels). Un bouclier n'est joué que s'il évite la
  mort (`MANDATORY`) ou s'il achète un tour de survie alors qu'on perd le
  combat ; sinon il vaut 0 et l'IA garde le tempo offensif ;
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
4. `decision_lib.attack()` — **buff de force d'abord** (s'il est rentable),
   puis boucle : on **re-score** toutes les options à chaque itération (les
   PV, les PT et les boucliers changent), on exécute la meilleure (attaque /
   soin / buff / bouclier), on mesure les dégâts réels vs attendus.
5. Si rien n'était à portée : `decision_lib.approach()` — en 1c1 on se
   place hors de la zone de menace de l'ennemi (`threat_lib.kite_distance()`),
   sinon on se rapproche (`me.moveToward(enemy)`) ; puis on rejoue le
   calcul (la rentabilité change avec la distance).
6. `decision_lib.hide()` — **seulement si `HIDE_AFTER_ATTACK`** (par défaut
   on ne fuit pas : Kepo est un DPS). La fuite est **sautee** si l'ennemi
   ne peut pas nous atteindre (hors de sa zone de menace) : elle ne ferait
   que perdre nos PM et l'initiative.
7. `decision_lib.end_turn()` — mémorise nos PV (base de la mesure du tour
   suivant).

### Politique de journal

Le rapport de combat est lu après coup : il ne doit pas être noyé.

| Bloc | Fréquence | Contenu |
|---|---|---|
| identité | **une fois par combat** | nom de l'IA, force/agilité/sagesse/science, multiplicateur de dégâts, inventaire (effets parsés), équipement ignoré |
| état | chaque tour | PV de l'ennemi, boucliers, PV manquants |
| rentabilité | chaque tour | une ligne : `objet valeur/PT=score` par option encore jouable — pour une arme, la **valeur du tour** (tirs possibles × dégâts) et les PT **réellement dépensés** (équipement + tirs, plafonnés par `maxUses`) |
| actions | chaque action | une ligne : tir (dégâts réels **vs dégâts attendus hors vol de vie**), refus du moteur nommé (`refused (MAX_USES)`), soin, buff, bouclier, changement d'arme |
| positionnement | chaque repositionnement | portée ennemie + zone de menace, distance visée, distance obtenue (`Kiting:` / `Position:`) |

Mécanique : `libs/logs_lib.log_once(clé, message)` n'écrit qu'une fois par
combat (réarmé automatiquement quand le compteur de tours repart de zéro ;
`logs_lib.reset()` le force dans les tests). Le nom affiché vient de
`libs/logs_lib.AI_NAME` — à aligner avec le nom du fichier d'entrée.

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
| Boucliers | `Final = Base * (1 - BouclierRelatif/100) - BouclierAbsolu` (plancher 0) | `docs/encyclopedia/resistance.md` |
| Ignorent les boucliers | poisons, renvoi de dégâts, dégâts nova | `docs/encyclopedia/resistance.md` |
| Sagesse | `SoinsFinaux = Base * (1 + Sagesse / 100)` (plafonné aux PV max) | `docs/encyclopedia/sagesse.md` |
| Vol de vie | `SoinsParVolDeVie = DegatsFinaux * Sagesse / 1000` | `docs/encyclopedia/vol_de_vie.md` |
| Science | amplifie les buffs `BUFF_*` (pas les `RAW_*`) | `docs/encyclopedia/effets.md` |
| Effets | 59 types + masques de cibles (`ENEMIES=1`, `ALLIES=2`, `CASTER=4`, `NON_SUMMONS=8`, `SUMMONS=16`) | `docs/encyclopedia/effets.md` |
| Armes : coût et plafond | `Item.cost` = PT par utilisation, `Item.maxUses` = utilisations **par tour** (compteur `Entity.itemUses()`), dégâts de base = `value1 + rand(0..value2)` | mesuré sur le moteur (combat de test #54910256 : pistol `cost=3`, `maxUses=4` → 4 tirs puis refus) |
| Érosion | les dégâts subis réduisent la **vie maximum** : 5 % des dégâts classiques, 10 % du poison, +10 % sur un coup critique ; les boucliers atténuent l'érosion | `docs/encyclopedia/erosion.md` |
| Ligne de vue | `Item.needsLos` : la plupart des armes l'exigent, 11 puces du catalogue frappent sans (trébuchet, étincelle, repiquage, picquant…) | `docs/leekwars-api-python.md` + données du jeu (`weapon/get-all`, `chip/get-all`) |
| Distance | le moteur compte la portée avec `Cell.distance()` : **une diagonale vaut 2 cases** (`2·min(dx,dy) + |dx−dy|`) — c'est la métrique à utiliser pour toute comparaison de portée | mesuré sur le moteur (combat de test #54912618 : le fusil, portée 7, est accepté à distance 7 ; la puce, portée 5, est refusée) — **le mock utilise le chebyshev** : écart connu (cf. §8, #27) |

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
| 22 | Les puces de bouclier étaient ignorées (« no damage, no buff, no heal ») : l'IA ne modélisait ni `RELATIVE_SHIELD` ni `ABSOLUTE_SHIELD` | `libs/analysis_lib.py`, `libs/decision_lib.py` | **corrigé** (parsing + `shield_value()` ; le bouclier n'est joué que s'il évite la mort ou achète un tour de survie) |
| 23 | L'IA ignorait la **ligne de vue** : elle tentait un tir que le moteur refusait (`INVALID_POSITION`) et perdait une action ; à l'inverse, les objets qui frappent **sans** ligne de vue (`needsLos = False`) doivent rester utilisables | `libs/analysis_lib.py` | **corrigé** (`in_range()` vérifie la ligne de vue seulement si l'objet l'exige) |
| 24 | L'IA ne modélisait pas la **portée de l'ennemi** : elle se rapprochait toujours (`moveToward`), donc elle entrait dans sa portée et le laissait tirer en premier | `libs/threat_lib.py`, `libs/decision_lib.py` | **corrigé** (`threat_lib` : zone de menace = portée de l'arme ennemie + ses PM ; `decision_lib.approach()` se place hors de cette zone en 1c1 quand notre portée domine la sienne) |
| 25 | La **fuite de fin de tour** partait même quand l'ennemi ne pouvait pas nous atteindre : elle jetait nos PM et annulait le positionnement « kiting » | `libs/decision_lib.py` | **corrigé** (`hide()` saute la fuite si l'ennemi est hors de sa zone de menace) |
| 26 | Hypothèses du modèle de menace : PM de l'ennemi = `maxMP` (remis à zéro à chaque tour), ligne de vue non modélisée, puces offensives ennemies prises en compte (hypothèse prudente) | `libs/threat_lib.py` | hypothèses assumées — à confronter à un combat de test |
| 27 | Le **mock** et le site ne mesurent pas les distances de la même façon : le mock compte les cases en chebyshev, le moteur compte une diagonale comme 2 cases (`2·min(dx,dy) + |dx−dy|`) → en local, l'IA peut croire à portée (ou hors de portée) d'une cible diagonale que le moteur traiterait autrement | `leekwars_api/rules.py`, `leekwars_api/cell.py` | **écart connu** — le code de l'IA utilise toujours `Cell.distance()` (la métrique du moteur) ; aligner le mock sur le site reste à faire |

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
