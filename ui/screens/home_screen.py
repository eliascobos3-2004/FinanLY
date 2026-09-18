from __future__ import annotations

import datetime

import flet as ft

from ui.screens.base_screen import BaseScreen


class HomeScreen(BaseScreen):
    def render(self):
        resumen = self.db.get_dashboard_summary()
        hoy = datetime.date.today()
        trans_hoy = self.db.list_transactions(mes=hoy.strftime("%Y-%m"))

        cards = ft.Row(
            wrap=True,
            spacing=12,
            run_spacing=12,
            controls=[
                ft.Container(
                    width=190,
                    padding=18,
                    border_radius=16,
                    bgcolor="#101827",
                    content=ft.Column(
                        controls=[
                            ft.Text("Saldo total", size=13, color=ft.Colors.SECONDARY),
                            ft.Text(self.finance.money(resumen["saldo_total"]), size=25, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ],
                        spacing=8,
                    ),
                ),
                ft.Container(
                    width=190,
                    padding=18,
                    border_radius=16,
                    bgcolor="#101827",
                    content=ft.Column(
                        controls=[
                            ft.Text("Ingresos del mes", size=13, color=ft.Colors.SECONDARY),
                            ft.Text(self.finance.money(resumen["ingresos_mes"]), size=22, weight=ft.FontWeight.W_600, color=ft.Colors.GREEN),
                        ],
                        spacing=8,
                    ),
                ),
                ft.Container(
                    width=190,
                    padding=18,
                    border_radius=16,
                    bgcolor="#101827",
                    content=ft.Column(
                        controls=[
                            ft.Text("Gastos del mes", size=13, color=ft.Colors.SECONDARY),
                            ft.Text(self.finance.money(resumen["gastos_mes"]), size=22, weight=ft.FontWeight.W_600, color=ft.Colors.RED),
                        ],
                        spacing=8,
                    ),
                ),
            ],
        )

        if trans_hoy:
            today_list = [
                ft.Container(
                    padding=12,
                    border_radius=12,
                    bgcolor="#101827",
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ARROW_DOWNWARD_ROUNDED if tx["tipo"] == "ingreso" else ft.Icons.ARROW_UPWARD_ROUNDED, color=ft.Colors.GREEN if tx["tipo"] == "ingreso" else ft.Colors.RED),
                            ft.Column(
                                expand=True,
                                controls=[
                                    ft.Text(f"{tx['categoria']} • {tx['tipo'].title()}", weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                                    ft.Text(f"{tx['fecha']} • {tx['nombre_cuenta']}", color=ft.Colors.SECONDARY),
                                ],
                            ),
                            ft.Text(self.finance.money(tx["monto"]), weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN if tx["tipo"] == "ingreso" else ft.Colors.RED),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                )
                for tx in trans_hoy[:5]
            ]
        else:
            today_list = [ft.Text("Hoy no hay transacciones.", color=ft.Colors.SECONDARY)]

        def open_today_transactions(_):
            dialog = self.app._build_modal_container(
                "Transacciones de hoy",
                [
                    ft.Text(f"Fecha: {hoy.isoformat()}", color=ft.Colors.SECONDARY),
                    ft.Container(
                        padding=8,
                        content=ft.Column(controls=today_list if trans_hoy else [ft.Text("No hay movimientos hoy.", color=ft.Colors.SECONDARY)])
                    )
                ],
                width=430,
            )
            self.app.open_dialog(dialog)

        return ft.Column(
            expand=True,
            spacing=16,
            controls=[
                ft.Text("Inicio / Balance", size=34, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                cards,
                ft.Row(
                    controls=[
                        ft.Container(
                            expand=True,
                            height=54,
                            border_radius=28,
                            bgcolor="#7aa2ff",
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(ft.Icons.ADD, color=ft.Colors.WHITE),
                                    ft.Text("Ingreso", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                                ],
                            ),
                            ink=True,
                            on_click=lambda e, tipo="ingreso": self.app.open_quick_transaction_dialog(tipo=tipo),
                        ),
                        ft.Container(
                            expand=True,
                            height=54,
                            border_radius=28,
                            border=ft.Border.all(1, "#374151"),
                            bgcolor="#111827",
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(ft.Icons.REMOVE, color=ft.Colors.WHITE),
                                    ft.Text("Gasto", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                                ],
                            ),
                            ink=True,
                            on_click=lambda e, tipo="gasto": self.app.open_quick_transaction_dialog(tipo=tipo),
                        ),
                    ],
                    spacing=12,
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.TextButton(
                            "Ver transacciones",
                            icon=ft.Icons.LIST_ALT,
                            on_click=open_today_transactions,
                            style=ft.ButtonStyle(color=ft.Colors.WHITE),
                        )
                    ],
                ),
                ft.Text("Últimas transacciones", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(
                    border_radius=16,
                    bgcolor="#0f172a",
                    padding=10,
                    content=ft.ListView(expand=True, spacing=10, auto_scroll=True, controls=[
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.ARROW_DOWNWARD_ROUNDED if tx["tipo"] == "ingreso" else ft.Icons.ARROW_UPWARD_ROUNDED, color=ft.Colors.GREEN if tx["tipo"] == "ingreso" else ft.Colors.RED),
                            title=ft.Text(f"{tx['categoria']} • {tx['tipo'].title()}", color=ft.Colors.WHITE),
                            subtitle=ft.Text(f"{tx['fecha']} • {tx['nombre_cuenta']}", color=ft.Colors.SECONDARY),
                            trailing=ft.Text(self.finance.money(tx["monto"]), weight=ft.FontWeight.W_600, color=ft.Colors.GREEN if tx["tipo"] == "ingreso" else ft.Colors.RED),
                        )
                        for tx in (resumen["ultimas_transacciones"] or [])
                    ]),
                ),
            ],
        )
