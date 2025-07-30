import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(layout="wide")

# --- Sidebar de configuración de unidades ---
st.sidebar.title("Configuración de Unidades")
st.sidebar.markdown("---")

st.sidebar.subheader("Sistema de Unidades")
unidad_temp = st.sidebar.selectbox("Temperatura", ["°C", "°F", "K", "R"],
                                  help="Sistema de unidades para temperaturas")
unidad_longitud = st.sidebar.selectbox("Longitud", ["m", "cm", "mm", "in", "ft"],
                                      help="Sistema de unidades para dimensiones")
unidad_velocidad = st.sidebar.selectbox("Velocidad", ["m/s", "cm/s", "km/h", "ft/s"],
                                       help="Sistema de unidades para velocidades")

# Resumen del sistema actual
st.sidebar.markdown("---")
st.sidebar.markdown("**Sistema actual:**")
st.sidebar.markdown(f"""
- **Temperatura:** {unidad_temp}
- **Longitud:** {unidad_longitud}
- **Velocidad:** {unidad_velocidad}
""")

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

# --- Título principal ---
st.title("Convección en Flujo Externo - Placa Plana")
st.info(f"**Sistema de unidades activo:** Temperatura = {unidad_temp} | Longitud = {unidad_longitud} | Velocidad = {unidad_velocidad}")

# --- Selección de fluido ---
st.subheader("Configuración del Fluido")

col1, col2 = st.columns([2, 1])
with col1:
    fluido = st.selectbox("Selecciona el tipo de fluido:", [
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
    ], help="Base de datos de propiedades termofísicas del fluido")

# Mapeo de archivos
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

# Cargar tabla de propiedades
tabla = pd.read_csv(archivo)

# Selección de estado para fluidos con fases
si_tiene_fases = archivo in ["tabla_a9.csv", "tabla_a10.csv", "tabla_a11.csv", "tabla_a12.csv"]
estado = None

with col2:
    if si_tiene_fases:
        estado = st.selectbox("Estado del fluido:", ["líquido", "vapor"],
                             help="Fase del fluido para obtener las propiedades correctas")
        st.success(f"Fluido: {estado}")
    else:
        st.info("Fluido de fase única")

# --- Condiciones de operación ---
st.subheader("Condiciones de Operación")

col1, col2 = st.columns(2)
with col1:
    T_inf_input = st.number_input(f"Temperatura del fluido ({unidad_temp})", 
                                  value=20.0, step=1.0,
                                  help=f"Temperatura del fluido libre en {unidad_temp}")
    T_inf = convertir_temp(T_inf_input, unidad_temp)
    
    T_s_input = st.number_input(f"Temperatura de la superficie ({unidad_temp})", 
                                value=40.0, step=1.0,
                                help=f"Temperatura de la placa en {unidad_temp}")
    T_s = convertir_temp(T_s_input, unidad_temp)

with col2:
    V_input = st.number_input(f"Velocidad del fluido ({unidad_velocidad})", 
                              value=6.0, step=0.1, min_value=0.1,
                              help=f"Velocidad de aproximación del fluido en {unidad_velocidad}")
    V = convertir_velocidad(V_input, unidad_velocidad)

# --- Geometría de la placa ---
st.subheader("Dimensiones de la Placa")

col1, col2 = st.columns(2)
with col1:
    L_input = st.number_input(f"Longitud de la placa ({unidad_longitud})", 
                              min_value=0.001, value=0.5, step=0.01,
                              help=f"Dimensión en la dirección del flujo en {unidad_longitud}")
    L = convertir_longitud(L_input, unidad_longitud)

with col2:
    b_input = st.number_input(f"Ancho de la placa ({unidad_longitud})", 
                              min_value=0.001, value=0.3, step=0.01,
                              help=f"Dimensión perpendicular al flujo en {unidad_longitud}")
    b = convertir_longitud(b_input, unidad_longitud)

# Configuración especial para aire a presión diferente
diferente_presion = False
presion_kpa = 101.325
if fluido == "aire (tabla_a15.csv)":
    st.subheader("Configuración Especial para Aire")
    diferente_presion = st.checkbox("La presión es diferente a 1 atm", 
                                   help="Activar para corregir las propiedades por presión")
    if diferente_presion:
        presion_kpa = st.number_input("Presión del aire (kPa):", 
                                     min_value=1.0, value=101.325, step=1.0,
                                     help="Presión absoluta del aire para corrección de viscosidad")

# --- Esquema de la configuración ---
st.subheader("Esquema del Problema")

def dibujar_diagrama_placa_2d(L=0.5, T_s=120, T_inf=30, V=6):
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Dibujar la placa
    ax.add_patch(plt.Rectangle((0, 0), L, 0.02, color="lightgray", edgecolor="black", linewidth=2))
    
    # Flechas de flujo
    for y in [0.04, 0.08, 0.12, 0.16]:
        ax.arrow(-0.15, y, 0.12, 0, head_width=0.015, head_length=0.02, fc='blue', ec='blue', linewidth=2)
    
    # Etiquetas del fluido
    ax.text(-0.18, 0.22, f"{fluido.split()[0].capitalize()}", fontsize=14, weight='bold')
    ax.text(-0.18, 0.18, f"V = {V:.1f} m/s", fontsize=12)
    ax.text(-0.18, 0.14, f"T∞ = {T_inf:.1f}°C", fontsize=12)
    
    # Temperatura de superficie
    ax.annotate(f"Ts = {T_s:.1f}°C",
                xy=(L/2, 0.02), xytext=(L/2, 0.35),
                arrowprops=dict(arrowstyle="->", color="red", linewidth=2), 
                ha='center', fontsize=12, color='red', weight='bold')
    
    # Dimensión de longitud
    ax.annotate("", xy=(0, -0.03), xytext=(L, -0.03), 
                arrowprops=dict(arrowstyle="<->", color="black", linewidth=2))
    ax.text(L/2, -0.08, f"L = {L:.3f} m", ha="center", fontsize=12, weight='bold')
    
    # Configuración del gráfico
    ax.set_xlim(-0.25, L + 0.15)
    ax.set_ylim(-0.12, 0.4)
    ax.axis("off")
    ax.set_title("Configuración: Placa Plana en Flujo Externo", fontsize=16, weight='bold', pad=20)
    
    st.pyplot(fig)

dibujar_diagrama_placa_2d(L=L, T_s=T_s, T_inf=T_inf, V=V)

# --- Cálculo de temperatura de película ---
T_film = (T_inf + T_s) / 2
st.success(f"**Temperatura de película:** {T_film:.2f} °C")

# --- Interpolación de propiedades ---
def interpolar(x, y, valor):
    return np.interp(valor, x, y)

T_col = "Temp. (°C)"

# Obtener propiedades según el tipo de fluido
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

# --- Cálculo del número de Reynolds ---
if fluido == "aire (tabla_a15.csv)" and diferente_presion:
    nu_1atm = interpolar(tabla[T_col], tabla["Viscosidad cinemática (m²/s)"], T_film)
    nu = nu_1atm * 101.325 / presion_kpa
    Re_L = V * L / nu
    st.info(f"**Corrección por presión aplicada:** ν = {nu:.2e} m²/s (a {presion_kpa:.1f} kPa)")
else:
    Re_L = props['rho'] * V * L / props['mu']

# --- Mostrar propiedades del fluido ---
st.subheader("Propiedades del Fluido")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Propiedades interpoladas a temperatura de película:**")
    propiedades_df = pd.DataFrame({
        "Propiedad": ["Viscosidad dinámica", "Conductividad térmica", "Densidad", "Calor específico", "Número de Prandtl"],
        "Valor": [f"{props['mu']:.2e}", f"{props['k']:.4f}", f"{props['rho']:.2f}", f"{props['cp']:.1f}", f"{props['pr']:.3f}"],
        "Unidad": ["kg/m·s", "W/m·K", "kg/m³", "J/kg·K", "-"]
    })
    st.dataframe(propiedades_df, use_container_width=True)

with col2:
    Pr = props['pr']
    st.metric("Número de Reynolds", f"{Re_L:,.0f}")
    st.metric("Número de Prandtl", f"{Pr:.3f}")
    
    # Clasificación de régimen
    if Re_L < 5e5:
        regimen = "Laminar"
        st.success("**Régimen:** Laminar")
    elif 5e5 <= Re_L <= 1e7:
        regimen = "Mixto o Turbulento"
        st.warning("**Régimen:** Mixto o Turbulento")
    else:
        regimen = "Fuera de rango (Re > 10⁷)"
        st.error("**Régimen:** Fuera de rango (Re > 10⁷)")

# --- Validación de rangos ---
st.subheader("Validación de Correlaciones")

validacion_msgs = []
if Pr < 0.6:
    validacion_msgs.append("⚠️ Número de Prandtl fuera del rango válido (Pr < 0.6)")
elif Pr > 60:
    validacion_msgs.append("⚠️ Número de Prandtl fuera del rango válido (Pr > 60)")
else:
    validacion_msgs.append("✅ Número de Prandtl dentro del rango válido (0.6 ≤ Pr ≤ 60)")

if Re_L > 1e7:
    validacion_msgs.append("⚠️ Reynolds fuera del rango de validez (Re > 10⁷)")
else:
    validacion_msgs.append("✅ Reynolds dentro del rango de validez")

for msg in validacion_msgs:
    if "⚠️" in msg:
        st.warning(msg)
    else:
        st.success(msg)

# --- Análisis y cálculos ---
st.subheader("Análisis de Transferencia de Calor")

modo = st.radio("Selecciona el tipo de análisis:", 
                ["Flujo de calor promedio", "Flujo de calor local"],
                help="Elige entre análisis promedio (toda la placa) o local (punto específico)")

# Variables para almacenar resultados
resultados = {}

if modo == "Flujo de calor promedio":
    st.markdown("### Análisis Promedio")
    
    if Re_L < 5e5 and Pr > 0.6:
        # Régimen laminar
        Nu = 0.664 * Re_L**0.5 * Pr**(1/3)
        h = Nu * props['k'] / L
        q = h * (T_s - T_inf) * L * b
        
        resultados = {
            "tipo_analisis": "Flujo de calor promedio",
            "regimen": "Laminar",
            "numero_nusselt": Nu,
            "coeficiente_conveccion": h,
            "flujo_calor_total": q,
            "area_transferencia": L * b
        }
        
        col1, col2 = st.columns(2)
        with col1:
            st.success("**Régimen: Laminar**")
            st.metric("Número de Nusselt", f"{Nu:.2f}")
            st.metric("Coeficiente de convección", f"{h:.2f} W/m²·K")
        with col2:
            st.metric("Flujo de calor total", f"{q:.2f} W")
            st.metric("Área de transferencia", f"{L*b:.4f} m²")

    elif 5e5 <= Re_L <= 1e7 and 0.6 <= Pr <= 60:
        # Régimen mixto
        x_c = 5e5 * props['mu'] / (props['rho'] * V)
        
        if x_c < L:
            # Cálculos para régimen mixto
            Re_c = 5e5
            Nu_lam = 0.664 * Re_c**0.5 * Pr**(1/3)
            h_lam = Nu_lam * props['k'] / x_c
            q_lam = h_lam * (T_s - T_inf) * x_c * b

            Nu_mix = (0.037 * Re_L**(4/5) - 871) * Pr**(1/3)
            h_mix = Nu_mix * props['k'] / L
            q_mix = h_mix * (T_s - T_inf) * L * b

            q_turb = q_mix - q_lam

            resultados = {
                "tipo_analisis": "Flujo de calor promedio",
                "regimen": "Mixto",
                "longitud_critica": x_c,
                "numero_nusselt_mixto": Nu_mix,
                "coeficiente_conveccion_mixto": h_mix,
                "flujo_laminar": q_lam,
                "flujo_mixto_total": q_mix,
                "flujo_turbulento": q_turb,
                "area_transferencia": L * b
            }

            col1, col2 = st.columns(2)
            with col1:
                st.warning("**Régimen: Mixto**")
                st.metric("Longitud crítica", f"{x_c:.4f} m")
                st.metric("Nusselt mixto", f"{Nu_mix:.2f}")
                st.metric("Coef. convección mixto", f"{h_mix:.2f} W/m²·K")
            with col2:
                st.metric("Flujo laminar", f"{q_lam:.2f} W")
                st.metric("Flujo mixto total", f"{q_mix:.2f} W")
                st.metric("Flujo turbulento", f"{q_turb:.2f} W")
        else:
            # Turbulento completo
            Nu = 0.037 * Re_L**(4/5) * Pr**(1/3)
            h = Nu * props['k'] / L
            q = h * (T_s - T_inf) * L * b
            
            resultados = {
                "tipo_analisis": "Flujo de calor promedio",
                "regimen": "Turbulento completo",
                "numero_nusselt": Nu,
                "coeficiente_conveccion": h,
                "flujo_calor_total": q,
                "area_transferencia": L * b
            }
            
            col1, col2 = st.columns(2)
            with col1:
                st.info("**Régimen: Turbulento completo**")
                st.metric("Número de Nusselt", f"{Nu:.2f}")
                st.metric("Coeficiente de convección", f"{h:.2f} W/m²·K")
            with col2:
                st.metric("Flujo de calor total", f"{q:.2f} W")
                st.metric("Área de transferencia", f"{L*b:.4f} m²")

elif modo == "Flujo de calor local":
    st.markdown("### Análisis Local")
    
    # Calcular un valor por defecto apropiado para x en la unidad seleccionada
    valor_defecto_x_unidad = min(0.05, L_input * 0.1, L_input * 0.9)
    valor_defecto_x_unidad = max(0.0001, min(valor_defecto_x_unidad, L_input))

    x_input = st.number_input(
        f"Posición sobre la placa (x en {unidad_longitud})",
        min_value=0.0001, max_value=L_input, value=valor_defecto_x_unidad, step=0.001,
        help=f"Distancia desde el borde de ataque de la placa en {unidad_longitud}"
    )
    x = convertir_longitud(x_input, unidad_longitud)  # Convertir a metros para cálculos
    
    # Cálculo del Reynolds local considerando corrección por presión si aplica
    if fluido == "aire (tabla_a15.csv)" and diferente_presion:
        nu_1atm = interpolar(tabla[T_col], tabla["Viscosidad cinemática (m²/s)"], T_film)
        nu = nu_1atm * 101.325 / presion_kpa
        Re_x = V * x / nu
    else:
        Re_x = props['rho'] * V * x / props['mu']

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Reynolds local", f"{Re_x:.0f}")
        st.metric("Posición x", f"{x:.4f} m")
    
    if Re_x < 5e5 and Pr > 0.6:
        Nu_x = 0.332 * Re_x**0.5 * Pr**(1/3)
        h_x = Nu_x * props['k'] / x
        q_local = h_x * (T_s - T_inf)
        
        resultados = {
            "tipo_analisis": "Flujo de calor local",
            "posicion_x": x,
            "reynolds_local": Re_x,
            "regimen_local": "Laminar",
            "numero_nusselt_local": Nu_x,
            "coeficiente_conveccion_local": h_x,
            "flujo_calor_local": q_local
        }
        
        with col2:
            st.success("**Régimen local: Laminar**")
            st.metric("Nusselt local", f"{Nu_x:.2f}")
            st.metric("h local", f"{h_x:.2f} W/m²·K")
            st.metric("Flujo local", f"{q_local:.2f} W/m²")

    elif Re_x >= 5e5 and Re_x <= 1e7 and 0.6 <= Pr <= 60:
        Nu_x = 0.0296 * Re_x**(4/5) * Pr**(1/3)
        h_x = Nu_x * props['k'] / x
        q_local = h_x * (T_s - T_inf)
        
        resultados = {
            "tipo_analisis": "Flujo de calor local",
            "posicion_x": x,
            "reynolds_local": Re_x,
            "regimen_local": "Turbulento",
            "numero_nusselt_local": Nu_x,
            "coeficiente_conveccion_local": h_x,
            "flujo_calor_local": q_local
        }
        
        with col2:
            st.warning("**Régimen local: Turbulento**")
            st.metric("Nusselt local", f"{Nu_x:.2f}")
            st.metric("h local", f"{h_x:.2f} W/m²·K")
            st.metric("Flujo local", f"{q_local:.2f} W/m²")
    else:
        st.error("Reynolds local fuera del rango válido para correlaciones")

# --- Visualización: h_x vs x ---
st.subheader("Variación del Coeficiente de Convección")

x_vals = np.linspace(0.001, L, 100)
Re_x_vals = props['rho'] * V * x_vals / props['mu']
Pr = props['pr']

h_vals = np.where(
    Re_x_vals < 5e5,
    0.332 * Re_x_vals**0.5 * Pr**(1/3) * props['k'] / x_vals,  # Laminar
    0.0296 * Re_x_vals**(4/5) * Pr**(1/3) * props['k'] / x_vals  # Turbulento
)

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x_vals, h_vals, linewidth=2, color='blue')
ax.set_xlabel("Posición x (m)", fontsize=12)
ax.set_ylabel("Coeficiente de convección local hₓ (W/m²·K)", fontsize=12)
ax.set_title("Variación del Coeficiente de Convección a lo largo de la Placa", fontsize=14, weight='bold')
ax.grid(True, alpha=0.3)

# Marcar la transición laminar-turbulento si existe
x_c_teorico = 5e5 * props['mu'] / (props['rho'] * V)
if x_c_teorico < L:
    ax.axvline(x=x_c_teorico, color='red', linestyle='--', linewidth=2, 
               label=f'Transición (x = {x_c_teorico:.3f} m)')
    ax.legend()

plt.tight_layout()
st.pyplot(fig)

# --- EXPORTACIÓN A CSV ---
st.subheader("Exportar Resultados")

def crear_txt_resultados():
    """Función para crear el archivo TXT con todos los datos y resultados"""
    
    output = StringIO()
    
    # Encabezado
    output.write("="*80 + "\n")
    output.write("ANÁLISIS DE CONVECCIÓN EN FLUJO EXTERNO - PLACA PLANA\n")
    output.write("="*80 + "\n\n")
    
    # Datos de entrada
    output.write("DATOS DE ENTRADA:\n")
    output.write("-"*50 + "\n")
    output.write(f"Fluido seleccionado:           {fluido.split('(')[0].strip()}\n")
    if estado:
        output.write(f"Estado del fluido:             {estado}\n")
    else:
        output.write(f"Estado del fluido:             Fase única\n")
    output.write(f"Temperatura del fluido:        {T_inf_input:.2f} {unidad_temp}\n")
    output.write(f"Temperatura de superficie:     {T_s_input:.2f} {unidad_temp}\n")
    output.write(f"Velocidad del fluido:          {V_input:.2f} {unidad_velocidad}\n")
    output.write(f"Longitud de la placa:          {L_input:.4f} {unidad_longitud}\n")
    output.write(f"Ancho de la placa:             {b_input:.4f} {unidad_longitud}\n")
    
    if fluido == "aire (tabla_a15.csv)" and diferente_presion:
        output.write(f"Presión del aire:              {presion_kpa:.1f} kPa\n")
    
    output.write(f"\nSistema de unidades usado:     Temp={unidad_temp}, Long={unidad_longitud}, Vel={unidad_velocidad}\n")
    output.write("\n")
    
    # Propiedades del fluido
    output.write("PROPIEDADES DEL FLUIDO:\n")
    output.write("-"*50 + "\n")
    output.write(f"Temperatura de película:       {T_film:.2f} °C\n")
    output.write(f"Viscosidad dinámica:           {props['mu']:.6e} kg/m·s\n")
    output.write(f"Conductividad térmica:         {props['k']:.6f} W/m·K\n")
    output.write(f"Densidad:                      {props['rho']:.2f} kg/m³\n")
    output.write(f"Calor específico:              {props['cp']:.1f} J/kg·K\n")
    output.write(f"Número de Prandtl:             {props['pr']:.6f}\n")
    output.write(f"Número de Reynolds:            {Re_L:.0f}\n")
    output.write(f"Régimen de flujo:              {regimen}\n")
    output.write("\n")
    
    # Validación
    output.write("VALIDACIÓN DE CORRELACIONES:\n")
    output.write("-"*50 + "\n")
    if 0.6 <= Pr <= 60:
        output.write("✓ Número de Prandtl dentro del rango válido (0.6 ≤ Pr ≤ 60)\n")
    else:
        output.write("⚠ Número de Prandtl fuera del rango válido\n")
    
    if Re_L <= 1e7:
        output.write("✓ Reynolds dentro del rango de validez (Re ≤ 10⁷)\n")
    else:
        output.write("⚠ Reynolds fuera del rango de validez\n")
    output.write("\n")
    
    # Resultados del análisis
    output.write("RESULTADOS DEL ANÁLISIS:\n")
    output.write("-"*50 + "\n")
    
    if resultados:
        if resultados.get("tipo_analisis") == "Flujo de calor promedio":
            output.write("Tipo de análisis: FLUJO DE CALOR PROMEDIO\n\n")
            
            if resultados.get("regimen") == "Laminar":
                output.write("Régimen: LAMINAR\n")
                output.write(f"Número de Nusselt:             {resultados['numero_nusselt']:.6f}\n")
                output.write(f"Coeficiente de convección:     {resultados['coeficiente_conveccion']:.6f} W/m²·K\n")
                output.write(f"Flujo de calor total:          {resultados['flujo_calor_total']:.6f} W\n")
                output.write(f"Área de transferencia:         {resultados['area_transferencia']:.6f} m²\n")
                
            elif resultados.get("regimen") == "Mixto":
                output.write("Régimen: MIXTO (Laminar + Turbulento)\n")
                output.write(f"Longitud crítica:              {resultados['longitud_critica']:.6f} m\n")
                output.write(f"Número de Nusselt mixto:       {resultados['numero_nusselt_mixto']:.6f}\n")
                output.write(f"Coef. convección mixto:        {resultados['coeficiente_conveccion_mixto']:.6f} W/m²·K\n")
                output.write(f"Flujo laminar:                 {resultados['flujo_laminar']:.6f} W\n")
                output.write(f"Flujo turbulento:              {resultados['flujo_turbulento']:.6f} W\n")
                output.write(f"Flujo mixto total:             {resultados['flujo_mixto_total']:.6f} W\n")
                output.write(f"Área de transferencia:         {resultados['area_transferencia']:.6f} m²\n")
                
            elif resultados.get("regimen") == "Turbulento completo":
                output.write("Régimen: TURBULENTO COMPLETO\n")
                output.write(f"Número de Nusselt:             {resultados['numero_nusselt']:.6f}\n")
                output.write(f"Coeficiente de convección:     {resultados['coeficiente_conveccion']:.6f} W/m²·K\n")
                output.write(f"Flujo de calor total:          {resultados['flujo_calor_total']:.6f} W\n")
                output.write(f"Área de transferencia:         {resultados['area_transferencia']:.6f} m²\n")
                
        elif resultados.get("tipo_analisis") == "Flujo de calor local":
            output.write("Tipo de análisis: FLUJO DE CALOR LOCAL\n\n")
            # Mostrar posición analizada en la unidad seleccionada y en metros
            x_val_m = resultados['posicion_x']
            x_val_unidad = x_val_m / {"m":1.0, "cm":0.01, "mm":0.001, "in":0.0254, "ft":0.3048}[unidad_longitud]
            output.write(f"Posición analizada (x):        {x_val_unidad:.6f} {unidad_longitud} ({x_val_m:.6f} m)\n")
            output.write(f"Reynolds local:                {resultados['reynolds_local']:.0f}\n")
            output.write(f"Régimen local:                 {resultados['regimen_local']}\n")
            output.write(f"Número de Nusselt local:       {resultados['numero_nusselt_local']:.6f}\n")
            output.write(f"Coef. convección local:        {resultados['coeficiente_conveccion_local']:.6f} W/m²·K\n")
            output.write(f"Flujo de calor local:          {resultados['flujo_calor_local']:.6f} W/m²\n")
    else:
        output.write("No se encontraron resultados válidos para las condiciones dadas.\n")
    
    output.write("\n")
    output.write("="*80 + "\n")
    output.write("Fin del reporte\n")
    output.write("="*80 + "\n")
    
    return output.getvalue()

# Botón para descargar TXT
txt_data = crear_txt_resultados()

st.download_button(
    label="📥 Descargar resultados en TXT",
    data=txt_data,
    file_name=f"reporte_conveccion_{fluido.split()[0]}_{regimen.replace(' ', '_').replace('(', '').replace(')', '')}.txt",
    mime="text/plain",
    help="Descarga un archivo TXT con todos los datos de entrada, propiedades del fluido y resultados del análisis"
)

# Mostrar vista previa del TXT
with st.expander("Vista previa del archivo TXT"):
    st.text(txt_data)