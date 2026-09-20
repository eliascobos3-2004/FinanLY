from __future__ import annotations

import datetime

import flet as ft

from ui.screens.base_screen import BaseScreen


class TransactionsScreen(BaseScreen):
    def render(self):
        accounts = self.db.list_accounts()
        fecha_field = ft.TextField(label="Fecha", value=datetime.date.today().isoformat(), read_only=True, width=220)

        category_filter = ft.Dropdown(
            value="todos",
            width=220,
            options=[ft.DropdownOption("todos", text="Todas las categorías")] + [ft.DropdownOption(nombre, text=nombre) for nombre in self.db.list_categories()],
        )

        account_filter = ft.Dropdown(
            value="todos",
            width=220,
            options=[ft.DropdownOption("todos", text="Todas las cuentas")] + [ft.DropdownOption(str(a["id"]), text=a["nombre"]) for a in accounts],
        )

        summary_text = ft.Text("0 movimientos • Ingresos $0.00 • Gastos $0.00", color=ft.Colors.SECONDARY)
        list_view = ft.ListView(expand=True, spacing=8, auto_scroll=True)

        def apply_filters(_):
            fecha = fecha_field.value or datetime.date.today().isoformat()
            categoria = None if category_filter.value == "todos" else category_filter.value
            cuenta_id = None if account_filter.value == "todos" else int(account_filter.value)
            rows = self.db.list_transactions(categoria=categoria, cuenta_id=cuenta_id, fecha=fecha)

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
                                        ft.Icon(ft.Icons.ARROW_DOWNWARD_ROUNDED if r["tipo"] == "ingreso" else ft.Icons.ARROW_UPWARD_ROUNDED, color=ft.Colors.GREEN if r["tipo"] == "ingreso" else ft.Colors.RED),
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

        def open_date_selection(_):
            # pasar apply_filters como callback para que al seleccionar fecha se apliquen filtros
            self.app.open_date_picker(fecha_field, fecha_field.value, on_select=apply_filters)

        apply_filters(None)

        return ft.Column(
            expand=True,
            spacing=12,
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                ft.Text("Transacciones", size=28, weight=ft.FontWeight.BOLD),
                ft.FilledButton("Nueva transacción", icon=ft.Icons.ADD, on_click=lambda e: self.app.open_transaction_dialog()),
                ft.Row(
                    controls=[
                        ft.Container(
                            expand=True,
                            content=ft.Row(
                                controls=[
                                    ft.Text("Fecha", width=80),
                                    fecha_field,
                                    ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=open_date_selection),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ),
                    ],
                ),
                ft.Row(controls=[category_filter, account_filter], wrap=True),
                ft.OutlinedButton("Aplicar filtros", on_click=apply_filters),
                summary_text,
                list_view,
            ],
        )
