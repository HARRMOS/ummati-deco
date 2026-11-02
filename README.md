# AYAH by INOMA — sculpture islamique qui récite le Coran

Objet de décoration premium (niche en goutte, panneau ajouré rétroéclairé, sphère lumineuse)
avec lecteur de sourates hors ligne, écran de sélection et contrôle depuis l'application Ummati.

## Arborescence

| Dossier | Contenu |
|---|---|
| `design/ayah_v3.py` | Modèle Blender paramétrique actuel (v3, niche en goutte) — `blender -b -P design/ayah_v3.py -- ivory preview` |
| `design/ayah_model.py`, `design/ayah_model_v1.py` | Explorations précédentes (arche) |
| `design/screen_ui.html`, `design/panel_ui.html` | Maquette de l'interface de l'écran 1,9" (liste des sourates) |
| `design/renders/` | Rendus |
| `design/import/` | Analyse du modèle de référence généré par IA |
| `cad/` | **Pièces imprimables** (STL/STEP), visserie et assemblage — voir [cad/README.md](cad/README.md) |
| `firmware/` | Firmware ESP32-S3 (PlatformIO) |

## Matériel du prototype

- ESP32-S3 DevKitC N16R8
- Ampli I2S MAX98357A + haut-parleur 4 Ω 50 mm *(à acheter)*
- Écran IPS 1,9" 170×320 ST7789 *(à acheter)*
- Lecteur microSD *(à acheter)*
- Encodeur EC11 *(à acheter)*, boutons, ruban LED adressable 5 V

## Firmware — test n°1

```bash
cd firmware
pio run -t upload -t monitor
```

Brochage : LED test GPIO4, ruban GPIO5 (via 330 Ω), boutons GPIO6/7/8 vers GND, potentiomètre GPIO1 (3V3).
À éviter sur S3 N16R8 : GPIO 35-37 (PSRAM), 19-20 (USB), 0/3/45/46 (démarrage).
