**Tests statistiques — exp0_pilot**

| comparaison                             | méthode   |   écart moyen cible (%) |   écart moyen autre (%) |   p (Wilcoxon) |   A12 moyen | V/E/D   |   n instances |   p Holm | significatif (α=0,05)   |
|:----------------------------------------|:----------|------------------------:|------------------------:|---------------:|------------:|:--------|--------------:|---------:|:------------------------|
| AG + QL (en ligne) vs AG standard       | GA        |                 0.01817 |                 0.06468 |         0.1562 |      0.787  | 4/2/0   |             6 |   0.4688 | non                     |
| AG + QL (en ligne) vs AG op. aléatoires | GA-RAND   |                 0.01817 |                 0.01577 |         0.25   |      0.4977 | 0/6/0   |             6 |   0.4688 | non                     |
| AG + QL (en ligne) vs AG + UCB1         | GA-UCB    |                 0.01817 |                 0.01399 |         0.1875 |      0.4792 | 0/6/0   |             6 |   0.4688 | non                     |
