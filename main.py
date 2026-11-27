from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import hashlib
import uuid
import sqlite3
from database import obtener_conexion

app = FastAPI(
    title="BarberFlow API",
    description="Sistema de gestión de citas y ventas para barberías",
    version="1.1.0"
)

TOKENS_ACTIVOS = {}

def inicializar_admin():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS administradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM administradores")
    if cursor.fetchone()[0] == 0:
        pass_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("INSERT INTO administradores (usuario, password_hash) VALUES (?, ?)", ("admin", pass_hash))
        conexion.commit()
    conexion.close()

inicializar_admin()

def verificar_admin(x_admin_token: str = Header(None)):
    if not x_admin_token or x_admin_token not in TOKENS_ACTIVOS:
        raise HTTPException(status_code=401, detail="Acceso no autorizado")
    return TOKENS_ACTIVOS[x_admin_token]

# ==================== AUTENTICACIÓN ====================

@app.post("/login")
def login(usuario: str, password: str):
    pass_hash = hashlib.sha256(password.encode()).hexdigest()
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id FROM administradores WHERE usuario = ? AND password_hash = ?", (usuario, pass_hash))
    user = cursor.fetchone()
    conexion.close()

    if user:
        token = str(uuid.uuid4())
        TOKENS_ACTIVOS[token] = usuario
        return {"token": token, "mensaje": "Inicio de sesión correcto"}
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

# ENTREGABLE 5: Modificar usuario y contraseña del administrador
@app.post("/cambiar-credenciales")
def cambiar_credenciales(nuevo_usuario: str, password_actual: str, nueva_password: str, admin_user: str = Depends(verificar_admin)):
    old_hash = hashlib.sha256(password_actual.encode()).hexdigest()
    new_hash = hashlib.sha256(nueva_password.encode()).hexdigest()

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id FROM administradores WHERE usuario = ? AND password_hash = ?", (admin_user, old_hash))
    user = cursor.fetchone()

    if not user:
        conexion.close()
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

    cursor.execute("UPDATE administradores SET usuario = ?, password_hash = ? WHERE usuario = ?", (nuevo_usuario, new_hash, admin_user))
    conexion.commit()
    conexion.close()

    for t, u in list(TOKENS_ACTIVOS.items()):
        if u == admin_user:
            TOKENS_ACTIVOS[t] = nuevo_usuario

    return {"mensaje": "Credenciales actualizadas con éxito"}

# ==================== SERVICIOS ====================

@app.get("/servicios")
def listar_servicios():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, precio, duracion_minutos FROM servicios")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "precio": f[2], "duracion_minutos": f[3]} for f in filas]

@app.post("/servicios")
def crear_servicio(nombre: str, precio: float, duracion_minutos: int, _: str = Depends(verificar_admin)):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO servicios (nombre, precio, duracion_minutos) VALUES (?, ?, ?)", (nombre, precio, duracion_minutos))
    conexion.commit()
    nuevo_id = cursor.lastrowid
    conexion.close()
    return {"mensaje": "Servicio registrado con éxito", "id": nuevo_id}

@app.put("/servicios/{servicio_id}")
def actualizar_servicio(servicio_id: int, nombre: str, precio: float, duracion_minutos: int, _: str = Depends(verificar_admin)):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE servicios 
        SET nombre = ?, precio = ?, duracion_minutos = ? 
        WHERE id = ?
    """, (nombre, precio, duracion_minutos, servicio_id))
    conexion.commit()
    conexion.close()
    return {"mensaje": f"Servicio {servicio_id} actualizado con éxito"}

@app.delete("/servicios/{servicio_id}")
def eliminar_servicio(servicio_id: int, _: str = Depends(verificar_admin)):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM servicios WHERE id = ?", (servicio_id,))
    conexion.commit()
    conexion.close()
    return {"mensaje": f"Servicio {servicio_id} eliminado con éxito"}

# ==================== BARBEROS ====================

@app.get("/barberos")
def listar_barberos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, telefono, activo FROM barberos")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "telefono": f[2], "activo": f[3]} for f in filas]

@app.post("/barberos")
def crear_barbero(nombre: str, telefono: str, _: str = Depends(verificar_admin)):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO barberos (nombre, telefono) VALUES (?, ?)", (nombre, telefono))
    conexion.commit()
    nuevo_id = cursor.lastrowid
    conexion.close()
    return {"mensaje": "Barbero registrado con éxito", "id": nuevo_id}

@app.delete("/barberos/{barbero_id}")
def eliminar_barbero(barbero_id: int, _: str = Depends(verificar_admin)):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM barberos WHERE id = ?", (barbero_id,))
    conexion.commit()
    conexion.close()
    return {"mensaje": f"Barbero {barbero_id} eliminado con éxito"}

# ==================== CITAS (ENTREGABLE 4) ====================

@app.post("/citas")
def crear_cita(cliente_nombre: str, cliente_telefono: str, barbero_id: int, servicio_id: int, fecha_hora: str):
    try:
        dt = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha u hora inválido. Usa YYYY-MM-DD HH:MM")

    # Validar Horario de Atención (09:00 a 19:00 hrs)
    HORA_INICIO = 9
    HORA_FIN = 19
    if dt.hour < HORA_INICIO or dt.hour >= HORA_FIN:
        raise HTTPException(
            status_code=400, 
            detail=f"El cliente no puede agendar fuera del horario de atención ({HORA_INICIO}:00 a {HORA_FIN}:00 hrs)."
        )

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # Validar Redundancia / Ocupación del barbero
    cursor.execute("""
        SELECT id FROM citas 
        WHERE barbero_id = ? AND fecha_hora = ? AND estado != 'Cancelada'
    """, (barbero_id, fecha_hora))
    if cursor.fetchone():
        conexion.close()
        raise HTTPException(
            status_code=400, 
            detail="El barbero ya está ocupado en esa hora. Por favor selecciona otro horario o barbero."
        )

    cursor.execute(
        "INSERT INTO citas (cliente_nombre, cliente_telefono, barbero_id, servicio_id, fecha_hora) VALUES (?, ?, ?, ?, ?)",
        (cliente_nombre, cliente_telefono, barbero_id, servicio_id, fecha_hora)
    )
    conexion.commit()
    nuevo_id = cursor.lastrowid
    conexion.close()
    return {"mensaje": "Cita agendada con éxito", "id": nuevo_id}

@app.get("/citas")
def listar_citas(_: str = Depends(verificar_admin)):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT c.id, c.cliente_nombre, c.cliente_telefono, b.nombre, s.nombre, c.fecha_hora, c.estado
        FROM citas c
        JOIN barberos b ON c.barbero_id = b.id
        JOIN servicios s ON c.servicio_id = s.id
    """)
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "cliente": f[1], "telefono": f[2], "barbero": f[3], "servicio": f[4], "fecha_hora": f[5], "estado": f[6]} for f in filas]

@app.put("/citas/{cita_id}")
def actualizar_estado_cita(cita_id: int, estado: str, _: str = Depends(verificar_admin)):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE citas SET estado = ? WHERE id = ?", (estado, cita_id))
    conexion.commit()
    conexion.close()
    return {"mensaje": f"Cita {cita_id} actualizada a {estado}"}

@app.delete("/citas/{cita_id}")
def eliminar_cita(cita_id: int, _: str = Depends(verificar_admin)):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM citas WHERE id = ?", (cita_id,))
    conexion.commit()
    conexion.close()
    return {"mensaje": f"Cita {cita_id} eliminada con éxito"}

@app.get("/ingresos")
def obtener_ingresos(_: str = Depends(verificar_admin)):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT SUM(s.precio) 
        FROM citas c 
        JOIN servicios s ON c.servicio_id = s.id 
        WHERE c.estado = 'Completada'
    """)
    resultado = cursor.fetchone()[0]
    conexion.close()
    total = resultado if resultado is not None else 0.0
    return {"total_ingresos": total}

import os
import json
import urllib.request
import urllib.error
from pydantic import BaseModel

class ConsultaAsistente(BaseModel):
    categoria: str              # "cabello" o "barba"
    tipo_cabello: str | None = None
    largo_cabello: str | None = None
    estado_barba: str | None = None
    preferencia_extra: str | None = None

def recomendacion_respaldo(datos: ConsultaAsistente) -> str:
    if datos.categoria == "cabello":
        tipo = datos.tipo_cabello or "tu tipo de cabello"
        largo = datos.largo_cabello or "tu largo actual"
        return (
            f"Para cabello {tipo} de largo {largo}, te conviene un corte con textura o degradado "
            f"lateral limpio que aporte equilibrio y sea fácil de peinar en el día a día. "
            f"Pídele a tu barbero: 'Quiero un corte limpio en los laterales y mantener textura arriba "
            f"adaptado a mi cabello {tipo.lower()}'."
        )
    estado = datos.estado_barba or "tu barba actual"
    return (
        f"Para una barba {estado}, lo ideal es mantener orden en el contorno sin perder naturalidad. "
        f"Pídele a tu barbero: 'Perfilado limpio en mejillas y cuello respetando mi crecimiento natural, "
        f"con rebaje parejo para que se vea uniforme'."
    )

@app.post("/asistente-estilo")
def consultar_asistente_estilo(datos: ConsultaAsistente):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "respuesta": recomendacion_respaldo(datos),
            "modo": "respaldo_sin_api_key"
        }

    if datos.categoria == "cabello":
        contexto = (
            f"El cliente quiere asesoría para CORTE DE CABELLO. "
            f"Tipo de cabello: {datos.tipo_cabello or 'no especificado'}. "
            f"Largo actual: {datos.largo_cabello or 'no especificado'}. "
            f"Nota adicional: {datos.preferencia_extra or 'ninguna'}."
        )
    else:
        contexto = (
            f"El cliente quiere asesoría para CORTE DE BARBA. "
            f"Estado actual de la barba: {datos.estado_barba or 'no especificado'}. "
            f"Nota adicional: {datos.preferencia_extra or 'ninguna'}."
        )

    prompt = (
        "Actúa como un barbero profesional y estilista de BarberFlow. "
        "Responde en español, de forma directa, amable y clara (máximo 120 palabras). "
        "Indica 2 opciones de estilo que le favorezcan y explica brevemente cómo pedírselo "
        "exactamente a su barbero según su condición actual.\n\n"
        f"{contexto}"
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 250}
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            candidatos = body.get("candidates", [])
            partes = candidatos[0].get("content", {}).get("parts", []) if candidatos else []
            texto = partes[0].get("text", "").strip() if partes else ""
            if texto:
                return {"respuesta": texto, "modo": "gemini"}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, IndexError, json.JSONDecodeError):
        pass

    return {
        "respuesta": recomendacion_respaldo(datos),
        "modo": "respaldo_error_api"
    }

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/login.html")
def login_view():
    return FileResponse("static/login.html")

@app.get("/admin.html")
def admin_view():
    return FileResponse("static/admin.html")