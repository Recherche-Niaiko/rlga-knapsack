# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Outils communs aux campagnes expérimentales : exécution parallèle, références exactes,
sauvegarde des résultats (CSV + courbes NPZ).

Protocole commun (cf. 00_JOURNAL_DE_BORD) :
  * budget identique pour toutes les variantes d'AG : P = 100 individus × G générations ;
  * mêmes graines (seeds) pour toutes les méthodes (appariement pour les tests statistiques) ;
  * référence = optimum prouvé (fichier / PD / PLNE) sinon meilleure valeur connue.
"""
from __future__ import annotations

import os
import sys
import time
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rlga_kp.controllers import make_controller  # noqa: E402
from rlga_kp.exact import solve_dp, solve_milp  # noqa: E402
from rlga_kp.ga import GAConfig, GeneticAlgorithm, N_ACTIONS  # noqa: E402
from rlga_kp.heuristics import dantzig_bound, run_greedy  # noqa: E402
from rlga_kp.instances import instance_features  # noqa: E402

RESULTS = os.path.join(ROOT, "results")
N_WORKERS = max(1, (os.cpu_count() or 2) - 1)
# « spawn » évite les blocages liés au fork après initialisation d'OpenBLAS
MP = mp.get_context("spawn")


def _ga_task(args):
    inst, key, seed, cfg_kw, ctrl_kw = args
    import os as _os
    _os.environ.setdefault("OMP_NUM_THREADS", "1")
    ctrl = make_controller(key, **dict(ctrl_kw))
    ga = GeneticAlgorithm(inst, GAConfig(**cfg_kw), ctrl, seed=seed)
    r = ga.run()
    acts = np.array(r.actions)
    G = len(acts)
    # fréquence des actions par tiers de la recherche (début / milieu / fin)
    phase_freq = np.zeros((3, N_ACTIONS))
    for ph in range(3):
        seg = acts[ph * G // 3:(ph + 1) * G // 3]
        if len(seg):
            phase_freq[ph] = np.bincount(seg, minlength=N_ACTIONS) / len(seg)
    curve = np.array(r.curve)
    final = curve[-1]
    hit = int(np.argmax(curve >= final - 1e-9)) + 1
    return {"instance": inst.name, "method": key, "seed": seed, "value": r.value, "time": r.time,
            "evaluations": r.evaluations, "feasible": r.feasible, "gen_to_best": hit,
            "final_diversity": r.diversity_curve[-1]}, curve, np.array(r.diversity_curve), phase_freq


def _ref_one(args):
    inst, milp_time, use_dp, use_milp = args
    return _reference_row(inst, milp_time, use_dp, use_milp)


def references(instances, milp_time=60.0, use_dp=True, use_milp=True, log=print) -> pd.DataFrame:
    """Références (glouton, borne LP, PD, PLNE) calculées en parallèle."""
    with ProcessPoolExecutor(N_WORKERS, mp_context=MP) as ex:
        rows = list(ex.map(_ref_one, [(i, milp_time, use_dp, use_milp) for i in instances]))
    for row in rows:
        log(f"  réf. {row['instance']}: opt={row['optimum_file']} dp={row.get('dp')} milp={row.get('milp')} "
            f"({row.get('milp_status')}) glouton={row['greedy']:.0f}")
    return pd.DataFrame(rows)


def _reference_row(inst, milp_time, use_dp, use_milp):
    feats = instance_features(inst)
    g = run_greedy(inst)
    row = {"instance": inst.name, "family": inst.family, "class": inst.klass, "n": inst.n, "m": inst.m,
           "optimum_file": inst.optimum, "greedy": g["value"], "t_greedy": g["time"],
           "ub_lp": dantzig_bound(inst), **{f"f_{k}": v for k, v in feats.items()}}
    if use_dp and not inst.is_mkp:
        d = solve_dp(inst, reconstruct=False)
        row.update(dp=d["value"], t_dp=d["time"], dp_status=d["status"])
    if use_milp:
        mi = solve_milp(inst, time_limit=milp_time)
        row.update(milp=mi["value"], t_milp=mi["time"], milp_status=mi["status"], milp_bound=mi.get("bound"))
    return row


def run_campaign(name, instances, keys, seeds, cfg_kw=None, ctrl_kw=None, log=print):
    """Exécute toutes les combinaisons (instance × méthode × graine) en parallèle."""
    cfg_kw = cfg_kw or {}
    ctrl_kw = ctrl_kw or {}
    out = os.path.join(RESULTS, name)
    os.makedirs(out, exist_ok=True)
    tasks = [(inst, k, s, cfg_kw, tuple(ctrl_kw.get(k, {}).items())) for inst in instances for k in keys
             for s in seeds]
    rows, curves, divs, phases = [], {}, {}, {}
    t0 = time.time()
    with ProcessPoolExecutor(N_WORKERS, mp_context=MP) as ex:
        futs = [ex.submit(_ga_task, t) for t in tasks]
        for i, f in enumerate(as_completed(futs), 1):
            row, c, d, ph = f.result()
            rows.append(row)
            key = (row["instance"], row["method"])
            curves.setdefault(key, []).append(c)
            divs.setdefault(key, []).append(d)
            phases.setdefault(key, []).append(ph)
            if i % max(1, len(tasks) // 40) == 0:
                log(f"  [{name}] {i}/{len(tasks)} exécutions ({time.time() - t0:.0f} s)")
    df = pd.DataFrame(rows).sort_values(["instance", "method", "seed"])
    df.to_csv(os.path.join(out, "runs.csv"), index=False)
    L = min(len(c) for v in curves.values() for c in v)
    np.savez_compressed(os.path.join(out, "curves.npz"),
                        keys=np.array([f"{a}||{b}" for a, b in curves]),
                        best_mean=np.array([np.mean([c[:L] for c in v], axis=0) for v in curves.values()]),
                        div_mean=np.array([np.mean([d[:L] for d in v], axis=0) for v in divs.values()]),
                        phase_freq=np.array([np.mean(v, axis=0) for v in phases.values()]))
    log(f"  [{name}] terminé : {len(df)} exécutions en {time.time() - t0:.0f} s → {out}")
    return df


def attach_reference(df_runs: pd.DataFrame, df_ref: pd.DataFrame) -> pd.DataFrame:
    """Ajoute la valeur de référence (optimum prouvé ou meilleure connue) et l'écart relatif (%)."""
    ref = df_ref.set_index("instance")
    best_run = df_runs.groupby("instance")["value"].max()
    refs = {}
    for inst in ref.index:
        cands = [ref.loc[inst].get("optimum_file"), ref.loc[inst].get("dp"), ref.loc[inst].get("milp"),
                 best_run.get(inst, np.nan)]
        cands = [c for c in cands if c is not None and not pd.isna(c)]
        refs[inst] = max(cands)
    df = df_runs.copy()
    df["reference"] = df["instance"].map(refs)
    df["gap_pct"] = 100.0 * (df["reference"] - df["value"]) / df["reference"]
    df["optimal_hit"] = df["gap_pct"] <= 1e-9
    meta_cols = [c for c in ["family", "class", "n", "m"] if c in ref.columns]
    df = df.merge(ref[meta_cols], left_on="instance", right_index=True, how="left")
    return df
