# Réalisation — RL-in-GA pour le problème du sac à dos

Implémentation, expérimentations et application de démonstration du mémoire de Master Recherche
« *Intégration de l'apprentissage par renforcement dans l'algorithme génétique pour la résolution du problème de sac à dos complexe* »
(RALAIVAO Niaiko Michaël — ENI, Université de Fianarantsoa — laboratoire LIMAD, équipe GLoRIA).

**Code source** : <https://github.com/Recherche-Niaiko/rlga-knapsack>  
**Application en ligne** (prévue) : <https://rlga-knapsack.onrender.com> — **page de présentation** : <https://recherche-niaiko-rlga-knapsack.hf.space> — voir `DEPLOIEMENT.md`.

## Installation

```bash
cd 03_REALISATION_RL_GA_KP
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

> Sur cette machine, `/etc/timezone` et `/etc/localtime` sont en conflit, ce qui fait échouer l'import de Taipy.
> Les scripts fournis fixent `TZ=Indian/Antananarivo`.

## Contenu

| Élément | Rôle |
|---|---|
| `rlga_kp/` | paquet : instances (KP/MKP, Pisinger, Jooken, OR-Library), PD, PLNE (HiGHS), glouton, AG vectorisé, contrôleurs (fixe, aléatoire, UCB1, Q-learning en ligne / pré-entraîné), entraînement hors ligne |
| `experiments/run_all.py` | campagnes : `train` (Q-tables), `e1` (KP générés), `e2` (benchmarks + Jooken), `e3` (MKP), `e5` (passage à l'échelle) |
| `experiments/analysis.py` | tableaux (CSV/MD/LaTeX), tests (Wilcoxon + Holm, Friedman, A12), figures numérotées |
| `experiments/exp0_pilot.py` | pilote de calibration (instances disjointes des tests) |
| `experiments/schemas.py` | schémas explicatifs (boucle AR–AG, architecture) |
| `app_taipy/ressources.py`, `app_taipy/worker.py` | encadrement des ressources des calculs lourds (processus séparé, file d'attente, limites de mémoire et de durée, estimation préalable) |
| `tests/` | tests unitaires, de robustesse, de performance et d'intégration (voir ci-dessous) |
| `app_taipy/` | application web Taipy (9 pages, thème clair/sombre, adaptée au téléphone ; vérification des hypothèses H1–H4 sur les cas d'usage) + scénarios (`config/config.toml`, éditable dans Taipy Studio) |
| `cas_usage/` | 4 cas d'usage (données synthétiques illustratives) + générateur |
| `results/` | résultats bruts (`runs.csv`, `runs_gap.csv`, `references.csv`, `curves.npz`), Q-tables, `analyse/`, `figures/` |
| `docs/` | analyse des résultats, discussion, perspectives (MD + LaTeX + PDF) |
| `data/` | jeux de données embarqués (voir `data/SOURCES.md`) |
| `Dockerfile`, `requirements-app.txt`, `render.yaml` | image de déploiement et plan Render (offre gratuite) — voir `DEPLOIEMENT.md` |
| `vitrine/` | page de présentation statique (Space Hugging Face « Static », gratuit) |
| `.github/workflows/` | tests, puis déploiement automatique (Render et vitrine Hugging Face) de la version testée |
| `VERSION`, `CHANGELOG.md` | numéro de version et historique — voir `GUIDE_GIT.md` |

## Reproduire les résultats

```bash
./launch.sh train e1 e2 e3 e5          # ≈ 2 h sur 8 cœurs ; journal : results/run_all.stdout
TZ=Indian/Antananarivo .venv/bin/python experiments/analysis.py
```

## Lancer l'application

```bash
./app_taipy/run_app.sh                 # http://127.0.0.1:5000
```

## Encadrement des ressources

Les calculs lancés depuis l'application (comparaison, cas d'usage, hypothèses, scénarios) ne s'exécutent plus dans le serveur web mais dans un **processus séparé**, afin que l'interface reste réactive et que l'ordinateur ne soit jamais saturé :

1. **estimation préalable** : la durée du calcul est estimée ; au-delà de 10 minutes, il est refusé avec un conseil (moins d'exécutions, de générations ou de méthodes) ;
2. **file d'attente globale** : un seul calcul à la fois pour tout le serveur, quel que soit le nombre d'onglets ou de visiteurs ; les méthodes sont exécutées l'une après l'autre et les résultats rassemblés à la fin ;
3. **limites du processus** : mémoire virtuelle (2 Go, minimum 1 Go car NumPy et SciPy en réservent près de 1 Go au chargement ; la mémoire réellement occupée reste de 100 à 250 Mo), temps processeur, priorité basse (`nice`), un seul fil pour les bibliothèques numériques, durée réelle maximale (15 minutes) ;
4. **bouton « Arrêter le calcul »** sur chaque page de calcul.

Les seuils se règlent par variables d'environnement :

| Variable | Défaut | Rôle |
|---|---|---|
| `RLGA_MAX_CALCULS` | 1 | calculs simultanés (tout le serveur) |
| `RLGA_MEMOIRE_MO` | 2048 | mémoire virtuelle maximale d'un calcul (Mo, minimum 1024) |
| `RLGA_DUREE_MAX_S` | 900 | durée réelle maximale d'un calcul (s) |
| `RLGA_ESTIMATION_MAX_S` | 600 | durée estimée au-delà de laquelle un calcul est refusé (s) |
| `RLGA_ATTENTE_MAX_S` | 300 | attente maximale dans la file (s) |
| `RLGA_PRIORITE` | 10 | priorité (`nice`) du processus de calcul |
| `RLGA_FACTEUR_MACHINE` | 1.0 | multiplie les estimations (> 1 sur une machine plus lente ; 20 sur Render) |
| `RLGA_N_MAX`, `RLGA_EXECUTIONS_MAX`, `RLGA_GENERATIONS_MAX` | 5000, 10, 500 | bornes des paramètres et des curseurs |
| `RLGA_N_DEFAUT`, `RLGA_EXECUTIONS_DEFAUT`, `RLGA_GENERATIONS_DEFAUT` | 500, 3, 200 | réglages initiaux de la page « Comparaison » |

## Tests

```bash
export TZ=Indian/Antananarivo OPENBLAS_NUM_THREADS=1
.venv/bin/python -m unittest discover -s tests -v          # tous les tests (≈ 2 min)
.venv/bin/python tests/test_unitaires.py                  # paquet rlga_kp et fonctions de calcul (≈ 5 s)
.venv/bin/python tests/test_ressources.py                 # encadrement des ressources (≈ 20 s)
.venv/bin/python tests/test_performance.py                # durées et mémoire par méthode → results/performance/
.venv/bin/python tests/test_application.py                # démarrage de l'application et temps de réponse
```

| Fichier | Ce qui est vérifié |
|---|---|
| `test_unitaires.py` | PD = force brute, PLNE = PD (KP et MKP), garanties du glouton, réparation, élitisme, reproductibilité, bornes des paramètres, hypothèses H1–H4 |
| `test_ressources.py` | refus du calcul qui avait bloqué l'ordinateur (9 méthodes, 10 × 500 générations, n = 5 000), processus séparé et limité, dépassements de mémoire et de durée, arrêt sur demande, file d'attente, réactivité du serveur pendant un calcul |
| `test_performance.py` | durée réelle et mémoire de chaque méthode pour n = 200, 1 000, 2 000 ; estimation jamais trop optimiste |
| `test_application.py` | démarrage de l'application web et temps de réponse des pages |
| `test_smoke.py` | test de fumée historique |

## Taipy Studio

1. Installer l'extension **Taipy Studio** dans VS Code.
2. Ouvrir `app_taipy/config/config.toml` : le graphe `parametres → construire_instance → instance → resoudre → resultats, convergence` s'affiche et se modifie graphiquement.
3. Pour régénérer le fichier depuis le code : `TZ=Indian/Antananarivo .venv/bin/python app_taipy/config/build_config.py`.

## Licence

- **Code** (paquet `rlga_kp/`, `experiments/`, `app_taipy/`, `tests/`, scripts) : licence **MIT** — voir [`LICENSE`](LICENSE).
- **Documents, figures, résultats et cas d'usage synthétiques** (`docs/`, `results/`, `cas_usage/`) : licence **Creative Commons Attribution 4.0 International (CC BY 4.0)** — voir [`LICENSE-docs`](LICENSE-docs).
- **Exclus** : jeux de données de tiers (`data/`, voir `data/SOURCES.md`), police Montserrat (SIL Open Font License, `app_taipy/assets/fonts/OFL.txt`) et logos des institutions (`app_taipy/assets/logos/`).

Pour citer ce travail : RALAIVAO, N. M. (2026). *Intégration de l'apprentissage par renforcement dans l'algorithme génétique pour la résolution du problème de sac à dos complexe* [Mémoire de Master Recherche, École Nationale d'Informatique, Université de Fianarantsoa].
