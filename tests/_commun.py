# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""Réglages communs aux tests : chemins, fuseau horaire et un seul fil de calcul numérique."""
import os
import sys

os.environ.setdefault("TZ", "Indian/Antananarivo")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app_taipy")
for p in (ROOT, APP):
    if p not in sys.path:
        sys.path.insert(0, p)
QTABLE = os.path.join(ROOT, "results", "qtables", "Q_OOD.json")
