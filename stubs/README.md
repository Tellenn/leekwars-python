# Stubs Python de l'API Leek Wars

`__builtins__.pyi` est une copie des stubs officiels générés par l'éditeur
Leek Wars (source : générateur du site, extrait depuis
<https://raw.githubusercontent.com/florelabs/leekwars-py-toolkit/main/data/leekwars_raw.pyi>).

L'éditeur monte ce fichier à la racine du FS virtuel de Pyright : les
globaux `Fight`, `Effect`, `Weapon`, `Cell`, `Debug`… sont alors résolus
comme des *builtins*, sans import.

En local, `pyproject.toml` configure `stubPath = "stubs"` pour obtenir le
même comportement :

```bash
make typecheck   # pyright
```

Snapshot septembre 2026 : il manque quelques membres récents
(`Entity.components`, `Entity.plantTriggers`, `Me.getInventory`,
`System.fileRead`, …). Le bundel TypeScript officiel, plus à jour, est dans
`docs/leekwars-api.d.ts`.
