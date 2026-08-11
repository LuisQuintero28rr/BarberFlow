from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
import hashlib
import uuid
import sqlite3
from database import obtener_conexion

app = FastAPI(
    title="BarberFlow API",
    description="Sistema de gestión de citas y ventas para barberías",
    version="1.1.0"
)

# Diccionario temporal para guardar tokens activos en memoria
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
    # Si no existe ningún admin, se crea uno por defecto: admin / admin123
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

@app.post("/cambiar-password")
def cambiar_password(password_actual: str, nueva_password: str, admin_user: str = Depends(verificar_admin)):
    old_hash = hashlib.sha256(password_actual.encode()).hexdigest()
    new_hash = hashlib.sha256(nueva_password.encode()).hexdigest()

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id FROM administradores WHERE usuario = ? AND password_hash = ?", (admin_user, old_hash))
    user = cursor.fetchone()

    if not user:
        conexion.close()
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

    cursor.execute("UPDATE administradores SET password_hash = ? WHERE usuario = ?", (new_hash, admin_user))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Contraseña actualizada con éxito"}

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

# ==================== CITAS ====================

@app.post("/citas")
def crear_cita(cliente_nombre: str, cliente_telefono: str, barbero_id: int, servicio_id: int, fecha_hora: str):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
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

app.mount("/", StaticFiles(directory="static", html=True), name="static")