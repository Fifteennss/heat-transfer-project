import streamlit as st
import pandas as pd
import numpy as np
from math import pi

# --- Configuración de la página ---
st.set_page_config(
    page_title="Convección en Cilindros",
    page_icon="🔥",
    layout="wide"
)

# --- Conversión de unidades ---
def convertir_temperatura(valor, unidad_origen, unidad_destino):
    if unidad_origen == unidad_destino:
        return valor

    # Convertir origen a °C
    if unidad_origen == "°F":
        valor = (valor - 32) * 5/9
    elif unidad_origen == "K":
        valor = valor - 273.15
    elif unidad_origen == "R":
        valor = (valor - 491.67) * 5/9

    # Convertir °C a destino
    if unidad_destino == "°F":
        return valor * 9/5 + 32
    elif unidad_destino == "K":
        return valor + 273.15
    elif unidad_destino == "R":
        return (valor + 273.15) * 9/5
    return valor

def convertir_velocidad(valor, unidad):
    factores = {
        "m/s": 1,
        "km/h": 1 / 3.6,
        "cm/s": 0.01,
        "ft/s": 0.3048,
        "mph": 0.44704
    }
    return valor * factores[unidad]

def convertir_longitud(valor, unidad):
    factores = {
        "m": 1,
        "mm": 0.001,
        "cm": 0.01,
        "ft": 0.3048,
        "in": 0.0254
    }
    return valor * factores[unidad]

# --- Correlaciones ---
def calcular_h_churchill(Re, Pr, k, D):
    """Correlación de Churchill-Bernstein para flujo cruzado en cilindros"""
    if Pr <= 0.2:
        return None
    
    term1 = 0.62 * (Re**0.5) * (Pr**(1/3))
    term2 = (1 + (0.4/Pr)**(2/3))**(1/4)
    term3 = (1 + (Re/282000)**(5/8))**(4/5)
    
    Nu = 0.3 + term1 / term2 * term3
    return Nu * k / D

def calcular_h_compacto(Re, Pr, k, D, df_coef):
    """Correlación compacta usando coeficientes C y m"""
    try:
        # Buscar el rango de Re adecuado
        for _, row in df_coef.iterrows():
            rango = row['Re_D Range']
            if '–' in rango:
                re_min, re_max = map(float, rango.split('–'))
            elif '-' in rango:
                re_min, re_max = map(float, rango.split('-'))
            else:
                continue
                
            if re_min <= Re <= re_max:
                C = row['C']
                m = row['m']
                Nu = C * (Re ** m) * (Pr ** (1/3))
                return Nu * k / D
        
        st.error("No se encontró coeficiente para el rango de Re calculado")
        return None
    except Exception as e:
        st.error(f"Error en correlación compacta: {str(e)}")
        return None

# --- Carga de datos ---
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
    
    datos = {}
    for fluido, archivo in archivos.items():
        try:
            df = pd.read_csv(archivo)
            if df.empty:
                st.error(f"El archivo {archivo} está vacío")
                datos[fluido] = None
            else:
                datos[fluido] = df
        except FileNotFoundError:
            st.error(f"Error: Archivo no encontrado - {archivo}")
            datos[fluido] = None
        except Exception as e:
            st.error(f"Error al cargar {archivo}: {str(e)}")
            datos[fluido] = None
    
    # Cargar coeficientes para correlación compacta
    try:
        df_coef = pd.read_csv('cylinder_cross_flow_constants.csv')
    except:
        df_coef = None
        st.error("No se pudo cargar los coeficientes para la correlación compacta")
    
    # Filtrar fluidos no cargados
    datos = {k: v for k, v in datos.items() if v is not None}
    return (datos, df_coef) if datos else (None, None)

# --- Obtener propiedades termofísicas ---
def obtener_propiedades(df, T_pelicula, fase=None):
    try:
        if 'Densidad líquido (kg/m³)' in df.columns:  # Fluido bifásico
            if fase == "Líquido":
                props = {
                    'densidad': np.interp(T_pelicula, df['Temp. (°C)'], df['Densidad líquido (kg/m³)']),
                    'viscosidad': np.interp(T_pelicula, df['Temp. (°C)'], df['Viscosidad dinámica líquido (kg/m·s)']),
                    'k': np.interp(T_pelicula, df['Temp. (°C)'], df['Conductividad térmica líquido (W/m·K)']),
                    'Pr': np.interp(T_pelicula, df['Temp. (°C)'], df['Número de Prandtl líquido']),
                    'cp': np.interp(T_pelicula, df['Temp. (°C)'], df['Calor específico líquido (J/kg·K)'])
                }
            else:  # Vapor
                props = {
                    'densidad': np.interp(T_pelicula, df['Temp. (°C)'], df['Densidad vapor (kg/m³)']),
                    'viscosidad': np.interp(T_pelicula, df['Temp. (°C)'], df['Viscosidad dinámica vapor (kg/m·s)']),
                    'k': np.interp(T_pelicula, df['Temp. (°C)'], df['Conductividad térmica vapor (W/m·K)']),
                    'Pr': np.interp(T_pelicula, df['Temp. (°C)'], df['Número de Prandtl vapor']),
                    'cp': np.interp(T_pelicula, df['Temp. (°C)'], df['Calor específico vapor (J/kg·K)'])
                }
        else:  # Fluido monofásico
            props = {
                'densidad': np.interp(T_pelicula, df['Temp. (°C)'], df['Densidad (kg/m³)']),
                'viscosidad': np.interp(T_pelicula, df['Temp. (°C)'], df['Viscosidad dinámica (kg/m·s)']),
                'k': np.interp(T_pelicula, df['Temp. (°C)'], df['Conductividad térmica (W/m·K)']),
                'Pr': np.interp(T_pelicula, df['Temp. (°C)'], df['Número de Prandtl']),
                'cp': np.interp(T_pelicula, df['Temp. (°C)'], df['Calor específico (J/kg·K)'])
            }
        return props
    except Exception as e:
        st.error(f"Error al obtener propiedades: {str(e)}")
        return None

# --- Interfaz principal ---
st.title("Convección externa en Cilindros")

# Cargar datos
datos, df_coef = cargar_datos()

if datos is None:
    st.error("No se pudo cargar ningún archivo de datos. Verifica los archivos CSV.")
    st.stop()

fluidos_disponibles = list(datos.keys())
if not fluidos_disponibles:
    st.error("No hay datos disponibles para ningún fluido")
    st.stop()

with st.sidebar:
    st.header("⚙️ Configuración")
    fluido = st.selectbox("Fluido:", options=fluidos_disponibles)
    
    # Mostrar selector de fase solo para fluidos bifásicos
    if 'Densidad líquido (kg/m³)' in datos[fluido].columns:
        fase = st.radio("Fase:", ["Líquido", "Vapor"], horizontal=True)
    
    correlacion = st.radio("Correlación para h:", 
                         ['Compacta (C y m)', 'Completa (Churchill-Bernstein)'])
    
    st.subheader("Unidades")
    unidad_temp = st.selectbox("Temperatura", ["°C", "°F", "K", "R"])
    unidad_vel = st.selectbox("Velocidad", ["m/s", "km/h", "cm/s", "ft/s", "mph"])
    unidad_dia = st.selectbox("Diámetro", ["m", "mm", "cm", "ft", "in"])
    unidad_long = st.selectbox("Longitud", ["m", "mm", "cm", "ft", "in"])

# Entradas de usuario
col1, col2 = st.columns(2)
with col1:
    T_fluido_input = st.number_input(f"Temperatura del fluido ({unidad_temp})", value=25.0)
    velocidad_input = st.number_input(f"Velocidad del fluido ({unidad_vel})", value=1.0)
    diametro_input = st.number_input(f"Diámetro del cilindro ({unidad_dia})", value=0.05)
with col2:
    T_superficie_input = st.number_input(f"Temperatura superficie ({unidad_temp})", value=100.0)
    longitud_input = st.number_input(f"Longitud del cilindro ({unidad_long})", value=1.0)

# Validación temperatura para escalas absolutas
if unidad_temp in ["K", "R"] and (T_fluido_input < 0 or T_superficie_input < 0):
    st.error("❌ No se permiten temperaturas negativas en escalas absolutas (K, R)")
    st.stop()

# Conversión a unidades base
T_fluido = convertir_temperatura(T_fluido_input, unidad_temp, "°C")
T_superficie = convertir_temperatura(T_superficie_input, unidad_temp, "°C")
velocidad = convertir_velocidad(velocidad_input, unidad_vel)
diametro = convertir_longitud(diametro_input, unidad_dia)
longitud = convertir_longitud(longitud_input, unidad_long)

# 1. Temperatura de película
T_pelicula = (T_fluido + T_superficie) / 2
st.subheader("1. Temperatura de película")
st.latex(rf"T_{{película}} = \frac{{T_{{fluido}} + T_{{superficie}}}}{{2}} = \frac{{{T_fluido:.1f} + {T_superficie:.1f}}}{{2}} = {T_pelicula:.1f}°C")

# 2. Propiedades termofísicas
if 'Densidad líquido (kg/m³)' in datos[fluido].columns:
    props = obtener_propiedades(datos[fluido], T_pelicula, fase)
else:
    props = obtener_propiedades(datos[fluido], T_pelicula)

if props is None:
    st.error("Error al obtener propiedades termofísicas")
    st.stop()

st.subheader("2. Propiedades termofísicas")
cols = st.columns(3)
cols[0].metric("Densidad (ρ)", f"{props['densidad']:.2f} kg/m³")
cols[1].metric("Viscosidad (μ)", f"{props['viscosidad']:.2e} kg/m·s")
cols[2].metric("Conductividad (k)", f"{props['k']:.4f} W/m·K")

cols = st.columns(3)
cols[0].metric("Prandtl (Pr)", f"{props['Pr']:.2f}")
cols[1].metric("Calor específico (cp)", f"{props['cp']/1000:.2f} kJ/kg·K")

# 3. Número de Reynolds
Re = (velocidad * diametro * props['densidad']) / props['viscosidad']
st.subheader("3. Número de Reynolds")
st.latex(rf"Re = \frac{{V \cdot D \cdot \rho}}{{\mu}} = \frac{{{velocidad:.4f} \cdot {diametro:.4f} \cdot {props['densidad']:.4f}}}{{{props['viscosidad']:.6f}}} = {Re:.2f}")

# 4. Coeficiente de convección
st.subheader("4. Coeficiente de convección (h)")

if correlacion == 'Completa (Churchill-Bernstein)':
    h = calcular_h_churchill(Re, props['Pr'], props['k'], diametro)
    if h is None:
        st.error("❌ La correlación Churchill-Bernstein requiere Pr > 0.2")
        st.stop()
    
    st.latex(r"""
    \text{Correlación Churchill-Bernstein (válida para Pr > 0.2):}
    """)
    st.latex(rf"Nu = 0.3 + \frac{{0.62 \cdot {Re:.2f}^{{1/2}} \cdot {props['Pr']:.4f}^{{1/3}}}}{{\left[1 + \left(\frac{{0.4}}{{{props['Pr']:.4f}}}\right)^{{2/3}}\right]^{{1/4}}}} \cdot \left[1 + \left(\frac{{{Re:.2f}}}{{282000}}\right)^{{5/8}}\right]^{{4/5}} = {h/props['k']*diametro:.2f}")
    
    st.latex(rf"h = \frac{{Nu \cdot k}}{{D}} = \frac{{{h/props['k']*diametro:.2f} \cdot {props['k']:.6f}}}{{{diametro:.4f}}} = {h:.2f} \, \text{{W/m}}²\text{{K}}")
else:
    if df_coef is None:
        st.error("No se encontraron coeficientes para la correlación compacta")
        st.stop()
    
    h = calcular_h_compacto(Re, props['Pr'], props['k'], diametro, df_coef)
    if h is None:
        st.stop()
    
    st.latex(r"""
    \text{Correlación compacta:}
    """)
    st.latex(rf"Nu = C \cdot Re^m \cdot Pr^{{1/3}}")
    st.latex(rf"h = \frac{{Nu \cdot k}}{{D}} = {h:.2f} \, \text{{W/m}}²\text{{K}}")

# 5. Transferencia de calor
A = pi * diametro * longitud
q = h * A * (T_superficie - T_fluido)
st.subheader("5. Transferencia de calor")
cols = st.columns(3)
cols[0].latex(rf"A = \pi \cdot D \cdot L = \pi \cdot {diametro:.4f} \cdot {longitud:.4f} = {A:.4f} \, \text{{m}}²")
cols[1].latex(rf"\Delta T = {T_superficie:.1f} - {T_fluido:.1f} = {T_superficie - T_fluido:.1f}°C")
cols[2].latex(rf"q = h \cdot A \cdot \Delta T = {h:.2f} \cdot {A:.4f} \cdot {T_superficie - T_fluido:.1f}")
st.success(f"## 🔥 Transferencia de calor: {q:.2f} W")