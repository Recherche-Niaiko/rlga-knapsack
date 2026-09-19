# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""Tests unitaires du paquet rlga_kp et des fonctions de calcul de la plateforme (backend).

Lancement : python -m unittest discover -s tests -v   (depuis 03_REALISATION_RL_GA_KP)
"""
import itertools
import unittest

import numpy as np

import _commun  # noqa: F401  (chemins et variables d'environnement)
from _commun import QTABLE
from rlga_kp.controllers import ACTION_LABELS, make_controller
from rlga_kp.exact import dp_feasibility, solve_dp, solve_milp
from rlga_kp.ga import N_ACTIONS, GAConfig, GeneticAlgorithm
from rlga_kp.heuristics import dantzig_bound, run_greedy
from rlga_kp.instances import KPInstance, generate_pisinger, instance_features


def force_brute(inst: KPInstance) -> float:
    best = 0.0
    for bits in itertools.product((0, 1), repeat=inst.n):
        x = np.array(bits)
        if inst.is_feasible(x):
            best = max(best, inst.value(x))
    return best


def petite_instance(seed: int, n: int = 12, m: int = 1) -> KPInstance:
    rng = np.random.default_rng(seed)
    w = rng.integers(1, 30, size=(m, n))
    return KPInstance(f"alea{seed}", rng.integers(1, 40, n), w, (w.sum(axis=1) * 0.45).astype(int))


class TestInstances(unittest.TestCase):
    def test_classes_de_pisinger(self):
        for k in ["UC", "WC", "SC", "ISC", "ASC", "SS"]:
            inst = generate_pisinger(k, 100, seed=1)
            self.assertEqual((inst.n, inst.m), (100, 1))
            self.assertTrue(np.all(inst.weights > 0) and np.all(inst.values > 0))
            self.assertLess(inst.capacities[0], inst.weights.sum())
        sc = generate_pisinger("SC", 200, seed=0)
        self.assertGreater(instance_features(sc)["corr_vw"], 0.95)       # fortement corrélée
        ss = generate_pisinger("SS", 50, seed=0)
        np.testing.assert_allclose(ss.values, ss.weights[0])             # somme de sous-ensembles

    def test_generation_reproductible(self):
        a, b = generate_pisinger("WC", 80, seed=7), generate_pisinger("WC", 80, seed=7)
        np.testing.assert_array_equal(a.values, b.values)
        np.testing.assert_array_equal(a.weights, b.weights)

    def test_valeur_et_realisabilite(self):
        inst = KPInstance("t", [10, 5, 7], [[4, 3, 2]], [6])
        self.assertEqual(inst.value(np.array([1, 0, 1])), 17)
        self.assertTrue(inst.is_feasible(np.array([1, 0, 1])))
        self.assertFalse(inst.is_feasible(np.array([1, 1, 0])))


class TestMethodesExactes(unittest.TestCase):
    def test_pd_egale_force_brute(self):
        for s in range(6):
            inst = petite_instance(s)
            r = solve_dp(inst)
            self.assertAlmostEqual(r["value"], force_brute(inst))
            self.assertTrue(inst.is_feasible(r["solution"]))
            self.assertAlmostEqual(inst.value(r["solution"]), r["value"])

    def test_plne_egale_pd(self):
        for s in range(4):
            inst = generate_pisinger("SC", 60, seed=s)
            self.assertAlmostEqual(solve_milp(inst, time_limit=30)["value"], solve_dp(inst)["value"])

    def test_plne_mkp_egale_force_brute(self):
        inst = petite_instance(3, n=10, m=3)
        self.assertAlmostEqual(solve_milp(inst, time_limit=30)["value"], force_brute(inst))

    def test_pd_refuse_les_cas_hors_portee(self):
        self.assertFalse(dp_feasibility(petite_instance(0, m=2))[0])                 # MKP
        big = KPInstance("grand", [1, 2], [[1, 2]], [1e9])
        ok, pourquoi = dp_feasibility(big)
        self.assertFalse(ok)
        self.assertIn("capacité", pourquoi)
        self.assertTrue(np.isnan(solve_dp(big)["value"]))


class TestHeuristiques(unittest.TestCase):
    def test_glouton_realisable_et_garanti(self):
        for s in range(6):
            inst = petite_instance(s)
            g, opt = run_greedy(inst), force_brute(inst)
            self.assertTrue(g["feasible"])
            self.assertGreaterEqual(g["value"], opt / 2 - 1e-9)                   # garantie du glouton étendu
            self.assertGreaterEqual(dantzig_bound(inst), opt - 1e-9)              # borne supérieure


class TestAlgorithmeGenetique(unittest.TestCase):
    def test_reparation_rend_realisable(self):
        inst = generate_pisinger("SC", 80, seed=0)
        ga = GeneticAlgorithm(inst, GAConfig(), make_controller("GA"), seed=0)
        X = np.ones((20, inst.n), dtype=np.uint8)
        Y = ga.repair(X.copy())
        self.assertTrue(all(inst.is_feasible(y) for y in Y))

    def test_toutes_les_variantes(self):
        inst = generate_pisinger("SC", 100, seed=0)
        opt = solve_dp(inst)["value"]
        for key in ["GA", "GA-RAND", "GA-UCB", "GA-QL", "GA-QL-T", "GA-FIX-UX+BF3"]:
            kw = {"qtable": QTABLE} if key == "GA-QL-T" else {}
            r = GeneticAlgorithm(inst, GAConfig(n_generations=30), make_controller(key, **kw), seed=0).run()
            self.assertTrue(r.feasible, key)
            self.assertLessEqual(r.value, opt + 1e-9, key)
            self.assertEqual(len(r.curve), 30, key)
            self.assertTrue(all(b >= a - 1e-9 for a, b in zip(r.curve, r.curve[1:])), key)   # élitisme
            self.assertTrue(all(0 <= a < N_ACTIONS for a in r.actions), key)

    def test_reproductibilite_par_graine(self):
        inst = generate_pisinger("WC", 100, seed=0)
        run = lambda s: GeneticAlgorithm(inst, GAConfig(n_generations=20), make_controller("GA-RAND"), seed=s).run()  # noqa: E731
        self.assertEqual(run(3).value, run(3).value)

    def test_mkp(self):
        inst = petite_instance(5, n=40, m=3)
        r = GeneticAlgorithm(inst, GAConfig(n_generations=20), make_controller("GA-UCB"), seed=0).run()
        self.assertTrue(r.feasible)

    def test_actions(self):
        self.assertEqual(len(ACTION_LABELS), 9)
        self.assertIn("UX+BF3", ACTION_LABELS)
        with self.assertRaises(ValueError):
            make_controller("inconnu")


class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import backend
        cls.B = backend

    def test_comparaison_et_tableau(self):
        B = self.B
        inst = B.build_instance({"source": B.SOURCES[0], "classe": "SC", "n": 120, "seed": 1})
        res, conv, actions = B.compare(inst, ["GREEDY", "DP", "MILP", "GA", "GA-QL-T"], runs=2, generations=20)
        self.assertEqual(list(res["code"]), ["GREEDY", "DP", "MILP", "GA", "GA-QL-T"])
        self.assertAlmostEqual(res.loc[res.code == "DP", "écart moyen (%)"].iloc[0], 0.0)
        self.assertTrue((res["écart moyen (%)"] >= -1e-9).all())
        self.assertEqual(len(conv), 20)
        self.assertEqual(set(actions), {"GA", "GA-QL-T"})

    def test_bornes_des_parametres(self):
        B = self.B
        inst = B.build_instance({"source": B.SOURCES[0], "n": 60})
        res, conv, _ = B.compare(inst, ["GA", "INCONNUE"], runs=999, generations=5)
        self.assertEqual(int(res["exécutions"].iloc[0]), B.LIMITES.executions_max)   # 999 → borné
        self.assertEqual(len(conv), 10)                                              # 5 → 10 générations
        self.assertEqual(list(res["code"]), ["GA"])                                  # méthode inconnue ignorée
        grand = B.build_instance({"source": B.SOURCES[0], "n": 10 ** 7})
        self.assertEqual(grand.n, B.LIMITES.n_max)

    def test_cas_usage_et_hypotheses(self):
        B = self.B
        cas = B.list_files("Cas d'usage réel")
        self.assertGreaterEqual(len(cas), 4)
        inst, df, meta = B.load_use_case(cas[0])
        self.assertEqual(inst.n, len(df))
        R = B.run_hypotheses(inst, runs=5, generations=20, milp_time=10)
        table, details = B.hypothesis_tables(R)
        self.assertEqual(set(details), {"H1", "H2", "H3", "H4"})
        self.assertTrue(all(d["classe"] in ("ok", "partial", "ko") for d in details.values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
