<!-- Snapshot local de l'encyclopédie Leek Wars (fr) :
     source : https://leekwars.com/api/encyclopedia/get/fr/Sagesse
     rafraîchissable via `python3 tools/sync_encyclopedia.py` -->

# Sagesse
> Caractéristiques

<img src="/image/charac//wisdom.png" style="vertical-align:top; float:right;"> 

La Sagesse permet d'augmenter le montant de points de vie récupérés avec les Armes et Puces ayant un effet de soins. Voir les [[Effets]] (`EFFECT_HEAL` et `EFFECT_BOOST_MAX_LIFE`).
Elle s'applique de la manière suivante :

<code>SoinsFinaux = SoinsDeBase * (1 + Sagesse / 100)</code>

Ainsi, avec 100 de Sagesse, les soins sont doublés, avec 200, ils sont triplés et ainsi de suite.

De plus, la Sagesse a un effet [[Vol de vie]]. Une partie des dégâts infligés sont convertis en [[Points de vie|Vie]] qui sont rendus à votre poireau. (Cela ne s'applique que pour les dégâts dépendant de la [[Force]])

<code>SoinsParVolDeVie = DegatsFinaux * Sagesse / 1000</code>

Ainsi, avec 200 de Sagesse, une attaque à 100 de dégâts (après application des boucliers) vous soignera de 20 points de vie.

Selon la quantité de capital dépensé dans la Sagesse, le ratio Sagesse/[[Points de Capital]] change :

<table>
	<tr>
		<th>Sagesse ajoutée</th>
		<th>Rapport Sagesse/Capital</th>
	</tr>
	<tr>
		<td>Sagesse ajoutée < 200 </td>
		<td>1 Capital pour 2 points de Sagesse</td>
	</tr>
	<tr>
		<td>200 <= Sagesse ajoutée < 400</td>
		<td>1 Capital pour 1 point de Sagesse</td>
	</tr>
	<tr>
		<td>400 <= Sagesse ajoutée < 600</td>
		<td>2 Capital pour 1 point de Sagesse</td>
	</tr>
	<tr>
		<td>600 <= Sagesse ajoutée</td>
		<td>3 Capital pour 1 point de Sagesse</td>
	</tr>
</table>
