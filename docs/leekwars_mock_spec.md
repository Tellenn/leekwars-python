# Contrat du SDK mock Leek Wars (`leekwars_api/`)

Mock **local uniquement**. Il ne doit **jamais** être importé par le code de
l'IA (`Kepo_solo.py`, `libs/*`) : sur le site, ces modules n'existent pas.

## Principe d'injection

Le code de l'IA utilise des globaux non qualifiés (`Fight`, `Effect`,
`Debug`, ...) qui, sur le site, sont injectés par le moteur. En local, le mock
fait la même chose en installant ces noms dans `builtins` :

```python
from leekwars_api import install
fight = install(fight)      # lie Fight/Effect/Debug/... dans builtins
```

Conséquence : `import Kepo_solo` (ou `importlib.reload(ai)`) doit avoir lieu
**après** `install()`, car `Kepo_solo.py` lit `Fight.me` au niveau module.

## API publique

### `leekwars_api.install(fight=None) -> Fight`
Lie dans `builtins` : `Fight`, `Effect`, `Debug`, `Field`, `Registers`,
`System`, `Weapon`, `Chip`, `Cell`, `Entity`, `Me`, `Leek`, `Item`,
`Feature`, `Math` (non requis, `math` stdlib suffira).
Retourne le `Fight` lié. `uninstall()` retire les bindings.

### `leekwars_api.builder`

```python
make_fight(*, me, enemies=(), allies=(), map_size=12, seed=0) -> Fight
entity(*, name="leek", life=100, max_life=100, tp=10, max_tp=10, mp=10,
       max_mp=10, strength=0, agility=0, wisdom=0, resistance=0, science=0,
       magic=0, power=0, level=1, cell=(0, 0), weapons=(), chips=(),
       relative_shield=0, absolute_shield=0, side=1, id=None) -> Entity
weapon(name, cost=1, min_range=0, max_range=1, features=(), max_uses=0,
       needs_los=True, inline=False, failure=0, id=None) -> Weapon
chip(name, cost=1, min_range=0, max_range=1, features=(), max_uses=0,
     needs_los=True, inline=False, failure=0, id=None) -> Chip
feature(type, targets, min_value=0, max_value=0, turns=0, modifiers=0) -> Feature
```

`make_fight` place les entités sur une carte carrée `map_size x map_size`
(vide, sans obstacle), calcule `Fight.me`, `Fight.getNearestEnemy()` etc.

### Objet `Fight`

Attributs : `me`, `turn` (int, 0 au départ), `id`, `type`, `context`,
`logs` (liste des messages `Debug.log`), `rng` (`random.Random(seed)`).
Méthodes : `getNearestEnemy()`, `getNearestAlly()`, `getFarthestEnemy()`,
`getFarthestAlly()`, `getEnemies()`, `getAllies()`, `getAliveEnemies()`,
`getAliveAllies()`, `getDeadEnemies()`, `getDeadAllies()`, `getEnemiesCount()`,
`getAlliesCount()`, `getAliveEnemiesCount()`, `getAliveAlliesCount()`,
`getAlliedTurret()`, `getEnemyTurret()`, `getNearestEnemyToCell(cell)`,
`weaponCell/chipCell/weaponCells/chipCells/weaponTargets/chipTargets`,
`next_turn()` (incrémente `turn`, remet TP/MP à max, vide les usages d'items
du tour, décrémente la durée des effets).

### Objet `Entity` (et `Me`, `Leek`)

Propriétés en lecture/écriture : `id`, `name`, `life`, `maxLife`, `tp`,
`maxTP`, `mp`, `maxMP`, `strength`, `agility`, `wisdom`, `resistance`,
`science`, `magic`, `power`, `level`, `cell`, `weapon`, `weapons`, `chips`,
`absoluteShield`, `relativeShield`, `damageReturn`, `effects`, `states`,
`summons`, `summoner`, `summoned`, `alive`, `dead`, `isStatic`, `side`,
`teamID`, `leekID`, `entityType`.
Méthodes : `isAlly()`, `isEnemy()`, `distance(target)`, `stat(stat)`.

**Érosion** (fr/Érosion) : quand une entité subit des dégâts, une part de
ceux-ci est retirée à sa `maxLife` (5 % des dégâts classiques, 10 % du
poison, +10 % sur un coup critique). Les boucliers atténuent l'érosion :
elle est calculée sur les dégâts réellement subis.

`Me` ajoute : `moveToward(target, mp=None)`, `moveAwayFrom(target, mp=None)`,
`moveTowardCells`, `moveTowardEntities`, `moveTowardLine`,
`moveAwayFromCells`, `moveAwayFromEntities`, `moveAwayFromLine`,
`useWeapon(target)`, `useWeaponOnCell(cell)`, `useChip(chip, target=None)`,
`useChipOnCell(chip, cell)`, `setWeapon(weapon)`, `say(msg)`, `lama()`,
`canUseWeapon(target, weapon=None)`, `canUseChip(chip, target)`,
`canUseChipOnCell(chip, cell)`, `itemUses(item)`, `resurrect(...)`,
`setLoadout(...)`, `getInventory()`, `summon(...)`.

### Objets `Cell`

`id`, `x`, `y`, `empty`, `obstacle`, `entity`, `hasEntity`, `content`,
`distance(target)`, `pathLength(target)`, `lineOfSight(target)`,
`path(target)`, `onSameLine(target)`, `Cell.get(id)`.

**Distance** : chebyshev (`max(|dx|, |dy|)`), convention Leek Wars (déplacement
en 8 directions). Centralisée dans une constante `leekwars_api.RULES.distance`
pour être modifiable.

**Line of sight** : approximated (pas d'obstacle par défaut → `True` ;
`obstacle=True` sur une case bloque). Les entités ne bloquent pas la vue.

### Objets `Weapon` / `Chip` / `Item` / `Feature`

`Item` : `id`, `cost`, `minRange`, `maxRange`, `name`, `area`, `launchType`,
`maxUses`, `inline`, `needsLos`, `failure`, `features`.
`Weapon`/`Chip` : + `Weapon.get(id)`, `Weapon.getAll()`, `Weapon.isWeapon(v)`,
`Chip.get(id)`, `Chip.getAll()`, `Chip.isChip(v)`.
`Feature` : `type`, `minValue`, `maxValue`, `turns`, `targets`, `modifiers`,
`raw`.

### `Effect`

Namespace de constantes :

- `Effect.Type` : les types de l'encyclopédie FR « Effets » **plus** les types
  ajoutés par le moteur, avec les **valeurs numériques exactes** :
  `DAMAGE=1, HEAL=2, BUFF_STRENGTH=3, BUFF_AGILITY=4, RELATIVE_SHIELD=5,
  ABSOLUTE_SHIELD=6, BUFF_MP=7, BUFF_TP=8, DEBUFF=9, TELEPORT=10, INVERT=11,
  BOOST_MAX_LIFE=12, POISON=13, SUMMON=14, RESURRECT=15, KILL=16,
  SHACKLE_MP=17, SHACKLE_TP=18, SHACKLE_STRENGTH=19, DAMAGE_RETURN=20,
  BUFF_RESISTANCE=21, BUFF_WISDOM=22, ANTIDOTE=23, SHACKLE_MAGIC=24,
  AFTEREFFECT=25, VULNERABILITY=26, ABSOLUTE_VULNERABILITY=27,
  LIFE_DAMAGE=28, STEAL_ABSOLUTE_SHIELD=29, NOVA_DAMAGE=30, RAW_BUFF_MP=31,
  RAW_BUFF_TP=32, POISON_TO_SCIENCE=33, DAMAGE_TO_ABSOLUTE_SHIELD=34,
  DAMAGE_TO_STRENGTH=35, NOVA_DAMAGE_TO_MAGIC=36, RAW_ABSOLUTE_SHIELD=37,
  RAW_BUFF_STRENGTH=38, RAW_BUFF_MAGIC=39, RAW_BUFF_SCIENCE=40,
  RAW_BUFF_AGILITY=41, RAW_BUFF_RESISTANCE=42, PROPAGATION=43,
  RAW_BUFF_WISDOM=44, NOVA_VITALITY=45, ATTRACT=46, SHACKLE_AGILITY=47,
  SHACKLE_WISDOM=48, REMOVE_SHACKLES=49, MOVED_TO_MP=50, PUSH=51,
  RAW_BUFF_POWER=52, REPEL=53, RAW_RELATIVE_SHIELD=54,
  ALLY_KILLED_TO_AGILITY=55, KILL_TO_TP=56, RAW_HEAL=57, CRITICAL_TO_HEAL=58,
  ADD_STATE=59, TOTAL_DEBUFF=60, STEAL_LIFE=61, MULTIPLY_STATS=62,
  DAMAGE_TO_RESISTANCE=63, SUPERINFECTION=64, RAW_SHACKLE_STRENGTH=65`
  + alias `BUFF_FORCE = 3` (alias de `BUFF_STRENGTH`).
- `Effect.Target` : `NOT_CASTER=0, ENEMIES=1, ALLIES=2, CASTER=4,
  NON_SUMMONS=8, SUMMONS=16, ALWAYS_CASTER=32`
  (combinables par `|`, testables par `&`).
- `Effect.Modifier` : `STACKABLE=1, MULTIPLIED_BY_TARGETS=2, ON_CASTER=4,
  NOT_REPLACEABLE=8, IRREDUCTIBLE=16`.
- `Effect.getAll()` renvoie la liste des types.
- Instances d'effets : `raw`, `type`, `value`, `caster`, `turns`, `critical`,
  `item`, `target`, `modifiers`.

### `Fight.Use`

Codes d'action retournés par `useWeapon` / `useChip` (et variantes) :
`SUCCESS=1, CRITICAL=2, FAILED=0, INVALID_TARGET=-1, NOT_ENOUGH_TP=-2,
INVALID_COOLDOWN=-3, INVALID_POSITION=-4, TOO_MANY_SUMMONS=-5,
RESURRECT_INVALID_ENTITY=-6, MAX_USES=-7, INVALID_STATE=-8`.

Une action impossible **retourne un code négatif**, elle ne lève pas
d'exception (`if me.useWeapon(e) > 0:` est l'idiome officiel).
`canUseWeapon` / `canUseChip` sont des prédicats (booléens), pas des codes.

### `Debug`

`Debug.log(value, color=None)` → append `str(value)` à `fight.logs`.
`mark`, `markText`, `clearMarks`, `show`, `pause` → no-op (ou no-op loggué).

### `Field`, `Registers`, `System`

- `Field` : `type`, `cellFromXY(x, y)`, `getObstacles()`, `distance(a, b)`,
  `cellDistance(a, b)`, `euclideanDistance(a, b)`, `pathLength(a, b)`,
  `lineOfSight(a, b)`, `onSameLine(a, b)`, `path(a, b)`.
- `Registers` : `get(key)`, `set(key, value)`, `delete(key)`, `all()` —
  dictionnaire persistant **au niveau du processus** (comme sur le site).
- `System` : `operations`, `maxOperations`, `instructionsCount`, `usedRAM`,
  `maxRAM`, `date`, `time`, `timestamp`, `fileRead(path)` → `None`,
  `getLoadout(path)` → `None`, `sendNotification(...)` → `False`.

## Règles de jeu implémentées (source : encyclopédie FR)

Le mock applique les **vraies formules** du jeu, pour que les tests
valident la même arithmétique que le serveur :

| Règle | Formule |
|---|---|
| Force | `DegatsFinaux = Base * (1 + Force / 100)` |
| Coup critique | `P = Agilité / 1000`, multiplicateur `1.3` (`CRITICAL_FACTOR`) |
| Boucliers | `DegatsFinaux = Base * (1 - BouclierRelatif / 100) - BouclierAbsolu`, plancher 0 |
| Ignorent les boucliers | poisons, renvoi de dégâts, dégâts nova |
| Sagesse | `SoinsFinaux = Base * (1 + Sagesse / 100)` (plafonné aux PV max) |
| Science | amplifie `BUFF_STRENGTH`, `BUFF_AGILITY`, `BUFF_RESISTANCE`, `BUFF_WISDOM`, `BUFF_TP`, `BUFF_MP` (les variantes `RAW_*` ne sont **pas** amplifiées) |
| Vol de vie | `SoinsParVolDeVie = DegatsFinaux * Sagesse / 1000` (seulement dégâts dépendant de la Force) |
| Coûts | `useWeapon`/`useChip` coûtent `item.cost` PT ; `setWeapon` coûte 1 PT ; 1 PM par case déplacée |
| Portée | `minRange <= cell.distance(cible) <= maxRange` |
| Ligne de vue | vérifiée si `item.needs_los` |

Jet de valeur : `rng.randint(minValue, maxValue)` (le jeu tire au sort dans
l'intervalle). `rng` est graineable via `make_fight(seed=...)` → tests
déterministes.

Effets à la volée : un `useWeapon`/`useChip` applique les `features` de
l'item. `Effect.DAMAGE` sur `ENEMIES` retire des PV ; `Effect.HEAL` /
`BOOST_MAX_LIFE` soigne le lanceur ; les buffs modifient les stats de la
cible ; `RELATIVE_SHIELD` / `ABSOLUTE_SHIELD` ajoutent des boucliers
(amplifiés par la résistance) ; `KILL` met à 0 les PV ; `NOVA_DAMAGE` retire
des **PV maximum** ; `LIFE_DAMAGE` retire un pourcentage des PV max du
lanceur.

Valeurs par défaut de `entity.relativeShield` / `absoluteShield` : ce que
le test fixe ; les boucliers ajoutés par des effets s'y ajoutent.

## Contraintes

- Python 3.10+ compatible, **aucune dépendance externe** (stdlib uniquement).
- Pas d'accès réseau, pas de fichier, pas de `print` (utiliser `Debug.log`).
- Docstrings et commentaires en français, style proche des libs existantes.
- Tests fournis : `python -m unittest discover -s tests` doit passer.
