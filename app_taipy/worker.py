# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""
Processus de calcul de la plateforme (lancé par ressources.executer).

Lit sur l'entrée standard un triplet picklé (nom de fonction de backend, arguments, arguments nommés),
exécute la fonction et écrit sur la sortie standard un couple picklé (statut, valeur) :
("ok", résultat), ("memoire", message) ou ("erreur", message).
Les limites (mémoire, temps processeur, priorité) sont posées par le processus parent avant le lancement.
"""
import os
import pickle
import sys

os.environ.setdefault("TZ", "Indian/Antananarivo")
APP = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [APP, os.path.dirname(APP)]   # backend et paquet rlga_kp (nécessaires au dépicklage)


def main() -> None:
    fonction, args, kwargs = pickle.loads(sys.stdin.buffer.read())
    try:
        import backend
        statut, valeur = "ok", getattr(backend, fonction)(*args, **kwargs)
    except MemoryError:
        statut, valeur = "memoire", "mémoire insuffisante"
    except Exception as e:  # noqa: BLE001
        statut, valeur = "erreur", f"{type(e).__name__} : {e}"
    sys.stdout.buffer.write(pickle.dumps((statut, valeur)))
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
