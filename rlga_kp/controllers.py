# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Contrôleurs de l'AG — ils décident, à chaque génération, de l'action (croisement, mutation).

  FixedController        AG classique : toujours la même action (ex. 1P+BF1).
  RandomController       sélection uniforme aléatoire (ablation : diversité d'opérateurs sans apprentissage).
  UCBController          bandit manchot UCB1 (Auer et al., 2002) — référence classique de l'AOS.
  QLearningController    Q-learning tabulaire (Watkins & Dayan, 1992) sur l'état de la population
                         (diversité × stagnation × progression [× classe d'instance]).
                         - mode « en ligne » : Q-table vierge à chaque exécution ;
                         - mode « pré-entraîné » : Q-table apprise hors ligne sur d'autres instances
                           puis réutilisée (transfert), avec poursuite optionnelle de l'apprentissage.
"""
from __future__ import annotations

import json

import numpy as np

from .ga import N_ACTIONS, STANDARD_ACTION, ACTION_LABELS

# Seuils de discrétisation de l'état (calibrés empiriquement, cf. journal de bord)
DIV_THRESHOLDS = (0.01, 0.05)       # diversité génotypique : faible / moyenne / élevée
STAG_THRESHOLDS = (3, 15)           # stagnation (générations sans amélioration)
PROG_THRESHOLDS = (1 / 3, 2 / 3)    # début / milieu / fin de recherche
# Descripteur d'instance : écart relatif glouton / borne de Dantzig (proxy de difficulté)
INST_THRESHOLDS = (0.001, 0.01)


def _bin(x, th):
    for i, t in enumerate(th):
        if x < t:
            return i
    return len(th)


def instance_bin(inst) -> int:
    from .instances import instance_features
    return _bin(instance_features(inst)["greedy_gap_ub"], INST_THRESHOLDS)


class Controller:
    name = "controller"

    def reset(self, inst, n_generations, rng):
        self.rng = rng

    def select(self, obs) -> int:
        raise NotImplementedError

    def update(self, obs, action, reward, next_obs):
        pass


class FixedController(Controller):
    def __init__(self, action: int = STANDARD_ACTION, name: str | None = None):
        self.action = action
        self.name = name or f"AG fixe ({ACTION_LABELS[action]})"

    def select(self, obs):
        return self.action


class RandomController(Controller):
    name = "AG opérateurs aléatoires"

    def select(self, obs):
        return int(self.rng.integers(N_ACTIONS))


class UCBController(Controller):
    name = "AG + bandit UCB1"

    def __init__(self, c: float = 0.5):
        self.c = c

    def reset(self, inst, n_generations, rng):
        super().reset(inst, n_generations, rng)
        self.counts = np.zeros(N_ACTIONS)
        self.sums = np.zeros(N_ACTIONS)
        self.rmax = 1e-9
        self.t = 0

    def select(self, obs):
        self.t += 1
        if np.any(self.counts == 0):
            return int(np.flatnonzero(self.counts == 0)[0])
        mean = self.sums / self.counts / self.rmax
        ucb = mean + self.c * np.sqrt(2 * np.log(self.t) / self.counts)
        return int(np.argmax(ucb))

    def update(self, obs, action, reward, next_obs):
        self.counts[action] += 1
        self.sums[action] += reward
        self.rmax = max(self.rmax, reward)


class QLearningController(Controller):
    """Q-learning tabulaire avec exploration ε-greedy décroissante."""

    def __init__(self, alpha=0.1, gamma=0.8, eps_start=1.0, eps_end=0.05, eps_frac=0.5,
                 use_instance_feature=False, Q=None, learn=True, name=None):
        self.alpha, self.gamma = alpha, gamma
        self.eps_start, self.eps_end, self.eps_frac = eps_start, eps_end, eps_frac
        self.use_inst = use_instance_feature
        self.n_states = 27 * (3 if use_instance_feature else 1)
        self.Q0 = None if Q is None else np.array(Q, dtype=float)
        self.learn = learn
        self.name = name or ("AG + Q-learning (pré-entraîné)" if Q is not None else "AG + Q-learning")

    def reset(self, inst, n_generations, rng):
        super().reset(inst, n_generations, rng)
        self.Q = np.zeros((self.n_states, N_ACTIONS)) if self.Q0 is None else self.Q0.copy()
        self.ibin = instance_bin(inst) if self.use_inst else 0
        steps = max(1, int(self.eps_frac * n_generations))
        self.eps = self.eps_start
        self.decay = (self.eps_end / self.eps_start) ** (1.0 / steps) if self.eps_start > self.eps_end else 1.0
        self.visits = np.zeros_like(self.Q)

    def state(self, obs) -> int:
        d = _bin(obs["diversity"], DIV_THRESHOLDS)
        s = _bin(obs["stagnation"], STAG_THRESHOLDS)
        p = _bin(obs["progress"], PROG_THRESHOLDS)
        return self.ibin * 27 + d * 9 + s * 3 + p

    def select(self, obs):
        s = self.state(obs)
        if self.rng.random() < self.eps:
            a = int(self.rng.integers(N_ACTIONS))
        else:
            q = self.Q[s]
            a = int(self.rng.choice(np.flatnonzero(q == q.max())))
        self.eps = max(self.eps_end, self.eps * self.decay)
        return a

    def update(self, obs, action, reward, next_obs):
        s, s2 = self.state(obs), self.state(next_obs)
        self.visits[s, action] += 1
        if self.learn:
            td = reward + self.gamma * self.Q[s2].max() - self.Q[s, action]
            self.Q[s, action] += self.alpha * td

    # persistance de la Q-table (apprentissage hors ligne → transfert)
    def save(self, path):
        with open(path, "w") as f:
            json.dump({"Q": self.Q.tolist(), "use_instance_feature": self.use_inst,
                       "actions": ACTION_LABELS}, f)

    @staticmethod
    def load(path, **kw):
        with open(path) as f:
            d = json.load(f)
        return QLearningController(Q=d["Q"], use_instance_feature=d["use_instance_feature"], **kw)


def make_controller(key: str, **kw) -> Controller:
    """Fabrique utilisée par les expériences et l'application Taipy."""
    if key == "GA":
        return FixedController(STANDARD_ACTION, name="AG standard")
    if key.startswith("GA-FIX-"):
        a = ACTION_LABELS.index(key[len("GA-FIX-"):])
        return FixedController(a)
    if key == "GA-RAND":
        return RandomController()
    if key == "GA-UCB":
        return UCBController()
    if key == "GA-QL":
        return QLearningController(**kw)
    if key == "GA-QL-T":
        return QLearningController.load(kw.pop("qtable"), eps_start=0.05, eps_end=0.05,
                                        name="AG + Q-learning (pré-entraîné)", **kw)
    if key == "GA-QL-Tphi":
        return QLearningController.load(kw.pop("qtable"), eps_start=0.05, eps_end=0.05,
                                        name="AG + Q-learning (pré-entraîné, avec φ(I))", **kw)
    raise ValueError(key)


METHOD_LABELS = {
    "DP": "Programmation dynamique",
    "MILP": "PLNE (HiGHS)",
    "GREEDY": "Glouton étendu",
    "GA": "AG standard",
    "GA-RAND": "AG opérateurs aléatoires",
    "GA-UCB": "AG + bandit UCB1",
    "GA-QL": "AG + Q-learning",
    "GA-QL-T": "AG + Q-learning pré-entraîné",
    "GA-QL-Tphi": "AG + Q-learning pré-entraîné + φ(I)",
    "GA-FIX-UX+BF3": "AG meilleure config. fixe (oracle)",
}
