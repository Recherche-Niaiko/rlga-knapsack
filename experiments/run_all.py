# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Campagnes expérimentales complètes (à lancer une fois) :

  python experiments/run_all.py [etape ...]      étapes : train e1 e2 e3 e5  (défaut : toutes)

  train  entraînement hors ligne des Q-tables (Q_OOD : UC/WC/SS ; Q_ALL_phi : toutes classes + φ(I))
  e1     KP 0/1 générés (Pisinger) : 6 classes × n ∈ {200, 500, 1000} × 3 instances
  e2     KP 0/1 de référence : instances_01_KP (n ≤ 2000) + Jooken et al. (2022)
  e3     MKP OR-Library : OR5x100 (30), OR10x100 (10), OR5x250 (10), SAC-94 weing (8)
  e5     passage à l'échelle : temps PD / PLNE / glouton / AG / AG+QL-T pour n → 10 000
"""
import os, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from common import RESULTS, run_campaign, references, attach_reference, N_WORKERS
from rlga_kp.instances import (generate_pisinger, load_kp01_large_scale, load_jooken, load_orlib_mkp)
from rlga_kp.ga import GAConfig, GeneticAlgorithm, ACTION_LABELS
from rlga_kp.training import train_qtable
from rlga_kp.controllers import make_controller

SEEDS = range(10)
CFG = {"n_generations": 200, "pop_size": 100}
QT = os.path.join(RESULTS, "qtables")
BASE = ["GA", "GA-RAND", "GA-UCB", "GA-QL", "GA-QL-T", "GA-FIX-UX+BF3"]
CTRL = {"GA-QL-T": {"qtable": os.path.join(QT, "Q_OOD.json")}}
LOG = open(os.path.join(RESULTS, "run_all.log"), "a")

def log(*a):
    msg = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(msg, flush=True); LOG.write(msg + "\n"); LOG.flush()

def finish(name, insts, df, milp_time=60, use_dp=True):
    ref = references(insts, milp_time=milp_time, use_dp=use_dp, log=log)
    ref.to_csv(os.path.join(RESULTS, name, "references.csv"), index=False)
    d = attach_reference(df, ref)
    d.to_csv(os.path.join(RESULTS, name, "runs_gap.csv"), index=False)
    log(name, "\n" + d.pivot_table(index="class", columns="method", values="gap_pct", aggfunc="mean").round(4).to_string())

def stage_train():
    os.makedirs(QT, exist_ok=True)
    cfg = GAConfig(**CFG)
    for name, classes, phi in [("Q_OOD", ["UC", "WC", "SS"], False),
                               ("Q_ALL_phi", ["UC", "WC", "SC", "ISC", "ASC", "SS"], True)]:
        train = [generate_pisinger(k, n, seed=500 + i) for k in classes for n in (100, 200) for i in range(2)]
        ctrl, hist = train_qtable(train, n_episodes_per_instance=4, cfg=cfg, use_instance_feature=phi, seed=1, log=log)
        ctrl.save(os.path.join(QT, f"{name}.json"))
        pd.DataFrame(hist).to_csv(os.path.join(QT, f"{name}_history.csv"), index=False)
        log("Q-table", name, "entraînée sur", len(train), "instances ×4 épisodes")

def stage_e1():
    insts = [generate_pisinger(k, n, seed=i) for k in ["UC", "WC", "SC", "ISC", "ASC", "SS"]
             for n in (200, 500, 1000) for i in range(3)]
    ctrl = dict(CTRL); ctrl["GA-QL-Tphi"] = {"qtable": os.path.join(QT, "Q_ALL_phi.json")}
    df = run_campaign("e1_kp01_generes", insts, BASE + ["GA-QL-Tphi"], SEEDS, CFG, ctrl, log=log)
    finish("e1_kp01_generes", insts, df, milp_time=30)

def stage_e2():
    insts = load_kp01_large_scale(max_n=2000) + load_jooken()
    df = run_campaign("e2_kp01_benchmarks", insts, BASE, SEEDS, CFG, CTRL, log=log)
    finish("e2_kp01_benchmarks", insts, df, milp_time=60)

def stage_e3():
    insts = (load_orlib_mkp("chubeas/OR5x100") + load_orlib_mkp("chubeas/OR10x100")[:10]
             + load_orlib_mkp("chubeas/OR5x250")[:10] + load_orlib_mkp("sac94/weing"))
    for i in insts:
        i.klass = "MKP-" + i.meta["subset"].split("/")[-1]
    df = run_campaign("e3_mkp", insts, BASE, SEEDS, CFG, CTRL, log=log)
    finish("e3_mkp", insts, df, milp_time=60, use_dp=False)

def _scal_task(args):
    from rlga_kp.exact import solve_dp, solve_milp
    from rlga_kp.heuristics import run_greedy
    k, n, method, seed = args
    inst = generate_pisinger(k, n, seed=seed)
    if method == "DP":
        r = solve_dp(inst, reconstruct=False); return (k, n, method, seed, r["value"], r["time"], r["status"])
    if method == "MILP":
        r = solve_milp(inst, time_limit=120); return (k, n, method, seed, r["value"], r["time"], r["status"])
    if method == "GREEDY":
        r = run_greedy(inst); return (k, n, method, seed, r["value"], r["time"], "heuristique")
    r = GeneticAlgorithm(inst, GAConfig(**CFG), make_controller(method, **CTRL.get(method, {})), seed=seed).run()
    return (k, n, method, seed, r.value, r.time, "métaheuristique")

def stage_e5():
    from concurrent.futures import ProcessPoolExecutor
    tasks = [(k, n, m, s) for k in ("UC", "SC") for n in (100, 500, 1000, 2000, 5000, 10000)
             for m in ("DP", "MILP", "GREEDY", "GA", "GA-QL-T") for s in range(3)]
    from common import MP
    with ProcessPoolExecutor(min(4, N_WORKERS), mp_context=MP) as ex:
        rows = list(ex.map(_scal_task, tasks))
    out = os.path.join(RESULTS, "e5_scalabilite"); os.makedirs(out, exist_ok=True)
    pd.DataFrame(rows, columns=["class", "n", "method", "seed", "value", "time", "status"]).to_csv(
        os.path.join(out, "scalability.csv"), index=False)
    log("e5 terminé")

if __name__ == "__main__":
    stages = sys.argv[1:] or ["train", "e1", "e2", "e3", "e5"]
    for s in stages:
        log("=== étape", s, "===")
        globals()[f"stage_{s}"]()
    log("=== FIN ===")
