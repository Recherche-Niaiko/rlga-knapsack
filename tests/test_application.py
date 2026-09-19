# SPDX-License-Identifier: MIT
# Copyright (c) 2026 RALAIVAO Niaiko Michaël
"""Test d'intégration : démarrage de l'application web et temps de réponse des pages.

Lance l'application dans un processus séparé (port 5091, sans navigateur), attend qu'elle réponde,
puis mesure le temps de réponse de la page d'accueil. Ignoré si RLGA_SANS_APPLI=1 ou si le port est pris.
"""
import os
import socket
import statistics
import subprocess
import sys
import time
import unittest
import urllib.request

import _commun

PORT = 5091


def port_libre(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


@unittest.skipIf(os.environ.get("RLGA_SANS_APPLI") == "1" or not port_libre(PORT), "application non testée")
class TestApplication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env = dict(os.environ, PORT=str(PORT), NO_BROWSER="1", HOST="127.0.0.1", TZ="Indian/Antananarivo",
                   OPENBLAS_NUM_THREADS="1")
        cls.proc = subprocess.Popen([sys.executable, os.path.join(_commun.APP, "main.py")], cwd=_commun.APP, env=env,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.url = f"http://127.0.0.1:{PORT}/"
        t0, cls.demarrage = time.perf_counter(), None
        while time.perf_counter() - t0 < 120 and cls.proc.poll() is None:
            try:
                if urllib.request.urlopen(cls.url, timeout=2).status == 200:
                    cls.demarrage = time.perf_counter() - t0
                    break
            except OSError:
                time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        try:
            cls.proc.wait(15)
        except subprocess.TimeoutExpired:
            cls.proc.kill()

    def test_demarrage(self):
        self.assertIsNotNone(self.demarrage, "l'application n'a pas répondu en 120 s")
        print(f"\n  démarrage : {self.demarrage:.1f} s")

    def test_temps_de_reponse(self):
        self.assertIsNotNone(self.demarrage)
        durees = []
        for _ in range(20):
            t = time.perf_counter()
            with urllib.request.urlopen(self.url, timeout=10) as r:
                self.assertEqual(r.status, 200)
                r.read()
            durees.append(time.perf_counter() - t)
        med = statistics.median(durees)
        print(f"\n  temps de réponse médian : {1000 * med:.0f} ms (max {1000 * max(durees):.0f} ms)")
        self.assertLess(med, 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
