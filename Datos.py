import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Sensores ESP32",
    page_icon="🔌",
    layout="wide"
)

st.title("🔌 Dashboard de Monitoreo - Proyecto Electrónica")

# ★★★ CONFIGURACIÓN ★★★
SPREADSHEET_ID = "1k78q-NphTejY9YaNQF1Mr2wxa6jsjTidXyJUnPFss3o" 

# Scopes específicos para Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
# ★★★ FIN CONFIGURACIÓN ★★★

@st.cache_data(ttl=300)
def load_data():
    try:
        creds = Credentials.from_service_account_file(
            'credentials.json', 
            scopes=SCOPES  
        )
        client = gspread.authorize(creds)
        
        # Acceder a la hoja de cálculo
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        records = sheet.get_all_records()
        
        df = pd.DataFrame(records)
        
        # Convertir fecha/hora
        if 'FechaHora' in df.columns:
            df['FechaHora'] = pd.to_datetime(df['FechaHora'])
        elif 'Timestamp' in df.columns:
            df['FechaHora'] = pd.to_datetime(df['Timestamp'])
        else:
            # Si no hay columna de tiempo, crear una
            df['FechaHora'] = pd.date_range(
                start=datetime.now() - timedelta(days=1), 
                periods=len(df), 
                freq='10S'
            )
        
        return df
    
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

# Cargar datos
df = load_data()

if not df.empty:
    st.success(f"✅ Datos cargados correctamente: {len(df)} registros")
    
    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Registros", len(df))
    
    with col2:
        if 'Voltaje' in df.columns:
            st.metric("⚡ Voltaje Promedio", f"{df['Voltaje'].mean():.2f} V")
        else:
            st.metric("⚡ Voltaje", "N/A")
    
    with col3:
        if 'Temperatura' in df.columns:
            st.metric("🌡️ Temp. Actual", f"{df['Temperatura'].iloc[-1]:.1f} °C")
        else:
            st.metric("🌡️ Temperatura", "N/A")
    
    with col4:
        if 'Humedad' in df.columns:
            st.metric("💧 Humedad Actual", f"{df['Humedad'].iloc[-1]:.1f} %")
        else:
            st.metric("💧 Humedad", "N/A")

    # Mostrar columnas disponibles para debugging
    st.sidebar.markdown("### 🔍 Columnas disponibles:")
    if not df.empty:
        for col in df.columns:
            st.sidebar.write(f"- `{col}`")

    # Gráfico de evolución temporal
    if 'FechaHora' in df.columns:
        st.subheader("📈 Evolución Temporal")
        
        # Seleccionar variables para graficar
        available_columns = [col for col in df.columns if col != 'FechaHora' and df[col].dtype in ['float64', 'int64']]
        
        if available_columns:
            selected_columns = st.multiselect(
                "Selecciona variables para graficar:",
                available_columns,
                default=available_columns[:2] if len(available_columns) >= 2 else available_columns
            )
            
            if selected_columns:
                fig = go.Figure()
                
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
                
                for i, col in enumerate(selected_columns):
                    fig.add_trace(go.Scatter(
                        x=df['FechaHora'], 
                        y=df[col],
                        name=col,
                        line=dict(color=colors[i % len(colors)])
                    ))
                
                fig.update_layout(
                    title="Evolución de Sensores en el Tiempo",
                    xaxis_title="Fecha y Hora",
                    yaxis_title="Valores",
                    hovermode='x unified',
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay columnas numéricas para graficar")

    # Mostrar datos en tabla
    st.subheader("📋 Datos Recientes")
    
    # Mostrar información sobre la estructura de datos
    with st.expander("🔍 Ver estructura de datos"):
        st.write("**Tipos de datos:**")
        st.write(df.dtypes)
        st.write("**Primeras filas:**")
        st.dataframe(df.head(), use_container_width=True)
    
    st.dataframe(df.tail(10), use_container_width=True)

else:
    st.error("❌ No se pudieron cargar los datos")
    
    with st.expander("🔧 Solución de problemas", expanded=True):
        
        # Mostrar estructura esperada
        ejemplo_data = {
            'FechaHora': ['2024-01-01 10:00:00', '2024-01-01 10:00:10'],
            'Voltaje': [3.3, 3.2],
            'CorrienteINA': [150.5, 148.2],
            'Potencia': [495.0, 480.0],
            'CorrienteACS': [145.0, 143.5],
            'Temperatura': [25.5, 25.6],
            'Humedad': [60.0, 59.8]
        }
        st.dataframe(pd.DataFrame(ejemplo_data))

# Auto-actualización
st.sidebar.markdown("---")
st.sidebar.info("Los datos se actualizan automáticamente cada 5 minutos")
if st.sidebar.button("🔄 Actualizar Ahora"):
    st.cache_data.clear()
    st.rerun()

# Información de debug
st.sidebar.markdown("---")
st.sidebar.write(f"📊 Datos cargados: {len(df)} registros")