# Historique des versions

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ; numérotation : [SemVer](https://semver.org/lang/fr/) (MAJEUR.MINEUR.CORRECTIF).

## [1.0.1] — 2026-09-19
### Modifié
- Lien vers le code source cliquable dans le pied de page et la page « À propos » (phrases d'un seul paragraphe).
- Schéma d'architecture de la page « À propos » : déploiement sur Render (application) et Hugging Face (page de présentation), 9 pages.
- `README.md` et `DEPLOIEMENT.md` : adresses en ligne (`https://rlga-knapsack.onrender.com`, `https://recherche-niaiko-rlga-knapsack.static.hf.space`) et état du déploiement.
### Corrigé
- Page vitrine : texte « <head> » affiché en haut de page (balise coupée par le script inséré par Hugging Face).
- Action « Déploiement » : diagnostic lisible en cas d'échec de l'envoi de la vitrine.
Aucun changement du code de calcul ni des résultats.

## [1.0.0] — 2026-09-19 — première version publique
Version publiée dans `Recherche-Niaiko/rlga-knapsack` et présentée à la soutenance du 25 septembre 2026. Elle réunit les versions de développement 0.1.0 à 0.3.0 (voir plus bas) et les ajouts suivants.
### Ajouté
- Encadrement des ressources des calculs lourds (`app_taipy/ressources.py`, `app_taipy/worker.py`) : exécution dans un processus séparé, file d'attente globale (un calcul à la fois), limites de mémoire, de temps processeur et de durée, priorité basse, un seul fil numérique, estimation de la durée avant lancement et refus au-delà du budget, bouton « Arrêter le calcul » sur les pages Comparaison, Cas d'usage, Hypothèses et Scénarios.
- Tests unitaires (`tests/test_unitaires.py`), de robustesse (`tests/test_ressources.py`), de performance (`tests/test_performance.py`, rapport dans `results/performance/`) et d'intégration (`tests/test_application.py`) ; exécutés par l'intégration continue.
- Section « Choisir une licence » dans `GUIDE_GIT.md` ; licence **MIT** pour le code (`LICENSE`, en-têtes SPDX) et **CC BY 4.0** pour les documents, figures, résultats et cas d'usage (`LICENSE-docs`).
- `.gitignore` complétés (dépôt public de la réalisation et dépôt privé du mémoire) ; guides personnels (démonstration, parcours) exclus du dépôt public et de l'image Docker.
- Dépôts dans l'organisation GitHub `Recherche-Niaiko` (liens de l'application, de `LICENSE-docs` et du `README.md`) ; `DEPLOIEMENT.md` réécrit en plan de déploiement daté ; déploiement déclenché seulement après la réussite des tests, sur la version testée.
- Hébergement : l'offre gratuite de Hugging Face n'autorisant plus que les Spaces « Static », l'application est déployée sur **Render** (offre gratuite, `render.yaml`, deploy hook) et une **page vitrine statique** (`vitrine/`) est publiée sur Hugging Face ; bornes et réglages initiaux configurables (`RLGA_N_MAX`, `RLGA_N_DEFAUT`…), estimation de la PLNE non multipliée par le facteur machine ; démonstration par tunnel Cloudflare.
### Corrigé
- Blocage de l'ordinateur lorsqu'une comparaison lançait toutes les méthodes sur une grande instance : le calcul occupait le serveur web lui-même, sans limite de durée ni de concurrence.
- Bornes des paramètres appliquées aussi côté serveur (taille, exécutions, générations, limite de la PLNE), y compris pour les scénarios.

## Versions de développement (non publiées)

## [0.3.0] — 2026-09-19
### Ajouté
- Page « Hypothèses » : vérification de H1 à H4 sur un cas d'usage ou sur l'instance courante (exécutions appariées, tests de Wilcoxon unilatéraux, verdicts comparés à ceux du mémoire).
- Surlignage de la meilleure valeur par colonne (ou par ligne pour les tableaux des campagnes) dans tous les tableaux de résultats.
- Page « Scénarios » entièrement en français (exécuter, supprimer, créer, comparer les scénarios exécutés) à la place des composants génériques en anglais.
- Explication, sur la page « Cas d'usage », de la supériorité de la PLNE sur les instances de taille modérée ; toutes les méthodes ex æquo sont désormais citées.
- Guide de parcours de la plateforme (`docs/guide_parcours_plateforme.md`, usage personnel de l'auteur).
### Modifié
- Mise en page : barre de navigation horizontale (menu repliable sur téléphone), contenu centré de largeur limitée, police Montserrat servie localement, textes descriptifs en 19 px / 23 px, indicateurs en cartes, page « Politique apprise » en une seule colonne.
- Nombres au format français dans les tableaux et indicateurs.
- Aucune mention de la bibliothèque d'interface dans la plateforme (menus, textes, schéma d'architecture, filigrane).
- Bibliographies enrichies des documents « Analyse des résultats » (35 références) et « Discussion » (37 références).
### Supprimé
- Téléchargement public du guide de démonstration (page « À propos »).

## [0.2.0] — 2026-09-19
### Ajouté
- Refonte de l'interface Taipy : menu latéral à icônes, thème clair/sombre, page d'accueil pour les visiteurs, parcours guidé en étapes, indicateurs (`metric`), figures commentées, page « À propos ».
- Déploiement : `Dockerfile`, `requirements-app.txt`, métadonnées Hugging Face Spaces, action GitHub de déploiement automatique, test de fumée.
- Jeux de données embarqués dans `data/` (application autonome).
### Modifié
- Nuage des objets : graphique natif Taipy (plus d'erreur « WebGL is not supported »).
- Figures regénérées en français, polices agrandies, sans titre interne (légendes dans le manuscrit et l'application).
- Équipe d'accueil : GLoRe devient GLoRIA.

## [0.1.0] — 2026-09-18
### Ajouté
- Paquet `rlga_kp` (instances, PD, PLNE HiGHS, glouton, AG vectorisé, contrôleurs fixe/aléatoire/UCB1/Q-learning, pré-entraînement).
- Campagnes E0–E5, analyses statistiques et figures ; application Taipy initiale ; cas d'usage.
