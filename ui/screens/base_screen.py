from __future__ import annotations

import flet as ft


class BaseScreen:
    """Clase base para todas las pantallas."""

    def __init__(self, app):
        self.app = app
        self.db = app.db
        self.finance = app.finance
        self.page = app.page

    def render(self):
        raise NotImplementedError("Cada pantalla debe implementar render().")
