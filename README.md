# leekwars-python

IA **Leek Wars** écrite en Python : le code de l'IA est importé dans
l'éditeur du site (arbre de fichiers git), et le repo permet de **tester la
logique de décision en local** grâce à un mock du SDK du jeu.

> Guide de travail pour les agents et les développeurs : **[AGENTS.md](AGENTS.md)**.

## Contenu

| Chemin | Rôle |
|---|---|
| `main.py` | point d'entrée de l'IA (fonction `turn()`), déployé sur le site |
| `libs/` | logique de jeu (analyse d'équipement, décision, équipement, logs) |
| `leekwars_api/` | **mock local** du SDK Leek Wars (jamais déployé) |
| `tests/` | tests `unittest` (zéro dépendance) |
| `docs/encyclopedia/` | snapshot local de l'encyclopédie FR (formules du jeu) |
| `docs/leekwars-api.d.ts` | stubs TypeScript officiels de l'API Leek Wars |
| `tools/` | scripts d'outillage (build de déploiement, sync de la doc) |

## Démarrage rapide

```bash
make test      # python3 -m unittest discover -s tests -v
make dist      # dist/leekwars/ : main.py + libs/ à copier dans l'éditeur
```

Exemple de test local d'un combat :

```python
from leekwars_api import builder, install

fight = builder.make_fight(
    me=builder.entity(strength=100, life=100, cell=(0, 0)),
    enemies=[builder.entity(life=60, max_life=60, cell=(2, 0))],
)
install(fight)

import main
main.turn()
print(fight.logs)      # journal de l'IA (Debug.log)
```

## Documentation de référence

- Site officiel : <https://leekwars.com/help> (encyclopédie, documentation de l'API)
- Polyglot / Python : <https://leekwars.com/help/polyglot>
- Snapshots locaux : `docs/encyclopedia/` (Force, Agilité, Résistance, Sagesse, Effets…)
