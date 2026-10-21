
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Control de Gastos del Hogar", page_icon="💰", layout="wide")

# Conexión a la base de datos SQLite
conn = sqlite3.connect("gastos_hogar.db", check_same_thread=False)
cursor = conn.cursor()

# Crear tabla si no existe
cursor.execute("""
CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    descripcion TEXT,
    monto REAL,
    categoria TEXT,
    registrado_por TEXT
)
""")
conn.commit()

# Título de la app
st.title("💰 Control de Gastos del Hogar")
st.markdown("Visualicen en tiempo real cuánto gastan y en qué conceptos, trabajando en equipo de forma simultánea.")

# Sidebar para ingresar datos
st.sidebar.header("📝 Registrar Gasto")
with st.sidebar.form("formulario_gasto", clear_on_submit=True):
    fecha = st.date_input("Fecha", datetime.now())
    descripcion = st.text_input("Descripción (ej. Supermercado, Luz, etc.)")
    monto = st.number_input("Monto ($)", min_value=0.0, step=10.0, format="%.2f")
    categoria = st.selectbox("Categoría", ["Alimentos", "Servicios (Luz/Agua/Internet)", "Alquiler/Vivienda", "Salidas/Entretenimiento", "Mascotas", "Salud/Farmacia", "Otros"])
    registrado_por = st.selectbox("¿Quién lo registró?", ["Persona A", "Persona B"])
    
    boton_guardar = st.form_submit_button("Guardar Gasto")

if boton_guardar:
    if descripcion and monto > 0:
        cursor.execute("""
        INSERT INTO gastos (fecha, descripcion, monto, categoria, registrado_por)
        VALUES (?, ?, ?, ?, ?)
        """, (fecha.strftime("%Y-%m-%d"), descripcion, monto, categoria, registrado_por))
        conn.commit()
        st.sidebar.success("¡Gasto guardado con éxito!")
    else:
        st.sidebar.error("Por favor, completa la descripción y el monto.")

# Leer datos actuales
df = pd.read_sql_query("SELECT * FROM gastos ORDER BY fecha DESC, id DESC", conn)

# --- PANEL DE CONTROL (MÉTRICAS) ---
st.subheader("📊 Totales Acumulados")

if not df.empty:
    total_gastado = df["monto"].sum()
    gastos_A = df[df["registrado_por"] == "Persona A"]["monto"].sum()
    gastos_B = df[df["registrado_por"] == "Persona B"]["monto"].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Gastado en el Hogar", f"${total_gastado:,.2f}")
    col2.metric("Registrado por Persona A", f"${gastos_A:,.2f}")
    col3.metric("Registrado por Persona B", f"${gastos_B:,.2f}")
    
    st.markdown("---")

    # --- GRÁFICOS Y TABLA ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🍕 ¿En qué gastamos? (Por Categoría)")
        # Agrupar datos para el gráfico
        df_cat = df.groupby("categoria")["monto"].sum().reset_index()
        fig = px.pie(df_cat, values="monto", names="categoria", hole=0.4, 
                     color_discrete_sequence=px.colors.sequential.Plotly3)
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.subheader("📋 Historial de Movimientos")
        # Mostrar tabla limpia sin la columna ID
        st.dataframe(df[["fecha", "descripcion", "monto", "categoria", "registrado_por"]], use_container_width=True, height=320)
        
        # Botón para borrar el último registro en caso de error
        if st.button("🗑️ Borrar último registro"):
            ultimo_id = df["id"].max()
            cursor.execute("DELETE FROM gastos WHERE id = ?", (int(ultimo_id),))
            conn.commit()
            st.warning("Último gasto eliminado.")
            st.rerun()
