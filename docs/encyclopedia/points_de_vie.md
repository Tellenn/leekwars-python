<!-- Snapshot local de l'encyclopédie Leek Wars (fr) :
     source : https://leekwars.com/api/encyclopedia/get/fr/Points de Vie
     rafraîchissable via `python3 tools/sync_encyclopedia.py` -->

# Points de Vie
> Caractéristiques

<img src="/image/charac/life.png" style="vertical-align:top; float:right;">

La vie d'un poireau est essentielle durant un combat dans le potager. En effet, une entité reste en jeu tant qu'elle a encore des points de vie. Pour vérifier les points de vie d'une entité, la fonction [getLife](https://leekwars.com/help/documentation/getLife) est disponible dans votre code.

Au niveau 1, un poireau a 100 points de vie. Ensuite, il gagne 3 points de vie supplémentaires à chaque niveau. Ces points de vie forment une base de points de vie.

	BaseDeVie = 100 + ((Niveau - 1) * 3)


En plus de cette base de points de vie, vous pouvez dépenser des [[Points de Capital]] dans la Vie. Selon la quantité de capital dépensé dans la Vie, le ratio Vie/Capital change : 

Vie ajoutée | Rapport Vie/Capital
------------|--------------------
Vie ajoutée < 1000 	| 1 Capital pour 4 Points de Vie
1000 <= Vie ajoutée < 2000 	| 1 Capital pour 3 Points de Vie
2000 <= Vie ajoutée | 1 Capital pour 2 Points de Vie 

Investir dans les points de vie permettra à votre poireau d'encaisser plus de dommage avant de mourir et d'être recyclé en compost.

>Il ne faut pas confondre la vie et la vie max de votre poireau. Au début du combat, la vie est égale à la vie max. Votre vie ne dépassera jamais le montant de votre vie max. Mais les deux varient au cours d'un combat. Pour plus d'explications voir : [[Vie Max]].

<u>Pour augmenter la vie de votre poireau **avant le combat** :</u>
- Vous pouvez investir des [[Points de Capital]] dans les [[Points de Vie]].

<u>Pour augmenter la vie de votre poireau **durant le combat** :</u>
- Vous pouvez utiliser les [puces de soin](https://leekwars.com/encyclopedia/March%C3%A9#Soins) et donc investir des [[Points de Capital]] dans la [[Sagesse]]
- Vous pouvez compter sur le [[Vol de vie]] gagné par les dégâts infligés.

<u>Pour éviter de perdre de la vie **durant le combat** :</u>
- Vous pouvez vous protéger des dégâts de force via les [puces de protection](https://leekwars.com/encyclopedia/March%C3%A9#Protection) et donc investir des [[Points de Capital]] dans la [[Résistance]]
- Vous pouvez vous protéger des dégâts poison via la puce [[Antidote]] (ou dans une moindre mesure avec [[Libération]]).

>Si vous réduisez à 0 la vie d'un invocateur,
Alors toutes ses invocations (=[[Bulbes]]) mourront avec lui.

Il est possible de ramener à la vie des entités via la puce [[Résurrection]].