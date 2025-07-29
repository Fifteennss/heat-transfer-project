import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from io import StringIO
import os

# --- Configuración inicial
st.set_page_config(layout="wide")

# --- Funciones de conversión de unidades
def convertir_longitud(valor, unidad_entrada):
    factores = {"m": 1.0, "cm": 0.01, "mm": 0.001, "in": 0.0254, "ft": 0.3048}
    return valor * factores[unidad_entrada]

def convertir_espesor(valor, unidad_entrada):
    factores = {"m": 1.0, "cm": 0.01, "mm": 0.001, "in": 0.0254, "ft": 0.3048, "μm": 1e-6}
    return valor * factores[unidad_entrada]

def convertir_radio(valor, unidad_entrada):
    factores = {"m": 1.0, "cm": 0.01, "mm": 0.001, "in": 0.0254, "ft": 0.3048}
    return valor * factores[unidad_entrada]

def convertir_area(valor, unidad_entrada):
    factores = {"m²": 1.0, "cm²": 0.0001, "mm²": 1e-6, "ft²": 0.092903, "in²": 0.00064516}
    return valor * factores[unidad_entrada]

def convertir_temperatura(valor, unidad_entrada):
    if unidad_entrada == "°F": return (valor - 32) * 5/9
    elif unidad_entrada == "K": return valor - 273.15
    return valor

def convertir_k(valor, unidad_entrada):
    factores = {"W/m·K": 1.0, "W/cm·K": 100, "W/mm·K": 1000, "BTU/(h·ft·°F)": 1.73073}
    return valor * factores[unidad_entrada]

def convertir_h(valor, unidad_entrada):
    factores = {"W/m²·K": 1.0, "W/cm²·K": 10000, "BTU/(h·ft²·°F)": 5.67826}
    return valor * factores[unidad_entrada]

def formatear_resultado(valor, unidad_salida, tipo):
    if tipo == "flujo":
        factores = {"W": 1.0, "BTU/h": 3.41214, "kcal/h": 0.859845}
        return valor * factores[unidad_salida]
    elif tipo == "flujo_area":
        factores = {"W/m²": 1.0, "BTU/(h·ft²)": 0.316998, "kcal/(h·m²)": 0.859845}
        return valor * factores[unidad_salida]

@st.cache_data
def cargar_materiales():
    """Cargar todos los archivos CSV de materiales - solo columnas necesarias"""
    materiales_dict = {}
    archivos_materiales = {
        "Metales sólidos": "tabla_a3.csv",
        "No metales sólidos": "tabla_a4.csv", 
        "Materiales de construcción": "tabla_a5.csv",
        "Aislantes": "tabla_a6.csv"
    }
    
    # Solo leer las columnas necesarias para el cálculo
    columnas_necesarias = ["Material", "Conductividad térmica (W/m·K)"]
    
    for categoria, archivo in archivos_materiales.items():
        try:
            if os.path.exists(archivo):
                # Leer solo las columnas necesarias
                df = pd.read_csv(archivo, usecols=columnas_necesarias)
                # Verificar que tenga las columnas necesarias
                if all(col in df.columns for col in columnas_necesarias):
                    materiales_dict[categoria] = df
                else:
                    st.warning(f"El archivo {archivo} no tiene las columnas necesarias: {columnas_necesarias}")
            else:
                st.warning(f"No se encontró el archivo: {archivo}")
        except Exception as e:
            st.error(f"Error al cargar {archivo}: {str(e)}")
    
    # Si no se pudieron cargar archivos, usar datos de ejemplo
    if not materiales_dict:
        st.info("No se encontraron archivos CSV. Usando base de datos de ejemplo.")
        materiales_dict = crear_datos_ejemplo()
    
    return materiales_dict

def crear_datos_ejemplo():
    """Crear datos de ejemplo si no se encuentran los archivos CSV - solo columnas necesarias"""
    return {
        "Metales sólidos": pd.DataFrame({
            "Material": ["Aluminio", "Cobre", "Acero inoxidable", "Hierro", "Plomo"],
            "Conductividad térmica (W/m·K)": [237.0, 401.0, 16.2, 80.2, 35.3]
        }),
        "No metales sólidos": pd.DataFrame({
            "Material": ["Vidrio", "Cuarzo", "Granito", "Mármol", "Hielo"],
            "Conductividad térmica (W/m·K)": [1.4, 1.3, 2.8, 2.1, 1.88]
        }),
        "Materiales de construcción": pd.DataFrame({
            "Material": ["Concreto", "Ladrillo", "Madera de pino", "Yeso", "Asfalto"],
            "Conductividad térmica (W/m·K)": [1.4, 0.72, 0.12, 0.17, 0.062]
        }),
        "Aislantes": pd.DataFrame({
            "Material": ["Lana de vidrio", "Poliestireno expandido", "Espuma de poliuretano", "Corcho", "Aire"],
            "Conductividad térmica (W/m·K)": [0.038, 0.036, 0.026, 0.045, 0.026]
        })
    }

def generar_color(i):
    colores_base = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
    ]
    return colores_base[i % len(colores_base)]

def dibujar_anillos_radiales(radios, unidad_radio, unidad_espesor):
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Factor de conversión para espesores
    factor_espesor = {"m": 1.0, "cm": 100, "mm": 1000, "in": 39.3701, "ft": 3.28084, "μm": 1e6}[unidad_espesor]
    
    for i, (r_i, r_o, mat) in enumerate(radios):
        espesor_display = (r_o - r_i) * factor_espesor
        
        wedge = Wedge((0, 0), r_o, 0, 360, width=r_o - r_i, 
                     facecolor=generar_color(i), edgecolor='k', linewidth=2)
        ax.add_patch(wedge)
        
        # Texto con material y espesor únicamente
        radio_medio = (r_i + r_o) / 2
        ax.text(0, radio_medio, f"{mat}\n{espesor_display:.3f} {unidad_espesor}", 
                ha='center', va='center', fontsize=10, color='white', weight='bold')
    
    ax.set_aspect('equal')
    max_radio = radios[-1][1]
    ax.set_xlim(-max_radio * 1.1, max_radio * 1.1)
    ax.set_ylim(-max_radio * 1.1, max_radio * 1.1)
    ax.axis('off')
    ax.set_title(f"Configuración de Capas Cilíndricas", fontsize=14, weight='bold')
    st.pyplot(fig)

def dibujar_capas_rectangulares(capas, unidad_espesor):
    fig, ax = plt.subplots(figsize=(12, 4))
    
    factor_espesor = {"m": 1.0, "cm": 100, "mm": 1000, "in": 39.3701, "ft": 3.28084, "μm": 1e6}[unidad_espesor]
    inicio = 0
    
    for i, capa in enumerate(capas):
        ancho_visual = capa['L'] * factor_espesor
        rect = ax.barh(0, ancho_visual, left=inicio, height=0.8, 
                      label=capa['material'], color=generar_color(i), 
                      edgecolor='k', linewidth=2)
        
        # Texto con material y espesor únicamente
        ax.text(inicio + ancho_visual / 2, 0, 
               f"{capa['material']}\n{ancho_visual:.3f} {unidad_espesor}", 
               ha='center', va='center', fontsize=11, color='white', weight='bold')
        
        inicio += ancho_visual
    
    ax.set_xlim(-inicio*0.05, inicio*1.05)
    ax.set_ylim(-0.6, 0.6)
    ax.axis('off')
    ax.set_title(f"Configuración de Capas Planas", fontsize=14, weight='bold')
    st.pyplot(fig)

# --- Sidebar mejorado con explicaciones
st.sidebar.title("⚙️ Configuración de Unidades")

# Información del sistema de unidades actual
st.sidebar.info("**Sistema de Unidades Actual**")

geometria = st.sidebar.selectbox("Geometría del problema", 
                                ["Plana", "Cilíndrica", "Esférica"],
                                help="Selecciona el tipo de geometría para el análisis de conducción")

st.sidebar.markdown("---")
st.sidebar.subheader("Unidades de Dimensiones")

unidad_longitud = st.sidebar.selectbox("Longitud general", 
                                      ["m", "cm", "mm", "in", "ft"],
                                      help="Unidad para longitudes generales (ej: longitud del cilindro)")

unidad_radio = st.sidebar.selectbox("Radios", 
                                   ["m", "cm", "mm", "in", "ft"],
                                   help="Unidad específica para radios internos y externos")

unidad_espesor = st.sidebar.selectbox("Espesores", 
                                     ["m", "cm", "mm", "in", "ft", "μm"],
                                     help="Unidad específica para espesores de capas (incluye micrómetros)")

unidad_area = st.sidebar.selectbox("Área", 
                                  ["m²", "cm²", "mm²", "ft²", "in²"],
                                  help="Unidad para el área total (solo geometría plana)")

st.sidebar.markdown("---")
st.sidebar.subheader("Unidades de Temperatura")

unidad_temp = st.sidebar.selectbox("Temperatura", 
                                  ["°C", "°F", "K"],
                                  help="Unidad para las temperaturas de entrada")

st.sidebar.markdown("---")
st.sidebar.subheader("Unidades de Propiedades Térmicas")

unidad_k = st.sidebar.selectbox("Conductividad térmica (k)", 
                               ["W/m·K", "W/cm·K", "W/mm·K", "BTU/(h·ft·°F)"],
                               help="Unidad para la conductividad térmica de los materiales")

unidad_h = st.sidebar.selectbox("Coeficiente de convección (h)", 
                               ["W/m²·K", "W/cm²·K", "BTU/(h·ft²·°F)"],
                               help="Unidad para los coeficientes de convección")

st.sidebar.markdown("---")
st.sidebar.subheader("Unidades de Resultados")

unidad_flujo = st.sidebar.selectbox("Flujo de calor", 
                                   ["W", "BTU/h", "kcal/h"],
                                   help="Unidad para el flujo total de calor")

unidad_flujo_area = st.sidebar.selectbox("Flujo por área", 
                                        ["W/m²", "BTU/(h·ft²)", "kcal/(h·m²)"],
                                        help="Unidad para el flujo de calor por unidad de área")

# Resumen del sistema de unidades actual
st.sidebar.markdown("---")
st.sidebar.markdown("**Resumen actual:**")
st.sidebar.markdown(f"""
- **Longitud:** {unidad_longitud}
- **Radios:** {unidad_radio}
- **Espesores:** {unidad_espesor}
- **Temperatura:** {unidad_temp}  
- **Conductividad:** {unidad_k}
- **Resultados:** {unidad_flujo}
""")

# --- Título principal con información de unidades
titulo = {
    "Plana": "Pared Compuesta en Serie (Plana)",
    "Cilíndrica": "Cilindro Multicapa en Serie",
    "Esférica": "Esfera Multicapa en Serie"
}[geometria]

st.title(f"Conducción - {titulo}")
st.info(f"**Sistema de unidades activo:** Longitud = {unidad_longitud} | Radios = {unidad_radio} | Espesores = {unidad_espesor} | Temperatura = {unidad_temp}")

# --- Entradas generales con etiquetas dinámicas
st.subheader("Condiciones de Temperatura")
col1, col2 = st.columns(2)
with col1:
    T1 = st.number_input(f"🔴 Temperatura interna ({unidad_temp})", 
                        value=100.0, step=1.0,
                        help=f"Temperatura del lado caliente en {unidad_temp}")
with col2:
    T2 = st.number_input(f"🔵 Temperatura externa ({unidad_temp})", 
                        value=25.0, step=1.0,
                        help=f"Temperatura del lado frío en {unidad_temp}")

st.subheader("Dimensiones Geométricas")
if geometria == "Plana":
    A_total = st.number_input(f"Área total de transferencia ({unidad_area})", 
                             value=1.0, step=0.1, min_value=0.0001,
                             help=f"Área perpendicular al flujo de calor en {unidad_area}")
else:
    L_cil = st.number_input(f"Longitud del cilindro ({unidad_longitud})", 
                           min_value=0.0001, value=1.0, step=0.1,
                           help=f"Longitud axial del cilindro en {unidad_longitud}")

n_capas = st.slider("Número de capas del material", 1, 5, 2,
                   help="Cantidad de capas diferentes de materiales")

# Convección con etiquetas mejoradas
st.subheader("Resistencia por Convección (Opcional)")
usar_conveccion = st.checkbox("Incluir resistencia por convección en las superficies",
                             help="Activar para considerar la resistencia térmica por convección en las superficies interna y externa")

if usar_conveccion:
    col1, col2 = st.columns(2)
    with col1:
        h_in = st.number_input(f"🔴 Coef. convección interior ({unidad_h})", 
                              value=10.0, step=1.0, min_value=0.1,
                              help=f"Coeficiente de convección del lado caliente en {unidad_h}")
    with col2:
        h_out = st.number_input(f"🔵 Coef. convección exterior ({unidad_h})", 
                               value=10.0, step=1.0, min_value=0.1,
                               help=f"Coeficiente de convección del lado frío en {unidad_h}")
else:
    h_in = h_out = 0

# Cargar materiales desde los archivos CSV
materiales_dict = cargar_materiales()

# --- Configuración de capas con base de datos mejorada
st.subheader(f"Configuración de Capas")
st.info(f"**Unidades activas para esta sección:** Radios = {unidad_radio} | Espesores = {unidad_espesor}")

# Mostrar información sobre los materiales cargados
if materiales_dict:
    with st.expander("📚 Base de Datos de Materiales Disponibles"):
        for categoria, df in materiales_dict.items():
            st.write(f"**{categoria}:** {len(df)} materiales disponibles")
            if not df.empty:
                st.dataframe(df, use_container_width=True)

tabla_capas = []
radios = []
r_i_actual = None

for i in range(n_capas):
    with st.expander(f"Capa {i + 1}", expanded=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown("**Material y Propiedades**")
            manual = st.checkbox(f"Ingresar conductividad manualmente", 
                               key=f"k_manual_{i}",
                               help="Activar para ingresar el valor de k manualmente")
            
            if manual:
                mat = st.text_input("Nombre del material", 
                                  value=f"Capa {i + 1}", key=f"mat_{i}")
                k = st.number_input(f"Conductividad térmica ({unidad_k})", 
                                  min_value=0.0001, value=0.5, key=f"k_{i}", step=0.001, format="%.4f",
                                  help=f"Valor de conductividad térmica en {unidad_k}")
            else:
                # Selección de categoría
                if materiales_dict:
                    categoria = st.selectbox("Categoría de material", 
                                           list(materiales_dict.keys()), 
                                           key=f"cat_{i}",
                                           help="Selecciona la categoría del material")
                    
                    if categoria in materiales_dict and not materiales_dict[categoria].empty:
                        df_categoria = materiales_dict[categoria]
                        mat = st.selectbox("Seleccionar material", 
                                         df_categoria["Material"].tolist(), 
                                         key=f"mat_sel_{i}",
                                         help=f"Materiales disponibles en la categoría: {categoria}")
                        
                        # Obtener propiedades del material seleccionado
                        df_filtrado = df_categoria[df_categoria["Material"].str.strip() == mat.strip()]
                        if not df_filtrado.empty:
                            valor_crudo = df_filtrado.iloc[0]["Conductividad térmica (W/m·K)"]
                            try:
                                k_valor = float(valor_crudo)
                            except ValueError:
                                st.error(f"⚠️ Valor de conductividad no numérico para '{mat}': '{valor_crudo}'. Se usa k=1.0 W/m·K")
                                k_valor = 1.0
                        else:
                            st.error(f"⚠️ El material '{mat}' no se encontró en la tabla.")
                            k_valor = 1.0
                        
                        # Mostrar información del material
                        st.success(f"**{mat}:**")
                        st.write(f"• k = {k_valor} W/m·K")
                        
                        k = k_valor
                    else:
                        st.error("No hay materiales disponibles en esta categoría")
                        k = 1.0
                        mat = "Material desconocido"
                else:
                    st.error("No se pudieron cargar los archivos de materiales")
                    k = 1.0
                    mat = "Material desconocido"
            
            k = convertir_k(float(k), unidad_k)
        
        with col2:
            st.markdown("**Dimensiones**")
            if i == 0 and geometria != "Plana":
                r_i = convertir_radio(
                    st.number_input(f"Radio interior ({unidad_radio})", 
                                  min_value=0.0001, value=0.01, key="r_i", step=0.001,
                                  help=f"Radio interno de la primera capa en {unidad_radio}"), 
                    unidad_radio)
                
                e = convertir_espesor(
                    st.number_input(f"Espesor de la capa ({unidad_espesor})", 
                                  min_value=0.0001, value=0.005, key=f"e_{i}", step=0.001,
                                  help=f"Espesor de esta capa en {unidad_espesor}"), 
                    unidad_espesor)
                
                r_o = r_i + e
                r_i_actual = r_o
                radios.append((r_i, r_o, mat))
                
                # Mostrar información calculada
                factor_display_radio = {"m": 1.0, "cm": 100, "mm": 1000, "in": 39.3701, "ft": 3.28084}[unidad_radio]
                st.success(f"Radio exterior: {r_o * factor_display_radio:.4f} {unidad_radio}")
                
            else:
                e = convertir_espesor(
                    st.number_input(f"Espesor de la capa ({unidad_espesor})", 
                                  min_value=0.0001, value=0.005, key=f"e_{i}", step=0.001,
                                  help=f"Espesor de esta capa en {unidad_espesor}"), 
                    unidad_espesor)
                
                if geometria != "Plana":
                    r_i = r_i_actual
                    r_o = r_i + e
                    radios.append((r_i, r_o, mat))
                    r_i_actual = r_o
                    
                    # Mostrar información calculada
                    factor_display_radio = {"m": 1.0, "cm": 100, "mm": 1000, "in": 39.3701, "ft": 3.28084}[unidad_radio]
                    st.success(f"Radio exterior: {r_o * factor_display_radio:.4f} {unidad_radio}")
        
        with col3:
            st.markdown("**Información**")
            st.metric("Capa", f"#{i+1}")
            if geometria != "Plana" and radios:
                st.metric("Geometría", geometria)
    
    tabla_capas.append({"material": mat, "L": e, "k": k})

# --- Visualización mejorada
st.subheader("📊 Visualización de la Configuración")
if geometria == "Plana":
    dibujar_capas_rectangulares(tabla_capas, unidad_espesor)
else:
    dibujar_anillos_radiales(radios, unidad_radio, unidad_espesor)

# --- Cálculo con resultados más detallados
if st.button("**Calcular Transferencia de Calor**", type="primary"):
    with st.spinner("Calculando..."):
        T1_C = convertir_temperatura(T1, unidad_temp)
        T2_C = convertir_temperatura(T2, unidad_temp)
        
        if geometria == "Plana":
            A_m2 = convertir_area(A_total, unidad_area)
            R_capas = sum(c["L"] / (c["k"] * A_m2) for c in tabla_capas)
            R_conv_in = 1 / (convertir_h(h_in, unidad_h) * A_m2) if h_in > 0 else 0
            R_conv_out = 1 / (convertir_h(h_out, unidad_h) * A_m2) if h_out > 0 else 0
            R_total = R_capas + R_conv_in + R_conv_out
            
        elif geometria == "Cilíndrica":
            L_cil_m = convertir_longitud(L_cil, unidad_longitud)
            R_capas = 0
            for (r_i, r_o, _), c in zip(radios, tabla_capas):
                R_capas += np.log(r_o / r_i) / (2 * np.pi * L_cil_m * c["k"])
            R_conv_in = 1 / (convertir_h(h_in, unidad_h) * 2 * np.pi * radios[0][0] * L_cil_m) if h_in > 0 else 0
            R_conv_out = 1 / (convertir_h(h_out, unidad_h) * 2 * np.pi * radios[-1][1] * L_cil_m) if h_out > 0 else 0
            R_total = R_capas + R_conv_in + R_conv_out
            
        elif geometria == "Esférica":
            R_capas = 0
            for (r_i, r_o, _), c in zip(radios, tabla_capas):
                R_capas += (1 / (4 * np.pi * c["k"])) * (1/r_i - 1/r_o)
            R_conv_in = 1 / (convertir_h(h_in, unidad_h) * 4 * np.pi * radios[0][0]**2) if h_in > 0 else 0
            R_conv_out = 1 / (convertir_h(h_out, unidad_h) * 4 * np.pi * radios[-1][1]**2) if h_out > 0 else 0
            R_total = R_capas + R_conv_in + R_conv_out

        q = (T1_C - T2_C) / R_total
        A_ref = convertir_area(A_total, unidad_area) if geometria == "Plana" else 1

        # Mostrar resultados detallados
        st.success("**Cálculo Completado**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Diferencia de temperatura", f"{T1_C - T2_C:.2f} °C")
            st.metric("Flujo de calor total", 
                     f"{formatear_resultado(q, unidad_flujo, 'flujo'):.2f} {unidad_flujo}")
            
        with col2:
            st.metric("Resistencia total", f"{R_total:.6f} K/W")
            if geometria == "Plana":
                st.metric("📊 Flujo por área", 
                         f"{formatear_resultado(q/A_ref, unidad_flujo_area, 'flujo_area'):.2f} {unidad_flujo_area}")

        # Desglose de resistencias
        st.subheader("Desglose de Resistencias")
        resistencias_df = pd.DataFrame({
            "Componente": ["Convección interna", "Capas (conducción)", "Convección externa"],
            "Resistencia (K/W)": [R_conv_in, R_capas, R_conv_out],
            "Porcentaje (%)": [R_conv_in/R_total*100, R_capas/R_total*100, R_conv_out/R_total*100]
        })
        st.dataframe(resistencias_df, use_container_width=True)
        
        # --- EXPORTACIÓN A TXT ---
        st.subheader("Exportar Resultados")

        def crear_txt_resultados():
            """Función para crear el archivo TXT con todos los datos y resultados"""
            
            output = StringIO()
            
            # Encabezado
            output.write("="*80 + "\n")
            output.write(f"ANÁLISIS DE CONDUCCIÓN - {titulo.upper()}\n")
            output.write("="*80 + "\n\n")
            
            # Datos de entrada
            output.write("DATOS DE ENTRADA:\n")
            output.write("-"*50 + "\n")
            output.write(f"Geometría del problema:        {geometria}\n")
            output.write(f"Número de capas:               {n_capas}\n")
            output.write(f"Temperatura interna:           {T1:.2f} {unidad_temp}\n")
            output.write(f"Temperatura externa:           {T2:.2f} {unidad_temp}\n")
            
            if geometria == "Plana":
                output.write(f"Área total de transferencia:   {A_total:.4f} {unidad_area}\n")
            else:
                output.write(f"Longitud del cilindro:         {L_cil:.4f} {unidad_longitud}\n")
            
            if usar_conveccion:
                output.write(f"Coef. convección interior:    {h_in:.2f} {unidad_h}\n")
                output.write(f"Coef. convección exterior:     {h_out:.2f} {unidad_h}\n")
            else:
                output.write("Convección:                    No incluida\n")
            
            output.write(f"\nSistema de unidades usado:     Long={unidad_longitud}, Radio={unidad_radio}, Esp={unidad_espesor}, Temp={unidad_temp}\n")
            output.write("\n")
            
            # Configuración de capas
            output.write("CONFIGURACIÓN DE CAPAS:\n")
            output.write("-"*50 + "\n")
            for i, capa in enumerate(tabla_capas):
                output.write(f"Capa {i+1}:\n")
                output.write(f"  Material:                    {capa['material']}\n")
                output.write(f"  Espesor:                     {capa['L']:.6f} m\n")
                output.write(f"  Conductividad térmica:       {capa['k']:.6f} W/m·K\n")
                
                if geometria != "Plana" and i < len(radios):
                    r_i, r_o, _ = radios[i]
                    output.write(f"  Radio interior:              {r_i:.6f} m\n")
                    output.write(f"  Radio exterior:              {r_o:.6f} m\n")
                output.write("\n")
            
            # Resistencias térmicas
            output.write("RESISTENCIAS TÉRMICAS:\n")
            output.write("-"*50 + "\n")
            output.write(f"Resistencia por convección interna:  {R_conv_in:.8f} K/W ({R_conv_in/R_total*100:.2f}%)\n")
            output.write(f"Resistencia por conducción (capas):  {R_capas:.8f} K/W ({R_capas/R_total*100:.2f}%)\n")
            output.write(f"Resistencia por convección externa:  {R_conv_out:.8f} K/W ({R_conv_out/R_total*100:.2f}%)\n")
            output.write(f"Resistencia térmica total:           {R_total:.8f} K/W\n")
            output.write("\n")
            
            # Resultados del análisis
            output.write("RESULTADOS DEL ANÁLISIS:\n")
            output.write("-"*50 + "\n")
            output.write(f"Diferencia de temperatura:     {T1_C - T2_C:.2f} °C\n")
            output.write(f"Flujo de calor total:          {formatear_resultado(q, unidad_flujo, 'flujo'):.6f} {unidad_flujo}\n")
            output.write(f"Flujo de calor (base SI):      {q:.6f} W\n")
            
            if geometria == "Plana":
                output.write(f"Flujo de calor por área:       {formatear_resultado(q/A_ref, unidad_flujo_area, 'flujo_area'):.6f} {unidad_flujo_area}\n")
                output.write(f"Área de referencia:            {A_ref:.6f} m²\n")
            
            # Información sobre materiales utilizados
            output.write("\n")
            output.write("MATERIALES UTILIZADOS:\n")
            output.write("-"*50 + "\n")
            for i, capa in enumerate(tabla_capas):
                output.write(f"Capa {i+1}: {capa['material']}\n")
                # Si el material viene de la base de datos, mostrar propiedades
                material_encontrado = False
                for categoria, df in materiales_dict.items():
                    if not df.empty and capa['material'] in df['Material'].values:
                        material_info = df[df['Material'] == capa['material']].iloc[0]
                        output.write(f"  Categoría: {categoria}\n")
                        output.write(f"  Conductividad térmica: {material_info['Conductividad térmica (W/m·K)']} W/m·K\n")
                        material_encontrado = True
                        break
                if not material_encontrado:
                    output.write(f"  Material personalizado\n")
                    output.write(f"  Conductividad térmica: {capa['k']:.6f} W/m·K\n")
                output.write("\n")
            
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
            file_name=f"reporte_conduccion_{geometria.lower()}_{n_capas}capas.txt",
            mime="text/plain",
            help="Descarga un archivo TXT con todos los datos de entrada, configuración de capas y resultados del análisis"
        )

        # Mostrar vista previa del TXT
        with st.expander("Vista previa del archivo TXT"):
            st.text(txt_data)