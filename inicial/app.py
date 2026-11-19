# Sistema de Solicitudes Academicas - VERSION INICIAL
# (deuda tecnica deliberada para el diagnostico del TPI)
import json
import os
import sys
from datetime import datetime

ARCHIVO = "datos.json"
solicitudes = []
estudiantes = []
contador = 0
responsables = ["Alumnado", "Bedelia", "Secretaria Academica"]


def cargar():
    global solicitudes, estudiantes, contador
    try:
        f = open(ARCHIVO, "r", encoding="utf-8")
        d = json.load(f)
        solicitudes = d["solicitudes"]
        estudiantes = d["estudiantes"]
        contador = d["contador"]
        f.close()
    except:
        solicitudes = []
        estudiantes = []
        contador = 0


def guardar():
    f = open(ARCHIVO, "w", encoding="utf-8")
    json.dump({"contador": contador, "estudiantes": estudiantes,
               "solicitudes": solicitudes}, f, indent=2, ensure_ascii=False)
    f.close()


def crear_solicitud(legajo, nombre, tipo, prioridad, desc):
    global contador
    existe = False
    for e in estudiantes:
        if e["legajo"] == legajo:
            existe = True
    if not existe:
        estudiantes.append({"legajo": legajo, "nombre": nombre})
    if tipo == "BAJA":
        prioridad = "ALTA"
    contador = contador + 1
    solicitudes.append({"id": contador, "legajo": legajo, "tipo": tipo,
                        "prioridad": prioridad, "estado": "PENDIENTE",
                        "descripcion": desc, "responsable": None,
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")})
    guardar()
    print("Solicitud #" + str(contador) + " registrada (estado PENDIENTE, prioridad " + prioridad + ")")


def opcion_registrar():
    legajo = input("Legajo: ").strip()
    nombre = input("Nombre del estudiante: ").strip()
    tipo = input("Tipo (CONSTANCIA/EQUIVALENCIA/BAJA/OTRO): ").strip().upper()
    prioridad = input("Prioridad (ALTA/MEDIA/BAJA): ").strip().upper()
    desc = input("Descripcion: ").strip()
    if legajo == "":
        print("Error: legajo obligatorio")
    else:
        if not legajo.isdigit():
            print("Error: el legajo debe ser numerico")
        else:
            existe = False
            for e in estudiantes:
                if e["legajo"] == legajo:
                    existe = True
            if not existe and nombre == "":
                print("Error: nombre obligatorio para estudiante nuevo")
            else:
                if tipo not in ["CONSTANCIA", "EQUIVALENCIA", "BAJA", "OTRO"]:
                    print("Error: tipo invalido")
                else:
                    if prioridad not in ["ALTA", "MEDIA", "BAJA"]:
                        print("Error: prioridad invalida")
                    else:
                        if desc == "":
                            print("Error: descripcion obligatoria")
                        else:
                            if len(desc) > 200:
                                print("Error: descripcion demasiado larga (max 200)")
                            else:
                                crear_solicitud(legajo, nombre, tipo, prioridad, desc)


def opcion_cambiar_estado():
    id_txt = input("ID de solicitud: ").strip()
    if not id_txt.isdigit():
        print("Error: ID invalido")
        return
    s = None
    for x in solicitudes:
        if x["id"] == int(id_txt):
            s = x
    if s is None:
        print("Error: solicitud no encontrada")
        return
    nuevo = input("Nuevo estado (EN_PROCESO/RESUELTA/RECHAZADA): ").strip().upper()
    if nuevo not in ["PENDIENTE", "EN_PROCESO", "RESUELTA", "RECHAZADA"]:
        print("Error: estado invalido")
        return
    actual = s["estado"]
    if actual == "PENDIENTE":
        if nuevo != "EN_PROCESO" and nuevo != "RECHAZADA":
            print("Error: transicion no permitida de " + actual + " a " + nuevo)
            return
    elif actual == "EN_PROCESO":
        if nuevo != "RESUELTA" and nuevo != "RECHAZADA":
            print("Error: transicion no permitida de " + actual + " a " + nuevo)
            return
    else:
        print("Error: transicion no permitida de " + actual + " a " + nuevo)
        return
    if nuevo == "EN_PROCESO" and s["responsable"] is None:
        print("Error: debe asignar un responsable antes de pasar a EN_PROCESO")
        return
    s["estado"] = nuevo
    guardar()
    print("Solicitud #" + str(s["id"]) + " ahora esta " + nuevo)


def opcion_asignar():
    id_txt = input("ID de solicitud: ").strip()
    if not id_txt.isdigit():
        print("Error: ID invalido")
        return
    s = None
    for x in solicitudes:
        if x["id"] == int(id_txt):
            s = x
    if s is None:
        print("Error: solicitud no encontrada")
        return
    if s["estado"] == "RESUELTA" or s["estado"] == "RECHAZADA":
        print("Error: la solicitud ya esta cerrada")
        return
    n = input("Responsable: ").strip()
    r = None
    for x in responsables:
        if x.lower() == n.lower():
            r = x
    if r is None:
        print("Error: responsable inexistente")
        return
    s["responsable"] = r
    guardar()
    print("Solicitud #" + str(s["id"]) + " asignada a " + r)


def opcion_buscar():
    campo = input("Filtrar por (estado/tipo/prioridad/legajo/ninguno): ").strip().lower()
    res = []
    if campo == "ninguno":
        res = solicitudes
    elif campo == "estado":
        v = input("Valor: ").strip().upper()
        for s in solicitudes:
            if s["estado"] == v:
                res.append(s)
    elif campo == "tipo":
        v = input("Valor: ").strip().upper()
        for s in solicitudes:
            if s["tipo"] == v:
                res.append(s)
    elif campo == "prioridad":
        v = input("Valor: ").strip().upper()
        for s in solicitudes:
            if s["prioridad"] == v:
                res.append(s)
    elif campo == "legajo":
        v = input("Valor: ").strip()
        for s in solicitudes:
            if s["legajo"] == v:
                res.append(s)
    else:
        print("Error: criterio de filtro invalido")
        return
    if len(res) == 0:
        print("Sin resultados")
    for s in res:
        nom = ""
        for e in estudiantes:
            if e["legajo"] == s["legajo"]:
                nom = e["nombre"]
        resp = "-"
        if s["responsable"] is not None:
            resp = s["responsable"]
        print("#" + str(s["id"]) + " | " + s["legajo"] + " " + nom + " | " + s["tipo"]
              + " | " + s["prioridad"] + " | " + s["estado"] + " | " + resp)


def opcion_reporte():
    print("--- REPORTE ---")
    print("Total de solicitudes: " + str(len(solicitudes)))
    print("Por estado:")
    for e in ["PENDIENTE", "EN_PROCESO", "RESUELTA", "RECHAZADA"]:
        c = 0
        for s in solicitudes:
            if s["estado"] == e:
                c = c + 1
        print("  " + e + ": " + str(c))
    print("Por tipo:")
    for t in ["CONSTANCIA", "EQUIVALENCIA", "BAJA", "OTRO"]:
        c = 0
        for s in solicitudes:
            if s["tipo"] == t:
                c = c + 1
        print("  " + t + ": " + str(c))
    print("Por prioridad:")
    for p in ["ALTA", "MEDIA", "BAJA"]:
        c = 0
        for s in solicitudes:
            if s["prioridad"] == p:
                c = c + 1
        print("  " + p + ": " + str(c))
    sin = 0
    for s in solicitudes:
        if s["responsable"] is None:
            sin = sin + 1
    print("Sin responsable asignado: " + str(sin))


def main():
    cargar()
    while True:
        print("")
        print("=== Gestion de Solicitudes Academicas ===")
        print("1. Registrar solicitud")
        print("2. Cambiar estado")
        print("3. Asignar responsable")
        print("4. Buscar / filtrar")
        print("5. Reporte")
        print("0. Salir")
        op = input("Opcion: ").strip()
        if op == "1":
            opcion_registrar()
        elif op == "2":
            opcion_cambiar_estado()
        elif op == "3":
            opcion_asignar()
        elif op == "4":
            opcion_buscar()
        elif op == "5":
            opcion_reporte()
        elif op == "0":
            print("Hasta luego")
            break
        else:
            print("Opcion invalida")


if __name__ == "__main__":
    main()
