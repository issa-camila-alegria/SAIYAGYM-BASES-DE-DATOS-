"""Formatos de presentacion (iguales a los de PKG_FORMATO en la base de datos, RN-17)."""
from __future__ import annotations
from datetime import date, datetime

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def moneda(valor) -> str:
    """$ 1.234.567 (pesos colombianos, punto de miles, sin decimales)."""
    if valor is None:
        return ""
    try:
        return "$ " + f"{int(round(float(valor))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(valor)


def moneda_corta(valor) -> str:
    """Version compacta para etiquetas de graficos: 450 mil, 1,3 M."""
    try:
        v = float(valor or 0)
    except (TypeError, ValueError):
        return str(valor)
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}".replace(".", ",").rstrip("0").rstrip(",") + " M"
    if v >= 1_000:
        return f"{round(v / 1_000)} mil"
    return str(int(v))


def fecha(valor) -> str:
    if not valor:
        return ""
    if isinstance(valor, (datetime, date)):
        return valor.strftime("%d/%m/%Y")
    return str(valor)


def fecha_larga(valor) -> str:
    if not valor:
        return ""
    return f"{valor.day} de {MESES[valor.month - 1]} de {valor.year}"


def fecha_input(valor) -> str:
    return valor.strftime("%Y-%m-%d") if valor else ""


def iniciales(nombre: str, apellido: str = "") -> str:
    return ((nombre or " ")[0] + (apellido or " ")[0]).strip().upper()


_ESTADOS = {
    "ACTIVO": "ok", "ACTIVA": "ok", "PAGADO": "ok", "VIGENTE": "ok", "LOGRADO": "ok",
    "PENDIENTE": "warn", "POR VENCER": "warn", "ABONO PARCIAL": "warn",
    "INACTIVO": "off", "INACTIVA": "off", "FINALIZADA": "off", "SIN ASIGNAR": "warn",
    "VENCIDA": "bad", "ANULADO": "bad", "CANCELADA": "bad", "INTERRUMPIDA": "bad",
    "SIN EJERCICIOS": "bad", "SIN ASISTENCIAS": "off",
}


def clase_estado(estado) -> str:
    return _ESTADOS.get(str(estado or "").upper(), "off")
