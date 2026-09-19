# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""Exp. 0 — Pilote de calibration des hyperparamètres du Q-learning.
Instances de calibration DISJOINTES des instances de test (graines 900+)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import run_campaign, references, attach_reference, RESULTS
from rlga_kp.instances import generate_pisinger
import pandas as pd

insts = [generate_pisinger(k, n, seed=900 + i) for k in ["SC", "ASC", "UC"] for n in [500] for i in range(2)]
variants = {
    "GA-QL": {},                                  # défaut : alpha .1, gamma .8, eps 1→.05 sur 50 %
    "GA-QL-a": {"eps_start": 0.3, "eps_frac": 0.3},
    "GA-QL-b": {"gamma": 0.5},
    "GA-QL-c": {"alpha": 0.3, "eps_start": 0.5},
}
# enregistrement des variantes sous des clés distinctes
import rlga_kp.controllers as C
_orig = C.make_controller
def mk(key, **kw):
    if key.startswith("GA-QL-") and key != "GA-QL-T":
        return C.QLearningController(name=key, **kw)
    return _orig(key, **kw)
C.make_controller = mk
import common; common.make_controller = mk

ref = references(insts, milp_time=30)
df = run_campaign("exp0_pilot", insts, ["GA", "GA-RAND", "GA-UCB"] + list(variants), range(6),
                  cfg_kw={"n_generations": 200}, ctrl_kw=variants)
df = attach_reference(df, ref)
ref.to_csv(os.path.join(RESULTS, "exp0_pilot", "references.csv"), index=False)
df.to_csv(os.path.join(RESULTS, "exp0_pilot", "runs_gap.csv"), index=False)
print(df.pivot_table(index="class", columns="method", values="gap_pct", aggfunc="mean").round(4).to_string())
print(df.groupby("method")["gap_pct"].mean().round(4).sort_values().to_string())
