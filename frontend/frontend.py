import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import io
from datetime import datetime, timedelta
import time
import numpy as np

# Page configuration
st.set_page_config(
    page_title="FloatChat - ARGO Data Explorer",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for modern, professional UI
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global styling */
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #475569 75%, #64748b 100%);
        color: white;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Enhanced sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(148, 163, 184, 0.1);
    }
    
    /* Modern metric cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05));
        backdrop-filter: blur(15px);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        margin-bottom: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(59, 130, 246, 0.2);
        border-color: rgba(59, 130, 246, 0.3);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: rgba(148, 163, 184, 0.9);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Enhanced chat messages */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 24px;
        padding: 1.5rem 2rem;
        margin: 16px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    [data-testid="stChatMessage"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    /* User message styling */
    div[data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-user"]) {
        margin-left: auto;
        margin-right: 0;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(37, 99, 235, 0.1));
        border-color: rgba(59, 130, 246, 0.3);
    }
    
    /* Assistant message styling */
    div[data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-assistant"]) {
        margin-left: 0;
        margin-right: auto;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.1));
        border-color: rgba(16, 185, 129, 0.3);
    }
    
    /* Enhanced buttons */
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.875rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(59, 130, 246, 0.4);
        background: linear-gradient(135deg, #2563eb, #1e40af);
    }
    
    /* Welcome screen enhancement */
    .welcome-container {
        text-align: center;
        padding: 4rem 2rem;
        max-width: 1000px;
        margin: 0 auto;
    }
    
    .welcome-title {
        font-size: 4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa, #34d399, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        line-height: 1.1;
    }
    
    .welcome-subtitle {
        font-size: 1.25rem;
        color: rgba(148, 163, 184, 0.8);
        margin-bottom: 3rem;
        font-weight: 400;
    }
    
    .example-prompts {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin-top: 3rem;
    }
    
    .prompt-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        backdrop-filter: blur(15px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        padding: 2rem;
        border-radius: 20px;
        font-size: 0.95rem;
        text-align: left;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .prompt-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
        border-color: rgba(59, 130, 246, 0.4);
    }
    
    .prompt-card strong {
        color: #60a5fa;
        font-weight: 600;
        font-size: 1.1rem;
        display: block;
        margin-bottom: 8px;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-online {
        background-color: #10b981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
    }
    
    .status-offline {
        background-color: #ef4444;
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
    }
    
    /* Enhanced tabs */
    .stTabs [data-baseweb="tab-list"] button {
        background-color: rgba(255, 255, 255, 0.05);
        color: rgba(148, 163, 184, 0.8);
        border-radius: 12px;
        margin-right: 8px;
        padding: 12px 20px;
        font-weight: 500;
        border: 1px solid rgba(148, 163, 184, 0.1);
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        border-color: #3b82f6;
    }
    
    /* Loading animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading-pulse {
        animation: pulse 2s infinite;
    }
    
    /* Data table enhancements */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.1);
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'backend_status' not in st.session_state:
    st.session_state.backend_status = 'checking'

# Backend API configuration
BACKEND_URL = "http://localhost:5000"

# Enhanced helper functions
def check_backend_status():
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{BACKEND_URL}/stats", timeout=5)
        if response.status_code == 200:
            st.session_state.backend_status = 'online'
            return True
        else:
            st.session_state.backend_status = 'offline'
            return False
    except requests.exceptions.RequestException:
        st.session_state.backend_status = 'offline'
        return False

def query_backend(user_query):
    """Send query to Flask backend with enhanced error handling"""
    try:
        with st.spinner("🔍 Analyzing your query..."):
            response = requests.post(
                f"{BACKEND_URL}/ask",
                json={"query": user_query},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Backend responded with status {response.status_code}"}
    except requests.exceptions.Timeout:
        return {"error": "Query timeout - the backend took too long to respond"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend service - please ensure it's running"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}"}

def get_stats():
    """Get statistics from backend with fallback data"""
    try:
        response = requests.get(f"{BACKEND_URL}/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return create_fallback_stats()
    except requests.exceptions.RequestException:
        return create_fallback_stats()

def create_fallback_stats():
    """Create fallback stats when backend is unavailable"""
    return {
        "count": "N/A",
        "pressure_count": "N/A",
        "latest_date": "N/A",
        "fallback": True
    }

# Enhanced visualization functions
def create_float_trajectory_map(data):
    """Create an interactive trajectory map with enhanced styling"""
    if not data or 'results' not in data:
        return create_empty_figure("No trajectory data available")
    
    profile_data = [r for r in data['results'] if 'warning' not in r]
    if not profile_data:
        return create_empty_figure("No valid profile data found")
    
    df = pd.DataFrame(profile_data)
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    
    for i, float_id in enumerate(df['float_id'].unique()[:10]):  # Limit to 10 floats for performance
        float_data = df[df['float_id'] == float_id].copy()
        float_data['date'] = pd.to_datetime(float_data['date'])
        float_data = float_data.sort_values('date')
        
        color = colors[i % len(colors)]
        
        # Add trajectory line
        fig.add_trace(go.Scattermapbox(
            lon=float_data['longitude'],
            lat=float_data['latitude'],
            mode='lines',
            name=f'Float {float_id} Path',
            line=dict(width=3, color=color),
            opacity=0.7,
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Add measurement points
        fig.add_trace(go.Scattermapbox(
            lon=float_data['longitude'],
            lat=float_data['latitude'],
            mode='markers',
            name=f'Float {float_id}',
            marker=dict(
                size=12,
                color=color,
                symbol='circle',
                line=dict(width=2, color='white')
            ),
            text=[f"<b>Float {float_id}</b><br>" +
                  f"📅 {date.strftime('%Y-%m-%d')}<br>" +
                  f"📍 {lat:.3f}°N, {lon:.3f}°E<br>" +
                  f"🌡️ {temp_count} temp readings<br>" +
                  f"📊 {pres_count} pressure readings" 
                  for date, lat, lon, temp_count, pres_count in zip(
                      float_data['date'], float_data['latitude'], float_data['longitude'],
                      float_data['temperature_count'], float_data['pressure_count'])],
            hovertemplate='%{text}<extra></extra>'
        ))
    
    # Calculate center and zoom
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    lat_range = df['latitude'].max() - df['latitude'].min()
    lon_range = df['longitude'].max() - df['longitude'].min()
    zoom = max(0, min(10, 8 - max(lat_range, lon_range)))
    
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom
        ),
        title=dict(
            text='🌊 ARGO Float Trajectories',
            font=dict(size=20, color='white'),
            x=0.5
        ),
        height=600,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=0, r=0, t=60, b=0),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1
        )
    )
    return fig

def create_depth_temperature_plot(data):
    """Enhanced depth vs temperature profile plot"""
    if not data or 'results' not in data:
        return create_empty_figure("No temperature profile data available")
    
    profile_data = [r for r in data['results'] if 'warning' not in r]
    if not profile_data:
        return create_empty_figure("No valid temperature data found")
    
    fig = go.Figure()
    colors = px.colors.qualitative.Set2
    
    profiles_added = 0
    for idx, row in enumerate(profile_data):
        if profiles_added >= 8:  # Limit to 8 profiles for readability
            break
            
        try:
            temps = json.loads(row['temperature_values'])
            pressures = json.loads(row['pressure_levels'])
            
            if temps and pressures and len(temps) > 0 and len(pressures) > 0:
                # Handle different JSON structures
                temp_vals = []
                pres_vals = []
                
                for t, p in zip(temps[:min(len(temps), len(pressures))], pressures[:min(len(temps), len(pressures))]):
                    try:
                        if isinstance(t, dict):
                            temp_val = float(t.get('value', t.get('temperature', 0)))
                        else:
                            temp_val = float(t)
                        
                        if isinstance(p, dict):
                            pres_val = float(p.get('value', p.get('pressure', 0)))
                        else:
                            pres_val = float(p)
                        
                        if temp_val > -5 and temp_val < 40 and pres_val > 0:  # Reasonable ranges
                            temp_vals.append(temp_val)
                            pres_vals.append(pres_val)
                    except (ValueError, KeyError):
                        continue
                
                if len(temp_vals) > 0:
                    color = colors[profiles_added % len(colors)]
                    fig.add_trace(go.Scatter(
                        x=temp_vals,
                        y=pres_vals,
                        mode='lines+markers',
                        name=f"Float {row['float_id']}",
                        line=dict(width=3, color=color),
                        marker=dict(size=6, color=color, line=dict(width=1, color='white')),
                        text=[f"🌡️ {t:.2f}°C<br>📊 {p:.1f} dbar" for t, p in zip(temp_vals, pres_vals)],
                        hovertemplate='%{text}<extra></extra>'
                    ))
                    profiles_added += 1
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            continue
    
    if profiles_added == 0:
        return create_empty_figure("No valid temperature profiles could be processed")
    
    fig.update_layout(
        title=dict(
            text='🌡️ Temperature vs Depth Profiles',
            font=dict(size=20, color='white'),
            x=0.5
        ),
        xaxis=dict(
            title='Temperature (°C)',
            titlefont=dict(size=14, color='white'),
            tickfont=dict(color='white'),
            gridcolor='rgba(255,255,255,0.1)',
            zerolinecolor='rgba(255,255,255,0.2)'
        ),
        yaxis=dict(
            title='Depth (dbar)',
            titlefont=dict(size=14, color='white'),
            tickfont=dict(color='white'),
            autorange='reversed',
            gridcolor='rgba(255,255,255,0.1)',
            zerolinecolor='rgba(255,255,255,0.2)'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500,
        legend=dict(
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1
        )
    )
    return fig

def create_measurement_summary_plot(data):
    """Create a comprehensive measurement summary"""
    if not data or 'results' not in data:
        return create_empty_figure("No measurement data available")
    
    profile_data = [r for r in data['results'] if 'warning' not in r]
    if not profile_data:
        return create_empty_figure("No valid measurement data found")
    
    df = pd.DataFrame(profile_data)
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('📊 Measurements by Float', '📅 Measurements Over Time', 
                       '🌍 Geographic Distribution', '📈 Data Quality Overview'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"type": "scattermapbox"}, {"type": "bar"}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # Plot 1: Measurements by Float
    fig.add_trace(
        go.Bar(x=df['float_id'].astype(str), 
               y=df['temperature_count'], 
               name='Temperature',
               marker_color='#60a5fa',
               text=df['temperature_count'],
               textposition='auto'),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=df['float_id'].astype(str), 
               y=df['pressure_count'], 
               name='Pressure',
               marker_color='#34d399',
               text=df['pressure_count'],
               textposition='auto'),
        row=1, col=1
    )
    
    # Plot 2: Time series
    df['date'] = pd.to_datetime(df['date'])
    df_time = df.groupby(df['date'].dt.date).agg({
        'temperature_count': 'sum',
        'pressure_count': 'sum'
    }).reset_index()
    
    fig.add_trace(
        go.Scatter(x=df_time['date'], 
                  y=df_time['temperature_count'],
                  mode='lines+markers',
                  name='Temp/Day',
                  line=dict(color='#60a5fa', width=3),
                  marker=dict(size=8)),
        row=1, col=2
    )
    
    # Plot 3: Geographic distribution
    fig.add_trace(
        go.Scattermapbox(
            lon=df['longitude'],
            lat=df['latitude'],
            mode='markers',
            marker=dict(
                size=df['temperature_count']/10 + 5,
                color=df['temperature_count'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(x=0.45, len=0.4)
            ),
            text=[f"Float {fid}<br>{tc} measurements" for fid, tc in zip(df['float_id'], df['temperature_count'])],
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Plot 4: Data quality overview
    total_floats = len(df)
    floats_with_temp = len(df[df['temperature_count'] > 0])
    floats_with_pressure = len(df[df['pressure_count'] > 0])
    
    fig.add_trace(
        go.Bar(x=['Total Floats', 'With Temperature', 'With Pressure'],
               y=[total_floats, floats_with_temp, floats_with_pressure],
               marker_color=['#94a3b8', '#60a5fa', '#34d399'],
               text=[total_floats, floats_with_temp, floats_with_pressure],
               textposition='auto'),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text="📊 ARGO Data Analysis Dashboard",
        title_x=0.5,
        title_font=dict(size=24, color='white'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        legend=dict(
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1
        )
    )
    
    # Update mapbox
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()),
            zoom=2
        )
    )
    
    return fig

def create_empty_figure(message):
    """Create an empty figure with a message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="rgba(255,255,255,0.6)")
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=400
    )
    return fig

# Export functions
def export_data_as_csv(data):
    if not data or 'results' not in data:
        return None
    
    results = [r for r in data['results'] if 'warning' not in r]
    if not results:
        return None
    
    # Create a clean DataFrame for export
    export_data = []
    for r in results:
        clean_row = {k: v for k, v in r.items() if k not in ['temperature_values', 'pressure_levels']}
        export_data.append(clean_row)
    
    df = pd.DataFrame(export_data)
    return df.to_csv(index=False).encode('utf-8')

def export_data_as_json(data):
    if not data or 'results' not in data:
        return None
    
    results = [r for r in data['results'] if 'warning' not in r]
    if not results:
        return None
    
    return json.dumps(results, indent=2, default=str).encode('utf-8')

# Main application
def main():
    # Check backend status
    backend_online = check_backend_status()
    
    # Sidebar
    with st.sidebar:
        st.markdown("# 🌊 FloatChat")
        st.markdown("*AI-Powered ARGO Data Explorer*")
        
        # Backend status indicator
        status_color = "status-online" if backend_online else "status-offline"
        status_text = "Online" if backend_online else "Offline"
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 16px 0;">
            <span class="status-indicator {status_color}"></span>
            <span style="font-size: 0.875rem; color: rgba(148, 163, 184, 0.8);">
                Backend: {status_text}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # System Overview
        st.markdown("### 📊 System Overview")
        stats_data = get_stats()
        
        is_fallback = stats_data.get('fallback', False)
        fallback_note = " (Demo)" if is_fallback else ""
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stats_data.get('count', 'N/A')}{fallback_note}</div>
            <div class="metric-label">Total Profiles</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{stats_data.get('pressure_count', 'N/A')}</div>
            <div class="metric-label">With Pressure Data</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">Indian Ocean</div>
            <div class="metric-label">Primary Region</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">Real-time</div>
            <div class="metric-label">Data Updates</div>
        </div>
        """, unsafe_allow_html=True)
        
        if is_fallback:
            st.warning("⚠️ Using demo data - backend unavailable")
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("### 🚀 Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.session_state.backend_status = 'checking'
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        
        st.markdown("---")
        
        # Advanced Filters
        with st.expander("⚙️ Advanced Filters", expanded=False):
            date_range = st.date_input(
                "Date Range", 
                [datetime(2025, 1, 1), datetime(2025, 8, 31)],
                key="date_filter"
            )
            region = st.selectbox(
                "Region", 
                ["All", "Indian Ocean", "Arabian Sea", "Bay of Bengal"],
                key="region_filter"
            )
            temp_range = st.slider(
                "Temperature Range (°C)", 
                -5.0, 40.0, (-5.0, 40.0),
                key="temp_filter"
            )
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["💬 Chatbot", "📊 Analytics", "🔧 Tools"])
    
    with tab1:
        # Welcome screen or chat history
        if not st.session_state.chat_history:
            st.markdown("""
            <div class="welcome-container">
                <h1 class="welcome-title">🌊 FloatChat</h1>
                <p class="welcome-subtitle">Explore the world's oceans through AI-powered ARGO float data analysis</p>
                
                <div class="example-prompts">
                    <div class="prompt-card">
                        <strong>🌡️ Temperature Analysis</strong>
                        <p>Show me temperature profiles near the equator with gradients above 2°C per 100m</p>
                    </div>
                    <div class="prompt-card">
                        <strong>🗺️ Regional Search</strong>
                        <p>Find ARGO floats in the Arabian Sea from the last 3 months</p>
                    </div>
                    <div class="prompt-card">
                        <strong>📊 Data Comparison</strong>
                        <p>Compare pressure measurements between different ocean regions</p>
                    </div>
                    <div class="prompt-card">
                        <strong>🔍 Quality Analysis</strong>
                        <p>Show floats with the most complete temperature and pressure data</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Chat history display
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                if message["role"] == "assistant" and "results" in message:
                    results = message["results"]
                    
                    if "error" in results:
                        st.error(f"❌ **Error:** {results['error']}")
                        if not backend_online:
                            st.info("💡 **Tip:** Make sure the backend service is running on `localhost:5000`")
                    
                    elif results.get('count', 0) > 0 and 'results' in results and results['results']:
                        profile_data = [r for r in results['results'] if 'warning' not in r]
                        
                        if profile_data:
                            # Results summary
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("🔢 Profiles Found", len(profile_data))
                            with col2:
                                total_temp = sum(r.get('temperature_count', 0) for r in profile_data)
                                st.metric("🌡️ Temperature Points", f"{total_temp:,}")
                            with col3:
                                total_pressure = sum(r.get('pressure_count', 0) for r in profile_data)
                                st.metric("📊 Pressure Points", f"{total_pressure:,}")
                            with col4:
                                unique_floats = len(set(r['float_id'] for r in profile_data))
                                st.metric("🌊 Unique Floats", unique_floats)
                            
                            st.markdown("---")
                            
                            # Interactive tabs for different visualizations
                            viz_tabs = st.tabs([
                                "📋 Data Table", 
                                "🗺️ Trajectories", 
                                "🌡️ Temperature Profiles", 
                                "📊 Analytics Dashboard",
                                "💾 Export Data"
                            ])
                            
                            with viz_tabs[0]:  # Data Table
                                st.markdown("#### 📋 Profile Data Overview")
                                display_df = pd.DataFrame(profile_data)
                                
                                # Remove complex JSON columns for display
                                display_columns = [col for col in display_df.columns 
                                                 if col not in ['temperature_values', 'pressure_levels']]
                                display_df = display_df[display_columns]
                                
                                # Format the dataframe
                                if 'date' in display_df.columns:
                                    display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d %H:%M')
                                if 'latitude' in display_df.columns:
                                    display_df['latitude'] = display_df['latitude'].round(4)
                                if 'longitude' in display_df.columns:
                                    display_df['longitude'] = display_df['longitude'].round(4)
                                
                                st.dataframe(
                                    display_df, 
                                    use_container_width=True, 
                                    hide_index=True,
                                    column_config={
                                        "float_id": st.column_config.NumberColumn("Float ID", format="%d"),
                                        "latitude": st.column_config.NumberColumn("Latitude", format="%.4f°"),
                                        "longitude": st.column_config.NumberColumn("Longitude", format="%.4f°"),
                                        "temperature_count": st.column_config.NumberColumn("🌡️ Temp Points"),
                                        "pressure_count": st.column_config.NumberColumn("📊 Pressure Points"),
                                    }
                                )
                            
                            with viz_tabs[1]:  # Trajectories
                                st.markdown("#### 🗺️ Float Trajectory Map")
                                trajectory_map = create_float_trajectory_map(results)
                                st.plotly_chart(trajectory_map, use_container_width=True)
                                
                                # Additional trajectory insights
                                if len(profile_data) > 1:
                                    st.markdown("##### 📈 Trajectory Insights")
                                    df = pd.DataFrame(profile_data)
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        lat_range = df['latitude'].max() - df['latitude'].min()
                                        lon_range = df['longitude'].max() - df['longitude'].min()
                                        st.info(f"**Coverage Area:** {lat_range:.2f}° × {lon_range:.2f}°")
                                    
                                    with col2:
                                        if 'date' in df.columns:
                                            df['date'] = pd.to_datetime(df['date'])
                                            time_span = (df['date'].max() - df['date'].min()).days
                                            st.info(f"**Time Span:** {time_span} days")
                            
                            with viz_tabs[2]:  # Temperature Profiles
                                st.markdown("#### 🌡️ Temperature vs Depth Analysis")
                                temp_plot = create_depth_temperature_plot(results)
                                st.plotly_chart(temp_plot, use_container_width=True)
                                
                                # Temperature statistics
                                st.markdown("##### 📊 Temperature Statistics")
                                col1, col2, col3 = st.columns(3)
                                
                                try:
                                    all_temps = []
                                    for row in profile_data[:5]:  # Sample from first 5 floats
                                        temps = json.loads(row.get('temperature_values', '[]'))
                                        for t in temps:
                                            try:
                                                if isinstance(t, dict):
                                                    temp_val = float(t.get('value', 0))
                                                else:
                                                    temp_val = float(t)
                                                if -5 <= temp_val <= 40:
                                                    all_temps.append(temp_val)
                                            except:
                                                continue
                                    
                                    if all_temps:
                                        with col1:
                                            st.metric("🌡️ Avg Temperature", f"{np.mean(all_temps):.2f}°C")
                                        with col2:
                                            st.metric("🔥 Max Temperature", f"{np.max(all_temps):.2f}°C")
                                        with col3:
                                            st.metric("🧊 Min Temperature", f"{np.min(all_temps):.2f}°C")
                                except:
                                    st.warning("Unable to calculate temperature statistics")
                            
                            with viz_tabs[3]:  # Analytics Dashboard
                                st.markdown("#### 📊 Comprehensive Analytics")
                                analytics_plot = create_measurement_summary_plot(results)
                                st.plotly_chart(analytics_plot, use_container_width=True)
                            
                            with viz_tabs[4]:  # Export Data
                                st.markdown("#### 💾 Export Options")
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("##### 📊 Structured Data Export")
                                    csv_data = export_data_as_csv(results)
                                    if csv_data:
                                        st.download_button(
                                            label="📊 Download CSV",
                                            data=csv_data,
                                            file_name=f"argo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                            mime="text/csv",
                                            use_container_width=True
                                        )
                                    
                                    json_data = export_data_as_json(results)
                                    if json_data:
                                        st.download_button(
                                            label="📄 Download JSON",
                                            data=json_data,
                                            file_name=f"argo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                            mime="application/json",
                                            use_container_width=True
                                        )
                                
                                with col2:
                                    st.markdown("##### 📋 Export Summary")
                                    st.info(f"""
                                    **Dataset Summary:**
                                    - 📊 **Profiles:** {len(profile_data)}
                                    - 🌡️ **Temperature Points:** {sum(r.get('temperature_count', 0) for r in profile_data):,}
                                    - 📈 **Pressure Points:** {sum(r.get('pressure_count', 0) for r in profile_data):,}
                                    - 🌊 **Unique Floats:** {len(set(r['float_id'] for r in profile_data))}
                                    """)
        
        # Chat input
        if prompt := st.chat_input("Ask about ARGO data..." if backend_online else "Backend offline - demo mode"):
            if not backend_online:
                st.warning("⚠️ Backend is offline. Please start the Flask backend service.")
                return
            
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Process query and add response
            with st.spinner("🤔 Processing your query..."):
                response = query_backend(prompt)
                
                assistant_message = {
                    "role": "assistant",
                    "results": response
                }
                
                if "error" in response:
                    assistant_message["content"] = f"I encountered an issue: {response['error']}"
                else:
                    count = response.get('count', 0)
                    if count > 0:
                        assistant_message["content"] = f"✅ Found **{count} ARGO profiles** matching your query! Here's what I discovered:"
                    else:
                        assistant_message["content"] = "🔍 I searched through the ARGO database but couldn't find any profiles matching your specific criteria. Try:\n\n• Broadening your search terms\n• Using different time ranges\n• Checking spelling of location names"
                
                st.session_state.chat_history.append(assistant_message)
            
            st.rerun()
    
    with tab2:  # Analytics Dashboard
        st.markdown("# 📊 ARGO Analytics Dashboard")
        
        if not backend_online:
            st.error("⚠️ Analytics dashboard requires backend connection")
            return
        
        # Dashboard controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dashboard_region = st.selectbox(
                "🌍 Region", 
                ["Indian Ocean", "Arabian Sea", "Bay of Bengal", "All Regions"],
                key="dash_region"
            )
        
        with col2:
            dashboard_timeframe = st.selectbox(
                "📅 Timeframe",
                ["Last 30 days", "Last 3 months", "Last 6 months", "Last year"],
                index=1,
                key="dash_time"
            )
        
        with col3:
            if st.button("🔄 Refresh Dashboard", use_container_width=True):
                st.rerun()
        
        # Generate dashboard query
        timeframe_map = {
            "Last 30 days": "last 30 days",
            "Last 3 months": "last 3 months", 
            "Last 6 months": "last 6 months",
            "Last year": "last year"
        }
        
        dashboard_query = f"Show all ARGO profiles in {dashboard_region} from {timeframe_map[dashboard_timeframe]} with temperature and pressure data"
        
        # Load dashboard data
        with st.spinner("📊 Loading dashboard data..."):
            dashboard_response = query_backend(dashboard_query)
        
        if "error" in dashboard_response:
            st.error(f"❌ Dashboard Error: {dashboard_response['error']}")
        elif dashboard_response.get('count', 0) > 0:
            # Dashboard metrics
            profile_data = [r for r in dashboard_response['results'] if 'warning' not in r]
            
            if profile_data:
                # Key metrics row
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("🔢 Total Profiles", len(profile_data))
                with col2:
                    unique_floats = len(set(r['float_id'] for r in profile_data))
                    st.metric("🌊 Active Floats", unique_floats)
                with col3:
                    total_temp = sum(r.get('temperature_count', 0) for r in profile_data)
                    st.metric("🌡️ Temperature Points", f"{total_temp:,}")
                with col4:
                    total_pressure = sum(r.get('pressure_count', 0) for r in profile_data)
                    st.metric("📊 Pressure Points", f"{total_pressure:,}")
                with col5:
                    if profile_data:
                        df = pd.DataFrame(profile_data)
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                            latest_date = df['date'].max().strftime('%Y-%m-%d')
                            st.metric("📅 Latest Data", latest_date)
                
                st.markdown("---")
                
                # Main dashboard visualization
                dashboard_viz = create_measurement_summary_plot(dashboard_response)
                st.plotly_chart(dashboard_viz, use_container_width=True)
                
                # Additional dashboard sections
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🗺️ Regional Coverage")
                    trajectory_map = create_float_trajectory_map(dashboard_response)
                    st.plotly_chart(trajectory_map, use_container_width=True)
                
                with col2:
                    st.markdown("#### 🌡️ Temperature Analysis")
                    temp_profiles = create_depth_temperature_plot(dashboard_response)
                    st.plotly_chart(temp_profiles, use_container_width=True)
        else:
            st.warning("📭 No data available for the selected dashboard filters")
    
    with tab3:  # Tools
        st.markdown("# 🔧 System Tools")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔍 System Diagnostics")
            
            if st.button("🔄 Test Backend Connection", use_container_width=True):
                with st.spinner("Testing connection..."):
                    test_result = check_backend_status()
                    if test_result:
                        st.success("✅ Backend connection successful")
                        # Test a simple query
                        test_query = query_backend("show 5 recent profiles")
                        if "error" not in test_query:
                            st.success("✅ Query processing works")
                        else:
                            st.error(f"❌ Query failed: {test_query['error']}")
                    else:
                        st.error("❌ Cannot connect to backend")
                        st.info("💡 Make sure Flask backend is running on localhost:5000")
            
            if st.button("📊 Get System Stats", use_container_width=True):
                with st.spinner("Fetching stats..."):
                    stats = get_stats()
                    if not stats.get('fallback'):
                        st.json(stats)
                    else:
                        st.warning("Using fallback stats - backend unavailable")
        
        with col2:
            st.markdown("### ⚙️ Configuration")
            
            st.info(f"""
            **Current Settings:**
            - 🌐 Backend URL: `{BACKEND_URL}`
            - 🔄 Connection Status: {'🟢 Online' if backend_online else '🔴 Offline'}
            - 💬 Chat History: {len(st.session_state.chat_history)} messages
            """)
            
            st.markdown("### 📚 Quick Help")
            
            with st.expander("🤖 How to use FloatChat"):
                st.markdown("""
                **Natural Language Queries:**
                - "Show temperature profiles near the equator"
                - "Find floats in Arabian Sea from last month"
                - "Compare pressure data between regions"
                
                **Supported Parameters:**
                - 🌡️ Temperature measurements
                - 📊 Pressure/depth data
                - 📍 Geographic coordinates
                - 📅 Date ranges
                """)
            
            with st.expander("🔧 Troubleshooting"):
                st.markdown("""
                **Common Issues:**
                
                1. **Backend Offline:**
                   - Ensure Flask app is running: `python app.py`
                   - Check port 5000 is available
                
                2. **No Results Found:**
                   - Try broader search terms
                   - Check date ranges
                   - Verify region names
                
                3. **Slow Responses:**
                   - Backend may be processing large queries
                   - Try more specific searches
                """)

if __name__ == "__main__":
    main()