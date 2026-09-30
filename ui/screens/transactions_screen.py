from __future__ import annotations

import datetime

import flet as ft

from ui.screens.base_screen import BaseScreen


class TransactionsScreen(BaseScreen):
    def render(self):
        accounts = self.db.list_accounts()
        today = datetime.date.today()

        selected_month = f"{today.year:04d}-{today.month:02d}"
        selected_category = "todos"
        selected_account = "todos"

        summary_text = ft.Text("0 movimientos • Ingresos $0.00 • Gastos $0.00", color=ft.Colors.SECONDARY)
        list_view = ft.ListView(expand=True, spacing=8, auto_scroll=True)

        def build_filter_dialog():
            month_field = ft.Dropdown(
                value=selected_month,
                width=180,
                options=[
                    ft.DropdownOption(f"{today.year:04d}-{m:02d}", text=datetime.date(today.year, m, 1).strftime("%B %Y"))
                    for m in range(1, 13)
                ],
            )
            category_field = ft.Dropdown(
                value=selected_category,
                width=220,
                options=[ft.DropdownOption("todos", text="Todas las categorías")] + [ft.DropdownOption(nombre, text=nombre) for nombre in self.db.list_categories()],
            )
            account_field = ft.Dropdown(
                value=selected_account,
                width=220,
                options=[ft.DropdownOption("todos", text="Todas las cuentas")] + [ft.DropdownOption(str(a["id"]), text=a["nombre"]) for a in accounts],
            )

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Filtrar movimientos", size=22, weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    width=420,
                    padding=12,
                    content=ft.Column(
                        spacing=16,
                        controls=[
                            ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Text("Mes", color=ft.Colors.SECONDARY),
                                    month_field,
                                ],
                            ),
                            ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Text("Categoría", color=ft.Colors.SECONDARY),
                                    category_field,
                                ],
                            ),
                            ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Text("Cuenta", color=ft.Colors.SECONDARY),
                                    account_field,
                                ],
                            ),
                        ],
                    ),
                ),
                actions=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=16,
                        controls=[
                            ft.TextButton("Cancelar", on_click=lambda e: self.app.close_dialog(dialog), style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                            ft.FilledButton(
                                "Aplicar",
                                on_click=lambda e: apply_filter_state(month_field.value, category_field.value, account_field.value, dialog),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                            ),
                        ],
                    )
                ],
            )
            return dialog

        def apply_filter_state(month_value, category_value, account_value, dialog=None):
            nonlocal selected_month, selected_category, selected_account
            selected_month = month_value or selected_month
            selected_category = category_value or selected_category
            selected_account = account_value or selected_account

            if dialog is not None:
                self.app.close_dialog(dialog)

            categoria = None if selected_category == "todos" else selected_category
            cuenta_id = None if selected_account == "todos" else int(selected_account)
            rows = self.db.list_transactions(categoria=categoria, cuenta_id=cuenta_id, mes=selected_month)

            total_ingreso = sum(float(r["monto"]) for r in rows if r["tipo"] == "ingreso")
            total_gasto = sum(float(r["monto"]) for r in rows if r["tipo"] == "gasto")
            summary_text.value = f"{len(rows)} movimientos • Ingresos ${total_ingreso:,.2f} • Gastos ${total_gasto:,.2f}"

            list_controls = []
            if rows:
                for r in rows:
                    list_controls.append(
                        ft.Card(
                            content=ft.Container(
                                padding=12,
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.ARROW_DOWNWARD_ROUNDED if r["tipo"] == "ingreso" else ft.Icons.ARROW_UPWARD_ROUNDED,
                                            color=ft.Colors.GREEN if r["tipo"] == "ingreso" else ft.Colors.RED,
                                        ),
                                        ft.Column(
                                            expand=True,
                                            controls=[
                                                ft.Text(f"{r['categoria']} • {r['tipo'].title()}", weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                                                ft.Text(f"{r['fecha']} • {r['nombre_cuenta']}", color=ft.Colors.SECONDARY),
                                                ft.Text(r["nota"] or "Sin nota", color=ft.Colors.SECONDARY),
                                            ],
                                        ),
                                        ft.Column(
                                            controls=[
                                                ft.Text(self.finance.money(r["monto"]), weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN if r["tipo"] == "ingreso" else ft.Colors.RED),
                                                ft.Row(
                                                    controls=[
                                                        ft.IconButton(ft.Icons.EDIT, on_click=lambda e, item_id=r["id"]: self.app.open_transaction_dialog(tx_id=item_id)),
                                                        ft.IconButton(ft.Icons.DELETE_OUTLINE, on_click=lambda e, item_id=r["id"]: self.app.delete_transaction(item_id)),
                                                    ]
                                                ),
                                            ]
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            )
                        )
                    )
            else:
                list_controls.append(ft.Text("No hay transacciones con esos filtros.", color=ft.Colors.SECONDARY))

            list_view.controls = list_controls
            self.page.update()

        def open_filter_modal(_):
            dialog = build_filter_dialog()
            self.app.open_dialog(dialog)

        apply_filter_state(selected_month, selected_category, selected_account)

        return ft.Column(
            expand=True,
            spacing=12,
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                ft.Text("Transacciones", size=28, weight=ft.FontWeight.BOLD),
                ft.FilledButton("Nueva transacción", icon=ft.Icons.ADD, on_click=lambda e: self.app.open_transaction_dialog()),
                ft.Row(
                    controls=[
                        ft.FilledButton("Filtrar", icon=ft.Icons.FILTER_ALT_OUTLINED, on_click=open_filter_modal),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                summary_text,
                ft.Container(
                    expand=True,
                    height=360,
                    border_radius=16,
                    padding=10,
                    bgcolor="#0f172a",
                    content=list_view,
                ),
            ],
        )
