# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Analyse des campagnes : tableaux (CSV / Markdown / LaTeX), tests statistiques et figures.

  python experiments/analysis.py            # analyse toutes les campagnes disponibles

Sorties : results/analyse/<campagne>/  (tableaux)  et  results/figures/  (figures PNG + PDF).
Les figures sont numérotées et regroupées pour une intégration directe dans le manuscrit.
"""
from __future__ import annotations

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from rlga_kp.ga import ACTION_LABELS  # noqa: E402

RES = os.path.join(ROOT, "results")
FIG = os.path.join(RES, "figures")
ANA = os.path.join(RES, "analyse")
os.makedirs(FIG, exist_ok=True)
os.makedirs(ANA, exist_ok=True)

# ── identité visuelle : une couleur fixe par méthode (palette de référence validée) ──
LABELS = {
    "GA": "AG standard",
    "GA-RAND": "AG op. aléatoires",
    "GA-UCB": "AG + UCB1",
    "GA-QL": "AG + QL (en ligne)",
    "GA-QL-T": "AG + QL pré-entraîné",
    "GA-QL-Tphi": "AG + QL pré-entraîné + φ(I)",
    "GA-FIX-UX+BF3": "Meilleure config. fixe (oracle)",
    "GREEDY": "Glouton étendu", "DP": "Prog. dynamique", "MILP": "PLNE (HiGHS)",
}
COLORS = {
    "GA-QL-T": "#2a78d6", "GA-RAND": "#eb6834", "GA-QL": "#1baf7a", "GA-UCB": "#eda100",
    "GA-QL-Tphi": "#e87ba4", "GA-FIX-UX+BF3": "#4a3aa7", "GA": "#e34948",
    "GREEDY": "#008300", "DP": "#52514e", "MILP": "#0b0b0b",
}
ORDER = ["GA", "GA-RAND", "GA-UCB", "GA-QL", "GA-QL-T", "GA-QL-Tphi", "GA-FIX-UX+BF3"]
CLASS_ORDER = ["UC", "WC", "SS", "ISC", "SC", "ASC", "LD", "JOOKEN"]

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "font.size": 11, "axes.titlesize": 11.5, "axes.labelsize": 11,
    "xtick.labelsize": 10, "ytick.labelsize": 10.5, "legend.fontsize": 10, "figure.titlesize": 12.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#e4e3df", "grid.linewidth": 0.6, "axes.edgecolor": "#8a8984",
    "axes.labelcolor": "#2b2b29", "xtick.color": "#52514e", "ytick.color": "#52514e",
    "legend.frameon": False, "font.family": "DejaVu Sans",
})


def save(fig, name):
    # Pas de titre interne : la légende (manuscrit, plateforme) décrit la figure (norme des publications).
    if fig._suptitle is not None:
        fig._suptitle.remove()
        fig._suptitle = None
    for ax in fig.axes:
        if ax.get_title(loc="left") and ax.get_title(loc="left") == ax.get_title(loc="left").split("\n(")[0] \
                and len(fig.axes) == 1:
            pass
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print("  figure :", name)


def methods_in(df):
    return [m for m in ORDER if m in set(df["method"])]


# ════════════════════════════════════════════════════════════════════════════
#  Statistiques
# ════════════════════════════════════════════════════════════════════════════

def a12(x, y):
    """A12 de Vargha–Delaney : P(X < Y) + 0.5 P(X = Y) — ici X, Y = écarts (plus petit = mieux).
    A12 > 0.5 ⇒ la méthode X obtient des écarts plus faibles que Y."""
    x, y = np.asarray(x), np.asarray(y)
    gt = (x[:, None] < y[None, :]).sum()
    eq = (x[:, None] == y[None, :]).sum()
    return (gt + 0.5 * eq) / (len(x) * len(y))


def holm(pvals):
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(p) - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj


def pairwise_tests(df, target, others):
    """Comparaison de `target` à chaque autre méthode :
       - Wilcoxon signé apparié sur les écarts moyens par instance (niveau instance), correction de Holm ;
       - bilan victoires / égalités / défaites par instance (Mann-Whitney, α = 0,05) ;
       - A12 moyen."""
    per_inst = df.groupby(["instance", "method"])["gap_pct"].mean().unstack()
    rows = []
    for o in others:
        if o not in per_inst or target not in per_inst:
            continue
        d = per_inst[[target, o]].dropna()
        diff = d[target] - d[o]
        try:
            p = stats.wilcoxon(d[target], d[o], zero_method="zsplit").pvalue if (diff != 0).any() else 1.0
        except ValueError:
            p = 1.0
        w = l = t = 0
        a_list = []
        for inst, g in df.groupby("instance"):
            x = g[g.method == target]["gap_pct"].values
            y = g[g.method == o]["gap_pct"].values
            if len(x) == 0 or len(y) == 0:
                continue
            a_list.append(a12(x, y))
            if np.allclose(x, y) or (np.all(x == x[0]) and np.all(y == x[0])):
                t += 1
                continue
            try:
                pm = stats.mannwhitneyu(x, y, alternative="two-sided").pvalue
            except ValueError:
                pm = 1.0
            if pm < 0.05:
                w += int(np.mean(x) < np.mean(y))
                l += int(np.mean(x) > np.mean(y))
            else:
                t += 1
        rows.append({"comparaison": f"{LABELS[target]} vs {LABELS[o]}", "méthode": o,
                     "écart moyen cible (%)": d[target].mean(), "écart moyen autre (%)": d[o].mean(),
                     "p (Wilcoxon)": p, "A12 moyen": np.mean(a_list), "V/E/D": f"{w}/{t}/{l}",
                     "n instances": len(d)})
    out = pd.DataFrame(rows)
    if len(out):
        out["p Holm"] = holm(out["p (Wilcoxon)"])
        out["significatif (α=0,05)"] = np.where(out["p Holm"] < 0.05, "oui", "non")
    return out


def friedman(df):
    per_inst = df.groupby(["instance", "method"])["gap_pct"].mean().unstack().dropna()
    ms = [m for m in ORDER if m in per_inst.columns]
    per_inst = per_inst[ms]
    ranks = per_inst.rank(axis=1, method="average")
    try:
        stat, p = stats.friedmanchisquare(*[per_inst[m] for m in ms])
    except ValueError:
        stat, p = np.nan, np.nan
    k, N = len(ms), len(per_inst)
    q_alpha = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031, 9: 3.102}.get(k, 3.1)
    cd = q_alpha * np.sqrt(k * (k + 1) / (6 * N))   # différence critique de Nemenyi (α = 0,05)
    return ranks.mean().sort_values(), stat, p, cd, N


# ════════════════════════════════════════════════════════════════════════════
#  Tableaux
# ════════════════════════════════════════════════════════════════════════════

def fmt_table(df, path_base, caption, floatfmt=4):
    df.to_csv(path_base + ".csv")
    with open(path_base + ".md", "w") as f:
        f.write(f"**{caption}**\n\n" + df.to_markdown(floatfmt=f".{floatfmt}f") + "\n")
    with open(path_base + ".tex", "w") as f:
        f.write(df.to_latex(float_format=lambda x: f"{x:.{floatfmt}f}", caption=caption,
                            label="tab:" + os.path.basename(path_base), escape=True))


def summary_tables(name, df, group="class"):
    out = os.path.join(ANA, name)
    os.makedirs(out, exist_ok=True)
    ms = methods_in(df)
    g = df.groupby([group, "method"])
    mean = g["gap_pct"].mean().unstack()[ms]
    std = g["gap_pct"].std().unstack()[ms]
    hit = (g["optimal_hit"].mean().unstack()[ms] * 100)
    mean.loc["Moyenne"] = df.groupby("method")["gap_pct"].mean()[ms]
    hit.loc["Moyenne"] = df.groupby("method")["optimal_hit"].mean()[ms] * 100
    ren = {m: LABELS[m] for m in ms}
    fmt_table(mean.rename(columns=ren), os.path.join(out, "ecart_moyen"), f"Écart moyen à la référence (%) — {name}")
    fmt_table(std.rename(columns=ren), os.path.join(out, "ecart_ecart_type"), f"Écart-type de l'écart (%) — {name}")
    fmt_table(hit.rename(columns=ren), os.path.join(out, "taux_optimum"), f"Taux d'atteinte de la référence (%) — {name}", 1)
    t = df.groupby("method")["time"].mean()[ms].to_frame("temps moyen (s)").rename(index=ren)
    fmt_table(t, os.path.join(out, "temps"), f"Temps moyen par exécution (s) — {name}", 2)
    tests = []
    for target in ("GA-QL-T", "GA-QL"):
        if target in ms:
            tests.append(pairwise_tests(df, target, [m for m in ms if m != target]))
    if tests:
        tt = pd.concat(tests)
        tt.to_csv(os.path.join(out, "tests_statistiques.csv"), index=False)
        with open(os.path.join(out, "tests_statistiques.md"), "w") as f:
            f.write(f"**Tests statistiques — {name}**\n\n" + tt.to_markdown(index=False, floatfmt=".4g") + "\n")
        with open(os.path.join(out, "tests_statistiques.tex"), "w") as f:
            f.write(tt.drop(columns=["méthode"]).to_latex(index=False, float_format=lambda x: f"{x:.3g}",
                                                          caption=f"Tests statistiques — {name}",
                                                          label=f"tab:tests-{name}"))
    ranks, st, p, cd, N = friedman(df)
    fr = pd.DataFrame({"rang moyen": ranks}).rename(index=ren)
    fmt_table(fr, os.path.join(out, "friedman_rangs"),
              f"Rangs moyens (Friedman χ²={st:.2f}, p={p:.2e}, N={N}, CD Nemenyi={cd:.2f}) — {name}", 2)
    with open(os.path.join(out, "friedman.json"), "w") as f:
        json.dump({"chi2": st, "p": p, "cd": cd, "N": N, "ranks": ranks.to_dict()}, f, indent=1)
    return mean, ranks, cd, p


# ════════════════════════════════════════════════════════════════════════════
#  Figures
# ════════════════════════════════════════════════════════════════════════════

def fig_dot_by_class(df, name, title, fig_id, classes=None):
    """Graphique en points (Cleveland) : écart moyen par classe × méthode (petits multiples, 2 colonnes)."""
    ms = methods_in(df)
    classes = classes or [c for c in CLASS_ORDER if c in set(df["class"])] + \
        sorted(c for c in set(df["class"]) if c not in CLASS_ORDER)
    ncol = 2 if len(classes) > 1 else 1
    nrow = int(np.ceil(len(classes) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(8.2, 0.36 * len(ms) * nrow + 0.55 * nrow + 0.8),
                             squeeze=False, gridspec_kw={"wspace": 0.16, "hspace": 0.45})
    for k, (ax, c) in enumerate(zip(axes.flat, classes)):
        sub = df[df["class"] == c]
        mean = sub.groupby("method")["gap_pct"].mean()
        se = sub.groupby("method")["gap_pct"].std() / np.sqrt(sub.groupby("method").size())
        for y, m in enumerate(ms):
            if m in mean:
                ax.errorbar(mean[m], y, xerr=1.96 * se[m], fmt="o", color=COLORS[m], ms=7,
                            ecolor=COLORS[m], elinewidth=1.6, capsize=0)
        ax.set_yticks(range(len(ms)))
        ax.set_yticklabels([LABELS[m] for m in ms] if k % ncol == 0 else [])
        ax.invert_yaxis()
        ax.set_title(f"classe {c}" if len(c) <= 4 else c, fontweight="bold")
        ax.set_xlim(left=0)
        ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))
        if k >= len(classes) - ncol:
            ax.set_xlabel("écart moyen à l'optimum (%)")
    for ax in list(axes.flat)[len(classes):]:
        ax.axis("off")
    fig.suptitle(title, x=0.01, ha="left")
    save(fig, fig_id)


def fig_boxplots(df, name, title, fig_id, classes):
    ms = methods_in(df)
    ncol = 2
    nrow = int(np.ceil(len(classes) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(8.2, 3.9 * nrow), squeeze=False,
                             gridspec_kw={"hspace": 0.75, "wspace": 0.25})
    for k, (ax, c) in enumerate(zip(axes.flat, classes)):
        sub = df[df["class"] == c]
        data = [sub[sub.method == m]["gap_pct"].values for m in ms]
        bp = ax.boxplot(data, patch_artist=True, widths=0.6, showfliers=True,
                        medianprops={"color": "#0b0b0b", "linewidth": 1.4},
                        flierprops={"marker": "o", "markersize": 3, "markerfacecolor": "#8a8984",
                                    "markeredgecolor": "none"})
        for patch, m in zip(bp["boxes"], ms):
            patch.set_facecolor(COLORS[m]); patch.set_alpha(0.85); patch.set_edgecolor("white")
        ax.set_xticks(range(1, len(ms) + 1))
        ax.set_xticklabels([LABELS[m] for m in ms], rotation=40, ha="right")
        ax.set_title(f"classe {c}" if len(c) <= 4 else c, fontweight="bold")
        ax.set_ylabel("écart à l'optimum (%)" if k % ncol == 0 else "")
    for ax in list(axes.flat)[len(classes):]:
        ax.axis("off")
    fig.suptitle(title, x=0.01, ha="left")
    save(fig, fig_id)


def load_curves(name):
    z = np.load(os.path.join(RES, name, "curves.npz"), allow_pickle=True)
    keys = [k.split("||") for k in z["keys"]]
    return keys, z["best_mean"], z["div_mean"], z["phase_freq"]


def _pretty_instance(inst):
    s = inst.replace("_R1000", "").replace("_s0", "").replace("_n", ", n = ")
    if inst.startswith("n_"):
        p = inst.split("_")
        s = f"Jooken, n = {p[1]}, C = {float(p[3]):.0e}"
    if inst.startswith("knapPI_"):
        p = inst.split("_")
        s = f"Pisinger classe {p[1]}, n = {p[2]}"
    return s


def fig_convergence(name, df, instances, fig_id, title):
    """Deux figures : convergence du meilleur (fig_id) et diversité génotypique (fig_id → _diversite)."""
    keys, best, div, _ = load_curves(name)
    ref = df.groupby("instance")["reference"].first()
    ncol = 2
    nrow = int(np.ceil(len(instances) / ncol))
    for what, suffix, ylab in (("best", "", "écart du meilleur (%)"), ("div", "_diversite", "diversité D")):
        fig, axes = plt.subplots(nrow, ncol, figsize=(8.2, 3.1 * nrow + 1.0), squeeze=False, sharex=True,
                                 gridspec_kw={"hspace": 0.35, "wspace": 0.25})
        for k, (ax, inst) in enumerate(zip(axes.flat, instances)):
            for m in methods_in(df):
                idx = [i for i, (a, b) in enumerate(keys) if a == inst and b == m]
                if not idx:
                    continue
                y = 100 * (ref[inst] - best[idx[0]]) / ref[inst] if what == "best" else div[idx[0]]
                ax.plot(np.arange(1, len(y) + 1), y, color=COLORS[m], lw=2.2, label=LABELS[m])
            if what == "best":
                ax.set_yscale("symlog", linthresh=0.01)
                ax.set_ylim(bottom=0)
            ax.set_title(_pretty_instance(inst), fontweight="bold")
            if k % ncol == 0:
                ax.set_ylabel(ylab)
            if k >= len(instances) - ncol:
                ax.set_xlabel("génération")
        for ax in list(axes.flat)[len(instances):]:
            ax.axis("off")
        h, l = axes[0, 0].get_legend_handles_labels()
        fig.legend(h, l, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.02 - 0.03 * (len(l) > 6)))
        fig.subplots_adjust(bottom=0.2 if nrow == 1 else 0.14)
        t = title if what == "best" else title.replace("convergence du meilleur individu", "diversité génotypique de la population")
        fig.suptitle(t, x=0.01, ha="left")
        save(fig, fig_id + suffix)


def fig_ranks(ranks, cd, p, fig_id, title):
    fig, ax = plt.subplots(figsize=(8.2, 0.5 * len(ranks) + 1.6))
    ms = list(ranks.index)
    for y, m in enumerate(ms):
        ax.plot([ranks[m]], [y], "o", color=COLORS[m], ms=10, zorder=3)
        ax.text(ranks[m] + 0.08, y, f"{ranks[m]:.2f}", va="center", fontsize=10.5, color="#2b2b29")
    best = ranks.iloc[0]
    ax.axvspan(best, best + cd, color="#cde2fb", alpha=0.6, lw=0,
               label=f"différence critique de Nemenyi (CD = {cd:.2f}) ; test de Friedman : p = {p:.2e}")
    ax.set_yticks(range(len(ms)))
    ax.set_yticklabels([LABELS[m] for m in ms])
    ax.invert_yaxis()
    ax.set_xlim(right=max(ranks.max() + 0.5, best + cd + 0.2))
    ax.set_xlabel("rang moyen (1 = meilleur)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.25), fontsize=10, frameon=False)
    fig.tight_layout()
    save(fig, fig_id)


def fig_policy(name, df, fig_id, title, methods=("GA-QL", "GA-QL-T"), classes=("UC", "SC")):
    """Fréquence d'utilisation des 9 actions par phase de la recherche."""
    keys, _, _, phase = load_curves(name)
    cls = df.groupby("instance")["class"].first()
    methods = [m for m in methods if m in set(df.method)]
    classes = [c for c in classes if c in set(df["class"])]
    fig, axes = plt.subplots(len(methods), len(classes), figsize=(2.9 * len(classes) + 1.2, 2.3 * len(methods) + 1.4),
                             squeeze=False, gridspec_kw={"hspace": 0.4, "wspace": 0.06})
    for i, m in enumerate(methods):
        for j, c in enumerate(classes):
            idx = [k for k, (a, b) in enumerate(keys) if b == m and cls.get(a) == c]
            if not idx:
                continue
            mat = phase[idx].mean(axis=0) * 100      # (3 phases, 9 actions)
            ax = axes[i, j]
            im = ax.imshow(mat, cmap="Blues", vmin=0, vmax=max(40, mat.max()), aspect="auto")
            for (r, q), v in np.ndenumerate(mat):
                ax.text(q, r, f"{v:.0f}", ha="center", va="center", fontsize=9,
                        color="white" if v > 25 else "#2b2b29")
            ax.set_yticks(range(3)); ax.set_yticklabels(["début", "milieu", "fin"])
            ax.set_xticks(range(9))
            ax.set_xticklabels(ACTION_LABELS if i == len(methods) - 1 else [], rotation=60, ha="right", fontsize=9)
            if j > 0:
                ax.set_yticklabels([])
            court = {"GA-QL": "QL en ligne", "GA-QL-T": "QL pré-entraîné", "GA-UCB": "UCB1"}.get(m, LABELS[m])
            ax.set_title(f"{court} · {c}", fontsize=10.5, fontweight="bold")
            ax.grid(False)
    fig.colorbar(im, ax=axes, shrink=0.8, label="% des générations")
    fig.suptitle(title, x=0.01, ha="left", fontsize=11)
    save(fig, fig_id)


def fig_qtable(path, fig_id, title):
    with open(path) as f:
        Q = np.array(json.load(f)["Q"])
    Q = Q[:27]
    div = ["D faible", "D moy.", "D élevée"]
    stg = ["stag. 0-2", "stag. 3-14", "stag. ≥15"]
    prg = ["début", "milieu", "fin"]
    labels = [f"{d} | {s} | {p}" for d in div for s in stg for p in prg]
    fig, ax = plt.subplots(figsize=(8.2, 9.5))
    # normalisation par ligne (état) : (Q - min) / (max - min) → préférences relatives entre actions
    rng_ = Q.max(axis=1, keepdims=True) - Q.min(axis=1, keepdims=True)
    Qn = np.where(rng_ > 0, (Q - Q.min(axis=1, keepdims=True)) / np.where(rng_ > 0, rng_, 1), 0)
    im = ax.imshow(Qn, cmap="Blues", aspect="auto", vmin=0, vmax=1)
    best = Q.argmax(axis=1)
    for r in range(27):
        if np.abs(Q[r]).sum() > 0:
            ax.add_patch(plt.Rectangle((best[r] - 0.5, r - 0.5), 1, 1, fill=False, ec="#eb6834", lw=1.8))
    ax.set_yticks(range(27)); ax.set_yticklabels(labels, fontsize=9)
    ax.set_xticks(range(9)); ax.set_xticklabels(ACTION_LABELS, rotation=45, ha="right", fontsize=10)
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.6, label="Q(s, a) normalisé par état")
    ax.set_title("cadre orange : action préférée ; ligne vide : état jamais visité", loc="left",
                 fontsize=9.5)
    fig.tight_layout()
    save(fig, fig_id)


def fig_success_failure(df, fig_id, title, pairs):
    """Différence d'écart moyen par instance (négatif = la 1re méthode gagne) — succès et échecs."""
    per = df.groupby(["class", "instance", "method"])["gap_pct"].mean().unstack()
    pairs = [(a, b) for a, b in pairs if a in per and b in per]
    fig, axes = plt.subplots(len(pairs), 1, figsize=(8.2, 3.0 * len(pairs) + 0.6), squeeze=False,
                             gridspec_kw={"hspace": 0.55})
    for ax, (a, b) in zip(axes[:, 0], pairs):
        d = (per[a] - per[b]).reset_index()
        d.columns = ["class", "instance", "diff"]
        d = d.sort_values(["class", "diff"])
        cols = np.where(d["diff"] < -1e-9, "#2a78d6", np.where(d["diff"] > 1e-9, "#e34948", "#b5b3ad"))
        ax.bar(range(len(d)), d["diff"], color=cols, width=0.85)
        ax.axhline(0, color="#52514e", lw=0.8)
        cls_list = list(d["class"])
        centers, names, start = [], [], 0
        for i in range(1, len(cls_list) + 1):
            if i == len(cls_list) or cls_list[i] != cls_list[start]:
                centers.append((start + i - 1) / 2); names.append(cls_list[start])
                if i < len(cls_list):
                    ax.axvline(i - 0.5, color="#d6d4cf", lw=0.8)
                start = i
        ax.set_xticks(centers)
        ax.set_xticklabels(names)
        ax.set_ylabel("Δ écart (points de %)")
        n_w, n_l = (d["diff"] < -1e-9).sum(), (d["diff"] > 1e-9).sum()
        ax.set_title(f"{LABELS[a]} vs {LABELS[b]} : {n_w} gains, {n_l} pertes", loc="left",
                     fontweight="bold", fontsize=10.5)
        ax.grid(axis="x", visible=False)
    fig.suptitle(title, x=0.01, ha="left")
    save(fig, fig_id)


def fig_exact_vs_meta(ref, df, fig_id, title):
    """Qualité vs temps : méthodes exactes, glouton et variantes d'AG (moyennes par instance)."""
    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    refv = df.groupby("instance")["reference"].first()
    pts = []
    for m in methods_in(df):
        s = df[df.method == m]
        pts.append((m, s["time"].mean(), s["gap_pct"].mean()))
    r = ref.set_index("instance")
    gg = (100 * (refv - r.loc[refv.index, "greedy"]) / refv).mean()
    pts.append(("GREEDY", r["t_greedy"].mean(), gg))
    if "t_dp" in r and r["t_dp"].notna().any():
        ok = r["dp"].notna()
        pts.append(("DP", r.loc[ok, "t_dp"].mean(), 0.0))
    if "t_milp" in r:
        gm = (100 * (refv - r.loc[refv.index, "milp"]) / refv).mean()
        pts.append(("MILP", r["t_milp"].mean(), gm))
    markers = {"GREEDY": "s", "DP": "D", "MILP": "D"}
    for m, t, g in pts:
        lab = LABELS[m] + (" (instances où elle est faisable)" if m == "DP" else "")
        ax.scatter(t, g, s=80, color=COLORS[m], marker=markers.get(m, "o"), edgecolor="white", linewidth=1.5,
                   zorder=3, label=lab)
    ax.set_xscale("log")
    ax.set_yscale("symlog", linthresh=0.01)
    ax.set_ylim(bottom=0, top=max(g for _, _, g in pts) * 2.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, fontsize=9.5, frameon=False)
    ax.set_xlabel("temps moyen par instance ou par exécution (s, échelle log)")
    ax.set_ylabel("écart moyen à l'optimum (%)")
    fig.tight_layout()
    save(fig, fig_id)


def fig_scalability(fig_id):
    p = os.path.join(RES, "e5_scalabilite", "scalability.csv")
    if not os.path.exists(p):
        return
    d = pd.read_csv(p)
    best = d.groupby(["class", "n", "seed"])["value"].transform("max")
    d["gap_pct"] = 100 * (best - d["value"]) / best
    fig, axes = plt.subplots(2, 2, figsize=(8.2, 7.2), sharex=True)
    for j, c in enumerate(["UC", "SC"]):
        for m in ["DP", "MILP", "GREEDY", "GA", "GA-QL-T"]:
            s = d[(d["class"] == c) & (d.method == m)].groupby("n")[["time", "gap_pct"]].mean()
            if len(s) == 0:
                continue
            axes[0, j].plot(s.index, s["time"], "o-", color=COLORS[m], lw=2, ms=6, label=LABELS[m])
            axes[1, j].plot(s.index, s["gap_pct"], "o-", color=COLORS[m], lw=2, ms=6)
        axes[0, j].set_xscale("log"); axes[0, j].set_yscale("log")
        axes[0, j].set_title(f"classe {c}")
        axes[1, j].set_yscale("symlog", linthresh=0.001)
        axes[1, j].set_ylim(bottom=0)
        axes[1, j].set_xlabel("nombre d'objets n (échelle log)")
    axes[0, 0].set_ylabel("temps (s, log)")
    axes[1, 0].set_ylabel("écart au meilleur (%)")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.08))
    fig.suptitle("Passage à l'échelle : temps et qualité selon la taille (C ≈ n·R/4)", x=0.01, ha="left")
    fig.tight_layout()
    save(fig, fig_id)


def fig_training(fig_id):
    p = os.path.join(RES, "qtables", "Q_OOD_history.csv")
    if not os.path.exists(p):
        return
    h = pd.read_csv(p)
    acts = np.array([json.loads(a) if isinstance(a, str) else a for a in h["action_hist"]], dtype=float)
    acts = acts / acts.sum(axis=1, keepdims=True)
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.6))
    axes[0].plot(h["episode"], h["eps"], color="#52514e", lw=2)
    axes[0].set_xlabel("épisode d'entraînement"); axes[0].set_ylabel("ε (exploration)")
    axes[0].set_title("Décroissance de l'exploration", loc="left")
    win = 8
    for k, lab in enumerate(ACTION_LABELS):
        sm = pd.Series(acts[:, k]).rolling(win, min_periods=1).mean() * 100
        if lab in ("UX+BF3", "1P+BF1", "UX+SWAP", "2P+BF3"):
            col = {"UX+BF3": "#2a78d6", "1P+BF1": "#e34948", "UX+SWAP": "#1baf7a", "2P+BF3": "#eda100"}[lab]
            axes[1].plot(h["episode"], sm, color=col, lw=2, label=lab)
        else:
            axes[1].plot(h["episode"], sm, color="#c9c8c3", lw=1)
    axes[1].set_xlabel("épisode d'entraînement"); axes[1].set_ylabel("% des générations")
    axes[1].set_title("Part de chaque action\n(moyenne glissante ; gris : autres)", loc="left")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    save(fig, fig_id)


# ════════════════════════════════════════════════════════════════════════════

def analyse(name, title, fig_prefix, conv_instances=None, box_classes=None, group="class"):
    p = os.path.join(RES, name, "runs_gap.csv")
    if not os.path.exists(p):
        print("absent :", name)
        return None
    print("Analyse", name)
    df = pd.read_csv(p)
    ref = pd.read_csv(os.path.join(RES, name, "references.csv"))
    mean, ranks, cd, pf = summary_tables(name, df, group)
    fig_dot_by_class(df, name, f"{title} — écart moyen à l'optimum (IC 95 %)", f"{fig_prefix}_ecart_par_classe")
    fig_ranks(ranks, cd, pf, f"{fig_prefix}_rangs_friedman", f"{title} — rangs moyens")
    if box_classes:
        fig_boxplots(df, name, f"{title} — distribution des écarts (10 exécutions × instances)",
                     f"{fig_prefix}_boites", [c for c in box_classes if c in set(df["class"])])
    if conv_instances:
        insts = [i for i in conv_instances if i in set(df.instance)]
        if insts:
            fig_convergence(name, df, insts, f"{fig_prefix}_convergence", f"{title} — convergence du meilleur individu")
    fig_success_failure(df, f"{fig_prefix}_succes_echecs", f"{title} — succès et échecs par instance",
                        [("GA-QL-T", "GA"), ("GA-QL", "GA-RAND"), ("GA-QL-T", "GA-FIX-UX+BF3")])
    fig_exact_vs_meta(ref, df, f"{fig_prefix}_qualite_temps", f"{title} — compromis qualité / temps")
    return df


if __name__ == "__main__":
    only = sys.argv[1:]
    runs = {
        "exp0_pilot": dict(title="Pilote (calibration)", fig_prefix="fig00_pilote"),
        "e1_kp01_generes": dict(title="E1 · KP 0/1 générés (Pisinger)", fig_prefix="fig01_e1",
                                conv_instances=["UC_n1000_R1000_s0", "SC_n1000_R1000_s0", "ASC_n1000_R1000_s0",
                                                "ISC_n1000_R1000_s0"],
                                box_classes=["SC", "ASC", "ISC", "UC"]),
        "e2_kp01_benchmarks": dict(title="E2 · KP 0/1 de référence (Pisinger, Jooken)", fig_prefix="fig02_e2",
                                   conv_instances=["knapPI_3_1000_1000_1", "knapPI_1_2000_1000_1",
                                                   "n_1000_c_100000000_g_10_f_0.3_eps_0.01_s_100"],
                                   box_classes=["UC", "WC", "SC", "JOOKEN"]),
        "e3_mkp": dict(title="E3 · Sac à dos multidimensionnel (OR-Library)", fig_prefix="fig03_e3",
                       box_classes=["MKP-OR5x100", "MKP-OR10x100", "MKP-OR5x250", "MKP-weing"]),
    }
    for k, kw in runs.items():
        if only and k not in only:
            continue
        df = analyse(k, **kw)
        if df is not None and k == "e1_kp01_generes":
            fig_policy(k, df, "fig04_politique_actions",
                       "Politique apprise : fréquence des actions par phase (E1)",
                       methods=("GA-QL", "GA-QL-T", "GA-UCB"), classes=("UC", "SC", "ASC"))
    for qt, fid in (("Q_OOD", "fig05_qtable_Q_OOD"), ("Q_ALL_phi", "fig05b_qtable_Q_ALL_phi")):
        p = os.path.join(RES, "qtables", f"{qt}.json")
        if os.path.exists(p) and (not only or "qtables" in only):
            fig_qtable(p, fid, f"Q-table pré-entraînée {qt} (27 premiers états)")
    if not only or "qtables" in only:
        fig_training("fig06_entrainement_Q_OOD")
    if not only or "e5" in only:
        fig_scalability("fig07_scalabilite")
