# Rapport de performance — 19/09/2026 16:30

Instances Pisinger SC, 1 exécution par variante d'AG, 100 générations, PLNE limitée à 10 s ; chaque méthode dans le processus encadré (mémoire ≤ 2048 Mo, un fil, nice 10).

|    n | méthode       |   durée réelle (s) |   durée estimée (s) |   mémoire max. (Mo) |
|-----:|:--------------|-------------------:|--------------------:|--------------------:|
|  200 | GREEDY        |               0.45 |                2    |                 198 |
|  200 | DP            |               0.53 |                2.04 |                 198 |
|  200 | MILP          |               0.94 |               12    |                 198 |
|  200 | GA            |               0.83 |                2.22 |                 198 |
|  200 | GA-RAND       |               0.85 |                2.22 |                 198 |
|  200 | GA-UCB        |               0.88 |                2.22 |                 198 |
|  200 | GA-QL         |               0.9  |                2.22 |                 198 |
|  200 | GA-QL-T       |               1.01 |                2.22 |                 198 |
|  200 | GA-FIX-UX+BF3 |               0.95 |                2.22 |                 198 |
| 1000 | GREEDY        |               0.47 |                2    |                 198 |
| 1000 | DP            |               1.28 |                3.02 |                 198 |
| 1000 | MILP          |              10.84 |               12    |                 198 |
| 1000 | GA            |               1.69 |                3.1  |                 198 |
| 1000 | GA-RAND       |               1.85 |                3.1  |                 198 |
| 1000 | GA-UCB        |               1.86 |                3.1  |                 198 |
| 1000 | GA-QL         |               1.93 |                3.1  |                 198 |
| 1000 | GA-QL-T       |               1.9  |                3.1  |                 198 |
| 1000 | GA-FIX-UX+BF3 |               1.97 |                3.1  |                 198 |
| 2000 | GREEDY        |               0.49 |                2    |                 198 |
| 2000 | DP            |               4.69 |                6.06 |                 235 |
| 2000 | MILP          |              10.88 |               12    |                 235 |
| 2000 | GA            |               2.99 |                4.2  |                 235 |
| 2000 | GA-RAND       |               2.86 |                4.2  |                 235 |
| 2000 | GA-UCB        |               2.89 |                4.2  |                 235 |
| 2000 | GA-QL         |               2.78 |                4.2  |                 235 |
| 2000 | GA-QL-T       |               3.01 |                4.2  |                 235 |
| 2000 | GA-FIX-UX+BF3 |               3.2  |                4.2  |                 235 |

La mémoire est le maximum observé sur l'ensemble des processus de calcul déjà terminés.
