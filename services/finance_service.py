from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional


class FinanceService:
    """Lógica de negocio para resumenes, filtros y formato financiero."""

    def __init__(self, db):
        self.db = db

    def money(self, value: float) -> str:
        return f"${value:,.2f}"

    def today_summary(self) -> Dict[str, Any]:
        hoy = datetime.date.today()
        mes_actual = hoy.strftime("%Y-%m")
        return {
            "today": hoy,
            "transactions_today": self.db.list_transactions(mes=mes_actual),
            "dashboard": self.db.get_dashboard_summary(),
        }

    def month_summary(self, year: Optional[int] = None, month: Optional[int] = None) -> Dict[str, float]:
        today = datetime.date.today()
        year = year or today.year
        month = month or today.month
        return self.db.get_month_summary(year, month)

    def total_balance(self) -> float:
        return self.db.get_total_balance()

    def category_options(self, tipo: Optional[str] = None):
        return self.db.list_categories(tipo)
