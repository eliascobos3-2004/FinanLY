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
                                        ft.Text(cuenta["icono"], size=28),
                                        ft.Text(cuenta["nombre"], size=22, weight=ft.FontWeight.BOLD),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(f"Saldo actual: {self.finance.money(self.db.get_account_balance(cuenta['id']))}", size=18),
                                ft.Text(f"Saldo inicial: {self.finance.money(float(cuenta['saldo_inicial']))}", color=ft.Colors.SECONDARY),
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
