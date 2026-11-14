"""
Pasarela FALSA para probar la aplicacion sin Oracle (solo para pruebas locales).
Imita las funciones de los paquetes PKG_* con datos en memoria equivalentes a DATOS.sql.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta

from werkzeug.security import generate_password_hash

from saiyagym.db.gateway import AppError

HASH = generate_password_hash("Saiya2026*", method="pbkdf2:sha256:1000")
HOY = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def d(dias):
    return HOY + timedelta(days=dias)


USUARIOS = [
    dict(usuid=1, usuidentificacion="1002001001", usunombre="Laura", usuapellido="Gomez", usucorreo="laura.gomez@saiyagym.com",
         usutelefono="3101112233", usucontrasena=HASH, usuestado="ACTIVO", usufecharegistro=d(-300), rolnombre="ADMINISTRADOR"),
    dict(usuid=2, usuidentificacion="1002001002", usunombre="Carlos", usuapellido="Mendoza", usucorreo="carlos.mendoza@saiyagym.com",
         usutelefono="3112223344", usucontrasena=HASH, usuestado="ACTIVO", usufecharegistro=d(-300), rolnombre="ENTRENADOR"),
    dict(usuid=3, usuidentificacion="1002001003", usunombre="Andrea", usuapellido="Ruiz", usucorreo="andrea.ruiz@saiyagym.com",
         usutelefono="3123334455", usucontrasena=HASH, usuestado="ACTIVO", usufecharegistro=d(-300), rolnombre="ENTRENADOR"),
    dict(usuid=4, usuidentificacion="1061000004", usunombre="Mateo", usuapellido="Herrera", usucorreo="mateo.herrera@gmail.com",
         usutelefono="3134445566", usucontrasena=HASH, usuestado="ACTIVO", usufecharegistro=d(-120), rolnombre="CLIENTE"),
    dict(usuid=5, usuidentificacion="1061000005", usunombre="Sofia", usuapellido="Castillo", usucorreo="sofia.castillo@hotmail.com",
         usutelefono="3145556677", usucontrasena=HASH, usuestado="ACTIVO", usufecharegistro=d(-60), rolnombre="CLIENTE"),
    dict(usuid=10, usuidentificacion="1061000010", usunombre="Santiago", usuapellido="Ibarra", usucorreo="santiago.ibarra@hotmail.com",
         usutelefono=None, usucontrasena=HASH, usuestado="INACTIVO", usufecharegistro=d(-200), rolnombre="CLIENTE"),
]
TIPOS = [
    dict(memid=1, memnombre="Mensual", memduracion=30, memprecio=90000, memdescripcion="Acceso total por 30 dias", memestado="ACTIVA"),
    dict(memid=4, memnombre="Anual", memduracion=365, memprecio=800000, memdescripcion="Acceso total por 365 dias", memestado="ACTIVA"),
    dict(memid=5, memnombre="Pase semanal", memduracion=7, memprecio=30000, memdescripcion="Descontinuada", memestado="INACTIVA"),
]
ADQ = [
    dict(climemid=2, usuid=4, cliente="Mateo Herrera", memnombre="Mensual", climemfechainicio=d(-10), climemfechafin=d(20),
         climemestado="ACTIVA", climemvalor=90000, totalpagado=45000, saldo=45000),
    dict(climemid=3, usuid=5, cliente="Sofia Castillo", memnombre="Anual", climemfechainicio=d(-100), climemfechafin=d(265),
         climemestado="ACTIVA", climemvalor=800000, totalpagado=800000, saldo=0),
    dict(climemid=7, usuid=4, cliente="Mateo Herrera", memnombre="Mensual", climemfechainicio=d(-80), climemfechafin=d(-50),
         climemestado="PENDIENTE", climemvalor=90000, totalpagado=0, saldo=90000),
]
PAGOS = [
    dict(pagid=1, climemid=2, usuid=4, cliente="Mateo Herrera", memnombre="Mensual", pagfecha=d(-9), pagvalor=45000, pagmetodo="NEQUI", pagestado="PAGADO"),
    dict(pagid=2, climemid=7, usuid=4, cliente="Mateo Herrera", memnombre="Mensual", pagfecha=d(-3), pagvalor=90000, pagmetodo="EFECTIVO", pagestado="PENDIENTE"),
]
EJE = [
    dict(ejeid=1, ejenombre="Sentadilla", ejedescripcion="Con barra", ejegrupomuscular="Piernas", ejeniveldificultad="INTERMEDIO", enrutinas=2),
    dict(ejeid=2, ejenombre="Press de banca", ejedescripcion=None, ejegrupomuscular="Pecho", ejeniveldificultad="INTERMEDIO", enrutinas=1),
    dict(ejeid=3, ejenombre="Burpees", ejedescripcion="Cuerpo completo", ejegrupomuscular="Cardio", ejeniveldificultad="AVANZADO", enrutinas=0),
]
RUT = [
    dict(rutid=1, rutnombre="Full Body Inicial", rutobjetivo="Acondicionamiento", rutnivel="PRINCIPIANTE", rutdescripcion="Inicio",
         rutentrenadorid=2, entrenador="Carlos Mendoza", numejercicios=2, numasignaciones=2),
    dict(rutid=2, rutnombre="Movilidad y Core", rutobjetivo="Flexibilidad", rutnivel="PRINCIPIANTE", rutdescripcion=None,
         rutentrenadorid=3, entrenador="Andrea Ruiz", numejercicios=0, numasignaciones=0),
]
LINEAS = {1: [dict(rutejeid=1, ejeid=1, ejenombre="Sentadilla", ejegrupomuscular="Piernas", ejeniveldificultad="INTERMEDIO",
                   rutejeseries=3, rutejerepeticiones=12, rutejedescanso=60),
              dict(rutejeid=2, ejeid=2, ejenombre="Press de banca", ejegrupomuscular="Pecho", ejeniveldificultad="INTERMEDIO",
                   rutejeseries=4, rutejerepeticiones=10, rutejedescanso=90)], 2: []}
ASI = [
    dict(asirutid=1, usuid=4, rutid=1, asirutentrenadorid=2, cliente="Mateo Herrera", entrenador="Carlos Mendoza", rutnombre="Full Body Inicial",
         rutobjetivo="Acondicionamiento", rutnivel="PRINCIPIANTE", asirutfechaasignacion=d(-9), asirutfechafinalizacion=None, asirutestado="ACTIVA"),
    dict(asirutid=2, usuid=5, rutid=1, asirutentrenadorid=3, cliente="Sofia Castillo", entrenador="Andrea Ruiz", rutnombre="Full Body Inicial",
         rutobjetivo="Acondicionamiento", rutnivel="PRINCIPIANTE", asirutfechaasignacion=d(-30), asirutfechafinalizacion=d(-2), asirutestado="FINALIZADA"),
]
ASIST = {4: [dict(asiid=i, usuid=4, asifecha=d(-i), asihoraentrada="06:30") for i in (0, 1, 2)], 5: []}
LOGROS = [dict(dias=3, estado="LOGRADO", titulo="a"), dict(dias=7, estado="PENDIENTE", titulo="b"),
          dict(dias=14, estado="PENDIENTE", titulo="c"), dict(dias=30, estado="PENDIENTE", titulo="d")]


class FakeGateway:
    def __init__(self):
        self.llamadas: list[tuple] = []
        self.falla_con: dict[str, str] = {}          # nombre -> mensaje (simula regla de negocio violada)

    # ------------------------------------------------------------------
    def filas(self, f, *p):
        self.llamadas.append((f, p))
        if f in self.falla_con:
            raise AppError(self.falla_con[f])
        if f == "pkg_usuario.consultar":
            rol, q = p
            return [u for u in USUARIOS if (not rol or u["rolnombre"] == rol)
                    and (not q or q.lower() in (u["usunombre"] + u["usucorreo"]).lower())]
        if f == "pkg_usuario.obtener":
            return [u for u in USUARIOS if u["usuid"] == p[0]]
        if f == "pkg_usuario.obtener_por_correo":
            return [u for u in USUARIOS if u["usucorreo"] == p[0].lower()]
        if f == "pkg_usuario.clientes_de_entrenador":
            ids = {a["usuid"] for a in ASI if a["asirutentrenadorid"] == p[0]}
            return [dict(u, asignaciones=1, ultimaasignacion=d(-9)) for u in USUARIOS if u["usuid"] in ids]
        if f == "pkg_usuario.listar_roles":
            return [dict(rolid=1, rolnombre="ADMINISTRADOR"), dict(rolid=2, rolnombre="ENTRENADOR"), dict(rolid=3, rolnombre="CLIENTE")]
        if f == "pkg_membresia.consultar_tipos":
            return [t for t in TIPOS if not p[0] or t["memestado"] == "ACTIVA"]
        if f == "pkg_membresia.consultar_adquiridas":
            return [a for a in ADQ if p[0] is None or a["usuid"] == p[0]]
        if f == "pkg_membresia.membresia_vigente":
            v = [dict(a, diasrestantes=20) for a in ADQ if a["usuid"] == p[0] and a["climemestado"] == "ACTIVA"]
            return v
        if f == "pkg_pago.consultar":
            return [x for x in PAGOS if (p[0] is None or x["pagestado"] == p[0]) and (p[1] is None or x["usuid"] == p[1])]
        if f == "pkg_ejercicio.consultar":
            return [e for e in EJE if not p[0] or e["ejegrupomuscular"] == p[0]]
        if f == "pkg_ejercicio.grupos_musculares":
            return [dict(ejegrupomuscular=g) for g in sorted({e["ejegrupomuscular"] for e in EJE})]
        if f == "pkg_rutina.consultar":
            return [r for r in RUT if p[0] is None or r["rutentrenadorid"] == p[0]]
        if f == "pkg_rutina.obtener":
            return [r for r in RUT if r["rutid"] == p[0]]
        if f == "pkg_rutina.ejercicios_de_rutina":
            return LINEAS.get(p[0], [])
        if f == "pkg_rutina.consultar_asignaciones":
            return [a for a in ASI if (p[0] is None or a["asirutentrenadorid"] == p[0]) and (p[1] is None or a["usuid"] == p[1])]
        if f == "pkg_asistencia.consultar":
            return ASIST.get(p[0], [])
        if f == "pkg_asistencia.historial_rachas":
            return [dict(rachainicio=d(-2), rachafin=d(0), rachadias=3)] if p[0] == 4 else []
        if f == "pkg_asistencia.logros":
            return LOGROS
        if f == "pkg_reportes.resumen_general":
            return [dict(clientes_activos=2, membresias_vigentes=2, pagos_pendientes=1, recaudo_mes=845000, asistencias_hoy=1,
                         entrenadores=2, por_vencer=1, asignaciones_activas=3, cartera=135000, asistencias_semana=9)]
        if f == "pkg_reportes.graf_recaudo_mensual":
            return [dict(etiqueta=m, valor=v, actual=int(m == "Nov")) for m, v in
                    zip(["Jun", "Jul", "Ago", "Sep", "Oct", "Nov"], [1200000, 1850000, 1500000, 2100000, 1750000, 845000])]
        if f == "pkg_reportes.graf_asistencia_diaria":
            return [dict(etiqueta=f"{i + 1:02d}", valor=v, actual=int(i == 13)) for i, v in enumerate([3, 5, 4, 0, 6, 7, 2, 4, 5, 6, 8, 3, 5, 4])]
        if f == "pkg_reportes.graf_membresias_estado":
            return [dict(etiqueta="ACTIVA", valor=5), dict(etiqueta="VENCIDA", valor=3), dict(etiqueta="PENDIENTE", valor=1)]
        if f == "pkg_reportes.graf_ventas_tipo":
            return [dict(etiqueta="Mensual", valor=4), dict(etiqueta="Trimestral", valor=2), dict(etiqueta="Anual", valor=1)]
        if f == "pkg_reportes.graf_clientes_entrenador":
            return [dict(etiqueta="Carlos Mendoza", valor=3), dict(etiqueta="Andrea Ruiz", valor=2)]
        if f.startswith("pkg_reportes.rep"):
            return [dict(cliente="Mateo Herrera", membresia="Mensual", valor="$ 90.000", estado="PENDIENTE", n=3, correo="x@y.co",
                         vencio="01/10/2026", saldo="$ 45.000", racha_actual=3, mejor_racha=7, asistencias=11)]
        if f == "pkg_diccionario.tablas":
            return [dict(tabla="USUARIO", columnas=10, restricciones=8, indices=3)]
        if f == "pkg_diccionario.columnas":
            return [dict(posicion=1, columna="USUID", tipo="NUMBER(10)", admite_nulos="NO", llave="PK")] if p[0] == "USUARIO" else []
        if f == "pkg_diccionario.restricciones":
            return [dict(restriccion="PK_USUARIO", tipo="PRIMARY KEY", estado="ENABLED", referencia=None)]
        if f == "pkg_diccionario.indices":
            return [dict(indice="PK_USUARIO", unicidad="UNIQUE", columnas="USUID")]
        if f == "pkg_diccionario.procedimientos":
            return [dict(objeto="PKG_PAGO", tipo="PACKAGE", estado="VALID", modificado="01/11/2026 10:00")]
        if f == "pkg_diccionario.subprogramas":
            return [dict(paquete="PKG_PAGO", subprograma="REGISTRAR", parametros=5)]
        if f == "pkg_diccionario.codigo_fuente":
            return [dict(linea=1, codigo="PACKAGE pkg_pago AS"), dict(linea=2, codigo="END pkg_pago;")] if p[0] == "PKG_PAGO" else []
        if f == "pkg_diccionario.secuencias":
            return [dict(secuencia="SEQ_USUARIO", minimo=1, incremento=1, siguiente_valor=100)]
        raise AssertionError(f"funcion no simulada: {f}")

    def fila(self, f, *p):
        r = self.filas(f, *p)
        return r[0] if r else None

    def escalar(self, f, tipo, *p):
        self.llamadas.append((f, p))
        if f in self.falla_con:
            raise AppError(self.falla_con[f])
        if f == "pkg_usuario.es_cliente_de":
            return 1 if (p[0], p[1]) in {(2, 4), (3, 5)} else 0
        valores = {"pkg_membresia.actualizar_estados": 2, "pkg_pago.saldo": 45000,
                   "pkg_asistencia.racha_actual": 3, "pkg_asistencia.mejor_racha": 7,
                   "pkg_asistencia.estado_racha": "VIGENTE", "pkg_asistencia.asistio_hoy": 0}
        return valores[f]

    def procedimiento(self, nombre, entradas=(), salidas=()):
        self.llamadas.append((nombre, tuple(entradas)))
        if nombre in self.falla_con:
            raise AppError(self.falla_con[nombre])
        return [777 for _ in salidas]
