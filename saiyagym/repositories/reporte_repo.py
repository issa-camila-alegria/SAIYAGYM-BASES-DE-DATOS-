"""Repositorio de informes -> paquetes PKG_REPORTES y PKG_DICCIONARIO."""
from __future__ import annotations
from ..db.gateway import Gateway


class ReporteRepo:
    def __init__(self, gw: Gateway):
        self.gw = gw

    def resumen_general(self) -> dict:
        return self.gw.fila("pkg_reportes.resumen_general") or {}

    def ejecutar(self, funcion: str, *params) -> list[dict]:
        """Ejecuta una de las funciones pkg_reportes.repNN_* (nombre ya validado)."""
        return self.gw.filas(f"pkg_reportes.{funcion}", *params)


    def serie(self, funcion: str, *params) -> list[dict]:
        """Series de los graficos (pkg_reportes.graf_*)."""
        return self.gw.filas(f"pkg_reportes.{funcion}", *params)


class DiccionarioRepo:
    def __init__(self, gw: Gateway):
        self.gw = gw

    def tablas(self) -> list[dict]:
        return self.gw.filas("pkg_diccionario.tablas")

    def columnas(self, tabla: str) -> list[dict]:
        return self.gw.filas("pkg_diccionario.columnas", tabla)

    def restricciones(self, tabla: str) -> list[dict]:
        return self.gw.filas("pkg_diccionario.restricciones", tabla)

    def indices(self, tabla: str) -> list[dict]:
        return self.gw.filas("pkg_diccionario.indices", tabla)

    def procedimientos(self) -> list[dict]:
        return self.gw.filas("pkg_diccionario.procedimientos")

    def subprogramas(self, objeto: str) -> list[dict]:
        return self.gw.filas("pkg_diccionario.subprogramas", objeto)

    def codigo(self, objeto: str, tipo: str) -> list[dict]:
        return self.gw.filas("pkg_diccionario.codigo_fuente", objeto, tipo)

    def secuencias(self) -> list[dict]:
        return self.gw.filas("pkg_diccionario.secuencias")
