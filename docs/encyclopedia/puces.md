<!-- Snapshot local de l'encyclopédie Leek Wars (fr) :
     source : https://leekwars.com/api/encyclopedia/get/fr/Puces
     rafraîchissable via `python3 tools/sync_encyclopedia.py` -->

# Puces
> Marché

Dans Leek Wars, les poireaux peuvent utiliser des puces. Ce sont des objets achetables au [[marché]] qui permettent d'attaquer, de soigner, de se protéger, de booster, d'entraver, etc.

Contrairement aux armes, les [puces](https://leekwars.com/encyclopedia/Puces) n'ont pas besoin d'être prises en main. Si une puce est équipée sur votre poireau, il peut l'utiliser directement via la fonction [useChip](https://leekwars.com/help/documentation/useChip) (ou [summon](https://leekwars.com/help/documentation/summon) pour une puce d'invocation). Il n'y a pas besoin de la "prendre en main" avec une fonction comme [setWeapon](https://leekwars.com/help/documentation/setWeapon).

Si elles offrent ainsi plus de liberté que les armes, certaines puces sont par contre soumises à un temps de récupération, aussi appelé cooldown. Si une puce indique "Récupération : 3 tours", cela signifie que lorsque vous utilisez la puce, vous devez attendre 3 tours avant de pouvoir la réutiliser. Les fonctions [getCooldown](https://leekwars.com/help/documentation/getCooldown) et [getChipCooldown](https://leekwars.com/help/documentation/getChipCooldown) vous permettront d'obtenir des informations sur ce cooldown dans votre code. Les puces n'ayant pas de temps de récupération sont, comme les armes, soumises aux limites du nombre d’utilisations par tour. La fonction [getChipMaxUses](https://leekwars.com/help/documentation/getChipMaxUses) permet d'obtenir le nombre maximal d'utilisations par tour de la puce.


Les puces sont également soumises aux restrictions de lancement des armes. La fonction [getChipLaunchType](https://leekwars.com/help/documentation/getChipLaunchType) permet de les prendre en compte dans votre code.

- Puces à cible unique : Elles ne touchent qu'une cellule.
- Puces à cibles multiples : Ces puces peuvent toucher plusieurs cellules à la fois. On parle d'aire d'effet (ou [[AoE]]).


### Nombre de puces équipables

Depuis la version [2.40](https://leekwars.com/forum/category-6/topic-11126), le nombre de puces équipables par un poireau dépend directement de sa [[RAM]].

## Liste des puces
### Attaques
<table style="text-align:center;">
	<tr>
		<td>
			<img src="/image/chip/shock.png">
			<p>[[Décharge]]</p>
			<p>Niveau 2</p>
		</td>
		<td>
			<img src="/image/chip/pebble.png">
			<p>[[Caillou]]</p>
			<p>Niveau 4</p>
		</td>
		<td>
			<img src="/image/chip/ice.png">
			<p>[[Glaçon]]</p>
			<p>Niveau 9</p>
		</td>
		<td>
			<img src="/image/chip/rock.png">
			<p>[[Rocher]]</p>
			<p>Niveau 13</p>
		</td>
		<td>
			<img src="/image/chip/spark.png">
			<p>[[Étincelle]]</p>
			<p>Niveau 19</p>
		</td>
		<td>
			<img src="/image/chip/flash.png">
			<p>[[Éclair]]</p>
			<p>Niveau 24</p>
		</td>
		<td>
			<img src="/image/chip/flame.png">
			<p>[[Flamme]]</p>
			<p>Niveau 29</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/chip/stalactite.png">
			<p>[[Stalactite]]</p>
			<p>Niveau 50</p>
		</td>
		<td>
			<img src="/image/chip/alteration.png">
			<p>[[Altération]]</p>
			<p>Niveau 53</p>
		</td>
		<td>
			<img src="/image/chip/rockfall.png">
			<p>[[Éboulement]]</p>
			<p>Niveau 77</p>
		</td>
		<td>
			<img src="/image/chip/iceberg.png">
			<p>[[Iceberg]]</p>
			<p>Niveau 100</p>
		</td>
		<td>
			<img src="/image/chip/punishment.png">
			<p>[[Châtiment]]</p>
			<p>Niveau 147</p>
		</td>
		<td>
			<img src="/image/chip/meteorite.png">
			<p>[[Météorite]]</p>
			<p>Niveau 160</p>
		</td>
		<td>
			<img src="/image/chip/devil_strike.png">
			<p>[[Frappe du démon]]</p>
			<p>Niveau 171</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/chip/lightning.png">
			<p>[[Foudre]]</p>
			<p>Niveau 180</p>
		</td>
		<td>
			<img src="/image/chip/burning.png">
			<p>[[Brûlis]]</p>
			<p>Niveau 209</p>
		</td>
		<td>
			<img src="/image/chip/desintegration.png">
			<p>[[Désintégration]]</p>
			<p>Niveau 223</p>
		</td>
		<td>
			<img src="/image/chip/plasma.png">
			<p>[[Plasma]]</p>
			<p>Niveau 290</p>
		</td>
	</tr>
</table>

### Soins

<table style="text-align:center;">
	<tr>
		<td>
			<img src="/image/chip/bandage.png">
			<p>[[Bandage]]</p>
			<p>Niveau 3</p>
		</td>
		<td>
			<img src="/image/chip/cure.png">
			<p>[[Guérison]]</p>
			<p>Niveau 20</p>
		</td>
		<td>
			<img src="/image/chip/drip.png">
			<p>[[Perfusion]]</p>
			<p>Niveau 56</p>
		</td>
		<td>
			<img src="/image/chip/armoring.png">
			<p>[[Blindage]]</p>
			<p>Niveau 68</p>
		</td>
		<td>
			<img src="/image/chip/vaccine.png">
			<p>[[Vaccin]]</p>
			<p>Niveau 80</p>
		</td>
		<td>
			<img src="/image/chip/mutation.png">
			<p>[[Mutation]]</p>
			<p>Niveau 83</p>
		</td>
		<td>
			<img src="/image/chip/loam.png">
			<p>[[Terreau]]</p>
			<p>Niveau 111</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/chip/regeneration.png">
			<p>[[Régénération]]</p>
			<p>Niveau 122</p>
		</td>
		<td>
			<img src="/image/chip/remission.png">
			<p>[[Rémission]]</p>
			<p>Niveau 170</p>
		</td>
		<td>
			<img src="/image/chip/vampirization.png">
			<p>[[Vampirisation]]</p>
			<p>Niveau 177</p>
		</td>
		<td>
			<img src="/image/chip/serum.png">
			<p>[[Sérum]]</p>
			<p>Niveau 199</p>
		</td>
		<td>
			<img src="/image/chip/fertilizer.png">
			<p>[[Fertilisant]]</p>
			<p>Niveau 205</p>
		</td>
		<td>
			<img src="/image/chip/elevation.png">
			<p>[[Élévation]]</p>
			<p>Niveau 228</p>
		</td>
		<td>
			<img src="/image/chip/transmutation.png">
			<p>[[Transmutation]]</p>
			<p>Niveau 252</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/chip/therapy.png">
			<p>[[Thérapie]]</p>
			<p>Niveau 260</p>
		</td>
		<td>
			<img src="/image/chip/resurrection.png">
			<p>[[Résurrection]]</p>
			<p>Niveau 301</p>
		</td>
	</tr>
</table>

### Protection
<table style="text-align:center;">
	<tr>
		<td>
			<img src="/image/chip/helmet.png">
			<p>[[Casque]]</p>
			<p>Niveau 10</p>
		</td>
		<td>
			<img src="/image/chip/wall.png">
			<p>[[Mur]]</p>
			<p>Niveau 18</p>
		</td>
		<td>
			<img src="/image/chip/shield.png">
			<p>[[Bouclier]]</p>
			<p>Niveau 35</p>
		</td>
		<td>
			<img src="/image/chip/armor.png">
			<p>[[Armure]]</p>
			<p>Niveau 74</p>
		</td>
		<td>
			<img src="/image/chip/rampart.png">
			<p>[[Rempart]]</p>
			<p>Niveau 117</p>
		</td>
		<td>
			<img src="/image/chip/carapace.png">
			<p>[[Carapace]]</p>
			<p>Niveau 141</p>
		</td>
		<td>
			<img src="/image/chip/fortress.png">
			<p>[[Forteresse]]</p>
			<p>Niveau 194</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/chip/dome.png">
			<p>[[Dôme]]</p>
			<p>Niveau 243</p>
		</td>
	</tr>
</table>

### Boosts
<table style="text-align:center;">
	<tr>
		<td>
			<img src="/image/chip/protein.png">
			<p>[[Protéines]]</p>
			<p>Niveau 6</p>
		</td>
		<td>
			<img src="/image/chip/motivation.png">
			<p>[[Motivation]]</p>
			<p>Niveau 14</p>
		</td>
		<td>
			<img src="/image/chip/stretching.png">
			<p>[[Étirement]]</p>
			<p>Niveau 17</p>
		</td>
		<td>
			<img src="/image/chip/leather_boots.png">
			<p>[[Bottes de cuir]]</p>
			<p>Niveau 22</p>
		</td>
		<td>
			<img src="/image/chip/knowledge.png">
			<p>[[Connaissance]]</p>
			<p>Niveau 32</p>
		</td>
		<td>
			<img src="/image/chip/solidification.png">
			<p>[[Solidification]]</p>
			<p>Niveau 40</p>
		</td>
		<td>
			<img src="/image/chip/prism.png">
			<p>[[Prisme]]</p>
			<p>Niveau 92</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/chip/ferocity.png">
			<p>[[Férocité]]</p>
			<p>Niveau 107</p>
		</td>
		<td>
			<img src="/image/chip/whip.png">
			<p>[[Fouet]]</p>
			<p>Niveau 119</p>
		</td>
		<td>
			<img src="/image/chip/warm_up.png">
			<p>[[Échauffement]]</p>
			<p>Niveau 127</p>
		</td>
		<td>
			<img src="/image/chip/steroid.png">
			<p>[[Stéroïdes]]</p>
			<p>Niveau 134</p>
		</td>
		<td>
			<img src="/image/chip/covetousness.png">
			<p>[[Convoitise]]</p>
			<p>Niveau 139</p>
		</td>
		<td>
			<img src="/image/chip/acceleration.png">
			<p>[[Accélération]]</p>
			<p>Niveau 143</p>
		</td>
		<td>
			<img src="/image/chip/adrenaline.png">
			<p>[[Adrénaline]]</p>
			<p>Niveau 156</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/chip/wizardry.png">
			<p>[[Sorcellerie]]</p>
			<p>Niveau 166</p>
		</td>
		<td>
			<img src="/image/chip/winged_boots.png">
			<p>[[Bottes ailées]]</p>
			<p>Niveau 175</p>
		</td>
		<td>
			<img src="/image/chip/collar.png">
			<p>[[Collier]]</p>
			<p>Niveau 182</p>
		</td>
		<td>
			<img src="/image/chip/precipitation.png">
			<p>[[Précipitation]]</p>
			<p>Niveau 192</p>
		</td>
		<td>
			<img src="/image/chip/reflexes.png">
			<p>[[Réflexes]]</p>
			<p>Niveau 197</p>
		</td>
		<td>
			<img src="/image/chip/seven_league_boots.png">
			<p>[[Bottes de 7 lieues]]</p>
			<p>Niveau 203</p>
		</td>
		<td>
			<img src="/image/chip/doping.png">
			<p>[[Dopage]]</p>
			<p>Niveau 207</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/chip/rage.png">
			<p>[[Rage]]</p>
			<p>Niveau 226</p>
		</td>
		<td>
			<img src="/image/chip/bark.png">
			<p>[[Écorce]]</p>
			<p>Niveau 234</p>
		</td>
		<td>
			<img src="/image/chip/maturation.png">
			<p>[[Maturation]]</p>
			<p>Niveau 267</p>
		</td>
	</tr>
</table>

### Bulbes
<table style="text-align:center;">
	<tr>
		<td>
			<img width=50 src="/image/bulb/puny_bulb_front.png">
			<p>[[Bulbe Chétif]]</p>
			<p>Niveau 48</p>
		</td>
		<td>
			<img width=50 src="/image/plant/corn_front.png">
			<p>[[Maïs]]</p>
			<p>Niveau 63</p>
		</td>
		<td>
			<img width=50 src="/image/bulb/rocky_bulb_front.png">
			<p>[[Bulbe Rocheux]]</p>
			<p>Niveau 105</p>
		</td>
		<td>
			<img width=50 src="/image/bulb/iced_bulb_front.png">
			<p>[[Bulbe Glacé]]</p>
			<p>Niveau 130</p>
		</td>
		<td>
			<img width=50 src="/image/plant/prototaxite_front.png">
			<p>[[Prototaxite]]</p>
			<p>Niveau 152</p>
		</td>
		<td>
			<img width=50 src="/image/bulb/healer_bulb_front.png">
			<p>[[Bulbe Guérisseur]]</p>
			<p>Niveau 174</p>
		</td>
		<td>
			<img width=50 src="/image/plant/chilli_pepper_front.png">
			<p>[[Piment]]</p>
			<p>Niveau 179</p>
		</td>
	</tr>
	<tr>
		<td>
			<img width=50 src="/image/bulb/fire_bulb_front.png">
			<p>[[Bulbe Enflammé]]</p>
			<p>Niveau 190</p>
		</td>
		<td>
			<img width=50 src="/image/bulb/wizard_bulb_front.png">
			<p>[[Bulbe Magicien]]</p>
			<p>Niveau 215</p>
		</td>
		<td>
			<img width=50 src="/image/bulb/metallic_bulb_front.png">
			<p>[[Bulbe Métallique]]</p>
			<p>Niveau 230</p>
		</td>
		<td>
			<img width=50 src="/image/bulb/savant_bulb_front.png">
			<p>[[Bulbe Savant]]</p>
			<p>Niveau 250</p>
		</td>
		<td>
			<img width=50 src="/image/bulb/tactician_bulb_front.png">
			<p>[[Bulbe Tacticien]]</p>
			<p>Niveau 270</p>
		</td>
		<td>
			<img width=50 src="/image/bulb/lightning_bulb_front.png">
			<p>[[Bulbe Foudroyant]]</p>
			<p>Niveau 280</p>
		</td>
	</tr>
</table>

### Entraves
<table style="text-align:center;">
	<tr>
		<td>
			<img src="/image/chip/tranquilizer.png">
			<p>[[Tranquillisant]]</p>
			<p>Niveau 65</p>
		</td>
		<td>
			<img src="/image/chip/slow_down.png">
			<p>[[Ralentissement]]</p>
			<p>Niveau 98</p>
		</td>
		<td>
			<img src="/image/chip/soporific.png">
			<p>[[Somnifère]]</p>
			<p>Niveau 145</p>
		</td>
		<td>
			<img src="/image/chip/crushing.png">
			<p>[[Écrasement]]</p>
			<p>Niveau 158</p>
		</td>
		<td>
			<img src="/image/chip/ball_and_chain.png">
			<p>[[Boulet]]</p>
			<p>Niveau 184</p>
		</td>
		<td>
			<img src="/image/chip/fracture.png">
			<p>[[Fracture]]</p>
			<p>Niveau 240</p>
		</td>
		<td>
			<img src="/image/chip/brainwashing.png">
			<p>[[Décervelage]]</p>
			<p>Niveau 266</p>
		</td>
	</tr>
</table>

### Tactiques
<table style="text-align:center;">
	<tr>
		<td>
			<img src="/image/chip/liberation.png">
			<p>[[Libération]]</p>
			<p>Niveau 60</p>
		</td>
		<td>
			<img src="/image/chip/jump.png">
			<p>[[Saut]]</p>
			<p>Niveau 70</p>
		</td>
		<td>
			<img src="/image/chip/antidote.png">
			<p>[[Antidote]]</p>
			<p>Niveau 114</p>
		</td>
		<td>
			<img src="/image/chip/grapple.png">
			<p>[[Grappin]]</p>
			<p>Niveau 120</p>
		</td>
		<td>
			<img src="/image/chip/boxing_glove.png">
			<p>[[Gant de boxe]]</p>
			<p>Niveau 140</p>
		</td>
		<td>
			<img src="/image/chip/manumission.png">
			<p>[[Affranchissement]]</p>
			<p>Niveau 149</p>
		</td>
		<td>
			<img src="/image/chip/inversion.png">
			<p>[[Inversion]]</p>
			<p>Niveau 150</p>
		</td>
		</tr>
	<tr>
		<td>
			<img src="/image/chip/repotting.png">
			<p>[[Rempotage]]</p>
			<p>Niveau 163</p>
		</td>
		<td>
			<img src="/image/chip/hemorrhage.png">
			<p>[[Hémorragie]]</p>
			<p>Niveau 196</p>
		</td>
		<td>
			<img src="/image/chip/teleportation.png">
			<p>[[Téléportation]]</p>
			<p>Niveau 200</p>
		</td>
		<td>
			<img src="/image/chip/neutronium.png">
			<p>[[Neutronium]]</p>
			<p>Niveau 262</p>
		</td>
	</tr>
</table>


### Poisons
<table style="text-align:center;">
	<tr>
		<td>
			<img src="/image/chip/venom.png">
			<p>[[Venin]]</p>
			<p>Niveau 42</p>
		</td>
		<td>
			<img src="/image/chip/toxin.png">
			<p>[[Toxine]]</p>
			<p>Niveau 125</p>
		</td>
		<td>
			<img src="/image/chip/plague.png">
			<p>[[Peste]]</p>
			<p>Niveau 210</p>
		</td>
		<td>
			<img src="/image/chip/covid.png">
			<p>[[COVID-19]]</p>
			<p>Niveau 220</p>
		</td>
		<td>
			<img src="/image/chip/superinfection.png">
			<p>[[Surinfection]]</p>
			<p>Niveau 232</p>
		</td>
		<td>
			<img src="/image/chip/arsenic.png">
			<p>[[Arsenic]]</p>
			<p>Niveau 285</p>
		</td>
	</tr>
</table>

### Renvois
<table style="text-align:center;">
	<tr>
		<td>
			<img src="/image/chip/thorn.png">
			<p>[[Épine]]</p>
			<p>Niveau 132</p>
		</td>
		<td>
			<img src="/image/chip/mirror.png">
			<p>[[Miroir]]</p>
			<p>Niveau 246</p>
		</td>
		<td>
			<img src="/image/chip/bramble.png">
			<p>[[Ronce]]</p>
			<p>Niveau 278</p>
		</td>
	</tr>
</table>

## Puces spéciales
Les puces suivantes sont réservées aux [[Les Boss|boss]] et **ne peuvent pas** être obtenues ni équipées sur vos poireaux en dehors des tests.

<table style="text-align:center;">
	<tr>
		<td>
			<img src="/image/chip/kemuridama.png">
			<p>[[Kemuridama]]</p>
		</td>
		<td>
			<img src="/image/chip/shuriken.png">
			<p>[[Shuriken]]</p>
		</td>
		<td>
			<img src="/image/chip/divine_protection.png">
			<p>[[Protection divine]]</p>
		</td>
		<td>
			<img src="/image/chip/apocalypse.png">
			<p>[[Apocalypse]]</p>
		</td>
		<td>
			<img src="/image/chip/kill.png">
			<p>[[Tuer]]</p>
		</td>
		<td>
			<img src="/image/chip/fire_ball.png">
			<p>[[Boule de Feu]]</p>
		</td>
		<td>
			<img src="/image/chip/trebuchet.png">
			<p>[[Trébuchet]]</p>
		</td>
		<td>
			<img src="/image/chip/exasperation.png">
			<p>[[Exaspération]]</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/chip/awakening.png">
			<p>[[Réveil]]</p>
		</td>
		<td>
			<img src="/image/chip/thunder.png">
			<p>[[Tonnerre]]</p>
		</td>
		<td>
			<img src="/image/chip/grail_protection.png">
			<p>[[Protection du Graal]]</p>
		</td>
	</tr>
</table>

### Puces de plantes
Ces puces sont uniquement accessibles aux [[plantes]].
<table style="text-align:center;">
	<tr>
		<td>
			<img src="/image/chip/sugar.png">
			<p>[[Sucre]]</p>
			<p>Niveau 1</p>
		</td>
		<td>
			<img src="/image/chip/popcorn.png">
			<p>[[Pop-Corn]]</p>
			<p>Niveau 1</p>
		</td>
		<td>
			<img src="/image/chip/piquant.png">
			<p>[[Piquant]]</p>
			<p>Niveau 1</p>
		</td>
		<td>
			<img src="/image/chip/capsaicin.png">
			<p>[[Capsaïcine]]</p>
			<p>Niveau 1</p>
		</td>
	</tr>
</table>