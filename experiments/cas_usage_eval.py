# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""Évalue les méthodes sur les 4 cas d'usage → cas_usage/resultats_cas_usage.csv (+ .md)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "app_taipy"))
import pandas as pd
import backend as B
rows = []
for case in B.list_files("Cas d'usage réel"):
    inst, df, meta = B.load_use_case(case)
    res, _, _ = B.compare(inst, ["GREEDY", "DP", "MILP", "GA", "GA-RAND", "GA-QL", "GA-QL-T"], runs=5,
                          generations=200, milp_time=60)
    for _, r in res.iterrows():
        rows.append({"cas": case, "modèle": "MKP" if inst.m > 1 else "KP", "n": inst.n, "m": inst.m,
                     "méthode": r["méthode"], "valeur moyenne": r["valeur moyenne"], "meilleure": r["meilleure valeur"],
                     "écart moyen (%)": r["écart moyen (%)"], "temps moyen (s)": r["temps moyen (s)"], "statut": r["statut"]})
    print(case, "ok", flush=True)
out = pd.DataFrame(rows)
out.to_csv(os.path.join(ROOT, "cas_usage", "resultats_cas_usage.csv"), index=False)
with open(os.path.join(ROOT, "cas_usage", "resultats_cas_usage.md"), "w") as f:
    f.write(out.round(4).to_markdown(index=False))
print(out.round(4).to_string())
