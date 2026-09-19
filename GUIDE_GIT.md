# Guide Git et GitHub — versioning du projet

Les deux dépôts sont hébergés dans l'organisation GitHub **`Recherche-Niaiko`**, séparée des projets personnels du compte `Niaiko22`.

Ce guide décrit **ce que vous devez faire vous-même** pour versionner le projet avec Git, le publier sur GitHub et relier les nouvelles versions au déploiement. Aucun commit n'a été fait à votre place.

## 1. Organisation recommandée : deux dépôts

| Dépôt | Contenu | Visibilité | Pourquoi |
|---|---|---|---|
| **`Recherche-Niaiko/rlga-knapsack`** — `git@github.com:Recherche-Niaiko/rlga-knapsack.git` | le dossier `03_REALISATION_RL_GA_KP/` seul (code, données embarquées, résultats, application, documents d'analyse) | **public** | c'est lui qui est cité dans le mémoire (annexe « Reproductibilité ») et déployé sur Hugging Face |
| **`Recherche-Niaiko/memoire-master-rl-ga`** — `git@github.com:Recherche-Niaiko/memoire-master-rl-ga.git` | les dossiers `00_…` à `05_…` (journal, projet, état de l'art, manuscrit, soutenance) | **privé** | historique de la rédaction ; contient des éléments non destinés au public |

**À ne jamais publier** : `ZOTERO_REFERENCES/zotero_api_key_claude.txt` (clé d'API), les PDF d'articles (droits d'auteur), les environnements virtuels (`.venv/`), `FORMATION_PRATIQUE/`, `OLD_PROJECTS/`, `SIMULATIONS/` (volumineux, plusieurs Go).

## 2. Préparer Git (une seule fois) — fait

Configuration en place (`git config --global -e`) :

```ini
[user]
        name = Niaiko22
        email = ralaivaoniaiko@gmail.com
[init]
        defaultBranch = main
[core]
        editor = nano
```

La clé SSH du compte `Niaiko22` est enregistrée (`ssh -T git@github.com` → « Hi Niaiko22! ») et ce compte est *Owner* de l'organisation `Recherche-Niaiko`. Les commits porteront le nom « Niaiko22 » ; pour signer ceux d'un dépôt de votre nom complet, exécuter dans ce dépôt `git config user.name "RALAIVAO Niaiko Michaël"` (sans `--global`).

## 3. Publier le dépôt de la réalisation

Le dépôt distant `Recherche-Niaiko/rlga-knapsack` (public) existe et est vide ; il reste à créer le dépôt local et à le publier :

```bash
cd 03_REALISATION_RL_GA_KP
git init
git add .
git status                      # vérifier : pas de .venv/, .taipy/, user_data/ (exclus par .gitignore) ; LICENSE et LICENSE-docs présents
git commit -m "Version 1.3.0 : réalisation RL-in-GA, application web, encadrement des ressources et tests"
git tag -a v1.3.0 -m "Version présentée à la soutenance"
```

```bash
git remote add origin git@github.com:Recherche-Niaiko/rlga-knapsack.git
git push -u origin main --tags
```

Si le `push` est refusé parce que le dépôt distant contient déjà un commit (README ou licence créés par GitHub), exécuter `git pull --rebase origin main`, puis relancer le `push`.

Le lien affiché par l'application (`RLGA_GITHUB_URL` dans `app_taipy/main.py`), l'annexe du mémoire, `LICENSE-docs` et la diapositive « Mise en ligne et versions » pointent déjà vers `https://github.com/Recherche-Niaiko/rlga-knapsack`.

La clé SSH est celle du compte `Niaiko22` : en tant que propriétaire de l'organisation, ce compte a le droit de pousser dans ses dépôts.

## 4. Travailler au quotidien

| Situation | Commandes |
|---|---|
| Voir ce qui a changé | `git status` puis `git diff` |
| Enregistrer une modification | `git add <fichiers>` puis `git commit -m "…"` |
| Publier | `git push` (déclenche les tests puis, s'ils réussissent, le déploiement sur Render et la mise à jour de la vitrine) |
| Développer une nouveauté sans risque | `git switch -c fonctionnalite/nom` … puis *Pull Request* vers `main` sur GitHub |
| Revenir sur un fichier | `git restore <fichier>` |
| Consulter l'historique | `git log --oneline --graph` |

**Messages de commit** (convention *Conventional Commits*, en français) :

- `feat: ajout de la page …` — nouvelle fonctionnalité ;
- `fix: correction de l'affichage …` — correction ;
- `docs: mise à jour du guide …` — documentation ;
- `exp: nouvelle campagne E6 …` — expériences / résultats ;
- `refactor:`, `test:`, `chore:` — restructuration, tests, maintenance.

## 5. Publier une nouvelle version

1. Mettre à jour le numéro dans `VERSION` (MAJEUR.MINEUR.CORRECTIF : `1.2.1` pour une correction, `1.3.0` pour un ajout, `2.0.0` pour un changement incompatible).
2. Décrire les changements en tête de `CHANGELOG.md`.
3. Valider et étiqueter :

```bash
git add VERSION CHANGELOG.md <autres fichiers>
git commit -m "chore: version 1.3.0"
git tag -a v1.3.0 -m "Version 1.3.0"
git push && git push --tags
```

4. Sur GitHub : *Releases* → *Draft a new release* → choisir l'étiquette → publier (archive téléchargeable, citable).

L'action `.github/workflows/deploy.yml` met alors à jour l'application sur Render et la vitrine sur Hugging Face (prérequis : secrets `RENDER_DEPLOY_HOOK` et `HF_TOKEN` et variable `HF_SPACE`, voir `DEPLOIEMENT.md`). La version affichée en pied de page de l'application est lue dans `VERSION`.

## 6. Dépôt privé du mémoire (facultatif)

Le fichier `GIT_RECHERCHE/.gitignore` est déjà prêt : il exclut la clé d'API Zotero (`ZOTERO_REFERENCES/`), les dossiers contenant des articles ou des matériaux volumineux (`ETAT_DE_L_ART/`, `NOTES_DE_RECHERCHE_COFFRE_OBSIDIAN/`, `FORMATION_PRATIQUE/`, `OLD_PROJECTS/`, `SIMULATIONS/`, `VIDEOS_UTILES/`, `DATASETS/`), la réalisation (versionnée dans son propre dépôt), les fichiers auxiliaires LaTeX et les PDF horodatés des dossiers `versions/` (≈ 150 Mo ; supprimer la ligne `**/versions/` pour les versionner aussi). N'ajouter ensuite que les livrables :

```bash
git init && git add 00_JOURNAL_DE_BORD 01_PROJET_DE_RECHERCHE 02_ETAT_DE_L_ART_FINAL 04_MANUSCRIT 05_SOUTENANCE \
                    LIVRABLES_LISEZ-MOI.md HISTORIQUE.md TODO.md CLAUDE.md .gitignore
git status                      # vérifier : aucun fichier de ZOTERO_REFERENCES/, aucun PDF d'article
git commit -m "docs: manuscrit, état de l'art et soutenance"
```

Le dépôt distant **`memoire-master-rl-ga`** existe déjà et est vide (vérifier qu'il est **Private**), puis :

```bash
git remote add origin git@github.com:Recherche-Niaiko/memoire-master-rl-ga.git
git push -u origin main
```

Les PDF du manuscrit sont horodatés à chaque compilation (`04_MANUSCRIT/versions/`) : les versions successives restent disponibles même sans Git.

## 7. Choisir une licence avant de rendre le dépôt public

Sans fichier `LICENSE`, un dépôt public reste **protégé par le droit d'auteur** : chacun peut le lire, mais personne n'a légalement le droit de le copier, de le modifier ni de le redistribuer. Le choix d'une licence est donc indispensable pour que le code cité dans le mémoire soit réellement réutilisable. Ce choix vous appartient ; les éléments ci-dessous servent à le préparer.

### 7.1 Ce que contient le dépôt, et ce que la licence couvre

| Contenu | Auteur | Couvert par votre licence ? |
|---|---|---|
| Code (`rlga_kp/`, `experiments/`, `app_taipy/*.py`, `tests/`) | vous | **oui** — licence logicielle |
| Documents, figures, résultats (`docs/`, `results/`), cas d'usage synthétiques (`cas_usage/`) | vous | **oui** — de préférence une licence Creative Commons (adaptée aux textes et aux données) |
| Jeux de données de tiers (`data/` : Pisinger, Jooken et al., OR-Library) | leurs auteurs | **non** — ils restent sous leurs propres conditions ; `data/SOURCES.md` en donne l'origine et la citation attendue |
| Police Montserrat (`app_taipy/assets/fonts/`) | Julieta Ulanovsky et al. | **non** — SIL Open Font License, dont le texte (`OFL.txt`) doit rester à côté des fichiers |
| Logos de l'ENI, de l'Université et du laboratoire (`app_taipy/assets/logos/`) | les institutions | **non** — signes distinctifs, utilisés avec l'accord des institutions ; à mentionner comme exclus de la licence |
| Dépendances (NumPy, SciPy, pandas : BSD ; Plotly, Matplotlib : licences permissives ; Taipy : Apache 2.0) | leurs auteurs | non (installées, pas copiées) — toutes permissives, donc **compatibles avec chacune des licences proposées** |

### 7.2 Licences possibles pour le code

| Licence | Principe | Arguments pour | Arguments contre |
|---|---|---|---|
| **MIT** | permissive : tout usage, y compris commercial, à condition de conserver l'avis de droit d'auteur | la plus répandue en recherche ; texte court et compris de tous ; maximise la réutilisation et donc les citations ; compatible avec tout | aucune protection contre l'appropriation dans un logiciel fermé ; pas de clause sur les brevets |
| **Apache 2.0** | permissive, avec concession explicite des brevets et obligation de signaler les modifications | protège les utilisateurs contre les revendications de brevets ; appréciée des entreprises ; même licence que Taipy | texte long ; fichier `NOTICE` à maintenir si des mentions sont ajoutées |
| **BSD 3 clauses** | comme MIT, plus l'interdiction d'utiliser votre nom ou celui de l'ENI pour promouvoir un produit dérivé | protège la réputation de l'auteur et de l'établissement | légèrement moins connue que MIT |
| **GPL v3** | copyleft : toute version modifiée **distribuée** doit rester libre, sous GPL | garantit que les améliorations restent ouvertes | ne s'applique pas à une application seulement **hébergée** ; freine l'adoption industrielle |
| **AGPL v3** | copyleft étendu au réseau : quiconque met en ligne une version modifiée de l'application doit en publier le code | la seule qui couvre le cas d'une **plateforme web** comme la vôtre | la plus contraignante ; souvent refusée par les entreprises |
| **EUPL 1.2** | copyleft européen, texte officiel **en français** et dans 22 autres langues | valeur juridique dans la langue du mémoire ; compatible avec GPL et AGPL | moins connue hors d'Europe |
| **CeCILL 2.1 / CeCILL-B** | licences de droit français conçues par le CEA, le CNRS et Inria ; CeCILL = copyleft compatible GPL, CeCILL-B = permissive proche de BSD | rédigées en français et en droit civil, adoptées par la recherche publique francophone | peu connues des communautés internationales et des outils de détection de GitHub |

### 7.3 Licences possibles pour les documents, figures et données synthétiques

| Licence | Effet | Usage conseillé |
|---|---|---|
| **CC BY 4.0** | toute réutilisation, y compris commerciale et modifiée, avec citation de l'auteur | figures, documents d'analyse et cas d'usage : maximise la diffusion et les citations |
| **CC BY-SA 4.0** | idem, et les œuvres dérivées doivent rester sous la même licence | si vous souhaitez que les versions modifiées restent ouvertes |
| **CC BY-NC-ND 4.0** | réutilisation sans modification et sans usage commercial | pratique courante pour un **mémoire** ; à vérifier avec le règlement de l'ENI |
| **CC0** | renonciation aux droits (domaine public) | données synthétiques, si vous ne tenez pas à la citation obligatoire |

### 7.4 Recommandation

Pour un dépôt de recherche destiné à être cité et réutilisé, la combinaison la plus simple et la plus répandue est **MIT pour le code** et **CC BY 4.0 pour les documents, les figures et les données synthétiques**. Deux variantes se justifient selon votre priorité :

- **Apache 2.0** au lieu de MIT si vous envisagez des collaborations industrielles (clause de brevets) ;
- **AGPL v3** si vous tenez à ce que toute plateforme dérivée de la vôtre, mise en ligne par un tiers, reste ouverte.

Avant de choisir, vérifiez auprès de l'ENI (directeur du mémoire) qu'aucune règle de propriété intellectuelle de l'établissement ou du laboratoire ne s'impose au code produit dans le cadre du Master.

### 7.5 Appliquer la licence choisie

> **Choix retenu (19 septembre 2026) : MIT pour le code, CC BY 4.0 pour les documents.** Les étapes 1 à 3 sont faites : `LICENSE` (MIT), `LICENSE-docs` (CC BY 4.0, avec la liste des éléments exclus et le texte officiel de la licence), section « Licence » du `README.md`, champ `license: mit` de `vitrine/README.md`, en-têtes SPDX dans les 30 fichiers `.py` et `.sh`. La licence est mentionnée dans l'annexe du mémoire. Il reste à valider par un commit (étape 5).

1. Sur GitHub : *Add file → Create new file*, nommer le fichier `LICENSE` ; GitHub propose alors le texte officiel de la licence choisie (*Choose a license template*). En local, le texte officiel est disponible sur <https://choosealicense.com> ou <https://spdx.org/licenses/>.
2. Ajouter un fichier `LICENSE-docs` (ou une section du `README.md`) pour la licence Creative Commons des documents, et la liste des éléments exclus (données de tiers, police, logos).
3. Déclarer la licence dans le `README.md` (section « Licence ») et dans les métadonnées de la vitrine (`vitrine/README.md` : `license: mit`), et en tête de chaque fichier source avec un identifiant SPDX :

   ```python
   # SPDX-License-Identifier: MIT
   # Copyright (c) 2026 RALAIVAO Niaiko Michaël
   ```

4. Facultatif : un fichier `CITATION.cff` pour que GitHub affiche « Cite this repository ».
5. Valider : `git add LICENSE LICENSE-docs README.md && git commit -m "docs: licence du projet (MIT, CC BY 4.0)"` — ou inclure ces fichiers dans le premier commit (§3).
