<!-- Snapshot local de l'encyclopédie Leek Wars (fr) :
     source : https://leekwars.com/api/encyclopedia/get/fr/Force
     rafraîchissable via `python3 tools/sync_encyclopedia.py` -->

# Force
> Caractéristiques

<img src="/image/charac//strength.png" style="vertical-align:top; float:right;"> 

La force permet d'infliger plus de dégâts avec les Armes et les Puces ayant un effet de dégâts. Voir les [[Effets]].
Elle s'applique de la manière suivante :

<code>DegatsFinaux = DegatsDeBase * (1 + Force / 100)</code>

Ainsi, avec 100 de force, les dégâts sont doublés, avec 200, ils sont triplés et ainsi de suite.

Selon la quantité de capital dépensé dans la force, le ratio Force/Capital change :

<table>
	<tr>
		<th>Force ajoutée</th>
		<th>Rapport Force/Capital</th>
	</tr>
	<tr>
		<td>Force ajoutée < 200 </td>
		<td>1 Capital pour 2 points de Force</td>
	</tr>
	<tr>
		<td>200 <= Force ajoutée < 400</td>
		<td>1 Capital pour 1 point de Force</td>
	</tr>
	<tr>
		<td>400 <= Force ajoutée < 600</td>
		<td>2 Capital pour 1 point de Force</td>
	</tr>
	<tr>
		<td>600 <= Force ajoutée</td>
		<td>3 Capital pour 1 point de Force</td>
	</tr>
</table>

Investir dans les points de force est la méthode la plus simple pour augmenter les dommages qu'un poireau fait aux autres entités.