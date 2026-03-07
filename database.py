import sqlite3
from datetime import date

def init_db():
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            alimento TEXT,
            gramos REAL,
            kcal REAL,
            proteinas REAL,
            carbos REAL,
            grasas REAL
        )
    """)
    conn.commit()
    conn.close()

def guardar_comida(alimento, gramos, kcal, proteinas, carbos, grasas):
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO registros (fecha, alimento, gramos, kcal, proteinas, carbos, grasas)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (str(date.today()), alimento, gramos, kcal, proteinas, carbos, grasas))
    conn.commit()
    conn.close()

def resumen_hoy():
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("""
        SELECT alimento, gramos, kcal, proteinas, carbos, grasas
        FROM registros WHERE fecha = ?
    """, (str(date.today()),))
    filas = c.fetchall()
    conn.close()
    return filas


def borrar_ultimo():
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("""
        DELETE FROM registros 
        WHERE id = (SELECT MAX(id) FROM registros WHERE fecha = ?)
    """, (str(date.today()),))
    filas_afectadas = c.rowcount
    conn.commit()
    conn.close()
    return filas_afectadas > 0


def historial_semana():
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("""
        SELECT fecha, SUM(kcal), SUM(proteinas), SUM(carbos), SUM(grasas)
        FROM registros
        GROUP BY fecha
        ORDER BY fecha DESC
        LIMIT 7
    """)
    filas = c.fetchall()
    conn.close()
    return filas

def guardar_objetivo(kcal: float):
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS config (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)
    c.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('objetivo_kcal', ?)", (str(kcal),))
    conn.commit()
    conn.close()

def obtener_objetivo():
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    c.execute("SELECT valor FROM config WHERE clave = 'objetivo_kcal'")
    fila = c.fetchone()
    conn.close()
    return float(fila[0]) if fila else 2500.0  # 2500 por defecto
