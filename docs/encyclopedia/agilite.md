<!-- Snapshot local de l'encyclopédie Leek Wars (fr) :
     source : https://leekwars.com/api/encyclopedia/get/fr/Agilité
     rafraîchissable via `python3 tools/sync_encyclopedia.py` -->

# Agilité
> Caractéristiques

<img src="/image/charac/agility.png" style="float: right">

L'Agilité permet de renvoyer plus de dégâts avec les Puces ayant un effet de [[renvoi de dégâts]]. Voir les [[Effets]]. 
Elle s'applique de la manière suivante :

<code>RenvoiDeDegatsFinaux = RenvoiDeDegatsDeBase * (1 + Agilite / 100)</code>

Ainsi, avec 100 d'Agilité, les renvois de dégâts sont doublés. Avec 200, ils sont triplés. Etc.

De plus, l'Agilité augmente les chances de [[coup critique]]. Un [[coup critique]] multiplie la valeur de l'effet par 1.3 (ce ratio peut évoluer avec les mises à jour, dans le code il est accessible avec la constante CRITICAL_FACTOR), soit une augmentation de 30%. 

`Probabilité de coup critique = Agilité du lanceur / 1000`

Ainsi, avec 200 d'Agilité, votre poireau a 20% de chances d'infliger 130 de dégâts au lieu de 100.

Selon la quantité de capital dépensé dans l'Agilité, le ratio Agilité/Capital change : 

<table>
	<tr>
		<th>Agilité ajoutée</th>
		<th>Rapport Agilité/Capital</th>
	</tr>
	<tr>
		<td>Agilité ajoutée < 200 </td>
		<td>1 Capital pour 2 points d'Agilité</td>
	</tr>
	<tr>
		<td>200 <= Agilité ajoutée < 400</td>
		<td>1 Capital pour 1 point d'Agilité</td>
	</tr>
	<tr>
		<td>400 <= Agilité ajoutée < 600</td>
		<td>2 Capital pour 1 point d'Agilité</td>
	</tr>
	<tr>
		<td>600 <= Agilité ajoutée</td>
		<td>3 Capital pour 1 point d'Agilité</td>
	</tr>
</table>