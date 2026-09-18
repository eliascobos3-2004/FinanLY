from __future__ import annotations

import flet as ft


class Sidebar:
    """Navegación lateral con comportamiento colapsable."""

    def __init__(self, on_change, toggle_sidebar=None):
        self.extended = True
        self.width = 220
        self.collapsed_width = 84

        self.nav = ft.NavigationRail(
            selected_index=0,
            extended=True,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=self.collapsed_width,
            min_extended_width=self.width,
            bgcolor="#111827",
            elevation=0,
            on_change=on_change,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Inicio"),
                ft.NavigationRailDestination(icon=ft.Icons.RECEIPT_LONG_OUTLINED, selected_icon=ft.Icons.RECEIPT_LONG, label="Transacciones"),
                ft.NavigationRailDestination(icon=ft.Icons.WALLET_OUTLINED, selected_icon=ft.Icons.WALLET, label="Cuentas"),
                ft.NavigationRailDestination(icon=ft.Icons.INSIGHTS_OUTLINED, selected_icon=ft.Icons.INSIGHTS, label="Resumen"),
            ],
            leading=ft.IconButton(
                icon=ft.Icons.MENU,
                icon_color=ft.Colors.WHITE,
                on_click=toggle_sidebar,
                style=ft.ButtonStyle(shape=ft.CircleBorder()),
            ),
        )

        self.container = ft.Container(
            width=self.width,
            height=760,
            bgcolor="#111827",
            padding=ft.Padding(8, 12, 8, 12),
            content=self.nav,
        )

    def toggle(self):
        self.extended = not self.extended
        self.nav.extended = self.extended
        self.nav.label_type = ft.NavigationRailLabelType.ALL if self.extended else ft.NavigationRailLabelType.NONE
        self.container.width = self.width if self.extended else self.collapsed_width
        return self.container
