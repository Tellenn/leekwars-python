<!-- Snapshot local de l'encyclopédie Leek Wars (fr) :
     source : https://leekwars.com/api/encyclopedia/get/fr/Vol de vie
     rafraîchissable via `python3 tools/sync_encyclopedia.py` -->

# Vol de vie
> Règles du jeu

La [[Sagesse]] augmente le [[Vol de vie]] : Une partie des dégâts infligés sont convertis en [[Points de Vie|vie]] qui sont rendus à votre poireau. Le vol de vie ne s'applique que pour les dégâts dépendant de la [[Force]].

<code>SoinsParVolDeVie = DegatsFinaux * Sagesse / 1000</code>

Ainsi, avec 200 de [[Sagesse]], une attaque à 100 de dégâts (après application des boucliers) vous soignera de 20 [[Points de Vie|points de vie]].