# Plan de déploiement de l'application

Ce plan décrit, dans l'ordre, ce qu'il reste à faire pour publier le code et mettre l'application en ligne avant la soutenance du **vendredi 25 septembre 2026**. Toutes les actions sont à réaliser par l'auteur ; aucun commit ni aucun déploiement n'a été fait à sa place.

**État au 19 septembre 2026 (soir)** : phases 4 à 8 terminées — code publié (`v1.0.0`, *Release*, protections) ; application Render en ligne sur <https://rlga-knapsack.onrender.com> ; vitrine publiée sur <https://recherche-niaiko-rlga-knapsack.static.hf.space> ; déploiement automatique opérationnel (tests → Render + vitrine). **Prochaines actions : phase 9 (vérifications), phase 11 (dépôt privé du mémoire), phase 12 (répétition avec le tunnel).**

## 1. Contrainte : offre gratuite « Static » de Hugging Face

Depuis 2026, la création d'un Space **Docker** (ou Gradio) sur Hugging Face exige un abonnement payant (PRO pour un compte personnel, Team ou Enterprise pour une organisation) ; l'offre gratuite ne permet que des Spaces **Static**, c'est-à-dire des pages HTML servies telles quelles, sans serveur Python ([documentation des Spaces](https://huggingface.co/docs/hub/en/spaces-overview) ; [annonce sur le forum](https://discuss.huggingface.co/t/docker-sdk-now-marked-as-paid-when-creating-a-new-space/177580)).

Or l'application est un serveur Python (interface web, calculs de programmation dynamique, de PLNE et d'algorithmes génétiques) : **elle ne peut pas s'exécuter dans un Space Static**. Le déploiement retenu sépare donc deux rôles :

| Rôle | Hébergement gratuit | Contenu |
|---|---|---|
| **Application interactive** | **Render**, offre *Free* (Docker, 512 Mo, 0,1 processeur, sans carte bancaire) | l'image Docker actuelle, sans modification |
| **Page vitrine** | **Hugging Face**, Space *Static* (gratuit) | page de présentation (`vitrine/`) : résumé, résultats, figures, liens vers l'application et le code |
| **Démonstration devant le jury** | poste de l'auteur + **tunnel Cloudflare** gratuit | l'application complète, avec toute la puissance de l'ordinateur, accessible par une adresse publique temporaire |

### Pourquoi Render

| Hébergeur gratuit | Ressources | Carte bancaire | Mise en veille | Verdict |
|---|---|---|---|---|
| **Render Free** | 512 Mo, 0,1 processeur, 750 h/mois | non | après 15 min sans trafic, réveil ≈ 1 min | **retenu** : Docker et WebSockets pris en charge, déploiement depuis GitHub |
| Koyeb Free | 512 Mo, 0,1 processeur, une instance | selon les conditions du moment | après 1 h sans trafic | équivalent ; solution de repli |
| Google Cloud Run | jusqu'à plusieurs Go, quota gratuit mensuel | **oui** (compte de facturation obligatoire) | à la demande | puissant, mais exige une carte |
| Hugging Face Docker (PRO, 9 $/mois) | 2 processeurs, 16 Go | oui | après ≈ 48 h | payant ; le plus confortable si un mois d'abonnement est envisageable |

**Mémoire mesurée** : pendant une comparaison par défaut, le serveur occupe au plus ≈ 200 Mo et le processus de calcul ≈ 100 Mo, soit ≈ 305 Mo ; un calcul sur 2 000 objets monte à ≈ 235 Mo pour le seul processus de calcul. Les 512 Mo de Render suffisent donc si la taille des calculs est bornée : le fichier `render.yaml` fixe **2 000 objets au plus, 5 exécutions, 300 générations**, des réglages initiaux plus légers (200 objets, 2 exécutions, 100 générations) et multiplie les durées estimées par 20 pour tenir compte des 0,1 processeur ; un calcul estimé à plus de 5 minutes est refusé avec un conseil.

**Essai réalisé** (image Docker limitée localement à 512 Mo et 0,1 processeur, réglages de `render.yaml`) : démarrage en ≈ 50 s ; comparaison par défaut terminée en **90 s**, pic de mémoire **198 Mo**, aucun arrêt pour manque de mémoire. Durées estimées dans ces conditions : cas d'usage 1 min 30 à 3 min ; vérification des hypothèses 5 à 13 min, donc **refusée sur Render** avec les réglages par défaut (la réduire à 50 générations, ou la présenter en local, phase 12).

Sources : [Render — offre gratuite](https://render.com/docs/free), [Render — deploy hooks](https://render.com/docs/deploy-hooks) et [déploiement d'un commit précis](https://render.com/docs/deploying-a-commit), [Koyeb — instances](https://www.koyeb.com/docs/reference/instances), [Cloud Run — tarifs](https://cloud.google.com/run/pricing).

## 2. Architecture retenue

```
 poste de l'auteur ──git push──▶ GitHub : Recherche-Niaiko/rlga-knapsack (public, licence MIT)
                                   │
                                   ├─ Action « Tests rapides » : 36 tests à chaque push
                                   │        │ succès sur main
                                   │        ▼
                                   └─ Action « Déploiement »
                                        ├─ deploy hook ──▶ Render : image Docker de la version testée
                                        │                  https://rlga-knapsack.onrender.com   (application)
                                        └─ envoi de vitrine/ ──▶ Hugging Face Space Static
                                                           https://recherche-niaiko-rlga-knapsack.static.hf.space   (vitrine)

 jour de la soutenance : ./app_taipy/run_app.sh + cloudflared ──▶ https://<aléatoire>.trycloudflare.com

 poste de l'auteur ──git push──▶ GitHub : Recherche-Niaiko/memoire-master-rl-ga (privé)
```

| Élément | Valeur |
|---|---|
| Organisation GitHub | `Recherche-Niaiko` (propriétaire : compte `Niaiko22`, `ralaivaoniaiko@gmail.com`) |
| Dépôt du code (public) | `git@github.com:Recherche-Niaiko/rlga-knapsack.git` |
| Dépôt du mémoire (privé) | `git@github.com:Recherche-Niaiko/memoire-master-rl-ga.git` |
| Application (Render) | service `rlga-knapsack` → `https://rlga-knapsack.onrender.com` (en ligne depuis le 19/09/2026) |
| Vitrine (Hugging Face) | Space Static `Recherche-Niaiko/rlga-knapsack` → `https://recherche-niaiko-rlga-knapsack.static.hf.space` |
| Version déployée | `1.0.0`, première version publique (fichier `VERSION`, affichée en pied de page de l'application) |

## 3. Calendrier proposé

| Date | Phases | Durée estimée |
|---|---|---|
| dimanche 20 septembre | ~~4 (préparation)~~ fait ; 5 (premier commit et publication du code) | 30 min |
| lundi 21 septembre | 6 (Render), 7 (vitrine Hugging Face), 8 (déploiement automatique), 9 (vérifications) | 1 h 30 |
| mardi 22 septembre | 10 (report des adresses : je mets à jour README, mémoire, diapositives et vitrine), 11 (dépôt privé du mémoire) | 30 min |
| mercredi 23 septembre | 12 (répétition avec le tunnel Cloudflare) ; démonstration en ligne sur Render | 1 h |
| jeudi 24 septembre (soir) | réveil de l'application Render ; vérification rapide (phase 9) | 10 min |
| vendredi 25 septembre | ouverture de l'application Render 15 min avant ; tunnel Cloudflare lancé depuis l'ordinateur de démonstration | 10 min |

## 4. Préparation (une seule fois) — faite

- [x] **Clé SSH du compte `Niaiko22`** (`ralaivaoniaiko@gmail.com`) enregistrée sur GitHub : `ssh -T git@github.com` répond « Hi Niaiko22! ».
- [x] **Organisation GitHub `Recherche-Niaiko`** créée, compte `Niaiko22` *Owner*.
- [x] **Configuration globale de Git** : `user.name = Niaiko22`, `user.email = ralaivaoniaiko@gmail.com`, `init.defaultBranch = main`, éditeur `nano`. Les commits apparaîtront sous le nom « Niaiko22 » et seront rattachés au compte par l'adresse électronique. Facultatif, pour signer les commits de ce seul dépôt de votre nom complet : `git config user.name "RALAIVAO Niaiko Michaël"` (sans `--global`), après le `git init` de la phase 5.
- [ ] Vérifier dans l'organisation que les actions sont autorisées (*Settings → Actions → General → Allow all actions*), avant le premier `git push`.

**Contrôle local avant publication** (depuis `03_REALISATION_RL_GA_KP/`, recommandé) :

   ```bash
   export TZ=Indian/Antananarivo OPENBLAS_NUM_THREADS=1
   .venv/bin/python -m unittest discover -s tests        # 36 tests : OK attendu
   docker build -t rlga-knapsack .
   # simulation de Render (512 Mo, 0,1 processeur, variables de render.yaml) → http://localhost:7860
   docker run --rm -p 7860:7860 --memory=512m --cpus=0.1 -e RLGA_N_MAX=2000 -e RLGA_EXECUTIONS_MAX=5 \
          -e RLGA_GENERATIONS_MAX=300 -e RLGA_MEMOIRE_MO=1024 -e RLGA_FACTEUR_MACHINE=20 \
          -e RLGA_ESTIMATION_MAX_S=300 -e RLGA_DUREE_MAX_S=600 -e RLGA_N_DEFAUT=200 \
          -e RLGA_EXECUTIONS_DEFAUT=2 -e RLGA_GENERATIONS_DEFAUT=100 rlga-knapsack
   ```

## 5. Dépôt public du code

1. ~~Créer le dépôt `rlga-knapsack` dans l'organisation~~ — **fait** : le dépôt public existe et est vide. Vérifier seulement qu'il ne contient ni README, ni `.gitignore`, ni licence créés par GitHub (sinon, le premier `git push` serait refusé ; voir la remarque ci-dessous). Facultatif : ajouter la description « Apprentissage par renforcement dans l'algorithme génétique pour le problème du sac à dos — Master Recherche, ENI » (*About → ⚙*).
2. **Premier commit et publication — fait** (commandes pour mémoire) :

   ```bash
   cd 03_REALISATION_RL_GA_KP
   git init
   git add .
   git status              # ni .venv/, ni .taipy/, ni user_data/, ni guides personnels
   git commit -m "Version 1.0.0 : réalisation RL-in-GA, application web, encadrement des ressources et tests"
   git tag -a v1.0.0 -m "Version présentée à la soutenance"
   git remote add origin git@github.com:Recherche-Niaiko/rlga-knapsack.git
   git push -u origin main --tags
   ```

   **2 bis. Mise en cohérence de la numérotation 1.0.0 — fait** : le premier commit contenait encore `VERSION = 1.3.0`. Après la mise à jour des fichiers (19/09 au soir), valider ces changements et replacer l'étiquette `v1.0.0` sur le nouveau commit (aucune *Release* n'ayant encore été publiée, déplacer l'étiquette est sans conséquence) :

   ```bash
   cd 03_REALISATION_RL_GA_KP
   git status                                   # VERSION, CHANGELOG.md, GUIDE_GIT.md, DEPLOIEMENT.md modifiés
   git add -A
   git commit -m "chore: numérotation de la première version publique (1.0.0)"
   git tag -d v1.0.0                            # supprime l'étiquette locale
   git push origin :refs/tags/v1.0.0            # supprime l'étiquette distante
   git tag -a v1.0.0 -m "Version présentée à la soutenance"
   git push && git push --tags
   ```

   *Remarque* : si GitHub refuse le `push` parce que le dépôt distant contient déjà un commit (README créé à la création), exécuter `git pull --rebase origin main` puis relancer `git push -u origin main --tags`.

3. **Vérifications** : la licence « MIT » apparaît dans la colonne de droite ; l'onglet *Actions* montre « Tests rapides » en vert (≈ 4 minutes). L'action « Déploiement » se déclenche ensuite et ignore ses étapes tant que les secrets de la phase 8 ne sont pas enregistrés : c'est normal.
4. *Releases → Draft a new release* → étiquette `v1.0.0` → titre « Version 1.0.0 — soutenance » → reprendre la section 1.0.0 de `CHANGELOG.md` → *Publish*.
5. Conseillé : *Settings → Branches → Add rule* sur `main`, « Require status checks to pass » (« Tests rapides »).

## 6. Application interactive sur Render

1. Créer un compte sur <https://render.com> **avec le compte GitHub `Niaiko22`** (*Sign in with GitHub*), sans carte bancaire. Autoriser l'application Render sur l'organisation **Recherche-Niaiko** (dépôt `rlga-knapsack` seulement).
2. *New → Blueprint* → dépôt `Recherche-Niaiko/rlga-knapsack` : Render lit `render.yaml` (service web `rlga-knapsack`, Docker, offre *Free*, région Francfort, variables de limitation) → *Apply*. Le premier déploiement démarre (construction de l'image : 5 à 10 minutes).
   *Sans Blueprint* : *New → Web Service* → même dépôt → *Language : Docker*, *Instance type : Free*, puis recopier les variables de `render.yaml` dans *Environment*.
3. Dans le service : *Settings → Build & Deploy* → **Auto-Deploy : Off** (le déploiement est commandé par GitHub après les tests), puis copier l'URL du **Deploy Hook** (elle est secrète).
4. Noter l'adresse publique affichée en haut de la page du service (par exemple `https://rlga-knapsack.onrender.com`).

## 7. Page vitrine sur Hugging Face (offre gratuite)

1. Sur <https://huggingface.co> : créer l'organisation **`Recherche-Niaiko`** (*New → Organization*), puis *New → Space* : propriétaire `Recherche-Niaiko`, nom **`rlga-knapsack`**, licence **MIT**, **SDK : Static** (modèle *Blank*), visibilité **Public**.
2. *Profil → Settings → Access Tokens → Create new token* : type **Write** (ou *Fine-grained* avec écriture sur l'organisation). Copier le jeton.
3. Si l'adresse Render diffère de `https://rlga-knapsack.onrender.com`, me la communiquer : je mets à jour `vitrine/index.html` et `vitrine/README.md` (ou remplacer l'adresse dans ces deux fichiers).

La vitrine (`vitrine/`) présente le travail, les principaux résultats (y compris les résultats négatifs), une figure commentée et une capture de l'application, avec deux boutons : « Ouvrir l'application interactive » (Render) et « Code source ». Elle reste en ligne en permanence, même quand l'application Render est en veille.

## 8. Déploiement automatique depuis GitHub

1. Dans le dépôt GitHub : *Settings → Secrets and variables → Actions* :
   - onglet *Secrets* : **`RENDER_DEPLOY_HOOK`** = l'URL du deploy hook (phase 6) ; **`HF_TOKEN`** = le jeton Hugging Face (phase 7) ;
   - onglet *Variables* : **`HF_SPACE`** = `Recherche-Niaiko/rlga-knapsack`.
2. Premier déploiement complet : *Actions → Déploiement → Run workflow* (branche `main`).

Ensuite, chaque `git push` sur `main` exécute les 36 tests et, **seulement s'ils réussissent**, redéploie sur Render **exactement la version testée** et met à jour la vitrine. Une étape dont le secret manque est ignorée sans échec.

## 9. Vérifications après déploiement

Sur l'application Render (attendre ≈ 1 min au premier accès si elle était en veille) :

- [ ] la page d'accueil s'affiche et le pied de page indique la version **1.0.0** ;
- [ ] page « Instance » : le curseur du nombre d'objets s'arrête à **2 000** ;
- [ ] page « Comparaison », réglages par défaut (200 objets, 2 exécutions, 100 générations) : la comparaison aboutit en ≈ 1 min 30 ;
- [ ] toutes les méthodes, 5 exécutions, 300 générations, 2 000 objets : le calcul est **refusé** avec un conseil ;
- [ ] un calcul lancé puis « Arrêter le calcul » : message « Calcul arrêté à votre demande » ;
- [ ] page « Cas d'usage » (camion humanitaire) : résultats en 2 à 3 minutes ;
- [ ] page « Hypothèses » : avec 200 générations, le calcul est refusé avec un conseil ; avec 50 générations sur le budget communal, il aboutit ;
- [ ] « À propos » : le lien vers le code ouvre `https://github.com/Recherche-Niaiko/rlga-knapsack` ;
- [ ] *Render → Metrics* : mémoire toujours sous 512 Mo pendant ces essais.

Sur la vitrine (<https://recherche-niaiko-rlga-knapsack.static.hf.space>) : la page s'affiche (téléphone, thème sombre), sans texte parasite en haut de page, et les deux boutons ouvrent l'application et le dépôt.

*Remarque* : Hugging Face insère un script juste après `<head>` à une position comptée en octets ; aucun caractère accentué ne doit donc précéder `<head>` dans `vitrine/index.html`, sinon la balise est coupée et « <head> » s'affiche en haut de la page.

## 10. Report des adresses dans les documents

Me transmettre les deux adresses définitives : je les reporte dans le `README.md`, l'annexe E et le chapitre 6 du mémoire, la diapositive « Mise en ligne et versions » et la vitrine, puis je recompile le mémoire, l'état de l'art et les diapositives. Ces changements forment une version **1.0.1** (correctif de documentation), publiée comme au §5 de `GUIDE_GIT.md`.

## 11. Dépôt privé du mémoire

Le dépôt **`memoire-master-rl-ga`** existe déjà dans l'organisation et est vide ; vérifier qu'il est bien **Private** (*Settings → General → Danger Zone → Change visibility*). Puis, depuis `GIT_RECHERCHE/` (le `.gitignore` est prêt, voir `GUIDE_GIT.md` §6) :

```bash
git init
git add 00_JOURNAL_DE_BORD 01_PROJET_DE_RECHERCHE 02_ETAT_DE_L_ART_FINAL 04_MANUSCRIT 05_SOUTENANCE \
        LIVRABLES_LISEZ-MOI.md HISTORIQUE.md TODO.md CLAUDE.md .gitignore
git status        # aucun fichier de ZOTERO_REFERENCES/, aucun PDF d'article, pas de 03_REALISATION_RL_GA_KP/
git commit -m "docs: manuscrit, état de l'art et soutenance"
git remote add origin git@github.com:Recherche-Niaiko/memoire-master-rl-ga.git
git push -u origin main
```

## 12. Démonstration devant le jury : application locale et tunnel Cloudflare

Avec 0,1 processeur, l'application Render convient à la consultation mais reste lente pour les calculs. Pour la démonstration, l'application tourne sur l'ordinateur de l'auteur (toute sa puissance, limites par défaut : 5 000 objets, 10 exécutions) et un **tunnel Cloudflare** gratuit, sans compte ni carte, lui donne une adresse publique temporaire que le jury peut ouvrir sur ses propres appareils :

```bash
# une seule fois : installer cloudflared (https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
cd 03_REALISATION_RL_GA_KP
./app_taipy/run_app.sh                               # terminal 1 : application sur http://127.0.0.1:5000
cloudflared tunnel --url http://localhost:5000       # terminal 2 : affiche https://<mots-aléatoires>.trycloudflare.com
```

L'adresse change à chaque lancement : la communiquer au jury le jour même (par exemple sous forme de QR code sur une diapositive). Sans réseau, la démonstration se fait directement sur `http://127.0.0.1:5000`.

## 13. Exploitation

| Situation | Action |
|---|---|
| Nouvelle version | `VERSION` + `CHANGELOG.md`, commit, étiquette, `git push && git push --tags` (`GUIDE_GIT.md` §5) : tests puis déploiements automatiques |
| Retour à une version antérieure | *Actions → Déploiement → Run workflow* en choisissant l'étiquette voulue (par exemple `v1.0.0`) ; ou, sur Render, *Events → Rollback* vers un déploiement précédent |
| Déploiement en échec | onglet *Actions* du dépôt, onglet *Logs* du service Render ; jeton Hugging Face expiré : en recréer un et mettre à jour `HF_TOKEN` |
| Application en veille (15 min sans trafic) | ouvrir l'adresse et attendre ≈ 1 min ; le faire avant toute présentation |
| Heures gratuites épuisées (750 h/mois) | le service est suspendu jusqu'au mois suivant : un seul service gratuit par compte évite ce cas |
| Panne ou réseau indisponible le jour J | application locale (`./app_taipy/run_app.sh`) ou image Docker (`docker run --rm -p 7860:7860 rlga-knapsack`), vérifiée la veille |
| Besoin de plus de puissance en ligne | abonnement Hugging Face PRO (9 $/mois) et Space Docker, ou Google Cloud Run avec un compte de facturation : l'image Docker est compatible sans modification |

## Annexe — Variables d'environnement

| Variable | Rôle | Défaut | Sur Render (`render.yaml`) |
|---|---|---|---|
| `PORT`, `HOST` | port et interface d'écoute | `7860`, `0.0.0.0` dans l'image | `PORT` fourni par Render |
| `DARK_MODE` | thème initial sombre (`1`) | `0` | — |
| `RLGA_GITHUB_URL` | lien affiché vers le code source | `https://github.com/Recherche-Niaiko/rlga-knapsack` | — |
| `RLGA_DATA_DIR` | dossier des jeux de données | `data/` | — |
| `RLGA_N_MAX`, `RLGA_EXECUTIONS_MAX`, `RLGA_GENERATIONS_MAX` | bornes des paramètres (et des curseurs de l'interface) | `5000`, `10`, `500` | `2000`, `5`, `300` |
| `RLGA_MEMOIRE_MO` | mémoire virtuelle d'un calcul (Mo, minimum 1 024) | `2048` | `1024` |
| `RLGA_FACTEUR_MACHINE` | multiplie les durées estimées | `1.0` | `10` |
| `RLGA_ESTIMATION_MAX_S`, `RLGA_DUREE_MAX_S` | durée estimée maximale acceptée, durée réelle maximale (s) | `600`, `900` | `300`, `600` |
| `RLGA_MAX_CALCULS`, `RLGA_ATTENTE_MAX_S`, `RLGA_PRIORITE` | calculs simultanés, attente dans la file, priorité | `1`, `300`, `10` | défauts |
