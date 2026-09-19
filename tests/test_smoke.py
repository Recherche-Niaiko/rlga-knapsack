# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""Test de fumée : instances, méthodes exactes et AG piloté sur une petite instance."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rlga_kp.controllers import make_controller  # noqa: E402
from rlga_kp.exact import solve_dp  # noqa: E402
from rlga_kp.ga import GAConfig, GeneticAlgorithm  # noqa: E402
from rlga_kp.instances import generate_pisinger, load_jooken  # noqa: E402

inst = generate_pisinger("SC", 100, seed=0)
opt = solve_dp(inst)["value"]
qt = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "qtables", "Q_OOD.json")
for key, kw in [("GA", {}), ("GA-RAND", {}), ("GA-QL", {}), ("GA-QL-T", {"qtable": qt})]:
    r = GeneticAlgorithm(inst, GAConfig(n_generations=30), make_controller(key, **kw), seed=0).run()
    assert r.feasible and r.value <= opt + 1e-9, key
    print(f"{key:8s} écart = {100 * (opt - r.value) / opt:.3f} %")
assert len(load_jooken()) == 16
print("OK")
