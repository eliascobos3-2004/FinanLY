from __future__ import annotations

import flet as ft

from ui.screens.base_screen import BaseScreen


class AccountsScreen(BaseScreen):
    def render(self):
        cuentas = self.db.list_accounts()
        cards = []
        if not cuentas:
            cards = [ft.Text("No hay cuentas todavía. Crea tu primera cuenta.", color=ft.Colors.SECONDARY)]
        else:
            cards = [
                ft.Card(
                    content=ft.Container(
                        padding=18,
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(cuenta["icono"], size=28, color=ft.Colors.WHITE),
                                        ft.Text(cuenta["nombre"], size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(f"Saldo actual: {self.finance.money(self.db.get_account_balance(cuenta['id']))}", size=18, color=ft.Colors.WHITE),
                                ft.Text(f"Saldo inicial: {self.finance.money(float(cuenta['saldo_inicial']))}", color=ft.Colors.SECONDARY),
                                # Gráfico comparativo: barra inicial (full) y barra actual (proporcional)
                                self._build_account_progress(cuenta),
                                ft.Row(
                                    controls=[
                                        ft.TextButton("Editar", on_click=lambda e, item_id=cuenta["id"]: self.app.open_account_dialog(account_id=item_id)),
                                        ft.TextButton("Eliminar", on_click=lambda e, item_id=cuenta["id"]: self.app.delete_account(item_id)),
                                    ],
                                ),
                            ]
                        ),
                    )
                )
                for cuenta in cuentas
            ]
        return ft.Column(
            expand=True,
            spacing=12,
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                ft.Text("Cuentas", size=28, weight=ft.FontWeight.BOLD),
                ft.FilledButton("Nueva cuenta", icon=ft.Icons.ADD, on_click=lambda e: self.app.open_account_dialog()),
                ft.ListView(expand=True, spacing=10, controls=cards),
            ],
        )

    def _build_account_progress(self, cuenta):
        try:
            inicial = float(cuenta["saldo_inicial"]) if "saldo_inicial" in cuenta.keys() else 0.0
        except Exception:
            inicial = 0.0
        actual = float(self.db.get_account_balance(cuenta["id"]))
        width = 320

        # evitar división por cero
        pct = (actual / inicial) if inicial > 0 else 0
        pct = max(0.0, min(1.0, pct))
        # Dibujar una sola barra compuesta: fondo = inicial, relleno = actual proporcional
        # Si inicial == 0, mostrar barra de fondo tenue y etiqueta con 0$
        bg_color = "#6b7280"  # gris para inicial
        fill_color = "#3b82f6"  # azul para actual

        actual_fill_width = max(2, int(width * pct)) if inicial > 0 else 2

        bar = ft.Container(
            width=width,
            height=18,
            border_radius=8,
            content=ft.Stack(
                controls=[
                    # capa de fondo que representa el total inicial
                    ft.Container(width=width, height=18, border_radius=8, bgcolor=bg_color),
                    # capa de relleno que muestra el estado actual
                    ft.Container(width=actual_fill_width, height=18, border_radius=8, bgcolor=fill_color),
                    # etiqueta de monto dentro de la barra (alineada a la izquierda)
                    ft.Container(padding=ft.Padding(left=8), content=ft.Text(f"{self.finance.money(actual)} ({int(pct*100)}%)", size=11, color=ft.Colors.WHITE)),
                ]
            ),
        )

        return ft.Column(controls=[ft.Text("Inicial vs Actual", size=12, color=ft.Colors.SECONDARY), bar], spacing=6)
