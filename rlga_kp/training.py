# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Apprentissage hors ligne d'une Q-table (« méta-apprentissage » de la stratégie de contrôle).

Un seul agent Q-learning pilote successivement l'AG sur un ensemble d'instances d'entraînement
(plusieurs épisodes par instance). La Q-table est conservée d'un épisode à l'autre et
l'exploration ε décroît sur l'ensemble de l'entraînement. La Q-table finale est ensuite
réutilisée telle quelle sur de nouvelles instances (éventuellement hors distribution) :
c'est le contrôleur « GA-QL-T » (transfert).
"""
from __future__ import annotations

import time

import numpy as np

from .controllers import QLearningController
from .ga import GAConfig, GeneticAlgorithm


def train_qtable(train_instances, n_episodes_per_instance=4, cfg: GAConfig | None = None,
                 use_instance_feature=False, alpha=0.1, gamma=0.8, seed=0, log=print):
    cfg = cfg or GAConfig()
    rng = np.random.default_rng(seed)
    order = [inst for _ in range(n_episodes_per_instance) for inst in train_instances]
    rng.shuffle(order)
    total_steps = len(order) * cfg.n_generations
    agent = QLearningController(alpha=alpha, gamma=gamma, use_instance_feature=use_instance_feature,
                                name="QL-train")
    Q = None
    eps = 1.0
    decay = (0.05 / 1.0) ** (1.0 / total_steps)
    history = []
    t0 = time.time()
    for ep, inst in enumerate(order):
        agent.Q0 = Q
        agent.eps_start = eps
        agent.eps_end = 0.05
        ga = GeneticAlgorithm(inst, cfg, agent, seed=int(rng.integers(1 << 31)))
        # on force la décroissance globale (et non par épisode)
        agent_reset = agent.reset

        def reset_with_global_eps(i, G, r, _eps=eps):
            agent_reset(i, G, r)
            agent.eps = _eps
            agent.decay = decay
        agent.reset = reset_with_global_eps
        res = ga.run()
        agent.reset = agent_reset
        Q = agent.Q.copy()
        eps = agent.eps
        history.append({"episode": ep, "instance": inst.name, "class": inst.klass, "n": inst.n,
                        "value": res.value, "eps": eps,
                        "action_hist": np.bincount(res.actions, minlength=Q.shape[1]).tolist()})
        if (ep + 1) % max(1, len(order) // 10) == 0:
            log(f"  entraînement : épisode {ep + 1}/{len(order)}  ε={eps:.3f}  ({time.time() - t0:.0f} s)")
    final = QLearningController(Q=Q, use_instance_feature=use_instance_feature, name="AG + Q-learning (pré-entraîné)")
    final.Q = Q
    return final, history
