"""Repositorio de membresias -> paquete PKG_MEMBRESIA."""
from __future__ import annotations
from datetime import date

import oracledb

from ..db.gateway import Gateway


class MembresiaRepo:
    def __init__(self, gw: Gateway):
        self.gw = gw

    # catalogo
    def tipos(self, solo_activas: bool = False) -> list[dict]:
        return self.gw.filas("pkg_membresia.consultar_tipos", 1 if solo_activas else 0)

    def tipo(self, mem_id: int) -> dict | None:
        return next((t for t in self.tipos() if t["memid"] == mem_id), None)

    def insertar_tipo(self, d: dict) -> int:
        (nuevo,) = self.gw.procedimiento(
            "pkg_membresia.insertar_tipo",
            [d["nombre"], d["duracion"], d["precio"], d["descripcion"]], [int])
        return int(nuevo)

    def actualizar_tipo(self, mem_id: int, d: dict) -> None:
        self.gw.procedimiento(
            "pkg_membresia.actualizar_tipo",
            [mem_id, d["nombre"], d["duracion"], d["precio"], d["descripcion"], d["estado"]])

    def eliminar_tipo(self, mem_id: int) -> None:
        self.gw.procedimiento("pkg_membresia.eliminar_tipo", [mem_id])

    # adquiridas
    def adquiridas(self, usu_id: int | None = None) -> list[dict]:
        return self.gw.filas("pkg_membresia.consultar_adquiridas", usu_id)

    def vigente(self, usu_id: int) -> dict | None:
        return self.gw.fila("pkg_membresia.membresia_vigente", usu_id)

    def adquirir(self, usu_id: int, mem_id: int, inicio: date) -> int:
        (nuevo,) = self.gw.procedimiento("pkg_membresia.adquirir", [usu_id, mem_id, inicio], [int])
        return int(nuevo)

    def eliminar_adquirida(self, cli_mem_id: int) -> None:
        self.gw.procedimiento("pkg_membresia.eliminar_adquirida", [cli_mem_id])

    def actualizar_estados(self) -> int:
        return int(self.gw.escalar("pkg_membresia.actualizar_estados", oracledb.DB_TYPE_NUMBER))
