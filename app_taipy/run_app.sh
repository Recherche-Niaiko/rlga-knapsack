#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
# Lance l'application Taipy (http://127.0.0.1:5000). Variables : PORT, NO_BROWSER=1
cd "$(dirname "$0")"
export TZ=Indian/Antananarivo OPENBLAS_NUM_THREADS=1
exec ../.venv/bin/python main.py
