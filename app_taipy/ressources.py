# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Encadrement des ressources des calculs lourds de la plateforme.

Chaque calcul (comparaison, cas d'usage, hypothèses, scénario) :
  1. est borné : les paramètres sont ramenés dans des intervalles sûrs (taille, exécutions, générations, PLNE) ;
  2. est estimé avant son lancement : au-delà d'une durée estimée maximale, il est refusé avec un conseil ;
  3. attend son tour dans une file globale : au plus `max_calculs` calculs simultanés pour tout le serveur,
     quel que soit le nombre de visiteurs ou d'onglets ;
  4. s'exécute dans un processus fils (worker.py), et non dans un fil du serveur web : l'interface reste
     réactive, et le processus peut être arrêté à tout moment ;
  5. est limité dans ce processus : mémoire virtuelle, temps processeur, priorité basse (nice) et un seul
     fil de calcul pour les bibliothèques numériques ; une durée réelle maximale met fin au calcul.
Les méthodes sont exécutées l'une après l'autre dans le processus fils, et les résultats ne sont rassemblés
qu'à la fin pour l'interprétation.

Tous les seuils se règlent par variables d'environnement (voir LIMITES).
"""
from __future__ import annotations

import os
import pickle
import subprocess
import sys
import threading
from dataclasses import dataclass

APP = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.join(APP, "worker.py")


def _env(nom: str, defaut: float) -> float:
    try:
        return float(os.environ.get(nom, defaut))
    except ValueError:
        return float(defaut)


@dataclass(frozen=True)
class Limites:
    max_calculs: int = int(_env("RLGA_MAX_CALCULS", 1))           # calculs simultanés (tout le serveur)
    # mémoire virtuelle (espace d'adressage) d'un calcul ; le chargement de NumPy et SciPy en réserve à lui seul
    # près de 1 Go, alors que la mémoire réellement occupée reste de 100 à 250 Mo (rapport de performance)
    memoire_mo: int = int(_env("RLGA_MEMOIRE_MO", 2048))
    duree_max_s: float = _env("RLGA_DUREE_MAX_S", 900)             # durée réelle maximale d'un calcul
    attente_max_s: float = _env("RLGA_ATTENTE_MAX_S", 300)         # attente maximale dans la file
    estimation_max_s: float = _env("RLGA_ESTIMATION_MAX_S", 600)   # durée estimée au-delà de laquelle on refuse
    priorite: int = int(_env("RLGA_PRIORITE", 10))                 # nice du processus de calcul (0 à 19)
    facteur_machine: float = _env("RLGA_FACTEUR_MACHINE", 1.0)     # > 1 sur une machine plus lente
    # bornes des paramètres (défense en profondeur : l'interface les respecte déjà)
    n_max: int = int(_env("RLGA_N_MAX", 5000))                     # objets au plus (2 000 sur un hébergeur à 512 Mo)
    executions_max: int = int(_env("RLGA_EXECUTIONS_MAX", 10))
    executions_hyp_max: int = 20
    generations_max: int = int(_env("RLGA_GENERATIONS_MAX", 500))
    plne_max_s: float = 120.0


LIMITES = Limites()
MEMOIRE_MIN_MO = 1024        # en deçà, les bibliothèques numériques ne peuvent même pas être chargées


class CalculRefuse(Exception):
    """Le calcul n'est pas lancé : son coût estimé dépasse le budget autorisé."""


class CalculInterrompu(Exception):
    """Le calcul a été lancé mais n'a pas abouti (file pleine, durée, mémoire, arrêt demandé, erreur)."""


# ── Bornes et estimation du coût ─────────────────────────────────────────────

def borner(valeur, bas, haut):
    return max(bas, min(haut, valeur))


# Coefficients mesurés sur un portable à 8 cœurs (septembre 2026), un seul fil de calcul :
# AG : ≈ 1,1e-5 s par (exécution × génération × objet) pour une population de 100 ;
# PD : ≈ 4e-9 s par cellule n·C ; PLNE : au plus sa limite de temps.
C_AG, C_PD, SURCOUT_FIXE = 1.1e-5, 4e-9, 2.0
CLES_AG = {"GA", "GA-RAND", "GA-UCB", "GA-QL", "GA-QL-T", "GA-FIX-UX+BF3"}


def estimer(n: int, m: int, cles: list[str], executions: int, generations: int, plne_s: float,
            cellules_pd: float | None = None) -> float:
    """Durée estimée (s) d'une comparaison, méthodes exécutées l'une après l'autre."""
    t = SURCOUT_FIXE
    n_ag = sum(1 for k in cles if k in CLES_AG)
    t += C_AG * n_ag * executions * generations * n * (1 + 0.3 * (m - 1))
    if "DP" in cles and cellules_pd:
        t += C_PD * cellules_pd
    t *= LIMITES.facteur_machine        # calculs proportionnels à la puissance de la machine
    if "MILP" in cles:
        t += plne_s                     # la limite de la PLNE est une durée réelle : non multipliée
    return t


def cellules_pd(inst) -> float | None:
    from rlga_kp.exact import dp_feasibility
    ok, _ = dp_feasibility(inst)
    return float(inst.n) * (float(inst.capacities[0]) + 1) if ok else None


def estimer_comparaison(inst, cles, executions, generations, plne_s) -> float:
    return estimer(inst.n, inst.m, cles, executions, generations, plne_s, cellules_pd(inst))


def estimer_hypotheses(inst, executions, generations, plne_s: float = 60.0) -> float:
    # 5 variantes d'AG, PD, PLNE longue puis PLNE au budget de l'AG, glouton
    t = estimer(inst.n, inst.m, ["GA"] * 5 + ["DP", "MILP"], executions, generations, plne_s, cellules_pd(inst))
    return t + plne_s / 2 + 5.0 * LIMITES.facteur_machine   # + seconde PLNE, limitée au temps de l'AG


def verifier_budget(estimation_s: float) -> None:
    if estimation_s > LIMITES.estimation_max_s:
        raise CalculRefuse(
            f"Calcul trop lourd : durée estimée ≈ {duree_lisible(estimation_s)}, pour un maximum autorisé de "
            f"{duree_lisible(LIMITES.estimation_max_s)}. Réduisez le nombre d'exécutions, de générations ou de "
            "méthodes, ou choisissez une instance plus petite.")


def duree_lisible(s: float) -> str:
    s = int(round(s))
    if s < 60:
        return f"{s} s"
    m, s = divmod(s, 60)
    return f"{m} min {s:02d} s" if m < 60 else f"{m // 60} h {m % 60:02d} min"


# ── Exécution encadrée dans un processus fils ────────────────────────────────

_FILE = threading.BoundedSemaphore(max(1, LIMITES.max_calculs))
_VERROU = threading.Lock()
_EN_COURS: dict[str, subprocess.Popen] = {}   # jeton (session) → processus de calcul
_ARRETS: set[str] = set()
_ATTENTE = 0


def _limiter_processus():  # exécuté dans le processus fils, avant le calcul (POSIX)
    import resource
    octets = max(MEMOIRE_MIN_MO, LIMITES.memoire_mo) * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (octets, octets))
    cpu = int(LIMITES.duree_max_s) + 30
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 5))
    cible = max(0, min(19, LIMITES.priorite))
    os.nice(max(0, cible - os.nice(0)))          # priorité absolue (jamais plus prioritaire que le serveur)


def _environnement() -> dict:
    env = dict(os.environ)
    for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[v] = "1"
    env.setdefault("TZ", "Indian/Antananarivo")
    return env


def etat_file() -> dict:
    with _VERROU:
        return {"en_cours": len(_EN_COURS), "en_attente": _ATTENTE, "max": LIMITES.max_calculs}


def arreter(jeton: str) -> bool:
    """Arrête le calcul de la session `jeton` (s'il existe). Retourne True si un calcul a été arrêté."""
    with _VERROU:
        proc = _EN_COURS.get(jeton)
        if proc is None:
            _ARRETS.add(jeton)          # arrêt demandé pendant l'attente : le calcul ne démarrera pas
            return False
        _ARRETS.add(jeton)
    proc.kill()
    return True


def executer(fonction: str, *args, jeton: str = "local", duree_max_s: float | None = None, **kwargs):
    """Exécute backend.<fonction>(*args, **kwargs) dans un processus fils encadré et renvoie son résultat."""
    global _ATTENTE
    duree = duree_max_s or LIMITES.duree_max_s
    with _VERROU:
        _ARRETS.discard(jeton)
        _ATTENTE += 1
    try:
        obtenu = _FILE.acquire(timeout=LIMITES.attente_max_s)
    finally:
        with _VERROU:
            _ATTENTE -= 1
    if not obtenu:
        raise CalculInterrompu("Le serveur est occupé par d'autres calculs ; réessayez dans quelques minutes.")
    try:
        with _VERROU:
            if jeton in _ARRETS:
                raise CalculInterrompu("Calcul arrêté à votre demande.")
        proc = subprocess.Popen([sys.executable, WORKER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, cwd=APP, env=_environnement(),
                                preexec_fn=_limiter_processus if os.name == "posix" else None)
        with _VERROU:
            _EN_COURS[jeton] = proc
        try:
            sortie, erreurs = proc.communicate(pickle.dumps((fonction, args, kwargs)), timeout=duree)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise CalculInterrompu(f"Durée maximale dépassée ({duree_lisible(duree)}) : calcul arrêté. "
                                   "Réduisez la taille du calcul.") from None
        finally:
            with _VERROU:
                _EN_COURS.pop(jeton, None)
                arret = jeton in _ARRETS
                _ARRETS.discard(jeton)
        if arret:
            raise CalculInterrompu("Calcul arrêté à votre demande.")
        if proc.returncode != 0 or not sortie:
            detail = erreurs.decode("utf-8", "replace").strip().splitlines()[-1:] or ["fin anormale"]
            if proc.returncode in (-9, -24, 137, 152):   # SIGKILL / SIGXCPU
                raise CalculInterrompu("Limite de temps processeur atteinte : calcul arrêté.")
            raise CalculInterrompu(f"Le calcul s'est terminé anormalement ({detail[0]}).")
        statut, valeur = pickle.loads(sortie)
        if statut == "memoire":
            raise CalculInterrompu(f"Mémoire insuffisante : le calcul dépasse la limite de {LIMITES.memoire_mo} Mo. "
                                   "Choisissez une instance plus petite ou moins de méthodes.")
        if statut == "erreur":
            raise CalculInterrompu(f"Erreur pendant le calcul : {valeur}")
        return valeur
    finally:
        _FILE.release()


class Echec:
    """Résultat d'un calcul refusé ou interrompu, transmis à l'interface à la place d'une exception."""

    def __init__(self, message: str):
        self.message = message


def protege(fonction: str, *args, jeton: str = "local", **kwargs):
    """Comme executer(), mais renvoie un Echec au lieu de lever une exception (usage dans les fils de l'interface)."""
    try:
        return executer(fonction, *args, jeton=jeton, **kwargs)
    except (CalculRefuse, CalculInterrompu) as e:
        return Echec(str(e))
    except Exception as e:  # noqa: BLE001 — toute autre erreur est rapportée proprement
        return Echec(f"Erreur inattendue : {e}")
