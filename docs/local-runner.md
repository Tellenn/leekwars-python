# Rejouer l'IA dans le moteur officiel (option « haute fidélité »)

Le mock `leekwars_api/` rejoue les **formules** du jeu, mais pas le moteur
(combat, IA adverse, carte, cooldown, budget d'opérations…). Pour ça, il
existe le **générateur officiel** de Leek Wars, open source : il rejoue une
IA `.py` dans le vrai moteur, hors site.

> Source : <https://github.com/leek-wars/leek-wars-generator>

## Mise en place

```bash
git clone https://github.com/leek-wars/leek-wars-generator.git
cd leek-wars-generator
sh libs/fetch-isolate.sh && gradle jar
```

Le générateur a besoin des **données de jeu** (armes, puces, cartes) :
`libs/fetch-isolate.sh` les récupère.

## Rejouer un scénario

`scenarios/duel.json` (de ce dépôt) oppose l'IA à elle-même sur une carte
vide 17×17, avec une graine fixe → le combat est **rejouable à l'identique**.

```bash
# l'IA doit être dans un dossier "ai" : copie le contenu de dist/leekwars/
cp -r /chemin/vers/leekwars-python/dist/leekwars /tmp/ai

java -jar generator.jar --analyze /tmp/ai/main.py        # vérifie le fichier
java -jar generator.jar /chemin/vers/scenarios/duel.json  # rejoue le combat
```

Le combat s'affiche dans le navigateur (mode « battle ») et le journal de
combat (`Debug.log`) est lisible dans le rapport de fin de combat : c'est
l'endroit où l'on confronte les **dégâts attendus** (journal de l'IA) aux
**dégâts réels**.

## Adapter le scénario

| Champ | Rôle |
|---|---|
| `entities[0]` / `entities[1]` | les deux équipes (une entité = un membre d'équipe) |
| `ai` | chemin du fichier IA **relatif au dossier `/ai`** (`main.py`, ou une autre IA) |
| `weapons` / `chips` | ids d'objets du jeu (voir les données du générateur) |
| `cell` | id de case de départ |
| `random_seed` | graine du combat (même graine ⇒ même combat) |
| `max_turns`, `max_operations_per_entity` | limites du combat |

## Port Python communautaire

<https://github.com/Traual/leekwars-generator-python> rejoue les mêmes
scénarios en Python pur, avec la parité de l'aléa (RNG) : utile pour
comparer une correction du mock avec le moteur de référence.
