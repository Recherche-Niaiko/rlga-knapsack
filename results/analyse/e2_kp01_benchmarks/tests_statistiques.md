**Tests statistiques — e2_kp01_benchmarks**

| comparaison                                             | méthode       |   écart moyen cible (%) |   écart moyen autre (%) |   p (Wilcoxon) |   A12 moyen | V/E/D   |   n instances |   p Holm | significatif (α=0,05)   |
|:--------------------------------------------------------|:--------------|------------------------:|------------------------:|---------------:|------------:|:--------|--------------:|---------:|:------------------------|
| AG + QL pré-entraîné vs AG standard                     | GA            |                 0.01736 |                 0.04065 |      0.0002832 |      0.6244 | 5/26/0  |            31 | 0.001416 | oui                     |
| AG + QL pré-entraîné vs AG op. aléatoires               | GA-RAND       |                 0.01736 |                 0.02448 |      0.1337    |      0.511  | 0/30/1  |            31 | 0.4011   | non                     |
| AG + QL pré-entraîné vs AG + UCB1                       | GA-UCB        |                 0.01736 |                 0.02943 |      0.05337   |      0.5305 | 0/31/0  |            31 | 0.2135   | non                     |
| AG + QL pré-entraîné vs AG + QL (en ligne)              | GA-QL         |                 0.01736 |                 0.02594 |      0.6786    |      0.5045 | 0/31/0  |            31 | 0.8697   | non                     |
| AG + QL pré-entraîné vs Meilleure config. fixe (oracle) | GA-FIX-UX+BF3 |                 0.01736 |                 0.02478 |      0.4349    |      0.5353 | 2/28/1  |            31 | 0.8697   | non                     |
| AG + QL (en ligne) vs AG standard                       | GA            |                 0.02594 |                 0.04065 |      0.0003264 |      0.6271 | 9/22/0  |            31 | 0.001632 | oui                     |
| AG + QL (en ligne) vs AG op. aléatoires                 | GA-RAND       |                 0.02594 |                 0.02448 |      0.929     |      0.5115 | 1/30/0  |            31 | 1        | non                     |
| AG + QL (en ligne) vs AG + UCB1                         | GA-UCB        |                 0.02594 |                 0.02943 |      0.02856   |      0.5345 | 0/31/0  |            31 | 0.1143   | non                     |
| AG + QL (en ligne) vs AG + QL pré-entraîné              | GA-QL-T       |                 0.02594 |                 0.01736 |      0.6786    |      0.4955 | 0/31/0  |            31 | 1        | non                     |
| AG + QL (en ligne) vs Meilleure config. fixe (oracle)   | GA-FIX-UX+BF3 |                 0.02594 |                 0.02478 |      0.6363    |      0.525  | 3/28/0  |            31 | 1        | non                     |
