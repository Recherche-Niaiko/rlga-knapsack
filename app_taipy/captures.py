# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""Captures d'écran automatiques de l'application (Playwright) → results/figures/app_*.png
Usage : (application lancée sur PORT) python app_taipy/captures.py [pages...]
Variables : PORT (5000 par défaut), SUFFIX (ex. « _sombre », application lancée avec DARK_MODE=1)."""
import os, sys, time
from playwright.sync_api import sync_playwright
PORT = os.environ.get("PORT", "5000")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "figures")
pages = sys.argv[1:] or ["accueil", "instance", "comparaison", "politique", "resultats", "cas_usage", "hypotheses",
                         "scenarios", "a_propos"]
SUFFIX = os.environ.get("SUFFIX", "")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 950}, device_scale_factor=1.5)
    for name in pages:
        pg.goto(f"http://127.0.0.1:{PORT}/{name}", wait_until="networkidle")
        time.sleep(4)
        full = True
        if name == "comparaison":
            pg.get_by_role("button", name="Lancer la comparaison").click()
            pg.wait_for_function("document.body.innerText.includes('Comparaison terminée')", timeout=600000)
            time.sleep(3)
        if name == "politique":
            # Page longue (une colonne) : on capture la section de la table Q.
            pg.get_by_text("3 · Préférences de la Q-table").scroll_into_view_if_needed()
            pg.evaluate("window.scrollBy(0, -40)")
            time.sleep(2)
            full = False
        if name == "cas_usage":
            pg.get_by_text("camion_humanitaire").first.click()
            time.sleep(3)
            pg.get_by_role("button", name="Résoudre").first.click()
            pg.wait_for_function("document.body.innerText.includes('Meilleure valeur atteinte')", timeout=600000)
            time.sleep(3)
        if name == "hypotheses":
            pg.get_by_text("camion_humanitaire").first.click()
            time.sleep(1)
            pg.get_by_role("button", name="Vérifier les quatre hypothèses").click()
            pg.wait_for_function("document.body.innerText.includes('Vérification terminée')", timeout=600000)
            time.sleep(3)
        if name == "scenarios":
            if "Exécuté —" not in pg.evaluate("document.body.innerText"):
                pg.get_by_role("button", name="Nouveau scénario").click()
                time.sleep(2)
                pg.get_by_role("button", name="Exécuter le scénario").click()
                pg.wait_for_function("document.body.innerText.includes('Exécuté —')", timeout=600000)
                time.sleep(3)
        pg.screenshot(path=os.path.join(OUT, f"app_{name}{SUFFIX}.png"), full_page=full)
        print("capture", name)
    b.close()
