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
                content=ft.Text(self.finance.money(ingreso), size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
            )
            red_bar = ft.Container(
                width=170 * gasto_pct if gasto > 0 else 0,
                height=24,
                border_radius=10,
                bgcolor="#f87171",
                padding=ft.Padding(left=8, right=8),
                content=ft.Text(self.finance.money(gasto), size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
            )

            rows.append(
                ft.Row(
                    controls=[
                        ft.Text(str(item["dia"]), color=ft.Colors.SECONDARY, size=12, width=26),
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

    def render(self):
        today = datetime.date.today()
        mes_actual = f"{today.year:04d}-{today.month:02d}"
        resumen_mes = self.db.get_month_summary(today.year, today.month)
        categorias_gasto = self.db.get_category_totals("gasto", mes_actual)
        categorias_ingreso = self.db.get_category_totals("ingreso", mes_actual)
        total_gastos = sum(float(i["total"]) for i in categorias_gasto)
        total_ingresos = float(resumen_mes["ingresos"])
        saldo_total = self.db.get_total_balance()
        saldo_neto = total_ingresos - total_gastos
        daily = self.db.get_daily_totals(today.year, today.month)

        cards = [
            ft.Container(
                width=180,
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
                width=180,
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
                width=180,
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
                width=180,
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
