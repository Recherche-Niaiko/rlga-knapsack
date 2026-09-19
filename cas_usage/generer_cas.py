# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Génère les jeux de données des cas d'usage de démonstration (données SYNTHÉTIQUES mais
calibrées sur des ordres de grandeur plausibles ; elles ne proviennent d'aucun organisme réel).

  1. budget_communal      — sélection de projets communaux sous budget (KP 0/1)
  2. camion_humanitaire   — chargement d'un camion de secours : poids + volume (MKP, m = 2)
  3. placement_vm_cloud   — admission de machines virtuelles : CPU, RAM, disque (MKP, m = 3)
  4. portefeuille         — sélection d'investissements sous budget, profits corrélés aux coûts (KP 0/1 difficile)
"""
import json
import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)

def save(name, df, meta):
    df.to_csv(f"{name}.csv", index=False)
    with open(f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(name, df.shape)

# 1. Budget communal ----------------------------------------------------------
types = [("École primaire (2 salles)", 180, 60), ("Puits / borne-fontaine", 45, 25), ("Réhabilitation piste rurale (km)", 120, 40),
         ("Centre de santé de base (CSB)", 350, 90), ("Éclairage public solaire", 60, 20), ("Marché couvert", 220, 70),
         ("Latrines publiques", 30, 12), ("Pont / radier", 260, 80), ("Bibliothèque communale", 90, 30),
         ("Adduction d'eau (village)", 150, 50), ("Terrain de sport", 70, 25), ("Digue anti-inondation", 300, 100)]
fokontany = ["Tanambao", "Antarandolo", "Isada", "Andrainjato", "Ambalapaiso", "Mahamanina", "Anjoma", "Ampitakely",
             "Ivory", "Talatamaty", "Ambatomena", "Andohanitralika"]
rows = []
for i in range(120):
    t, c, sd = types[rng.integers(len(types))]
    cost = max(10, rng.normal(c, sd * 0.4))
    benef = int(max(200, rng.normal(c * 18, c * 6)))
    urgence = int(rng.integers(1, 6))
    impact = round(benef * (0.6 + 0.2 * urgence) / 100, 1)
    rows.append({"id": f"P{i+1:03d}", "projet": t, "fokontany": fokontany[rng.integers(len(fokontany))],
                 "coût (M Ar)": round(cost, 1), "bénéficiaires": benef, "urgence (1-5)": urgence,
                 "score d'impact": impact})
df = pd.DataFrame(rows)
save("budget_communal", df, {
    "titre": "Sélection de projets d'investissement communaux sous contrainte budgétaire",
    "description": "Une commune dispose d'un budget annuel d'investissement et doit choisir, parmi 120 projets proposés par les fokontany, ceux qui maximisent l'impact social (bénéficiaires pondérés par l'urgence). Modèle : KP 0/1.",
    "value_column": "score d'impact", "weight_columns": ["coût (M Ar)"], "capacities": [float(round(df["coût (M Ar)"].sum() * 0.3, 1))],
    "unites": ["M Ar"], "label_column": "projet", "donnees": "synthétiques (illustratives)"})

# 2. Camion humanitaire -------------------------------------------------------
lots = [("Sac de riz 50 kg", 50, 0.07, 9), ("Bidon d'eau 20 L", 20, 0.025, 8), ("Kit d'hygiène", 6, 0.03, 6),
        ("Bâche de protection", 8, 0.04, 7), ("Kit médical d'urgence", 12, 0.05, 10), ("Couvertures (lot de 10)", 15, 0.12, 5),
        ("Comprimés de purification (carton)", 10, 0.02, 9), ("Lampe solaire (carton)", 9, 0.04, 4), ("Kit cuisine", 11, 0.06, 5),
        ("Aliment thérapeutique (carton)", 14, 0.03, 10), ("Tente familiale", 35, 0.15, 6), ("Jerrycan pliable (lot)", 7, 0.05, 6)]
rows = []
for i in range(250):
    nom, p, v, prio = lots[rng.integers(len(lots))]
    q = int(rng.integers(1, 6))
    poids = round(p * q * rng.uniform(0.9, 1.1), 1)
    vol = round(v * q * rng.uniform(0.9, 1.15), 3)
    personnes = int(q * rng.integers(3, 12))
    rows.append({"id": f"L{i+1:03d}", "lot": f"{nom} ×{q}", "poids (kg)": poids, "volume (m3)": vol,
                 "personnes aidées": personnes, "priorité (1-10)": prio,
                 "utilité": round(personnes * prio / 10 * rng.uniform(0.85, 1.15), 1)})
df = pd.DataFrame(rows)
save("camion_humanitaire", df, {
    "titre": "Chargement d'un camion de secours après un cyclone (poids et volume)",
    "description": "Un camion de 6 tonnes et 20 m³ doit acheminer, depuis l'entrepôt, les lots de secours maximisant l'utilité humanitaire (personnes aidées × priorité). Deux contraintes de capacité : KP multidimensionnel (m = 2).",
    "value_column": "utilité", "weight_columns": ["poids (kg)", "volume (m3)"], "capacities": [6000.0, 20.0],
    "unites": ["kg", "m³"], "label_column": "lot", "donnees": "synthétiques (illustratives)"})

# 3. Placement de machines virtuelles -------------------------------------------
profils = [("micro", 1, 1, 20), ("small", 2, 4, 40), ("medium", 4, 8, 80), ("large", 8, 16, 160), ("xlarge", 16, 32, 320),
           ("mémoire", 4, 32, 100), ("calcul", 16, 8, 60), ("stockage", 2, 8, 800)]
rows = []
for i in range(300):
    nom, cpu, ram, disk = profils[rng.integers(len(profils))]
    rev = (cpu * 9 + ram * 2.5 + disk * 0.05) * rng.uniform(0.7, 1.4)
    rows.append({"id": f"VM{i+1:03d}", "profil": nom, "vCPU": cpu, "RAM (Go)": ram, "disque (Go)": disk,
                 "revenu mensuel (USD)": round(rev, 2)})
df = pd.DataFrame(rows)
save("placement_vm_cloud", df, {
    "titre": "Admission de machines virtuelles sur un serveur (CPU, RAM, disque)",
    "description": "Un hébergeur doit accepter un sous-ensemble de 300 demandes de machines virtuelles sur une grappe de capacité limitée (256 vCPU, 1 To de RAM, 20 To de disque) afin de maximiser le revenu mensuel. KP multidimensionnel (m = 3).",
    "value_column": "revenu mensuel (USD)", "weight_columns": ["vCPU", "RAM (Go)", "disque (Go)"],
    "capacities": [256.0, 1024.0, 20000.0], "unites": ["vCPU", "Go", "Go"], "label_column": "profil",
    "donnees": "synthétiques (illustratives)"})

# 4. Portefeuille d'investissements (profits fortement corrélés aux coûts) -------
secteurs = ["Agro-industrie (vanille)", "Énergie solaire", "Tourisme", "Textile", "Télécoms", "Transport", "Pêche", "Riziculture", "Mines artisanales", "Éducation privée"]
rows = []
for i in range(400):
    cout = float(rng.integers(10, 1000))
    rend = round(cout * rng.uniform(1.08, 1.12) + 5, 1)       # rendement ≈ proportionnel au coût : instance difficile (type SC)
    rows.append({"id": f"A{i+1:03d}", "secteur": secteurs[rng.integers(len(secteurs))],
                 "investissement (k USD)": cout, "valeur attendue à 3 ans (k USD)": rend})
df = pd.DataFrame(rows)
save("portefeuille", df, {
    "titre": "Sélection d'un portefeuille d'investissements sous budget",
    "description": "Un fonds dispose d'un budget et choisit parmi 400 opportunités ; la valeur attendue est presque proportionnelle au montant investi — structure « fortement corrélée » (Pisinger) qui rend le glouton peu discriminant. KP 0/1 difficile.",
    "value_column": "valeur attendue à 3 ans (k USD)", "weight_columns": ["investissement (k USD)"],
    "capacities": [float(round(df["investissement (k USD)"].sum() * 0.4))], "unites": ["k USD"], "label_column": "secteur",
    "donnees": "synthétiques (illustratives)"})
