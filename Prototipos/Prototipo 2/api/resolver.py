# -*- coding: utf-8 -*-
"""Función de Vercel: POST /api/resolver (resuelve una instancia con el método pedido).

La lógica está en servidor.py (carpeta de arriba), la misma que usa el servidor local.
En Vercel cada resolución se limita a 240 s (la función se corta a los 300 s; ver vercel.json).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servidor import ManejadorVercel  # noqa: E402


class handler(ManejadorVercel):  # noqa: N801 — Vercel busca una clase llamada 'handler'
    ruta_fija = '/api/resolver'
