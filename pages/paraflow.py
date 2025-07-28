import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="centered")

st.title("Convección en Flujo Externo - Placa Plana")

# --- Sidebar de configuración de unidades ---
st.sidebar.title("Configuración de Unidades")
unidad_temp = st.sidebar.selectbox("Unidad de temperatura", ["°C", "°F", "K", "R"])
unidad_longitud = st.sidebar.selectbox("Unidad de longitud", ["m", "cm", "mm", "in", "ft"])
unidad_velocidad = st.sidebar.selectbox("Unidad de velocidad del fluido", ["m/s", "cm/s", "km/h", "ft/s"])

# --- Funciones de conversión ---
def convertir_temp(temp, unidad):
    if unidad == "°F": return (temp - 32) * 5/9
    elif unidad == "K": return temp - 273.15
    elif unidad == "R": return (temp - 491.67) * 5/9
    return temp

def convertir_longitud(valor, unidad):
    factores = {"m": 1.0, "cm": 0.01, "mm": 0.001, "in": 0.0254, "ft": 0.3048}
    return valor * factores[unidad]

def convertir_velocidad(valor, unidad):
    factores = {"m/s": 1.0, "cm/s": 0.01, "km/h": 1/3.6, "ft/s": 0.3048}
    return valor * factores[unidad]

# --- Selección de fluido y estado ---
fluido = st.selectbox("Selecciona el fluido:", [
    "agua saturada (tabla_a9.csv)",
    "refrigerante 134a (tabla_a10.csv)",
    "amoniaco (tabla_a11.csv)",
    "propano (tabla_a12.csv)",
    "aire (tabla_a15.csv)",
    "glicerina (tabla_glicerina.csv)",
    "isobutano (tabla_isobutano.csv)",
    "metano (tabla_metano.csv)",
    "metanol (tabla_metanol.csv)",
    "aceite para motor (tabla_aceitemotor.csv)"
])

archivo = {
    "agua saturada (tabla_a9.csv)": "tabla_a9.csv",
    "refrigerante 134a (tabla_a10.csv)": "tabla_a10.csv",
    "amoniaco (tabla_a11.csv)": "tabla_a11.csv",
    "propano (tabla_a12.csv)": "tabla_a12.csv",
    "aire (tabla_a15.csv)": "tabla_a15.csv",
    "glicerina (tabla_glicerina.csv)": "tabla_glicerina.csv",
    "isobutano (tabla_isobutano.csv)": "tabla_isobutano.csv",
    "metano (tabla_metano.csv)": "tabla_metano.csv",
    "metanol (tabla_metanol.csv)": "tabla_metanol.csv",
    "aceite para motor (tabla_aceitemotor.csv)": "tabla_aceitemotor.csv"
}[fluido]

tabla = pd.read_csv(archivo)

# --- Selección de estado si aplica ---
si_tiene_fases = archivo in ["tabla_a9.csv", "tabla_a10.csv", "tabla_a11.csv", "tabla_a12.csv"]
estado = None
if si_tiene_fases:
    estado = st.selectbox("Selecciona el estado:", ["líquido", "vapor"])

# --- Entradas del usuario ---
T_inf = convertir_temp(st.number_input(f"Temperatura del fluido ({unidad_temp})", value=20.0), unidad_temp)
T_s = convertir_temp(st.number_input(f"Temperatura de la superficie ({unidad_temp})", value=40.0), unidad_temp)
V = convertir_velocidad(st.number_input(f"Velocidad del fluido ({unidad_velocidad})", value=6.0), unidad_velocidad)
L = convertir_longitud(st.number_input(f"Longitud de la placa ({unidad_longitud})", min_value=0.001, value=0.5), unidad_longitud)
b = convertir_longitud(st.number_input(f"Ancho de la placa ({unidad_longitud})", min_value=0.001, value=0.3), unidad_longitud)

# --- Esquema 2D de la placa ---
def dibujar_diagrama_placa_2d(L=0.5, T_s=120, T_inf=30, V=6):
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.add_patch(plt.Rectangle((0, 0), L, 0.01, color="gray"))
    for y in [0.02, 0.05, 0.08]:
        ax.arrow(-0.2, y, 0.18, 0, head_width=0.01, head_length=0.02, fc='black', ec='black')
    ax.text(-0.25, 0.17, f"{fluido.split()[0].capitalize()}", fontsize=12)
    ax.text(-0.25, 0.14, f"$V = {V} \\ \\mathrm{{m/s}}$", fontsize=12)
    ax.text(-0.25, 0.11, f"$T_\\infty = {T_inf}^\\circ\\mathrm{{C}}$", fontsize=12)
    ax.annotate(f"$T_s = {T_s}^\\circ\\mathrm{{C}}$",
                xy=(L/2, 0.01), xytext=(L/2, 0.25),
                arrowprops=dict(arrowstyle="->"), ha='center', fontsize=12)
    ax.annotate("", xy=(0, -0.02), xytext=(L, -0.02), arrowprops=dict(arrowstyle="<->"))
    ax.text(L/2, -0.06, f"$L = {L:.2f}$ m", ha="center", fontsize=14)
    ax.set_xlim(-0.3, L + 0.2)
    ax.set_ylim(-0.1, 0.3)
    ax.axis("off")
    ax.set_title("Esquema 2D de Placa Plana en Flujo Externo", fontsize=13)
    st.pyplot(fig)

dibujar_diagrama_placa_2d(L=L, T_s=T_s, T_inf=T_inf, V=V)

T_film = (T_inf + T_s) / 2
st.markdown(f"**Temperatura de película:** {T_film:.2f} °C")

# --- Interpolación de propiedades ---
def interpolar(x, y, valor):
    return np.interp(valor, x, y)

T_col = "Temp. (°C)"
if si_tiene_fases:
    if estado == "líquido":
        props = {
            "mu": interpolar(tabla[T_col], tabla["Viscosidad dinámica líquido (kg/m·s)"], T_film),
            "k": interpolar(tabla[T_col], tabla["Conductividad térmica líquido (W/m·K)"], T_film),
            "rho": interpolar(tabla[T_col], tabla["Densidad líquido (kg/m³)"], T_film),
            "cp": interpolar(tabla[T_col], tabla["Calor específico líquido (J/kg·K)"], T_film),
            "pr": interpolar(tabla[T_col], tabla["Número de Prandtl líquido"], T_film)
        }
    else:
        props = {
            "mu": interpolar(tabla[T_col], tabla["Viscosidad dinámica vapor (kg/m·s)"], T_film),
            "k": interpolar(tabla[T_col], tabla["Conductividad térmica vapor (W/m·K)"], T_film),
            "rho": interpolar(tabla[T_col], tabla["Densidad vapor (kg/m³)"], T_film),
            "cp": interpolar(tabla[T_col], tabla["Calor específico vapor (J/kg·K)"], T_film),
            "pr": interpolar(tabla[T_col], tabla["Número de Prandtl vapor"], T_film)
        }
else:
    props = {
        "mu": interpolar(tabla[T_col], tabla["Viscosidad dinámica (kg/m·s)"], T_film),
        "k": interpolar(tabla[T_col], tabla["Conductividad térmica (W/m·K)"], T_film),
        "rho": interpolar(tabla[T_col], tabla["Densidad (kg/m³)"], T_film),
        "cp": interpolar(tabla[T_col], tabla["Calor específico (J/kg·K)"], T_film),
        "pr": interpolar(tabla[T_col], tabla["Número de Prandtl"], T_film)
    }

# --- Ajuste de viscosidad cinemática si el fluido es aire y presión ≠ 1 atm ---
if fluido == "aire (tabla_a15.csv)":
    diferente_presion = st.checkbox("¿La presión es diferente a 1 atm?")
    if diferente_presion:
        presion_kpa = st.number_input("Ingresa la presión del aire (kPa):", min_value=1.0, value=101.325)
        nu_1atm = interpolar(tabla[T_col], tabla["Viscosidad cinemática (m²/s)"], T_film)
        nu = nu_1atm * 101.325 / presion_kpa
        Re_L = V * L / nu
    else:
        Re_L = props['rho'] * V * L / props['mu']
else:
    Re_L = props['rho'] * V * L / props['mu']

# --- Mostrar propiedades ---
st.markdown("**Propiedades interpoladas a temperatura de película:**")
st.write(props)

Pr = props['pr']
st.markdown(f"**Reynolds en L:** {Re_L:,.0f}")

# --- Clasificación de régimen ---
if Re_L < 5e5:
    st.success("Régimen laminar")
elif 5e5 <= Re_L <= 1e7:
    st.warning("Régimen mixto o turbulento")
else:
    st.error("Reynolds fuera del rango de validez de las correlaciones (Re > 10⁷)")

# --- Validación de Pr ---
if Pr < 0.6:
    st.error("Número de Prandtl fuera del rango válido (Pr < 0.6).")
elif Pr > 60:
    st.error("Número de Prandtl fuera del rango válido (Pr > 60).")

# --- Selección de tipo de análisis ---
modo = st.radio("¿Qué deseas calcular?", ["Flujo de calor promedio", "Flujo de calor local"])

if modo == "Flujo de calor promedio":
    if Re_L < 5e5 and Pr > 0.6:
        Nu = 0.664 * Re_L**0.5 * Pr**(1/3)
        h = Nu * props['k'] / L
        q = h * (T_s - T_inf) * L * b
        st.markdown(f"**Laminar**\n- Nusselt: {Nu:.2f}\n- h: {h:.2f} W/m²·K\n- Flujo de calor: {q:.2f} W")

    elif 5e5 <= Re_L <= 1e7 and 0.6 <= Pr <= 60:
        x_c = 5e5 * props['mu'] / (props['rho'] * V)
        if x_c < L:
            Re_c = 5e5
            Nu_lam = 0.664 * Re_c**0.5 * Pr**(1/3)
            h_lam = Nu_lam * props['k'] / x_c
            q_lam = h_lam * (T_s - T_inf) * x_c * b

            Nu_mix = (0.037 * Re_L**(4/5) - 871) * Pr**(1/3)
            h_mix = Nu_mix * props['k'] / L
            q_mix = h_mix * (T_s - T_inf) * L * b

            q_turb = q_mix - q_lam

            st.markdown(f"**Régimen mixto**\n- Longitud crítica: {x_c:.4f} m\n- Flujo laminar: {q_lam:.2f} W\n- Flujo mixto total: {q_mix:.2f} W\n- Flujo turbulento estimado: {q_turb:.2f} W")
        else:
            Nu = 0.037 * Re_L**(4/5) * Pr**(1/3)
            h = Nu * props['k'] / L
            q = h * (T_s - T_inf) * L * b
            st.markdown(f"**Turbulento completo**\n- Nusselt: {Nu:.2f}\n- h: {h:.2f} W/m²·K\n- Flujo de calor: {q:.2f} W")

elif modo == "Flujo de calor local":
    x = st.number_input("Posición sobre la placa (x en m)", min_value=0.0001, max_value=L, value=0.05)
    Re_x = props['rho'] * V * x / props['mu']

    if Re_x < 5e5 and Pr > 0.6:
        Nu_x = 0.332 * Re_x**0.5 * Pr**(1/3)
        h_x = Nu_x * props['k'] / x
        q_local = h_x * (T_s - T_inf)
        st.markdown(f"**Punto laminar**\n- Re_x: {Re_x:.0f}\n- Nusselt local: {Nu_x:.2f}\n- h_x: {h_x:.2f} W/m²·K\n- Flujo local: {q_local:.2f} W/m²")

    elif Re_x >= 5e5 and Re_x <= 1e7 and 0.6 <= Pr <= 60:
        Nu_x = 0.0296 * Re_x**(4/5) * Pr**(1/3)
        h_x = Nu_x * props['k'] / x
        q_local = h_x * (T_s - T_inf)
        st.markdown(f"**Punto turbulento**\n- Re_x: {Re_x:.0f}\n- Nusselt local: {Nu_x:.2f}\n- h_x: {h_x:.2f} W/m²·K\n- Flujo local: {q_local:.2f} W/m²")

    else:
        st.error("Re_x fuera del rango válido para correlaciones.")
        
# --- Visualización: h_x vs x ---
x_vals = np.linspace(0.01, L, 100)
Re_x_vals = props['rho'] * V * x_vals / props['mu']
Pr = props['pr']
h_vals = np.where(
    Re_x_vals < 5e5,
    0.332 * Re_x_vals**0.5 * Pr**(1/3) * props['k'] / x_vals,
    0.0296 * Re_x_vals**(4/5) * Pr**(1/3) * props['k'] / x_vals
)

fig, ax = plt.subplots()
ax.plot(x_vals, h_vals)
ax.set_xlabel("x (m)")
ax.set_ylabel("hₓ (W/m²·K)")
ax.set_title("Coeficiente de convección local hₓ vs posición x")
ax.grid(True)
st.pyplot(fig)

