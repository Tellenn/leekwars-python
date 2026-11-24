<!-- Snapshot local de l'encyclopédie Leek Wars (fr) :
     source : https://leekwars.com/api/encyclopedia/get/fr/Résistance
     rafraîchissable via `python3 tools/sync_encyclopedia.py` -->

# Résistance
> Caractéristiques

<img src="/image/charac//resistance.png" style="vertical-align:top; float:right;"> 

La résistance permet d'augmenter l'efficacité des [[Puces]] ayant un effet de bouclier. Voir les [[Effets]].

Le Bouclier Absolu réduit les dégâts infligés d'une certaine quantité alors que le Bouclier Relatif les réduit d'un certain pourcentage. Les [[poison|poisons]], les [[renvoi de dégâts|renvois de dégâts]] et les [[dégâts nova]] ignorent les boucliers.

<code>BouclierAbsoluFinal = BouclierAbsoluDeBase * (1 + Resistance / 100)</code>

<code>BouclierRelatifFinal = BouclierRelatifDeBase * (1 + Resistance / 100)</code>

Ainsi, avec 100 de Résistance, la protection est doublée, avec 200, elle est triplée et ainsi de suite.

Les dégâts finaux se calculent comme ceci :

<code>DegatsFinaux = DegatsDeBase * (1 - BouclierRelatif / 100) - BouclierAbsolu</code>

**Note** : Au moment du calcul des dégâts, la résistance n'intervient plus dans la formule, car les effets sont calculés au lancement de la puce et restent fixes ensuite. Ils peuvent cependant être réduits avec une puce comme [[libération]].

Il est possible d'avoir des valeurs de bouclier négatives avec les effets de vulnérabilité et de vulnérabilité absolue. Dans ce cas, la formule reste la même, les dégâts seront amplifiés au lieu d'être réduits.

Les fonctions [[getAbsoluteShield]] et [[getRelativeShield]] permettent d'obtenir respectivement le bouclier absolu et relatif *actuels* d'une entité.

Selon la quantité de capital dépensé dans la Résistance, le ratio Résistance/Capital change :

<table>
	<tr>
		<th>Résistance ajoutée</th>
		<th>Rapport Résistance/Capital</th>
	</tr>
	<tr>
		<td>Résistance ajoutée < 200 </td>
		<td>1 Capital pour 2 points de Résistance</td>
	</tr>
	<tr>
		<td>200 <= Résistance ajoutée < 400</td>
		<td>1 Capital pour 1 point de Résistance</td>
	</tr>
	<tr>
		<td>400 <= Résistance ajoutée < 600</td>
		<td>2 Capital pour 1 point de Résistance</td>
	</tr>
	<tr>
		<td>600 <= Résistance ajoutée</td>
		<td>3 Capital pour 1 point de Résistance</td>
	</tr>
</table>