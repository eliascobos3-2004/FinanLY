from __future__ import annotations

import flet as ft


class Sidebar:
    """Barra de navegación inferior fija.

    Implementada como una barra inferior que permanece fuera del área
    desplazable del contenido principal. Proporciona los mismos índices
    de navegación que antes y ejecuta el callback `on_change` con un
    objeto sintético que contiene `control.selected_index`.
    """

    def __init__(self, on_change, toggle_sidebar=None):
        self.extended = True
        self.width = None
        self.collapsed_width = None
        self.selected_index = 0
        self._on_change = on_change

        # Destinos con iconos y etiquetas (etiqueta opcional según `extended`)
        def make_dest(idx, icon, label):
            def _click(e=None):
                self.selected_index = idx
                # crear evento sintético compatible con on_nav_change
                class C:
                    pass

                c = C()
                c.selected_index = idx

                class E:
                    pass

                eobj = E()
                eobj.control = c
                self._on_change(eobj)

            col = ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                tight=True,
                controls=[
                    ft.IconButton(
                        icon=icon,
                        on_click=_click,
                        icon_color=ft.Colors.WHITE,
                        icon_size=28,
                        width=42,
                        height=42,
                        style=ft.ButtonStyle(color=ft.Colors.WHITE),
                    ),
                    ft.Text(label, size=11, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
                ],
            )
            return col

        controls = [
            make_dest(0, ft.Icons.HOME_OUTLINED, "Inicio"),
            make_dest(1, ft.Icons.RECEIPT_LONG_OUTLINED, "Transacciones"),
            make_dest(2, ft.Icons.WALLET_OUTLINED, "Cuentas"),
            make_dest(3, ft.Icons.INSIGHTS_OUTLINED, "Resumen"),
        ]

        self.container = ft.Container(
            width=500,
            height=88,
            bgcolor="#111827",
            padding=ft.Padding(10, 8, 10, 8),
            margin=ft.Margin(12, 12, 12, 18),
            border_radius=20,
            alignment=ft.Alignment(0, 1),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls,
            ),
        )

        # Intentar añadir sombra si la versión de Flet lo soporta
        BoxShadow = getattr(ft, "BoxShadow", None)
        if BoxShadow is not None:
            try:
                self.container.box_shadow = ft.BoxShadow(blur_radius=12, spread=0, color=ft.Colors.BLACK)
            except Exception:
                try:
                    # alternativa: propiedad 'shadow'
                    self.container.shadow = ft.BoxShadow(blur_radius=12, spread=0, color=ft.Colors.BLACK)
                except Exception:
                    pass

        # Exponer un 'nav' ligero similar al previo para compatibilidad
        class NavProxy:
            def __init__(self, inst):
                self.selected_index = inst.selected_index
                self.extended = inst.extended

        self.nav = NavProxy(self)

    def toggle(self):
        self.extended = not self.extended
        return self.container
