"""Repositorio de asistencias y rachas -> paquete PKG_ASISTENCIA."""
from __future__ import annotations
from datetime import date

import oracledb

from ..db.gateway import Gateway


class AsistenciaRepo:
    def __init__(self, gw: Gateway):
        self.gw = gw

    def registrar(self, usu_id: int) -> int:
        (nuevo,) = self.gw.procedimiento("pkg_asistencia.registrar", [usu_id], [int])
        return int(nuevo)

    def consultar(self, usu_id: int, desde: date | None = None, hasta: date | None = None) -> list[dict]:
        return self.gw.filas("pkg_asistencia.consultar", usu_id, desde, hasta)

    def racha_actual(self, usu_id: int) -> int:
        return int(self.gw.escalar("pkg_asistencia.racha_actual", oracledb.DB_TYPE_NUMBER, usu_id))

    def mejor_racha(self, usu_id: int) -> int:
        return int(self.gw.escalar("pkg_asistencia.mejor_racha", oracledb.DB_TYPE_NUMBER, usu_id))

    def estado_racha(self, usu_id: int) -> str:
        return self.gw.escalar("pkg_asistencia.estado_racha", oracledb.DB_TYPE_VARCHAR, usu_id)

    def asistio_hoy(self, usu_id: int) -> bool:
        return bool(self.gw.escalar("pkg_asistencia.asistio_hoy", oracledb.DB_TYPE_NUMBER, usu_id))

    def historial_rachas(self, usu_id: int) -> list[dict]:
        return self.gw.filas("pkg_asistencia.historial_rachas", usu_id)

    def logros(self, usu_id: int) -> list[dict]:
        return self.gw.filas("pkg_asistencia.logros", usu_id)
