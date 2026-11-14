"""Repositorio de pagos -> paquete PKG_PAGO."""
from __future__ import annotations
import oracledb

from ..db.gateway import Gateway


class PagoRepo:
    def __init__(self, gw: Gateway):
        self.gw = gw

    def consultar(self, estado: str | None = None, usu_id: int | None = None) -> list[dict]:
        return self.gw.filas("pkg_pago.consultar", estado, usu_id)

    def obtener(self, pag_id: int) -> dict | None:
        return next((p for p in self.consultar() if p["pagid"] == pag_id), None)

    def saldo(self, cli_mem_id: int) -> float:
        return float(self.gw.escalar("pkg_pago.saldo", oracledb.DB_TYPE_NUMBER, cli_mem_id))

    def registrar(self, cli_mem_id: int, valor: float, metodo: str, estado: str) -> int:
        (nuevo,) = self.gw.procedimiento(
            "pkg_pago.registrar", [cli_mem_id, valor, metodo, estado], [int])
        return int(nuevo)

    def actualizar(self, pag_id: int, valor: float, metodo: str) -> None:
        self.gw.procedimiento("pkg_pago.actualizar", [pag_id, valor, metodo])

    def cambiar_estado(self, pag_id: int, estado: str) -> None:
        self.gw.procedimiento("pkg_pago.cambiar_estado", [pag_id, estado])

    def eliminar(self, pag_id: int) -> None:
        self.gw.procedimiento("pkg_pago.eliminar", [pag_id])
