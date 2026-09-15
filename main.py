"""
FinanLY - PASO 2
===============

Este archivo define la base de la aplicación Flet para FinanLY:
- tema visual Material 3 estilizado para móvil
- navegación con NavigationBar de 4 pantallas
- estado global ligero para compartir datos con la UI
- estructura base para que luego se añadan las pantallas reales de inicio,
  transacciones, cuentas y gráficas.

Ejecución:
    python main.py
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

import flet as ft

from db import DatabaseManager


@dataclass
class AppState:
    """Estado global ligero y reutilizable por todas las pantallas.

    Mantiene la conexión a SQLite, la pantalla activa y los datos del mes actual.
    Se usa para evitar pasar demasiados parámetros entre componentes.
    """

    db: DatabaseManager
    selected_index: int = 0
    current_month: str = field(default_factory=lambda: "2026-09")
    current_screen: str = "inicio"
    page: Optional[ft.Page] = None

    def set_page(self, page: ft.Page) -> None:
        self.page = page

    def change_tab(self, index: int) -> None:
        """Actualiza la pantalla activa según la selección de NavigationBar."""
        self.selected_index = index
        self.current_screen = {
            0: "inicio",
            1: "transacciones",
            2: "cuentas",
            3: "graficas",
        }.get(index, "inicio")

        if self.page is not None:
            self.page.update()


class FinanLYApp:
    """Contenedor principal de la app.

    Tiene la responsabilidad de:
    - configurar la temática general
    - montar el NavigationBar
    - renderizar la pantalla según el índice actual
    - mantener un flujo limpio para continuar con los pasos 3, 4 y 5.
    """

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.db = DatabaseManager("finanly.db")
        self.db.seed_demo_data()  # Datos demo para comprobar flujos rápidamente.

        self.state = AppState(db=self.db)
        self.state.set_page(page)

        self.page.title = "FinanLY"
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.padding = 0

        self.page.theme = ft.Theme(
            color_scheme_seed="#3B82F6",
            use_material3=True,
        )

        # Configuración rápida y ligera para apariencia moderna.
        self.page.bgcolor = ft.colors.SURFACE
        self.page.theme_mode = ft.ThemeMode.SYSTEM

        self.content = ft.Container(
            expand=True,
            padding=ft.padding.only(left=16, right=16, top=16, bottom=8),
        )

        self.navigation = ft.NavigationBar(
            selected_index=0,
            on_change=self.on_nav_change,
            destinations=[
                ft.NavigationDestination(icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="Inicio"),
                ft.NavigationDestination(icon=ft.icons.RECEIPT_LONG_OUTLINED, selected_icon=ft.icons.RECEIPT_LONG, label="Transacciones"),
                ft.NavigationDestination(icon=ft.icons.WALLET_OUTLINED, selected_icon=ft.icons.WALLET, label="Cuentas"),
                ft.NavigationDestination(icon=ft.icons.INSIGHTS_OUTLINED, selected_icon=ft.icons.INSIGHTS, label="Gráficas"),
            ],
        )

        self.root = ft.Column(
            expand=True,
            controls=[
                self.content,
                ft.Divider(height=1),
                self.navigation,
            ],
        )

        self.page.add(self.root)
        self.render_screen()

    def on_nav_change(self, e: ft.ControlEvent) -> None:
        """Manejador del cambio de pantalla en NavigationBar."""
        self.state.change_tab(int(e.control.selected_index))
        self.render_screen()

    def render_screen(self) -> None:
        """Renderea la pantalla según el estado actual."""
        index = self.state.selected_index
        self.navigation.selected_index = index

        screen_map: Dict[int, Callable[[], ft.Control]] = {
            0: self.build_home_screen,
            1: self.build_transactions_screen,
            2: self.build_accounts_screen,
            3: self.build_graphics_screen,
        }

        builder = screen_map.get(index, self.build_home_screen)
        self.content.content = builder()
        self.page.update()

    def _money(self, value: float) -> str:
        return f"${value:,.2f}"

    def open_quick_transaction_dialog(self, e: Optional[ft.ControlEvent] = None) -> None:
        """Abre un diálogo rápido para registrar un ingreso o gasto."""
        accounts = self.db.list_accounts()

        if not accounts:
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Sin cuentas"),
                content=ft.Text("Crea al menos una cuenta antes de registrar transacciones."),
                actions=[
                    ft.TextButton("Aceptar", on_click=lambda _: self.page.close(dialog)),
                ],
            )
            self.page.dialog = dialog
            self.page.open(dialog)
            return

        self.quick_type = ft.Dropdown(
            value="gasto",
            width=170,
            options=[
                ft.DropdownOption("gasto", text="Gasto"),
                ft.DropdownOption("ingreso", text="Ingreso"),
            ],
        )
        self.quick_category = ft.TextField(label="Categoría", value="General")
        self.quick_account = ft.Dropdown(
            value=str(accounts[0]["id"]),
            width=220,
            options=[
                ft.DropdownOption(str(cuenta["id"]), text=cuenta["nombre"])
                for cuenta in accounts
            ],
        )
        self.quick_amount = ft.TextField(label="Monto", keyboard_type=ft.KeyboardType.NUMBER)
        self.quick_note = ft.TextField(label="Nota")
        self.quick_date = ft.TextField(
            label="Fecha",
            value=datetime.date.today().isoformat(),
            hint_text="YYYY-MM-DD",
        )
        self.quick_error = ft.Text("", color=ft.colors.ERROR)

        def close_dialog(_):
            self.page.close(dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Registrar movimiento"),
            content=ft.Container(
                width=360,
                content=ft.Column(
                    tight=True,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Tipo"),
                                self.quick_type,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        self.quick_category,
                        ft.Row(
                            controls=[
                                ft.Text("Cuenta"),
                                self.quick_account,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        self.quick_amount,
                        self.quick_date,
                        self.quick_note,
                        self.quick_error,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.ElevatedButton("Guardar", on_click=self.save_quick_transaction),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        self.page.open(dialog)

    def save_quick_transaction(self, e: ft.ControlEvent) -> None:
        """Guarda la transacción creada desde el diálogo rápido."""
        try:
            if not self.quick_amount.value:
                raise ValueError("El monto es obligatorio.")

            monto = float(self.quick_amount.value)
            if monto <= 0:
                raise ValueError("El monto debe ser mayor que cero.")

            tipo = self.quick_type.value or "gasto"
            categoria = (self.quick_category.value or "General").strip() or "General"
            cuenta_id = int(self.quick_account.value)
            fecha = self.quick_date.value or datetime.date.today().isoformat()
            nota = self.quick_note.value or ""

            self.db.create_transaction(
                tipo=tipo,
                monto=monto,
                categoria=categoria,
                cuenta_id=cuenta_id,
                fecha=fecha,
                nota=nota,
            )

            self.page.close(self.page.dialog)
            self.render_screen()
        except Exception as exc:  # noqa: BLE001 - detalle útil para UI
            self.quick_error.value = str(exc)
            self.page.update()

    # ------------------------------------------------------------------
    # Pantallas base (placeholder funcional)
    # ------------------------------------------------------------------

    def build_home_screen(self) -> ft.Control:
        """Pantalla de Inicio / Balance con resumen financiero y acceso rápido."""
        resumen = self.db.get_dashboard_summary()

        summary_cards = ft.Row(
            controls=[
                ft.Card(
                    content=ft.Container(
                        padding=16,
                        content=ft.Column(
                            controls=[
                                ft.Text("Saldo total", size=12, color=ft.colors.SECONDARY),
                                ft.Text(self._money(resumen["saldo_total"]), size=24, weight=ft.FontWeight.BOLD),
                            ],
                        ),
                    )
                ),
                ft.Card(
                    content=ft.Container(
                        padding=16,
                        content=ft.Column(
                            controls=[
                                ft.Text("Ingresos del mes", size=12, color=ft.colors.SECONDARY),
                                ft.Text(self._money(resumen["ingresos_mes"]), size=20, weight=ft.FontWeight.W_600, color=ft.colors.GREEN),
                            ]
                        ),
                    )
                ),
                ft.Card(
                    content=ft.Container(
                        padding=16,
                        content=ft.Column(
                            controls=[
                                ft.Text("Gastos del mes", size=12, color=ft.colors.SECONDARY),
                                ft.Text(self._money(resumen["gastos_mes"]), size=20, weight=ft.FontWeight.W_600, color=ft.colors.RED),
                            ]
                        ),
                    )
                ),
            ],
            wrap=True,
        )

        latest_items = [
            ft.ListTile(
                leading=ft.Icon(
                    ft.icons.ARROW_DOWNWARD_ROUNDED if tx["tipo"] == "ingreso" else ft.icons.ARROW_UPWARD_ROUNDED,
                    color=ft.colors.GREEN if tx["tipo"] == "ingreso" else ft.colors.RED,
                ),
                title=ft.Text(f"{tx['categoria']} • {tx['tipo'].title()}"),
                subtitle=ft.Text(f"{tx['fecha']} • {tx['nombre_cuenta']}"),
                trailing=ft.Text(
                    self._money(tx["monto"]),
                    weight=ft.FontWeight.W_600,
                    color=ft.colors.GREEN if tx["tipo"] == "ingreso" else ft.colors.RED,
                ),
            )
            for tx in resumen["ultimas_transacciones"]
        ]

        home = ft.Column(
            expand=True,
            spacing=18,
            controls=[
                ft.Text("Inicio / Balance", size=28, weight=ft.FontWeight.BOLD),
                summary_cards,
                ft.Row(
                    controls=[
                        ft.ElevatedButton("Ingresar", icon=ft.icons.ADD, on_click=lambda e: self.open_quick_transaction_dialog()),
                        ft.OutlinedButton("Gasto", icon=ft.icons.REMOVE, on_click=lambda e: self.open_quick_transaction_dialog()),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
                ft.Text("Últimas transacciones", size=18, weight=ft.FontWeight.BOLD),
                ft.ListView(
                    expand=True,
                    spacing=6,
                    auto_scroll=True,
                    controls=latest_items,
                ),
            ],
        )

        fab = ft.Container(
            alignment=ft.alignment.bottom_right,
            content=ft.FloatingActionButton(
                icon=ft.icons.ADD,
                tooltip="Registrar movimiento",
                on_click=self.open_quick_transaction_dialog,
            ),
        )

        return ft.Stack(
            expand=True,
            controls=[
                home,
                fab,
            ],
        )

    def _get_month_options(self) -> list[ft.DropdownOption]:
        """Genera opciones del selector de mes usando el año actual."""
        today = datetime.date.today()
        options = [ft.DropdownOption("todos", text="Todos los meses")]
        for year in [today.year, today.year - 1]:
            for month in range(1, 13):
                if year == today.year and month > today.month:
                    continue
                label = f"{year:04d}-{month:02d}"
                options.append(ft.DropdownOption(label, text=f"{label}"))
        return options

    def _get_category_options(self) -> list[ft.DropdownOption]:
        """Devuelve las categorías base más usadas para filtros y formularios."""
        categories = [
            "Comida",
            "Transporte",
            "Servicios",
            "Sueldo",
            "Freelance",
            "Entretenimiento",
            "Salud",
            "Educación",
            "Hogar",
            "Ahorros",
            "Otros",
        ]
        return [ft.DropdownOption(cat, text=cat) for cat in categories]

    def open_transaction_dialog(self, transaction_id: Optional[int] = None) -> None:
        """Abre un diálogo de creación/edición de transacción."""
        accounts = self.db.list_accounts()
        if not accounts:
            self.page.show_snack_bar(ft.SnackBar(ft.Text("Primero crea una cuenta para registrar transacciones.")))
            return

        edit_tx = self.db.get_transaction(transaction_id) if transaction_id else None

        tipo_field = ft.Dropdown(
            value=(edit_tx["tipo"] if edit_tx else "gasto"),
            width=170,
            options=[
                ft.DropdownOption("gasto", text="Gasto"),
                ft.DropdownOption("ingreso", text="Ingreso"),
            ],
        )

        categoria_field = ft.Dropdown(
            value=(edit_tx["categoria"] if edit_tx else "Comida"),
            width=230,
            options=self._get_category_options(),
        )

        account_field = ft.Dropdown(
            value=str((edit_tx["cuenta_id"] if edit_tx else accounts[0]["id"])),
            width=230,
            options=[ft.DropdownOption(str(cuenta["id"]), text=cuenta["nombre"]) for cuenta in accounts],
        )

        amount_field = ft.TextField(
            label="Monto",
            value=(str(edit_tx["monto"]) if edit_tx else ""),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        date_field = ft.TextField(
            label="Fecha",
            value=(edit_tx["fecha"] if edit_tx else datetime.date.today().isoformat()),
            hint_text="YYYY-MM-DD",
        )
        note_field = ft.TextField(
            label="Nota",
            value=(edit_tx["nota"] if edit_tx else ""),
            multiline=True,
            min_lines=1,
            max_lines=3,
        )
        error_text = ft.Text("", color=ft.colors.ERROR)

        def close_dialog(_):
            self.page.close(dialog)

        def submit_transaction(_):
            try:
                if not amount_field.value:
                    raise ValueError("El monto es obligatorio.")
                monto = float(amount_field.value)
                if monto <= 0:
                    raise ValueError("El monto debe ser mayor que 0.")
                tipo = tipo_field.value or "gasto"
                categoria = categoria_field.value or "General"
                cuenta_id = int(account_field.value)
                fecha = date_field.value or datetime.date.today().isoformat()
                nota = note_field.value or ""

                if edit_tx is None:
                    self.db.create_transaction(tipo, monto, categoria, cuenta_id, fecha, nota)
                else:
                    self.db.update_transaction(
                        transaction_id=transaction_id,
                        tipo=tipo,
                        monto=monto,
                        categoria=categoria,
                        cuenta_id=cuenta_id,
                        fecha=fecha,
                        nota=nota,
                    )

                self.page.close(dialog)
                self.render_screen()
            except Exception as exc:  # noqa: BLE001
                error_text.value = str(exc)
                self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar transacción" if edit_tx else "Nueva transacción"),
            content=ft.Container(
                width=380,
                content=ft.Column(
                    tight=True,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Tipo"),
                                tipo_field,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text("Categoría"),
                                categoria_field,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text("Cuenta"),
                                account_field,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        amount_field,
                        date_field,
                        note_field,
                        error_text,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.ElevatedButton("Guardar", on_click=submit_transaction),
            ],
        )
        self.page.dialog = dialog
        self.page.open(dialog)

    def delete_transaction(self, transaction_id: int) -> None:
        """Elimina una transacción y actualiza la vista."""
        if self.db.delete_transaction(transaction_id):
            self.render_screen()

    def build_transactions_screen(self) -> ft.Control:
        """Pantalla de Transacciones con formulario y filtros."""
        accounts = self.db.list_accounts()
        account_options = [ft.DropdownOption("todos", text="Todas las cuentas")]
        account_options.extend(
            ft.DropdownOption(str(cuenta["id"]), text=cuenta["nombre"]) for cuenta in accounts
        )

        month_filter = ft.Dropdown(
            value="todos",
            width=170,
            options=self._get_month_options(),
        )
        category_filter = ft.Dropdown(
            value="todos",
            width=170,
            options=[ft.DropdownOption("todos", text="Todas las categorías")] + self._get_category_options(),
        )
        account_filter = ft.Dropdown(value="todos", width=200, options=account_options)

        def apply_filters(_):
            month = None if month_filter.value == "todos" else month_filter.value
            categoria = None if category_filter.value == "todos" else category_filter.value
            cuenta_id = None if account_filter.value == "todos" else int(account_filter.value)
            rows = self.db.list_transactions(categoria=categoria, cuenta_id=cuenta_id, mes=month)
            transactions_list.controls = [
                ft.Card(
                    content=ft.Container(
                        padding=12,
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.icons.ARROW_DOWNWARD_ROUNDED if tx["tipo"] == "ingreso" else ft.icons.ARROW_UPWARD_ROUNDED,
                                    color=ft.colors.GREEN if tx["tipo"] == "ingreso" else ft.colors.RED,
                                ),
                                ft.Column(
                                    expand=True,
                                    controls=[
                                        ft.Text(f"{tx['categoria']} • {tx['tipo'].title()}", weight=ft.FontWeight.W_600),
                                        ft.Text(f"{tx['fecha']} • {tx['nombre_cuenta']}"),
                                        ft.Text(tx["nota"] or "Sin nota", color=ft.colors.SECONDARY),
                                    ],
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            self._money(tx["monto"]),
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.colors.GREEN if tx["tipo"] == "ingreso" else ft.colors.RED,
                                        ),
                                        ft.Row(
                                            controls=[
                                                ft.IconButton(ft.icons.EDIT, on_click=lambda _, item_id=tx["id"]: self.open_transaction_dialog(item_id)),
                                                ft.IconButton(ft.icons.DELETE_OUTLINE, on_click=lambda _, item_id=tx["id"]: self.delete_transaction(item_id)),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    )
                )
                for tx in rows
            ]
            self.page.update()

        transactions_list = ft.ListView(expand=True, spacing=8, auto_scroll=True)
        apply_filters(None)

        return ft.Column(
            expand=True,
            spacing=12,
            controls=[
                ft.Text("Transacciones", size=28, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        ft.ElevatedButton("Nueva transacción", icon=ft.icons.ADD, on_click=lambda _: self.open_transaction_dialog()),
                    ]
                ),
                ft.Row(
                    controls=[
                        month_filter,
                        category_filter,
                        account_filter,
                    ],
                    wrap=True,
                ),
                ft.ElevatedButton("Aplicar filtros", on_click=apply_filters),
                transactions_list,
            ],
        )

    def open_account_dialog(self, account_id: Optional[int] = None) -> None:
        """Abre el diálogo para crear o editar una cuenta."""
        edit_account = self.db.get_account(account_id) if account_id else None

        name_field = ft.TextField(label="Nombre", value=(edit_account["nombre"] if edit_account else ""))
        balance_field = ft.TextField(
            label="Saldo inicial",
            value=(str(edit_account["saldo_inicial"]) if edit_account else "0"),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        icon_field = ft.TextField(label="Icono", value=(edit_account["icono"] if edit_account else "💰"))
        error_text = ft.Text("", color=ft.colors.ERROR)

        def close(_):
            self.page.close(dialog)

        def submit_account(_):
            try:
                nombre = (name_field.value or "").strip()
                if not nombre:
                    raise ValueError("El nombre de la cuenta es obligatorio.")
                saldo = float(balance_field.value or 0)
                icono = icon_field.value or "💰"

                if edit_account is None:
                    self.db.create_account(nombre, saldo, icono)
                else:
                    self.db.update_account(account_id, nombre=nombre, saldo_inicial=saldo, icono=icono)

                self.page.close(dialog)
                self.render_screen()
            except Exception as exc:  # noqa: BLE001
                error_text.value = str(exc)
                self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar cuenta" if edit_account else "Nueva cuenta"),
            content=ft.Container(
                width=360,
                content=ft.Column(
                    tight=True,
                    controls=[
                        name_field,
                        balance_field,
                        icon_field,
                        error_text,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close),
                ft.ElevatedButton("Guardar", on_click=submit_account),
            ],
        )
        self.page.dialog = dialog
        self.page.open(dialog)

    def delete_account(self, account_id: int) -> None:
        """Elimina una cuenta y sus transacciones asociadas."""
        if self.db.delete_account(account_id):
            self.render_screen()

    def build_accounts_screen(self) -> ft.Control:
        """Pantalla de Cuentas con CRUD."""
        cuentas = self.db.list_accounts()

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
                            ft.Text(f"Saldo actual: {self._money(self.db.get_account_balance(cuenta['id']))}", size=18),
                            ft.Text(f"Saldo inicial: {self._money(float(cuenta['saldo_inicial']))}", color=ft.colors.SECONDARY),
                            ft.Row(
                                controls=[
                                    ft.TextButton("Editar", on_click=lambda _, item_id=cuenta["id"]: self.open_account_dialog(item_id)),
                                    ft.TextButton("Eliminar", on_click=lambda _, item_id=cuenta["id"]: self.delete_account(item_id)),
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
            controls=[
                ft.Text("Cuentas", size=28, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton("Nueva cuenta", icon=ft.icons.ADD, on_click=lambda _: self.open_account_dialog()),
                ft.ListView(expand=True, spacing=10, controls=cards),
            ],
        )

    def build_graphics_screen(self) -> ft.Control:
        """Pantalla de Gráficas con análisis visual de gastos e ingresos.

        La versión de Flet instalada en este entorno no expone PieChart/BarChart,
        por lo que se usa un fallback nativo basado en ProgressBar, Row y Container,
        manteniendo la misma lógica funcional y sin romper la ejecución.
        """
        import datetime

        hoy = datetime.date.today()
        categorias = self.db.get_category_totals("gasto", f"{hoy.year:04d}-{hoy.month:02d}")
        comparativa = self.db.get_monthly_comparison(hoy.year)

        total_gastos = sum(float(item["total"]) for item in categorias)

        pie_sections = []
        palette = [
            ft.colors.BLUE,
            ft.colors.GREEN,
            ft.colors.ORANGE,
            ft.colors.RED,
            ft.colors.PURPLE,
            ft.colors.TEAL,
            ft.colors.YELLOW,
            ft.colors.PINK,
        ]

        if categorias:
            for idx, categoria in enumerate(categorias):
                percent = (float(categoria["total"]) / total_gastos * 100) if total_gastos else 0
                pie_sections.append(
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=14,
                                height=14,
                                border_radius=8,
                                bgcolor=palette[idx % len(palette)],
                            ),
                            ft.Text(f"{categoria['categoria']}: {self._money(float(categoria['total']))}", size=12),
                            ft.Text(f"{percent:.1f}%", size=12, color=ft.colors.SECONDARY),
                        ],
                        spacing=8,
                    )
                )
        else:
            pie_sections.append(ft.Text("Sin gastos en este mes.", color=ft.colors.SECONDARY))

        bar_rows = []
        if comparativa:
            max_value = max(
                max(float(item["ingresos"]), float(item["gastos"])) for item in comparativa
            ) or 1
            for item in comparativa:
                ingresos = float(item["ingresos"])
                gastos = float(item["gastos"])
                mes_label = item["mes"][-2:]
                bar_rows.append(
                    ft.Column(
                        controls=[
                            ft.Text(f"{item['mes']}", size=12, color=ft.colors.SECONDARY),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        width=200 * (ingresos / max_value) if max_value else 0,
                                        height=18,
                                        bgcolor=ft.colors.GREEN,
                                        border_radius=9,
                                        content=ft.Text("I", size=10, color=ft.colors.WHITE, text_align=ft.TextAlign.CENTER),
                                    ),
                                    ft.Container(
                                        width=200 * (gastos / max_value) if max_value else 0,
                                        height=18,
                                        bgcolor=ft.colors.RED,
                                        border_radius=9,
                                        content=ft.Text("G", size=10, color=ft.colors.WHITE, text_align=ft.TextAlign.CENTER),
                                    ),
                                ],
                                spacing=5,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text(f"I: {self._money(ingresos)}", size=11, color=ft.colors.GREEN),
                                    ft.Text(f"G: {self._money(gastos)}", size=11, color=ft.colors.RED),
                                ],
                                spacing=15,
                            ),
                        ],
                        spacing=4,
                    )
                )
        else:
            bar_rows.append(ft.Text("No hay datos mensuales disponibles.", color=ft.colors.SECONDARY))

        if hasattr(ft, "PieChart") and hasattr(ft, "BarChart"):
            # Si en otra versión de Flet se habilitan los gráficos nativos,
            # esta rama usa la API nativa sin romper compatibilidad.
            pie_chart = ft.PieChart(
                sections=[
                    ft.PieChartSection(
                        value=float(item["total"]),
                        title=f"{item['categoria']}",
                        color=palette[idx % len(palette)],
                        radius=80,
                    )
                    for idx, item in enumerate(categorias)
                ]
            )
            bar_chart = ft.BarChart(
                bars=[
                    ft.BarChartGroup(
                        x=idx,
                        bar_rods=[
                            ft.BarChartRod(
                                from_y=0,
                                to_y=float(item["ingresos"]),
                                color=ft.colors.GREEN,
                            ),
                            ft.BarChartRod(
                                from_y=0,
                                to_y=float(item["gastos"]),
                                color=ft.colors.RED,
                            ),
                        ],
                    )
                    for idx, item in enumerate(comparativa)
                ],
                border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
                width=400,
                height=250,
            )
            chart_body = ft.Column(
                controls=[
                    ft.Text("Distribución de gastos por categoría", size=18, weight=ft.FontWeight.BOLD),
                    pie_chart,
                    ft.Text("Ingresos vs Gastos por mes", size=18, weight=ft.FontWeight.BOLD),
                    bar_chart,
                ],
                spacing=18,
            )
        else:
            chart_body = ft.Column(
                controls=[
                    ft.Card(
                        content=ft.Container(
                            padding=16,
                            content=ft.Column(
                                controls=[
                                    ft.Text("Distribución de gastos por categoría", size=18, weight=ft.FontWeight.BOLD),
                                    *pie_sections,
                                ],
                                spacing=10,
                            ),
                        )
                    ),
                    ft.Card(
                        content=ft.Container(
                            padding=16,
                            content=ft.Column(
                                controls=[
                                    ft.Text("Ingresos vs Gastos por mes", size=18, weight=ft.FontWeight.BOLD),
                                    *bar_rows,
                                ],
                                spacing=12,
                            ),
                        )
                    ),
                ],
                spacing=18,
            )

        return ft.Column(
            expand=True,
            spacing=18,
            controls=[
                ft.Text("Gráficas", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Análisis visual del balance y gastos mensuales.", color=ft.colors.SECONDARY),
                chart_body,
            ],
        )


def main(page: ft.Page) -> None:
    """Punto de entrada de la aplicación Flet."""
    app = FinanLYApp(page)
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
