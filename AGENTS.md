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
| **Code de l'IA** | `main.py`, `libs/` | ✅ oui — c'est ce que le moteur exécute |
| **Outillage local** | `leekwars_api/`, `tests/`, `tools/`, `docs/` | ❌ non — local uniquement |

### Invariants (à ne jamais enfreindre)

1. **Aucun import local-only dans le code de l'IA.**
   `main.py` et `libs/*` ne doivent jamais importer `leekwars_api`, `pytest`,
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
4. **Le point d'entrée reste `main.py` à la racine**, avec une fonction
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
make dist        # assemble dist/leekwars/ (main.py + libs/) pour l'import site
make docs-sync   # rafraîchit docs/encyclopedia/ depuis le site Leek Wars
```

Les tests n'utilisent **que** `unittest` (stdlib) : ils sont exécutables
avec `python3 -m unittest` comme avec `pytest` si celui-ci est installé.
Aucune installation réseau n'est nécessaire pour `make test`.

---

## 3. Architecture du code de l'IA

```
main.py                 point d'entrée : turn() →/logique
libs/constants_lib.py   constantes de jeu (types d'effets, groupes, CRITICAL_FACTOR)
libs/analysis_lib.py    parsing d'équipement → dégâts/soins/buffs attendus
libs/decision_lib.py    options possibles, scoring value/TP, exécution du plan
libs/equipment_lib.py   choix de l'arme de départ
libs/logs_lib.py        écriture dans le journal de combat (Debug.log)
```

Flux d'un tour (`main.turn()`) :

1. `Fight.getNearestEnemy()` — pas d'ennemi → sortie.
2. `equipment_lib.equip_starting_weapon()` — équipe la meilleure arme
   (ratio dégâts/PT) si aucune n'est en main.
3. `decision_lib.attack()` — boucle : on **re-score** toutes les options à
   chaque itération (les PV, les PT et les boucliers changent), on exécute la
   meilleure (attaque / soin / buff), on mesure les dégâts réels vs
   attendus.
4. Si rien n'était à portée : `me.moveToward(enemy)` puis on rejoue le
   calcul (la rentabilité change avec la distance).
5. `decision_lib.hide()` — on tente de casser la ligne de vue.

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

import main             # main.py lit Fight.me au niveau module
main.turn()
```

Points d'attention :

- `install()` **avant** `import main` (ou `importlib.reload(main)` si le
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
                                      builder.Effect.DAMAGE,
                                      builder.Effect.Target.ENEMIES,
                                      10, 10)])]),
            enemies=[builder.entity(life=20, max_life=20, cell=(1, 0))],
        )
        install(fight)
        main = importlib.import_module("main")
        importlib.reload(main)

        main.turn()

        self.assertEqual(fight.enemies[0].life, 0)
```

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
Stubs officiels de l'API : `docs/leekwars-api.d.ts`.

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

---

## 7. Contraintes Leek Wars (à respecter)

- **Langage** : Python **3.12** (GraalPy), fichiers `.py`. Un seul point
  d'entrée : la fonction `turn()`.
- **Le corps du module est évalué UNE SEULE FOIS** (variables de module
  persistantes), puis **le moteur rejoue `turn()` à chaque tour**. →
  Ne pas appeler `turn()` à la fin de `main.py` (tir en double au tour 1).
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
  limités → `make dist` ne dépose que `main.py` + `libs/`.
- **Arborescence git** : l'éditeur Leek Wars est un dépôt git (clone, pull,
  push, commit, branches) → le dépôt GitHub peut être importé tel quel.
  Attention : **l'IA doit vivre dans un dossier**, pas à la racine du dépôt
  importé → cloner le dépôt dans un dossier, ou pointer l'IA sur le
  sous-dossier qui contient `main.py`.
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
| 1 | `libs/logs_lib.py` vs import `libs.log_lib` : le code importait un module inexistant (`ImportError` sur le site) | `libs/decision_lib.py` | corrigé (import unifié sur `libs.logs_lib`) |
| 2 | `analysis_lib.expected_damage()` lit le global `Fight.me` au lieu de l'entité passée → non testable, faux si l'entité ≠ `me` | `libs/analysis_lib.py` | à corriger |
| 3 | `HEAL_TYPES` ignore `Effect.RAW_HEAL` (57) | `libs/constants_lib.py` | à corriger |
| 4 | `LIFE_DAMAGE` = % des PV **du lanceur** (traité comme un montant plat) | `libs/analysis_lib.py` | à corriger |
| 5 | `NOVA_DAMAGE` retire des **PV maximum** (traité comme des dégâts plats sur les PV courants) | `libs/analysis_lib.py` | à corriger |
| 6 | `SCIENCE_AMPLIFIED` incomplet : il manque `BUFF_AGILITY`, `BUFF_RESISTANCE`, `BUFF_WISDOM` | `libs/constants_lib.py` | à corriger |
| 7 | Le vol de vie (sagesse) n'est pas modélisé dans les dégâts attendus | `libs/analysis_lib.py` | à décider |
| 8 | `buff_value()` : hypothèse « la puissance ajoute des dégâts plats par tir » (à confirmer en jeu) | `libs/decision_lib.py` | hypothèse assumée |
| 9 | `expected_damage` n'exclut pas la partie « flat » du multiplicateur force/crit : correct pour `DAMAGE`, à vérifier pour `LIFE_DAMAGE` | `libs/analysis_lib.py` | à corriger |
| 10 | `main.py` appelait `turn()` à la fin du module : le moteur rejoue déjà `turn()` chaque tour → tir en double au tour 1 | `main.py` | corrigé (appel retiré) — **à confirmer au premier import sur le site** |
| 11 | `main.py` n'est pas un nom imposé par la plateforme (le moteur exécute le fichier `aiPath` de l'IA) : c'est une convention de ce dépôt | `main.py` | à documenter |

---

## 9. Workflow de livraison

1. Modifier le code de l'IA (`main.py`, `libs/`).
2. `make test` — la suite doit passer (aucun test cassé, aucun test
   supprimé pour faire passer).
3. Si la modification touche une formule : mettre à jour le snapshot
   (`make docs-sync`) et le tableau §8.
4. Commit : message en français, préfixe `feat:` / `fix:` / `test:` /
   `docs:` / `refactor:`. Un commit = une intention.
5. `make dist` puis copier `dist/leekwars/` dans l'éditeur Leek Wars (ou
   re-cloner le dépôt via le panneau git de l'éditeur).
6. Tester dans l'arène du site et lire le journal de combat
   (`Debug.log` → rapport de fin de combat) pour confronter les dégâts
   attendus aux dégâts réels.

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
