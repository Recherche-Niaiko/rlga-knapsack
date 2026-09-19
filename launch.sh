#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
# Lance les campagnes expérimentales en arrière-plan (journal : results/run_all.stdout)
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TZ=Indian/Antananarivo
nohup .venv/bin/python experiments/run_all.py "$@" > results/run_all.stdout 2>&1 &
echo "PID $!"
