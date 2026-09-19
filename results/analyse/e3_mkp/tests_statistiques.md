**Tests statistiques — e3_mkp**

| comparaison                                             | méthode       |   écart moyen cible (%) |   écart moyen autre (%) |   p (Wilcoxon) |   A12 moyen | V/E/D   |   n instances |    p Holm | significatif (α=0,05)   |
|:--------------------------------------------------------|:--------------|------------------------:|------------------------:|---------------:|------------:|:--------|--------------:|----------:|:------------------------|
| AG + QL pré-entraîné vs AG standard                     | GA            |                  0.2355 |                  0.3346 |      3.148e-09 |      0.7058 | 28/30/0 |            58 | 1.574e-08 | oui                     |
| AG + QL pré-entraîné vs AG op. aléatoires               | GA-RAND       |                  0.2355 |                  0.2275 |      0.6843    |      0.5008 | 0/57/1  |            58 | 1         | non                     |
| AG + QL pré-entraîné vs AG + UCB1                       | GA-UCB        |                  0.2355 |                  0.2278 |      0.7362    |      0.5042 | 2/55/1  |            58 | 1         | non                     |
| AG + QL pré-entraîné vs AG + QL (en ligne)              | GA-QL         |                  0.2355 |                  0.2396 |      0.2054    |      0.5169 | 2/56/0  |            58 | 0.6162    | non                     |
| AG + QL pré-entraîné vs Meilleure config. fixe (oracle) | GA-FIX-UX+BF3 |                  0.2355 |                  0.1913 |      1.58e-05  |      0.4109 | 0/51/7  |            58 | 6.319e-05 | oui                     |
| AG + QL (en ligne) vs AG standard                       | GA            |                  0.2396 |                  0.3346 |      1.319e-08 |      0.6867 | 22/36/0 |            58 | 6.593e-08 | oui                     |
| AG + QL (en ligne) vs AG op. aléatoires                 | GA-RAND       |                  0.2396 |                  0.2275 |      0.4296    |      0.4845 | 0/56/2  |            58 | 0.4296    | non                     |
| AG + QL (en ligne) vs AG + UCB1                         | GA-UCB        |                  0.2396 |                  0.2278 |      0.01238   |      0.4854 | 1/57/0  |            58 | 0.03714   | oui                     |
| AG + QL (en ligne) vs AG + QL pré-entraîné              | GA-QL-T       |                  0.2396 |                  0.2355 |      0.2054    |      0.4831 | 0/56/2  |            58 | 0.4108    | non                     |
| AG + QL (en ligne) vs Meilleure config. fixe (oracle)   | GA-FIX-UX+BF3 |                  0.2396 |                  0.1913 |      1.406e-06 |      0.3999 | 0/49/9  |            58 | 5.625e-06 | oui                     |
