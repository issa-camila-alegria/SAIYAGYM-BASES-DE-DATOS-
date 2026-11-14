"""Repositorio de usuarios -> paquete PKG_USUARIO."""
from __future__ import annotations
from ..db.gateway import Gateway


class UsuarioRepo:
    def __init__(self, gw: Gateway):
        self.gw = gw

    def consultar(self, rol: str | None = None, buscar: str | None = None) -> list[dict]:
        return self.gw.filas("pkg_usuario.consultar", rol, buscar)

    def obtener(self, usu_id: int) -> dict | None:
        return self.gw.fila("pkg_usuario.obtener", usu_id)

    def obtener_por_correo(self, correo: str) -> dict | None:
        return self.gw.fila("pkg_usuario.obtener_por_correo", correo)

    def insertar(self, d: dict, hash_clave: str) -> int:
        (nuevo_id,) = self.gw.procedimiento(
            "pkg_usuario.insertar",
            [d["identificacion"], d["nombre"], d["apellido"], d["correo"],
             d["telefono"], hash_clave, d["rol_id"]],
            [int],
        )
        return int(nuevo_id)

    def actualizar(self, usu_id: int, d: dict) -> None:
        self.gw.procedimiento(
            "pkg_usuario.actualizar",
            [usu_id, d["identificacion"], d["nombre"], d["apellido"], d["correo"], d["telefono"]],
        )

    def cambiar_contrasena(self, usu_id: int, hash_clave: str) -> None:
        self.gw.procedimiento("pkg_usuario.cambiar_contrasena", [usu_id, hash_clave])

    def cambiar_estado(self, usu_id: int, estado: str) -> None:
        self.gw.procedimiento("pkg_usuario.cambiar_estado", [usu_id, estado])

    def eliminar(self, usu_id: int) -> None:
        self.gw.procedimiento("pkg_usuario.eliminar", [usu_id])

    def clientes_de_entrenador(self, entrenador_id: int) -> list[dict]:
        return self.gw.filas("pkg_usuario.clientes_de_entrenador", entrenador_id)

    def es_cliente_de(self, entrenador_id: int, cliente_id: int) -> bool:
        import oracledb
        return bool(self.gw.escalar("pkg_usuario.es_cliente_de", oracledb.DB_TYPE_NUMBER,
                                    entrenador_id, cliente_id))

    def roles(self) -> list[dict]:
        return self.gw.filas("pkg_usuario.listar_roles")
