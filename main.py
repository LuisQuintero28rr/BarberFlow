from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import sqlite3
from database import obtener_conexion

app = FastAPI(
    title="BarberFlow API",
    description="Sistema de gestión de citas y ventas para barberías",
    version="1.0.0"
)

# ==================== SERVICIOS ====================

# 1. Obtener la lista de servicios disponibles
@app.get("/servicios")
def listar_servicios():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, precio, duracion_minutos FROM servicios")
    filas = cursor.fetchall()
    conexion.close()
    
    servicios = []
    for fila in filas:
        servicios.append({
            "id": fila[0],
            "nombre": fila[1],
            "precio": fila[2],
            "duracion_minutos": fila[3]
        })
    return servicios

# 2. Agregar un nuevo servicio al catálogo
@app.post("/servicios")
def crear_servicio(nombre: str, precio: float, duracion_minutos: int):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO servicios (nombre, precio, duracion_minutos) VALUES (?, ?, ?)",
        (nombre, precio, duracion_minutos)
    )
    conexion.commit()
    nuevo_id = cursor.lastrowid
    conexion.close()
    return {"mensaje": "Servicio registrado con éxito", "id": nuevo_id}

# ==================== BARBEROS ====================

# 3. Registrar un nuevo barbero
@app.post("/barberos")
def crear_barbero(nombre: str, telefono: str):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO barberos (nombre, telefono) VALUES (?, ?)",
        (nombre, telefono)
    )
    conexion.commit()
    nuevo_id = cursor.lastrowid
    conexion.close()
    return {"mensaje": "Barbero registrado con éxito", "id": nuevo_id}

# 4. Obtener lista de barberos
@app.get("/barberos")
def listar_barberos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, telefono, activo FROM barberos")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "telefono": f[2], "activo": f[3]} for f in filas]

# ==================== CITAS ====================

# 5. Agendar una nueva cita
@app.post("/citas")
def crear_cita(cliente_nombre: str, cliente_telefono: str, barbero_id: int, servicio_id: int, fecha_hora: str):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """INSERT INTO citas (cliente_nombre, cliente_telefono, barbero_id, servicio_id, fecha_hora)
           VALUES (?, ?, ?, ?, ?)""",
        (cliente_nombre, cliente_telefono, barbero_id, servicio_id, fecha_hora)
    )
    conexion.commit()
    nuevo_id = cursor.lastrowid
    conexion.close()
    return {"mensaje": "Cita agendada con éxito", "id": nuevo_id}

# 6. Obtener todas las citas
@app.get("/citas")
def listar_citas():
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
    
    return [
        {
            "id": f[0],
            "cliente": f[1],
            "telefono": f[2],
            "barbero": f[3],
            "servicio": f[4],
            "fecha_hora": f[5],
            "estado": f[6]
        }
        for f in filas
    ]

# 7. Actualizar el estado de una cita (Pendiente -> Completada / Cancelada)
@app.put("/citas/{cita_id}")
def actualizar_estado_cita(cita_id: int, estado: str):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE citas SET estado = ? WHERE id = ?", (estado, cita_id))
    conexion.commit()
    conexion.close()
    return {"mensaje": f"Cita {cita_id} actualizada a {estado}"}

# 8. Obtener total de ingresos acumulados de citas completadas
@app.get("/ingresos")
def obtener_ingresos():
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

# 9. Eliminar una cita de la base de datos
@app.delete("/citas/{cita_id}")
def eliminar_cita(cita_id: int):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM citas WHERE id = ?", (cita_id,))
    conexion.commit()
    conexion.close()
    return {"mensaje": f"Cita {cita_id} eliminada con éxito"}

# ==================== ARCHIVOS ESTÁTICOS (FRONTEND) ====================
# Servir la interfaz gráfica alojada en la carpeta 'static'
app.mount("/", StaticFiles(directory="static", html=True), name="static")