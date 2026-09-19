# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Méthodes exactes :
  * Programmation Dynamique (PD) pseudo-polynomiale O(n·C) pour le KP 0/1 (Bellman) ;
  * Programmation Linéaire en Nombres Entiers (PLNE) par Branch-and-Bound/Cut (solveur HiGHS via SciPy),
    utilisable pour le KP 0/1 et le MKP ;
  * borne de relaxation linéaire (LP).
"""
from __future__ import annotations

import time

import numpy as np

from .instances import KPInstance

DP_MAX_CELLS = 3e9          # au-delà : PD jugée infaisable (temps)
DP_MAX_CAPACITY = 5e7       # au-delà : vecteur de PD trop volumineux (mémoire)
DP_MAX_TABLE_BYTES = 6e8    # table de reconstruction (bits) maximale


def dp_feasibility(inst: KPInstance) -> tuple[bool, str]:
    if inst.is_mkp:
        return False, "PD non applicable au MKP (table m-dimensionnelle)"
    C = inst.capacities[0]
    if not np.allclose(inst.weights, np.round(inst.weights)) or C != int(C):
        return False, "PD nécessite des poids entiers"
    cells = inst.n * (C + 1)
    if C > DP_MAX_CAPACITY:
        return False, f"capacité C = {C:.3g} : mémoire O(C) ≈ {8 * C / 1e9:.1f} Go"
    if cells > DP_MAX_CELLS:
        return False, f"n·C = {cells:.3g} opérations : temps prohibitif"
    return True, "ok"


def solve_dp(inst: KPInstance, reconstruct: bool = True) -> dict:
    """PD de Bellman sur un vecteur 1D (vectorisée NumPy). Reconstruction via table de bits."""
    ok, why = dp_feasibility(inst)
    if not ok:
        return {"method": "Programmation dynamique", "value": np.nan, "solution": None, "time": np.nan,
                "feasible": False, "status": f"infaisable : {why}"}
    t0 = time.perf_counter()
    C = int(inst.capacities[0])
    w = np.round(inst.weights[0]).astype(np.int64)
    v = inst.values.astype(np.float64)
    n = inst.n
    dp = np.zeros(C + 1, dtype=np.float64)
    keep = None
    if reconstruct and n * (C + 1) / 8 <= DP_MAX_TABLE_BYTES:
        keep = np.zeros((n, (C + 8) // 8), dtype=np.uint8)
    for i in range(n):
        wi = w[i]
        if wi > C:
            continue
        cand = dp[:C + 1 - wi] + v[i]
        better = cand > dp[wi:]
        dp[wi:] = np.where(better, cand, dp[wi:])
        if keep is not None:
            row = np.zeros(C + 1, dtype=bool)
            row[wi:] = better
            keep[i] = np.packbits(row, bitorder="little")[: keep.shape[1]]
    value = float(dp[C])
    x = None
    if keep is not None:
        x = np.zeros(n, dtype=np.uint8)
        c = C
        for i in range(n - 1, -1, -1):
            if (keep[i, c >> 3] >> (c & 7)) & 1:
                x[i] = 1
                c -= w[i]
    return {"method": "Programmation dynamique", "value": value, "solution": x,
            "time": time.perf_counter() - t0, "feasible": True, "status": "optimal"}


def solve_milp(inst: KPInstance, time_limit: float = 60.0) -> dict:
    """PLNE résolue par HiGHS (Branch-and-Cut) via scipy.optimize.milp."""
    from scipy.optimize import Bounds, LinearConstraint, milp
    t0 = time.perf_counter()
    res = milp(c=-inst.values,
               constraints=LinearConstraint(inst.weights, -np.inf, inst.capacities),
               integrality=np.ones(inst.n), bounds=Bounds(0, 1),
               options={"time_limit": time_limit, "disp": False, "mip_rel_gap": 0.0})
    dt = time.perf_counter() - t0
    if res.x is None:
        return {"method": "PLNE (HiGHS B&B)", "value": np.nan, "solution": None, "time": dt,
                "feasible": False, "status": res.message}
    x = np.round(res.x).astype(np.uint8)
    status = "optimal" if res.status == 0 else "limite de temps"
    bound = None
    try:
        bound = -float(res.mip_dual_bound)
    except Exception:
        pass
    return {"method": "PLNE (HiGHS B&B)", "value": inst.value(x), "solution": x, "time": dt,
            "feasible": inst.is_feasible(x), "status": status, "bound": bound}


def lp_bound(inst: KPInstance) -> float:
    from scipy.optimize import linprog
    res = linprog(-inst.values, A_ub=inst.weights, b_ub=inst.capacities, bounds=(0, 1), method="highs")
    return float(-res.fun)
