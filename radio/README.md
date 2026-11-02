# AYAH « Radio » — pièces imprimables

Design simplifié : arche en radio rétro, grille dorée en treillis, cartouche « القرآن الكريم », 3 touches tactiles dorées, molette, 2 haut-parleurs Ø40.
Dimensions : **170 × 78 × 150 mm** (socle compris).

```bash
../.venv-cad/bin/python ayah_radio.py          # régénère stl/ et step/
blender -b -P render_radio.py -- vert          # rendus (vert | noir | blanc)
```

## Ordre d'impression

### Étape 1 — tout de suite (ne dépend d'aucun composant)

| # | Pièce | Filament | Orientation | Supports | Réglages |
|---|---|---|---|---|---|
| 1 | `08_socle_OR` | or | à plat | non | 0,2 mm |
| 2 | `02_grille_OR` | or | **face avant sur le plateau** | non | 0,12 mm, 3 parois |
| 3 | `03_plaque_calligraphie_NOIR+OR` | noir, puis or | collerette sur le plateau, lettres vers le haut | non | 0,12 mm — **changement de filament à 3,3 mm** (curseur de couches → clic droit → changer de filament) |
| 4 | `10/11/12_touche_..._OR` | or | face gravée vers le haut | non | 0,12 mm |
| 5 | `01_corps` | noir (ou vert) | **face avant sur le plateau** | non | 0,2 mm, 3 parois, 15 % gyroïde |

### Étape 2 — quand les composants sont arrivés (mesure-les d'abord)

| # | Pièce | Dépend de |
|---|---|---|
| 6 | `04_baffle` (blanc : reflète la lumière) | haut-parleurs Ø40 |
| 7 | `05_bague_HP_x2` (×2) | haut-parleurs Ø40 |
| 8 | `09_molette_OR` | axe de l'encodeur EC11 (axe en D 6 mm) |
| 9 | `06_dos_electronique` + `07_barrette_esp32` | ESP32, MAX98357A, module SD, prise USB-C de façade |

Pas encore de filament or ? Imprime d'abord les pièces « OR » en blanc ou en gris pour valider les emboîtements.

## Visserie

| Article | Qté |
|---|---|
| Inserts laiton M3 (Ø4 × 5,7) | 10 (4 baffle, 4 dos, 2 socle) |
| Vis M3 × 8 tête cylindrique | 6 (baffle 4, socle 2) |
| Vis M3 × 8 tête fraisée | 4 (dos) |
| Vis à plastique Ø2,2 × 8 | 8 (bagues HP 6, barrette 2) |
| Ruban cuivre adhésif | 3 pastilles Ø12 (dans les touches) |
| Patins silicone Ø10 | 4 |

## Composants spécifiques à cette version

- **2 haut-parleurs Ø40 mm 8 Ω 2–3 W**, câblés **en parallèle** sur un seul MAX98357A (= 4 Ω).
- **Encodeur EC11** avec bouton poussoir : rotation = volume / choix de sourate, appui = lecture/pause.
- **Rallonge USB-C mâle → femelle à visser sur panneau** (avec data) : la prise est sur le dos, le câble va à l'ESP32.
- Touches ◀ ▶ ⏯ : **tactiles** (ruban cuivre collé dans la coupelle de chaque touche, fil vers GPIO tactile de l'ESP32-S3).
- Ruban LED adressable : 2 ou 3 tronçons de 3 LED collés sur la face avant du baffle → la grille s'illumine.

## Assemblage

1. Inserts au fer dans le corps (baffle + dos) et le socle.
2. Touches : coller le cuivre dans la coupelle, souder un fil, emboîter les touches dans la façade.
3. Encodeur EC11 dans son trou, écrou serré devant, molette emmanchée.
4. Grille dorée posée **par l'intérieur** dans l'ouverture, plaque calligraphiée derrière le cartouche.
5. Baffle (HP + LED déjà montés) vissé sur les 4 colonnes : il plaque la grille et la plaque.
6. Dos avec l'électronique, 4 vis. Socle vissé par-dessous (2 vis depuis l'intérieur avant de fermer).

## Notes

- La calligraphie vient de la police **Diwan Thuluth** (fournie avec macOS) : OK pour le prototype, mais **vérifier la licence** avant une vente — sinon utiliser une police libre (Amiri, OFL) ou une calligraphie dessinée par un calligraphe.
- Aucune pièce n'a encore été imprimée : les jeux (`FIT = 0,15 mm`) sont à valider sur ta P2S.
