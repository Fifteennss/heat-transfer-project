import streamlit as st
import pandas as pd
import numpy as np
from math import pi, log
from io import StringIO

# --- Conversión de unidades (se mantiene igual) ---
def convertir_temperatura(valor, unidad_origen, unidad_destino):
    if unidad_origen == unidad_destino:
        return valor
    if unidad_origen == "°F":
        valor = (valor - 32) * 5/9
    elif unidad_origen == "K":
        valor = valor - 273.15
    elif unidad_origen == "R":
        valor = (valor - 491.67) * 5/9

    if unidad_destino == "°F":
        return valor * 9/5 + 32
    elif unidad_destino == "K":
        return valor + 273.15
    elif unidad_destino == "R":
        return (valor + 273.15) * 9/5
    return valor

def convertir_velocidad(valor, unidad):
    factores = {"m/s": 1, "km/h": 1/3.6, "cm/s": 0.01, "ft/s": 0.3048, "mph": 0.44704}
    return valor * factores[unidad]

def convertir_longitud(valor, unidad):
    factores = {"m": 1, "mm": 0.001, "cm": 0.01, "ft": 0.3048, "in": 0.0254}
    return valor * factores[unidad]

# --- Carga de datos (se mantiene igual) ---
@st.cache_data
def cargar_datos():
    archivos = {
        "agua saturada": "tabla_a9.csv",
        "refrigerante 134a": "tabla_a10.csv",
        "amoniaco": "tabla_a11.csv",
        "propano": "tabla_a12.csv",
        "aire": "tabla_a15.csv",
        "glicerina": "tabla_glicerina.csv",
        "isobutano": "tabla_isobutano.csv",
        "metano": "tabla_metano.csv",
        "metanol": "tabla_metanol.csv",
        "aceite para motor": "tabla_aceitemotor.csv"
    }
    data = {}
    for nombre, archivo in archivos.items():
        try:
            data[nombre] = pd.read_csv(archivo)
        except Exception as e:
            st.error(f"No se pudo cargar {archivo}: {e}")
            data[nombre] = None
    return data

# --- Función de interpolación (se mantiene igual) ---
def interpolar_propiedades(df, T_pelicula, tiene_fases=False, fase=None):
    props = {}
    
    if tiene_fases and fase:
        sufijo = "líquido" if fase == "líquido" else "vapor"
        props = {
            'densidad': np.interp(T_pelicula, df['Temp. (°C)'], df[f'Densidad {sufijo} (kg/m³)']),
            'viscosidad': np.interp(T_pelicula, df['Temp. (°C)'], df[f'Viscosidad dinámica {sufijo} (kg/m·s)']),
            'k': np.interp(T_pelicula, df['Temp. (°C)'], df[f'Conductividad térmica {sufijo} (W/m·K)']),
            'Pr': np.interp(T_pelicula, df['Temp. (°C)'], df[f'Número de Prandtl {sufijo}'])
        }
    else:
        props = {
            'densidad': np.interp(T_pelicula, df['Temp. (°C)'], df['Densidad (kg/m³)']),
            'viscosidad': np.interp(T_pelicula, df['Temp. (°C)'], df['Viscosidad dinámica (kg/m·s)']),
            'k': np.interp(T_pelicula, df['Temp. (°C)'], df['Conductividad térmica (W/m·K)']),
            'Pr': np.interp(T_pelicula, df['Temp. (°C)'], df['Número de Prandtl'])
        }
    
    return props

# --- Función para calcular temperatura media logarítmica ---
def calcular_TML(T_entrada, T_salida, T_pared):
    ΔT1 = abs(T_pared - T_entrada)
    ΔT2 = abs(T_pared - T_salida) 
    if ΔT1 == ΔT2:
        return ΔT1  # Evita división por cero cuando ΔT1 = ΔT2
    return (ΔT2 - ΔT1) / log(ΔT2 / ΔT1)

# --- Programa principal modificado ---
st.title("Convección Interna Forzada en Tubos - Temperatura Constante")

fluidos = cargar_datos()

with st.sidebar:
    st.header("⚙️ Configuración")
    fluido = st.selectbox("Fluido", list(fluidos.keys()))
    
    fluidos_con_fases = ["agua saturada", "refrigerante 134a", "amoniaco", "propano"]
    tiene_fases = fluido in fluidos_con_fases
    
    if tiene_fases:
        fase = st.radio("Fase", ["líquido", "vapor"], horizontal=True)
    
    unidad_temp = st.selectbox("Unidad temperatura", ["°C", "°F", "K", "R"])
    unidad_vel = st.selectbox("Unidad velocidad", ["m/s", "km/h", "cm/s", "ft/s", "mph"])
    unidad_dia = st.selectbox("Unidad de diámetro", ["m", "mm", "cm", "ft", "in"])
    unidad_long = st.selectbox("Unidad de longitud", ["m", "mm", "cm", "ft", "in"])

col1, col2 = st.columns(2)
with col1:
    T_entrada_input = st.number_input(f"Temperatura de entrada del fluido ({unidad_temp})", value=25.0)
    velocidad_input = st.number_input(f"Velocidad del fluido ({unidad_vel})", value=1.0)
    diametro_input = st.number_input(f"Diámetro interno del tubo ({unidad_dia})", value=0.05)
with col2:
    T_pared_input = st.number_input(f"Temperatura de la pared ({unidad_temp})", value=100.0)
    longitud_input = st.number_input(f"Longitud del tubo ({unidad_long})", value=1.0)
    T_salida_input = st.number_input(f"Temperatura de salida del fluido ({unidad_temp})", value=50.0)

# Validación de temperatura
if unidad_temp in ["K", "R"] and (T_entrada_input < 0 or T_pared_input < 0 or T_salida_input < 0):
    st.error("❌ No se permiten temperaturas negativas en escalas absolutas")
    st.stop()

# Conversión de unidades
T_entrada = convertir_temperatura(T_entrada_input, unidad_temp, "°C")
T_pared = convertir_temperatura(T_pared_input, unidad_temp, "°C")
T_salida = convertir_temperatura(T_salida_input, unidad_temp, "°C")
velocidad = convertir_velocidad(velocidad_input, unidad_vel)
diametro = convertir_longitud(diametro_input, unidad_dia)
longitud = convertir_longitud(longitud_input, unidad_long)

# Cálculo de temperatura media logarítmica
TML = calcular_TML(T_entrada, T_salida, T_pared)
T_pelicula = (T_entrada + T_salida) / 2  # Temperatura promedio para propiedades

st.subheader("1. Temperaturas características")
col_temp1, col_temp2 = st.columns(2)
with col_temp1:
    st.metric("Temperatura media logarítmica", f"{TML:.2f} °C")
with col_temp2:
    st.metric("Temperatura de película", f"{T_pelicula:.2f} °C")

# Obtener datos del fluido seleccionado
df = fluidos[fluido]
if df is None:
    st.error("No hay datos del fluido seleccionado")
    st.stop()

# Interpolar propiedades
try:
    props = interpolar_propiedades(df, T_pelicula, tiene_fases, fase if tiene_fases else None)
    
    st.subheader("2. Propiedades termofísicas")
    col_prop1, col_prop2 = st.columns(2)
    with col_prop1:
        st.write(f"Densidad (ρ): {props['densidad']:.4f} kg/m³")
        st.write(f"Viscosidad (μ): {props['viscosidad']:.4e} kg/m·s")
    with col_prop2:
        st.write(f"Conductividad térmica (k): {props['k']:.4f} W/m·K")
        st.write(f"Número de Prandtl (Pr): {props['Pr']:.4f}")

    # Cálculo del número de Reynolds
    Re = (velocidad * diametro * props['densidad']) / props['viscosidad']
    st.subheader("3. Número de Reynolds")
    st.latex(rf"Re = \frac{{\rho \cdot v \cdot D}}{{\mu}} = {Re:.2f}")
    regimen = "Laminar" if Re < 2300 else ("Transición" if Re < 10000 else "Turbulento")
    st.info(f"Régimen del flujo: **{regimen}**")

    # Determinar si es calentamiento o enfriamiento
    if T_salida > T_entrada:  # Pared más caliente que el fluido -> calentamiento
        n = 0.4
        regimen_termico = "Calentamiento (n=0.4)"
    else:  # Pared más fría que el fluido -> enfriamiento
        n = 0.3
        regimen_termico = "Enfriamiento (n=0.3)"

    # Cálculo del número de Nusselt
    st.subheader("4. Número de Nusselt y coeficiente h")
    if Re < 2300:
        Nu = 3.66  # Para temperatura constante en flujo laminar
        st.latex(rf"Nu = {Nu:.2f} \quad \text{{(flujo laminar totalmente desarrollado)}}")
    else:
        Nu = 0.023 * (Re**0.8) * (props['Pr']**n)
        st.latex(rf"Nu = 0.023 \cdot Re^{{0.8}} \cdot Pr^{{{n}}} = {Nu:.2f}")
        st.info(f"Regimen térmico: **{regimen_termico}**")

    h = Nu * props['k'] / diametro
    st.latex(rf"h = \frac{{Nu \cdot k}}{{D}} = \frac{{{Nu:.2f} \times {props['k']:.4f}}}{{{diametro:.4f}}} = {h:.2f} \, \text{{W/m}}²\text{{K}}")

    # Cálculo de transferencia de calor
    A = pi * diametro * longitud
    q = h * A * TML
    
    st.subheader("5. Transferencia de calor")
    st.latex(rf"q = h \cdot A \cdot \Delta T_{{ml}} = {h:.2f} \times {A:.4f} \times {TML:.2f} = {q:.2f} \, \text{{W}}")
    st.success(f"**Transferencia de calor total:** {q:.2f} W")
    
    # --- EXPORTACIÓN A TXT ---
    st.subheader("Exportar Resultados")

    def crear_txt_resultados():
        """Función para crear el archivo TXT con todos los datos y resultados"""
        
        output = StringIO()
        
        # Encabezado
        output.write("="*80 + "\n")
        output.write("ANÁLISIS DE CONVECCIÓN INTERNA FORZADA EN TUBOS\n")
        output.write("="*80 + "\n\n")
        
        # Datos de entrada
        output.write("DATOS DE ENTRADA:\n")
        output.write("-"*50 + "\n")
        output.write(f"Fluido seleccionado:           {fluido}\n")
        if tiene_fases:
            output.write(f"Fase del fluido:               {fase}\n")
        output.write(f"Temperatura de entrada:        {T_entrada:.2f} °C\n")
        output.write(f"Temperatura de salida:         {T_salida:.2f} °C\n")
        output.write(f"Temperatura de pared:          {T_pared:.2f} °C\n")
        output.write(f"Velocidad del fluido:          {velocidad:.4f} m/s\n")
        output.write(f"Diámetro interno del tubo:     {diametro:.6f} m\n")
        output.write(f"Longitud del tubo:             {longitud:.4f} m\n")
        output.write(f"Régimen térmico:               {regimen_termico}\n")
        output.write(f"\nSistema de unidades usado:     Temp=°C, Vel=m/s, Long=m\n")
        output.write("\n")
        
        # Temperaturas características
        output.write("TEMPERATURAS CARACTERÍSTICAS:\n")
        output.write("-"*50 + "\n")
        output.write(f"Temperatura de película:       {T_pelicula:.4f} °C\n")
        output.write(f"Temperatura media logarítmica: {TML:.4f} °C\n")
        output.write("\n")
        
        # Propiedades termofísicas
        output.write("PROPIEDADES TERMOFÍSICAS (a temperatura de película):\n")
        output.write("-"*50 + "\n")
        output.write(f"Densidad (ρ):                  {props['densidad']:.6f} kg/m³\n")
        output.write(f"Viscosidad dinámica (μ):       {props['viscosidad']:.6e} kg/m·s\n")
        output.write(f"Conductividad térmica (k):     {props['k']:.6f} W/m·K\n")
        output.write(f"Número de Prandtl (Pr):        {props['Pr']:.6f}\n")
        output.write("\n")
        
        # Análisis dimensional
        output.write("ANÁLISIS DIMENSIONAL:\n")
        output.write("-"*50 + "\n")
        output.write(f"Número de Reynolds:            {Re:.2f}\n")
        output.write(f"Régimen de flujo:              {regimen}\n")
        output.write(f"Número de Nusselt:             {Nu:.4f}\n")
        output.write("\n")
        
        # Resultados del análisis
        output.write("RESULTADOS DEL ANÁLISIS:\n")
        output.write("-"*50 + "\n")
        output.write(f"Coeficiente de transferencia:  {h:.4f} W/m²·K\n")
        output.write(f"Área de transferencia:         {A:.6f} m²\n")
        output.write(f"Transferencia de calor total:  {q:.4f} W\n")
        
        # Información adicional
        if Re < 2300:
            output.write(f"\nCorrelación utilizada:         Nu = 3.66 (flujo laminar desarrollado)\n")
        else:
            output.write(f"\nCorrelación utilizada:         Nu = 0.023 × Re^0.8 × Pr^{n} (Dittus-Boelter)\n")
            output.write(f"Exponente n utilizado:         {n} ({'calentamiento' if n == 0.4 else 'enfriamiento'})\n")
        
        output.write("\n")
        output.write("="*80 + "\n")
        output.write("Fin del reporte - Convección Interna Forzada\n")
        output.write("="*80 + "\n")
        
        return output.getvalue()

    # Botón para descargar TXT
    txt_data = crear_txt_resultados()

    st.download_button(
        label="📥 Descargar resultados en TXT",
        data=txt_data,
        file_name=f"reporte_conveccion_{fluido.replace(' ', '_')}_{regimen.lower()}.txt",
        mime="text/plain",
        help="Descarga un archivo TXT con todos los datos de entrada, propiedades termofísicas y resultados del análisis"
    )

    # Mostrar vista previa del TXT
    with st.expander("Vista previa del archivo TXT"):
        st.text(txt_data)

except Exception as e:
    st.error(f"Error en los cálculos: {str(e)}")