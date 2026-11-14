"""
Pasarela de acceso a Oracle.

TODO el acceso a datos de la aplicacion pasa por esta clase y se limita a
LLAMAR procedimientos y funciones almacenadas de los paquetes PKG_* (rubrica:
"Acceso a datos con procedimientos almacenados"). La aplicacion no ejecuta
SQL directo sobre las tablas; ademas la cuenta SAIYA_APP solo tiene EXECUTE
sobre los paquetes.
"""
from __future__ import annotations
import logging
import re
from contextlib import contextmanager
from typing import Any, Iterable, Sequence

import oracledb

log = logging.getLogger("saiyagym.db")

# ORA-20xxx = errores de reglas de negocio lanzados por triggers y paquetes
_PATRON_ORA = re.compile(r"ORA-(20\d{3}):\s*(.+)")


class AppError(Exception):
    """Error con mensaje apto para mostrar al usuario."""

    def __init__(self, mensaje: str, codigo: int | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


def traducir_error(exc: oracledb.DatabaseError) -> AppError:
    """Convierte un error de Oracle en un AppError legible."""
    texto = str(exc)
    m = _PATRON_ORA.search(texto)
    if m:
        return AppError(m.group(2).split("\n")[0].strip(), int(m.group(1)))
    log.error("Error de base de datos: %s", texto)
    return AppError("No fue posible completar la operacion en la base de datos. Intente de nuevo.")


class Gateway:
    def __init__(self, config: dict):
        self._cfg = config
        self._pool: oracledb.ConnectionPool | None = None

    # -- conexion ---------------------------------------------------------
    def _pool_(self) -> oracledb.ConnectionPool:
        if self._pool is None:
            extra = {}
            if self._cfg.get("ORACLE_CONFIG_DIR"):          # Autonomous Database: tnsnames.ora
                extra["config_dir"] = self._cfg["ORACLE_CONFIG_DIR"]
            if self._cfg.get("ORACLE_WALLET_DIR"):          # Autonomous Database: ewallet.pem
                extra["wallet_location"] = self._cfg["ORACLE_WALLET_DIR"]
                extra["wallet_password"] = self._cfg.get("ORACLE_WALLET_PASSWORD")
            self._pool = oracledb.create_pool(
                user=self._cfg["ORACLE_USER"],
                password=self._cfg["ORACLE_PASSWORD"],
                dsn=self._cfg["ORACLE_DSN"],
                min=1, max=6, increment=1,
                **extra,
            )
        return self._pool

    @contextmanager
    def _conexion(self):
        try:
            conn = self._pool_().acquire()
        except oracledb.DatabaseError as exc:
            log.error("No se pudo conectar a Oracle: %s", exc)
            raise AppError("No hay conexion con la base de datos. Verifique que Oracle este en linea.") from exc
        try:
            # los paquetes viven en el esquema SAIYAGYM; la cuenta de la app no es duena
            conn.current_schema = self._cfg["ORACLE_SCHEMA"]
            yield conn
            conn.commit()
        except oracledb.DatabaseError as exc:
            conn.rollback()
            raise traducir_error(exc) from exc
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # -- operaciones ------------------------------------------------------
    def filas(self, funcion: str, *params: Any) -> list[dict]:
        """Llama una funcion que devuelve SYS_REFCURSOR y entrega una lista de dicts."""
        with self._conexion() as conn:
            cur = conn.cursor()
            ref = cur.callfunc(funcion, oracledb.DB_TYPE_CURSOR, list(params))
            columnas = [d[0].lower() for d in ref.description]
            return [dict(zip(columnas, fila)) for fila in ref.fetchall()]

    def fila(self, funcion: str, *params: Any) -> dict | None:
        filas = self.filas(funcion, *params)
        return filas[0] if filas else None

    def escalar(self, funcion: str, tipo: Any, *params: Any) -> Any:
        """Llama una funcion que devuelve un valor simple (NUMBER, VARCHAR2...)."""
        with self._conexion() as conn:
            return conn.cursor().callfunc(funcion, tipo, list(params))

    def procedimiento(self, nombre: str, entradas: Sequence[Any] = (),
                      salidas: Iterable[Any] = ()) -> list[Any]:
        """
        Llama un procedimiento. Los parametros OUT van al final; `salidas` indica
        su tipo (por ejemplo [int]). Devuelve los valores OUT en orden.
        """
        with self._conexion() as conn:
            cur = conn.cursor()
            variables = [cur.var(tipo) for tipo in salidas]
            cur.callproc(nombre, list(entradas) + variables)
            return [v.getvalue() for v in variables]
