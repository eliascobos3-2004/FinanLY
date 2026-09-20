"""FinanLY - Interfaz principal de la app.

Este archivo concentra la capa de presentación de la aplicación, construida con Flet.
Se encarga de:
- inicializar la página
- crear la navegación lateral
- renderizar las pantallas principales
- abrir modales para ingresos, gastos y cuentas
- mostrar los resúmenes y gráficos del mes

La lógica de persistencia se mantiene en db.py, mientras que aquí vive la interfaz.
"""

from __future__ import annotations

import datetime
from typing import Optional

import flet as ft

from db import DatabaseManager
from services.finance_service import FinanceService
from ui.sidebar import Sidebar
from ui.screens.home_screen import HomeScreen
from ui.screens.transactions_screen import TransactionsScreen
from ui.screens.accounts_screen import AccountsScreen
from ui.screens.summary_screen import SummaryScreen


class FinanLYApp:
    """Aplicación principal de FinanLY.

    Esta clase gestiona toda la experiencia visual del usuario: encabezado,
    navegación lateral, pantallas, modales y cálculos visuales básicos.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "FinanLY"
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.padding = 0
        self.page.bgcolor = "#0b1220"
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.theme = ft.Theme(color_scheme_seed="#3B82F6", use_material3=True)
        self.page.theme_mode = ft.ThemeMode.SYSTEM

        self.db = DatabaseManager("finanly.db")
        self.finance = FinanceService(self.db)
        self.tab_index = 0
        self.transactions_filter_date = datetime.date.today().isoformat()
        self.transactions_filter_category = "todos"
        self.transactions_filter_account = "todos"
        # Not using calendar widget; we show a small dialog with day/month/year selectors instead
        self.content = ft.Container(
            expand=True,
            padding=0,
            alignment=ft.Alignment(0, 0),
        )

        self.header_bar = ft.Container(
            height=58,
            padding=ft.Padding(left=18, right=18, top=8, bottom=8),
            bgcolor="#111827",
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=48),
                    ft.Text("FinanLY", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Container(width=48),
                ],
            ),
        )

        self.sidebar = Sidebar(self.on_nav_change, self.toggle_sidebar)
        self.nav = self.sidebar.nav
        self.sidebar_extended = self.sidebar.extended
        self.sidebar_width = self.sidebar.width
        self.sidebar_collapsed_width = self.sidebar.collapsed_width
        self.sidebar_container = self.sidebar.container

        # Contenido principal desplazable con espacio reservado para la barra
        # inferior fija. Sin este padding, la barra se superpone sobre los
        # títulos y el contenido final de cada pantalla.
        self.main_list = ft.ListView(
            expand=True,
            spacing=0,
            padding=ft.Padding(bottom=110),
            controls=[
                self.header_bar,
                ft.Container(expand=True, content=self.content, padding=0, margin=0, alignment=ft.Alignment(0, 0)),
            ],
        )

        # Añadir solo el contenido principal; la barra inferior se dibuja como
        # overlay flotante, pero ahora dejamos margen inferior en la vista.
        self.page.add(self.main_list)

        try:
            self.sidebar.container.alignment = ft.Alignment(0, 1)
            self.sidebar.container.expand = False
            self.sidebar.container.bottom = 18
            self.page.overlay.append(self.sidebar.container)
        except Exception:
            self.page.overlay.append(self.sidebar.container)

        self.render()

    def debug(self, message: str):
        """Imprime mensajes de depuración del flujo de la app."""
        print(f"[FinanLY DEBUG] {message}")

    def show_message(self, message: str):
        """Muestra un aviso tipo snackbar para feedback visual."""
        self.debug(message)
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), open=True)
        self.page.update()

    def toggle_sidebar(self, e=None):
        """Muestra/oculta el comportamiento extendido de la barra inferior."""
        try:
            self.sidebar.toggle()
        except Exception:
            # Si el sidebar no implementa toggle exactamente, mantener compatibilidad
            self.sidebar_extended = not self.sidebar_extended
        self.page.update()

    def on_nav_change(self, e):
        """Cambia la pantalla activa al tocar una sección del sidebar."""
        self.tab_index = e.control.selected_index
        self.render()

    def render(self):
        """Actualiza el contenido principal según la ventana activa."""
        self.screens = [
            HomeScreen(self),
            TransactionsScreen(self),
            AccountsScreen(self),
            SummaryScreen(self),
        ]
        self.content.content = self.screens[self.tab_index].render()
        self.page.update()

    def _handle_date_picker_change(self, e):
        """Cuando el usuario elige una fecha, la refleja en el campo que la solicitó.

        Si se proporcionó un callback en `open_date_picker`, también se invoca
        para que la pantalla pueda aplicar filtros automáticamente.
        """
        if self.date_picker_target is not None:
            self.date_picker_target.value = self.date_picker.value.isoformat()
            try:
                self.date_picker_target.update()
            except Exception:
                pass

        # Llamar callback si existe
        cb = getattr(self, "_date_picker_callback", None)
        if callable(cb):
            try:
                cb()
            except Exception:
                pass

        # limpiar callback
        if hasattr(self, "_date_picker_callback"):
            delattr(self, "_date_picker_callback")

        self.page.update()

    def money(self, value: float) -> str:
        """Formatea un número como moneda local con dos decimales."""
        return f"${value:,.2f}"

    def open_date_picker(self, target_field, default_date: Optional[str] = None, on_select: Optional[callable] = None):
        """Muestra un diálogo con selectores de día/mes/año y devuelve la fecha seleccionada.

        Esto reemplaza el DatePicker nativo para evitar dependencias de versión y
        permite filtrar mediante `on_select` tras confirmar.
        """
        # parsear fecha por defecto
        try:
            if default_date:
                d = datetime.date.fromisoformat(default_date)
            else:
                d = datetime.date.today()
        except Exception:
            d = datetime.date.today()

        day_field = ft.Dropdown(
            value=str(d.day),
            width=120,
            height=52,
            options=[ft.DropdownOption(str(i), text=str(i)) for i in range(1, 32)],
            text_style=ft.TextStyle(size=16),
        )
        month_field = ft.Dropdown(
            value=str(d.month),
            width=150,
            height=52,
            options=[ft.DropdownOption(str(i), text=datetime.date(2000, i, 1).strftime('%B')) for i in range(1, 13)],
            text_style=ft.TextStyle(size=16),
        )
        # años: últimos 5 años hasta el próximo año
        today = datetime.date.today()
        years = list(range(today.year - 5, today.year + 2))
        year_field = ft.Dropdown(
            value=str(d.year),
            width=140,
            height=52,
            options=[ft.DropdownOption(str(y), text=str(y)) for y in years],
            text_style=ft.TextStyle(size=16),
        )

        error_text = ft.Text("", color=ft.Colors.ERROR)

        def confirm(_):
            try:
                dy = int(day_field.value)
                mo = int(month_field.value)
                yr = int(year_field.value)
                sel = datetime.date(yr, mo, dy)
                iso = sel.isoformat()
                target_field.value = iso
                try:
                    target_field.update()
                except Exception:
                    pass
                if callable(on_select):
                    try:
                        on_select(None)
                    except Exception:
                        pass
                self.close_dialog(dialog)
                self.page.update()
            except Exception as exc:
                error_text.value = "Fecha inválida"
                self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Seleccionar fecha", size=22, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=440,
                padding=12,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=14,
                            controls=[
                                ft.Column(
                                    spacing=8,
                                    controls=[
                                        ft.Text("Día", size=16, weight=ft.FontWeight.W_600),
                                        day_field,
                                    ],
                                ),
                                ft.Column(
                                    spacing=8,
                                    controls=[
                                        ft.Text("Mes", size=16, weight=ft.FontWeight.W_600),
                                        month_field,
                                    ],
                                ),
                                ft.Column(
                                    spacing=8,
                                    controls=[
                                        ft.Text("Año", size=16, weight=ft.FontWeight.W_600),
                                        year_field,
                                    ],
                                ),
                            ],
                        ),
                        error_text,
                    ],
                ),
            ),
            actions=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=16,
                    controls=[
                        ft.TextButton("Cancelar", on_click=lambda e: self.close_dialog(dialog), style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                        ft.FilledButton("Aceptar", on_click=confirm, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))),
                    ],
                )
            ],
        )

        self.open_dialog(dialog)

    def _build_modal_container(self, title: str, content_controls, save_callback=None, width: int = 420):
        """Crea un contenedor modal estándar para formularios y vistas rápidas."""
        dialog_holder = {"dialog": None}

        def close_current(_=None):
            self.close_dialog(dialog_holder["dialog"])

        actions = []
        if save_callback is not None:
            actions.append(
                ft.Container(
                    alignment=ft.alignment.center_right,
                    content=ft.IconButton(
                        icon=ft.Icons.SAVE_ALT_ROUNDED,
                        tooltip="Guardar",
                        on_click=save_callback,
                        icon_color=ft.Colors.WHITE,
                        bgcolor="#3b82f6",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                    ),
                )
            )

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor="#1c2434",
            content_padding=20,
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(title, size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.IconButton(icon=ft.Icons.CLOSE, on_click=close_current, style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                ],
            ),
            content=ft.Container(
                width=width,
                padding=10,
                content=ft.Column(
                    tight=True,
                    spacing=14,
                    controls=content_controls,
                ),
            ),
            actions=actions,
        )
        dialog_holder["dialog"] = dialog
        return dialog

    def _modal_action(self, source: str, dialog: Optional[ft.AlertDialog] = None):
        self.debug(f"CLICK MODAL -> {source}")
        self.close_dialog(dialog)
        self.debug(f"MODAL cerrado por: {source}")

    def _build_category_bar_chart(self, items, color_hex: str, title: Optional[str] = None):
        if not items:
            return ft.Text(f"Sin {title.lower() if title else 'datos'} este mes.", color=ft.Colors.SECONDARY)

        total = sum(float(item["total"]) for item in items)
        total = total if total > 0 else 1

        rows = []
        for item in items[:5]:
            value = float(item["total"])
            pct = max(value / total, 0.04)
            rows.append(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(item["categoria"], color=ft.Colors.WHITE, size=14),
                                ft.Text(self.money(value), color=ft.Colors.WHITE, size=14),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(
                            height=12,
                            border_radius=12,
                            bgcolor="#1f2937",
                            content=ft.Container(
                                width=280 * pct,
                                height=12,
                                border_radius=12,
                                bgcolor=color_hex,
                            ),
                        ),
                    ],
                    spacing=6,
                )
            )

        return ft.Container(width=360, content=ft.Column(controls=rows, spacing=12))

    def _build_daily_flow_chart(self, daily):
        """Genera la gráfica de evolución diaria con ingresos y gastos del mes."""
        if not daily:
            return ft.Text("Sin movimientos para este mes.", color=ft.Colors.SECONDARY)

        max_value = max(max(float(item["ingresos"]), float(item["gastos"])) for item in daily)
        max_value = max_value if max_value > 0 else 1

        rows = []
        for item in daily:
            ingreso = float(item["ingresos"])
            gasto = float(item["gastos"])
            ingreso_pct = max(ingreso / max_value, 0.0)
            gasto_pct = max(gasto / max_value, 0.0)

            green_bar = ft.Container(
                width=170 * ingreso_pct if ingreso > 0 else 0,
                height=24,
                border_radius=10,
                bgcolor="#22c55e",
                padding=ft.Padding(left=8, right=8),
                content=ft.Text(self.money(ingreso), size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
            )
            red_bar = ft.Container(
                width=170 * gasto_pct if gasto > 0 else 0,
                height=24,
                border_radius=10,
                bgcolor="#f87171",
                padding=ft.Padding(left=8, right=8),
                content=ft.Text(self.money(gasto), size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
            )

            rows.append(
                ft.Row(
                    controls=[
                        ft.Text(str(item["dia"]), color=ft.Colors.SECONDARY, size=12, width=24),
                        ft.Row(
                            controls=[green_bar, red_bar],
                            spacing=6,
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        return ft.Container(width=420, content=ft.Column(controls=rows, spacing=10))

    def open_dialog(self, dialog: ft.AlertDialog):
        """Abre un diálogo con la estrategia compatible con la versión de Flet usada."""
        self.debug(f"open_dialog: attach modal to page overlay -> {type(dialog).__name__}")
        try:
            self.page.show_dialog(dialog)
        except Exception:
            self.page.dialog = dialog
            dialog.open = True
            overlay = getattr(self.page, "overlay", None)
            if overlay is not None and dialog not in overlay:
                overlay.append(dialog)
        self.page.update()

    def close_dialog(self, dialog: Optional[ft.AlertDialog] = None):
        """Cierra el modal abierto sin romper el estado de la página."""
        target = dialog if dialog is not None else getattr(self.page, "dialog", None)
        if target is not None:
            try:
                target.open = False
            except Exception:
                pass
        try:
            self.page.pop_dialog()
        except Exception:
            try:
                self.page.dialog = None
            except Exception:
                pass
            try:
                overlay = getattr(self.page, "overlay", None)
                if overlay is not None:
                    for item in list(overlay):
                        try:
                            if hasattr(item, "open"):
                                item.open = False
                        except Exception:
                            pass
                    overlay.clear()
            except Exception:
                pass
        self.page.update()

    def home_screen(self):
        """Pantalla principal: saldo, ingresos, gastos y transacciones recientes."""
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
                            ft.Text(self.money(resumen["saldo_total"]), size=25, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
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
                            ft.Text(self.money(resumen["ingresos_mes"]), size=22, weight=ft.FontWeight.W_600, color=ft.Colors.GREEN),
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
                            ft.Text(self.money(resumen["gastos_mes"]), size=22, weight=ft.FontWeight.W_600, color=ft.Colors.RED),
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
                            ft.Text(self.money(tx["monto"]), weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN if tx["tipo"] == "ingreso" else ft.Colors.RED),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                )
                for tx in trans_hoy[:5]
            ]
        else:
            today_list = [ft.Text("Hoy no hay transacciones.", color=ft.Colors.SECONDARY)]

        def open_today_transactions(_):
            dialog = self._build_modal_container(
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
            self.open_dialog(dialog)

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
                            on_click=lambda e, tipo="ingreso": self.open_quick_transaction_dialog(tipo=tipo),
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
                            on_click=lambda e, tipo="gasto": self.open_quick_transaction_dialog(tipo=tipo),
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
                            trailing=ft.Text(self.money(tx["monto"]), weight=ft.FontWeight.W_600, color=ft.Colors.GREEN if tx["tipo"] == "ingreso" else ft.Colors.RED),
                        )
                        for tx in (resumen["ultimas_transacciones"] or [])
                    ]),
                ),
            ],
        )

    def open_quick_transaction_dialog(self, e=None, tipo: str = "gasto"):
        accounts = self.db.list_accounts()
        if not accounts:
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Sin cuentas", size=26, weight=ft.FontWeight.BOLD),
                        ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda _: self._modal_action("X", dialog)),
                    ],
                ),
                content=ft.Text("Primero crea una cuenta para registrar movimientos."),
                actions=[ft.IconButton(icon=ft.Icons.CHECK_CIRCLE, on_click=lambda _: self._modal_action("ACEPTAR", dialog))],
            )
            self.open_dialog(dialog)
            return

        tipo_field = ft.Dropdown(
            width=200,
            value=tipo,
            hint_text="Tipo",
            options=[
                ft.DropdownOption("gasto", text="Gasto"),
                ft.DropdownOption("ingreso", text="Ingreso"),
            ],
        )

        def categoria_options_for_tipo(selected_tipo: Optional[str]):
            if not selected_tipo:
                return [ft.DropdownOption("General", text="General")]
            return [ft.DropdownOption(cat, text=cat) for cat in self.db.list_categories(selected_tipo)]

        categoria_field = ft.Dropdown(
            width=220,
            value=("General" if tipo == "gasto" else "Sueldo"),
            options=categoria_options_for_tipo(tipo),
            hint_text="Categoría",
        )
        custom_categoria_field = ft.TextField(label="Nueva categoría", hint_text="Ej. Veterinaria")
        account_field = ft.Dropdown(
            width=220,
            hint_text="Cuenta",
            options=[ft.DropdownOption(str(a["id"]), text=a["nombre"]) for a in accounts],
        )
        amount_field = ft.TextField(label="Monto", keyboard_type=ft.KeyboardType.NUMBER)
        note_field = ft.TextField(label="Nota")
        date_field = ft.TextField(label="Fecha", value=datetime.date.today().isoformat(), read_only=True)
        error_text = ft.Text("", color=ft.Colors.ERROR)

        def open_date_selection(_):
            self.open_date_picker(date_field, date_field.value)

        date_field_row = ft.Row(
            controls=[
                date_field,
                ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=open_date_selection),
            ],
            spacing=6,
        )

        def on_tipo_change(_):
            if tipo_field.value:
                categoria_field.options = categoria_options_for_tipo(tipo_field.value)
                if categoria_field.options:
                    categoria_field.value = categoria_field.options[0].key
                self.page.update()

        tipo_field.on_change = on_tipo_change

        def save(e):
            try:
                if not tipo_field.value:
                    raise ValueError("Debes seleccionar un tipo.")
                if not account_field.value:
                    raise ValueError("Debes seleccionar una cuenta.")
                if not amount_field.value:
                    raise ValueError("El monto es obligatorio.")

                monto = float(amount_field.value)
                if monto <= 0:
                    raise ValueError("El monto debe ser mayor que 0.")

                categoria_custom = (custom_categoria_field.value or "").strip()
                if categoria_custom:
                    categoria = self.db.add_custom_category(categoria_custom, tipo_field.value)
                else:
                    categoria = (categoria_field.value or "General").strip() or "General"

                cuenta_id = int(account_field.value)
                fecha = date_field.value or datetime.date.today().isoformat()
                nota = note_field.value or ""
                self.db.create_transaction(tipo_field.value, monto, categoria, cuenta_id, fecha, nota)
                self.close_dialog(dialog)
                self.show_message("Transacción registrada.")
                self.render()
            except ValueError as exc:
                error_text.value = str(exc)
                self.page.update()
            except Exception:
                error_text.value = "No se pudo guardar la transacción."
                self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Registrar movimiento", size=26, weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda _: self._modal_action("X", dialog)),
                ],
            ),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    tight=True,
                    controls=[
                        ft.Row(controls=[ft.Text("Tipo"), tipo_field], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row(controls=[ft.Text("Categoría"), categoria_field], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        custom_categoria_field,
                        ft.Row(controls=[ft.Text("Cuenta"), account_field], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        amount_field,
                        date_field_row,
                        note_field,
                        error_text,
                    ],
                ),
            ),
            actions=[
                ft.IconButton(
                    icon=ft.Icons.SAVE_ALT_ROUNDED,
                    tooltip="Guardar",
                    on_click=lambda e: save(e),
                )
            ],
        )
        self.open_dialog(dialog)

    def transactions_screen(self):
        accounts = self.db.list_accounts()
        fecha_field = ft.TextField(label="Fecha", value=datetime.date.today().isoformat(), read_only=True, width=220)
        category_filter = ft.Dropdown(
            value="todos",
            width=220,
            options=[ft.DropdownOption("todos", text="Todas las categorías")] + self.category_options(),
        )
        account_filter = ft.Dropdown(
            value="todos",
            width=220,
            options=[ft.DropdownOption("todos", text="Todas las cuentas")] + [ft.DropdownOption(str(a["id"]), text=a["nombre"]) for a in accounts],
        )

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
                                                ft.Text(self.money(r["monto"]), weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN if r["tipo"] == "ingreso" else ft.Colors.RED),
                                                ft.Row(
                                                    controls=[
                                                        ft.IconButton(ft.Icons.EDIT, on_click=lambda e, item_id=r["id"]: self.open_transaction_dialog(tx_id=item_id)),
                                                        ft.IconButton(ft.Icons.DELETE_OUTLINE, on_click=lambda e, item_id=r["id"]: self.delete_transaction(item_id)),
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

        summary_text = ft.Text("0 movimientos • Ingresos $0.00 • Gastos $0.00", color=ft.Colors.SECONDARY)
        list_view = ft.ListView(expand=True, spacing=8, auto_scroll=True)

        def open_date_selection(_):
            self.open_date_picker(fecha_field, fecha_field.value)

        apply_filters(None)

        return ft.Column(
            expand=True,
            spacing=12,
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                ft.Text("Transacciones", size=28, weight=ft.FontWeight.BOLD),
                ft.FilledButton("Nueva transacción", icon=ft.Icons.ADD, on_click=lambda e: self.open_transaction_dialog()),
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

    def month_options(self):
        today = datetime.date.today()
        options = [ft.DropdownOption("todos", text="Todos los meses")]
        for year in [today.year, today.year - 1]:
            for month in range(1, 13):
                if year == today.year and month > today.month:
                    continue
                label = f"{year:04d}-{month:02d}"
                options.append(ft.DropdownOption(label, text=label))
        return options

    def category_options(self, tipo: Optional[str] = None):
        options = []
        for nombre in self.db.list_categories(tipo):
            options.append(ft.DropdownOption(nombre, text=nombre))
        return options

    def open_transaction_dialog(self, e=None, tx_id: Optional[int] = None):
        accounts = self.db.list_accounts()
        if not accounts:
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Sin cuentas", size=26, weight=ft.FontWeight.BOLD),
                        ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda _: self._modal_action("X", dialog)),
                    ],
                ),
                content=ft.Text("Primero crea una cuenta para registrar transacciones."),
                actions=[ft.IconButton(icon=ft.Icons.CHECK_CIRCLE, on_click=lambda _: self._modal_action("ACEPTAR", dialog))],
            )
            self.open_dialog(dialog)
            return

        edit_tx = self.db.get_transaction(tx_id) if tx_id else None
        tipo_field = ft.Dropdown(
            width=170,
            value=edit_tx["tipo"] if edit_tx else "gasto",
            hint_text="Tipo",
            options=[
                ft.DropdownOption("gasto", text="Gasto"),
                ft.DropdownOption("ingreso", text="Ingreso"),
            ],
        )

        def categoria_options_for_tipo(selected_tipo: Optional[str]):
            if not selected_tipo:
                return [ft.DropdownOption("General", text="General")]
            return [ft.DropdownOption(cat, text=cat) for cat in self.db.list_categories(selected_tipo)]

        categoria_field = ft.Dropdown(
            width=220,
            value=(edit_tx["categoria"] if edit_tx else "General"),
            options=categoria_options_for_tipo(edit_tx["tipo"] if edit_tx else "gasto"),
            hint_text="Categoría",
        )
        custom_categoria_field = ft.TextField(label="Nueva categoría", hint_text="Ej. Veterinaria")
        account_field = ft.Dropdown(
            width=230,
            value=str(edit_tx["cuenta_id"]) if edit_tx else None,
            hint_text="Cuenta",
            options=[ft.DropdownOption(str(a["id"]), text=a["nombre"]) for a in accounts],
        )
        amount_field = ft.TextField(label="Monto", value=str(edit_tx["monto"]) if edit_tx else "", keyboard_type=ft.KeyboardType.NUMBER)
        date_field = ft.TextField(label="Fecha", value=edit_tx["fecha"] if edit_tx else datetime.date.today().isoformat())
        note_field = ft.TextField(label="Nota", value=edit_tx["nota"] if edit_tx else "", multiline=True, min_lines=1, max_lines=3)
        error_text = ft.Text("", color=ft.Colors.ERROR)

        def on_tipo_change(_):
            if tipo_field.value:
                categoria_field.options = categoria_options_for_tipo(tipo_field.value)
                if categoria_field.options:
                    categoria_field.value = categoria_field.options[0].key
                self.page.update()

        tipo_field.on_change = on_tipo_change

        def submit(e):
            try:
                if not tipo_field.value:
                    raise ValueError("Debes seleccionar un tipo.")
                if not account_field.value:
                    raise ValueError("Debes seleccionar una cuenta.")
                if not amount_field.value:
                    raise ValueError("El monto es obligatorio.")
                monto = float(amount_field.value)
                if monto <= 0:
                    raise ValueError("El monto debe ser mayor que 0.")

                tipo = tipo_field.value
                categoria_custom = (custom_categoria_field.value or "").strip()
                if categoria_custom:
                    categoria = self.db.add_custom_category(categoria_custom, tipo)
                else:
                    categoria = (categoria_field.value or "General").strip() or "General"
                cuenta_id = int(account_field.value)
                fecha = date_field.value or datetime.date.today().isoformat()
                nota = note_field.value or ""

                if edit_tx is None:
                    self.db.create_transaction(tipo, monto, categoria, cuenta_id, fecha, nota)
                else:
                    self.db.update_transaction(tx_id, tipo=tipo, monto=monto, categoria=categoria, cuenta_id=cuenta_id, fecha=fecha, nota=nota)

                self.close_dialog(dialog)
                self.show_message("Cambios guardados.")
                self.render()
            except ValueError as exc:
                error_text.value = str(exc)
                self.page.update()
            except Exception:
                error_text.value = "No se pudo guardar la transacción."
                self.page.update()

        date_field_row = ft.Row(
            controls=[
                ft.Container(expand=True, content=date_field),
                ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=lambda _: self.open_date_picker(date_field, date_field.value)),
            ],
            spacing=6,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Editar transacción" if edit_tx else "Nueva transacción", size=26, weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda _: self._modal_action("X", dialog)),
                ],
            ),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    tight=True,
                    controls=[
                        ft.Row(controls=[ft.Text("Tipo"), tipo_field], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row(controls=[ft.Text("Categoría"), categoria_field], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        custom_categoria_field,
                        ft.Row(controls=[ft.Text("Cuenta"), account_field], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        amount_field,
                        date_field_row,
                        note_field,
                        error_text,
                    ],
                ),
            ),
            actions=[ft.IconButton(icon=ft.Icons.SAVE_ALT_ROUNDED, tooltip="Guardar", on_click=lambda e: submit(e))],
        )
        self.open_dialog(dialog)

    def delete_transaction(self, tx_id: int):
        if self.db.delete_transaction(tx_id):
            self.show_message("Transacción eliminada.")
            self.render()

    def accounts_screen(self):
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
                                ft.Text(f"Saldo actual: {self.money(self.db.get_account_balance(cuenta['id']))}", size=18),
                                ft.Text(f"Saldo inicial: {self.money(float(cuenta['saldo_inicial']))}", color=ft.Colors.SECONDARY),
                                ft.Row(
                                    controls=[
                                        ft.TextButton("Editar", on_click=lambda e, item_id=cuenta["id"]: self.open_account_dialog(account_id=item_id)),
                                        ft.TextButton("Eliminar", on_click=lambda e, item_id=cuenta["id"]: self.delete_account(item_id)),
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
                ft.FilledButton("Nueva cuenta", icon=ft.Icons.ADD, on_click=lambda e: self.open_account_dialog()),
                ft.ListView(expand=True, spacing=10, controls=cards),
            ],
        )

    def open_account_dialog(self, e=None, account_id: Optional[int] = None):
        edit_account = self.db.get_account(account_id) if account_id else None
        name_field = ft.TextField(label="Nombre", value=edit_account["nombre"] if edit_account else "")
        balance_field = ft.TextField(label="Saldo inicial", value=str(edit_account["saldo_inicial"]) if edit_account else "", keyboard_type=ft.KeyboardType.NUMBER)
        icon_field = ft.TextField(label="Icono", value=edit_account["icono"] if edit_account else "💰")
        error_text = ft.Text("", color=ft.Colors.ERROR)

        def submit(e):
            try:
                nombre = (name_field.value or "").strip()
                if not nombre:
                    raise ValueError("El nombre de la cuenta es obligatorio.")
                saldo = float(balance_field.value or 0)
                icono = (icon_field.value or "💰").strip() or "💰"

                if edit_account is None:
                    self.db.create_account(nombre, saldo, icono)
                else:
                    self.db.update_account(account_id, nombre=nombre, saldo_inicial=saldo, icono=icono)

                self.close_dialog(dialog)
                self.show_message("Cuenta guardada.")
                # ir automáticamente a la pestaña Cuentas
                self.tab_index = 2
                self.render()
            except ValueError as exc:
                error_text.value = str(exc)
                self.page.update()
            except Exception:
                error_text.value = "No se pudo guardar la cuenta."
                self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Editar cuenta" if edit_account else "Nueva cuenta", size=26, weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda _: self._modal_action("X", dialog)),
                ],
            ),
            content=ft.Container(
                width=360,
                content=ft.Column(tight=True, controls=[name_field, balance_field, icon_field, error_text]),
            ),
            actions=[ft.IconButton(icon=ft.Icons.SAVE_ALT_ROUNDED, tooltip="Guardar", on_click=lambda e: submit(e))],
        )
        self.open_dialog(dialog)

    def delete_account(self, account_id: int):
        if self.db.delete_account(account_id):
            self.show_message("Cuenta eliminada.")
            self.render()

    def graphics_screen(self):
        """Pantalla de resumen financiero con KPIs y gráfica mensual."""
        today = datetime.date.today()
        mes_actual = f"{today.year:04d}-{today.month:02d}"
        resumen_mes = self.db.get_month_summary(today.year, today.month)
        categorias_gasto = self.db.get_category_totals("gasto", mes_actual)
        categorias_ingreso = self.db.get_category_totals("ingreso", mes_actual)
        total_gastos = sum(float(i["total"]) for i in categorias_gasto)
        total_ingresos = float(resumen_mes["ingresos"])
        saldo_total = self.db.get_total_balance()
        saldo_neto = total_ingresos - total_gastos

        cards = [
            ft.Container(
                width=180,
                padding=16,
                border_radius=12,
                bgcolor="#111827",
                content=ft.Column(
                    controls=[
                        ft.Text("Saldo total", size=15, color=ft.Colors.SECONDARY),
                        ft.Text(self.money(saldo_total), size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                    ],
                    spacing=6,
                ),
            ),
            ft.Container(
                width=180,
                padding=16,
                border_radius=12,
                bgcolor="#111827",
                content=ft.Column(
                    controls=[
                        ft.Text("Ingresos", size=15, color=ft.Colors.SECONDARY),
                        ft.Text(self.money(total_ingresos), size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                    ],
                    spacing=6,
                ),
            ),
            ft.Container(
                width=180,
                padding=16,
                border_radius=12,
                bgcolor="#111827",
                content=ft.Column(
                    controls=[
                        ft.Text("Gastos", size=15, color=ft.Colors.SECONDARY),
                        ft.Text(self.money(total_gastos), size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                    ],
                    spacing=6,
                ),
            ),
            ft.Container(
                width=180,
                padding=16,
                border_radius=12,
                bgcolor="#111827",
                content=ft.Column(
                    controls=[
                        ft.Text("Neto", size=15, color=ft.Colors.SECONDARY),
                        ft.Text(self.money(saldo_neto), size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE),
                    ],
                    spacing=6,
                ),
            ),
        ]

        daily = self.db.get_daily_totals(today.year, today.month)

        return ft.Column(
            expand=True,
            spacing=20,
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                ft.Text(f"Resumen • {today.strftime('%B %Y').title()}", size=42, weight=ft.FontWeight.BOLD),
                ft.Text("Métricas clave del mes actual.", size=16, color=ft.Colors.SECONDARY),
                ft.Row(controls=cards, wrap=True, spacing=12, run_spacing=12),
                ft.Container(
                    padding=18,
                    border_radius=16,
                    bgcolor="#111827",
                    content=ft.Column(
                        controls=[
                            ft.Text("Top 5 gastos del mes", size=28, weight=ft.FontWeight.BOLD),
                            self._build_category_bar_chart(categorias_gasto, "#f87171", "gastos"),
                        ],
                        spacing=10,
                    ),
                ),
                ft.Container(
                    padding=18,
                    border_radius=16,
                    bgcolor="#111827",
                    content=ft.Column(
                        controls=[
                            ft.Text("Top 5 ingresos del mes", size=28, weight=ft.FontWeight.BOLD),
                            self._build_category_bar_chart(categorias_ingreso, "#22c55e", "ingresos"),
                        ],
                        spacing=10,
                    ),
                ),
                ft.Container(
                    padding=18,
                    border_radius=16,
                    bgcolor="#111827",
                    content=ft.Column(
                        controls=[
                            ft.Text("Evolución diaria del mes", size=28, weight=ft.FontWeight.BOLD),
                            self._build_daily_flow_chart(daily),
                        ],
                        spacing=10,
                    ),
                ),
            ],
        )


def main(page: ft.Page):
    FinanLYApp(page)


if __name__ == "__main__":
    ft.run(main)
