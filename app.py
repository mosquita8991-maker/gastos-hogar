import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Gastos", page_icon="💰", layout="wide")

conn = sqlite3.connect("gastos_hogar.db", check_same_thread=False)
cursor = conn.cursor()

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

st.title("💰 Control de Gastos del Hogar")

st.sidebar.header("📝 Registrar Gasto")
with st.sidebar.form("formulario_gasto", clear_on_submit=True):
    fecha = st.date_input("Fecha", datetime.now())
    descripcion = st.text_input("Descripcion")
    monto = st.number_input("Monto ($)", min_value=0.0, step=10.0, format="%.2f")
    categoria = st.selectbox("Categoria", ["Alimentos", "Servicios", "Alquiler", "Salidas", "Otros"])
    registrado_por = st.selectbox("Quien lo registro", ["Persona A", "Persona B"])
    boton_guardar = st.form_submit_button("Guardar Gasto")

if boton_guardar:
    if descripcion and monto > 0:
        cursor.execute("""
        INSERT INTO gastos (fecha, descripcion, monto, categoria, registrado_por)
        VALUES (?, ?, ?, ?, ?)
        """, (fecha.strftime("%Y-%m-%d"), descripcion, monto, categoria, registrado_por))
        conn.commit()
        st.sidebar.success("Guardado!")

df = pd.read_sql_query("SELECT * FROM gastos ORDER BY fecha DESC, id DESC", conn)

if not df.empty:
    total_gastado = df["monto"].sum()
    gastos_A = df[df["registrado_por"] == "Persona A"]["monto"].sum()
    gastos_B = df[df["registrado_por"] == "Persona B"]["monto"].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Gastado", f"${total_gastado:,.2f}")
    col2.metric("Persona A", f"${gastos_A:,.2f}")
    col3.metric("Persona B", f"${gastos_B:,.2f}")
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Gastos por Categoría")
        df_cat = df.groupby("categoria")["monto"].sum()
        st.bar_chart(df_cat)
    with c2:
        st.subheader("📋 Historial de Movimientos")
        st.dataframe(df[["fecha", "descripcion", "monto", "categoria", "registrado_por"]], use_container_width=True)
