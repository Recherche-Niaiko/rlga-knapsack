---
title: "Perspectives de recherche — RL-in-GA pour le problème du sac à dos et au-delà"
author: "RALAIVAO Niaiko Michaël — Master Recherche, ENI / LIMAD / GLoRIA"
date: "Septembre 2026"
lang: fr
bibliography: ../../02_ETAT_DE_L_ART_FINAL/references.bib
---

Ce document recense ce qui **manque** au travail actuel, les **extensions** immédiates, les **interactions avec d'autres domaines** et les pistes de **généralisation**. Les pistes sont classées par horizon (court : quelques semaines ; moyen : un semestre ; long : une thèse).

# Ce qui manque au travail actuel (limites à lever en priorité)

| Limite | Conséquence | Action proposée | Horizon |
|---|---|---|---|
| Population initiale aléatoire et budget indépendant de n | Au-delà de 5 000 objets, le glouton bat l'AG (E5) | Initialisation gloutonne d'une fraction de la population (option `init_greedy_fraction` déjà codée) ; budget proportionnel à n | court |
| Budget d'évaluation unique (P = 100, G = 200) | Les conclusions peuvent dépendre du budget : avec plus de générations, le QL en ligne aurait plus de temps pour apprendre | Courbes « qualité vs budget » (G ∈ {50, 100, 200, 500, 1 000}) ; comparaison à temps de calcul égal | court |
| Une seule métaheuristique de base et une seule réparation (très efficace) | La réparation gloutonne « lisse » les différences entre opérateurs | Répéter avec pénalisation au lieu de réparation ; faire de la stratégie de réparation une **action** (GAP 1, action $r_t$) | court |
| Signal de récompense qui s'éteint en fin de recherche | Les états « fin de recherche » sont peu ou pas appris (Q ≈ 0) | Récompenses normalisées par rang ou relatives aux améliorations récentes ; attribution de crédit par valeurs extrêmes (EVCA) ou fenêtre glissante [@karimi-mamaghan_machine_2022] | court |
| Espace d'état discret et grossier (27 états) | Généralisation limitée ; seuils calibrés à la main | Q-learning avec approximation de fonction (tuile, MLP) ; **DQN** [@mnih_2015] ou **PPO** [@schulman_2017] sur l'état continu | moyen |
| Descripteur d'instance φ(I) scalaire | Les états « classe difficile » ne sont vus qu'à l'entraînement | Représentation apprise de l'instance et de la population : Deep Sets / **Set Transformer** [@lee_settransformer_2019] sur les objets $(w_i, v_i, p_i)$ (GAP 3) | moyen |
| 10 exécutions par instance, instances de taille ≤ 2 000 (sauf E5) | Puissance statistique limitée sur les petites différences | 30 exécutions ; instances de Pisinger « hard » (déjà téléchargées) et 3 240 instances de Jooken | court |
| Comparaison exacte limitée à la PD et à HiGHS | Pas de comparaison avec *Combo* ou *Expknap* | Intégrer *Combo* (code C de Pisinger) comme référence exacte spécialisée | court |

# Extensions méthodologiques

1. **Contrôle continu des paramètres** : au lieu de 9 actions discrètes, l'agent règle directement $(p_c, p_m, k)$ — politique continue (PPO, SAC) ; comparaison avec la configuration dynamique d'algorithmes [@biedenkapp_2020].
2. **Méta-apprentissage et transfert systématique** : entraîner sur une distribution hétérogène d'instances et mesurer la généralisation hors distribution selon trois axes — taille, corrélation, serrage — comme proposé dans l'hypothèse GAP 1 ; sélection d'instances d'entraînement représentatives [@benjamins_2024].
3. **Portefeuille de politiques (GAP 2)** : une archive MAP-Elites [@mouret_clune_2015] indexée par les caractéristiques d'instance (corrélation × serrage) contenant des politiques spécialisées, sélectionnées à l'exécution.
4. **Boucle fermée AR ↔ AG (type EAM)** : une politique neuronale constructive initialise la population et l'AG affine ; les solutions évoluées ré-entraînent la politique [@gu_eam_2025] — à étendre au KP et à l'évaluation hors distribution.
5. **Hyper-heuristique** : l'agent choisit entre heuristiques complètes (AG, recuit simulé, recherche tabou, recherche locale) plutôt qu'entre opérateurs [@kallestad_general_2023; @dokeroglu_hyper-heuristics_2024].
6. **Cadre théorique** : relier la diversité de population (ou l'entropie des fréquences $p_i$) à la capacité de généralisation (question QT1/QT4 du brainstorming) ; borne sur le biais introduit par l'agent (à la manière de la borne KL d'EAM).

# Autres variantes du sac à dos et autres problèmes

| Cible | Ce qui change | Intérêt |
|---|---|---|
| MKP de grande taille (GK, OR30x500) | rien dans l'architecture | NP-difficile au sens fort : la PLNE atteint vite ses limites |
| Sac à dos avec graphe de conflits (KPCG) [@pferschy_knapsack_2009], avec précédences (PCKP) | réparation respectant les conflits / précédences | lien avec la théorie des graphes et la coloration |
| Sac à dos quadratique, multiple, avec *setups* [@cacchiani_knapsack_2022] | évaluation non linéaire, codage entier | variantes sans algorithme dédié performant |
| KP stochastique, dynamique, *chance-constrained* | l'état inclut l'incertitude ; ré-optimisation | logistique en temps réel |
| KP multi-objectif (valeur vs risque) | NSGA-II [@deb_fast_2002] piloté par AR | aide à la décision multicritère (axe du LIMAD) |
| TSP / CVRP, ordonnancement (FJSP) | codage en permutation, opérateurs OX / 2-opt | valider la **généralité** du cadre (GAP 1, cas TSP) [@chen_slga_2020] |

# Interactions avec d'autres domaines

- **Aide à la décision territoriale et SIG** (LIMAD) : sélection de sites d'équipements, planification de projets communaux géolocalisés — prolongement direct de la communication de mai 2024 (cartographie numérique).
- **Logistique humanitaire** (gestion des risques et catastrophes) : chargement multi-contraintes, affectation de véhicules, avec données réelles d'organismes partenaires.
- **Infonuagique et réseaux** : placement de machines virtuelles, allocation de bande passante — problèmes MKP dynamiques.
- **Finance** : portefeuilles sous contraintes (KP moyenne-VaR [@vaezi_mean-var_2020]).
- **Génie logiciel** (équipe GLoRIA) : sélection de fonctionnalités à livrer sous contrainte de budget (*next release problem*, variante du KP), sélection de tests de régression, allocation de ressources dans les projets agiles.
- **Modèles de langage** : génération ou sélection d'opérateurs par un LLM, avec l'AR pour arbitrer — piste émergente.

# Feuille de route proposée (vers une thèse)

| Phase | Contenu | Valorisation visée |
|---|---|---|
| 1 (3 mois) | Levée des limites courtes : budget, réparation comme action, récompense normalisée, 30 exécutions, instances *hard* | article de conférence (CARI, GECCO *student workshop*) |
| 2 (6 mois) | État continu + DQN/PPO ; représentation Set Transformer ; protocole OOD complet (taille × corrélation × serrage) | article (EvoCOP, LION) |
| 3 (6–12 mois) | Généralisation TSP/FJSP ; portefeuille de politiques ; cas réels avec partenaires | revue (C&OR, EJOR, *Applied Soft Computing*) |
