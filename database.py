import sqlite3
from datetime import date

def init_db():
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            fecha TEXT,
            alimento TEXT,
            gramos REAL,
            kcal REAL,
            proteinas REAL,
            carbos REAL,
            grasas REAL,
            comida TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS config (
            user_id INTEGER,
            clave TEXT,
            valor TEXT,
            PRIMARY KEY (user_id, clave)
        )
    """)
    conn.commit()
    conn.close()

def guardar_comida(user_id, alimento, gramos, kcal, proteinas, carbos, grasas, comida):
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO registros (user_id, fecha, alimento, gramos, kcal, proteinas, carbos, grasas, comida)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, str(date.today()), alimento, gramos, kcal, proteinas, carbos, grasas, comida))
    conn.commit()
    conn.close()

def resumen_hoy(user_id):
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("""
        SELECT alimento, gramos, kcal, proteinas, carbos, grasas, comida
        FROM registros WHERE fecha = ? AND user_id = ?
        ORDER BY comida
    """, (str(date.today()), user_id))
    filas = c.fetchall()
    conn.close()
    return filas

def borrar_ultimo(user_id):
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("""
        DELETE FROM registros 
        WHERE id = (SELECT MAX(id) FROM registros WHERE fecha = ? AND user_id = ?)
    """, (str(date.today()), user_id))
    filas_afectadas = c.rowcount
    conn.commit()
    conn.close()
    return filas_afectadas > 0

def historial_semana(user_id):
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("""
        SELECT fecha, SUM(kcal), SUM(proteinas), SUM(carbos), SUM(grasas)
        FROM registros WHERE user_id = ?
        GROUP BY fecha
        ORDER BY fecha DESC
        LIMIT 7
    """, (user_id,))
    filas = c.fetchall()
    conn.close()
    return filas

def guardar_objetivo(user_id, kcal: float):
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO config (user_id, clave, valor) VALUES (?, 'objetivo_kcal', ?)", (user_id, str(kcal)))
    conn.commit()
    conn.close()

def obtener_objetivo(user_id):
    conn = sqlite3.connect("dieta.db")
    c = conn.cursor()
    c.execute("SELECT valor FROM config WHERE user_id = ? AND clave = 'objetivo_kcal'", (user_id,))
    fila = c.fetchone()
    conn.close()
    return float(fila[0]) if fila else 2500.0
