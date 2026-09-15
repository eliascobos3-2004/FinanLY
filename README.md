# FinanLY

FinanLY es un gestor de finanzas personales 100% local, ligero y rápido, desarrollado con Python + Flet.

## Características

- Gestión local con SQLite
- Sin internet ni APIs externas
- Control de cuentas y transacciones
- Resúmenes mensuales
- Dashboard visual de gastos e ingresos
- Funcionamiento offline y sin dependencias pesadas

## Requisitos

- Python 3.11+
- Flet
- Android SDK (solo para generar APK)

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install flet
```

## Ejecutar la app

```bash
source .venv/bin/activate
python main.py
```

## Generar APK

```bash
source .venv/bin/activate
flet build apk --project FinanLY --product "FinanLY" --org com.finanly
```

## Estructura

- `main.py`: aplicación Flet
- `db.py`: capa de SQLite
- `finanly.db`: base de datos local

## Licencia

MIT
# FinanLY
