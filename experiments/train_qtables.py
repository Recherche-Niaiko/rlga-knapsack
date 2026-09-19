# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""Entraînement hors ligne des Q-tables utilisées par GA-QL-T (transfert).

Q_OOD  : entraînée UNIQUEMENT sur les classes faciles UC, WC, SS (n = 100, 200)
         → testée sur SC / ASC / ISC, tailles 500-1000, Jooken, MKP (hors distribution).
Q_ALL  : entraînée sur toutes les classes générées (n = 100, 200), avec descripteur d'instance φ(I)
         → teste l'apport du descripteur d'instance (tailles plus grandes = hors distribution).
Graines d'instances d'entraînement : 500+ (disjointes des tests : 0-99, calibration : 900+)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS
from rlga_kp.instances import generate_pisinger
from rlga_kp.training import train_qtable
from rlga_kp.ga import GAConfig, ACTION_LABELS
import numpy as np, pandas as pd

out = os.path.join(RESULTS, "qtables"); os.makedirs(out, exist_ok=True)
cfg = GAConfig(n_generations=200)
specs = {
    "Q_OOD": (["UC", "WC", "SS"], False),
    "Q_ALL_phi": (["UC", "WC", "SC", "ISC", "ASC", "SS"], True),
}
for name, (classes, use_phi) in specs.items():
    train = [generate_pisinger(k, n, seed=500 + i) for k in classes for n in (100, 200) for i in range(2)]
    ctrl, hist = train_qtable(train, n_episodes_per_instance=4, cfg=cfg, use_instance_feature=use_phi, seed=1)
    ctrl.save(os.path.join(out, f"{name}.json"))
    pd.DataFrame(hist).to_csv(os.path.join(out, f"{name}_history.csv"), index=False)
    Q = ctrl.Q
    pref = pd.Series(np.argmax(Q, axis=1)).map(lambda a: ACTION_LABELS[a]).value_counts()
    print(name, "— action gloutonne par état (nb d'états) :", pref.to_dict())
    print(name, "— Q moyen par action :", dict(zip(ACTION_LABELS, Q.mean(axis=0).round(3))))
