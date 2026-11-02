# G — Procédures internes

## G1 — Identification et traçabilité des lots

- **Format :** `AY-R1-AAAA-LLL` (année + numéro de lot), numéro de série `0001`, `0002`… dans le lot.
- **Un lot** = même version matérielle + même version firmware + même lot de filament + mêmes fournisseurs.
- **Registre de production** (tableur) — une ligne par appareil :

| N° série | Lot | Date | Version HW | Version FW | Filament (lot) | Fournisseur ESP32 (commande) | Contrôle final OK | Client / commande |
|---|---|---|---|---|---|---|---|---|

- Conserver les factures fournisseurs (preuve d'origine des composants) **10 ans**.

## G2 — Contrôle de fabrication (chaque appareil)

| # | Contrôle | Critère | OK |
|---|---|---|---|
| 1 | Aspect | Pas de bavure, d'arête vive, de fissure | ☐ |
| 2 | Fixations | Toutes les vis serrées, touches et molette non détachables à la main | ☐ |
| 3 | Antenne | Rien de métallique ajouté près du module (conforme au dossier A §5) | ☐ |
| 4 | Mise sous tension | Démarrage, éclairage, son sur les 2 haut-parleurs | ☐ |
| 5 | Commandes | 3 touches + molette (rotation et appui) | ☐ |
| 6 | Firmware | Version attendue, démarrage sécurisé activé, code d'appairage unique programmé | ☐ |
| 7 | Échauffement rapide | 15 min volume fort : pas d'odeur, pas de chaleur anormale | ☐ |
| 8 | Étiquette | CE, DEEE, modèle, lot, série, adresse, code d'appairage | ☐ |
| 9 | Emballage | Notice, mentions, Triman / Info-tri | ☐ |

## G3 — Réclamations clients

1. Enregistrer chaque réclamation : date, n° de série, description, photos.
2. Classer : **sécurité** (chaleur, odeur, fumée, blessure) / fonctionnement / aspect.
3. **Toute réclamation de sécurité** → analyse sous 48 h, vérification des autres appareils du même lot.
4. Réponse au client, réparation / remplacement / remboursement selon garanties.
5. Revue mensuelle : les mêmes problèmes reviennent-ils ? → action corrective + mise à jour du dossier.

## G4 — Produit dangereux : alerte et rappel (GPSR)

Si un risque pour la sécurité est identifié :

1. **Arrêter immédiatement** la vente du lot concerné.
2. **Signaler** sans délai aux autorités via le **Safety Business Gateway** de la Commission européenne (obligation du fabricant en cas de produit dangereux) **[À VÉRIFIER : modalités]** ; en France, autorités compétentes : DGCCRF (et ANFR pour la conformité radio/CEM).
3. **Informer les clients** du lot (e-mail, site) avec une consigne claire (débrancher, ne plus utiliser).
4. Proposer un remède (réparation, remplacement ou remboursement).
5. Documenter toutes les actions dans le dossier.
6. Publier l'avis de rappel si requis (site officiel Rappel Conso en France) **[À VÉRIFIER]**.

## G5 — Vulnérabilités et mises à jour (cybersécurité)

- **Contact sécurité public :** `securite@[domaine]` (ou formulaire) indiqué sur le site.
- **Traitement :** accusé de réception sous 5 jours ouvrés ; évaluation ; correctif ; mise à jour OTA signée ; information des clients.
- **Vulnérabilité activement exploitée** : obligations de signalement au titre du Cyber Resilience Act **[À VÉRIFIER : délais et plateforme]**.
- **Durée de support** annoncée (notice + CGV) : mises à jour de sécurité jusqu'au [À COMPLÉTER].
- **Clés de signature du firmware** : stockées hors ligne, sauvegardées, jamais dans le dépôt Git.
- Journal des versions publiées : version, date, empreinte, contenu, failles corrigées.

## G6 — Gestion des modifications

Toute modification (composant, fournisseur, firmware, boîtier, filament) :

1. Évaluer l'impact sur la conformité (radio, CEM, thermique, cyber, RoHS).
2. Refaire les essais concernés si nécessaire.
3. Nouvelle version du dossier technique (+ nouvelle déclaration si le produit change de façon substantielle).
4. Nouveau lot.
