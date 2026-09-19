# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""Tests de performance de la plateforme.

Pour chaque méthode et plusieurs tailles d'instance, mesure dans le processus encadré la durée réelle et
la mémoire maximale, les compare à l'estimation utilisée pour autoriser les calculs, et écrit un rapport
(results/performance/rapport_performance.md et .csv). Les assertions vérifient que :
  * l'estimation n'est jamais inférieure à la moitié de la durée réelle (pas de calcul lourd sous-estimé) ;
  * la mémoire d'un calcul reste très en deçà de la limite du processus ;
  * les calculs typiques de l'interface restent interactifs (moins de 30 s pour n = 1 000).
Lancement : python tests/test_performance.py   (≈ 1 à 2 minutes)
"""
import os
import resource
import time
import unittest

import pandas as pd

import _commun
import backend as B
import ressources as RS

SORTIE = os.path.join(_commun.ROOT, "results", "performance")
TAILLES = (200, 1000, 2000)
EXECUTIONS, GENERATIONS, PLNE_S = 1, 100, 10


class TestPerformance(unittest.TestCase):
    lignes: list = []

    @classmethod
    def setUpClass(cls):
        for n in TAILLES:
            inst = B.build_instance({"source": B.SOURCES[0], "classe": "SC", "n": n, "seed": 0})
            for k in B.METHODS:
                est = RS.estimer_comparaison(inst, [k], EXECUTIONS, GENERATIONS, PLNE_S)
                t0 = time.perf_counter()
                RS.executer("compare", inst, [k], runs=EXECUTIONS, generations=GENERATIONS, milp_time=PLNE_S)
                duree = time.perf_counter() - t0
                mem = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024   # Mo (Linux : Ko)
                cls.lignes.append({"n": n, "méthode": k, "durée réelle (s)": round(duree, 2),
                                   "durée estimée (s)": round(est, 2), "mémoire max. (Mo)": round(mem)})
        cls.df = pd.DataFrame(cls.lignes)
        os.makedirs(SORTIE, exist_ok=True)
        cls.df.to_csv(os.path.join(SORTIE, "rapport_performance.csv"), index=False)
        with open(os.path.join(SORTIE, "rapport_performance.md"), "w", encoding="utf-8") as f:
            f.write(f"# Rapport de performance — {time.strftime('%d/%m/%Y %H:%M')}\n\n"
                    f"Instances Pisinger SC, {EXECUTIONS} exécution par variante d'AG, {GENERATIONS} générations, "
                    f"PLNE limitée à {PLNE_S} s ; chaque méthode dans le processus encadré "
                    f"(mémoire ≤ {RS.LIMITES.memoire_mo} Mo, un fil, nice {RS.LIMITES.priorite}).\n\n")
            f.write(cls.df.to_markdown(index=False))
            f.write("\n\nLa mémoire est le maximum observé sur l'ensemble des processus de calcul déjà terminés.\n")
        print("\n" + cls.df.to_string(index=False))

    def test_estimation_prudente(self):
        significatif = self.df[self.df["durée réelle (s)"] > 1.0]
        ratio = significatif["durée estimée (s)"] / significatif["durée réelle (s)"]
        self.assertTrue((ratio >= 0.5).all(), significatif.assign(ratio=ratio).to_string())

    def test_memoire_bornee(self):
        self.assertLess(self.df["mémoire max. (Mo)"].max(), 0.8 * RS.LIMITES.memoire_mo)

    def test_interactivite(self):
        n1000 = self.df[self.df.n == 1000]
        self.assertLess(n1000["durée réelle (s)"].max(), 30)


if __name__ == "__main__":
    unittest.main(verbosity=2)
