import sqlite3

NOMBRE_BD = "barberflow.db"

def obtener_conexion():
    """ Crea la conexión a la base de datos de SQLite """
    conexion = sqlite3.connect(NOMBRE_BD)
    # Habilitamos soporte para Llaves Foráneas en SQLite
    conexion.execute("PRAGMA foreign_keys = ON;")
    return conexion

def inicializar_base_datos():
    """ Crea las tablas necesarias si no existen """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # 1. Tabla de Servicios (Catálogo de lo que ofrece el negocio)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            duracion_minutos INTEGER NOT NULL
        )
    """)

    # 2. Tabla de Barberos / Estilistas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS barberos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            activo INTEGER DEFAULT 1
        )
    """)

    # 3. Tabla de Citas (El núcleo del negocio)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_nombre TEXT NOT NULL,
            cliente_telefono TEXT NOT NULL,
            barbero_id INTEGER NOT NULL,
            servicio_id INTEGER NOT NULL,
            fecha_hora TEXT NOT NULL,
            estado TEXT DEFAULT 'Pendiente',
            FOREIGN KEY (barbero_id) REFERENCES barberos (id),
            FOREIGN KEY (servicio_id) REFERENCES servicios (id)
        )
    """)

    conexion.commit()
    conexion.close()
    print("✅ Base de datos 'barberflow.db' inicializada correctamente con las 3 tablas.")

if __name__ == "__main__":
    inicializar_base_datos()