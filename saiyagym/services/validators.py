"""
Validacion de formatos de entrada (rubrica: "Manejo de formatos de entrada de datos").
Las reglas replican las de la base de datos (RN-17 y CHECK) para dar mensajes
claros antes de llegar a Oracle; la base de datos sigue siendo la ultima defensa.
"""
from __future__ import annotations
import re
from datetime import date, datetime
from typing import Mapping

RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RE_IDENTIFICACION = re.compile(r"^\d{5,15}$")
RE_TELEFONO = re.compile(r"^3\d{9}$")
RE_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]{1,59}$")

NIVELES = ("PRINCIPIANTE", "INTERMEDIO", "AVANZADO")
METODOS_PAGO = ("EFECTIVO", "TARJETA", "TRANSFERENCIA", "NEQUI")


class Resultado:
    """Datos limpios + errores por campo."""

    def __init__(self):
        self.datos: dict = {}
        self.errores: dict[str, str] = {}

    @property
    def ok(self) -> bool:
        return not self.errores

    def error(self, campo: str, mensaje: str) -> None:
        self.errores.setdefault(campo, mensaje)


def _texto(f: Mapping, campo: str) -> str:
    return (f.get(campo) or "").strip()


def _entero(f: Mapping, campo: str, r: Resultado, minimo: int, maximo: int, etiqueta: str) -> int | None:
    bruto = _texto(f, campo)
    try:
        valor = int(bruto)
    except ValueError:
        r.error(campo, f"{etiqueta} debe ser un numero entero.")
        return None
    if not (minimo <= valor <= maximo):
        r.error(campo, f"{etiqueta} debe estar entre {minimo} y {maximo}.")
        return None
    return valor


def validar_clave(clave: str) -> str | None:
    """Politica de contrasena: 8+ caracteres con mayuscula, minuscula y digito."""
    if len(clave) < 8:
        return "La contrasena debe tener al menos 8 caracteres."
    if not (re.search(r"[A-Z]", clave) and re.search(r"[a-z]", clave) and re.search(r"\d", clave)):
        return "La contrasena debe combinar mayusculas, minusculas y numeros."
    return None


def usuario(f: Mapping, con_clave: bool, roles_validos: set[int] | None = None) -> Resultado:
    r = Resultado()
    d = r.datos
    d["identificacion"] = _texto(f, "identificacion")
    d["nombre"] = _texto(f, "nombre")
    d["apellido"] = _texto(f, "apellido")
    d["correo"] = _texto(f, "correo").lower()
    d["telefono"] = _texto(f, "telefono") or None
    if not RE_IDENTIFICACION.match(d["identificacion"]):
        r.error("identificacion", "La identificacion debe tener entre 5 y 15 digitos.")
    if not RE_NOMBRE.match(d["nombre"]):
        r.error("nombre", "Ingrese un nombre valido (solo letras, 2 a 60 caracteres).")
    if not RE_NOMBRE.match(d["apellido"]):
        r.error("apellido", "Ingrese un apellido valido (solo letras, 2 a 60 caracteres).")
    if not RE_CORREO.match(d["correo"]) or len(d["correo"]) > 100:
        r.error("correo", "Ingrese un correo electronico valido.")
    if d["telefono"] and not RE_TELEFONO.match(d["telefono"]):
        r.error("telefono", "El telefono debe ser un celular de 10 digitos que inicia en 3.")
    if roles_validos is not None:
        try:
            d["rol_id"] = int(_texto(f, "rol_id"))
            if d["rol_id"] not in roles_validos:
                raise ValueError
        except ValueError:
            r.error("rol_id", "Seleccione un rol valido.")
    if con_clave:
        d["clave"] = f.get("clave") or ""
        msg = validar_clave(d["clave"])
        if msg:
            r.error("clave", msg)
    return r


def tipo_membresia(f: Mapping) -> Resultado:
    r = Resultado()
    d = r.datos
    d["nombre"] = _texto(f, "nombre")
    d["descripcion"] = _texto(f, "descripcion") or None
    d["estado"] = _texto(f, "estado") or "ACTIVA"
    if not (2 <= len(d["nombre"]) <= 100):
        r.error("nombre", "El nombre debe tener entre 2 y 100 caracteres.")
    d["duracion"] = _entero(f, "duracion", r, 1, 3650, "La duracion (dias)")
    d["precio"] = _entero(f, "precio", r, 1, 100_000_000, "El precio")
    if d["estado"] not in ("ACTIVA", "INACTIVA"):
        r.error("estado", "Estado no valido.")
    if d["descripcion"] and len(d["descripcion"]) > 200:
        r.error("descripcion", "La descripcion admite hasta 200 caracteres.")
    return r


def fecha_iso(texto: str) -> date | None:
    try:
        return datetime.strptime(texto.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def adquisicion(f: Mapping) -> Resultado:
    r = Resultado()
    d = r.datos
    d["usu_id"] = _entero(f, "usu_id", r, 1, 10**9, "El cliente")
    d["mem_id"] = _entero(f, "mem_id", r, 1, 10**9, "La membresia")
    d["inicio"] = fecha_iso(_texto(f, "inicio"))
    if d["inicio"] is None:
        r.error("inicio", "Ingrese una fecha de inicio valida.")
    return r


def pago(f: Mapping, con_destino: bool = True) -> Resultado:
    r = Resultado()
    d = r.datos
    if con_destino:
        d["cli_mem_id"] = _entero(f, "cli_mem_id", r, 1, 10**9, "La membresia adquirida")
        d["estado"] = _texto(f, "estado") or "PAGADO"
        if d["estado"] not in ("PAGADO", "PENDIENTE"):
            r.error("estado", "El pago nuevo debe quedar PAGADO o PENDIENTE.")
    d["valor"] = _entero(f, "valor", r, 1, 100_000_000, "El valor")
    d["metodo"] = _texto(f, "metodo").upper()
    if d["metodo"] not in METODOS_PAGO:
        r.error("metodo", "Seleccione un metodo de pago valido.")
    return r


def ejercicio(f: Mapping) -> Resultado:
    r = Resultado()
    d = r.datos
    d["nombre"] = _texto(f, "nombre")
    d["descripcion"] = _texto(f, "descripcion") or None
    d["grupo"] = _texto(f, "grupo")
    d["nivel"] = _texto(f, "nivel").upper()
    if not (2 <= len(d["nombre"]) <= 100):
        r.error("nombre", "El nombre debe tener entre 2 y 100 caracteres.")
    if not (2 <= len(d["grupo"]) <= 50):
        r.error("grupo", "Indique el grupo muscular (2 a 50 caracteres).")
    if d["nivel"] not in NIVELES:
        r.error("nivel", "Seleccione un nivel valido.")
    if d["descripcion"] and len(d["descripcion"]) > 200:
        r.error("descripcion", "La descripcion admite hasta 200 caracteres.")
    return r


def rutina(f: Mapping) -> Resultado:
    r = Resultado()
    d = r.datos
    d["nombre"] = _texto(f, "nombre")
    d["objetivo"] = _texto(f, "objetivo")
    d["nivel"] = _texto(f, "nivel").upper()
    d["descripcion"] = _texto(f, "descripcion") or None
    if not (2 <= len(d["nombre"]) <= 100):
        r.error("nombre", "El nombre debe tener entre 2 y 100 caracteres.")
    if not (2 <= len(d["objetivo"]) <= 150):
        r.error("objetivo", "Indique el objetivo (2 a 150 caracteres).")
    if d["nivel"] not in NIVELES:
        r.error("nivel", "Seleccione un nivel valido.")
    if d["descripcion"] and len(d["descripcion"]) > 200:
        r.error("descripcion", "La descripcion admite hasta 200 caracteres.")
    return r


def linea_rutina(f: Mapping, con_ejercicio: bool = True) -> Resultado:
    r = Resultado()
    d = r.datos
    if con_ejercicio:
        d["eje_id"] = _entero(f, "eje_id", r, 1, 10**9, "El ejercicio")
    d["series"] = _entero(f, "series", r, 1, 20, "Las series")
    d["repeticiones"] = _entero(f, "repeticiones", r, 1, 200, "Las repeticiones")
    d["descanso"] = _entero(f, "descanso", r, 0, 900, "El descanso (segundos)")
    return r


def asignacion(f: Mapping) -> Resultado:
    r = Resultado()
    r.datos["cliente_id"] = _entero(f, "cliente_id", r, 1, 10**9, "El cliente")
    r.datos["rut_id"] = _entero(f, "rut_id", r, 1, 10**9, "La rutina")
    return r
