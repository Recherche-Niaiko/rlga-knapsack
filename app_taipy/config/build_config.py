# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Déclare la configuration Taipy des scénarios puis l'exporte dans config.toml
(fichier ouvrable et modifiable graphiquement dans l'extension VS Code « Taipy Studio »).

Graphe du scénario « comparaison_rlga » :
    parametres ──► [construire_instance] ──► instance ──► [resoudre] ──► resultats, convergence
         └──────────────────────────────────────────────────┘
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from taipy import Config, Scope
import backend

DEFAULT = {"source": "Pisinger (générée)", "classe": "SC", "n": 500, "seed": 0, "fichier": "",
           "methodes": ["GREEDY", "DP", "GA", "GA-RAND", "GA-QL", "GA-QL-T"], "runs": 3,
           "generations": 200, "milp_time": 30}

parametres = Config.configure_data_node("parametres", storage_type="pickle", scope=Scope.SCENARIO, default_data=DEFAULT)
instance = Config.configure_data_node("instance", storage_type="pickle", scope=Scope.SCENARIO)
resultats = Config.configure_data_node("resultats", storage_type="pickle", scope=Scope.SCENARIO)
convergence = Config.configure_data_node("convergence", storage_type="pickle", scope=Scope.SCENARIO)
t_build = Config.configure_task("construire_instance", backend.task_build_instance, input=parametres, output=instance, skippable=True)
t_solve = Config.configure_task("resoudre", backend.task_solve, input=[instance, parametres], output=[resultats, convergence])
scenario_cfg = Config.configure_scenario("comparaison_rlga", task_configs=[t_build, t_solve])

if __name__ == "__main__":
    Config.backup(os.path.join(HERE, "config.toml"))
    print("config.toml écrit")
