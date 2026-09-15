"""
FinanLY - Módulo de Base de Datos SQLite
=====================================

Este archivo es el PASO 1 del proyecto FinanLY. Provee la capa de persistencia local
utilizando SQLite nativo de Python, sin dependencias externas ni ORMs.

Objetivos principales:
- Crear y mantener la estructura de datos del sistema.
- Gestionar cuentas y transacciones de forma segura.
- Calcular saldos y resúmenes de manera eficiente con SQL directo.
- Mantener el proyecto liviano, estable y 100% offline.

Uso recomendado:
    from db import DatabaseManager
    db = DatabaseManager("finanly.db")

Si quieres ejecutarlo directamente como prueba:
    python db.py
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional


class DatabaseManager:
    """Gestor central de SQLite para FinanLY.

    Este objeto encapsula la conexión, la inicialización de la base de datos,
    el CRUD de cuentas y transacciones, y las consultas agregadas para calcular
    saldos, balances mensuales y categorías.
    """

    def __init__(self, db_path: str = "finanly.db") -> None:
        self.db_path = db_path
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        """Crea la conexión a SQLite con configuración ligera y segura.

        Se activa `PRAGMA foreign_keys = ON` para asegurar integridad referencial
        y `row_factory = sqlite3.Row` para acceder a columnas por nombre.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def init_db(self) -> None:
        """Crea las tablas e índices si aún no existen."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cuentas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    saldo_inicial REAL NOT NULL DEFAULT 0,
                    icono TEXT NOT NULL DEFAULT '💰'
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transacciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL CHECK (tipo IN ('ingreso', 'gasto')),
                    monto REAL NOT NULL CHECK (monto >= 0),
                    categoria TEXT NOT NULL,
                    cuenta_id INTEGER NOT NULL,
                    fecha TEXT NOT NULL,
                    nota TEXT DEFAULT '',
                    FOREIGN KEY (cuenta_id) REFERENCES cuentas(id) ON DELETE CASCADE
                )
                """
            )

            # Índices para acelerar búsquedas por cuenta, tipo, fecha y categoría.
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cuentas_nombre ON cuentas(nombre)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transacciones_cuenta_id ON transacciones(cuenta_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transacciones_tipo_fecha ON transacciones(tipo, fecha)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transacciones_categoria ON transacciones(categoria)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transacciones_fecha ON transacciones(fecha)"
            )

            conn.commit()

    # ------------------------------------------------------------------
    # CRUD de cuentas
    # ------------------------------------------------------------------

    def create_account(
        self,
        nombre: str,
        saldo_inicial: float = 0.0,
        icono: str = "💰",
    ) -> int:
        """Crea una nueva cuenta y devuelve su ID."""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO cuentas (nombre, saldo_inicial, icono)
                VALUES (?, ?, ?)
                """,
                (nombre.strip(), float(saldo_inicial), icono or "💰"),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def get_account(self, account_id: int) -> Optional[sqlite3.Row]:
        """Obtiene una cuenta por su ID."""
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM cuentas WHERE id = ?",
                (account_id,),
            ).fetchone()

    def list_accounts(self) -> List[sqlite3.Row]:
        """Lista todas las cuentas ordenadas por nombre."""
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM cuentas ORDER BY nombre ASC"
            ).fetchall()

    def update_account(
        self,
        account_id: int,
        nombre: Optional[str] = None,
        saldo_inicial: Optional[float] = None,
        icono: Optional[str] = None,
    ) -> bool:
        """Actualiza los datos de una cuenta."""
        account = self.get_account(account_id)
        if account is None:
            return False

        nombre = nombre.strip() if nombre is not None else account["nombre"]
        saldo_inicial = (
            float(saldo_inicial)
            if saldo_inicial is not None
            else float(account["saldo_inicial"])
        )
        icono = icono or account["icono"]

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE cuentas
                SET nombre = ?, saldo_inicial = ?, icono = ?
                WHERE id = ?
                """,
                (nombre, saldo_inicial, icono, account_id),
            )
            conn.commit()
            return True

    def delete_account(self, account_id: int) -> bool:
        """Elimina una cuenta y sus transacciones asociadas por cascada."""
        if self.get_account(account_id) is None:
            return False

        with self._connect() as conn:
            conn.execute("DELETE FROM cuentas WHERE id = ?", (account_id,))
            conn.commit()
            return True

    # ------------------------------------------------------------------
    # CRUD de transacciones
    # ------------------------------------------------------------------

    def create_transaction(
        self,
        tipo: str,
        monto: float,
        categoria: str,
        cuenta_id: int,
        fecha: str,
        nota: str = "",
    ) -> int:
        """Crea una transacción y devuelve su ID."""
        if tipo not in ("ingreso", "gasto"):
            raise ValueError("El tipo debe ser 'ingreso' o 'gasto'.")

        if self.get_account(cuenta_id) is None:
            raise ValueError(f"La cuenta con id {cuenta_id} no existe.")

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO transacciones (tipo, monto, categoria, cuenta_id, fecha, nota)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (tipo, float(monto), categoria.strip(), cuenta_id, fecha, nota or ""),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def get_transaction(self, transaction_id: int) -> Optional[sqlite3.Row]:
        """Devuelve una transacción por ID con datos de la cuenta."""
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT t.*, c.nombre AS nombre_cuenta
                FROM transacciones t
                INNER JOIN cuentas c ON c.id = t.cuenta_id
                WHERE t.id = ?
                """,
                (transaction_id,),
            ).fetchone()

    def list_transactions(
        self,
        tipo: Optional[str] = None,
        categoria: Optional[str] = None,
        cuenta_id: Optional[int] = None,
        mes: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[sqlite3.Row]:
        """Lista transacciones con filtros opcionales.

        Ejemplo de mes: '2026-09'.
        """
        query = """
            SELECT t.*, c.nombre AS nombre_cuenta
            FROM transacciones t
            INNER JOIN cuentas c ON c.id = t.cuenta_id
            WHERE 1 = 1
        """
        params: List[Any] = []

        if tipo:
            query += " AND t.tipo = ?"
            params.append(tipo)

        if categoria:
            query += " AND t.categoria = ?"
            params.append(categoria)

        if cuenta_id is not None:
            query += " AND t.cuenta_id = ?"
            params.append(cuenta_id)

        if mes:
            query += " AND strftime('%Y-%m', t.fecha) = ?"
            params.append(mes)

        query += " ORDER BY t.fecha DESC, t.id DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(int(limit))

        with self._connect() as conn:
            return conn.execute(query, params).fetchall()

    def update_transaction(
        self,
        transaction_id: int,
        tipo: Optional[str] = None,
        monto: Optional[float] = None,
        categoria: Optional[str] = None,
        cuenta_id: Optional[int] = None,
        fecha: Optional[str] = None,
        nota: Optional[str] = None,
    ) -> bool:
        """Actualiza una transacción existente."""
        tx = self.get_transaction(transaction_id)
        if tx is None:
            return False

        nuevo_tipo = tipo or tx["tipo"]
        nuevo_monto = float(monto) if monto is not None else float(tx["monto"])
        nueva_categoria = categoria.strip() if categoria is not None else tx["categoria"]
        nueva_cuenta = cuenta_id if cuenta_id is not None else int(tx["cuenta_id"])
        nueva_fecha = fecha or tx["fecha"]
        nueva_nota = nota if nota is not None else tx["nota"]

        if self.get_account(nueva_cuenta) is None:
            raise ValueError(f"La cuenta con id {nueva_cuenta} no existe.")

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE transacciones
                SET tipo = ?, monto = ?, categoria = ?, cuenta_id = ?, fecha = ?, nota = ?
                WHERE id = ?
                """,
                (
                    nuevo_tipo,
                    nuevo_monto,
                    nueva_categoria,
                    nueva_cuenta,
                    nueva_fecha,
                    nueva_nota,
                    transaction_id,
                ),
            )
            conn.commit()
            return True

    def delete_transaction(self, transaction_id: int) -> bool:
        """Elimina una transacción por ID."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM transacciones WHERE id = ?",
                (transaction_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Cálculos de saldo y resúmenes
    # ------------------------------------------------------------------

    def get_account_balance(self, account_id: int) -> float:
        """Calcula el saldo actual de una cuenta.

        Fórmula:
            saldo_inicial + ingresos - gastos
        """
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    c.saldo_inicial,
                    COALESCE(SUM(CASE WHEN t.tipo = 'ingreso' THEN t.monto ELSE 0 END), 0) AS total_ingresos,
                    COALESCE(SUM(CASE WHEN t.tipo = 'gasto' THEN t.monto ELSE 0 END), 0) AS total_gastos
                FROM cuentas c
                LEFT JOIN transacciones t ON t.cuenta_id = c.id
                WHERE c.id = ?
                GROUP BY c.id, c.saldo_inicial
                """,
                (account_id,),
            ).fetchone()

            if row is None:
                return 0.0

            saldo = float(row["saldo_inicial"]) + float(row["total_ingresos"]) - float(row["total_gastos"])
            return saldo

    def get_total_balance(self) -> float:
        """Suma el saldo actual de todas las cuentas."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(
                        c.saldo_inicial +
                        COALESCE((SELECT SUM(t.monto) FROM transacciones t WHERE t.cuenta_id = c.id AND t.tipo = 'ingreso'), 0)
                        -
                        COALESCE((SELECT SUM(t.monto) FROM transacciones t WHERE t.cuenta_id = c.id AND t.tipo = 'gasto'), 0)
                    ), 0) AS total
                FROM cuentas c
                """
            ).fetchone()
            return float(row["total"]) if row else 0.0

    def get_month_summary(self, year: int, month: int) -> Dict[str, float]:
        """Devuelve ingresos y gastos del mes indicado.

        Ejemplo: get_month_summary(2026, 9)
        """
        mes = f"{year:04d}-{month:02d}"
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) AS ingresos,
                    COALESCE(SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END), 0) AS gastos
                FROM transacciones
                WHERE strftime('%Y-%m', fecha) = ?
                """,
                (mes,),
            ).fetchone()

            if row is None:
                return {"ingresos": 0.0, "gastos": 0.0}

            return {
                "ingresos": float(row["ingresos"]),
                "gastos": float(row["gastos"]),
            }

    def get_current_month_summary(self) -> Dict[str, float]:
        """Devuelve resumen del mes actual."""
        import datetime

        hoy = datetime.date.today()
        return self.get_month_summary(hoy.year, hoy.month)

    def get_last_transactions(self, limit: int = 5) -> List[sqlite3.Row]:
        """Devuelve las transacciones más recientes."""
        return self.list_transactions(limit=limit)

    def get_category_totals(
        self,
        tipo: str = "gasto",
        mes: Optional[str] = None,
    ) -> List[sqlite3.Row]:
        """Agrupa por categoría y suma montos.

        Ejemplo:
            db.get_category_totals(tipo='gasto', mes='2026-09')
        """
        if tipo not in ("ingreso", "gasto"):
            raise ValueError("El tipo debe ser 'ingreso' o 'gasto'.")

        query = """
            SELECT categoria, SUM(monto) AS total
            FROM transacciones
            WHERE tipo = ?
        """
        params: List[Any] = [tipo]

        if mes:
            query += " AND strftime('%Y-%m', fecha) = ?"
            params.append(mes)

        query += " GROUP BY categoria ORDER BY total DESC"

        with self._connect() as conn:
            return conn.execute(query, params).fetchall()

    def get_monthly_comparison(self, year: int) -> List[sqlite3.Row]:
        """Genera comparación mensual de ingresos vs gastos para un año concreto."""
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT
                    strftime('%Y-%m', fecha) AS mes,
                    COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) AS ingresos,
                    COALESCE(SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END), 0) AS gastos
                FROM transacciones
                WHERE strftime('%Y', fecha) = ?
                GROUP BY strftime('%Y-%m', fecha)
                ORDER BY mes ASC
                """,
                (f"{year:04d}",),
            ).fetchall()

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Resumen completo listo para la pantalla de inicio."""
        import datetime

        hoy = datetime.date.today()
        mes_actual = f"{hoy.year:04d}-{hoy.month:02d}"
        resumen = self.get_month_summary(hoy.year, hoy.month)

        return {
            "saldo_total": self.get_total_balance(),
            "ingresos_mes": resumen["ingresos"],
            "gastos_mes": resumen["gastos"],
            "ultimas_transacciones": self.get_last_transactions(5),
            "categorias_gasto": self.get_category_totals("gasto", mes_actual),
        }

    def seed_demo_data(self) -> None:
        """Inserta datos de prueba para validar la app rápidamente.

        Es opcional y útil durante desarrollo para verificar que todo funciona.
        """
        with self._connect() as conn:
            cuenta_existente = conn.execute(
                "SELECT COUNT(*) AS total FROM cuentas"
            ).fetchone()["total"]

            if int(cuenta_existente) > 0:
                return

        self.create_account("Efectivo", 2500.0, "💵")
        self.create_account("Banco", 12000.0, "🏦")
        self.create_account("Tarjeta", 0.0, "💳")

        cuentas = self.list_accounts()
        efectivo_id = next(c["id"] for c in cuentas if c["nombre"] == "Efectivo")
        banco_id = next(c["id"] for c in cuentas if c["nombre"] == "Banco")
        tarjeta_id = next(c["id"] for c in cuentas if c["nombre"] == "Tarjeta")

        # Ingresos
        self.create_transaction(
            tipo="ingreso",
            monto=3500.0,
            categoria="Sueldo",
            cuenta_id=banco_id,
            fecha="2026-09-01",
            nota="Pago mensual",
        )
        self.create_transaction(
            tipo="ingreso",
            monto=250.0,
            categoria="Freelance",
            cuenta_id=efectivo_id,
            fecha="2026-09-08",
            nota="Trabajo extra",
        )

        # Gastos
        self.create_transaction(
            tipo="gasto",
            monto=420.0,
            categoria="Comida",
            cuenta_id=tarjeta_id,
            fecha="2026-09-03",
            nota="Supermercado",
        )
        self.create_transaction(
            tipo="gasto",
            monto=180.0,
            categoria="Transporte",
            cuenta_id=efectivo_id,
            fecha="2026-09-06",
            nota="Gasolina",
        )
        self.create_transaction(
            tipo="gasto",
            monto=320.0,
            categoria="Servicios",
            cuenta_id=banco_id,
            fecha="2026-09-10",
            nota="Internet y luz",
        )


if __name__ == "__main__":
    """Prueba rápida del módulo: crea una base de datos demo y muestra el resumen."""
    db = DatabaseManager("finanly_demo.db")
    db.seed_demo_data()

    print("Cuentas:")
    for cuenta in db.list_accounts():
        print(
            f"- {cuenta['nombre']} | saldo inicial: {cuenta['saldo_inicial']} | "
            f"saldo actual: {db.get_account_balance(cuenta['id'])}"
        )

    print("\nResumen del mes actual:")
    print(db.get_current_month_summary())

    print("\nÚltimas transacciones:")
    for tx in db.get_last_transactions(5):
        print(
            f"- {tx['fecha']} | {tx['tipo']} | {tx['categoria']} | "
            f"{tx['monto']} | cuenta: {tx['nombre_cuenta']}"
        )

    print("\nBalance total:")
    print(db.get_total_balance())
