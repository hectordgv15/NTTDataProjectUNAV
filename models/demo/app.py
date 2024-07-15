import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import time

# Load datasets
meteo_df = pd.read_csv("meteo_data.csv", sep=',')
hist_df = pd.read_csv("hist_caudal.csv", sep=',')
pron_df = pd.read_csv("pron_models.csv", sep=',')
metrics_df = pd.read_csv("error_df.csv", sep=',')
importance_df = pd.DataFrame({
    'Variable meteorológica': ['rain_roll_mean_7_day', 'soil_moisture_7_to_28cm', 'wind_gusts_10m_roll_mean_7_day', 'temperature_2m_roll_mean_30_day', 'soil_moisture_7_to_28cm_roll_mean_30_day', 'cloud_cover_low_roll_mean_30_day', 'pressure_msl_roll_mean_30_day', 'surface_pressure_roll_mean_30_day', 'pressure_msl_roll_mean_7_day', 'week_of_year_sine', 'cloud_cover_high_roll_mean_30_day', 'wind_direction_10m_roll_mean_7_day', 'cloud_cover_low_roll_mean_7_day', 'snow_depth_roll_mean_30_day', 'terrestrial_radiation'],
    'LightGBM': [1, 3, 2, 7, 4, 5, 8, 12, 6, 13, 10, 11, 9, 15, 14],
    'XGBoost': [1, 4, 2, 5, 9, 3, 12, 6, 8, 7, 13, 15, 11, 6, 10],
    'Prophet': [8, 6, 11, 3, 4, 5, 1, 2, 14, 9, 13, 10, 12, 15, 7],
    'SARIMAX': [10, 5, 8, 2, 4, 11, 1, 15, 14, 7, 12, 9, 6, 15, 14]
})

# Configure Streamlit page
st.set_page_config(
    page_title="Pronóstico de caudales para la cuenca del Duero",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar with menu options
st.sidebar.image("logo_unav.png")
menu_options = ["Central hidroeléctrica", "Datos meteorológicos", "Pronóstico caudal"]
icons = ["bar-chart", "cloud-rain"]
with st.sidebar:
    selected = option_menu("Menú", menu_options, icons=icons, menu_icon="cast", default_index=0)

# Central hidroeléctrica section
def central_hidroelectrica():
    with open('geo_map.html', 'r', encoding='utf-8') as f:
        geo_map = f.read()
    with open('aemet_map.html', 'r', encoding='utf-8') as g:
        aemet_map = g.read()

    # CSS for styling
    st.markdown("""
        <style>
        .content {
            border: 3px solid #5D4037;
            padding: 25px;
            border-radius: 15px;
            background: #FDF5E6;
            box-shadow: 4px 4px 15px #aaaaaa;
            margin-bottom: 25px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Content for central hidroeléctrica
    st.markdown("""
        <div class="content">
            <h1 style="font-size: 50px; color: #000000;">Central hidroeléctrica</h1>
            <h2 style="font-size: 35px; color: #000000;">Seleccione la central hidroeléctrica para obtener estimaciones de clima, caudal y generación de energía</h2>
            <p style="font-size: 20px; color: #000000;">Proveedor: Confederación Hidrográfica del Duero y AEMET</p>
        </div>
    """, unsafe_allow_html=True)

    opcion = st.selectbox("", ["Seleccionar", "Aldeadávila I y Aldeadávila II", "Saucelle I y Saucelle II", "Villalcampo I y Villalcampo II", "Castro I y Castro II", "Puerto Seguro", "Pereruela y San Román"])
    
    col1, col2 = st.columns(2)

    def bordered_html(map_html):
        return f"""<div style="border: 2px solid #5D4037; width: 710px; height: 510px; margin-bottom: 20px;">{map_html}</div>"""

    with col1:
        st.components.v1.html(bordered_html(geo_map), width=710, height=510)
    with col2:
        if opcion == "Pereruela y San Román":
            st.components.v1.html(bordered_html(aemet_map), width=710, height=510)
        elif opcion != "Seleccionar":
            st.warning("La opción elegida no está aún configurada")

    st.markdown("""
        <div class="footer">&copy; 2024 Pronóstico de caudales. Todos los derechos reservados.</div>
    """, unsafe_allow_html=True)

# Datos meteorológicos section
def datos_meteorologicos():
    # CSS for styling
    st.markdown("""
        <style>
        .content {
            border: 3px solid #5D4037;
            padding: 25px;
            border-radius: 15px;
            background: #FDF5E6;
            box-shadow: 4px 4px 15px #aaaaaa;
            margin-bottom: 25px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Content for datos meteorológicos
    st.markdown("""
        <div class="content">
            <h1 style="font-size: 50px; color: #000000;">Datos meteorológicos para la zona seleccionada</h1>
            <h2 style="font-size: 35px; color: #000000;">Datos históricos y pronósticos a 7 días</h2>
            <p style="font-size: 20px; color: #000000;">Proveedor: Open-Meteo</p>
        </div>
    """, unsafe_allow_html=True)

    meteo_df['date'] = pd.to_datetime(meteo_df['date'])
    historical_data = meteo_df[meteo_df['date'] <= '2024-03-31']
    forecast_data = meteo_df[meteo_df['date'] > '2024-03-31']
    
    # Create figure for plotting
    def create_figure(historical_data, forecast_data, variable, title, yaxis_title, color):
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=historical_data['date'], 
            y=historical_data[variable], 
            mode='lines', 
            name='Histórico', 
            line=dict(color=color, dash='solid')
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_data['date'], 
            y=forecast_data[variable], 
            mode='lines', 
            name='Pronóstico', 
            line=dict(color=color, dash='dash')
        ))
        
        fig.update_layout(
            title=title, 
            yaxis_title=yaxis_title, 
            template='plotly_white', 
            xaxis_rangeslider_visible=True,
            legend=dict(
                orientation="h", 
                yanchor="bottom", 
                y=1.02, 
                xanchor="right", 
                x=1,
                font=dict(color='black')
            ),
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=7, label="1w", step="day", stepmode="backward"),
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=3, label="3m", step="month", stepmode="backward"),
                        dict(step="all")
                    ]),
                    font=dict(color='black'),
                    bordercolor='#5D4037',
                    borderwidth=1
                ),
                type="date",
                showgrid=True,
                gridcolor='white',
                tickfont=dict(color='black'),
                titlefont=dict(color='black')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='white',
                tickfont=dict(color='black'),
                titlefont=dict(color='black')
            )
        )
        
        fig.add_shape(type="rect",
            x0=0, y0=0, x1=1, y1=1,
            xref='paper', yref='paper',
            line=dict(color="#5D4037", width=1))
        
        return fig

    variables = [
        ('rain', 'Lluvia', 'Lluvia (mm)', '#1f77b4'),
        ('temperature_2m', 'Temperatura a 2m', 'Temperatura (°C)', '#ff7f0e'),
        ('soil_moisture_7_to_28cm', 'Humedad del suelo 7-28cm', 'Humedad del suelo (%)', '#2ca02c'),
        ('cloud_cover_low', 'Cobertura de nubes bajas', 'Cobertura de nubes (%)', '#d62728'),
        ('wind_gusts_10m', 'Ráfagas de viento', 'Ráfagas de viento (10m)', '#9467bd'),
        ('cloud_cover_high', 'Cobertura de nubes altas', 'Cobertura de nubes (%)', '#8c564b'),
        ('terrestrial_radiation', 'Radiación terrestre', 'Radiación terrestre (W/m²)', '#e377c2'),
        ('surface_pressure', 'Presión en superficie', 'Presión en superficie (hPa)', '#7f7f7f')
    ]

    figures = [create_figure(historical_data, forecast_data, var, title, yaxis_title, color) for var, title, yaxis_title, color in variables]

    col1, col2 = st.columns(2)
    for i, fig in enumerate(figures):
        with col1 if i % 2 == 0 else col2:
            st.plotly_chart(fig, use_container_width=True)

# Pronóstico caudal section
def pronostico_caudal():
    # Calculate flow statistics
    caudal_promedio = hist_df['flow'].tail(30).mean()
    desviacion_estandar = hist_df['flow'].tail(30).std()
    caudal_min = hist_df['flow'].tail(30).min()
    caudal_max = hist_df['flow'].tail(30).max()

    # CSS for styling
    st.markdown("""
        <style>
        .content {
            border: 3px solid #5D4037;
            padding: 25px;
            border-radius: 15px;
            background: #FDF5E6;
            box-shadow: 4px 4px 15px #aaaaaa;
            margin-bottom: 25px;
        }
        .stats-container {
            display: flex;
            justify-content: space-around;
            margin-top: 25px;
        }
        .stats-box {
            border: 3px solid #5D4037;
            padding: 20px;
            border-radius: 15px;
            background: #fffaf0;
            box-shadow: 3px 3px 12px #aaaaaa;
            text-align: center;
            width: 22%;
        }
        .stats-box h3 {
            margin: 0;
            color: #000000;
            font-size: 22px;
        }
        .stats-box p {
            margin: 0;
            font-size: 26px;
            font-weight: bold;
            color: #000000;
        }
        </style>
    """, unsafe_allow_html=True)

    # Content for pronóstico caudal
    st.markdown("""
        <div class="content">
            <h1 style="font-size: 50px; color: #000000;">Pronóstico Diario del Caudal</h1>
            <h2 style="font-size: 35px; color: #000000;">Horizonte de Pronóstico Semanal: Modelos XGBoost, LightGBM, SARIMAX y Prophet</h2>
            <p style="font-size: 20px; color: #000000;">Proveedor: NTTDATA - UNAV</p>
        </div>
    """, unsafe_allow_html=True)

    # Container for flow statistics
    st.markdown(f"""
        <style>
            .stats-container {{
                border: 3px solid #5D4037; 
                background-color: #FDF5E6; 
                padding: 15px;
                display: flex;
                border-radius: 15px;
                gap: 10px;
                justify-content: space-around;
                align-items: center;
            }}
            .stats-box {{
                border: 1px solid #5D4037;
                padding: 20px;
                border-radius: 5px;
                text-align: center;
                flex: 1;
                color: #ffffff;
            }}
            .stats-box h3 {{
                font-size: 28px;
            }}
            .stats-box p {{
                font-size: 25px;
            }}
        </style>
        <div class="stats-container">
            <div class="stats-box">
                <h3>Promedio</h3>
                <p>{caudal_promedio:.2f} m³/s</p>
            </div>
            <div class="stats-box">
                <h3>Desviación</h3>
                <p>{desviacion_estandar:.2f} m³/s</p>
            </div>
            <div class="stats-box">
                <h3>Mínimo</h3>
                <p>{caudal_min:.2f} m³/s</p>
            </div>
            <div class="stats-box">
                <h3>Máximo</h3>
                <p>{caudal_max:.2f} m³/s</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <style>
        .stMultiSelect [data-baseweb="select"] {
            min-width: 100px;
            max-width: 1100px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    modelos = ['lgbm', 'xgb', 'prophet', 'sarimax']
    seleccion_modelos = st.multiselect('', modelos)

    plot_placeholder = st.empty()

    if seleccion_modelos:
        with st.spinner(f'Calculando pronóstico con modelo(s) {", ".join(seleccion_modelos)}'):
            time.sleep(2)

    for i in range(len(pron_df)):
        fig = go.Figure()

        # Historial
        fig.add_trace(go.Scatter(
            x=hist_df['date'].tail(30), 
            y=hist_df['flow'].tail(30), 
            mode='lines+markers', 
            name='Histórico',
            line=dict(color='rgba(139, 69, 19, 0.8)', dash='dash', width=2),
            marker=dict(color='rgba(139, 69, 19, 0.8)', size=6)
        ))

        # Pronósticos
        colors = {
            'lgbm': 'rgba(200, 0, 0, 0.8)',
            'xgb': 'rgba(0, 100, 0, 0.8)',
            'prophet': 'rgba(0, 0, 200, 0.8)',
            'sarimax': 'rgba(255, 140, 0, 0.8)'
        }
        for modelo in seleccion_modelos:
            fig.add_trace(go.Scatter(
                x=pron_df['date'][:i+1], 
                y=pron_df[modelo][:i+1], 
                mode='lines+markers', 
                name=f'Pronóstico {modelo}',
                line=dict(color=colors[modelo], width=2),
                marker=dict(color=colors[modelo], size=6)
            ))
        
        # Highlight forecast area
        if seleccion_modelos:
            fig.add_vrect(
                x0=hist_df['date'].tail(1).values[0], x1=pron_df['date'].iloc[i],
                fillcolor="Gray", opacity=0.3, layer="below", line_width=0,
                line=dict(dash='dot', color='gray')
            )

        fig.update_xaxes(rangeslider_visible=True, rangeselector=dict(buttons=list([
            dict(count=7, label="1w", step="day", stepmode="backward"),
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=3, label="3m", step="month", stepmode="backward"),
            dict(step="all")
        ]), font=dict(color='black'),
                    bordercolor='#5D4037',
                    borderwidth=1))

        fig.update_layout(
            title={
                'text': "Caudal del río Duero en Zamora (7 días)",
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 20}},
            yaxis_title="Caudal M3S",
            legend_title="Leyenda", 
            template="plotly_white", 
            width=1000, 
            height=600,
            paper_bgcolor="#EFE5DA",
            plot_bgcolor="#EFE5DA",
            xaxis=dict(showgrid=True, gridcolor='white', tickfont=dict(color='black'), titlefont=dict(color='black')),
            yaxis=dict(showgrid=True, gridcolor='white', tickfont=dict(color='black'), titlefont=dict(color='black'))
        )
        
        fig.add_shape(type="rect",
            x0=0, y0=0, x1=1, y1=1,
            xref='paper', yref='paper',
            line=dict(color="#5D4037", width=1.5))

        plot_placeholder.plotly_chart(fig)
        time.sleep(0.7)

    # Additional information on metrics and relevant variables
    metrics_df.sort_values(by='Value', inplace=True)
    metrics = metrics_df['Metric'].unique()
    st.markdown("<h2>Información sobre los modelos</h2><hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    mostrar_graficos = col1.checkbox('Métricas de error')
    mostrar_importancia = col2.checkbox('Variables meteorológicas relevantes')

    if mostrar_graficos:
        from plotly.subplots import make_subplots
        fig = make_subplots(rows=2, cols=2, subplot_titles=metrics)
        for i, metric in enumerate(metrics):
            metric_df = metrics_df[metrics_df['Metric'] == metric]
            row, col = divmod(i, 2)
            fig.add_trace(go.Bar(x=metric_df['Model'], y=metric_df['Value'], name=metric), row=row + 1, col=col + 1)
        fig.update_layout(title='Backtesting Modelos', showlegend=False, template='plotly_white', width=1000, height=800, paper_bgcolor="rgba(245, 245, 245, 1)", plot_bgcolor="rgba(245, 245, 245, 1)")
        st.plotly_chart(fig)

    if mostrar_importancia:
        st.markdown("""
            <style>
            .dataframe-container { margin-top: 20px; }
            .dataframe-container table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 20px; text-align: left; }
            .dataframe-container th, .dataframe-container td { padding: 15px; border: 1px solid #ddd; }
            .dataframe-container th { background-color: #f2f2f2; color: #333; }
            .dataframe-container tr:nth-child(even) { background-color: #f9f9f9; }
            .dataframe-container tr:hover { background-color: #f1f1f1; }
            </style>
        """, unsafe_allow_html=True)
        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
        st.dataframe(importance_df)
        st.markdown('</div>', unsafe_allow_html=True)

# Main selection logic
if selected == "Central hidroeléctrica":
    central_hidroelectrica()
elif selected == "Datos meteorológicos":
    datos_meteorologicos()
elif selected == "Pronóstico caudal":
    pronostico_caudal()
