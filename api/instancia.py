# -*- coding: utf-8 -*-
"""Función de Vercel: GET /api/instancia (instancia original que edita la pestaña Edición).

La lógica está en 'Prototipos/Prototipo 2/servidor.py', la misma que usa el servidor local.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Prototipos', 'Prototipo 2'))

from servidor import ManejadorVercel  # noqa: E402


class handler(ManejadorVercel):  # noqa: N801 — Vercel busca una clase llamada 'handler'
    ruta_fija = '/api/instancia'
