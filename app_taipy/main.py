# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Application web « RL-in-GA : apprentissage par renforcement dans l'algorithme génétique
pour le problème du sac à dos » (bibliothèque Taipy, non mentionnée dans l'interface).

Lancement local :   ./app_taipy/run_app.sh          (http://127.0.0.1:5000)
Déploiement     :   voir DEPLOIEMENT.md (image Docker sur Render ; page vitrine statique sur Hugging Face)

Pages : Accueil · Instance · Comparaison · Politique apprise · Résultats · Cas d'usage ·
        Scénarios · À propos
"""
from __future__ import annotations

import os
import sys

APP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP)
os.environ.setdefault("TZ", "Indian/Antananarivo")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import taipy as tp  # noqa: E402
from taipy import Config  # noqa: E402
from taipy.gui import Gui, Markdown, get_state_id, invoke_long_callback, navigate, notify  # noqa: E402

import backend as B  # noqa: E402
import ressources as RS  # noqa: E402
from contenus import CAMPAGNES, CLASSES_TXT, FIGURES  # noqa: E402

Config.load(os.path.join(APP, "config", "config.toml"))
SCENARIO_CFG = Config.scenarios["comparaison_rlga"]

ROOT = os.path.dirname(APP)
FIG_DIR = os.path.join(B.RESULTS, "figures")
DOCS = os.path.join(ROOT, "docs")
GITHUB_URL = os.environ.get("RLGA_GITHUB_URL", "https://github.com/Recherche-Niaiko/rlga-knapsack")
_vf = os.path.join(ROOT, "VERSION")
VERSION = "dev"
if os.path.exists(_vf):
    with open(_vf) as _f:
        VERSION = _f.read().strip()
# Lignes contenant le lien cliquable vers le code (texte en mode Markdown, en un seul paragraphe)
PIED_TXT = (f"RALAIVAO Niaiko Michaël — École Nationale d'Informatique, Université de Fianarantsoa — Laboratoire LIMAD, "
            f"équipe GLoRIA — version {VERSION} — code source : [{GITHUB_URL}]({GITHUB_URL})")
CODE_TXT = f"Code, données et résultats : [{GITHUB_URL}]({GITHUB_URL}) — version déployée : {VERSION}."

COLORS = {"GA-QL-T": "#2a78d6", "GA-RAND": "#eb6834", "GA-QL": "#1baf7a", "GA-UCB": "#eda100",
          "GA": "#e34948", "GREEDY": "#008300", "DP": "#6b6a66", "MILP": "#8a8984"}
LABEL2KEY = {v: k for k, v in B.METHODS.items()}
GRID = "rgba(128,128,128,0.22)"
FONT = "Montserrat, sans-serif"


def fr(x: float, nd: int = 4) -> str:
    """Nombre au format français (virgule décimale, espace des milliers)."""
    if x is None or pd.isna(x):
        return "—"
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",")


def neutral_layout(fig: go.Figure, height: int = 420, **kw) -> go.Figure:
    """Mise en forme lisible en thème clair comme en thème sombre (fonds transparents, gris neutres)."""
    base = dict(height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8c8b87", size=14, family=FONT), margin=dict(l=60, r=20, t=30, b=50),
                separators=", ")
    base.update(kw)
    fig.update_layout(**base)
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


# ════════════════════════════════════════════════════════════════════════════
#  Navigation (barre horizontale ; tiroir sur mobile)
# ════════════════════════════════════════════════════════════════════════════
PAGES = [("accueil", "Accueil"), ("instance", "Instance"), ("comparaison", "Comparaison"),
         ("politique", "Politique apprise"), ("resultats", "Résultats"), ("cas_usage", "Cas d'usage"),
         ("hypotheses", "Hypothèses"), ("scenarios", "Scénarios"), ("a_propos", "À propos")]
nav_lov = [(f"/{pid}", label) for pid, label in PAGES]


def go_instance(state):
    navigate(state, "instance")


def go_comparaison(state):
    navigate(state, "comparaison")


def go_politique(state):
    navigate(state, "politique")


def go_resultats(state):
    navigate(state, "resultats")


def go_cas(state):
    navigate(state, "cas_usage")


def go_hypotheses(state):
    navigate(state, "hypotheses")


def go_scenarios(state):
    navigate(state, "scenarios")


# ════════════════════════════════════════════════════════════════════════════
#  Surlignage de la meilleure valeur (tableaux)
# ════════════════════════════════════════════════════════════════════════════
# Colonnes numériques : sens de l'optimisation (« max » : plus grand = meilleur) et nombre de décimales.
# Les tableaux sont affichés au format français (chaînes) ; la meilleure valeur est comparée après arrondi,
# si bien que les ex æquo sont tous surlignés.
BEST_SENSE = {"valeur moyenne": ("max", 2), "meilleure valeur": ("max", 2), "écart moyen (%)": ("min", 4),
              "temps moyen (s)": ("min", 3), "écart (%)": ("min", 4), "meilleur écart (%)": ("min", 4)}
EXTRA_NUM = {"écart-type (%)": 4, "écart cible (%)": 4, "écart autre (%)": 4, "p (Wilcoxon, unilatéral)": 4,
             "temps PLNE (s)": 3, "temps AG (s)": 3}


def format_table(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Formate les colonnes numériques en français et renvoie la meilleure valeur (formatée) par colonne."""
    out, best = df.copy(), {}
    for col, (sense, nd) in BEST_SENSE.items():
        if col not in out.columns:
            continue
        s = pd.to_numeric(out[col], errors="coerce")
        if s.notna().any():
            best[col] = fr(float(s.max() if sense == "max" else s.min()), nd)
        out[col] = s.map(lambda v, nd=nd: fr(v, nd))
    for col, nd in EXTRA_NUM.items():
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").map(lambda v, nd=nd: fr(v, nd))
    if "exécutions" in out.columns:
        out["exécutions"] = out["exécutions"].astype(str)
    return out, best


def _to_float(v):
    try:
        return float(str(v).replace("\u202f", "").replace(" ", "").replace(",", "."))
    except ValueError:
        return None


def _is_best(value, ref) -> bool:
    return ref is not None and value == ref


def cell_best_res(state, value, index, row, column_name):
    return "cell-best" if _is_best(value, state.res_best.get(column_name)) else ""


def cell_best_case(state, value, index, row, column_name):
    return "cell-best" if _is_best(value, state.case_best.get(column_name)) else ""


def cell_best_scen(state, value, index, row, column_name):
    return "cell-best" if _is_best(value, state.scen_best.get(column_name)) else ""


def cell_best_row(state, value, index, row, column_name):
    """Tableaux des campagnes : une ligne = une classe ; la meilleure méthode a l'écart le plus faible."""
    vals = [_to_float(v) for k, v in dict(row).items() if k in _camp_cols]  # colonnes affichées seulement
    vals = [v for v in vals if v is not None and not np.isnan(v)]
    x = _to_float(value)
    return "cell-best" if vals and x is not None and abs(x - min(vals)) < 1e-12 else ""


def _props(fn, cols) -> dict:
    return {f"cell_class_name[{c}]": fn for c in cols}


RES_NUM = ["valeur moyenne", "meilleure valeur", "écart moyen (%)", "temps moyen (s)"]
res_props = _props(cell_best_res, RES_NUM)
case_props = _props(cell_best_case, ["meilleure valeur", "écart moyen (%)", "temps moyen (s)"])
scen_props = _props(cell_best_scen, RES_NUM)


def camp_frame(campaign_id: str, table: str = "ecart_moyen") -> pd.DataFrame:
    """Tableau d'une campagne, nombres au format français (4 décimales)."""
    df = B.load_campaign_table(campaign_id, table)
    for c in df.columns:
        if pd.api.types.is_float_dtype(df[c]):
            df[c] = df[c].map(lambda v: fr(v, 4))
    return df


_camp_cols = sorted({c for k in CAMPAGNES for c in B.load_campaign_table(CAMPAGNES[k]["id"]).columns} - {
    "classe / méthode", "info", "n"})
camp_props = _props(cell_best_row, _camp_cols)


# ════════════════════════════════════════════════════════════════════════════
#  État initial
# ════════════════════════════════════════════════════════════════════════════
source = B.SOURCES[0]
sources = B.SOURCES
classe = "SC"
classes = B.CLASSES
classe_txt = CLASSES_TXT[classe]
n_items = int(os.environ.get("RLGA_N_DEFAUT", 500))      # réglages initiaux (plus légers sur un petit hébergeur)
seed = 0
fichiers = B.list_files("Benchmark instances_01_KP")
fichier = fichiers[0] if fichiers else ""

inst = B.build_instance({"source": source, "classe": classe, "n": n_items, "seed": seed})
inst_desc = B.describe(inst)
inst_items = B.items_frame(inst)
inst_n, inst_m = inst.n, inst.m
inst_corr = float(np.corrcoef(inst.values, inst.weights.sum(axis=0))[0, 1])
inst_corr_txt = fr(inst_corr, 3)
inst_title = inst.name
scatter_marker = {"size": 7, "opacity": 0.6, "color": "#2a78d6"}
scatter_layout = {"xaxis": {"title": "poids"}, "yaxis": {"title": "profit"}, "margin": {"t": 20},
                  "font": {"family": FONT}}

method_lov = list(B.METHODS.values())
methods_sel = [B.METHODS[k] for k in ["GREEDY", "DP", "GA", "GA-RAND", "GA-QL", "GA-QL-T"]]
runs = int(os.environ.get("RLGA_EXECUTIONS_DEFAUT", 3))
generations = int(os.environ.get("RLGA_GENERATIONS_DEFAUT", 200))
milp_time = 30
busy = False
estim = 0.0
n_max_ui, runs_max_ui, gens_max_ui = RS.LIMITES.n_max, RS.LIMITES.executions_max, RS.LIMITES.generations_max
case_msg = ""
status_msg = "Choisissez les méthodes puis cliquez sur « Lancer la comparaison »."
RES_COLS = ["code", "méthode", "valeur moyenne", "meilleure valeur", "écart moyen (%)", "temps moyen (s)",
            "exécutions", "statut"]
res_table = pd.DataFrame(columns=RES_COLS)
res_best = {}
has_results = False
best_method = "—"
best_gap_txt = "—"
ref_value_txt = "—"
vue = "Convergence"
vues = ["Convergence", "Opérateurs choisis", "Tableau détaillé"]
conv_fig = neutral_layout(go.Figure())
action_fig = neutral_layout(go.Figure())
action_method = "GA-QL-T"
_last_actions = {}

qtable = B.qtable_frame() if os.path.exists(B.QTABLE) else pd.DataFrame()

campaign_names = list(CAMPAGNES)
campaign = campaign_names[0]
camp_resume = CAMPAGNES[campaign]["resume"]
camp_message = CAMPAGNES[campaign]["message"]
camp_table = camp_frame(CAMPAGNES[campaign]["id"])
camp_tests = B.load_campaign_table(CAMPAGNES[campaign]["id"], "tests_statistiques")
_kt = [t for t, _ in CAMPAGNES[campaign]["kpis"]] + [""] * 4
_kv = [fr(v) for _, v in CAMPAGNES[campaign]["kpis"]] + [""] * 4
k1t, k2t, k3t, k4t = _kt[:4]
k1v, k2v, k3v, k4v = _kv[:4]
show_kpis = True
kpi_std, kpi_rand, kpi_ql, kpi_qlt = 0.0382, 0.0111, 0.0111, 0.0074
kpi_std_txt, kpi_rand_txt, kpi_ql_txt, kpi_qlt_txt = (fr(v) for v in (kpi_std, kpi_rand, kpi_ql, kpi_qlt))
d_rand_txt, d_ql_txt, d_qlt_txt = (f"{fr(v - kpi_std)} point par rapport à l'AG standard".replace("-", "−")
                                   for v in (kpi_rand, kpi_ql, kpi_qlt))


def figures_of(camp_label):
    tag = camp_label.split(" ")[0]
    return [FIGURES[f][1] for f in FIGURES
            if FIGURES[f][0] == tag and os.path.exists(os.path.join(FIG_DIR, f + ".png"))]


FIG_BY_TITLE = {v[1]: k for k, v in FIGURES.items()}
fig_titles = figures_of(campaign)
fig_title = fig_titles[0] if fig_titles else ""
fig_path = os.path.join(FIG_DIR, FIG_BY_TITLE.get(fig_title, "") + ".png")
fig_interp = FIGURES[FIG_BY_TITLE[fig_title]][2] if fig_title else ""

cases = B.list_files("Cas d'usage réel")
case = cases[0] if cases else ""
_case_inst, _case_df, case_meta = B.load_use_case(case) if case else (None, pd.DataFrame(), {})
case_title = case_meta.get("titre", "")
case_desc = case_meta.get("description", "")
case_items = B.generic_items(_case_df, case_meta) if case else pd.DataFrame()
CASE_RES_COLS = ["méthode", "meilleure valeur", "écart moyen (%)", "temps moyen (s)", "statut"]
case_result = pd.DataFrame(columns=CASE_RES_COLS)
case_best = {}
case_selection = case_items.iloc[0:0].copy()
case_summary = ""
case_done = False
case_n_sel = 0
case_value_txt = "—"
case_winners = ""

doc_resultats = os.path.join(DOCS, "analyse_resultats.pdf")
doc_discussion = os.path.join(DOCS, "discussion.pdf")
img_boucle = os.path.join(FIG_DIR, "fig08_boucle_rl_ag.png")
img_archi = os.path.join(APP, "assets", "architecture_plateforme.png")
img_politique = os.path.join(FIG_DIR, "fig04_politique_actions.png")
img_training = os.path.join(FIG_DIR, "fig06_entrainement_Q_OOD.png")
logo_eni = os.path.join(APP, "assets", "logos", "logo_eni.png")
logo_limad = os.path.join(APP, "assets", "logos", "logo_limad.png")
logo_gloria = os.path.join(APP, "assets", "logos", "logo_gloria.jpeg")
logo_univ = os.path.join(APP, "assets", "logos", "logo_univ.png")


# ════════════════════════════════════════════════════════════════════════════
#  Figures Plotly (thème neutre, sans WebGL)
# ════════════════════════════════════════════════════════════════════════════

def convergence_fig(conv: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col in conv.columns[1:]:
        k = LABEL2KEY.get(col, "")
        fig.add_trace(go.Scatter(x=conv["génération"], y=conv[col].clip(lower=1e-5), mode="lines", name=col,
                                 line=dict(width=3, color=COLORS.get(k))))
    return neutral_layout(fig, 460, xaxis_title="génération", yaxis_title="écart du meilleur individu (%)",
                          yaxis=dict(type="log", dtick=1, exponentformat="power"), hovermode="x unified",
                          legend=dict(orientation="h", y=-0.25))


def actions_fig(actions) -> go.Figure:
    tl = B.action_timeline(actions)
    fig = go.Figure()
    palette = ["#e34948", "#f08a6c", "#eda100", "#c3c2b7", "#a3a29c", "#6b6a66", "#1baf7a", "#2a78d6", "#4a3aa7"]
    for i, lab in enumerate(tl.columns[1:]):
        fig.add_trace(go.Scatter(x=tl["génération"], y=tl[lab], mode="lines", stackgroup="one", name=lab,
                                 line=dict(width=0.5, color=palette[i])))
    return neutral_layout(fig, 460, xaxis_title="génération", yaxis_title="part des choix (%)", hovermode="x unified")


def qtable_fig(q: pd.DataFrame) -> go.Figure:
    if q.empty:
        return go.Figure()
    Z = q[B.ACTION_LABELS].values
    rng = Z.max(axis=1, keepdims=True) - Z.min(axis=1, keepdims=True)
    Zn = np.where(rng > 0, (Z - Z.min(axis=1, keepdims=True)) / np.where(rng > 0, rng, 1), np.nan)
    fig = go.Figure(go.Heatmap(z=Zn, x=B.ACTION_LABELS, y=q["état"], colorscale="Blues",
                               colorbar=dict(title="préférence"),
                               hovertemplate="%{y}<br>%{x} : %{z:.2f}<extra></extra>"))
    return neutral_layout(fig, 820, margin=dict(l=220, r=20, t=20, b=60), yaxis=dict(autorange="reversed"))


q_fig = qtable_fig(qtable)


# ════════════════════════════════════════════════════════════════════════════
#  Callbacks — instance et comparaison
# ════════════════════════════════════════════════════════════════════════════

def _params(state) -> dict:
    return {"source": state.source, "classe": state.classe, "n": int(state.n_items), "seed": int(state.seed),
            "fichier": state.fichier}


def refresh_instance(state):
    try:
        new = B.build_instance(_params(state))
    except Exception as e:  # noqa: BLE001
        notify(state, "error", f"Instance impossible à construire : {e}")
        return
    state.inst = new
    state.inst_desc = B.describe(new)
    state.inst_items = B.items_frame(new)
    state.inst_n, state.inst_m = new.n, new.m
    state.inst_corr = float(np.corrcoef(new.values, new.weights.sum(axis=0))[0, 1])
    state.inst_corr_txt = fr(state.inst_corr, 3)
    state.inst_title = new.name
    state.classe_txt = CLASSES_TXT.get(state.classe, "")
    state.has_results = False


def on_source(state):
    if state.source != B.SOURCES[0]:
        state.fichiers = B.list_files(state.source)
        state.fichier = state.fichiers[0] if state.fichiers else ""
    refresh_instance(state)


def _jeton(state) -> str:
    """Identifiant de la session du visiteur (pour arrêter son propre calcul)."""
    try:
        return str(get_state_id(state))
    except Exception:  # noqa: BLE001
        return "local"


def _compare_thread(instance, keys, runs_, gens, mt, jeton):
    return RS.protege("compare", instance, keys, runs=runs_, generations=gens, milp_time=mt, jeton=jeton)


def _en_cours(debut: str, secondes, estimation: float) -> str:
    return f"{debut} ({secondes} s écoulées ; durée estimée ≈ {RS.duree_lisible(estimation)})"


def _echec(state, result, champ: str) -> bool:
    """Affiche le motif d'un calcul refusé, interrompu ou en erreur ; renvoie True en cas d'échec."""
    if isinstance(result, RS.Echec) or result is None:
        msg = result.message if isinstance(result, RS.Echec) else "Le calcul a échoué."
        state.assign(champ, msg)
        notify(state, "warning" if "arrêté à votre demande" in msg else "error", msg)
        return True
    return False


def _refuser(state, estimation: float, champ: str) -> bool:
    """Refuse un calcul dont la durée estimée dépasse le budget ; renvoie True si refusé."""
    try:
        RS.verifier_budget(estimation)
    except RS.CalculRefuse as e:
        state.assign(champ, str(e))
        notify(state, "error", str(e))
        return True
    return False


def stop_calc(state):
    if RS.arreter(_jeton(state)):
        notify(state, "warning", "Arrêt du calcul demandé.")


def _compare_status(state, status, result=None):
    if not isinstance(status, bool):
        state.status_msg = _en_cours("Calcul en cours…", status, state.estim)
        return
    state.busy = False
    if not status or _echec(state, result, "status_msg"):
        if not status:
            state.status_msg = "Le calcul a échoué."
            notify(state, "error", "Le calcul a échoué.")
        return
    res, conv, actions = result
    out, best = format_table(res[RES_COLS])
    state.res_best = best
    state.res_table = out
    state.conv_fig = convergence_fig(conv) if len(conv.columns) > 1 else neutral_layout(go.Figure())
    state._last_actions = actions
    key = state.action_method if state.action_method in actions else (list(actions)[0] if actions else None)
    state.action_fig = actions_fig(actions[key]) if key else neutral_layout(go.Figure())
    best = res.sort_values("écart moyen (%)").iloc[0]
    state.best_method = best["méthode"]
    state.best_gap_txt = fr(float(best["écart moyen (%)"])) + " %"
    state.ref_value_txt = fr(float(res["référence"].iloc[0]), 0)
    state.has_results = True
    state.status_msg = "Comparaison terminée."
    notify(state, "success", "Comparaison terminée.")


def run_compare(state):
    if state.busy:
        return
    keys = [LABEL2KEY[m] for m in state.methods_sel]
    if not keys:
        notify(state, "warning", "Choisissez au moins une méthode.")
        return
    runs_, gens, mt = int(state.runs), int(state.generations), float(state.milp_time)
    estimation = RS.estimer_comparaison(state.inst, keys, runs_, gens, mt)
    if _refuser(state, estimation, "status_msg"):
        return
    state.estim = estimation
    state.busy = True
    state.status_msg = f"Calcul lancé (durée estimée ≈ {RS.duree_lisible(estimation)})…"
    invoke_long_callback(state, _compare_thread, [state.inst, keys, runs_, gens, mt, _jeton(state)],
                         _compare_status, [], period=1000)


def on_action_method(state):
    if state.action_method in state._last_actions:
        state.action_fig = actions_fig(state._last_actions[state.action_method])


# ════════════════════════════════════════════════════════════════════════════
#  Callbacks — résultats et cas d'usage
# ════════════════════════════════════════════════════════════════════════════

def on_campaign(state):
    c = CAMPAGNES[state.campaign]
    state.camp_resume, state.camp_message = c["resume"], c["message"]
    state.camp_table = camp_frame(c["id"])
    state.camp_tests = B.load_campaign_table(c["id"], "tests_statistiques")
    titles = [t for t, _ in c["kpis"]] + [""] * 4
    vals = [fr(v) for _, v in c["kpis"]] + [""] * 4
    state.k1t, state.k2t, state.k3t, state.k4t = titles[:4]
    state.k1v, state.k2v, state.k3v, state.k4v = vals[:4]
    state.show_kpis = bool(c["kpis"])
    state.fig_titles = figures_of(state.campaign)
    state.fig_title = state.fig_titles[0] if state.fig_titles else ""
    on_figure(state)


def on_figure(state):
    fid = FIG_BY_TITLE.get(state.fig_title, "")
    state.fig_path = os.path.join(FIG_DIR, fid + ".png")
    state.fig_interp = FIGURES[fid][2] if fid else ""


def load_case(state):
    if not state.case:
        return
    inst_, df, meta = B.load_use_case(state.case)
    state.inst = inst_
    state.case_items = B.generic_items(df, meta)
    state.case_title, state.case_desc = meta["titre"], meta["description"]
    state.case_result = pd.DataFrame(columns=CASE_RES_COLS)
    state.case_best = {}
    state.case_selection = state.case_items.iloc[0:0].copy()
    state.case_done = False


CASE_KEYS = ["GREEDY", "MILP", "GA", "GA-QL-T"]


def _case_thread(instance, jeton):
    r = RS.protege("compare", instance, CASE_KEYS, runs=3, generations=200, milp_time=20, jeton=jeton)
    return r if isinstance(r, RS.Echec) else r[0]


def _case_status(state, status, result=None):
    if not isinstance(status, bool):
        return
    state.busy = False
    if not status:
        notify(state, "error", "Échec de la résolution.")
        return
    if _echec(state, result, "case_msg"):
        return
    res = result
    out, best = format_table(res[CASE_RES_COLS])
    state.case_best = best
    state.case_result = out
    # Toutes les méthodes qui atteignent la meilleure valeur sont citées (pas de départage arbitraire).
    top = res["meilleure valeur"].max()
    winners = res[np.isclose(res["meilleure valeur"], top, rtol=1e-9)]
    exact = winners[winners["code"].isin(["MILP", "DP"])]
    best = (exact if len(exact) else winners).iloc[0]
    _, raw, meta = B.load_use_case(state.case)
    mask = np.asarray(best["_solution"]).astype(bool)
    sel = raw[mask]
    state.case_selection = state.case_items[mask]
    state.case_n_sel = int(mask.sum())
    state.case_value_txt = fr(float(sel[meta["value_column"]].sum()), 1)
    used = [f"{fr(sel[c].sum(), 1)} / {fr(cap, 0)} {u}"
            for c, cap, u in zip(meta["weight_columns"], meta["capacities"], meta["unites"])]
    names = ", ".join(winners["méthode"])
    state.case_winners = names
    state.case_summary = (f"Meilleure valeur atteinte par : **{names}**. Solution affichée : {best['méthode']} — "
                          f"{len(sel)} objets retenus ; ressources utilisées : {' ; '.join(used)}.")
    state.case_done = True
    notify(state, "success", "Cas d'usage résolu.")


def solve_case(state):
    if state.busy or not state.case:
        return
    if state.inst.name != state.case:
        load_case(state)
    if _refuser(state, RS.estimer_comparaison(state.inst, CASE_KEYS, 3, 200, 20), "case_msg"):
        return
    state.case_msg = ""
    state.busy = True
    invoke_long_callback(state, _case_thread, [state.inst, _jeton(state)], _case_status, [], period=1000)


# ════════════════════════════════════════════════════════════════════════════
#  Callbacks — vérification des hypothèses H1 à H4 sur un cas réel
# ════════════════════════════════════════════════════════════════════════════
CURRENT = "Instance courante (page « Instance »)"
hyp_cases = cases + [CURRENT]
hyp_case = hyp_cases[0] if hyp_cases else CURRENT
hyp_runs = 8
hyp_gens = 200
hyp_done = False
hyp_status = "Choisissez un cas puis cliquez sur « Vérifier les quatre hypothèses »."
hyp_names = list(B.HYPOTHESES)
hyp_sel = "H1"
hyp_statement = B.HYPOTHESES["H1"]
hyp_memoire = B.VERDICTS_MEMOIRE["H1"]
hyp_verdict = ""
hyp_class = "ok"
hyp_expl = ""
hyp_context = ""
_hyp = {}
HYP_SUM_COLS = ["hypothèse", "verdict sur ce cas", "verdict du mémoire (toutes campagnes)"]
hyp_summary = pd.DataFrame(columns=HYP_SUM_COLS)
hyp_tests = pd.DataFrame(columns=["comparaison", "écart cible (%)", "écart autre (%)", "p (Wilcoxon, unilatéral)",
                                  "V/E/D", "significatif"])
hyp_methods = pd.DataFrame(columns=["méthode", "écart moyen (%)", "écart-type (%)", "meilleur écart (%)",
                                    "temps moyen (s)", "statut"])
hyp_best = {}


def cell_verdict(state, value, index, row, column_name):
    v = str(value)
    if v.startswith("Confirmée") or v.startswith("Première partie confirmée sur"):
        return "verdict-ok"
    if v.startswith("Non confirmée"):
        return "verdict-ko"
    return "verdict-partial"


def cell_best_hyp(state, value, index, row, column_name):
    return "cell-best" if _is_best(value, state.hyp_best.get(column_name)) else ""


def cell_signif(state, value, index, row, column_name):
    return "cell-best" if value == "oui" else ""


hyp_sum_props = {"cell_class_name[verdict sur ce cas]": cell_verdict}
hyp_methods_props = _props(cell_best_hyp, ["écart moyen (%)", "meilleur écart (%)", "temps moyen (s)"])
hyp_tests_props = {"cell_class_name[significatif]": cell_signif, "rebuild": True}


def _hyp_instance(state):
    if state.hyp_case == CURRENT:
        return state.inst
    return B.load_use_case(state.hyp_case)[0]


def _hyp_thread(instance, runs_, gens, jeton):
    R_ = RS.protege("run_hypotheses", instance, runs=runs_, generations=gens, jeton=jeton)
    if isinstance(R_, RS.Echec):
        return R_
    table, details = B.hypothesis_tables(R_)
    return R_, table, details


def _show_hypothesis(state):
    h = state.hyp_sel
    state.hyp_statement = B.HYPOTHESES[h]
    state.hyp_memoire = B.VERDICTS_MEMOIRE[h]
    d = state._hyp.get(h)
    if not d:
        return
    state.hyp_verdict, state.hyp_class, state.hyp_expl = d["verdict"], d["classe"], d["explication"]
    state.hyp_tests = pd.DataFrame(d["tests"])


def on_hyp_sel(state):
    _show_hypothesis(state)


def _hyp_status(state, status, result=None):
    if not isinstance(status, bool):
        state.hyp_status = _en_cours("Calcul en cours…", status, state.estim)
        return
    state.busy = False
    if not status:
        state.hyp_status = "Le calcul a échoué."
        notify(state, "error", "Le calcul a échoué.")
        return
    if _echec(state, result, "hyp_status"):
        return
    R_, table, details = result
    out, best = format_table(table)
    state.hyp_methods, state.hyp_best = out, best
    state._hyp = {h: {"verdict": d["verdict"], "classe": d["classe"], "explication": d["explication"],
                      "tests": format_table(d["tests"])[0].to_dict("records")} for h, d in details.items()}
    state.hyp_summary = pd.DataFrame([(h, d["verdict"], B.VERDICTS_MEMOIRE[h]) for h, d in details.items()],
                                     columns=HYP_SUM_COLS)
    state.hyp_context = (f"Instance : {R_['name']} — n = {R_['n']} objets, m = {R_['m']} contrainte(s), "
                         f"{R_['runs']} exécutions appariées (graines 0 à {R_['runs'] - 1}) par variante d'AG, "
                         f"valeur de référence {fr(R_['ref'], 2)}.")
    state.hyp_done = True
    _show_hypothesis(state)
    state.hyp_status = "Vérification terminée."
    notify(state, "success", "Vérification terminée.")


def run_hyp(state):
    if state.busy:
        return
    try:
        instance = _hyp_instance(state)
    except Exception as e:  # noqa: BLE001
        notify(state, "error", f"Instance indisponible : {e}")
        return
    runs_, gens = int(state.hyp_runs), int(state.hyp_gens)
    estimation = RS.estimer_hypotheses(instance, runs_, gens)
    if _refuser(state, estimation, "hyp_status"):
        return
    state.estim = estimation
    state.busy = True
    state.hyp_done = False
    state.hyp_status = f"Calcul lancé (durée estimée ≈ {RS.duree_lisible(estimation)})…"
    invoke_long_callback(state, _hyp_thread, [instance, runs_, gens, _jeton(state)],
                         _hyp_status, [], period=1000)


def go_hyp_from_case(state):
    if state.case:
        state.hyp_case = state.case
    navigate(state, "hypotheses")


# ════════════════════════════════════════════════════════════════════════════
#  Callbacks — scénarios (interface en français, sans composants génériques)
# ════════════════════════════════════════════════════════════════════════════

def _scen_label(sc) -> str:
    return f"{sc.name} · {sc.creation_date:%d/%m/%Y %H:%M} · {sc.id[-6:]}"


def _scen_map() -> dict:
    scs = sorted(tp.get_scenarios(), key=lambda s: s.creation_date, reverse=True)
    return {_scen_label(s): s.id for s in scs}


def _scen_params_frame(p: dict) -> pd.DataFrame:
    if not p:
        return pd.DataFrame(columns=["paramètre", "valeur"])
    noms = {"source": "Source des données", "classe": "Classe (Pisinger)", "n": "Nombre d'objets",
            "seed": "Graine aléatoire", "fichier": "Fichier d'instance", "methodes": "Méthodes (codes)",
            "runs": "Exécutions par variante d'AG", "generations": "Générations", "milp_time": "Limite PLNE (s)"}
    rows = []
    for k, lab in noms.items():
        if k in p:
            v = p[k]
            if k == "fichier" and p.get("source") == B.SOURCES[0]:
                continue
            if k in ("classe", "n", "seed") and p.get("source") != B.SOURCES[0]:
                continue
            rows.append((lab, ", ".join(v) if isinstance(v, list) else str(v)))
    return pd.DataFrame(rows, columns=["paramètre", "valeur"])


def _scen_summary_frame() -> pd.DataFrame:
    rows = []
    for s in sorted(tp.get_scenarios(), key=lambda s: s.creation_date, reverse=True):
        r = s.resultats.read() if s.resultats.is_ready_for_reading else None
        if r is None or len(r) == 0:
            rows.append((s.name, f"{s.creation_date:%d/%m %H:%M}", "non exécuté", "—", np.nan))
            continue
        b = r.sort_values("écart moyen (%)").iloc[0]
        rows.append((s.name, f"{s.creation_date:%d/%m %H:%M}", "exécuté", b["méthode"],
                     float(b["écart moyen (%)"])))
    return format_table(pd.DataFrame(rows, columns=["scénario", "créé le", "état", "meilleure méthode",
                                                    "écart (%)"]))


scen_map = _scen_map()
scen_lov = list(scen_map)
scen_sel = scen_lov[0] if scen_lov else None
scen_params = pd.DataFrame(columns=["paramètre", "valeur"])
SCEN_RES_COLS = ["code", "méthode", "valeur moyenne", "meilleure valeur", "écart moyen (%)", "temps moyen (s)",
                 "exécutions"]
scen_results = pd.DataFrame(columns=SCEN_RES_COLS)
scen_best = {}
scen_conv_fig = neutral_layout(go.Figure())
scen_ready = False
scen_state = "Aucun scénario sélectionné."
scen_summary, scen_summary_best = _scen_summary_frame()
scen_count = len(scen_lov)


def cell_best_summary(state, value, index, row, column_name):
    return "cell-best" if _is_best(value, state.scen_summary_best.get(column_name)) else ""


summary_props = {"cell_class_name[écart (%)]": cell_best_summary}


def _refresh_scenarios(state, select: str | None = None):
    m = _scen_map()
    state.scen_map = m
    state.scen_lov = list(m)
    state.scen_count = len(m)
    state.scen_summary, state.scen_summary_best = _scen_summary_frame()
    if select is not None:
        state.scen_sel = select
    elif state.scen_sel not in m:
        state.scen_sel = state.scen_lov[0] if state.scen_lov else None
    on_scenario(state)


def _current_scenario(state):
    sid = state.scen_map.get(state.scen_sel) if state.scen_sel else None
    return tp.get(sid) if sid else None


def on_scenario(state):
    sc = _current_scenario(state)
    if sc is None:
        state.scen_params = pd.DataFrame(columns=["paramètre", "valeur"])
        state.scen_ready = False
        state.scen_state = "Aucun scénario sélectionné."
        return
    p = sc.parametres.read() if sc.parametres.is_ready_for_reading else {}
    state.scen_params = _scen_params_frame(p or {})
    if sc.resultats.is_ready_for_reading and sc.resultats.read() is not None:
        r = sc.resultats.read()
        cols = [c for c in ["code", "méthode", "valeur moyenne", "meilleure valeur", "écart moyen (%)",
                            "temps moyen (s)", "exécutions"] if c in r.columns]
        out, best = format_table(r[cols])
        state.scen_best = best
        state.scen_results = out
        conv = sc.convergence.read()
        state.scen_conv_fig = (convergence_fig(conv) if conv is not None and len(conv.columns) > 1
                               else neutral_layout(go.Figure()))
        state.scen_ready = True
        state.scen_state = f"Exécuté — dernière écriture des résultats : {sc.resultats.last_edit_date:%d/%m/%Y %H:%M}."
    else:
        state.scen_ready = False
        state.scen_state = "Non exécuté : cliquez sur « Exécuter le scénario »."


def on_init(state):
    _refresh_scenarios(state)


def create_scenario(state):
    sc = tp.create_scenario(SCENARIO_CFG, name=f"{state.inst.name} ({len(state.methods_sel)} méthodes)")
    p = dict(_params(state))
    p.update({"methodes": [LABEL2KEY[m] for m in state.methods_sel], "runs": int(state.runs),
              "generations": int(state.generations), "milp_time": float(state.milp_time)})
    sc.parametres.write(p)
    _refresh_scenarios(state, _scen_label(sc))
    notify(state, "info", "Scénario enregistré : ouvrez la page « Scénarios » pour l'exécuter.")


def _submit_thread(sid):
    tp.submit(tp.get(sid), wait=True)
    return sid


def _submit_status(state, status, result=None):
    if not isinstance(status, bool):
        state.scen_state = f"Exécution en cours… ({status} s écoulées)"
        return
    state.busy = False
    if not status:
        state.scen_state = "L'exécution du scénario a échoué ou a été arrêtée (limites de ressources ou arrêt demandé)."
        notify(state, "error", "L'exécution du scénario a échoué ou a été arrêtée.")
        return
    try:
        _refresh_scenarios(state)
    except Exception as e:  # noqa: BLE001
        notify(state, "error", f"Résultats illisibles : {e}")
        return
    notify(state, "success", "Scénario exécuté.")


def run_scenario(state):
    sc = _current_scenario(state)
    if sc is None or state.busy:
        return
    p = dict(sc.parametres.read() or {})
    try:
        inst_ = B.build_instance(p)
        estimation = RS.estimer_comparaison(inst_, p.get("methodes", []), int(p.get("runs", 3)),
                                            int(p.get("generations", 200)), float(p.get("milp_time", 30)))
    except Exception as e:  # noqa: BLE001
        notify(state, "error", f"Paramètres du scénario illisibles : {e}")
        return
    if _refuser(state, estimation, "scen_state"):
        return
    p["_jeton"] = _jeton(state)
    sc.parametres.write(p)
    state.busy = True
    state.scen_state = "Exécution lancée…"
    invoke_long_callback(state, _submit_thread, [sc.id], _submit_status, [], period=1000)


def delete_scenario(state):
    sc = _current_scenario(state)
    if sc is None or state.busy:
        return
    tp.delete(sc.id)
    _refresh_scenarios(state)
    notify(state, "info", "Scénario supprimé.")


# ════════════════════════════════════════════════════════════════════════════
#  Pages
# ════════════════════════════════════════════════════════════════════════════
root_md = """
<|part|class_name=app-header|
<|layout|columns=1 auto|columns[mobile]=1 auto|class_name=app-brand|
<|part|
<|RL-in-GA · Problème du sac à dos|text|class_name=app-title|>

<|Apprentissage par renforcement dans l'algorithme génétique · Master Recherche en Informatique · ENI · LIMAD · GLoRIA|text|class_name=app-subtitle|>
|>
<|part|class_name=theme-switch|
<|toggle|theme|>
|>
|>

<|navbar|lov={nav_lov}|class_name=app-nav|>
|>
"""

accueil = Markdown("""
<|part|class_name=hero|
# L'apprentissage par renforcement peut-il améliorer l'algorithme génétique ?

Ce site présente les travaux d'un mémoire de **Master Recherche en Informatique**. Un **agent d'apprentissage par renforcement (Q-learning)** choisit, à chaque génération d'un **algorithme génétique**, les opérateurs de croisement et de mutation à appliquer pour résoudre le **problème du sac à dos**. Toutes les expériences sont reproductibles ici même, en quelques clics.

<|part|class_name=logo-row|
<|{logo_univ}|image|width=48px|height=60px|>
<|{logo_eni}|image|width=80px|height=60px|>
<|{logo_limad}|image|width=150px|height=60px|>
<|{logo_gloria}|image|width=170px|height=60px|>
|>
|>

<|part|class_name=callout|
**Réponse courte.** Oui, mais pas pour la raison attendue : appris *pendant* une exécution, le Q-learning ne fait pas mieux qu'un choix **aléatoire** des opérateurs — le gain vient de leur **diversité**. En revanche, un agent **pré-entraîné** sur des instances faciles, puis **transféré**, devient la meilleure méthode apprise sur le sac à dos 0/1.
|>

## Résultats clés

<|Écart moyen à l'optimum (%) sur 54 instances et 3 780 exécutions : plus l'écart est faible, meilleure est la méthode.|text|class_name=lead|>

<|layout|columns=1 1 1 1|columns[mobile]=1 1|class_name=kpi-row|
<|part|class_name=kpi-card|
<|AG standard|text|class_name=kpi-label|>
<|{kpi_std_txt}|text|class_name=kpi-value|>
<|méthode de référence|text|class_name=kpi-delta neutral|>
|>
<|part|class_name=kpi-card|
<|Opérateurs aléatoires|text|class_name=kpi-label|>
<|{kpi_rand_txt}|text|class_name=kpi-value|>
<|{d_rand_txt}|text|class_name=kpi-delta|>
|>
<|part|class_name=kpi-card|
<|Q-learning en ligne|text|class_name=kpi-label|>
<|{kpi_ql_txt}|text|class_name=kpi-value|>
<|{d_ql_txt}|text|class_name=kpi-delta|>
|>
<|part|class_name=kpi-card kpi-highlight|
<|Q-learning pré-entraîné|text|class_name=kpi-label|>
<|{kpi_qlt_txt}|text|class_name=kpi-value|>
<|{d_qlt_txt}|text|class_name=kpi-delta|>
|>
|>

## Parcourir les travaux

<|layout|columns=1 1 1|columns[mobile]=1|class_name=nav-grid|
<|part|class_name=card nav-card|
<|1 · Explorer|text|class_name=step|>

### Le problème

Générez une instance « facile » ou « difficile » et observez pourquoi l'heuristique gloutonne échoue sur les instances corrélées.

<|Explorer une instance|button|on_action=go_instance|>
|>
<|part|class_name=card nav-card|
<|2 · Comparer|text|class_name=step|>

### En direct

Lancez la programmation dynamique, le glouton et cinq variantes d'algorithme génétique sur la même instance, puis comparez leur convergence.

<|Comparer les méthodes|button|on_action=go_comparaison|>
|>
<|part|class_name=card nav-card|
<|3 · Comprendre|text|class_name=step|>

### La politique apprise

Visualisez ce que l'agent a appris : les opérateurs qu'il privilégie selon l'état de la recherche.

<|Voir la politique|button|on_action=go_politique|>
|>
<|part|class_name=card nav-card|
<|4 · Vérifier|text|class_name=step|>

### Les résultats statistiques

Tableaux, tests de Wilcoxon et de Friedman, figures commentées des quatre campagnes expérimentales.

<|Voir les résultats|button|on_action=go_resultats|>
|>
<|part|class_name=card nav-card|
<|5 · Appliquer|text|class_name=step|>

### Les cas d'usage

Budget communal, camion humanitaire, machines virtuelles, portefeuille : l'aide à la décision en pratique.

<|Voir les cas d'usage|button|on_action=go_cas|>
|>
<|part|class_name=card nav-card|
<|6 · Reproduire|text|class_name=step|>

### Les scénarios

Enregistrez une expérience complète, exécutez-la à nouveau quand vous le souhaitez et comparez les scénarios exécutés.

<|Gérer les scénarios|button|on_action=go_scenarios|>
|>
|>

<|part|class_name=footer|
<|{PIED_TXT}|text|mode=markdown|>
|>
""")

page_instance = Markdown("""
# Explorer une instance

<|Une instance du sac à dos est un ensemble d'objets (poids, profit) et une capacité. Sa difficulté dépend surtout de la corrélation entre profits et poids : plus elle est forte, plus les objets se ressemblent et plus le choix est délicat.|text|class_name=lead|>

<|layout|columns=1 2|columns[mobile]=1|
<|part|class_name=card|
### Paramètres

<|Source des données|text|class_name=field-label|>

<|{source}|selector|lov={sources}|dropdown|on_change=on_source|class_name=fullwidth|>

<|part|render={source == "Pisinger (générée)"}|
<|Classe d'instance (Pisinger, 2005)|text|class_name=field-label|>

<|{classe}|toggle|lov={classes}|on_change=refresh_instance|>

<|{classe_txt}|text|class_name=caption|>

<|Nombre d'objets : {n_items}|text|class_name=field-label|>

<|{n_items}|slider|min=50|max={n_max_ui}|step=50|on_change=refresh_instance|continuous=False|class_name=fullwidth|>

<|Graine aléatoire|text|class_name=field-label|>

<|{seed}|number|on_change=refresh_instance|>
|>
<|part|render={source != "Pisinger (générée)"}|
<|Instance|text|class_name=field-label|>

<|{fichier}|selector|lov={fichiers}|dropdown|on_change=refresh_instance|class_name=fullwidth|>
|>

<|Comparer les méthodes sur cette instance|button|on_action=go_comparaison|class_name=fullwidth mt2|>
|>

<|part|
<|layout|columns=1 1 1|columns[mobile]=1 1 1|class_name=kpi-row|
<|part|class_name=kpi-card|
<|Objets|text|class_name=kpi-label|>
<|{inst_n}|text|class_name=kpi-value|>
|>
<|part|class_name=kpi-card|
<|Contraintes|text|class_name=kpi-label|>
<|{inst_m}|text|class_name=kpi-value|>
|>
<|part|class_name=kpi-card|
<|Corrélation profit–poids|text|class_name=kpi-label|>
<|{inst_corr_txt}|text|class_name=kpi-value|>
|>
|>

<|part|class_name=card mt2|
### Nuage des objets

<|{inst_items}|chart|type=scatter|mode=markers|x=poids|y=profit|marker={scatter_marker}|layout={scatter_layout}|height=400px|>

<|Chaque point est un objet. Un nuage aligné (classes SC, ASC, SS) signifie que tous les objets ont une efficacité voisine : l'heuristique gloutonne ne sait plus les départager.|text|class_name=caption|>
|>
|>
|>

<|Caractéristiques détaillées de l'instance|expandable|expanded=False|class_name=mt2|
<|{inst_desc}|table|show_all|width=100%|>
|>
""")

page_compare = Markdown("""
# Comparer les méthodes

<|Toutes les méthodes résolvent la même instance. Les variantes d'algorithme génétique disposent du même budget (100 individus × G générations) ; seule la façon de choisir les opérateurs change.|text|class_name=lead|>

<|layout|columns=1 2|columns[mobile]=1|
<|part|class_name=card|
<|Étape 1 · Instance|text|class_name=step|>

<|{inst_title}|text|class_name=strong|> — <|{inst_n}|text|> objets, <|{inst_m}|text|> contrainte(s)

<|Changer d'instance|button|on_action=go_instance|>

<|Étape 2 · Méthodes|text|class_name=step mt2|>

<|{methods_sel}|selector|lov={method_lov}|multiple|mode=check|>

<|Paramètres avancés|expandable|expanded=False|
<|Exécutions par variante d'AG : {runs}|text|class_name=field-label|>

<|{runs}|slider|min=1|max={runs_max_ui}|class_name=fullwidth|>

<|Générations : {generations}|text|class_name=field-label|>

<|{generations}|slider|min=50|max={gens_max_ui}|step=50|class_name=fullwidth|>

<|Limite de temps de la PLNE (s)|text|class_name=field-label|>

<|{milp_time}|number|>
|>

<|Étape 3 · Lancer|text|class_name=step mt2|>

<|Lancer la comparaison|button|on_action=run_compare|active={not busy}|class_name=fullwidth plain|>

<|Enregistrer comme scénario|button|on_action=create_scenario|class_name=fullwidth mt1|>

<|part|render={busy}|
<|progress|>

<|Arrêter le calcul|button|on_action=stop_calc|class_name=fullwidth mt1|>
|>

<|{status_msg}|text|class_name=caption|>
|>

<|part|
<|part|render={not has_results}|class_name=card empty-state|
### Résultats

Les résultats apparaîtront ici : tableau comparatif, courbes de convergence et opérateurs choisis par l'agent au fil des générations. Un calcul prend de quelques secondes à une minute selon la taille de l'instance.
|>

<|part|render={has_results}|
<|layout|columns=1 1 1|columns[mobile]=1|class_name=kpi-row|
<|part|class_name=kpi-card kpi-highlight|
<|Meilleure méthode|text|class_name=kpi-label|>
<|{best_method}|text|class_name=kpi-value kpi-value-text|>
|>
<|part|class_name=kpi-card|
<|Meilleur écart moyen|text|class_name=kpi-label|>
<|{best_gap_txt}|text|class_name=kpi-value|>
|>
<|part|class_name=kpi-card|
<|Valeur de référence|text|class_name=kpi-label|>
<|{ref_value_txt}|text|class_name=kpi-value|>
|>
|>

<|{vue}|toggle|lov={vues}|class_name=mt2 view-switch|>

<|part|render={vue == "Convergence"}|class_name=card mt1|
<|chart|figure={conv_fig}|>

<|Écart du meilleur individu à la référence (échelle logarithmique), moyenne des exécutions. Plus la courbe descend vite et bas, meilleure est la méthode.|text|class_name=caption|>
|>

<|part|render={vue == "Opérateurs choisis"}|class_name=card mt1|
<|{action_method}|toggle|lov=GA-QL-T;GA-QL;GA-UCB;GA-RAND|on_change=on_action_method|>

<|chart|figure={action_fig}|>

<|Part de chaque couple (croisement + mutation) choisi au fil des générations. L'agent pré-entraîné (GA-QL-T) privilégie le croisement uniforme ; l'agent en ligne (GA-QL) choisit presque au hasard.|text|class_name=caption|>
|>

<|part|render={vue == "Tableau détaillé"}|class_name=card mt1|
<|{res_table}|table|width=100%|properties=res_props|show_all|>

<|La meilleure valeur de chaque colonne est surlignée en vert : la plus grande pour les valeurs, la plus faible pour l'écart et le temps.|text|class_name=caption|>
|>
|>
|>
|>
""")

page_policy = Markdown("""
# Politique apprise par l'agent

<|part|class_name=callout|
La Q-table a été apprise **hors ligne**, uniquement sur des instances **faciles** (classes UC, WC, SS ; 100 à 200 objets), puis appliquée telle quelle aux instances difficiles, plus grandes, et au sac à dos multidimensionnel.
|>

<|part|class_name=card section|
## 1 · Le principe

À chaque génération, l'agent observe la **diversité** de la population, la **stagnation** du meilleur individu et l'**avancement** de la recherche (27 états), choisit l'un des **9 couples d'opérateurs**, puis reçoit comme récompense l'amélioration relative du meilleur individu.

<|part|class_name=figure figure-medium|
<|{img_boucle}|image|width=100%|>
|>
|>

<|part|class_name=card section|
## 2 · Ce que l'agent choisit, selon la phase de la recherche

Fréquence des 9 couples d'opérateurs au début, au milieu et à la fin de la recherche, pour trois classes d'instances et trois contrôleurs.

<|part|class_name=figure|
<|{img_politique}|image|width=100%|>
|>

<|part|class_name=interpretation|
**Lecture.** Le Q-learning en ligne et le bandit UCB1 choisissent presque uniformément : ils n'apprennent rien en 200 générations. L'agent pré-entraîné privilégie le **croisement uniforme** (UX + BF3, UX + SWAP), la famille de la meilleure configuration fixe.
|>
|>

<|part|class_name=card section|
## 3 · Préférences de la Q-table, état par état

Chaque ligne est un état (diversité · stagnation · avancement) ; la couleur indique la préférence relative de l'agent pour chaque couple d'opérateurs, de 0 (action la moins bonne) à 1 (action préférée). Les lignes vides correspondent aux états jamais visités pendant l'entraînement.

<|chart|figure={q_fig}|>
|>

<|part|class_name=card section|
## 4 · Dynamique de l'entraînement

<|part|class_name=figure figure-medium|
<|{img_training}|image|width=100%|>
|>

<|part|class_name=interpretation|
**Lecture.** À mesure que l'exploration diminue, la part du croisement uniforme avec mutation BF3 augmente.
|>
|>

<|Valeurs numériques de la Q-table|expandable|expanded=False|class_name=mt2|
<|{qtable}|table|width=100%|number_format=%.4f|show_all|height=520px|>
|>
""")

page_results = Markdown("""
# Résultats expérimentaux

<|Choisissez une campagne : son résumé, ses indicateurs, ses figures commentées et ses tableaux statistiques s'affichent ci-dessous.|text|class_name=lead|>

<|{campaign}|toggle|lov={campaign_names}|on_change=on_campaign|class_name=campaign-switch|>

<|part|class_name=card mt2|
<|{camp_resume}|text|class_name=body-text|>

<|part|class_name=callout mt1|
<|{camp_message}|text|>
|>

<|part|render={show_kpis}|
<|layout|columns=1 1 1 1|columns[mobile]=1 1|class_name=kpi-row mt2|
<|part|class_name=kpi-card|
<|{k1t}|text|class_name=kpi-label|>
<|{k1v}|text|class_name=kpi-value|>
|>
<|part|class_name=kpi-card|
<|{k2t}|text|class_name=kpi-label|>
<|{k2v}|text|class_name=kpi-value|>
|>
<|part|class_name=kpi-card|
<|{k3t}|text|class_name=kpi-label|>
<|{k3v}|text|class_name=kpi-value|>
|>
<|part|class_name=kpi-card|
<|{k4t}|text|class_name=kpi-label|>
<|{k4v}|text|class_name=kpi-value|>
|>
|>

<|Écart moyen à la référence (%) : plus il est faible, meilleure est la méthode.|text|class_name=caption|>
|>
|>

<|part|class_name=card mt2|
## Figures

<|{fig_title}|selector|lov={fig_titles}|dropdown|class_name=fullwidth|on_change=on_figure|>

<|part|class_name=figure mt2|
<|{fig_path}|image|width=100%|>
|>

<|part|class_name=interpretation|
**Lecture.** <|{fig_interp}|text|>
|>
|>

<|Écart moyen par classe et par méthode (tableau)|expandable|expanded=False|class_name=mt2|
<|{camp_table}|table|width=100%|properties=camp_props|show_all|>

<|Dans chaque ligne, la méthode dont l'écart est le plus faible est surlignée en vert.|text|class_name=caption|>
|>

<|Tests statistiques : Wilcoxon apparié (correction de Holm), taille d'effet A12, victoires/égalités/défaites|expandable|expanded=False|
<|{camp_tests}|table|width=100%|number_format=%.4g|show_all|>
|>
""")

page_cases = Markdown("""
# Cas d'usage

<|Quatre problèmes de décision concrets, modélisés comme des sacs à dos. Les données sont synthétiques (ordres de grandeur plausibles) et servent à illustrer la démarche.|text|class_name=lead|>

<|layout|columns=1 3|columns[mobile]=1|
<|part|class_name=card|
### Choisir un cas

<|{case}|selector|lov={cases}|on_change=load_case|class_name=fullwidth|>

<|Résoudre|button|on_action=solve_case|active={not busy}|class_name=fullwidth plain mt2|>

<|part|render={busy}|
<|progress|>

<|Arrêter le calcul|button|on_action=stop_calc|class_name=fullwidth mt1|>
|>

<|{case_msg}|text|class_name=caption|>

<|Méthodes lancées : glouton, PLNE (solveur exact), AG standard et AG + Q-learning pré-entraîné.|text|class_name=caption|>

<|Vérifier les hypothèses sur ce cas|button|on_action=go_hyp_from_case|class_name=fullwidth mt2|>
|>
<|part|class_name=card|
## <|{case_title}|text|>

<|{case_desc}|text|class_name=body-text|>

<|part|render={case_done}|
<|layout|columns=1 1|columns[mobile]=1 1|class_name=kpi-row mt2|
<|part|class_name=kpi-card|
<|Objets retenus|text|class_name=kpi-label|>
<|{case_n_sel}|text|class_name=kpi-value|>
|>
<|part|class_name=kpi-card|
<|Valeur totale|text|class_name=kpi-label|>
<|{case_value_txt}|text|class_name=kpi-value|>
|>
|>

<|part|class_name=callout callout-success mt1|
<|{case_summary}|text|mode=markdown|>
|>

<|{case_result}|table|width=100%|properties=case_props|show_all|>

<|La meilleure valeur de chaque colonne est surlignée en vert.|text|class_name=caption|>
|>
|>
|>

<|Pourquoi la PLNE obtient-elle presque toujours la meilleure solution ?|expandable|expanded=False|class_name=mt2|
<|part|class_name=body-text|
La **PLNE** (programmation linéaire en nombres entiers, résolue par le solveur HiGHS par séparation et évaluation) est une méthode **exacte** : lorsqu'elle termine, elle **prouve** que sa solution est optimale. Les cas d'usage comptent de 120 à 400 objets et au plus 3 ressources ; à cette taille, le solveur trouve et prouve l'optimum en moins de 2 secondes. Aucune heuristique ne peut faire mieux que l'optimum : au mieux, elle l'égale — c'est le cas de l'AG sur le budget communal et, souvent, sur le portefeuille.

Ce résultat est donc **attendu** et conforme aux conclusions du mémoire (hypothèse H4) : sur des sacs à dos de taille modérée, les méthodes exactes dominent. L'intérêt de l'AG piloté par apprentissage apparaît lorsque les méthodes exactes atteignent leurs limites : capacités gigantesques où la programmation dynamique est inapplicable et où la PLNE ne termine pas en 60 s (instances de Jooken et al., 2022, sur lesquelles tous les AG font mieux que la PLNE), très grandes tailles, contraintes non linéaires ou temps de réponse imposé. L'objectif de ces cas d'usage est de montrer la démarche et d'évaluer honnêtement l'écart des heuristiques à l'optimum, y compris l'échec du cas « machines virtuelles ».
|>
|>

<|Objets retenus par la solution affichée|expandable|expanded=False|
<|{case_selection}|table|width=100%|show_all|height=480px|>
|>

<|Tous les objets disponibles|expandable|expanded=False|
<|{case_items}|table|width=100%|show_all|height=480px|>
|>
""")

page_hypotheses = Markdown("""
# Vérifier les hypothèses sur un cas réel

<|Les quatre hypothèses de recherche (H1 à H4) ont été évaluées dans le mémoire sur 143 instances de référence. Cette page permet de les confronter à un cas d'usage concret : un seul calcul exécute toutes les méthodes nécessaires, avec les mêmes graines aléatoires, puis établit un verdict pour chaque hypothèse à l'aide de tests statistiques appariés.|text|class_name=lead|>

<|layout|columns=1 2|columns[mobile]=1|
<|part|class_name=card|
<|Étape 1 · Cas|text|class_name=step|>

<|{hyp_case}|selector|lov={hyp_cases}|class_name=fullwidth|>

<|L'option « Instance courante » reprend l'instance choisie dans la page Instance (par exemple une instance de Jooken à capacité 10⁸ pour tester la seconde partie de H4).|text|class_name=caption|>

<|Étape 2 · Paramètres|text|class_name=step mt2|>

<|Exécutions appariées par variante d'AG : {hyp_runs}|text|class_name=field-label|>

<|{hyp_runs}|slider|min=5|max=20|class_name=fullwidth|>

<|Générations : {hyp_gens}|text|class_name=field-label|>

<|{hyp_gens}|slider|min=50|max=500|step=50|class_name=fullwidth|>

<|Étape 3 · Lancer|text|class_name=step mt2|>

<|Vérifier les quatre hypothèses|button|on_action=run_hyp|active={not busy}|class_name=fullwidth plain|>

<|part|render={busy}|
<|progress|>

<|Arrêter le calcul|button|on_action=stop_calc|class_name=fullwidth mt1|>
|>

<|{hyp_status}|text|class_name=caption|>

<|Méthodes exécutées : AG standard, AG opérateurs aléatoires, AG + Q-learning en ligne et pré-entraîné, AG fixe UX + BF3 (graines 0 à k − 1), programmation dynamique, PLNE (limite de 60 s puis limite égale au temps de l'AG pré-entraîné) et glouton. Durée : une à trois minutes selon le cas.|text|class_name=caption|>
|>

<|part|
<|part|render={not hyp_done}|class_name=card empty-state|
### Verdicts

Les verdicts apparaîtront ici : un tableau de synthèse pour H1 à H4, puis, pour chaque hypothèse, les tests statistiques qui la fondent. Un test est jugé significatif lorsque la valeur p du test de Wilcoxon apparié unilatéral est inférieure à 0,05.
|>

<|part|render={hyp_done}|
<|part|class_name=card|
### Synthèse

<|{hyp_context}|text|class_name=caption|>

<|{hyp_summary}|table|width=100%|properties=hyp_sum_props|show_all|class_name=mt1|>
|>

<|{hyp_sel}|toggle|lov={hyp_names}|on_change=on_hyp_sel|class_name=mt2 view-switch|>

<|part|class_name=card mt1|
<|part|class_name=callout|
**<|{hyp_sel}|text|>.** <|{hyp_statement}|text|>
|>

<|part|render={hyp_class == "ok"}|class_name=verdict verdict-ok|
<|{hyp_verdict}|text|>
|>
<|part|render={hyp_class == "partial"}|class_name=verdict verdict-partial|
<|{hyp_verdict}|text|>
|>
<|part|render={hyp_class == "ko"}|class_name=verdict verdict-ko|
<|{hyp_verdict}|text|>
|>

<|{hyp_expl}|text|class_name=body-text mt1|>

<|{hyp_tests}|table|width=100%|properties=hyp_tests_props|show_all|class_name=mt1|>

<|Verdict établi dans le mémoire, sur l'ensemble des campagnes : {hyp_memoire}.|text|class_name=caption|>
|>
|>
|>
|>

<|part|render={hyp_done}|
<|Écarts de toutes les méthodes sur ce cas|expandable|expanded=False|class_name=mt2|
<|{hyp_methods}|table|width=100%|properties=hyp_methods_props|show_all|>

<|Écart à la valeur de référence (optimum prouvé par la méthode exacte lorsqu'elle aboutit). La meilleure valeur de chaque colonne est surlignée en vert.|text|class_name=caption|>
|>
|>

<|Comment lire ces verdicts ?|expandable|expanded=False|
<|part|class_name=body-text|
Chaque variante d'algorithme génétique est exécutée avec les mêmes graines ; les écarts sont donc **appariés** graine par graine. Le test de Wilcoxon unilatéral vérifie si la méthode cible obtient des écarts plus faibles que l'autre ; la colonne V/E/D compte les graines où la cible gagne, fait jeu égal ou perd.

Un verdict obtenu sur **un seul cas** et quelques exécutions n'a pas la portée des campagnes du mémoire : il illustre l'hypothèse sur un problème concret et peut la contredire localement — c'est le cas du placement de machines virtuelles, où l'AG standard fait mieux que les variantes pilotées. Avec 5 exécutions, la plus petite valeur p atteignable est 0,03 ; au moins 8 exécutions sont conseillées.
|>
|>
""")

page_scenarios = Markdown("""
# Scénarios

<|Un scénario enregistre une expérience complète — instance, méthodes et paramètres — pour l'exécuter à nouveau ou la comparer plus tard. Son exécution enchaîne deux tâches : construire l'instance, puis résoudre avec chaque méthode ; les résultats restent enregistrés avec le scénario.|text|class_name=lead|>

<|layout|columns=1 2|columns[mobile]=1|
<|part|class_name=card|
### 1 · Choisir un scénario

<|{scen_count} scénario(s) enregistré(s)|text|class_name=caption|>

<|{scen_sel}|selector|lov={scen_lov}|on_change=on_scenario|class_name=fullwidth scen-list|height=320px|>

<|Exécuter le scénario|button|on_action=run_scenario|active={not busy and scen_sel is not None}|class_name=fullwidth plain mt2|>

<|Supprimer|button|on_action=delete_scenario|active={not busy and scen_sel is not None}|class_name=fullwidth mt1 danger|>

<|part|render={busy}|
<|progress|>

<|Arrêter le calcul|button|on_action=stop_calc|class_name=fullwidth mt1|>
|>

### 2 · Créer un scénario

<|Le bouton ci-dessous enregistre l'instance et les méthodes actuellement choisies (pages « Instance » et « Comparaison »).|text|class_name=caption|>

<|Nouveau scénario|button|on_action=create_scenario|class_name=fullwidth mt1|>
|>

<|part|class_name=card|
### Scénario sélectionné

<|{scen_state}|text|class_name=caption|>

<|part|class_name=pipeline|
<|Paramètres|text|class_name=pipe-node pipe-data|>
<|→|text|class_name=pipe-arrow|>
<|Construire l'instance|text|class_name=pipe-node pipe-task|>
<|→|text|class_name=pipe-arrow|>
<|Instance|text|class_name=pipe-node pipe-data|>
<|→|text|class_name=pipe-arrow|>
<|Résoudre|text|class_name=pipe-node pipe-task|>
<|→|text|class_name=pipe-arrow|>
<|Résultats + convergence|text|class_name=pipe-node pipe-data|>
|>

<|Graphe des tâches : les données (en gris) alimentent les tâches (en bleu). La construction de l'instance n'est pas refaite si les paramètres n'ont pas changé.|text|class_name=caption|>

<|{scen_params}|table|width=100%|show_all|class_name=mt1|>

<|part|render={scen_ready}|
#### Résultats

<|{scen_results}|table|width=100%|properties=scen_props|show_all|>

<|chart|figure={scen_conv_fig}|>
|>
|>
|>

<|part|class_name=card mt2|
### Comparer les scénarios

<|{scen_summary}|table|width=100%|properties=summary_props|show_all|>

<|Le scénario dont la meilleure méthode obtient l'écart le plus faible est surligné en vert. Les écarts ne sont comparables qu'entre scénarios portant sur la même instance.|text|class_name=caption|>
|>
""")

page_about = Markdown("""
# À propos

<|layout|columns=1 1|columns[mobile]=1|
<|part|class_name=card|
### Le projet

**Intégration de l'apprentissage par renforcement dans l'algorithme génétique pour la résolution du problème de sac à dos complexe** — mémoire de Master Recherche en Informatique.

- **Auteur** : RALAIVAO Niaiko Michaël
- **Encadrement** : Pr MAHATODY Thomas ; Dr RABETAFIKA Louis Haja ; Dr RATOVONDRAHONA Alain Josué
- **Établissement** : École Nationale d'Informatique, Université de Fianarantsoa
- **Laboratoire** : LIMAD — équipe **GLoRIA** (Génie Logiciel et Recherche émergente en Intelligence Artificielle)

### Documents

<|{doc_resultats}|file_download|label=Analyse des résultats (PDF)|>

<|{doc_discussion}|file_download|label=Discussion (PDF)|>
|>
<|part|class_name=card|
### Architecture

<|part|class_name=figure|
<|{img_archi}|image|width=100%|>
|>

### Code source et reproductibilité

<|{CODE_TXT}|text|mode=markdown|>

Technologies : Python, NumPy, SciPy (solveur HiGHS), Pandas, Matplotlib et Plotly.
|>
|>
""")

pages = {"/": root_md, "accueil": accueil, "instance": page_instance, "comparaison": page_compare,
         "politique": page_policy, "resultats": page_results, "cas_usage": page_cases,
         "hypotheses": page_hypotheses, "scenarios": page_scenarios, "a_propos": page_about}

stylekit = {"color_primary": "#1C5CAB", "color_secondary": "#1baf7a", "border_radius": 10,
            "font_family": FONT}

gui = Gui(pages=pages, css_file="assets/style.css")

if __name__ == "__main__":
    orchestrator = tp.Orchestrator()
    orchestrator.run()
    gui.run(title="RL-in-GA · Sac à dos", host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5000")), dark_mode=os.environ.get("DARK_MODE", "0") == "1",
            stylekit=stylekit, use_reloader=False, favicon="assets/icons/resultats.svg", watermark="",
            run_browser=os.environ.get("NO_BROWSER") is None, debug=False)
