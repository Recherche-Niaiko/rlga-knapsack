# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Instances du problème du sac à dos (KP 0/1) et du sac à dos multidimensionnel (MKP).

Représentation unifiée : une instance possède
  - values  : vecteur (n,) des profits v_i
  - weights : matrice (m, n) des poids w_ji (m = 1 pour le KP 0/1)
  - capacities : vecteur (m,) des capacités C_j

Ce module fournit :
  * des générateurs des classes de Pisinger (2005) : UC, WC, SC, ISC, ASC, SS, USW ;
  * des lecteurs pour les jeux de données présents dans DATASETS/ :
      - instances_01_KP (large_scale / low-dimensional, optimums fournis) ;
      - Jooken et al. (2022), instances difficiles (optimums fournis) ;
      - OR-Library MKP (chubeas, sac94, gk) ;
      - Pisinger "hard instances" (smallcoeff), si téléchargées ;
  * le calcul des caractéristiques d'instance phi(I) utilisées par l'agent RL.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

PISINGER_CLASSES = {
    "UC": "Non corrélée (uncorrelated)",
    "WC": "Faiblement corrélée (weakly correlated)",
    "SC": "Fortement corrélée (strongly correlated)",
    "ISC": "Inversement fortement corrélée",
    "ASC": "Presque fortement corrélée (almost strongly correlated)",
    "SS": "Somme de sous-ensembles (subset-sum)",
    "USW": "Non corrélée à poids similaires",
}


@dataclass
class KPInstance:
    name: str
    values: np.ndarray                 # (n,)
    weights: np.ndarray                # (m, n)
    capacities: np.ndarray             # (m,)
    optimum: Optional[float] = None    # valeur optimale (ou meilleure connue) si disponible
    optimum_is_proven: bool = False
    family: str = "custom"             # ex. "pisinger-gen", "jooken", "orlib-mkp", ...
    klass: str = ""                    # ex. "UC", "SC", "MKP"
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        self.values = np.asarray(self.values, dtype=np.float64)
        w = np.asarray(self.weights, dtype=np.float64)
        if w.ndim == 1:
            w = w[None, :]
        self.weights = w
        self.capacities = np.atleast_1d(np.asarray(self.capacities, dtype=np.float64))

    @property
    def n(self) -> int:
        return int(self.values.shape[0])

    @property
    def m(self) -> int:
        return int(self.weights.shape[0])

    @property
    def is_mkp(self) -> bool:
        return self.m > 1

    # -- évaluation d'une solution -------------------------------------------------
    def value(self, x: np.ndarray) -> float:
        return float(self.values @ x)

    def load(self, x: np.ndarray) -> np.ndarray:
        return self.weights @ x

    def is_feasible(self, x: np.ndarray) -> bool:
        return bool(np.all(self.load(x) <= self.capacities + 1e-9))

    def pseudo_utility(self) -> np.ndarray:
        """Efficacité u_i = v_i / sum_j (w_ji / C_j) (ratio classique v/w si m = 1)."""
        scaled = (self.weights / self.capacities[:, None]).sum(axis=0)
        return self.values / np.maximum(scaled, 1e-12)

    def summary(self) -> dict:
        return {"name": self.name, "family": self.family, "class": self.klass,
                "n": self.n, "m": self.m, "optimum": self.optimum}


# ════════════════════════════════════════════════════════════════════════════
#  Générateurs de Pisinger (2005) — "Where are the hard knapsack problems?"
# ════════════════════════════════════════════════════════════════════════════

def generate_pisinger(klass: str, n: int, R: int = 1000, h: int = 50, H: int = 100,
                      seed: int = 0) -> KPInstance:
    """Génère une instance KP 0/1 de la classe demandée (coefficients entiers).

    La capacité suit le schéma de Pisinger : C = h/(H+1) * sum(w)  (instance h sur H).
    Avec h = 50, H = 100, on obtient C ~ 0.5 * sum(w).
    """
    rng = np.random.default_rng(seed)
    k = klass.upper()
    if k == "UC":
        w = rng.integers(1, R + 1, n)
        v = rng.integers(1, R + 1, n)
    elif k == "WC":
        w = rng.integers(1, R + 1, n)
        v = w + rng.integers(-R // 10, R // 10 + 1, n)
        v = np.maximum(v, 1)
    elif k == "SC":
        w = rng.integers(1, R + 1, n)
        v = w + R // 10
    elif k == "ISC":
        v = rng.integers(1, R + 1, n)
        w = v + R // 10
    elif k == "ASC":
        w = rng.integers(1, R + 1, n)
        v = w + R // 10 + rng.integers(-R // 500, R // 500 + 1, n)
    elif k == "SS":
        w = rng.integers(1, R + 1, n)
        v = w.copy()
    elif k == "USW":
        w = rng.integers(100000, 100100 + 1, n)
        v = rng.integers(1, 1000 + 1, n)
    else:
        raise ValueError(f"Classe inconnue : {klass}")
    C = int(np.floor(h / (H + 1) * w.sum()))
    return KPInstance(name=f"{k}_n{n}_R{R}_s{seed}", values=v, weights=w, capacities=[C],
                      family="pisinger-gen", klass=k, meta={"R": R, "seed": seed})


# ════════════════════════════════════════════════════════════════════════════
#  Lecteurs de fichiers
# ════════════════════════════════════════════════════════════════════════════

def read_kp01_simple(path: str, optimum_path: Optional[str] = None, klass: str = "") -> KPInstance:
    """Format "instances_01_KP" : ligne 1 = 'n C', puis n lignes 'v w' (+ éventuelle ligne solution)."""
    with open(path) as f:
        lines = [l.split() for l in f if l.strip()]
    n, C = int(lines[0][0]), float(lines[0][1])
    vw = np.array([[float(a) for a in l[:2]] for l in lines[1:1 + n]])
    opt = None
    if optimum_path and os.path.exists(optimum_path):
        with open(optimum_path) as f:
            txt = f.read().strip().split()
            if txt:
                opt = float(txt[0])
    name = os.path.basename(path)
    if not klass and name.startswith("knapPI_"):
        klass = {"1": "UC", "2": "WC", "3": "SC"}.get(name.split("_")[1], "")
    return KPInstance(name=name, values=vw[:, 0], weights=vw[:, 1], capacities=[C], optimum=opt,
                      optimum_is_proven=opt is not None, family="kp01-files", klass=klass or "LD")


def read_jooken(folder: str, optimum: Optional[float] = None) -> KPInstance:
    """Format Jooken et al. (2022) : n, puis 'id profit poids', puis capacité."""
    with open(os.path.join(folder, "test.in")) as f:
        lines = [l.split() for l in f if l.strip()]
    n = int(lines[0][0])
    rows = np.array([[float(x) for x in l] for l in lines[1:1 + n]])
    C = float(lines[1 + n][0])
    name = os.path.basename(folder.rstrip("/"))
    return KPInstance(name=name, values=rows[:, 1], weights=rows[:, 2], capacities=[C],
                      optimum=optimum if (optimum is not None and optimum > 0) else None,
                      optimum_is_proven=optimum is not None and optimum > 0,
                      family="jooken", klass="JOOKEN")


def read_orlib_mkp(path: str, fmt: str = "auto") -> KPInstance:
    """Format OR-Library (chubeas / sac94 / gk) : 'n m opt', profits, m lignes de poids, capacités.

    Les nombres peuvent être répartis librement sur plusieurs lignes.
    """
    with open(path) as f:
        toks = f.read().split()
    nums = [float(t) for t in toks]
    n, m, opt = int(nums[0]), int(nums[1]), nums[2]
    p = 3
    values = np.array(nums[p:p + n]); p += n
    W = np.array(nums[p:p + m * n]).reshape(m, n); p += m * n
    C = np.array(nums[p:p + m])
    name = os.path.basename(path)
    return KPInstance(name=name, values=values, weights=W, capacities=C,
                      optimum=opt if opt > 0 else None, optimum_is_proven=False,
                      family="orlib-mkp", klass="MKP", meta={"m": m})


def read_pisinger_hard(path: str, max_instances: int = 10) -> list[KPInstance]:
    """Format des fichiers 'smallcoeff/largecoeff' de Pisinger (plusieurs instances par fichier)."""
    out = []
    with open(path) as f:
        block = []
        for line in f:
            line = line.strip()
            if line.startswith("-----"):
                if block:
                    out.append(_parse_pisinger_block(block))
                    block = []
                    if len(out) >= max_instances:
                        break
            elif line:
                block.append(line)
    return out


def _parse_pisinger_block(block: list[str]) -> KPInstance:
    name = block[0]
    n = int(block[1].split()[1])
    C = float(block[2].split()[1])
    z = float(block[3].split()[1])
    items = [l.split(",") for l in block[5:5 + n]]
    arr = np.array([[float(a) for a in it[:3]] for it in items])
    klass = "P" + name.split("_")[1] if name.startswith("knapPI_") else "P"
    return KPInstance(name=name, values=arr[:, 1], weights=arr[:, 2], capacities=[C], optimum=z,
                      optimum_is_proven=True, family="pisinger-hard", klass=klass)


# ════════════════════════════════════════════════════════════════════════════
#  Caractéristiques d'instance phi(I)
# ════════════════════════════════════════════════════════════════════════════

def instance_features(inst: KPInstance) -> dict:
    """Descripteurs statistiques de l'instance (cf. BRAINSTORMINGS/gap1-hypothese-knapsack.md)."""
    from .heuristics import dantzig_bound, greedy_solution
    v = inst.values
    w = inst.weights.sum(axis=0)
    ratio = inst.pseudo_utility()
    corr = float(np.corrcoef(v, w)[0, 1]) if np.std(v) > 0 and np.std(w) > 0 else 1.0
    ub = dantzig_bound(inst)
    g = inst.value(greedy_solution(inst))
    return {
        "n": inst.n, "m": inst.m,
        "tightness": float(np.mean(inst.capacities / np.maximum(inst.weights.sum(axis=1), 1e-12))),
        "corr_vw": corr,
        "cv_ratio": float(np.std(ratio) / max(np.mean(ratio), 1e-12)),
        "cv_w": float(np.std(w) / max(np.mean(w), 1e-12)),
        "cv_v": float(np.std(v) / max(np.mean(v), 1e-12)),
        "greedy_gap_ub": float((ub - g) / max(ub, 1e-12)),   # écart glouton / borne de Dantzig
    }


# ════════════════════════════════════════════════════════════════════════════
#  Chargement des jeux de données du projet
# ════════════════════════════════════════════════════════════════════════════

def datasets_root() -> str:
    """Dossier des jeux de données : variable RLGA_DATA_DIR, sinon data/ du projet (embarqué pour le
    déploiement), sinon le dossier DATASETS du dépôt de recherche."""
    env = os.environ.get("RLGA_DATA_DIR")
    if env and os.path.isdir(env):
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    local = os.path.normpath(os.path.join(here, "..", "data"))
    if os.path.isdir(os.path.join(local, "instances_01_KP")):
        return local
    return os.path.normpath(os.path.join(here, "..", "..", "DATASETS", "DATASETS (KP)"))


def load_kp01_large_scale(max_n: int = 2000) -> list[KPInstance]:
    base = os.path.join(datasets_root(), "instances_01_KP")
    out = []
    for fn in sorted(os.listdir(os.path.join(base, "large_scale"))):
        n = int(fn.split("_")[2])
        if n <= max_n:
            out.append(read_kp01_simple(os.path.join(base, "large_scale", fn),
                                        os.path.join(base, "large_scale-optimum", fn)))
    out.sort(key=lambda i: (i.klass, i.n))
    return out


def load_kp01_low_dim() -> list[KPInstance]:
    base = os.path.join(datasets_root(), "instances_01_KP")
    return [read_kp01_simple(os.path.join(base, "low-dimensional", fn),
                             os.path.join(base, "low-dimensional-optimum", fn), klass="LD")
            for fn in sorted(os.listdir(os.path.join(base, "low-dimensional")))]


def load_jooken() -> list[KPInstance]:
    base = os.path.join(datasets_root(), "JOOKEN_HARD")
    opts = {}
    with open(os.path.join(base, "subset.csv")) as f:
        for line in f:
            name, o = line.strip().split(",")
            opts[name] = float(o)
    out = [read_jooken(os.path.join(base, "problemInstances", k), v) for k, v in sorted(opts.items())]
    out.sort(key=lambda i: (i.n, i.name))
    return out


def load_orlib_mkp(subdir: str, pattern: str = "") -> list[KPInstance]:
    """subdir ex. 'chubeas/OR5x100', 'sac94/weing', 'gk'. Lit directement dans l'archive zip."""
    import zipfile, tempfile
    zpath = os.path.join(datasets_root(), "All-MKP-Instances.zip")
    out = []
    with zipfile.ZipFile(zpath) as z:
        for info in sorted(z.infolist(), key=lambda i: i.filename):
            fn = info.filename
            if fn.startswith(subdir + "/") and fn.endswith(".dat") and pattern in fn:
                if fn.endswith(subdir.split("/")[-1] + ".dat"):
                    continue  # fichier agrégé (toutes instances) : ignoré
                with tempfile.NamedTemporaryFile("wb", suffix=".dat", delete=False) as tmp:
                    tmp.write(z.read(fn))
                inst = read_orlib_mkp(tmp.name)
                os.unlink(tmp.name)
                inst.name = os.path.basename(fn)
                inst.meta["subset"] = subdir
                out.append(inst)
    return out
