# Référence de l'API Python Leek Wars

Résumé opérationnel de l'API **Python** du site (Leek Wars 2.49+,
Python 3.12 sur GraalPy). Sources : article « Python » de l'encyclopédie,
documentation de l'API du site, stubs officiels (`docs/leekwars-api.d.ts`,
`stubs/__builtins__.pyi`) et le runtime du générateur open source
(`leek-wars-generator`).

## Règles de nommage (crucial)

- L'API est **100 % objet** : pas de fonction plate (`getNearestEnemy()` seul
  n'existe pas → `Fight.getNearestEnemy()`), pas de constante plate
  (`WEAPON_PISTOL` → `Weapon.pistol`).
- Les noms **camelCase du site sont conservés** : `useWeapon`, `setWeapon`,
  `useChip`, `moveToward`, `moveAwayFrom`, `relativeShield`, `absoluteShield`,
  `maxLife`, `currentCooldown`…
- **Pas de variable globale `me`** : on obtient son entité via `Fight.me`.
- Les arguments positionnels acceptent un **objet ou un id** :
  `Cell | Entity | int`, `Weapon | Chip | int`.
- Les objets de l'API sont **poolés et en lecture seule** : `me.weapon is
  Weapon.pistol` est vrai, `cell.x = 3` lève une erreur. Seul `Fight.me` est
  modifiable (pratique pour y stash un état).
- Pendant le tour d'un bulbe invoqué, `Fight.me` **est** le bulbe.

## Point d'entrée

```python
def turn():
    ...   # rejoué par le moteur à chaque tour
```

- Le corps du module est évalué **une seule fois** (les variables de module
  persistent d'un tour à l'autre) ; `turn()` est ensuite rejouée à chaque
  tour.
- Si le module **ne définit pas** `turn()`, c'est le module entier qui est
  ré-évalué chaque tour.
- Ne pas appeler `turn()` à la fin du module (tir en double).
- Hooks disponibles (depuis 09/2026) : `beforeFight()` et `afterFight()`,
  uniquement pour une IA qui définit `turn()` et ne fait rien au niveau
  module.

## `Fight`

| Membre | Rôle |
|---|---|
| `me` | l'entité contrôlée (bulbe compris) |
| `turn`, `id`, `type`, `context`, `batched`, `boss`, `winner` | état du combat |
| `alliesLife`, `enemiesLife` | PV cumulés |
| `getNearestEnemy()`, `getNearestAlly()`, `getFarthestEnemy()`, `getFarthestAlly()` | ciblage |
| `getNearestEnemyTo(target)`, `getNearestAllyTo(target)`, `getNearestEnemyToCell(cell)` | ciblage relatif |
| `getEnemies()`, `getAllies()`, `getAliveEnemies()`, `getAliveAllies()`, `getDeadEnemies()`, `getDeadAllies()` | listes |
| `getEnemiesCount()`, `getAlliesCount()`, `getAliveEnemiesCount()`, `getAliveAlliesCount()`, `getDeadEnemiesCount()`, `getDeadAlliesCount()` | compteurs |
| `getAlliedTurret()`, `getEnemyTurret()` | tourelles |
| `getNextPlayer(entity?)`, `getPreviousPlayer(entity?)` | ordre de jeu |
| `listen()` | paroles prononcées (`[[entity, message]]`) |
| `weaponCell(...)`, `weaponCells(...)`, `chipCell(...)`, `chipCells(...)`, `weaponTargets(...)`, `chipTargets(...)` | géométrie de tir (aussi sur `Me`) |
| `CRITICAL_FACTOR` (1.3), `MAX_TURNS`, `SUMMON_LIMIT` | constantes |

**N'existent pas** : `Fight.allies`, `Fight.enemies`, `Fight.leeks`,
`Fight.getCell()`, `Fight.getLeek()`.

### `Fight.Use` (code retour des actions)

| Code | Valeur | Signification |
|---|---|---|
| `FAILED` | 0 | échec |
| `SUCCESS` | 1 | succès |
| `CRITICAL` | 2 | succès critique |
| `INVALID_TARGET` | -1 | cible invalide |
| `NOT_ENOUGH_TP` | -2 | pas assez de PT |
| `INVALID_COOLDOWN` | -3 | puce en recharge |
| `INVALID_POSITION` | -4 | position invalide (hors de portée / pas de ligne de vue) |
| `TOO_MANY_SUMMONS` | -5 | limite d'invocation |
| `RESURRECT_INVALID_ENTITY` | -6 | cible non ressuscitable |
| `MAX_USES` | -7 | limite d'utilisations atteinte |
| `INVALID_STATE` | -8 | état incompatible |

Idiome : `if me.useWeapon(enemy) > 0:` — une action impossible **retourne un
code**, elle ne lève pas d'exception.
`canUseWeapon(...)` / `canUseChip(...)` sont des **prédicats booléens**.

## `Entity` / `Me`

Propriétés : `id`, `entityType`, `life`, `maxLife`, `tp`, `maxTP`, `mp`,
`maxMP`, `strength`, `agility`, `wisdom`, `resistance`, `science`, `magic`,
`power`, `level`, `name`, `absoluteShield`, `relativeShield`, `damageReturn`,
`frequency`, `cores`, `ram`, `cell`, `weapon`, `weapons`, `chips`,
`components`, `effects`, `launchedEffects`, `passiveEffects`, `states`,
`summons`, `summoner`, `summoned`, `alive`, `dead`, `isStatic`, `birthTurn`,
`turnOrder`, `awakeningZone`, `plantTriggers`, `side`, `leekID`, `teamID`,
`teamName`, `compositionName`, `farmerID`, `farmerName`, `farmerCountry`,
`aiID`, `aiName`, `aiPath`.

Méthodes : `isAlly()`, `isEnemy()`, `stat(Entity.Stat.*)`, `distance(target)`,
`Entity.get(id)`.

Sous-types : `Leek`, `Turret`, `Bulb`, `Chest`, `Mob`, `Plant` (héritent
d'`Entity`, `isinstance()` fonctionne).

`Me` ajoute : `moveToward(target, mp?)`, `moveAwayFrom(target, mp?)`,
`moveTowardCells`, `moveTowardEntities`, `moveTowardLine`,
`moveAwayFromCells`, `moveAwayFromEntities`, `moveAwayFromLine`,
`useWeapon(target)`, `useWeaponOnCell(cell)`, `useChip(chip, target?)`,
`useChipOnCell(chip, cell)`, `setWeapon(weapon)`, `say(message)`, `lama()`,
`canUseWeapon`, `canUseWeaponOnCell`, `canUseChip`, `canUseChipOnCell`,
`resurrect(target, cell, chip?)`, `itemUses(item)`, `setLoadout(name,
changeStats?)`, `getInventory()`, `summon(chip, cell, callback, name?)`.

## `Cell`

`id`, `x`, `y`, `empty`, `obstacle`, `entity`, `hasEntity`, `content`
(`Cell.Type.EMPTY/ENTITY/OBSTACLE`), `distance(target)`, `pathLength(target)`,
`lineOfSight(target)`, `path(target)`, `onSameLine(target)`, `Cell.get(id)`.

Pas de `getDistanceTo()` : c'est `Cell.distance(target)`.

## `Effect`

Instance d'effet actif : `raw`, `type`, `value`, `caster`, `turns`,
`critical`, `item`, `target`, `modifiers`, `Effect.getAll()`.

Constantes (les plus utiles) :

| Constante | Valeur | Effet |
|---|---|---|
| `Effect.DAMAGE` | 1 | dégâts (force, boucliers, vol de vie) |
| `Effect.HEAL` | 2 | soin (sagesse) |
| `Effect.BUFF_STRENGTH` | 3 | buff force (science) |
| `Effect.BUFF_AGILITY` | 4 | buff agilité (science) |
| `Effect.RELATIVE_SHIELD` | 5 | bouclier relatif (résistance) |
| `Effect.ABSOLUTE_SHIELD` | 6 | bouclier absolu (résistance) |
| `Effect.BUFF_MP` | 7 | buff PM (science) |
| `Effect.BUFF_TP` | 8 | buff PT (science) |
| `Effect.BOOST_MAX_LIFE` | 12 | PV et PV max (sagesse) |
| `Effect.POISON` | 13 | poison (magie, ignore les boucliers) |
| `Effect.KILL` | 16 | exécution instantanée |
| `Effect.BUFF_RESISTANCE` | 21 | buff résistance (science) |
| `Effect.BUFF_WISDOM` | 22 | buff sagesse (science) |
| `Effect.AFTEREFFECT` | 25 | dégâts (science) |
| `Effect.LIFE_DAMAGE` | 28 | % des PV du lanceur |
| `Effect.NOVA_DAMAGE` | 30 | retire des PV max (science) |
| `Effect.RAW_BUFF_STRENGTH` | 38 | buff force **non** amplifié |
| `Effect.RAW_BUFF_POWER` | 52 | puissance (non amplifiée) |
| `Effect.RAW_HEAL` | 57 | soin **non** amplifié |
| … | … | jusqu'à `RAW_SHACKLE_STRENGTH` = 65 |

Alias : `Effect.BUFF_FORCE` = `Effect.BUFF_STRENGTH` (3).

`Effect.Target` (masque de cibles) : `NOT_CASTER=0`, `ENEMIES=1`,
`ALLIES=2`, `CASTER=4`, `NON_SUMMONS=8`, `SUMMONS=16`, `ALWAYS_CASTER=32`.

`Effect.Modifier` : `STACKABLE=1`, `MULTIPLIED_BY_TARGETS=2`,
`ON_CASTER=4`, `NOT_REPLACEABLE=8`, `IRREDUCTIBLE=16`.

## `Item` / `Weapon` / `Chip` / `Feature`

`Item` : `id`, `cost`, `minRange`, `maxRange`, `name`, `area`, `launchType`,
`maxUses` (0 = illimité), `inline`, `needsLos`, `failure`, `features`,
`effectiveArea(cell, from?)`, `Item.get(id)`.
`Weapon` : + `passiveFeatures`, `Weapon.get(id)`, `Weapon.getAll()`,
`Weapon.isWeapon(value)`.
`Chip` : + `cooldown`, `currentCooldown`, `minScope`, `maxScope`,
`bulbChips`, `currentCooldownOf(entity)`, `Chip.get(id)`, `Chip.getAll()`,
`Chip.isChip(value)`.
`Feature` : `raw`, `type`, `minValue`, `maxValue`, `turns`, `targets`,
`modifiers` — c'est le **potentiel déclaré** d'un objet ; `Effect` est
l'effet **actif** sur une entité.

## Autres globaux

- `Debug.log(value, color?)` (→ journal de combat), `mark`, `markText`,
  `clearMarks`, `show`, `pause`.
- `Field` : `type`, `cellFromXY(x, y)`, `getObstacles()`, `distance(a, b)`,
  `cellDistance`, `euclideanDistance`, `pathLength`, `lineOfSight`,
  `onSameLine`, `path`.
- `Registers` : `get(key)`, `set(key, value)`, `delete(key)`, `all()` —
  stockage persistant **entre les combats**.
- `Network` : `sendTo(entity, type, params)`, `sendAll(type, params)`,
  `getMessages(entity?)` ; `Message.Type.*` (HEAL=1, ATTACK=2, …).
- `System` : `operations`, `maxOperations`, `instructionsCount`, `usedRAM`,
  `maxRAM`, `date`, `time`, `timestamp`, `fileRead(path)` (64 KiB max),
  `getLoadout(path)`, `sendNotification(title, message?)`.
- `Color` : `rgb(r, g, b)`, `red`, `green`, `blue`.
- `Math` : uniquement des utilitaires de bits (`bitCount`, `setBit`, …) —
  `math.pi` vient de la stdlib.
- `State` : états (`UNHEALABLE=2`, `AMPUTATED=13`, `DENSE=6`, …).
- `print()` → journal de combat (même canal que `Debug.log`).

## Imports

- Seuls les **fichiers de l'IA** sont accessibles ; pas de disque, pas de
  réseau.
- Résolution : un module est cherché dans le **dossier du fichier d'entrée**,
  puis à la **racine**.
- Un dossier de package doit contenir `__init__.py`.
- Pas de tiret dans les noms de fichiers, pas d'import circulaire.
- Stdlib Python 3.12 disponible (`math`, `itertools`, `collections`,
  `heapq`, `functools`, `random`…), **pas de pip**.

## Bac à sable

- GraalPy, `SandboxPolicy.ISOLATED` : threads natifs, accès natif, création
  de processus et IO hors `/ai` interdits.
- Limites : « statements » ≈ 20 000 000, profondeur d'AST 5000, 1 thread,
  flux ≤ 1 Mo, mémoire bornée par le RAM du poireau
  (`System.maxRAM`).
- Déterminisme : `random` graine par combat, horloge figée.

## Sources

- <https://leekwars.com/help/polyglot> — écrire son IA en Python
- <https://leekwars.com/api/encyclopedia/get/fr/Python> — article Python
- <https://leekwars.com/help/api> — documentation de l'API
- `docs/leekwars-api.d.ts` — stubs TypeScript officiels (mêmes signatures)
- `stubs/__builtins__.pyi` — stubs Python officiels
- <https://github.com/leek-wars/leek-wars-generator> — runtime de référence
