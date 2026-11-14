"""Repositorio de ejercicios, rutinas y asignaciones -> PKG_EJERCICIO y PKG_RUTINA."""
from __future__ import annotations
from ..db.gateway import Gateway


class RutinaRepo:
    def __init__(self, gw: Gateway):
        self.gw = gw

    # ---- ejercicios ----
    def ejercicios(self, grupo: str | None = None) -> list[dict]:
        return self.gw.filas("pkg_ejercicio.consultar", grupo)

    def ejercicio(self, eje_id: int) -> dict | None:
        return next((e for e in self.ejercicios() if e["ejeid"] == eje_id), None)

    def grupos_musculares(self) -> list[str]:
        return [f["ejegrupomuscular"] for f in self.gw.filas("pkg_ejercicio.grupos_musculares")]

    def insertar_ejercicio(self, d: dict) -> int:
        (nuevo,) = self.gw.procedimiento(
            "pkg_ejercicio.insertar",
            [d["nombre"], d["descripcion"], d["grupo"], d["nivel"]], [int])
        return int(nuevo)

    def actualizar_ejercicio(self, eje_id: int, d: dict) -> None:
        self.gw.procedimiento(
            "pkg_ejercicio.actualizar",
            [eje_id, d["nombre"], d["descripcion"], d["grupo"], d["nivel"]])

    def eliminar_ejercicio(self, eje_id: int) -> None:
        self.gw.procedimiento("pkg_ejercicio.eliminar", [eje_id])

    # ---- rutinas ----
    def rutinas(self, entrenador_id: int | None = None) -> list[dict]:
        return self.gw.filas("pkg_rutina.consultar", entrenador_id)

    def rutina(self, rut_id: int) -> dict | None:
        return self.gw.fila("pkg_rutina.obtener", rut_id)

    def insertar_rutina(self, entrenador_id: int, d: dict) -> int:
        (nuevo,) = self.gw.procedimiento(
            "pkg_rutina.insertar",
            [entrenador_id, d["nombre"], d["objetivo"], d["nivel"], d["descripcion"]], [int])
        return int(nuevo)

    def actualizar_rutina(self, rut_id: int, entrenador_id: int, d: dict) -> None:
        self.gw.procedimiento(
            "pkg_rutina.actualizar",
            [rut_id, entrenador_id, d["nombre"], d["objetivo"], d["nivel"], d["descripcion"]])

    def eliminar_rutina(self, rut_id: int, entrenador_id: int) -> None:
        self.gw.procedimiento("pkg_rutina.eliminar", [rut_id, entrenador_id])

    # ---- ejercicios dentro de una rutina ----
    def ejercicios_de_rutina(self, rut_id: int) -> list[dict]:
        return self.gw.filas("pkg_rutina.ejercicios_de_rutina", rut_id)

    def agregar_ejercicio(self, rut_id: int, entrenador_id: int, eje_id: int,
                          series: int, repeticiones: int, descanso: int) -> int:
        (nuevo,) = self.gw.procedimiento(
            "pkg_rutina.agregar_ejercicio",
            [rut_id, entrenador_id, eje_id, series, repeticiones, descanso], [int])
        return int(nuevo)

    def actualizar_linea(self, rut_eje_id: int, entrenador_id: int,
                         series: int, repeticiones: int, descanso: int) -> None:
        self.gw.procedimiento(
            "pkg_rutina.actualizar_ejercicio",
            [rut_eje_id, entrenador_id, series, repeticiones, descanso])

    def quitar_ejercicio(self, rut_eje_id: int, entrenador_id: int) -> None:
        self.gw.procedimiento("pkg_rutina.quitar_ejercicio", [rut_eje_id, entrenador_id])

    # ---- asignaciones ----
    def asignaciones(self, entrenador_id: int | None = None, cliente_id: int | None = None) -> list[dict]:
        return self.gw.filas("pkg_rutina.consultar_asignaciones", entrenador_id, cliente_id)

    def asignar(self, entrenador_id: int, cliente_id: int, rut_id: int) -> int:
        (nuevo,) = self.gw.procedimiento(
            "pkg_rutina.asignar", [entrenador_id, cliente_id, rut_id], [int])
        return int(nuevo)

    def cerrar_asignacion(self, asi_rut_id: int, entrenador_id: int, estado: str) -> None:
        self.gw.procedimiento("pkg_rutina.cerrar_asignacion", [asi_rut_id, entrenador_id, estado])
