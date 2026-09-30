from __future__ import annotations

import datetime

import flet as ft

from ui.screens.base_screen import BaseScreen


class SummaryScreen(BaseScreen):
    def _build_category_bar_chart(self, items, color_hex: str, title: str | None = None):
        if not items:
            return ft.Text(f"Sin {title.lower() if title else 'datos'} este mes.", color=ft.Colors.SECONDARY)

        total = sum(float(item["total"]) for item in items)
        total = total if total > 0 else 1
        screen_width = float(getattr(self.page, "width", 0) or 360)
        chart_width = max(280, min(420, screen_width - 42))

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
                                ft.Text(self.finance.money(value), color=ft.Colors.WHITE, size=14),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(
                            height=12,
                            border_radius=12,
                            bgcolor="#1f2937",
                            content=ft.Container(
                                width=max(30, chart_width * pct - 20),
                                height=12,
                                border_radius=12,
                                bgcolor=color_hex,
                            ),
                        ),
                    ],
                    spacing=6,
                )
            )

        return ft.Container(width=chart_width, content=ft.Column(controls=rows, spacing=12))

    def _build_daily_flow_chart(self, daily):
        if not daily:
            return ft.Text("Sin movimientos para este mes.", color=ft.Colors.SECONDARY)

        screen_width = float(getattr(self.page, "width", 0) or 360)
        chart_width = max(280, min(420, screen_width - 42))
        slot_width = max(220, chart_width - 60)
        half = (slot_width - 10) / 2

        max_value = max(max(float(item["ingresos"]), float(item["gastos"])) for item in daily)
        max_value = max_value if max_value > 0 else 1

        rows = []
        for item in daily:
            ingreso = float(item["ingresos"])
            gasto = float(item["gastos"])
            ingreso_width = max(2, int((half * (ingreso / max_value)) if ingreso > 0 else 0))
            gasto_width = max(2, int((half * (gasto / max_value)) if gasto > 0 else 0))

            ingreso_bar = ft.Container(
                width=ingreso_width,
                height=24,
                border_radius=10,
                bgcolor="#22c55e",
                content=ft.Container(
                    alignment=ft.Alignment(1, 0.5),
                    padding=ft.Padding(left=4, right=4),
                    content=ft.Text(self.finance.money(ingreso), size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                ),
            )
            gasto_bar = ft.Container(
                width=gasto_width,
                height=24,
                border_radius=10,
                bgcolor="#f87171",
                content=ft.Container(
                    alignment=ft.Alignment(1, 0.5),
                    padding=ft.Padding(left=4, right=4),
                    content=ft.Text(self.finance.money(gasto), size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                ),
            )

            rows.append(
                ft.Row(
                    controls=[
                        ft.Container(width=30, content=ft.Text(str(item["dia"]), color=ft.Colors.SECONDARY, size=12)),
                        ft.Row(
                            controls=[ingreso_bar, gasto_bar],
                            spacing=6,
                            width=slot_width,
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        return ft.Container(width=chart_width, content=ft.Column(controls=rows, spacing=10))

    def _build_yearly_monthly_chart(self, year: int):
        monthly_data = self.db.get_monthly_comparison(year)
        values_by_month = {
            row["mes"]: {"ingresos": float(row["ingresos"]), "gastos": float(row["gastos"])}
            for row in monthly_data
        }

        screen_width = float(getattr(self.page, "width", 0) or 360)
        chart_width = max(280, min(430, screen_width - 42))
        bar_area = max(180, chart_width - 70)
        max_value = 1.0
        for month in range(1, 13):
            key = f"{year:04d}-{month:02d}"
            month_data = values_by_month.get(key, {"ingresos": 0.0, "gastos": 0.0})
            max_value = max(max_value, float(month_data["ingresos"]), float(month_data["gastos"]))

        rows = []
        for month in range(1, 13):
            key = f"{year:04d}-{month:02d}"
            month_data = values_by_month.get(key, {"ingresos": 0.0, "gastos": 0.0})
            ingresos = float(month_data["ingresos"])
            gastos = float(month_data["gastos"])

            ingreso_width = max(8, int(bar_area * 0.5 * (ingresos / max_value))) if ingresos > 0 else 0
            gasto_width = max(8, int(bar_area * 0.5 * (gastos / max_value))) if gastos > 0 else 0

            rows.append(
                ft.Row(
                    controls=[
                        ft.Container(width=30, content=ft.Text(f"{month:02d}", color=ft.Colors.SECONDARY, size=12)),
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=ingreso_width,
                                    height=18,
                                    border_radius=8,
                                    bgcolor="#22c55e",
                                    content=ft.Text(self.finance.money(ingresos), size=9, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                                ),
                                ft.Container(
                                    width=gasto_width,
                                    height=18,
                                    border_radius=8,
                                    bgcolor="#f87171",
                                    content=ft.Text(self.finance.money(gastos), size=9, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                                ),
                            ],
                            spacing=4,
                            width=bar_area,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        return ft.Container(width=chart_width, content=ft.Column(controls=rows, spacing=8))

    def render(self):
        today = datetime.date.today()
        selected_year = getattr(self.app, "summary_year", today.year)
        selected_month = getattr(self.app, "summary_month", today.month)
        mes_actual = f"{selected_year:04d}-{selected_month:02d}"
        resumen_mes = self.db.get_month_summary(selected_year, selected_month)
        categorias_gasto = self.db.get_category_totals("gasto", mes_actual)
        categorias_ingreso = self.db.get_category_totals("ingreso", mes_actual)
        total_gastos = sum(float(i["total"]) for i in categorias_gasto)
        total_ingresos = float(resumen_mes["ingresos"])
        saldo_total = self.db.get_total_balance()
        saldo_neto = total_ingresos - total_gastos
        daily = self.db.get_daily_totals(selected_year, selected_month)

        screen_width = float(getattr(self.page, "width", 0) or 360)
        card_width = max(150, min(180, int((screen_width - 48) / 2)))
        title_size = max(28, min(42, int(screen_width * 0.11)))

        cards = [
            ft.Container(
                width=card_width,
                padding=16,
                border_radius=12,
                bgcolor="#111827",
                content=ft.Column(
                    controls=[
                        ft.Text("Saldo total", size=15, color=ft.Colors.SECONDARY),
                        ft.Text(self.finance.money(saldo_total), size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                    ],
                    spacing=6,
                ),
            ),
            ft.Container(
                width=card_width,
                padding=16,
                border_radius=12,
                bgcolor="#111827",
                content=ft.Column(
                    controls=[
                        ft.Text("Ingresos", size=15, color=ft.Colors.SECONDARY),
                        ft.Text(self.finance.money(total_ingresos), size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                    ],
                    spacing=6,
                ),
            ),
            ft.Container(
                width=card_width,
                padding=16,
                border_radius=12,
                bgcolor="#111827",
                content=ft.Column(
                    controls=[
                        ft.Text("Gastos", size=15, color=ft.Colors.SECONDARY),
                        ft.Text(self.finance.money(total_gastos), size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                    ],
                    spacing=6,
                ),
            ),
            ft.Container(
                width=card_width,
                padding=16,
                border_radius=12,
                bgcolor="#111827",
                content=ft.Column(
                    controls=[
                        ft.Text("Neto", size=15, color=ft.Colors.SECONDARY),
                        ft.Text(self.finance.money(saldo_neto), size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE),
                    ],
                    spacing=6,
                ),
            ),
        ]

        return ft.Column(
            expand=True,
            spacing=20,
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(f"Resumen • {datetime.date(selected_year, selected_month, 1).strftime('%B %Y').title()}", size=title_size, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.Icons.CALENDAR_MONTH,
                            tooltip="Seleccionar mes",
                            on_click=lambda _: self.app.open_summary_period_dialog(selected_year, selected_month),
                        ),
                    ],
                ),
                ft.Text("Métricas clave del periodo seleccionado.", size=16, color=ft.Colors.SECONDARY),
                ft.Row(controls=cards, wrap=True, spacing=12, run_spacing=12),
                ft.Container(
                    padding=18,
                    border_radius=16,
                    bgcolor="#111827",
                    content=ft.Column(
                        controls=[
                            ft.Text("Top 5 gastos del mes", size=max(20, min(28, title_size - 4)), weight=ft.FontWeight.BOLD),
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
                            ft.Text("Top 5 ingresos del mes", size=max(20, min(28, title_size - 4)), weight=ft.FontWeight.BOLD),
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
                            ft.Text("Evolución mensual del año", size=max(20, min(28, title_size - 4)), weight=ft.FontWeight.BOLD),
                            self._build_yearly_monthly_chart(selected_year),
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
                            ft.Text(f"Evolución diaria de {datetime.date(selected_year, selected_month, 1).strftime('%B %Y').title()}", size=max(20, min(28, title_size - 4)), weight=ft.FontWeight.BOLD),
                            self._build_daily_flow_chart(daily),
                        ],
                        spacing=10,
                    ),
                ),
            ],
        )
