# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""Textes de l'application : campagnes, figures (légende + interprétation), classes d'instances, cas d'usage."""

CAMPAGNES = {
    "E1 — KP générés": {
        "id": "e1_kp01_generes",
        "resume": ("54 instances du KP 0/1 générées selon six classes de Pisinger (UC, WC, SS, ISC, SC, ASC), "
                   "de 200 à 1 000 objets ; 7 variantes d'AG × 10 exécutions ; optimum prouvé par programmation dynamique."),
        "message": ("Toutes les variantes adaptatives divisent l'écart de l'AG standard par plus de trois. Le Q-learning "
                    "en ligne ne fait pas mieux que le hasard ; pré-entraîné, il devient la meilleure méthode apprise "
                    "(0,0074 % contre 0,0111 %), derrière la meilleure configuration fixe identifiée a posteriori."),
        "kpis": [("AG standard", 0.0382), ("Opérateurs aléatoires", 0.0111), ("QL en ligne", 0.0111),
                 ("QL pré-entraîné", 0.0074)],
    },
    "E2 — Instances de référence": {
        "id": "e2_kp01_benchmarks",
        "resume": ("31 instances de référence : 15 instances de Pisinger (classes 1 à 3, 100 à 2 000 objets) et "
                   "16 instances difficiles de Jooken et al. (2022), optimums connus."),
        "message": ("Le QL pré-entraîné obtient la meilleure moyenne et le meilleur rang ; la configuration « oracle » "
                    "réglée sur E1 ne se transfère pas. Sur les instances de capacité 10⁸, la programmation dynamique "
                    "est infaisable et tous les AG battent le solveur PLNE limité à 60 s."),
        "kpis": [("AG standard", 0.0407), ("Opérateurs aléatoires", 0.0245), ("QL en ligne", 0.0259),
                 ("QL pré-entraîné", 0.0174)],
    },
    "E3 — Sac à dos multidimensionnel": {
        "id": "e3_mkp",
        "resume": ("58 instances du MKP de l'OR-Library (OR5x100, OR10x100, OR5x250, SAC-94) ; la Q-table apprise "
                   "sur le KP 0/1 est appliquée sans modification."),
        "message": ("Les variantes adaptatives battent nettement l'AG standard, mais le pré-entraînement n'apporte "
                    "aucun gain supplémentaire : le transfert d'un problème à un autre n'est pas établi. Le solveur "
                    "PLNE (60 s) reste meilleur que l'AG (≈ 2 s)."),
        "kpis": [("AG standard", 0.3346), ("Opérateurs aléatoires", 0.2275), ("QL en ligne", 0.2396),
                 ("QL pré-entraîné", 0.2355)],
    },
    "E5 — Passage à l'échelle": {
        "id": "e5_scalabilite",
        "resume": "Classes UC et SC, de 100 à 10 000 objets : temps de calcul et qualité de chaque méthode.",
        "message": ("La programmation dynamique devient hors de portée au-delà de 5 000 objets. Le QL pré-entraîné reste "
                    "3 à 8 fois meilleur que l'AG standard jusqu'à 10 000 objets, mais, à budget fixe, le glouton "
                    "devient meilleur que tous les AG à très grande taille."),
        "kpis": [],
    },
}

FIGURES = {
    "fig01_e1_ecart_par_classe": (
        "E1", "Écart moyen à l'optimum par classe et par méthode (IC à 95 %)",
        "Sur les classes corrélées SC et ASC, l'AG standard (rouge) est nettement le plus éloigné de l'optimum ; "
        "les variantes adaptatives se regroupent, le QL pré-entraîné (bleu) étant le plus proche de l'oracle (violet)."),
    "fig01_e1_rangs_friedman": (
        "E1", "Rangs moyens des méthodes (test de Friedman) et différence critique de Nemenyi",
        "L'oracle et le QL pré-entraîné occupent les deux premiers rangs ; aléatoire, UCB1 et QL en ligne sont "
        "indiscernables ; l'AG standard est dernier."),
    "fig01_e1_boites": (
        "E1", "Distribution des écarts sur 10 exécutions par instance",
        "La dispersion de l'AG standard est la plus forte ; le pré-entraînement réduit à la fois la médiane et la "
        "variabilité des écarts."),
    "fig01_e1_convergence": (
        "E1", "Convergence du meilleur individu (instances de 1 000 objets)",
        "Le QL pré-entraîné descend plus vite dès les premières générations car il n'explore pas au hasard ; sur SC, "
        "il atteint l'optimum vers la 70e génération, comme l'oracle."),
    "fig01_e1_convergence_diversite": (
        "E1", "Diversité génotypique de la population au fil des générations",
        "Toutes les variantes perdent rapidement leur diversité ; celles qui utilisent le croisement uniforme la "
        "conservent un peu plus longtemps, ce qui prolonge l'exploration."),
    "fig01_e1_succes_echecs": (
        "E1", "Succès et échecs par instance (différence d'écart moyen entre deux méthodes)",
        "Le QL pré-entraîné l'emporte sur l'AG standard sur 38 instances sans en perdre aucune ; le QL en ligne gagne 16 "
        "instances et en perd 14 face à la sélection aléatoire ; l'oracle reste devant sur SC et ASC."),
    "fig01_e1_qualite_temps": (
        "E1", "Compromis qualité / temps des méthodes",
        "Sur le KP 0/1 de taille modérée, la programmation dynamique est à la fois exacte et rapide ; le glouton est "
        "instantané mais imprécis ; les AG se situent entre les deux."),
    "fig04_politique_actions": (
        "E1", "Fréquence des 9 couples d'opérateurs par phase de la recherche",
        "Le QL en ligne et UCB1 choisissent presque uniformément (≈ 11 % par action) : ils n'apprennent rien en 200 "
        "générations. Le QL pré-entraîné privilégie le croisement uniforme (UX + BF3, UX + SWAP)."),
    "fig02_e2_ecart_par_classe": (
        "E2", "Écart moyen à l'optimum sur les instances de référence",
        "Le gain du pré-entraînement est le plus net sur la classe WC ; sur les instances de Jooken, toutes les "
        "variantes sont à moins de 0,003 % de l'optimum."),
    "fig02_e2_rangs_friedman": (
        "E2", "Rangs moyens (test de Friedman)",
        "Le QL pré-entraîné obtient le meilleur rang, mais les écarts entre variantes adaptatives restent inférieurs "
        "à la différence critique."),
    "fig02_e2_boites": ("E2", "Distribution des écarts sur les instances de référence",
                        "La variabilité entre instances d'une même classe domine les différences entre méthodes."),
    "fig02_e2_convergence": ("E2", "Convergence sur trois instances de référence",
                             "Les courbes confirment la hiérarchie observée sur E1."),
    "fig02_e2_succes_echecs": ("E2", "Succès et échecs par instance",
                               "Aucune perte du QL pré-entraîné face à l'AG standard."),
    "fig02_e2_qualite_temps": ("E2", "Compromis qualité / temps",
                               "La PLNE reste la plus précise, mais n'aboutit pas sur 4 instances de Jooken."),
    "fig03_e3_ecart_par_classe": (
        "E3", "Écart moyen à la référence sur le sac à dos multidimensionnel",
        "Les variantes adaptatives battent l'AG standard dans chaque sous-ensemble ; le QL pré-entraîné n'est pas "
        "meilleur que l'aléatoire, et l'oracle garde l'avantage."),
    "fig03_e3_rangs_friedman": ("E3", "Rangs moyens sur le MKP",
                                "L'oracle domine ; UCB1, QL pré-entraîné et aléatoire sont statistiquement à égalité."),
    "fig03_e3_boites": ("E3", "Distribution des écarts sur le MKP",
                        "Les écarts sont environ dix fois plus grands que sur le KP 0/1 : le MKP est plus difficile."),
    "fig03_e3_succes_echecs": ("E3", "Succès et échecs par instance sur le MKP",
                               "Face à l'AG standard, aucune perte ; face à l'oracle, uniquement des égalités ou des pertes."),
    "fig03_e3_qualite_temps": ("E3", "Compromis qualité / temps sur le MKP",
                               "Le solveur PLNE (60 s) reste nettement plus précis que l'AG (≈ 2 s) à ces tailles."),
    "fig07_scalabilite": (
        "E5", "Temps de calcul et qualité selon la taille (classes UC et SC)",
        "Le temps de la programmation dynamique croît comme n² ; celui du glouton reste négligeable. À budget fixe, "
        "l'écart des AG augmente avec n, moins vite pour le QL pré-entraîné."),
    "fig05_qtable_Q_OOD": (
        "Apprentissage", "Q-table pré-entraînée (préférences relatives par état)",
        "L'action préférée dépend de l'état : UX + BF3 domine à diversité moyenne, UX + SWAP en fin de recherche "
        "à diversité moyenne. 12 états sur 27 (milieu et fin de recherche, stagnation inférieure à 15 générations) n'ont jamais été visités : l'agent y choisit au hasard."),
    "fig06_entrainement_Q_OOD": (
        "Apprentissage", "Entraînement hors ligne : exploration et part des actions",
        "À mesure que l'exploration diminue, l'agent délaisse la configuration standard 1P + BF1 au profit de "
        "configurations plus exploratoires, en particulier UX + BF3 (jusqu'à 21 % des générations)."),
}

CLASSES_TXT = {
    "UC": "Non corrélée : profits et poids indépendants. Le glouton est presque optimal : instance facile.",
    "WC": "Faiblement corrélée : le profit suit le poids à ±10 %. Difficulté moyenne.",
    "SC": "Fortement corrélée : profit = poids + 100. Tous les objets ont une efficacité voisine : le glouton perd son "
          "pouvoir discriminant. Instance difficile.",
    "ISC": "Inversement fortement corrélée : poids = profit + 100. Difficile pour les méthodes de bornes.",
    "ASC": "Presque fortement corrélée : comme SC, avec une petite perturbation aléatoire. La plus difficile pour l'AG.",
    "SS": "Somme de sous-ensembles : profit = poids. Il s'agit de remplir exactement le sac.",
}
