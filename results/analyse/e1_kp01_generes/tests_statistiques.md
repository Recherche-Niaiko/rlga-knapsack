**Tests statistiques — e1_kp01_generes**

| comparaison                                             | méthode       |   écart moyen cible (%) |   écart moyen autre (%) |   p (Wilcoxon) |   A12 moyen | V/E/D   |   n instances |    p Holm | significatif (α=0,05)   |
|:--------------------------------------------------------|:--------------|------------------------:|------------------------:|---------------:|------------:|:--------|--------------:|----------:|:------------------------|
| AG + QL pré-entraîné vs AG standard                     | GA            |                0.007435 |                0.03823  |      5.678e-09 |      0.738  | 28/26/0 |            54 | 3.407e-08 | oui                     |
| AG + QL pré-entraîné vs AG op. aléatoires               | GA-RAND       |                0.007435 |                0.01108  |      9.01e-05  |      0.5878 | 9/45/0  |            54 | 0.0004505 | oui                     |
| AG + QL pré-entraîné vs AG + UCB1                       | GA-UCB        |                0.007435 |                0.01093  |      0.0009567 |      0.5829 | 10/44/0 |            54 | 0.00287   | oui                     |
| AG + QL pré-entraîné vs AG + QL (en ligne)              | GA-QL         |                0.007435 |                0.01107  |      0.000397  |      0.5785 | 7/47/0  |            54 | 0.001588  | oui                     |
| AG + QL pré-entraîné vs AG + QL pré-entraîné + φ(I)     | GA-QL-Tphi    |                0.007435 |                0.01054  |      0.001533  |      0.5664 | 7/47/0  |            54 | 0.003067  | oui                     |
| AG + QL pré-entraîné vs Meilleure config. fixe (oracle) | GA-FIX-UX+BF3 |                0.007435 |                0.004924 |      0.001725  |      0.4208 | 0/45/9  |            54 | 0.003067  | oui                     |
| AG + QL (en ligne) vs AG standard                       | GA            |                0.01107  |                0.03823  |      1.424e-08 |      0.7095 | 24/30/0 |            54 | 8.543e-08 | oui                     |
| AG + QL (en ligne) vs AG op. aléatoires                 | GA-RAND       |                0.01107  |                0.01108  |      0.8108    |      0.5056 | 0/53/1  |            54 | 1         | non                     |
| AG + QL (en ligne) vs AG + UCB1                         | GA-UCB        |                0.01107  |                0.01093  |      0.8614    |      0.5083 | 1/51/2  |            54 | 1         | non                     |
| AG + QL (en ligne) vs AG + QL pré-entraîné              | GA-QL-T       |                0.01107  |                0.007435 |      0.000397  |      0.4215 | 0/47/7  |            54 | 0.001588  | oui                     |
| AG + QL (en ligne) vs AG + QL pré-entraîné + φ(I)       | GA-QL-Tphi    |                0.01107  |                0.01054  |      0.4802    |      0.4878 | 0/53/1  |            54 | 1         | non                     |
| AG + QL (en ligne) vs Meilleure config. fixe (oracle)   | GA-FIX-UX+BF3 |                0.01107  |                0.004924 |      1.255e-05 |      0.3583 | 0/37/17 |            54 | 6.275e-05 | oui                     |
