# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Algorithme Génétique (AG) vectorisé pour le KP 0/1 et le MKP, avec un point d'extension
« contrôleur » qui choisit, à chaque génération, la combinaison d'opérateurs à appliquer.

  * Codage binaire x ∈ {0,1}^n ;
  * sélection par tournoi (taille k) ;
  * croisement : un point (1P), deux points (2P), uniforme (UX) ;
  * mutation : bit-flip 1/n (BF1), bit-flip 3/n (BF3), échange entrant/sortant (SWAP) ;
  * réparation gloutonne (suppression par pseudo-utilité croissante, puis ajout par
    pseudo-utilité décroissante) qui garantit la faisabilité — technique standard
    pour le KP/MKP (Chu & Beasley, 1998) ;
  * élitisme (e meilleurs individus conservés).

Le contrôleur (voir controllers.py) reçoit l'état de la recherche et renvoie une action
∈ {0..8} = (croisement, mutation). Un contrôleur « fixe » redonne l'AG classique.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from .instances import KPInstance

CROSSOVERS = ("1P", "2P", "UX")
MUTATIONS = ("BF1", "BF3", "SWAP")
ACTIONS = [(c, mu) for c in CROSSOVERS for mu in MUTATIONS]
ACTION_LABELS = [f"{c}+{mu}" for c, mu in ACTIONS]
N_ACTIONS = len(ACTIONS)
STANDARD_ACTION = ACTION_LABELS.index("1P+BF1")   # AG « classique » (Goldberg, 1989)


@dataclass
class GAConfig:
    pop_size: int = 100
    n_generations: int = 200
    tournament_size: int = 3
    crossover_rate: float = 0.9
    elite_size: int = 2
    init_greedy_fraction: float = 0.0   # part de la population initiale issue du glouton bruité
    time_limit: float | None = None     # arrêt anticipé (secondes)
    # Récompense de l'agent : "improve" = amélioration relative du meilleur (%),
    # "improve+success" = + taux de descendants meilleurs que leurs parents,
    # "improve+div" = + bonus de diversité (proposition R3, BRAINSTORMINGS/gap1-hypothese-knapsack.md)
    reward_mode: str = "improve"          # choix retenu après calibration (exp0, journal de bord)
    div_weight: float = 1.0
    div_target: float = 0.02


@dataclass
class RunResult:
    method: str
    value: float
    solution: np.ndarray
    time: float
    evaluations: int
    curve: list = field(default_factory=list)          # meilleure valeur par génération
    mean_curve: list = field(default_factory=list)     # valeur moyenne de la population
    diversity_curve: list = field(default_factory=list)
    actions: list = field(default_factory=list)        # action choisie à chaque génération
    rewards: list = field(default_factory=list)
    feasible: bool = True


class GeneticAlgorithm:
    def __init__(self, inst: KPInstance, cfg: GAConfig, controller, seed: int = 0):
        self.inst = inst
        self.cfg = cfg
        self.ctrl = controller
        self.rng = np.random.default_rng(seed)
        self.W = inst.weights                     # (m, n)
        self.C = inst.capacities                  # (m,)
        self.v = inst.values
        u = inst.pseudo_utility()
        self.add_order = np.argsort(-u, kind="stable")
        self.drop_order = self.add_order[::-1].copy()
        # min des poids sur les suffixes de add_order (arrêt anticipé de la phase d'ajout)
        w_sorted = self.W[:, self.add_order]
        self.suffix_min = np.minimum.accumulate(w_sorted[:, ::-1], axis=1)[:, ::-1]
        self.evaluations = 0

    # ── réparation (garantit la faisabilité) ────────────────────────────────
    def repair(self, X: np.ndarray) -> np.ndarray:
        loads = X @ self.W.T                                   # (P, m)
        over = np.any(loads > self.C + 1e-9, axis=1)
        if over.any():
            for i in self.drop_order:
                rows = over & (X[:, i] == 1)
                if rows.any():
                    X[rows, i] = 0
                    loads[rows] -= self.W[:, i]
                    over[rows] = np.any(loads[rows] > self.C + 1e-9, axis=1)
                    if not over.any():
                        break
        slack = self.C - loads
        for k, i in enumerate(self.add_order):
            if np.any(slack.max(axis=0) < self.suffix_min[:, k]):
                break
            rows = (X[:, i] == 0) & np.all(slack >= self.W[:, i] - 1e-9, axis=1)
            if rows.any():
                X[rows, i] = 1
                slack[rows] -= self.W[:, i]
        return X

    def evaluate(self, X: np.ndarray) -> np.ndarray:
        self.evaluations += X.shape[0]
        return X @ self.v

    # ── initialisation ─────────────────────────────────────────────────────
    def init_population(self) -> np.ndarray:
        P, n = self.cfg.pop_size, self.inst.n
        # probabilité d'inclusion calibrée pour démarrer près de la frontière de capacité
        frac = float(np.clip(np.min(self.C / np.maximum(self.W.sum(axis=1), 1e-12)), 0.02, 0.98))
        X = (self.rng.random((P, n)) < frac).astype(np.uint8)
        g = int(round(self.cfg.init_greedy_fraction * P))
        if g > 0:
            from .heuristics import greedy_solution
            base = greedy_solution(self.inst)
            for r in range(g):
                x = base.copy()
                flip = self.rng.random(n) < 2.0 / n
                x[flip] ^= 1
                X[r] = x
        return self.repair(X)

    # ── opérateurs ─────────────────────────────────────────────────────────
    def tournament(self, fit: np.ndarray, count: int) -> np.ndarray:
        idx = self.rng.integers(0, fit.shape[0], (count, self.cfg.tournament_size))
        return idx[np.arange(count), np.argmax(fit[idx], axis=1)]

    def crossover(self, A: np.ndarray, B: np.ndarray, kind: str):
        npairs, n = A.shape
        if kind == "UX":
            mask = self.rng.random((npairs, n)) < 0.5
        else:
            pos = np.arange(n)[None, :]
            if kind == "1P":
                a = self.rng.integers(1, n, npairs)[:, None]
                mask = pos >= a
            else:
                pts = np.sort(self.rng.integers(1, n, (npairs, 2)), axis=1)
                mask = (pos >= pts[:, :1]) & (pos < pts[:, 1:])
        do = (self.rng.random(npairs) < self.cfg.crossover_rate)[:, None]
        mask = mask & do
        C1 = np.where(mask, B, A)
        C2 = np.where(mask, A, B)
        return C1, C2

    def mutate(self, X: np.ndarray, kind: str) -> np.ndarray:
        P, n = X.shape
        if kind in ("BF1", "BF3"):
            rate = (1.0 if kind == "BF1" else 3.0) / n
            flip = self.rng.random((P, n)) < rate
            X ^= flip.astype(np.uint8)
        else:  # SWAP : un objet sélectionné sort, un objet non sélectionné entre
            r = self.rng.random((P, n))
            i_out = np.argmax(r * X, axis=1)
            i_in = np.argmax(r * (1 - X), axis=1)
            rows = np.arange(P)
            has_out = X[rows, i_out] == 1
            has_in = X[rows, i_in] == 0
            X[rows[has_out], i_out[has_out]] = 0
            X[rows[has_in], i_in[has_in]] = 1
        return X

    # ── état de la recherche (observé par le contrôleur) ────────────────────
    @staticmethod
    def gene_diversity(X: np.ndarray) -> float:
        p = X.mean(axis=0)
        return float(np.mean(4.0 * p * (1.0 - p)))          # ∈ [0,1] ; 0 = population convergée

    def observation(self, gen, fit, best, stagnation, X) -> dict:
        return {"gen": gen, "progress": gen / self.cfg.n_generations, "best": best,
                "mean": float(fit.mean()), "stagnation": stagnation,
                "diversity": self.gene_diversity(X)}

    # ── boucle principale ──────────────────────────────────────────────────
    def run(self, method_name: str | None = None) -> RunResult:
        t0 = time.perf_counter()
        cfg, P = self.cfg, self.cfg.pop_size
        X = self.init_population()
        fit = self.evaluate(X)
        b = int(np.argmax(fit))
        best, best_x = float(fit[b]), X[b].copy()
        stagnation = 0
        self.ctrl.reset(self.inst, cfg.n_generations, self.rng)
        res = RunResult(method=method_name or self.ctrl.name, value=best, solution=best_x, time=0.0,
                        evaluations=0)
        n_off = P - cfg.elite_size
        n_pairs = (n_off + 1) // 2
        obs = self.observation(0, fit, best, stagnation, X)
        for gen in range(cfg.n_generations):
            a = int(self.ctrl.select(obs))
            cx, mu = ACTIONS[a]
            par = self.tournament(fit, 2 * n_pairs)
            A, B = X[par[0::2]], X[par[1::2]]
            C1, C2 = self.crossover(A, B, cx)
            off = np.vstack([C1, C2])[:n_off]
            parent_fit = np.maximum(fit[par[0::2]], fit[par[1::2]])
            parent_fit = np.concatenate([parent_fit, parent_fit])[:n_off]
            off = self.repair(self.mutate(off, mu))
            off_fit = self.evaluate(off)
            elite = np.argsort(fit)[-cfg.elite_size:]
            X = np.vstack([X[elite], off])
            fit = np.concatenate([fit[elite], off_fit])
            b = int(np.argmax(fit))
            old_best = best
            if fit[b] > best + 1e-9:
                best, best_x = float(fit[b]), X[b].copy()
                stagnation = 0
            else:
                stagnation += 1
            nobs = self.observation(gen + 1, fit, best, stagnation, X)
            reward = 100.0 * (best - old_best) / max(abs(old_best), 1e-12)
            if cfg.reward_mode == "improve+success":
                reward += float(np.mean(off_fit > parent_fit + 1e-9))
            elif cfg.reward_mode == "improve+div":
                # pénalise l'effondrement de la diversité sous la cible D* (convergence prématurée)
                reward -= cfg.div_weight * max(0.0, cfg.div_target - nobs["diversity"]) / cfg.div_target
            self.ctrl.update(obs, a, reward, nobs)
            obs = nobs
            res.curve.append(best)
            res.mean_curve.append(float(fit.mean()))
            res.diversity_curve.append(nobs["diversity"])
            res.actions.append(a)
            res.rewards.append(reward)
            if cfg.time_limit and time.perf_counter() - t0 > cfg.time_limit:
                break
        res.value, res.solution = best, best_x
        res.time = time.perf_counter() - t0
        res.evaluations = self.evaluations
        res.feasible = self.inst.is_feasible(best_x)
        return res
