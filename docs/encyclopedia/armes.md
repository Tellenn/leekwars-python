<!-- Snapshot local de l'encyclopédie Leek Wars (fr) :
     source : https://leekwars.com/api/encyclopedia/get/fr/Armes
     rafraîchissable via `python3 tools/sync_encyclopedia.py` -->

# Armes
> Marché

Dans Leek Wars, les armes doivent être "prises en main" pour être utilisées. Une arme doit non seulement être équipée sur la page du poireau, mais également tenue en main par votre poireau pendant un combat. Un poireau ne peut se servir que d'une arme à la fois. Vous pouvez changer l'arme équipée grâce à la fonction [setWeapon](https://leekwars.com/help/documentation/setWeapon). Une utilisation de cette fonction consomme 1 [[PT]], même si c'est pour changer vers l'arme déjà en main.

>Les armes n'ont pas de temps de récupération, contrairement aux [[Puces]]. Ainsi, tant qu'il vous reste des PT en quantité suffisante, vous pouvez réutiliser une arme, dans la limite de ses utilisations maximums, qui peuvent être obtenues via la fonction [getWeaponMaxUses](https://leekwars.com/help/documentation/getWeaponMaxUses).


Tout comme les puces, les armes sont sujettes à des restrictions de tir. La fonction [getWeaponLaunchType](https://leekwars.com/help/documentation/getWeaponLaunchType) permet de les prendre en compte dans votre code.

On distingue trois types d'armes :
- Armes à **cible unique** : elles ne touchent qu'une cellule.
- Armes à **cibles multiples** : ces armes peuvent toucher plusieurs cellules à la fois, on parle d'aire d'effet (ou [[AoE]]).
- Armes **laser** : ces armes tirent un [[Laser]]. Ainsi, elles ne peuvent tirer qu'en ligne et peuvent frapper plusieurs cellules.


Un poireau peut avoir jusqu'à 4 armes équipées. Au niveau 1, il ne peut en équiper que 2. Il pourra en équiper une supplémentaire aux niveaux 100 puis 200. 


Tranche de niveau | Armes équipables
----|----
Niveau 1 à 99 | 2
Niveau 100 à 199 | 3
Niveau 200 à 301 | 4


## Liste des Armes
<table style="text-align:center; table-layout: fixed; width: 100%;">
	<tr>
		<td>
			<img src="/image/weapon/pistol.png">
			<p>[[Pistolet]]</p>
			<p>Niveau 1</p>
		</td>
		<td>
			<img src="/image/weapon/machine_gun.png">
			<p>[[Machine gun]]</p>
			<p>Niveau 8</p>
		</td>
		<td>
			<img src="/image/weapon/neutrino.png">
			<p>[[Neutrino]]</p>
			<p>Niveau 12</p>
		</td>
		<td>
			<img src="/image/weapon/shotgun.png">
			<p>[[Fusil à pompe]]</p>
			<p>Niveau 16</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/weapon/magnum.png">
			<p>[[Magnum]]</p>
			<p>Niveau 27</p>
		</td>
		<td>
			<img src="/image/weapon/broadsword.png">
			<p>[[Glaive]]</p>
			<p>Niveau 30</p>
		</td>
		<td>
			<img src="/image/weapon/laser.png">
			<p>[[Laser]]</p>
			<p>Niveau 38</p>
		</td>
		<td>
			<img src="/image/weapon/double_gun.png">
			<p>[[Double gun]]</p>
			<p>Niveau 45</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/weapon/sword.png">
			<p>[[Épée]]</p>
			<p>Niveau 75</p>
		</td>
		<td>
			<img src="/image/weapon/destroyer.png">
			<p>[[Destroyer]]</p>
			<p>Niveau 85</p>
		</td>
		<td>
			<img src="/image/weapon/unstable_destroyer.png">
			<p>[[Destroyer instable]]</p>
			<p>Niveau 86</p>
		</td>
		<td>
			<img src="/image/weapon/flame_thrower.png">
			<p>[[Lance-flammes]]</p>
			<p>Niveau 90</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/weapon/b_laser.png">
			<p>[[B-Laser]]</p>
			<p>Niveau 95</p>
		</td>
		<td>
			<img src="/image/weapon/axe.png">
			<p>[[Hache]]</p>
			<p>Niveau 110</p>
		</td>
		<td>
			<img src="/image/weapon/grenade_launcher.png">
			<p>[[Lance-grenades]]</p>
			<p>Niveau 135</p>
		</td>
		<td>
			<img src="/image/weapon/illicit_grenade_launcher.png">
			<p>[[Lance-grenades illicite]]</p>
			<p>Niveau 136</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/weapon/desert_saber.png">
			<p>[[Sabre du désert]]</p>
			<p>Niveau 151</p>
		</td>
		<td>
			<img src="/image/weapon/j_laser.png">
			<p>[[J-Laser]]</p>
			<p>Niveau 153</p>
		</td>
		<td>
			<img src="/image/weapon/bazooka.png">
			<p>[[Bazooka]]</p>
			<p>Niveau 168</p>
		</td>
		<td>
			<img src="/image/weapon/plutonium_bazooka.png">
			<p>[[Bazooka au Plutonium]]</p>
			<p>Niveau 169</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/weapon/rhino.png">
			<p>[[Rhino]]</p>
			<p>Niveau 187</p>
		</td>
		<td>
			<img src="/image/weapon/sun_spear.png">
			<p>[[Lance du soleil]]</p>
			<p>Niveau 201</p>
		</td>
		<td>
			<img src="/image/weapon/electrisor.png">
			<p>[[Électriseur]]</p>
			<p>Niveau 211</p>
		</td>
		<td>
			<img src="/image/weapon/mysterious_electrisor.png">
			<p>[[Électriseur mystérieux]]</p>
			<p>Niveau 212</p>
		</td>
	</tr>
	<tr>	
		<td>
			<img src="/image/weapon/lightninger.png">
			<p>[[Foudroyeur]]</p>
			<p>Niveau 237</p>
		</td>
		<td>
			<img src="/image/weapon/enhanced_lightninger.png">
			<p>[[Foudroyeur amélioré]]</p>
			<p>Niveau 238</p>
		</td>
		<td>
			<img src="/image/weapon/glowing_saber.png">
			<p>[[Sabre lumineux]]</p>
			<p>Niveau 248</p>
		</td>
		<td>
			<img src="/image/weapon/katana.png">
			<p>[[Katana]]</p>
			<p>Niveau 257</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/weapon/dark_katana.png">
			<p>[[Katana sombre]]</p>
			<p>Niveau 258</p>
		</td>
		<td>
			<img src="/image/weapon/rifle.png">
			<p>[[Fusil]]</p>
			<p>Niveau 271</p>
		</td>
		<td>
			<img src="/image/weapon/explorer_rifle.png">
			<p><a href="https://leekwars.com/encyclopedia/fr/Fusil_de_l'explorateur">Fusil de l'explorateur</a></p>
			<p>Niveau 272</p>
		</td>
		<td>
			<img src="/image/weapon/quantum_rifle.png">
			<p>[[Fusil Quantique]]</p>
			<p>Niveau 281</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/weapon/heavy_sword.png">
			<p>[[Épée lourde]]</p>
			<p>Niveau 288</p>
		</td>
		<td>
			<img src="/image/weapon/gazor.png">
			<p>[[Gazeur]]</p>
			<p>Niveau 297</p>
		</td>
		<td>
			<img src="/image/weapon/unbridled_gazor.png">
			<p>[[Gazeur débridé]]</p>
			<p>Niveau 298</p>
		</td>
		<td>
			<img src="/image/weapon/m_laser.png">
			<p>[[M-Laser]]</p>
			<p>Niveau 299</p>
		</td>
	</tr>
	<tr>
		<td>
			<img src="/image/weapon/revoked_m_laser.png">
			<p>[[M-Laser révoqué]]</p>
			<p>Niveau 300</p>
		</td>
	</tr>
</table>

## Armes spéciales
Les armes suivantes sont réservées aux [[Les Boss|boss]] et **ne peuvent pas** être obtenues ni équipées sur vos poireaux en dehors des tests.


<table style="text-align:center; table-layout: fixed; width: 100%;">
	<tr>
		<td>
			<img src="/image/weapon/odachi.png">
			<p>[[Odachi]]</p>
		</td>
		<td>
			<img src="/image/weapon/excalibur.png">
			<p>[[Excalibur]]</p>
		</td>
		<td>
			<img src="/image/weapon/scythe.png">
			<p>[[Faux]]</p>
		</td>
	</tr>
</table>