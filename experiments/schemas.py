# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""Schémas explicatifs (boucle AR ↔ AG, architecture logicielle) → results/figures/."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "figures")
os.makedirs(OUT, exist_ok=True)
INK, MUTED = "#2b2b29", "#52514e"

def box(ax, x, y, w, h, title, body="", fc="#eef4fc", ec="#2a78d6"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03", fc=fc, ec=ec, lw=1.6))
    ax.text(x + w / 2, y + h - 0.1, title, ha="center", va="top", fontsize=10.5, fontweight="bold", color=INK)
    if body:
        ax.text(x + w / 2, y + h - 0.45, body, ha="center", va="top", fontsize=8.3, color=MUTED, linespacing=1.35)

def arrow(ax, p, q, text="", rad=0.0, dy=0.03):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, lw=1.6, color=MUTED,
                                 connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + dy, text, ha="center", fontsize=8.5, color=INK,
                bbox=dict(fc="white", ec="none", pad=1.5))

# 1. boucle AR ↔ AG ----------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.2)); ax.set_xlim(0, 10); ax.set_ylim(0, 5.2); ax.axis("off")
box(ax, 0.3, 2.9, 3.4, 1.9, "Agent Q-learning",
    "Q-table 27 états × 9 actions\npolitique ε-gloutonne\nQ ← Q + α[r + γ max Q' − Q]")
box(ax, 6.2, 2.9, 3.5, 1.9, "Algorithme génétique", "population P = 100 (x ∈ {0,1}ⁿ)\nsélection par tournoi\nréparation gloutonne + élitisme",
    fc="#fdf1ec", ec="#eb6834")
box(ax, 3.3, 0.25, 3.4, 1.75, "Observation de la population",
    "diversité D = moy. 4pᵢ(1−pᵢ)\nstagnation du meilleur\navancement t / G", fc="#eaf7f1", ec="#1baf7a")
arrow(ax, (3.75, 4.25), (6.15, 4.25), "action aₜ = (croisement, mutation)\n{1P, 2P, UX} × {BF1, BF3, SWAP}", dy=0.12)
arrow(ax, (7.9, 2.85), (6.1, 1.4), "génération t+1", rad=-0.15)
arrow(ax, (3.3, 1.2), (2.0, 2.85), "état sₜ₊₁", rad=-0.15)
arrow(ax, (6.2, 3.25), (3.75, 3.25), "récompense rₜ = 100·Δf*/f*", dy=-0.22)
ax.set_title("Pilotage de l'AG par apprentissage par renforcement (une génération = un pas de décision)",
             loc="left", fontsize=11, color=INK)
fig.savefig(os.path.join(OUT, "fig08_boucle_rl_ag.png"), dpi=200, bbox_inches="tight")
fig.savefig(os.path.join(OUT, "fig08_boucle_rl_ag.pdf"), bbox_inches="tight"); plt.close(fig)

# 2. L'architecture technique est désormais un schéma Mermaid (04_MANUSCRIT/schemas/d15_architecture_technique.mmd).
print("ok")
