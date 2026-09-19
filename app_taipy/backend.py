# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Fonctions de calcul partagées par les pages de l'application et par les scénarios
(tâches déclarées dans config/config.toml, éditables dans Taipy Studio).
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

APP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(APP)
sys.path.insert(0, ROOT)

from rlga_kp.controllers import make_controller  # noqa: E402
from rlga_kp.exact import dp_feasibility, solve_dp, solve_milp  # noqa: E402
from rlga_kp.ga import ACTION_LABELS, GAConfig, GeneticAlgorithm  # noqa: E402
from rlga_kp.heuristics import dantzig_bound, run_greedy  # noqa: E402
from rlga_kp.instances import (KPInstance, generate_pisinger, instance_features, load_jooken,  # noqa: E402
                               load_kp01_large_scale, load_orlib_mkp)

import ressources as RS  # noqa: E402
from ressources import LIMITES, borner  # noqa: E402

RESULTS = os.path.join(ROOT, "results")
QTABLE = os.path.join(RESULTS, "qtables", "Q_OOD.json")
CASES = os.path.join(ROOT, "cas_usage")

METHODS = {
    "GREEDY": "Glouton étendu",
    "DP": "Programmation dynamique",
    "MILP": "PLNE (HiGHS, Branch-and-Cut)",
    "GA": "AG standard (1P + BF 1/n)",
    "GA-RAND": "AG opérateurs aléatoires",
    "GA-UCB": "AG + bandit UCB1",
    "GA-QL": "AG + Q-learning (en ligne)",
    "GA-QL-T": "AG + Q-learning pré-entraîné",
    "GA-FIX-UX+BF3": "AG fixe UX + BF3 (oracle de la calibration)",
}
GA_KEYS = ["GA", "GA-RAND", "GA-UCB", "GA-QL", "GA-QL-T", "GA-FIX-UX+BF3"]
SOURCES = ["Pisinger (générée)", "Benchmark instances_01_KP", "Jooken et al. (2022)", "MKP OR-Library", "Cas d'usage réel"]
CLASSES = ["UC", "WC", "SC", "ISC", "ASC", "SS"]


# ── Instances ────────────────────────────────────────────────────────────────

def list_files(source: str) -> list[str]:
    try:
        if source == "Benchmark instances_01_KP":
            return [i.name for i in load_kp01_large_scale(max_n=2000)]
        if source == "Jooken et al. (2022)":
            return [i.name for i in load_jooken()]
        if source == "MKP OR-Library":
            return [i.name for i in load_orlib_mkp("chubeas/OR5x100")[:10] + load_orlib_mkp("sac94/weing")]
        if source == "Cas d'usage réel":
            return sorted(f[:-4] for f in os.listdir(CASES)
                          if f.endswith(".csv") and os.path.exists(os.path.join(CASES, f[:-4] + ".json")))
    except Exception as e:  # jeux de données absents
        return [f"(indisponible : {e})"]
    return []


def load_use_case(name: str) -> tuple[KPInstance, pd.DataFrame, dict]:
    df = pd.read_csv(os.path.join(CASES, name + ".csv"))
    with open(os.path.join(CASES, name + ".json"), encoding="utf-8") as f:
        meta = json.load(f)
    wcols = meta["weight_columns"]
    inst = KPInstance(name=name, values=df[meta["value_column"]].values,
                      weights=df[wcols].values.T, capacities=meta["capacities"],
                      family="cas-usage", klass="MKP" if len(wcols) > 1 else "KP")
    return inst, df, meta


def build_instance(params: dict) -> KPInstance:
    src = params.get("source", SOURCES[0])
    if src == "Pisinger (générée)":
        return generate_pisinger(params.get("classe", "SC"), borner(int(params.get("n", 200)), 10, LIMITES.n_max),
                                 R=int(params.get("R", 1000)), seed=int(params.get("seed", 0)))
    name = params.get("fichier", "")
    if src == "Benchmark instances_01_KP":
        pool = load_kp01_large_scale(max_n=2000)
    elif src == "Jooken et al. (2022)":
        pool = load_jooken()
    elif src == "MKP OR-Library":
        pool = load_orlib_mkp("chubeas/OR5x100")[:10] + load_orlib_mkp("sac94/weing")
    else:
        return load_use_case(name)[0]
    for inst in pool:
        if inst.name == name:
            return inst
    return pool[0]


def describe(inst: KPInstance) -> pd.DataFrame:
    f = instance_features(inst)
    rows = [("Nom", inst.name), ("Famille / classe", f"{inst.family} / {inst.klass}"),
            ("Nombre d'objets n", inst.n), ("Nombre de contraintes m", inst.m),
            ("Capacité(s)", ", ".join(f"{c:,.0f}".replace(",", " ") for c in inst.capacities)),
            ("Optimum connu", "—" if inst.optimum is None else f"{inst.optimum:,.0f}".replace(",", " ")),
            ("Serrage C / Σw", f"{f['tightness']:.3f}"), ("Corrélation profit-poids", f"{f['corr_vw']:.3f}"),
            ("Écart glouton / borne de Dantzig", f"{100 * f['greedy_gap_ub']:.3f} %"),
            ("PD applicable ?", dp_feasibility(inst)[1] if not dp_feasibility(inst)[0] else "oui")]
    return pd.DataFrame(rows, columns=["Caractéristique", "Valeur"])


def items_frame(inst: KPInstance, max_points: int = 1500) -> pd.DataFrame:
    idx = np.arange(inst.n)
    if inst.n > max_points:
        idx = np.random.default_rng(0).choice(inst.n, max_points, replace=False)
    return pd.DataFrame({"poids": inst.weights.sum(axis=0)[idx], "profit": inst.values[idx]})


# ── Résolution ───────────────────────────────────────────────────────────────

def solve_one(inst: KPInstance, key: str, seed: int = 0, generations: int = 200, milp_time: float = 30.0):
    """Retourne (ligne de résultat, courbe du meilleur, actions)."""
    if key == "GREEDY":
        r = run_greedy(inst)
        return {"méthode": METHODS[key], "valeur": r["value"], "temps (s)": r["time"], "statut": "heuristique",
                "solution": r["solution"]}, None, None
    if key == "DP":
        r = solve_dp(inst)
        return {"méthode": METHODS[key], "valeur": r["value"], "temps (s)": r["time"], "statut": r["status"],
                "solution": r["solution"]}, None, None
    if key == "MILP":
        r = solve_milp(inst, time_limit=milp_time)
        return {"méthode": METHODS[key], "valeur": r["value"], "temps (s)": r["time"], "statut": r["status"],
                "solution": r["solution"]}, None, None
    kw = {"qtable": QTABLE} if key == "GA-QL-T" else {}
    ga = GeneticAlgorithm(inst, GAConfig(n_generations=generations), make_controller(key, **kw), seed=seed)
    r = ga.run()
    return {"méthode": METHODS[key], "valeur": r.value, "temps (s)": r.time, "statut": f"graine {seed}",
            "solution": r.solution}, r.curve, r.actions


def compare(inst: KPInstance, keys: list[str], runs: int = 3, generations: int = 200, milp_time: float = 30.0,
            progress=None):
    runs = borner(int(runs), 1, LIMITES.executions_max)
    generations = borner(int(generations), 10, LIMITES.generations_max)
    milp_time = borner(float(milp_time), 1.0, LIMITES.plne_max_s)
    keys = [k for k in keys if k in METHODS]
    rows, curves, actions = [], {}, {}
    total = sum(runs if k in GA_KEYS else 1 for k in keys)
    done = 0
    for k in keys:
        reps = runs if k in GA_KEYS else 1
        vals, times, best_sol, best_val = [], [], None, -np.inf
        for s in range(reps):
            row, curve, acts = solve_one(inst, k, seed=s, generations=generations, milp_time=milp_time)
            vals.append(row["valeur"]); times.append(row["temps (s)"])
            if row["valeur"] > best_val:
                best_val, best_sol = row["valeur"], row["solution"]
            if curve is not None:
                curves.setdefault(k, []).append(curve)
                actions.setdefault(k, []).append(acts)
            done += 1
            if progress:
                progress(done, total, METHODS[k])
        rows.append({"code": k, "méthode": METHODS[k], "valeur moyenne": float(np.nanmean(vals)),
                     "meilleure valeur": float(np.nanmax(vals)) if not np.all(np.isnan(vals)) else np.nan,
                     "temps moyen (s)": float(np.nanmean(times)), "exécutions": reps,
                     "statut": row["statut"], "_solution": best_sol})
    res = pd.DataFrame(rows)
    ref = max([v for v in [inst.optimum, res["meilleure valeur"].max()] if v is not None and not pd.isna(v)])
    res["écart moyen (%)"] = 100 * (ref - res["valeur moyenne"]) / ref
    res["référence"] = ref
    L = min((len(c) for v in curves.values() for c in v), default=0)
    conv = pd.DataFrame({"génération": np.arange(1, L + 1)})
    for k, v in curves.items():
        conv[METHODS[k]] = 100 * (ref - np.mean([c[:L] for c in v], axis=0)) / ref
    return res, conv, actions


def action_timeline(actions: list[list[int]], window: int = 20) -> pd.DataFrame:
    """Part (%) de chaque famille d'opérateur au fil des générations (moyenne glissante)."""
    A = np.array(actions)
    G = A.shape[1]
    out = pd.DataFrame({"génération": np.arange(1, G + 1)})
    for lab_idx, lab in enumerate(ACTION_LABELS):
        share = (A == lab_idx).mean(axis=0)
        out[lab] = pd.Series(share).rolling(window, min_periods=1).mean().values * 100
    return out


def qtable_frame(path: str = QTABLE) -> pd.DataFrame:
    with open(path) as f:
        Q = np.array(json.load(f)["Q"])[:27]
    div, stg, prg = ["D faible", "D moyenne", "D élevée"], ["stag. 0-2", "stag. 3-14", "stag. ≥15"], ["début", "milieu", "fin"]
    states = [f"{d} · {s} · {p}" for d in div for s in stg for p in prg]
    df = pd.DataFrame(Q, columns=ACTION_LABELS)
    df.insert(0, "état", states)
    df["action préférée"] = [ACTION_LABELS[i] if np.abs(q).sum() > 0 else "(non visité)" for i, q in
                             zip(Q.argmax(axis=1), Q)]
    return df


def chosen_items(inst: KPInstance, df_items: pd.DataFrame, solution: np.ndarray) -> pd.DataFrame:
    sel = df_items[np.asarray(solution).astype(bool)].copy()
    return sel


# ── Fonctions des tâches Taipy (scénarios) ───────────────────────────────────

def task_build_instance(parametres: dict) -> KPInstance:
    return build_instance(parametres)


def task_solve(instance: KPInstance, parametres: dict):
    """Tâche du scénario : même encadrement que la page de comparaison (budget, file, processus limité)."""
    keys = parametres.get("methodes", ["GREEDY", "GA", "GA-QL-T"])
    runs = borner(int(parametres.get("runs", 3)), 1, LIMITES.executions_max)
    gens = borner(int(parametres.get("generations", 200)), 10, LIMITES.generations_max)
    mt = borner(float(parametres.get("milp_time", 30)), 1.0, LIMITES.plne_max_s)
    RS.verifier_budget(RS.estimer_comparaison(instance, keys, runs, gens, mt))
    res, conv, _ = RS.executer("compare", instance, keys, runs=runs, generations=gens, milp_time=mt,
                               jeton=parametres.get("_jeton", "scenario"))
    return res.drop(columns=["_solution"]), conv


def load_campaign_table(campaign: str, table: str = "ecart_moyen") -> pd.DataFrame:
    p = os.path.join(RESULTS, "analyse", campaign, table + ".csv")
    if not os.path.exists(p):
        return pd.DataFrame({"info": [f"Résultats non disponibles : {p}"]})
    df = pd.read_csv(p)
    df = df.rename(columns={df.columns[0]: "classe / méthode"})
    return df.round(4)


def generic_items(df: pd.DataFrame, meta: dict) -> pd.DataFrame:
    """Vue normalisée (colonnes identiques pour tous les cas) : id, libellé, valeur, consommations."""
    cons = df[meta["weight_columns"]].apply(
        lambda r: " ; ".join(f"{v:g} {u}" for v, u in zip(r.values, meta["unites"])), axis=1)
    return pd.DataFrame({"id": df["id"].astype(str), "libellé": df[meta["label_column"]].astype(str),
                         "valeur": df[meta["value_column"]].astype(float), "consommation": cons})


# ── Vérification des hypothèses H1 à H4 sur une instance (cas d'usage) ─────────────────────

HYPOTHESES = {
    "H1": "L'AG piloté par apprentissage par renforcement obtient des écarts à l'optimum significativement plus "
          "faibles que l'AG standard, en particulier sur les instances corrélées.",
    "H2": "Appris en ligne, sur une seule exécution, le Q-learning ne surpasse pas une sélection aléatoire des "
          "opérateurs ; l'apport de l'apprentissage apparaît lorsque la politique est pré-entraînée.",
    "H3": "Une politique pré-entraînée sur des classes faciles et de petite taille se transfère à des instances hors "
          "distribution et y approche la meilleure configuration fixe.",
    "H4": "Les méthodes exactes restent supérieures sur le sac à dos 0/1 de taille modérée ; l'intérêt de l'approche "
          "croît lorsque la programmation dynamique devient infaisable et pour les variantes NP-difficiles au sens fort.",
}
# Verdicts établis dans le mémoire sur l'ensemble des campagnes (rappel, non recalculé ici).
VERDICTS_MEMOIRE = {
    "H1": "confirmée (E1, E2, E3)",
    "H2": "confirmée (E1, E2, E3)",
    "H3": "partiellement confirmée : oui entre classes et tailles du KP 0/1, non vers le MKP",
    "H4": "confirmée pour la première partie ; nuancée pour la seconde (E5, Jooken)",
}
HYP_GA = ["GA", "GA-RAND", "GA-QL", "GA-QL-T", "GA-FIX-UX+BF3"]
ALPHA = 0.05


def _paired_test(a: np.ndarray, b: np.ndarray) -> dict:
    """Test de Wilcoxon apparié unilatéral « a < b » (écarts, graines communes) + victoires/égalités/défaites."""
    from scipy.stats import wilcoxon
    d = np.asarray(a) - np.asarray(b)
    tol = 1e-9
    v, e, l = int((d < -tol).sum()), int((np.abs(d) <= tol).sum()), int((d > tol).sum())
    if v + l == 0:
        p = 1.0
    else:
        try:
            p = float(wilcoxon(a, b, zero_method="zsplit", alternative="less").pvalue)
        except ValueError:
            p = 1.0
    return {"p": p, "V/E/D": f"{v}/{e}/{l}"}


def run_hypotheses(inst: KPInstance, runs: int = 8, generations: int = 200, milp_time: float = 60.0) -> dict:
    """Exécute, sur une même instance et avec les mêmes graines, toutes les méthodes utiles aux hypothèses H1–H4."""
    runs = borner(int(runs), 5, LIMITES.executions_hyp_max)
    generations = borner(int(generations), 10, LIMITES.generations_max)
    milp_time = borner(float(milp_time), 1.0, LIMITES.plne_max_s)
    per_seed, times = {}, {}
    for k in HYP_GA:
        vals, ts = [], []
        for s in range(runs):
            row, _, _ = solve_one(inst, k, seed=s, generations=generations)
            vals.append(row["valeur"]); ts.append(row["temps (s)"])
        per_seed[k], times[k] = np.array(vals, float), float(np.mean(ts))
    exact = {"DP": solve_dp(inst, reconstruct=False) if inst.m == 1 else
             {"value": np.nan, "time": np.nan, "status": "infaisable : PD non applicable au MKP"},
             "MILP": solve_milp(inst, time_limit=milp_time)}
    budget = max(0.05, times["GA-QL-T"])
    exact["MILP-budget"] = solve_milp(inst, time_limit=budget)
    greedy = run_greedy(inst)
    cands = [inst.optimum] + [v.max() for v in per_seed.values()] + [e["value"] for e in exact.values()] + [greedy["value"]]
    ref = max(float(c) for c in cands if c is not None and not pd.isna(c))
    gaps = {k: 100 * (ref - v) / ref for k, v in per_seed.items()}
    corr = float(np.corrcoef(inst.values, inst.weights.sum(axis=0))[0, 1])
    return {"gaps": gaps, "times": times, "exact": exact, "greedy": greedy, "ref": ref, "runs": runs,
            "budget": budget, "milp_time": milp_time, "n": inst.n, "m": inst.m, "corr": corr, "name": inst.name}


def hypothesis_tables(R: dict) -> tuple[pd.DataFrame, dict]:
    """Tableau des méthodes et, pour chaque hypothèse : tests, verdict et explication."""
    g, T = R["gaps"], R["times"]
    rows = [{"méthode": METHODS[k], "écart moyen (%)": g[k].mean(), "écart-type (%)": g[k].std(ddof=1) if len(g[k]) > 1 else 0.0,
             "meilleur écart (%)": g[k].min(), "temps moyen (s)": T[k], "statut": f"{R['runs']} graines"} for k in HYP_GA]
    for key, lab in [("DP", "Programmation dynamique"), ("MILP", f"PLNE, limite {R['milp_time']:.0f} s"),
                     ("MILP-budget", f"PLNE, même temps que l'AG pré-entraîné ({R['budget']:.2f} s)")]:
        e = R["exact"][key]
        gap = np.nan if pd.isna(e["value"]) else 100 * (R["ref"] - e["value"]) / R["ref"]
        rows.append({"méthode": lab, "écart moyen (%)": gap, "écart-type (%)": np.nan, "meilleur écart (%)": gap,
                     "temps moyen (s)": e["time"], "statut": e["status"]})
    gr = R["greedy"]
    rows.append({"méthode": METHODS["GREEDY"], "écart moyen (%)": 100 * (R["ref"] - gr["value"]) / R["ref"],
                 "écart-type (%)": np.nan, "meilleur écart (%)": 100 * (R["ref"] - gr["value"]) / R["ref"],
                 "temps moyen (s)": gr["time"], "statut": "heuristique"})
    table = pd.DataFrame(rows)

    def test(a, b):
        r = _paired_test(g[a], g[b])
        return {"comparaison": f"{METHODS[a]} < {METHODS[b]}", "écart cible (%)": g[a].mean(),
                "écart autre (%)": g[b].mean(), "p (Wilcoxon, unilatéral)": r["p"], "V/E/D": r["V/E/D"],
                "significatif": "oui" if r["p"] < ALPHA else "non"}

    out = {}
    fr_ = lambda x: f"{x:.4f}".replace(".", ",")  # noqa: E731
    # H1
    t1 = [test("GA-QL-T", "GA"), test("GA-QL", "GA")]
    sig = [t for t in t1 if t["significatif"] == "oui"]
    lower = [t for t in t1 if t["écart cible (%)"] < t["écart autre (%)"]]
    if len(sig) == 2:
        v1, c1 = "Confirmée sur ce cas", "ok"
    elif sig:
        v1, c1 = "Partiellement confirmée sur ce cas", "partial"
    elif lower:
        v1, c1 = "Tendance favorable, non significative", "partial"
    else:
        v1, c1 = "Non confirmée sur ce cas", "ko"
    e1 = (f"Écart moyen : AG standard {fr_(g['GA'].mean())} %, AG + Q-learning en ligne {fr_(g['GA-QL'].mean())} %, "
          f"AG + Q-learning pré-entraîné {fr_(g['GA-QL-T'].mean())} %. Corrélation profit–poids de l'instance : "
          + f"{R['corr']:.2f}".replace(".", ",") + " (l'hypothèse prévoit un gain plus net sur les instances corrélées).")
    out["H1"] = {"tests": pd.DataFrame(t1), "verdict": v1, "classe": c1, "explication": e1}
    # H2
    t2 = [test("GA-QL", "GA-RAND"), test("GA-QL-T", "GA-QL"), test("GA-QL-T", "GA-RAND")]
    first = t2[0]["significatif"] == "non"
    second = t2[1]["significatif"] == "oui" or t2[2]["significatif"] == "oui"
    if first and second:
        v2, c2 = "Confirmée sur ce cas", "ok"
    elif first:
        v2, c2 = "Partiellement confirmée : le Q-learning en ligne ne bat pas l'aléatoire, le pré-entraînement n'apporte pas de gain significatif", "partial"
    else:
        v2, c2 = "Non confirmée : ici, le Q-learning en ligne bat significativement l'aléatoire", "ko"
    e2 = ("Première partie : le Q-learning en ligne ne doit pas être significativement meilleur que la sélection "
          "aléatoire. Seconde partie : le Q-learning pré-entraîné doit faire mieux que les deux.")
    out["H2"] = {"tests": pd.DataFrame(t2), "verdict": v2, "classe": c2, "explication": e2}
    # H3
    t3 = [test("GA-QL-T", "GA-RAND"), test("GA-FIX-UX+BF3", "GA-QL-T")]
    transfer = t3[0]["significatif"] == "oui"
    close = t3[1]["significatif"] == "non"
    if transfer and close:
        v3, c3 = "Confirmée sur ce cas", "ok"
    elif transfer or (close and g["GA-QL-T"].mean() <= g["GA-RAND"].mean()):
        v3, c3 = "Partiellement confirmée sur ce cas", "partial"
    else:
        v3, c3 = "Non confirmée sur ce cas", "ko"
    e3 = ("La Q-table a été apprise sur des KP 0/1 faciles de 100 à 200 objets : ce cas est hors de sa distribution "
          f"(n = {R['n']}, m = {R['m']}). Le transfert est utile si l'agent pré-entraîné bat la sélection aléatoire ; "
          "il « approche » la meilleure configuration fixe si celle-ci n'est pas significativement meilleure. "
          "La meilleure configuration fixe est approchée par UX + BF3, désignée par la calibration (E0, E1) ; "
          "elle n'est pas nécessairement la meilleure sur ce cas.")
    out["H3"] = {"tests": pd.DataFrame(t3), "verdict": v3, "classe": c3, "explication": e3}
    # H4
    mi, mb = R["exact"]["MILP"], R["exact"]["MILP-budget"]
    gap_qlt_best = g["GA-QL-T"].min()
    gap_mi = 100 * (R["ref"] - mi["value"]) / R["ref"] if not pd.isna(mi["value"]) else np.nan
    gap_mb = 100 * (R["ref"] - mb["value"]) / R["ref"] if not pd.isna(mb["value"]) else np.nan
    t4 = pd.DataFrame([
        {"comparaison": "PLNE (limite longue) contre meilleure exécution de l'AG pré-entraîné",
         "écart cible (%)": gap_mi, "écart autre (%)": gap_qlt_best, "statut PLNE": mi["status"],
         "temps PLNE (s)": mi["time"], "temps AG (s)": R["times"]["GA-QL-T"], "significatif": "—"},
        {"comparaison": "PLNE (même temps que l'AG) contre écart moyen de l'AG pré-entraîné",
         "écart cible (%)": gap_mb, "écart autre (%)": g["GA-QL-T"].mean(), "statut PLNE": mb["status"],
         "temps PLNE (s)": mb["time"], "temps AG (s)": R["times"]["GA-QL-T"], "significatif": "—"}])
    dp = R["exact"]["DP"]
    exact_wins = gap_mi <= gap_qlt_best + 1e-12 and mi["status"] == "optimal"
    if exact_wins and gap_mb <= g["GA-QL-T"].mean() + 1e-12:
        v4, c4 = "Première partie confirmée sur ce cas : la méthode exacte domine, même à temps égal", "ok"
    elif exact_wins:
        v4, c4 = "Première partie confirmée ; à temps égal, l'AG fait mieux que la PLNE interrompue", "partial"
    else:
        v4, c4 = "Seconde partie illustrée : la méthode exacte n'aboutit pas, l'AG garde son intérêt", "ok"
    e4 = (f"Programmation dynamique : {dp['status']}. Sur un cas de taille modérée, la PLNE prouve l'optimum ; "
          "l'intérêt de l'AG n'apparaît que si la méthode exacte n'aboutit pas dans le temps disponible "
          "(à tester sur une instance de Jooken à capacité 10⁸ via « Instance courante »).")
    out["H4"] = {"tests": t4, "verdict": v4, "classe": c4, "explication": e4}
    return table, out


# ── Sonde de diagnostic (tests de robustesse de l'encadrement des ressources) ─────────────

def sonde_ressources(memoire_mo: int = 0, secondes: float = 0.0) -> dict:
    """Alloue `memoire_mo` Mo puis calcule pendant `secondes` s ; renvoie les limites vues par le processus."""
    import resource
    bloc = np.ones(int(memoire_mo) * 131072, dtype=np.float64) if memoire_mo else None   # 131 072 × 8 o = 1 Mo
    fin = time.perf_counter() + secondes
    x = 0.0
    while time.perf_counter() < fin:
        x += 1.0
    return {"nice": os.nice(0), "openblas": os.environ.get("OPENBLAS_NUM_THREADS"),
            "memoire_max": resource.getrlimit(resource.RLIMIT_AS)[0] if os.name == "posix" else None,
            "alloue_mo": 0 if bloc is None else bloc.nbytes // 1048576, "pid": os.getpid()}
