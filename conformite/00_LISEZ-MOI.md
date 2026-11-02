# AYAH — Dossier de conformité et de commercialisation

**Produit :** AYAH « Radio », référence **AY-R1** — marque INOMA  
**Version du dossier :** 0.1 (brouillon) — 2 novembre 2026

> ⚠️ **Ce dossier est une base de travail, pas une attestation de conformité ni un avis juridique.**
> Il a été préparé avec l'aide d'une IA. **Tu signes la déclaration UE : chaque affirmation doit être vraie, vérifiée et prouvée.**

## Hypothèses de cette version du produit

| Élément | Choix retenu | Si tu changes ce choix |
|---|---|---|
| Radio | **Wi-Fi 2,4 GHz uniquement**, module **ESP32-S3-WROOM-1** certifié, antenne intégrée | Ajouter du Bluetooth → inscription Bluetooth SIG + réévaluation |
| Bluetooth | **Désactivé** dans le firmware, non annoncé | — |
| Contenu audio | **Aucun enregistrement fourni** | Fournir des récitations → licences écrites obligatoires |
| Alimentation | USB-C 5 V, **chargeur non fourni**, courant limité (fusible réarmable ≤ 2 A) | Fournir un chargeur → il doit être conforme et documenté |
| Batterie | **Aucune** | Batterie → règlement batteries + essais supplémentaires |
| Boîtier | Impression 3D (PLA ou PETG), visserie M3 | Changement de matière → refaire l'analyse thermique/incendie |

## Conventions

- **[À COMPLÉTER]** : une information que toi seul connais (adresse, SIRET, numéro de lot…).
- **[À VÉRIFIER]** : un point à confirmer dans un texte officiel, auprès d'un organisme ou d'un laboratoire.
- **[PREUVE]** : un document réel à joindre (mesure, photo, rapport, déclaration fournisseur). **Ne jamais l'inventer.**

## Contenu du dossier

| # | Document | Rôle | Qui le voit |
|---|---|---|---|
| A | [Dossier technique](A_Dossier_technique.md) | Démontre la conformité (RED, RoHS, sécurité, cyber) | Toi + autorités sur demande |
| B | [Déclaration UE de conformité](B_Declaration_UE_conformite.md) | L'engagement signé | Public (notice ou site) |
| C | [Notice d'utilisation](C_Notice_utilisateur.md) | Consignes obligatoires en français | Client |
| D | [Étiquetage et emballage](D_Etiquetage_emballage.md) | Marquages sur l'appareil et la boîte | Client |
| E | [Documents de vente](E_Documents_vente.md) | CGV, mentions légales, confidentialité, rétractation | Client |
| F | [Démarches administratives](F_Demarches_administratives.md) | DEEE, emballages, médiateur, assurance, marque, Bluetooth | Toi |
| G | [Procédures internes](G_Procedures_internes.md) | Lots, réclamations, rappels, failles, mises à jour | Toi |
| H | [Modèles de courriers](H_Modeles_courriers.md) | Demandes aux fournisseurs, labo, assureur | Toi |

## Ordre de travail recommandé

1. **Figer le design** : composants définitifs, firmware, boîtier → remplir A §1 à §3.
2. **Collecter les preuves fournisseurs** (courriers H) : rapports Espressif, déclarations RoHS.
3. **Faire les mesures** : températures (A §6) et perturbations électromagnétiques (A §7).
4. **Cybersécurité** : implémenter et documenter A §8.
5. **Démarches** F : entreprise, éco-organisme DEEE, emballages, médiateur, assurance.
6. **Rédiger** notice (C), étiquettes (D), documents de vente (E).
7. **Relire tout**, puis **signer** la déclaration B.
8. **Archiver** l'ensemble **10 ans** (une copie par version du produit).

## Ce qui reste payant (à prévoir)

- **Les textes des normes** (EN 62368-1, EN 301 489…) sont vendus par l'AFNOR. Une **consultation gratuite** est parfois possible dans certaines bibliothèques et CCI **[À VÉRIFIER]**. Un laboratoire les applique pour toi s'il fait les essais.
- Les cotisations éco-organisme / emballages / médiateur (faibles), l'assurance (recommandée).
