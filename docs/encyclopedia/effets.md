<!-- Snapshot local de l'encyclopédie Leek Wars (fr) :
     source : https://leekwars.com/api/encyclopedia/get/fr/Effets
     rafraîchissable via `python3 tools/sync_encyclopedia.py` -->

# Effets
> Règles du jeu

Un effet peut représenter deux choses : Un mécanisme du jeu ou l'application dudit mécanisme.

{{summary}}

## Effets des armes et puces

Ils sont utilisés dans la description d'une [[armes|arme]] ou d'une [[puces|puce]]. On peut les récupérer avec <a href="/help/documentation/getWeaponEffects">getWeaponEffects</a> et <a href="/help/documentation/getChipEffects">getChipEffects</a> respectivement. Les effets passifs des armes oubliées sont aussi récupérables dans le même format avec la fonction <a href="/help/documentation/getWeaponPassiveEffects">getWeaponPassiveEffects</a>. Le résultat est une liste d'effets sous forme de tableau de tableaux. Chaque effet est constitué :

- d'un type représentant quelle action cet effet aura sur le jeu en indice 0
- du jet minimum de l'effet (0 si l'effet n'a pas d'application numérique) en indice 1
- du jet maximum de l'effet (0 si l'effet n'a pas d'application numérique) en indice 2
- du nombre de tours durant lesquels l'effet reste actif en indice 3
- un masque binaire pour déterminer les cibles affectées par l'effet en indice 4
- un masque binaire pour déterminer les modificateurs de l'effet en indice 5


### Type

<table>
	<tr>
		<th>Nom de la constante</th>
		<th>Valeur</th>
		<th>Action</th>
	</tr>
	<tr>
		<td>EFFECT_DAMAGE</td>
		<td>1</td>
		<td>Retire des points de vie à une entité. Amplifié par la force. Interagit avec les boucliers, le vol de vie, et le retour de dégâts. Réduit le maximum de points de vie de 5% du montant retiré.</td>
	</tr>
	<tr>
		<td>EFFECT_HEAL</td>
		<td>2</td>
		<td>Rend des points de vie à une entité, limité par le maximum de points de vie. Amplifié par la sagesse.</td>
	</tr>
	<tr>
		<td>EFFECT_BUFF_STRENGTH</td>
		<td>3</td>
		<td>Procure de la force à une entité. Amplifié par la science.</td>
	</tr>
	<!-- <tr>
		<td>EFFECT_AGILITY</td>
		<td>4</td>
		<td>Augmente l'agilité de la cible.</td>
	</tr> -->
	<tr>
		<td>EFFECT_BUFF_AGILITY</td>
		<td>4</td>
		<td>Procure de l'agilité à une entité. Amplifié par la science.</td>
	</tr>
	<tr>
		<td>EFFECT_RELATIVE_SHIELD</td>
		<td>5</td>
		<td>Procure un bouclier relatif, réduisant les PV retirés par les dégâts d'un montant relatif. Amplifié par la résistance.</td>
	</tr>
	<tr>
		<td>EFFECT_ABSOLUTE_SHIELD</td>
		<td>6</td>
		<td>Procure du bouclier absolu, réduisant les PV retirés par les dégâts d'un montant fixe. Amplifié par la résistance.</td>
	</tr>
	<tr>
		<td>EFFECT_BUFF_MP</td>
		<td>7</td>
		<td>Procure des points de mouvement à une entité. Amplifié par la science.</td>
	</tr>
	<tr>
		<td>EFFECT_BUFF_TP</td>
		<td>8</td>
		<td>Procure des points de tour à une entité. Amplifié par la science.</td>
	</tr>
	<tr>
		<td>EFFECT_DEBUFF</td>
		<td>9</td>
		<td>Réduit la valeur de tous les effets présents sur une entité d'un pourcentage.</td>
	</tr>
	<tr>
		<td>EFFECT_TELEPORT</td>
		<td>10</td>
		<td>Change la position du lanceur.</td>
	</tr>
	<tr>
		<td>EFFECT_INVERT</td>
		<td>11</td>
		<td>Échange la position du lanceur avec celle de l'entité cible.</td>
	</tr>
	<tr>
		<td>EFFECT_BOOST_MAX_LIFE</td>
		<td>12</td>
		<td>Augmente les points de vie et le maximum de points de vie d'une entité. Amplifié par la sagesse.</td>
	</tr>
	<tr>
		<td>EFFECT_POISON</td>
		<td>13</td>
		<td>Retire des points de vie à une entité. Amplifié par la magie. Réduit le maximum de points de vie de 10% du montant retiré.</td>
	</tr>
	<tr>
		<td>EFFECT_SUMMON</td>
		<td>14</td>
		<td>Invoque un bulbe. Aucun effet si la limite d'invocation de l'équipe est atteinte.</td>
	</tr>
	<tr>
		<td>EFFECT_RESURRECT</td>
		<td>15</td>
		<td>Ressuscite une entité (PV max = moitié du PV max avant résurrection, PV courant = quart du PV max avant résurrection).</td>
	</tr>
	<tr>
		<td>EFFECT_KILL</td>
		<td>16</td>
		<td>Retire tous les points de vie d'une entité.</td>
	</tr>
	<tr>
		<td>EFFECT_SHACKLE_MP</td>
		<td>17</td>
		<td>Retire des points de mouvement à une entité. Amplifié par la magie.</td>
	</tr>
	<tr>
		<td>EFFECT_SHACKLE_TP</td>
		<td>18</td>
		<td>Retire des points de tour à une entité. Amplifié par la magie.</td>
	</tr>
	<tr>
		<td>EFFECT_SHACKLE_STRENGTH</td>
		<td>19</td>
		<td>Retire de la force à une entité. Amplifié par la magie.</td>
	</tr>
	<tr>
		<td>EFFECT_DAMAGE_RETURN</td>
		<td>20</td>
		<td>Procure du renvoi de dégâts à une entité, retirant des PV aux entités infligeant des dégâts au bénéficiaire. Amplifié par l'agilité. Réduit le maximum de PV de 5% du montant retiré.</td>
	</tr>
	<tr>
		<td>EFFECT_BUFF_RESISTANCE</td>
		<td>21</td>
		<td>Procure de la résistance à une entité. Amplifié par la science.</td>
	</tr>
	<tr>
		<td>EFFECT_BUFF_WISDOM</td>
		<td>22</td>
		<td>Procure de la sagesse à une entité. Amplifié par la science.</td>
	</tr>
	<tr>
		<td>EFFECT_ANTIDOTE</td>
		<td>23</td>
		<td>Retire tous les poisons (EFFECT_POISON) présents sur une cible.</td>
	</tr>
	<tr>
		<td>EFFECT_SHACKLE_MAGIC</td>
		<td>24</td>
		<td>Retire de la magie à une entité. Amplifié par la magie.</td>
	</tr>
	<tr>
		<td>EFFECT_AFTEREFFECT</td>
		<td>25</td>
		<td>Retire des points de vie à une entité. Amplifié par la science. Réduit le maximum de PV de 5% du montant retiré.</td>
	</tr>
	<tr>
		<td>EFFECT_VULNERABILITY</td>
		<td>26</td>
		<td>Retire du bouclier relatif à une entité. N'est pas amplifié. Augmente les PV retirés par les dégâts d'un montant relatif.</td>
	</tr>
	<tr>
		<td>EFFECT_ABSOLUTE_VULNERABILITY</td>
		<td>27</td>
		<td>Retire du bouclier absolu à une entité. N'est pas amplifié. Augmente les PV retirés par les dégâts d'un montant absolu.</td>
	</tr>
	<tr>
		<td>EFFECT_LIFE_DAMAGE</td>
		<td>28</td>
		<td>Retire des PV selon un pourcentage de la vie du lanceur. Interagit avec les boucliers et le retour de dégâts. Réduit le maximum de PV de 5% du montant retiré.</td>
	</tr>
	<tr>
		<td>EFFECT_STEAL_ABSOLUTE_SHIELD</td>
		<td>29</td>
		<td>Retire du bouclier absolu (EFFECT_ABSOLUTE_SHIELD) à la cible et le restitue au lanceur.</td>
	</tr>
	<tr>
		<td>EFFECT_NOVA_DAMAGE</td>
		<td>30</td>
		<td>Retire des points de vie max. Amplifié par la science.</td>
	</tr>
	<tr>
		<td>EFFECT_RAW_BUFF_MP</td>
		<td>31</td>
		<td>Procure des points de mouvement à une entité. Non amplifiable.</td>
	</tr>
	<tr>
		<td>EFFECT_RAW_BUFF_TP</td>
		<td>32</td>
		<td>Procure des points de tour à une entité. Non amplifiable.</td>
	</tr>
	<tr>
		<td>EFFECT_POISON_TO_SCIENCE</td>
		<td>33</td>
		<td>Procure de la science en fonction des dégâts poison (EFFECT_POISON) reçus.</td>
	</tr>
	<tr>
		<td>EFFECT_DAMAGE_TO_ABSOLUTE_SHIELD</td>
		<td>34</td>
		<td>Procure du bouclier absolu (EFFECT_ABSOLUTE_SHIELD) en fonction des dégâts reçus (EFFECT_DAMAGE).</td>
	</tr>
	<tr>
		<td>EFFECT_DAMAGE_TO_STRENGTH</td>
		<td>35</td>
		<td>Procure de la force en fonction des dégâts reçus (EFFECT_DAMAGE).</td>
	</tr>
	<tr>
		<td>EFFECT_NOVA_DAMAGE_TO_MAGIC</td>
		<td>36</td>
		<td>Procure de la magie en fonction des dégâts Nova (EFFECT_NOVA_DAMAGE) reçus.</td>
	</tr>
	<tr>
		<td>EFFECT_RAW_ABSOLUTE_SHIELD</td>
		<td>37</td>
		<td>Procure du bouclier absolu, réduisant les PV retirés par les dégâts (EFFECT_DAMAGE) d'un montant fixe. Non amplifiable.</td>
	</tr>
	<tr>
		<td>EFFECT_RAW_BUFF_STRENGTH</td>
		<td>38</td>
		<td>Procure de la force à une entité. Non amplifiable.</td>
	</tr>
	<tr>
		<td>EFFECT_RAW_BUFF_MAGIC</td>
		<td>39</td>
		<td>Procure de la magie à une entité. Non amplifiable.</td>
	</tr>
	<tr>
		<td>EFFECT_RAW_BUFF_SCIENCE</td>
		<td>40</td>
		<td>Procure de la science à une entité. Non amplifiable.</td>
	</tr>
	<tr>
		<td>EFFECT_RAW_BUFF_AGILITY</td>
		<td>41</td>
		<td>Procure de l'agilité à une entité. Non amplifiable.</td>
	</tr>
	<tr>
		<td>EFFECT_RAW_BUFF_RESISTANCE</td>
		<td>42</td>
		<td>Procure de la résistance à une entité. Non amplifiable.</td>
	</tr>
	<tr>
		<td>EFFECT_PROPAGATION</td>
		<td>43</td>
		<td>Se propage aux entités voisines de la cible à la fin de son tour.</td>
	</tr>
	<tr>
		<td>EFFECT_RAW_BUFF_WISDOM</td>
		<td>44</td>
		<td>Procure de la sagesse à une entité. Non amplifiable.</td>
	</tr>
	<tr>
		<td>EFFECT_NOVA_VITALITY</td>
		<td>45</td>
		<td>Augmente la vie max de la cible. Amplifié par la science.</td>
	</tr>
	<tr>
		<td>EFFECT_ATTRACT</td>
		<td>46</td>
		<td>Attire la première entité en ligne sur la case cible.</td>
	</tr>
	<tr>
		<td>EFFECT_SHACKLE_AGILITY</td>
		<td>47</td>
		<td>Retire de l'agilité à une entité. Amplifié par la magie.</td>
	</tr>
	<tr>
		<td>EFFECT_SHACKLE_WISDOM</td>
		<td>48</td>
		<td>Retire de la sagesse à une entité. Amplifié par la magie.</td>
	</tr>
	<tr>
		<td>EFFECT_REMOVE_SHACKLES</td>
		<td>49</td>
		<td>Retire toutes les entraves (EFFECT_SHACKLE_*) de la cible.</td>
	</tr>
	<tr>
		<td>EFFECT_MOVED_TO_MP</td>
		<td>50</td>
		<td>Augmente les PM de l'entité cible pour chaque déplacement subi.</td>
	</tr>
	<tr>
		<td>EFFECT_PUSH</td>
		<td>51</td>
		<td>Pousse la première entité de la ligne sur la case cible.</td>
	</tr>
	<tr>
		<td>EFFECT_RAW_BUFF_POWER</td>
		<td>52</td>
		<td>Procure de la puissance à une entité. Non amplifié. Utilisé par la puce [[Maturation]], ainsi que pour la puissance gagnée en [[Battle Royale]] et en tuant un [[Coffres|coffre]].</td>
	</tr>
	<tr>
		<td>EFFECT_REPEL</td>
		<td>53</td>
		<td>Éloigne l'entité cible d'un nombre de cases donné en ligne droite.</td>
	</tr>
	<tr>
		<td>EFFECT_RAW_RELATIVE_SHIELD</td>
		<td>54</td>
		<td>Procure un bouclier relatif, réduisant les PV retirés par les dégâts (EFFECT_DAMAGE) d'un montant relatif. Non amplifié par la résistance.</td>
	</tr>
	<tr>
		<td>EFFECT_ALLY_KILLED_TO_AGILITY</td>
		<td>55</td>
		<td>Donne de l'agilité à la cible pour chaque allié mort (hors invocations).</td>
	</tr>
	<tr>
		<td>EFFECT_KILL_TO_TP</td>
		<td>56</td>
		<td>Augmente les PT de la cible pour chaque mort qu'elle cause.</td>
	</tr>
	<tr>
		<td>EFFECT_RAW_HEAL</td>
		<td>57</td>
		<td>Rend des points de vie à une entité, limité par le maximum de PV. Non amplifié par la sagesse.</td>
	</tr>
	<tr>
		<td>EFFECT_CRITICAL_TO_HEAL</td>
		<td>58</td>
		<td>Soigne pour chaque coup critique effectué par l'entité cible.</td>
	</tr>
	<tr>
		<td>EFFECT_ADD_STATE</td>
		<td>59</td>
		<td>Ajoute un [[États|état]] à l'entité cible.</td>
	</tr>
	<tr>
		<td>EFFECT_TOTAL_DEBUFF</td>
		<td>60</td>
		<td>Retire 100% (130% en cas de Coup Critique) des effets de la cible.</td>
	</tr>
	<tr>
		<td>EFFECT_STEAL_LIFE</td>
		<td>61</td>
		<td>Soigne sa cible du total de l'effet précédent, limité par le maximum de PV (avec EFFECT_MODIFIER_ON_CASTER, la cible est le lanceur, comme sur le [[Fusil quantique]]).</td>
	</tr>
	<tr>
		<td>EFFECT_MULTIPLY_STATS</td>
		<td>62</td>
		<td>Multiplie les stats de la cible par la valeur de l'effet.</td>
	</tr>
	<tr>
		<td>EFFECT_DAMAGE_TO_RESISTANCE</td>
		<td>63</td>
		<td>Procure de la résistance en fonction des dégâts reçus (EFFECT_DAMAGE).</td>
	</tr>
	<tr>
		<td>EFFECT_SUPERINFECTION</td>
		<td>64</td>
		<td>Convertit un pourcentage des poisons (EFFECT_POISON) de la cible en dégâts immédiats. Chaque poison perd un tour.</td>
	</tr>
</table>

### Valeur min et max
Tous les effets indiquent une valeur minimale et maximale. La valeur finale sera tirée au hasard entre le minimum et le maximum.

Si vous voulez être sûrs de ne pas surestimer la valeur de l'effet, utilisez le min. Si vous vous sentez chanceux, visez le max. Vous êtes indécis ? Une moyenne entre le min et le max saura vous satisfaire.

À vous de décider quelle valeur vous pensez avoir !

La formule suivante vous permet de choisir un coefficient de confiance : s'il est à 0, `valeur_finale` sera égal à `effect_min`, s'il est à 1, `valeur_finale` sera égal à `effect_max`. Ici il est à `0.5` pour obtenir la moyenne.
```
var effect_min = effect[1];
var effect_max = effect[2];
var valeur_finale = effect_min + (effect_max - effect_min) * 0.5;
```

N'oubliez pas que la valeur de l'effet peut être multipliée par 1.3 en cas de [[Coup critique]] !

### Durée

Il s'agit du nombre de tours pendant lesquels l'effet sera actif sur la cible.

Dans le cas des effets ponctuels (soins, poisons, dégâts), une valeur de 0 signifie que l'effet aura lieu au moment où l'effet est lancé, et une valeur non nulle (1 ou plus) le fera agir au début du tour de la cible.

### Entités affectées

Les entités affectées par un effet sont encodées de manière binaire : si le bit correspondant à une catégorie d'entité vaut 1, cette catégorie sera affectée par l'effet.

Tester si une entité est vulnérable se fait alors en utilisant l'opérateur bit à bit ET (de symbole &), permettant ici de vérifier l'état d'un unique bit du nombre donné (les opérateurs == et === ne peuvent pas être utilisés : plusieurs bits peuvent être actifs simultanément).

<table>
	<tr>
		<th>Effet</th>
		<th>Valeur (binaire)</th>
		<th>Valeur (numérique)</th>
		<th>Entités affectées</th>
	</tr>
	<tr>
		<td>EFFECT_TARGET_ENEMIES</td>
		<td>00001</td>
		<td>1 </td>
		<td> ennemis de l'entité qui applique l'effet </td>
	</tr>
	<tr>
		<td>EFFECT_TARGET_ALLIES</td>
		<td>00010</td>
		<td>2 </td>
		<td> entités alliées de celle qui applique l'effet </td>
	</tr>
	<tr>
		<td>EFFECT_TARGET_CASTER</td>
		<td>00100</td>
		<td>4 </td>
		<td> entité qui applique l'effet </td>
	</tr>
	<tr>
		<td>EFFECT_TARGET_NON_SUMMONS</td>
		<td>01000</td>
		<td>8 </td>
		<td> poireaux, coffres, tourelles et mobs (qui ne sont pas des bulbes) </td>
	</tr>
	<tr>
		<td>EFFECT_TARGET_SUMMONS</td>
		<td>10000</td>
		<td>16 </td>
		<td> bulbes </td>
	</tr>
</table>

Par exemple, si le nombre représentant les entités affectées est 14 (en binaire : 01110), cela signifie que les entités affectées par l'effet sont les poireaux alliés, ainsi que celui qui applique l'effet. Donc, les bulbes et les ennemis ne seront pas affectés.

Le code suivant permet de tester si un effet affecte les bulbes ennemis : 
```
var targets = effect[4];
if (targets & EFFECT_TARGET_ENEMIES and targets & EFFECT_TARGET_SUMMONS) {
    //les bulbes ennemis sont affectés
}
```

### Modificateurs
Comme les entités affectées, les modificateurs sont encodés de manière binaire. Ces modificateurs s'appliquent sur l'effet pour en modifier la cible ou la valeur.
<table>
	<tr>
		<td>EFFECT_MODIFIER_STACKABLE</td>
		<td>00001</td>
		<td>1 </td>
		<td> L'effet est cumulable </td>
	</tr>
	<tr>
		<td>EFFECT_MODIFIER_MULTIPLIED_BY_TARGETS</td>
		<td>00010</td>
		<td>2 </td>
		<td> L'effet est multiplié par le nombre de cibles touchées dans la zone </td>
	</tr>
	<tr>
		<td>EFFECT_MODIFIER_ON_CASTER</td>
		<td>00100</td>
		<td>4 </td>
		<td>Affecte toujours le lanceur.</td>
	</tr>
	<tr>
		<td>EFFECT_MODIFIER_NOT_REPLACEABLE</td>
		<td>01000</td>
		<td>8 </td>
		<td>Non remplaçable.</td>
	</tr>
	<tr>
		<td>EFFECT_MODIFIER_IRREDUCTIBLE</td>
		<td>10000</td>
		<td>16 </td>
		<td>Irréductible.</td>
	</tr>
</table>

Le modificateur `EFFECT_MODIFIER_STACKABLE` permet d'indiquer que cet effet est cumulable, c'est-à-dire qu'une entité peut avoir plusieurs effets de ce type appliqués par la même arme ou puce. Par exemple, une entité peut avoir plusieurs effets de poison lancés par la même puce, mais ne peut pas avoir deux effets de boucliers absolus par la puce [[Casque]]. Si vous essayez de relancer [[Casque]] sur un poireau qui a déjà l'effet de [[Casque]], l'effet original sera remplacé par le nouveau. Attention à ne pas perdre de la protection en utilisant [[Casque]] avec votre bulbe chétif sur un poireau déjà équipé par un meilleur [[Casque]] ! 

Le modificateur `EFFECT_MODIFIER_MULTIPLIED_BY_TARGETS` multiplie la valeur de base de l'effet par le nombre d'entités dans l'[[AoE]] de l'objet.

Le modificateur `EFFECT_MODIFIER_ON_CASTER` indique que cet effet s'appliquera toujours au lanceur. Il est présent par exemple sur l'effet du boost de force du [[Glaive]], ce qui permet de taper dans le vide pour gagner de la force.

Le modificateur `EFFECT_MODIFIER_NOT_REPLACEABLE` indique que cet effet ne sera pas remplacé si la cible le possède déjà (ex : lancer la [[Covid-19]] sur un poireau étant déjà infecté ne changera pas la valeur du poison subi à cause de la Covid).

Le modificateur `EFFECT_MODIFIER_IRREDUCTIBLE` indique que la valeur de cet effet ne peut pas être réduite (par exemple avec libération).


## Effets appliqués sur les entités
Ils servent à rendre compte de l'état détaillé d'une Entité. On peut les récupérer avec [getEffects](/help/documentation/getEffects). Le résultat est une liste d'effets sous forme de tableau de tableaux. Il est aussi possible de récupérer la liste des effets appliqués par une entité avec [getLaunchedEffects](/help/documentation/getLaunchedEffects), cela peut par exemple servir à décider de l'éliminer dans le cas où elle serait une figure importante de l'adversaire. Chaque effet est constitué des informations suivantes:

- le type représentant quelle action cet effet a sur l'entité, en indice 0,
- la valeur de l'effet, en indice 1,
- l'identifiant de l'entité qui a appliqué l'effet, en indice 2,
- le nombre de tours restant avant que l'effet ne disparaisse, en indice 3,
- si l'effet a été appliqué avec un coup critique, en indice 4,
- l'identifiant de l'équipement qui a servi à appliquer l'effet, en indice 5,
- l'identifiant de l'entité sur laquelle l'effet a été appliqué, en indice 6,
- le masque binaire des modificateurs de l'effet, en indice 7.

Contrairement à l'effet obtenu par [getWeaponEffects](/help/documentation/getWeaponEffects) ou [getChipEffects](/help/documentation/getChipEffects), vous avez ici un effet qui a déjà été lancé et dont la valeur est connue, pas d'estimation à faire cette fois.

Note: une entité ne peut pas cumuler plusieurs fois le même effet venant de la même arme ou puce,  sauf s'il est explicitement cumulable. Imaginons par exemple que vous ayez lancé [[Armure]] sur vous, si votre Bulbe Métallique lance la même puce [[Armure]] sur vous, elles ne s'additionneront pas. En revanche, le compteur de temps sera réinitialisé.


## Déroulement des effets

Au début du tour de chaque entité, dans l'ordre :

1. Les poisons, séquelles et soins sur la durée qu'elle subit (`EFFECT_POISON`, `EFFECT_AFTEREFFECT`, `EFFECT_HEAL`) agissent, dans l'ordre reçu, et perdent chacun 1 tour. Si elle tombe à 0 PV, elle meurt.
2. Les autres effets qu'elle a lancés perdent 1 tour.
3. Son IA s'exécute.

Un effet qui tombe à 0 tour disparaît, avec ses bonus et malus. Ainsi, un poison, une séquelle ou un soin de N tours agit exactement N fois, tandis qu'un boost de N tours disparaît au début du N-ième tour suivant de son lanceur.