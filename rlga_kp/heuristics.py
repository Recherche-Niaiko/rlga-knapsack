# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Méthodes de référence non évolutionnaires :
  * algorithme glouton (ratio v/w ou pseudo-utilité pour le MKP) ;
  * glouton étendu (max entre glouton et meilleur objet seul — 1/2-approximation pour le KP 0/1) ;
  * borne supérieure de Dantzig (relaxation continue du KP 0/1) ;
  * recherche aléatoire (borne basse naïve).
"""
from __future__ import annotations

import time

import numpy as np

from .instances import KPInstance


def greedy_solution(inst: KPInstance) -> np.ndarray:
    """Glouton par efficacité décroissante : on ajoute chaque objet s'il tient encore."""
    order = np.argsort(-inst.pseudo_utility(), kind="stable")
    x = np.zeros(inst.n, dtype=np.uint8)
    load = np.zeros(inst.m)
    for i in order:
        wi = inst.weights[:, i]
        if np.all(load + wi <= inst.capacities + 1e-9):
            x[i] = 1
            load += wi
    return x


def extended_greedy_solution(inst: KPInstance) -> np.ndarray:
    """Glouton étendu : meilleure des deux solutions {glouton, meilleur objet seul faisable}."""
    x = greedy_solution(inst)
    feas = np.all(inst.weights <= inst.capacities[:, None] + 1e-9, axis=0)
    if feas.any():
        j = int(np.argmax(np.where(feas, inst.values, -np.inf)))
        if inst.values[j] > inst.value(x):
            x = np.zeros(inst.n, dtype=np.uint8)
            x[j] = 1
    return x


def dantzig_bound(inst: KPInstance) -> float:
    """Borne de Dantzig (relaxation LP du KP 0/1). Pour le MKP : borne LP via la contrainte la plus serrée
    n'est pas valide en général ; on retourne alors la borne LP calculée par scipy (voir exact.lp_bound)."""
    if inst.is_mkp:
        from .exact import lp_bound
        return lp_bound(inst)
    w = inst.weights[0]
    order = np.argsort(-(inst.values / w), kind="stable")
    cap = inst.capacities[0]
    total = 0.0
    for i in order:
        if w[i] <= cap:
            cap -= w[i]
            total += inst.values[i]
        else:
            total += inst.values[i] * cap / w[i]
            break
    return float(total)


def run_greedy(inst: KPInstance, extended: bool = True) -> dict:
    t0 = time.perf_counter()
    x = extended_greedy_solution(inst) if extended else greedy_solution(inst)
    return {"method": "Glouton" if not extended else "Glouton étendu", "value": inst.value(x),
            "solution": x, "time": time.perf_counter() - t0, "feasible": inst.is_feasible(x)}
