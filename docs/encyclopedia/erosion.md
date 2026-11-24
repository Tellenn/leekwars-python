<!-- Snapshot local de l'encyclopédie Leek Wars (fr) :
     source : https://leekwars.com/api/encyclopedia/get/fr/Érosion
     rafraîchissable via `python3 tools/sync_encyclopedia.py` -->

# Érosion
> Règles du jeu


L'<strong>Érosion</strong> a été implémentée pour la MAJ 1.98, le 1er juin 2017.

Pour comprendre ce qu'est l'<strong>érosion</strong> et "comment marche-t-elle ?"

{{summary}}

## Compréhension
L'<strong>Érosion</strong> est un effet bien à part dans Leek Wars, il découle du fait d'infliger des dégâts à un ennemi.

Il n'est pas directement visible à l'écran mais est bien présent dans le jeu.

Il se caractérise par une diminution des Points de [[Vie Max|vie maximum]].

## Fonctionnement
La [[Vie Max|vie maximum]] diminue lorsque l'entité reçoit des dégâts.

<strong>Dégâts classiques (EFFECT_DAMAGE, EFFECT_LIFE_DAMAGE, EFFECT_DAMAGE_RETURN et EFFECT_AFTEREFFECT)</strong>

L'érosion pour les dégâts classiques est calculée ainsi : 
- 5% des dégâts subis sont retirés à la [[Vie Max|Vie Maximum]] (la constante [[EROSION_DAMAGE]])
- 15% dans le cadre d'un [[Coup critique]] ([[EROSION_DAMAGE]] + `EROSION_CRITICAL_BONUS`)

Il faut savoir que le bouclier absolu ou relatif atténue l'effet (sauf pour les dégâts de type EFFECT_DAMAGE_RETURN et EFFECT_AFTEREFFECT qui ignorent les boucliers), puisque l'érosion est calculée sur les dégâts subis par le poireau. 

<strong>Dégâts de [[Poison]] (EFFECT_POISON)</strong>
L'érosion pour les dégâts de poison (liés à la [[Magie]]) est calculée différemment des 2 précédents : 
- 10% des dégâts du poison sont retirés à la [[Vie Max|Vie Maximum]] (la constante [[EROSION_POISON]])
- 20% dans le cadre d'un [[Coup critique]] ([[EROSION_POISON]] + `EROSION_CRITICAL_BONUS`)

Cela a pour effet de raccourcir un peu les combats et d'augmenter l'intérêt d'investir en [[Points de Vie]], améliorant aussi l'efficacité des poisons.

Par ailleurs, la puce [[Blindage]] et les autres [[Puces]] permettant de gagner de la [[Vie Max]] voient leur utilité augmenter.


## Voir aussi
- [[Dégâts nova]]
- [[Vie Max]]
- [[Points de Vie|Vie]]

