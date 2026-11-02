# AYAH — Pièces imprimables et assemblage

Généré par [`ayah_parts.py`](ayah_parts.py) (CadQuery). Fichiers : `stl/` pour Bambu Studio, `step/` pour retoucher dans Fusion/FreeCAD, `apercus/` pour les vues de contrôle.

```bash
# régénérer après modification d'une cote (depuis le dossier cad/)
../.venv-cad/bin/python ayah_parts.py
blender -b -P render_parts.py      # vues de contrôle
```

## ⚠️ Avant d'imprimer les grosses pièces

Les cotes des composants que tu n'as **pas encore reçus** sont des valeurs typiques. Mesure-les et corrige le haut de `ayah_parts.py` :

| Paramètre | Valeur actuelle | À mesurer sur |
|---|---|---|
| `ESP_L`, `ESP_W` | 64 × 28,5 mm | ta carte ESP32-S3 (sans les broches) |
| `AMP_L`, `AMP_W` | 19,5 × 18,5 mm | module MAX98357A |
| `SD_L`, `SD_W` | 42 × 24,5 mm | module microSD |
| `SPK_D` | 52 mm | diamètre extérieur du haut-parleur |
| `SCR_ACTIVE`, `SCR_PCB` | 43,5 × 23,5 / 52 × 28 × 4,5 mm | écran 1,9" (zone visible + circuit) |
| `ENC_HOLE`, `SHAFT_D`, `SHAFT_FLAT` | 7,3 / 6,0 / 4,5 mm | encodeur EC11 |

**Commence par imprimer les petites pièces** (molette, bride, barrette) pour valider tes tolérances avant les 15 h de la niche.

## Pièces (13)

| # | Fichier | Couleur | Orientation | Supports | Remarques |
|---|---|---|---|---|---|
| 01 | `01_niche_coque` | ivoire mat | debout, pied sur le plateau | **arborescents**, intérieur de la niche | 164 × 89 × 172 mm, 3 parois, 15 % gyroïde, couches 0,16 |
| 02 | `02_panneau_ajoure_OR` | or (silk) | à plat | non | couches 0,12, s'emboîte par l'avant dans la feuillure |
| 03 | `03_base_coque` | ivoire mat | **à l'envers** (dessus sur le plateau) | arborescents (bossages écran) | 166 × 133 × 40 mm |
| 04 | `04_fond_electronique` | ivoire / gris | à plat | non | porte toute l'électronique |
| 05 | `05_bride_haut_parleur` | n'importe | à plat | non | |
| 06 | `06_barrette_esp32` | n'importe | à plat | non | |
| 07 | `07_support_ecran` | n'importe | cavité vers le haut | non | |
| 08 | `08_cadre_ecran_NOIR` | noir | face gravée vers le haut | non | pictogrammes ◀ ▶ = zones tactiles |
| 09 | `09_molette_OR` | or | dessus sur le plateau | non | axe en D |
| 10 | `10_socle_OR` | or | à plat | non | 2 pions de centrage |
| 11 | `11_diffuseur_BLANC` | blanc translucide | à plat | non | 1 mm |
| 12 | `12_sphere_haut_BLANC` | blanc translucide | coupe à plat | non | étoiles en lithophanie (paroi amincie) |
| 13 | `13_sphere_bas_BLANC` | blanc translucide | coupe à plat | non | ouverture basse = entrée de la lumière |

## Visserie

| Article | Qté | Usage |
|---|---|---|
| Inserts laiton M3 à chaud (Ø4 × 5,7 mm) | 15 | colonnes de la base (4), bossages écran (2), pattes niche (4), bride HP (3), barrette ESP32 (2) |
| Vis M3 × 8 tête fraisée | 4 | fond → base |
| Vis M3 × 8 tête cylindrique | 8 | niche → base (4, depuis l'intérieur de la base), support écran (2), barrette ESP32 (2) |
| Vis M3 × 6 | 3 | bride du haut-parleur |
| Tube laiton Ø4 mm, ~80 mm | 1 | suspension de la sphère (emmanché serré, sans colle) |
| Patins silicone Ø10 | 4 | sous le fond |
| Ruban cuivre adhésif | ~10 cm | 2 pastilles tactiles derrière ◀ ▶ |

## Architecture

```
            ┌──────── NICHE (01) ────────┐
            │  panneau ajouré (02)       │  ← ruban LED dans la cavité de l'aile
            │  sphère (12+13) sur tube   │  ← éclairée PAR LE DESSOUS (aucun fil dans le tube)
            └──── 4 vis M3 par dessous ──┘
  socle (10) + diffuseur (11) ─── LED sous le trou central
            ┌──────── BASE (03) ─────────┐
  cadre noir (08) + écran + support (07)    molette (09) sur EC11
  arrière : 2 ports USB-C de l'ESP32 + fente microSD
            └──── 4 vis M3 fraisées ─────┘
            ┌──── FOND (04) ─────────────┐  ← s'enlève avec toute l'électronique
  ESP32 (posée composants vers le bas, broches vers le haut) + barrette (06)
  MAX98357A, module SD, haut-parleur tirant vers le bas + bride (05)
            └────────────────────────────┘
```

**Câblage LED :** GPIO5 → 330 Ω → LED sous le socle (3 LED de ruban, collées sous le trou) → ruban de l'aile (2 à 4 tronçons de 3 LED reliés par fils fins, passés par le trou de l'aile). Une seule ligne de données pilote tout.

**Commandes :** molette = volume / navigation, appui = lecture/pause. ◀ ▶ = **pastilles tactiles** (ruban cuivre collé à l'intérieur derrière les pictogrammes, reliées à GPIO6 et GPIO8, broches tactiles de l'ESP32-S3). Le firmware sera adapté.

## Ordre d'assemblage

1. Poser tous les inserts au fer (230 °C, pointe pour insert), bien perpendiculaires.
2. **Fond** : haut-parleur dans son logement + bride (3 vis) ; ESP32 sur ses plots + barrette ; MAX98357A et module SD dans leurs bacs.
3. **Base** : écran contre la fenêtre + support (2 vis) ; cadre noir clipsé à l'avant ; EC11 dans son trou, écrou serré à l'extérieur, molette emmanchée ; cuivre derrière ◀ ▶.
4. Passer les fils LED par les trous du dessus de la base ; poser les LED sous le trou du socle.
5. **Niche** : ruban dans la cavité de l'aile, panneau ajouré emboîté par l'avant ; poser la niche sur la base, **4 vis depuis l'intérieur de la base**.
6. Socle + diffuseur ; sphère assemblée (2 moitiés emboîtées) suspendue au tube laiton.
7. Brancher, refermer avec le fond (4 vis).

## Limites connues (v1 mécanique)

- Aucune pièce n'a encore été imprimée : les jeux (`FIT = 0,15 mm`) sont à valider sur ta P2S.
- La niche nécessite des supports dans la voûte ; prévoir ~12–15 h.
- Pas encore de passe-câble dédié pour l'USB : on utilise directement les ports de l'ESP32 (prototype). La version commerciale aura un PCB unique avec son propre USB-C.
- Le PLA ramollit vers 55–60 °C : garder les LED à puissance modérée dans la cavité de l'aile.
