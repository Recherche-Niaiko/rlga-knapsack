# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""Tests de robustesse de l'encadrement des ressources (app_taipy/ressources.py).

Ils vérifient que tout calcul lourd de la plateforme : est estimé et refusé au-delà du budget ;
s'exécute dans un processus séparé, de priorité basse et à un seul fil ; est arrêté s'il dépasse
la mémoire ou la durée autorisées, ou sur demande ; attend son tour dans une file globale ;
et ne bloque pas le serveur pendant son exécution.
"""
import os
import threading
import time
import unittest
from unittest import mock

import _commun  # noqa: F401
import backend as B
import ressources as RS


def limites(**kw):
    return mock.patch.object(RS, "LIMITES", RS.Limites(**{**RS.LIMITES.__dict__, **kw}))


class TestEstimationEtBudget(unittest.TestCase):
    def test_estimation_croissante(self):
        petit = B.build_instance({"source": B.SOURCES[0], "n": 200})
        grand = B.build_instance({"source": B.SOURCES[0], "n": 5000})
        cles = list(B.METHODS)
        self.assertLess(RS.estimer_comparaison(petit, cles, 3, 200, 30), RS.estimer_comparaison(grand, cles, 3, 200, 30))
        self.assertLess(RS.estimer_comparaison(grand, cles, 3, 200, 30), RS.estimer_comparaison(grand, cles, 10, 500, 30))

    def test_cas_du_plantage_refuse(self):
        """Toutes les méthodes cochées, 10 exécutions, 500 générations, 5 000 objets : refusé avant lancement."""
        grand = B.build_instance({"source": B.SOURCES[0], "n": 5000})
        est = RS.estimer_comparaison(grand, list(B.METHODS), 10, 500, 30)
        self.assertGreater(est, RS.LIMITES.estimation_max_s)
        with self.assertRaises(RS.CalculRefuse) as ctx:
            RS.verifier_budget(est)
        self.assertIn("Réduisez", str(ctx.exception))

    def test_calcul_raisonnable_accepte(self):
        inst = B.build_instance({"source": B.SOURCES[0], "n": 500})
        RS.verifier_budget(RS.estimer_comparaison(inst, list(B.METHODS), 3, 200, 30))   # ne lève rien

    def test_duree_lisible(self):
        self.assertEqual(RS.duree_lisible(42), "42 s")
        self.assertEqual(RS.duree_lisible(125), "2 min 05 s")
        self.assertEqual(RS.duree_lisible(3700), "1 h 01 min")


class TestProcessusEncadre(unittest.TestCase):
    def test_resultat_identique_au_calcul_direct(self):
        inst = B.build_instance({"source": B.SOURCES[0], "classe": "SC", "n": 150, "seed": 2})
        direct = B.compare(inst, ["GREEDY", "DP", "GA-QL-T"], runs=2, generations=30)[0]
        isole = RS.executer("compare", inst, ["GREEDY", "DP", "GA-QL-T"], runs=2, generations=30)[0]
        self.assertEqual(list(direct["valeur moyenne"]), list(isole["valeur moyenne"]))

    def test_limites_appliquees_au_processus(self):
        r = RS.executer("sonde_ressources")
        self.assertNotEqual(r["pid"], os.getpid())                          # processus séparé
        self.assertEqual(r["openblas"], "1")                                # un seul fil numérique
        if os.name == "posix":
            self.assertGreaterEqual(r["nice"], RS.LIMITES.priorite)         # priorité basse
            self.assertEqual(r["memoire_max"], max(RS.MEMOIRE_MIN_MO, RS.LIMITES.memoire_mo) * 1024 * 1024)

    @unittest.skipUnless(os.name == "posix", "limites mémoire POSIX")
    def test_depassement_memoire(self):
        with limites(memoire_mo=1100):
            with self.assertRaises(RS.CalculInterrompu) as ctx:
                RS.executer("sonde_ressources", memoire_mo=1500)
        self.assertIn("Mémoire insuffisante", str(ctx.exception))

    def test_depassement_de_duree(self):
        t0 = time.perf_counter()
        with self.assertRaises(RS.CalculInterrompu) as ctx:
            RS.executer("sonde_ressources", secondes=30, duree_max_s=2)
        self.assertLess(time.perf_counter() - t0, 8)
        self.assertIn("Durée maximale", str(ctx.exception))

    def test_arret_sur_demande(self):
        erreurs = []
        t = threading.Thread(target=lambda: erreurs.append(RS.protege("sonde_ressources", secondes=30, jeton="A")))
        t0 = time.perf_counter()
        t.start()
        time.sleep(1.5)
        self.assertTrue(RS.arreter("A"))
        t.join(10)
        self.assertLess(time.perf_counter() - t0, 8)
        self.assertIsInstance(erreurs[0], RS.Echec)
        self.assertIn("arrêté à votre demande", erreurs[0].message)

    def test_erreur_rapportee_proprement(self):
        r = RS.protege("fonction_inexistante")
        self.assertIsInstance(r, RS.Echec)
        self.assertIn("AttributeError", r.message)


class TestFileEtReactivite(unittest.TestCase):
    def test_un_seul_calcul_a_la_fois(self):
        """Deux visiteurs lancent un calcul de 2 s : le second attend, les deux aboutissent en séquence."""
        fins, vus = [], []
        lancer = lambda j: (RS.executer("sonde_ressources", secondes=2, jeton=j), fins.append(time.perf_counter()))  # noqa: E731
        t0 = time.perf_counter()
        th = [threading.Thread(target=lancer, args=(j,)) for j in ("A", "B")]
        for t in th:
            t.start()
        time.sleep(1.0)
        vus.append(RS.etat_file())
        for t in th:
            t.join(30)
        self.assertEqual(vus[0]["en_cours"], 1)
        self.assertEqual(vus[0]["en_attente"], 1)
        self.assertGreaterEqual(max(fins) - t0, 4.0)                      # exécutions successives

    def test_file_pleine(self):
        with limites(attente_max_s=0.5):
            th = threading.Thread(target=lambda: RS.executer("sonde_ressources", secondes=3, jeton="long"))
            th.start()
            time.sleep(1.0)
            with self.assertRaises(RS.CalculInterrompu) as ctx:
                RS.executer("sonde_ressources", jeton="refuse")
            th.join(10)
        self.assertIn("occupé", str(ctx.exception))

    def test_serveur_reactif_pendant_un_calcul(self):
        """Pendant un calcul intensif, le processus du serveur répond en moins de 100 ms."""
        th = threading.Thread(target=lambda: RS.executer("sonde_ressources", secondes=3))
        th.start()
        retard_max, fin = 0.0, time.perf_counter() + 2.5
        while time.perf_counter() < fin:
            t = time.perf_counter()
            time.sleep(0.01)
            retard_max = max(retard_max, time.perf_counter() - t - 0.01)
        th.join(10)
        self.assertLess(retard_max, 0.1)


class TestTacheDeScenario(unittest.TestCase):
    def test_scenario_encadre(self):
        inst = B.build_instance({"source": B.SOURCES[0], "n": 100})
        res, conv = B.task_solve(inst, {"methodes": ["GREEDY", "GA"], "runs": 2, "generations": 20})
        self.assertEqual(list(res["code"]), ["GREEDY", "GA"])

    def test_scenario_trop_lourd_refuse(self):
        grand = B.build_instance({"source": B.SOURCES[0], "n": 5000})
        with self.assertRaises(RS.CalculRefuse):
            B.task_solve(grand, {"methodes": list(B.METHODS), "runs": 10, "generations": 500})


if __name__ == "__main__":
    unittest.main(verbosity=2)
