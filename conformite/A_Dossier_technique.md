# A — Dossier technique AYAH AY-R1

> À conserver **10 ans** après la mise sur le marché du dernier exemplaire. Une version du dossier par version du produit.

## 1. Identification

| Champ | Valeur |
|---|---|
| Fabricant | INOMA — [À COMPLÉTER : forme juridique, nom du responsable] |
| Adresse postale | [À COMPLÉTER] |
| SIREN / SIRET | [À COMPLÉTER] |
| Contact | [À COMPLÉTER : e-mail dédié, ex. contact@…] |
| Nom commercial | AYAH « Radio » |
| Référence modèle | **AY-R1** |
| Variantes (coloris) | AY-R1-VE (vert), AY-R1-NO (noir), AY-R1-IV (ivoire) — électronique identique |
| Version matérielle | [À COMPLÉTER : ex. HW 1.0] |
| Version firmware | [À COMPLÉTER : ex. FW 1.0.0, empreinte SHA-256 du binaire] |
| Numérotation des lots | Voir G §1 |

## 2. Description du produit

**Usage prévu :** objet de décoration lumineux et lecteur audio pour usage **domestique intérieur**, posé sur un meuble. Permet d'écouter des fichiers audio fournis par l'utilisateur ou un service compatible, de régler le volume et l'éclairage d'ambiance. **Ce n'est pas un jouet.**

**Utilisations exclues :** extérieur, salle de bain, milieu humide, véhicule, exposition directe au soleil ou près d'une source de chaleur.

**Fonctions :**

- lecture audio (ampli I2S 3 W, 2 haut-parleurs Ø40 mm 8 Ω en parallèle) ;
- éclairage LED blanc chaud (LED adressables, intensité limitée par logiciel) ;
- commandes : 3 touches tactiles capacitives, 1 encodeur rotatif avec poussoir ;
- connexion **Wi-Fi 2,4 GHz** (IEEE 802.11 b/g/n) pour la configuration, les mises à jour et le pilotage depuis une application ;
- **Bluetooth matériellement présent dans le module mais désactivé par le firmware et non accessible à l'utilisateur.**

**Alimentation :** 5 V continu par connecteur USB-C. Courant d'entrée limité par fusible réarmable [À COMPLÉTER : référence, courant de maintien ≤ 2 A]. **Chargeur non fourni.** Pas de batterie.

**Dimensions / masse :** 170 × 78 × 150 mm — [À COMPLÉTER : masse mesurée] g.

**Matériaux accessibles :** [À COMPLÉTER : PLA ou PETG, marque et référence du filament], visserie acier zingué ou inox, inserts laiton.

**[PREUVE]** Photos à joindre : vues avant, arrière, dessus, dessous, intérieur ouvert, circuit imprimé recto/verso, étiquette.

## 3. Conception et fabrication

| Document | Référence / emplacement | Statut |
|---|---|---|
| Schéma électronique | [À COMPLÉTER : fichier, version] | ☐ |
| Circuit imprimé (fichiers de fabrication) | [À COMPLÉTER] | ☐ |
| Nomenclature (BOM) avec fournisseurs | Tableau §3.1 | ☐ |
| Plans mécaniques (STL/STEP) | `radio/stl`, `radio/step` (version figée : [À COMPLÉTER : tag Git]) | ☐ |
| Firmware (code source + binaire) | `firmware/` (tag Git : [À COMPLÉTER]) | ☐ |
| Procédure de fabrication et contrôles | G §2 | ☐ |

### 3.1 Nomenclature des composants critiques

| Fonction | Composant | Fabricant / réf. | Fournisseur | Déclaration RoHS | Certification utile |
|---|---|---|---|---|---|
| Module radio + MCU | ESP32-S3-WROOM-1-N16R8 | Espressif | [À COMPLÉTER] | ☐ | Rapports RED du module ☐ |
| Ampli audio | MAX98357A | Analog Devices (Maxim) | [À COMPLÉTER] | ☐ | — |
| Haut-parleurs ×2 | Ø40 mm 8 Ω | [À COMPLÉTER] | [À COMPLÉTER] | ☐ | — |
| LED | [À COMPLÉTER] | [À COMPLÉTER] | | ☐ | — |
| Encodeur | EC11 | [À COMPLÉTER] | | ☐ | — |
| Connecteur USB-C | [À COMPLÉTER] | | | ☐ | — |
| Fusible réarmable | [À COMPLÉTER] | | | ☐ | — |
| Boîtier | Filament [À COMPLÉTER] | | | ☐ | Fiche technique (température, classement feu) ☐ |
| Circuit imprimé nu + assemblage | [À COMPLÉTER] | | | ☐ | — |

## 4. Exigences applicables et normes

> Les versions des normes doivent être vérifiées dans la **liste des normes harmonisées publiée au Journal officiel de l'UE** (site de la Commission, « harmonised standards ») à la date de la déclaration. **[À VÉRIFIER pour chaque ligne]**

| Texte | Exigence | Norme(s) de référence | Méthode retenue | Résultat |
|---|---|---|---|---|
| **RED 2014/53/UE art. 3.1(a)** | Santé, sécurité | EN IEC 62368-1 [version] | Évaluation sur dossier + essais thermiques (§6) | ☐ |
| | Exposition aux champs | EN 62479 / EN 62311 [version] | Reprise de l'évaluation du module + calcul (§5) | ☐ |
| **RED art. 3.1(b)** | Compatibilité électromagnétique | EN 301 489-1 et EN 301 489-17 [versions] | Mesures sur le produit fini (§7) | ☐ |
| **RED art. 3.2** | Utilisation efficace du spectre | EN 300 328 [version] | Reprise des rapports du module certifié (§5) | ☐ |
| **RED art. 3.3(d)(e)(f)** — Règlement délégué (UE) 2022/30 | Cybersécurité | EN 18031-1 [version] (et -2 si données personnelles) | Évaluation documentée (§8) — **vérifier les restrictions de la citation au JOUE** | ☐ |
| **RoHS 2011/65/UE** (+ dir. déléguée 2015/863) | Substances dangereuses | EN IEC 63000 | Déclarations fournisseurs (§9) | ☐ |
| **Règlement (UE) 2023/988 (GPSR)** | Sécurité générale | — | Analyse de risques (§10), traçabilité, information | ☐ |
| **Écoconception veille** — Règlement (UE) 2023/826 | Consommation en veille / veille réseau | — | **[À VÉRIFIER : applicabilité]** ; mesure de la consommation au repos (§6.3) | ☐ |
| **REACH** (CE 1907/2006) | Substances extrêmement préoccupantes (SVHC) | — | Déclarations fournisseurs (§9) | ☐ |
| DEEE 2012/19/UE | Marquage, filière | — | Voir F | ☐ |

**Non applicables (avec justification) :**

- Directive basse tension 2014/35/UE : couverte par la RED pour un équipement radio (et tension < 75 V continu).
- EN 61000-3-2 / -3-3 (harmoniques, flicker réseau) : appareil alimenté en 5 V continu, non raccordé directement au réseau 230 V **[À VÉRIFIER avec le labo]**.
- Règlement batteries : aucune batterie.
- Directive jouets : produit non destiné aux enfants de moins de 14 ans, mention « Ce n'est pas un jouet ».

## 5. Radio et exposition aux ondes — intégration du module certifié

**Principe :** les essais radio (EN 300 328) et l'évaluation d'exposition sont **repris des rapports du fabricant du module**, à condition de respecter strictement ses consignes d'intégration.

| Condition d'intégration (guide Espressif) | Respectée ? | Preuve |
|---|---|---|
| Module utilisé **sans modification**, antenne PCB intégrée d'origine | ☐ | Photo du circuit |
| Zone sans cuivre / sans métal sous et autour de l'antenne (selon le guide) | ☐ | Plan du circuit |
| Antenne éloignée des vis, inserts, haut-parleurs (aimants) | ☐ | Photo intérieur |
| Puissance d'émission et paramètres radio **non modifiés** au-delà des réglages autorisés | ☐ | Extrait firmware |
| Bandes : 2,4 GHz uniquement | ☐ | — |

**[PREUVE]** À télécharger chez Espressif et joindre : déclaration UE et **rapports d'essais RED** du module ESP32-S3-WROOM-1 (EN 300 328, EN 301 489, EN 62368-1, évaluation d'exposition), et le **guide de conception matérielle** du module. Noter la version et la date de chaque document.

**Exposition :** [À COMPLÉTER : puissance maximale déclarée par le module, conclusion de l'évaluation du module, distance d'utilisation (> 20 cm en usage normal, objet posé)].

## 6. Sécurité électrique et thermique (EN IEC 62368-1)

### 6.1 Classification des sources d'énergie [À VÉRIFIER avec le texte de la norme]

| Énergie | Classe visée | Justification |
|---|---|---|
| Électrique | **ES1** | 5 V continu |
| Puissance (incendie) | **PS1 visé** | Puissance disponible limitée à ≤ 15 W par fusible réarmable ≤ 2 A — [PREUVE : mesure de la puissance max. disponible en défaut] |
| Thermique (surfaces touchables) | TS1 visé | Mesures §6.2 |
| Mécanique | MS1 | Objet léger, stable, pas de pièce mobile dangereuse, bords arrondis |
| Rayonnement (LED) | RS1 visé | LED d'éclairage d'ambiance, intensité limitée — [À VÉRIFIER] |

### 6.2 Essai d'échauffement — protocole

1. Appareil assemblé, fermé, posé sur un support bois, pièce à 23 ± 2 °C.
2. Alimentation 5 V avec un chargeur conforme 3 A.
3. **Cas le plus défavorable** : volume maximal (bruit rose ou récitation forte), LED à l'intensité maximale autorisée par le firmware, Wi-Fi actif, **4 h minimum** (jusqu'à stabilisation).
4. Thermocouples ou sonde sur : ESP32, ampli, LED, connecteur USB, fusible, boîtier intérieur au plus chaud, **surfaces extérieures touchables** (dessus, grille, molette).
5. Cas de défaut : un haut-parleur en court-circuit, LED bloquées à 100 % (si possible par logiciel), sortie de l'ampli en court-circuit **[À VÉRIFIER : défauts à simuler selon la norme]**.

| Point de mesure | T max mesurée (°C) | Limite applicable | OK ? |
|---|---|---|---|
| Surface extérieure dessus | [PREUVE] | [À VÉRIFIER : limite de toucher pour plastique] | ☐ |
| Grille / molette | [PREUVE] | | ☐ |
| Boîtier intérieur (près ampli) | [PREUVE] | < température de ramollissement du filament – marge (PLA ≈ 55 °C) | ☐ |
| ESP32 | [PREUVE] | Selon fiche technique | ☐ |
| Ampli | [PREUVE] | Selon fiche technique | ☐ |
| Connecteur USB | [PREUVE] | | ☐ |

**[PREUVE]** Photos du montage d'essai, relevés horodatés.

### 6.3 Consommation

| Mode | Puissance mesurée (W) |
|---|---|
| Lecture volume max + LED max | [PREUVE] |
| Repos, LED éteintes, Wi-Fi connecté (veille réseau) | [PREUVE] |
| Repos, Wi-Fi coupé | [PREUVE] |

### 6.4 Autres points de sécurité

- Matériau du boîtier : [À COMPLÉTER : classement au feu du filament si disponible]. En PS1, pas d'exigence d'enveloppe coupe-feu **[À VÉRIFIER]**.
- Aucune arête vive ; petites pièces (touches, molette) **non détachables sans outil** — [PREUVE : essai de traction, ex. 50 N] **[À VÉRIFIER valeur]**.
- Stabilité : ne bascule pas sur un plan incliné de 10° **[À VÉRIFIER]** — [PREUVE].
- Chute d'une table (≈ 75 cm) : pas de pièce dangereuse accessible — [PREUVE].

## 7. Compatibilité électromagnétique (EN 301 489-1 / -17)

**Méthode :** [À CHOISIR : essais complets en laboratoire / pré-tests maison + demi-journée en laboratoire].

### 7.1 Plan d'essais

| Phénomène | Essai | Port | Configuration | Critère d'aptitude |
|---|---|---|---|---|
| Émissions rayonnées | Selon EN 301 489-1 (renvoi EN 55032, classe B) | Enveloppe | Lecture audio volume max + LED + Wi-Fi | Limites classe B |
| Émissions conduites | Idem | Câble USB (via chargeur de référence) | Idem | Limites classe B |
| Décharges électrostatiques | EN 61000-4-2 | Touches, molette, grille, vis, USB | En fonctionnement | Critère B (récupération seule) **[À VÉRIFIER]** |
| Champ rayonné | EN 61000-4-3 | Enveloppe | Lecture | Critère A **[À VÉRIFIER]** |
| Transitoires rapides / ondes de choc | EN 61000-4-4 / -4-5 | Alimentation (si applicable, via chargeur) | | **[À VÉRIFIER applicabilité pour port DC]** |
| Perturbations conduites RF | EN 61000-4-6 | Câble USB | | **[À VÉRIFIER]** |

### 7.2 Résultats

| Essai | Lieu, date, matériel (n° de série, étalonnage) | Résultat | Marge | Conforme ? |
|---|---|---|---|---|
| | [PREUVE] | [PREUVE] | | ☐ |

**Mesures de conception déjà prises :** plan de masse, découplages, ferrites sur USB et fils HP, fils HP courts et torsadés, résistances série sur horloges I2S/SPI, modulation étalée de l'ampli active.

## 8. Cybersécurité (EN 18031-1)

> Structure à confronter au texte de la norme (mécanismes : contrôle d'accès, authentification, mise à jour sécurisée, stockage sécurisé, communication sécurisée, résilience, surveillance réseau, contrôle du trafic, clés cryptographiques confidentielles, capacités générales, cryptographie). **[À VÉRIFIER : restrictions de présomption de conformité dans la citation au JOUE — certains choix imposent un organisme notifié.]**

| Mécanisme | Mise en œuvre AYAH | Preuve |
|---|---|---|
| **Pas de mot de passe par défaut commun** | Configuration initiale : point d'accès temporaire protégé par un **code unique par appareil** imprimé sous l'appareil, ou appairage par l'appli avec confirmation physique (appui molette) | Extrait de code, procédure |
| Authentification des commandes réseau | API locale accessible uniquement après appairage ; jeton unique par appareil ; aucune commande sans authentification | ☐ |
| **Mises à jour sécurisées** | OTA **signées** (vérification de signature avant installation), démarrage sécurisé (Secure Boot v2) et chiffrement de la flash activés en production, retour arrière automatique en cas d'échec | ☐ |
| Stockage sécurisé | Identifiants Wi-Fi et jetons stockés en NVS chiffrée ; aucun secret en clair dans les journaux | ☐ |
| Communication sécurisée | TLS pour tout échange avec un serveur ; vérification du certificat | ☐ |
| Résilience | Limitation des tentatives, redémarrage sûr, chien de garde | ☐ |
| Surface d'attaque minimale | Bluetooth désactivé ; aucun port de débogage accessible ; services réseau limités au strict nécessaire | ☐ |
| Réinitialisation | Remise à zéro usine (appui long) effaçant identifiants et jetons | ☐ |
| Gestion des vulnérabilités | Procédure G §5 | ☐ |
| Données personnelles | [À COMPLÉTER : aucune / liste] — si oui, EN 18031-2 et RGPD | ☐ |

## 9. Substances (RoHS, REACH)

| Composant | Déclaration RoHS reçue (date) | Déclaration REACH / SVHC | Commentaire |
|---|---|---|---|
| (un par ligne de la nomenclature §3.1) | [PREUVE] | [PREUVE] | |

Méthode : approche EN IEC 63000 — collecte des déclarations fournisseurs, évaluation des fournisseurs, archivage. Modèle de demande : H §1.

## 10. Analyse de risques (sécurité générale)

Gravité : 1 mineure · 2 sérieuse · 3 grave. Probabilité : 1 rare · 2 possible · 3 probable.

| # | Danger | Situation | G | P | Mesures | G×P résiduel | Preuve |
|---|---|---|---|---|---|---|---|
| 1 | Échauffement / incendie | Utilisation prolongée, nuit, volume max | 3 | 1 | 5 V limité, fusible, LED limitées, mesures §6.2, consignes notice | faible | §6.2 |
| 2 | Déformation du boîtier | Soleil, voiture, radiateur | 1 | 2 | Consigne notice, filament [PETG recommandé] | faible | Notice |
| 3 | Ingestion de petites pièces | Enfant en bas âge | 3 | 1 | Pièces non détachables sans outil, mention « hors de portée des jeunes enfants » | faible | §6.4 |
| 4 | Choc électrique | — | 1 | 1 | ES1 (5 V), pas de secteur dans l'appareil | négligeable | §6.1 |
| 5 | Chargeur non conforme | Client utilise un chargeur bas de gamme | 2 | 2 | Notice : « chargeur conforme CE 5 V / 3 A » ; fusible d'entrée | faible | Notice |
| 6 | Chute de l'objet | Bord de meuble | 1 | 2 | Patins antidérapants, centre de gravité bas | faible | §6.4 |
| 7 | Volume sonore élevé | Écoute proche | 1 | 1 | Puissance 3 W, volume max limité par logiciel | négligeable | — |
| 8 | Lumière (éblouissement) | Mode nuit | 1 | 1 | LED diffusées, intensité limitée | négligeable | — |
| 9 | Piratage / prise de contrôle | Réseau domestique | 2 | 2 | Mesures §8 | faible | §8 |
| 10 | Arêtes / bavures d'impression | Manipulation | 1 | 2 | Contrôle visuel en fin de fabrication, ébavurage | faible | G §2 |

## 11. Conclusion et signature

La conformité est déclarée lorsque **toutes** les cases ☐ ci-dessus sont cochées avec leur preuve.

Établi par : [À COMPLÉTER], le [À COMPLÉTER] — Version du dossier : [À COMPLÉTER]
