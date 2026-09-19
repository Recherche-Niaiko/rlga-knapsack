---
title: "Analyse des résultats expérimentaux — RL-in-GA pour le problème du sac à dos"
author: "RALAIVAO Niaiko Michaël — Master Recherche, ENI / LIMAD / GLoRIA"
date: "Septembre 2026"
lang: fr
bibliography: ../../02_ETAT_DE_L_ART_FINAL/references.bib
---

# Organisation des résultats

Les résultats sont regroupés par campagne ; chaque figure porte un numéro stable (préfixe `figNN_`) et chaque tableau existe en CSV, Markdown et LaTeX dans `results/analyse/<campagne>/`, pour une intégration directe dans le manuscrit.

| Campagne | Question | Tableaux (`results/analyse/…`) | Figures (`results/figures/…`) |
|---|---|---|---|
| E0 — calibration | quels réglages ? | `exp0_pilot/` | `fig00_*`, `fig05_*`, `fig06_*` |
| E1 — KP générés | QR1, QR2, QR3, QR5 | `e1_kp01_generes/` | `fig01_e1_*`, `fig04_politique_actions` |
| E2 — KP de référence | QR1, QR3, QR4 | `e2_kp01_benchmarks/` | `fig02_e2_*` |
| E3 — MKP | QR3 (transfert inter-problèmes), QR4 | `e3_mkp/` | `fig03_e3_*` |
| E5 — passage à l'échelle | QR4 | `e5_scalabilite/scalability.csv` | `fig07_scalabilite` |
| Cas d'usage | utilité pratique | `cas_usage/resultats_cas_usage.csv` | `app_*` (captures) |

**Lecture des indicateurs.** L'*écart* est $100\,(f_{\text{ref}} - f)/f_{\text{ref}}$ en % (0 = optimum). Les écarts sont faibles en valeur absolue (quelques centièmes de %) parce que l'AG, grâce à la réparation gloutonne, est déjà un bon solveur ; ce sont les **différences relatives** entre méthodes et leur **significativité** qui importent. Les comparaisons suivent les recommandations de @demsar_2006 et @derrac_2011 : test de Friedman suivi du test post hoc de Nemenyi pour le classement global, test de Wilcoxon apparié avec correction de Holm pour les comparaisons deux à deux. *V/E/D* = nombre d'instances où la méthode cible gagne / fait jeu égal / perd (Mann–Whitney, α = 0,05) ; $A_{12} > 0{,}5$ signifie que la cible obtient plus souvent un écart plus faible (taille d'effet de @vargha_delaney_2000).

# E0 — Calibration (instances disjointes des tests)

Réalisée sur 6 instances (SC, ASC, UC ; n = 500 ; graines 900+), selon la démarche de réglage des paramètres des algorithmes évolutionnaires décrite par @eiben_1999 :

1. **Tous les contrôleurs adaptatifs** (aléatoire, UCB1, QL en ligne) divisent par ≈ 4 l'écart de l'AG standard sur SC/ASC, mais le **QL en ligne ne dépasse pas la sélection aléatoire** (écart moyen 0,0182 % contre 0,0158 %).
2. Parmi les **9 configurations fixes**, **UX + BF3** est de loin la meilleure (SC : 0,0000 % ; ASC : 0,0073 %) et 1P + BF1 (l'AG standard) la pire (SC : 0,1105 %) — un facteur > 10 : **le choix des opérateurs compte**, et il existe donc une marge pour l'apprentissage, ce qui est la prémisse de la sélection adaptative d'opérateurs [@dacosta_2008; @karimi-mamaghan_machine_2022].
3. Choix de la **récompense** (Q-table entraînée sur UC/WC/SS puis testée) : l'amélioration relative seule (R1) donne la meilleure politique (SC 0,0000 %, ASC 0,0149 %) ; l'ajout du taux de succès des descendants (SC 0,0237 %) ou d'une pénalité de diversité (SC 0,0395 %) la dégrade. → **R1 retenue**. Ce résultat est cohérent avec les récompenses fondées sur l'amélioration de la qualité, les plus fréquentes dans les revues sur l'apprentissage par renforcement au service des algorithmes évolutionnaires [@song_reinforcement_2023; @li_bridging_2025].

# E1 — KP 0/1 générés (54 instances × 7 variantes × 10 exécutions)

Les instances sont générées selon les classes de @pisinger_where_2005 ; les contrôleurs comparés sont l'AG standard [@holland_1975; @goldberg_1989], la sélection aléatoire, le bandit UCB1 [@auer_2002] et le Q-learning [@watkins_dayan_1992; @sutton_barto_2018], en ligne ou pré-entraîné.

**Tableau 1 — Écart moyen à l'optimum (%)** (optimum prouvé par programmation dynamique [@bellman_1957; @kellerer_knapsack_book_2004]) :

| Classe | AG standard | Aléatoire | UCB1 | QL en ligne | **QL pré-entraîné** | QL pré-entr. + φ(I) | Oracle fixe |
|---|---|---|---|---|---|---|---|
| UC | 0,0048 | 0,0028 | 0,0024 | 0,0031 | **0,0019** | 0,0031 | 0,0021 |
| WC | 0,0063 | 0,0039 | 0,0036 | 0,0039 | 0,0037 | 0,0035 | **0,0033** |
| SS | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 |
| ISC | 0,0053 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 |
| SC | 0,1114 | 0,0258 | 0,0275 | 0,0275 | 0,0158 | 0,0258 | **0,0086** |
| ASC | 0,1016 | 0,0341 | 0,0321 | 0,0319 | 0,0232 | 0,0309 | **0,0156** |
| **Moyenne** | 0,0382 | 0,0111 | 0,0109 | 0,0111 | **0,0074** | 0,0105 | 0,0049 |
| Rang moyen (Friedman) | 6,05 | 4,08 | 3,96 | 4,08 | **3,10** | 4,09 | 2,63 |

Test de Friedman : χ² = 130,15, p = 1,2·10⁻²⁵ (N = 54 instances, différence critique de Nemenyi CD = 1,23). Pour comparaison, le **glouton** fondé sur l'ordre des efficacités [@dantzig_1957] laisse un écart moyen de 0,34 % sur SC et ASC, soit **plus de 10 fois** celui des variantes adaptatives de l'AG.

**Tableau 2 — Tests appariés (Wilcoxon sur les 54 écarts moyens par instance, correction de Holm)** :

| Comparaison | Écarts (%) | p (Holm) | $A_{12}$ | V/E/D |
|---|---|---|---|---|
| QL pré-entraîné vs AG standard | 0,0074 vs 0,0382 | < 10⁻⁵ | 0,74 | 28/26/0 |
| QL pré-entraîné vs aléatoire | 0,0074 vs 0,0111 | 0,0005 | 0,59 | 9/45/0 |
| QL pré-entraîné vs UCB1 | 0,0074 vs 0,0109 | 0,003 | 0,58 | 10/44/0 |
| QL pré-entraîné vs QL en ligne | 0,0074 vs 0,0111 | 0,002 | 0,58 | 7/47/0 |
| QL pré-entraîné vs oracle fixe | 0,0074 vs 0,0049 | 0,003 | 0,42 | 0/45/9 |
| QL en ligne vs AG standard | 0,0111 vs 0,0382 | < 10⁻⁵ | 0,71 | 24/30/0 |
| QL en ligne vs aléatoire | 0,0111 vs 0,0111 | 1,00 (n.s.) | 0,51 | 0/53/1 |
| QL en ligne vs UCB1 | 0,0111 vs 0,0109 | 1,00 (n.s.) | 0,51 | 1/51/2 |

**Effet de la taille** (classes SC et ASC) : l'écart de l'AG standard croît de 0,046 % (n = 200) à 0,167 % (n = 1 000) ; celui du QL pré-entraîné passe de 0,005 % à 0,025 %, contre 0,043 % pour le QL en ligne et l'aléatoire à n = 1 000. **L'avantage du pré-entraînement augmente avec la taille** : les instances de 500 et 1 000 objets sont hors de la distribution d'entraînement (≤ 200 objets).

**Vitesse** : le QL pré-entraîné atteint son meilleur résultat plus tôt (génération 48,8 en moyenne, contre 56,9 pour l'AG standard et 50,5 pour l'aléatoire) ; le surcoût de l'agent est négligeable (≈ 4,6 s contre 4,0 s par exécution, à n moyen de 567).

**Méthodes exactes** : la PD résout toutes les instances d'E1 en ≤ 3,4 s ; la PLNE (solveur HiGHS [@huangfu_hall_2018], appelé depuis SciPy [@virtanen_scipy_2020]) trouve l'optimum sur les 54 instances mais **ne prouve pas l'optimalité** dans la limite de 30 s pour 12 instances corrélées (SC, ISC, ASC de 500–1 000 objets), confirmant leur difficulté pour le *Branch-and-Bound* [@pisinger_where_2005; @martello_toth_1990].

**Figures associées** : `fig01_e1_ecart_par_classe` (écarts et IC 95 %), `fig01_e1_rangs_friedman`, `fig01_e1_boites` (distributions), `fig01_e1_convergence` (courbes et diversité), `fig01_e1_succes_echecs`, `fig01_e1_qualite_temps`, `fig04_politique_actions`.

## Ce que montre la politique apprise (QR5)

La figure `fig04_politique_actions` donne la fréquence des 9 actions par tiers de la recherche :

- **QL en ligne et UCB1** : distributions **quasi uniformes** (≈ 11 % par action dans toutes les phases). En 200 générations, ils n'identifient pas de préférence : leur comportement est en pratique celui de la sélection aléatoire — ce qui **explique** l'égalité statistique avec GA-RAND (H2).
- **QL pré-entraîné** : préférence nette pour le **croisement uniforme** — UX + SWAP (40 %) et UX + BF3 (17–30 %) en début de recherche, UX + BF3 (46–54 %) et UX + SWAP (33–39 %) en fin de recherche — soit exactement la famille de l'oracle (UX + BF3), **découverte sans la connaître** — ce qui illustre l'intérêt de la configuration dynamique d'algorithmes apprise hors ligne [@biedenkapp_2020; @benjamins_2024] —, sur des instances faciles, et appliquée aux classes difficiles. En phase intermédiaire, la répartition est presque uniforme : ces états ont été peu visités pendant l'entraînement (valeurs Q quasi nulles), ce qui explique l'écart résiduel avec l'oracle.
- **φ(I)** n'apporte rien ici : avec 81 états au lieu de 27 pour un budget d'entraînement comparable, chaque état est moins visité ; la politique est plus diluée (écart 0,0105 % contre 0,0074 %). C'est la « malédiction de la dimension » des représentations tabulaires, qui motive l'approximation de fonction [@sutton_barto_2018; @mnih_2015].

# E2 — KP 0/1 de référence : `instances_01_KP` et Jooken et al. (31 instances × 6 variantes × 10 exécutions)

Ce jeu réunit des instances de Pisinger et les instances difficiles de @jooken_2022, conçues pour mettre en défaut les méthodes exactes.

**Tableau 3 — Écart moyen à l'optimum (%)** (optimums fournis avec les instances) :

| Classe | AG standard | Aléatoire | UCB1 | QL en ligne | **QL pré-entraîné** | Oracle fixe |
|---|---|---|---|---|---|---|
| UC (n = 100…2 000) | 0,0345 | **0,0184** | 0,0221 | 0,0190 | 0,0222 | 0,0229 |
| WC | 0,1904 | 0,1161 | 0,1571 | 0,1381 | **0,0827** | 0,1144 |
| SC | 0,0232 | 0,0142 | **0,0001** | 0,0008 | **0,0001** | 0,0139 |
| Jooken (n = 400, 1 000) | 0,0012 | 0,0010 | 0,0010 | 0,0009 | **0,0008** | **0,0008** |
| **Moyenne** | 0,0407 | 0,0245 | 0,0294 | 0,0259 | **0,0174** | 0,0248 |
| Rang moyen (Friedman) | 5,00 | 3,19 | 3,71 | 3,11 | **2,81** | 3,18 |

Friedman : χ² = 40,07, p = 1,5·10⁻⁷ (N = 31, CD = 1,35).

- Le **QL pré-entraîné** obtient la **meilleure moyenne** et le **meilleur rang** ; il bat significativement l'AG standard (p Holm = 0,001, 5/26/0). Face aux autres variantes adaptatives, les différences ne sont **pas significatives** sur ces 31 instances (p Holm ≥ 0,21) : avec 5 instances par classe (tailles de 100 à 2 000 objets), la variance entre instances est forte, et les instances de Jooken sont résolues à moins de 0,003 % par toutes les variantes, ce qui laisse peu de place aux différences. Le gain le plus net du pré-entraînement porte sur la classe WC (0,083 % contre 0,116–0,157 % pour les autres variantes adaptatives).
- **L'oracle n'est plus le meilleur** : UX + BF3, choisi sur les instances de calibration générées, se classe au niveau de l'aléatoire sur ce jeu (0,0248 %). Une configuration fixe réglée sur une distribution ne se transfère pas nécessairement ; la **politique apprise**, qui varie les opérateurs selon l'état de la recherche, se transfère mieux (0,0174 %). Ce constat rejoint le théorème « pas de repas gratuit » : aucun réglage fixe n'est meilleur sur toutes les distributions d'instances [@wolpert_macready_1997].
- **QL en ligne ≈ aléatoire** (p = 1,00), confirmant H2 sur un second jeu.

**Le mur des méthodes exactes (instances de Jooken, $C = 10^8$).** Pour les 8 instances de capacité $10^8$, la **programmation dynamique est infaisable** (vecteur de $10^8$ réels ≈ 0,8 Go, table de reconstruction bien au-delà), et la **PLNE (HiGHS) ne termine pas** en 60 s sur 4 d'entre elles. Sur ces 4 instances, **toutes les variantes d'AG, en ≈ 7 s, font mieux que la PLNE en 60 s** :

| Instance (Jooken) | AG standard | QL pré-entraîné | PLNE 60 s | Glouton |
|---|---|---|---|---|
| n = 1 000, g = 10, s = 100 | 0,0007 | **0,0001** | 0,0003 | 0,2464 |
| n = 1 000, g = 10, s = 300 | 0,0021 | **0,0020** | 0,0253 | 0,4662 |
| n = 400, g = 10, s = 100 | 0,0027 | 0,0023 | 0,0092 | 1,0400 |
| n = 400, g = 10, s = 300 | 0,0012 | **0,0011** | 0,0013 | 0,2244 |

(écarts en %, moyenne de 10 exécutions pour les AG). C'est la situation où une métaheuristique garde tout son intérêt face aux méthodes exactes (H4), comme le soulignent les revues récentes sur le sac à dos [@cacchiani_knapsack_2022-1; @wilbaut_knapsack_2022].

**Figures associées** : `fig02_e2_ecart_par_classe`, `fig02_e2_rangs_friedman`, `fig02_e2_boites`, `fig02_e2_convergence`, `fig02_e2_succes_echecs`, `fig02_e2_qualite_temps`.

# Cas d'usage réels (données synthétiques illustratives ; 5 exécutions par variante d'AG)

| Cas | Glouton | PD | PLNE | AG standard | Aléatoire | QL en ligne | QL pré-entraîné |
|---|---|---|---|---|---|---|---|
| Budget communal (KP, n = 120) | 0,073 % | non applicable (coûts décimaux) | **optimal, 0,07 s** | 0,003 % | **0 %** | **0 %** | **0 %** |
| Camion humanitaire (MKP, m = 2, n = 250) | 2,05 % | non applicable | **optimal, 0,3 s** | 0,096 % | 0,070 % | 0,061 % | 0,061 % |
| Machines virtuelles (MKP, m = 3, n = 300) | 25,4 % | non applicable | **optimal, 1,5 s** | **2,29 %** | 4,05 % | 2,84 % | 3,36 % |
| Portefeuille (KP corrélé, n = 400) | 0,173 % | optimal, 0,17 s | optimal, 1,7 s | 0,0045 % | 0,0019 % | 0,0022 % | **0,0014 %** |

Ces cas reprennent des applications classiques du sac à dos : sélection de projets sous contrainte budgétaire, chargement multi-ressources, allocation de ressources informatiques et choix de portefeuille [@kellerer_knapsack_book_2004; @vaezi_mean-var_2020; @wilbaut_knapsack_2022].

- Sur ces tailles modestes, la **PLNE** est la méthode de choix (optimale en moins de 2 s).
- Le **glouton** est très fragile en multidimensionnel (25 % d'écart sur les machines virtuelles), faute d'un ordre unique des efficacités lorsque plusieurs ressources sont contraintes [@kellerer_multidimensional_2004].
- Le QL pré-entraîné est le meilleur des AG sur 3 cas sur 4 ; il **échoue** sur les **machines virtuelles**, où l'AG standard, moins disruptif, fait mieux (voir la discussion).

# E3 — Sac à dos multidimensionnel, OR-Library (58 instances × 6 variantes × 10 exécutions)

Ce jeu, issu de l'OR-Library [@beasley_orlib_1990; @chu_beasley_1998], teste le **transfert inter-problèmes** : la Q-table Q_OOD, apprise sur le KP 0/1, est appliquée **sans modification** au MKP ($m$ = 5 ou 10 contraintes). Référence : optimum SAC-94 (*weing*) ou meilleure valeur connue (PLNE 60 s ou meilleure exécution).

**Tableau 4 — Écart moyen à la référence (%)** :

| Sous-ensemble | AG standard | Aléatoire | UCB1 | QL en ligne | QL pré-entraîné | Oracle fixe | PLNE 60 s | Glouton |
|---|---|---|---|---|---|---|---|---|
| OR5x100 (30) | 0,252 | 0,164 | 0,161 | 0,173 | 0,159 | **0,127** | 0,000 | 3,56 |
| OR10x100 (10) | 0,808 | 0,578 | 0,588 | 0,606 | 0,629 | **0,526** | 0,037 | 7,43 |
| OR5x250 (10) | 0,345 | 0,229 | 0,224 | 0,230 | 0,211 | **0,184** | 0,015 | 4,39 |
| SAC-94 *weing* (8) | 0,041 | **0,025** | 0,036 | 0,043 | 0,062 | **0,025** | 0,000 | 2,11 |
| **Moyenne** | 0,335 | 0,228 | 0,228 | 0,240 | 0,236 | **0,191** | — | — |
| Rang moyen (Friedman) | 5,55 | 3,36 | 3,17 | 3,69 | 3,29 | **1,93** | — | — |

Friedman : χ² = 128,2, p = 5,7·10⁻²⁶ (N = 58, CD = 0,99). Temps moyen par exécution d'AG : ≈ 1,9 s.

- **H1 confirmée sur le MKP** : toutes les variantes adaptatives battent l'AG standard (QL pré-entraîné : p Holm < 10⁻⁵, 28/30/0 ; QL en ligne : 22/36/0).
- **Le transfert inter-problèmes n'apporte pas de gain supplémentaire** : QL pré-entraîné, aléatoire, UCB1 et QL en ligne ne se distinguent pas (p Holm ≥ 0,41 ; seul UCB1 est très légèrement meilleur que le QL en ligne, p = 0,037). La politique apprise sur le KP 0/1 conserve la diversification mais ne capture pas la structure multi-contraintes, que les travaux dédiés au MKP intègrent explicitement dans l'état ou dans les caractéristiques de l'instance [@bushaj_k-means_2024; @rezoug_application_2022; @cacchiani_knapsack_2022]. L'**oracle** (UX + BF3) reste significativement meilleur (0/51/7) : le croisement uniforme est pertinent pour le MKP, mais la politique transférée l'utilise moins systématiquement (en phase intermédiaire notamment).
- **Méthodes exactes** : la PLNE (HiGHS) prouve l'optimalité sur 38 instances et atteint sa limite de 60 s sur 20 (9 OR10x100, 10 OR5x250, 1 OR5x100), avec un écart résiduel de 0,015 à 0,037 %. À ces tailles, **la PLNE en 60 s reste nettement meilleure que l'AG en ≈ 2 s** ; l'AG offre un compromis qualité/temps (0,2 % en 2 s) et le **glouton** est très médiocre en multidimensionnel (2 à 7 %).

**Figures associées** : `fig03_e3_ecart_par_classe`, `fig03_e3_rangs_friedman`, `fig03_e3_succes_echecs`, `fig03_e3_qualite_temps`.

# E5 — Passage à l'échelle (classes UC et SC, n = 100 à 10 000, 3 graines)

**Tableau 5 — Temps moyen (s) et écart à la meilleure valeur trouvée (%)** (budget de l'AG fixe : 200 générations × 100 individus) :

| Classe | n | PD | PLNE | Glouton | AG standard | QL pré-entraîné |
|---|---|---|---|---|---|---|
| SC | 1 000 | 1,2 s · 0 % | 80 s* · 0 % | 0,01 s · 0,134 % | 2,5 s · 0,166 % | 3,0 s · **0,021 %** |
| SC | 2 000 | 5,8 s · 0 % | 120 s* · 0 % | 0,01 s · 0,080 % | 5,5 s · 0,270 % | 5,9 s · **0,036 %** |
| SC | 10 000 | infaisable | 120 s* · 0 % | 0,06 s · **0,017 %** | 15,8 s · 1,170 % | 21,9 s · 0,365 % |
| UC | 1 000 | 1,5 s · 0 % | 0,5 s · 0 % | 0,01 s · 0,011 % | 4,1 s · 0,005 % | 4,5 s · **0,002 %** |
| UC | 10 000 | infaisable | 33 s · 0 % | 0,06 s · **0,0001 %** | 36 s · 6,25 % | 40 s · 1,44 % |

\* limite de temps atteinte sans preuve d'optimalité. « Infaisable » : $n \cdot C > 3 \cdot 10^9$ opérations (garde-fou ; la PD dépasserait plusieurs minutes et plusieurs gigaoctets pour reconstruire la solution).

- La **PD** croît en $O(nC)$, soit $O(n^2)$ ici ($C \propto n$) : 6 s à n = 2 000, hors de portée au-delà de 5 000. Elle est pseudo-polynomiale : le KP 0/1 n'est NP-difficile qu'au sens faible [@garey_johnson_1979; @kellerer_improved_2004].
- La **PLNE** trouve la meilleure valeur à toutes les tailles, mais **ne prouve plus l'optimalité** sur la classe SC dès n = 500 (limite de 80–120 s).
- À budget fixe, **l'AG se dégrade avec la taille** ; le **QL pré-entraîné reste 3 à 8 fois meilleur que l'AG standard** jusqu'à n = 10 000 — soit 50 fois la taille des instances d'entraînement : le transfert en taille fonctionne.
- **Échec à grande échelle** : à n ≥ 5 000, le **glouton** (0,06 s) fait mieux que toutes les variantes d'AG : avec 200 générations et une population initiale aléatoire, l'AG n'a pas le temps de converger sur 10 000 variables, alors que la solution gloutonne est quasi optimale lorsque n est grand ($C$ grand devant chaque poids), propriété liée à la borne de Dantzig [@dantzig_1957; @martello_toth_1990]. Remèdes évidents, non testés faute de temps : **initialisation gloutonne** d'une partie de la population (option `init_greedy_fraction` déjà implémentée) et **budget proportionnel à n**.

**Figures associées** : `fig07_scalabilite`.
