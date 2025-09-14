import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import io
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="FloatChat - ARGO Data Explorer",
    page_icon="🐙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for improved UI/UX
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global styling */
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0c1445 0%, #1e3a8a 50%, #3b82f6 100%);
        color: white;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* Main chat container */
    .main-chat-container {
        padding-bottom: 100px; /* Space for the fixed input bar */
        border-top-right-radius: 20px;
    }

    /* Chat message styling */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 1rem 1.25rem;
        margin: 10px 0;
        width: fit-content;
        max-width: 80%;
    }

    [data-testid="stChatMessage"] p {
        color: white !important;
    }
    
    /* Move user messages to the right */
    div[data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-user"]) {
        margin-left: auto;
        background: rgba(59, 130, 246, 0.25);
    }
    
    /* Assistant message styling */
    div[data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-assistant"]) {
        margin-right: auto;
    }

    /* Glassmorphism containers for results */
    .glass-container {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }

    /* Custom button styling */
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        width: 100%;
    }

    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
        color: white !important;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(12, 20, 69, 0.5); /* Darker sidebar */
        backdrop-filter: blur(20px);
    }
    
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
        color: white;
    }

    /* Metric card styling in sidebar */
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #60a5fa;
    }
    .metric-label {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.8);
        margin-top: 5px;
    }

    /* Welcome screen styling */
    .welcome-container {
        text-align: center;
        padding: 4rem 1rem;
    }
    .welcome-container h1 {
        font-size: 3rem;
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #60a5fa, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .example-prompts {
        display: flex;
        justify-content: center;
        gap: 15px;
        flex-wrap: wrap;
        margin-top: 2rem;
    }
    .prompt-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1rem;
        border-radius: 15px;
        width: 200px;
        font-size: 0.9rem;
        text-align: left;
    }
    .prompt-card strong {
        color: #a5caff;
    }

</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Backend API configuration
BACKEND_URL = "http://localhost:5000"

# Helper functions
def query_backend(user_query):
    """Send query to Flask backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/ask",
            json={"query": user_query},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Backend error: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

def get_stats():
    """Get statistics from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Backend error: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

# Visualization functions
def create_float_trajectory_map(data, key_suffix=""):
    """Create a trajectory map using Plotly"""
    if not data or 'results' not in data:
        return go.Figure()
    
    profile_data = [r for r in data['results'] if 'warning' not in r]
    if not profile_data:
        return go.Figure()
    
    df = pd.DataFrame(profile_data)
    
    fig = go.Figure()
    
    # Group by float_id and create trajectories
    for float_id in df['float_id'].unique():
        float_data = df[df['float_id'] == float_id].copy()
        float_data['date'] = pd.to_datetime(float_data['date'])
        float_data = float_data.sort_values('date')
        
        fig.add_trace(go.Scattermapbox(
            lon=float_data['longitude'],
            lat=float_data['latitude'],
            mode='markers+lines',
            name=f'Float {float_id}',
            marker=dict(size=8),
            line=dict(width=2),
            text=[f"Float {float_id}<br>Date: {date}<br>Lat: {lat:.3f}<br>Lon: {lon:.3f}<br>Temp points: {temp_count}<br>Pressure points: {pres_count}" 
                  for date, lat, lon, temp_count, pres_count in zip(
                      float_data['date'], float_data['latitude'], float_data['longitude'],
                      float_data['temperature_count'], float_data['pressure_count'])],
            hovertemplate='%{text}<extra></extra>'
        ))
    
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()),
            zoom=3
        ),
        title='Float Trajectories',
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=0, r=0, t=40, b=0)
    )
    return fig

def create_depth_temperature_plot(data, key_suffix=""):
    """Create depth vs temperature profile plot"""
    if not data or 'results' not in data:
        return go.Figure()
    
    profile_data = [r for r in data['results'] if 'warning' not in r]
    if not profile_data:
        return go.Figure()
    
    fig = go.Figure()
    
    for idx, row in enumerate(profile_data[:5]):  # Limit to first 5 floats
        try:
            # Handle the case where temperature_values and pressure_levels might be missing
            if 'temperature_values' not in row or 'pressure_levels' not in row:
                continue
                
            temps = json.loads(row['temperature_values']) if row['temperature_values'] else []
            pressures = json.loads(row['pressure_levels']) if row['pressure_levels'] else []
            
            if temps and pressures:
                # Parse temperature and pressure values
                temp_vals = [float(t.get('value', 0)) if isinstance(t, dict) else float(t) for t in temps]
                pres_vals = [float(p.get('value', 0)) if isinstance(p, dict) else float(p) for p in pressures]
                
                # Take minimum length to avoid index errors
                min_len = min(len(temp_vals), len(pres_vals))
                if min_len > 0:
                    fig.add_trace(go.Scatter(
                        x=temp_vals[:min_len],
                        y=pres_vals[:min_len],
                        mode='lines+markers',
                        name=f"Float {row['float_id']}",
                        line=dict(width=2),
                        marker=dict(size=6),
                        text=[f"Depth: {p:.1f} dbar<br>Temp: {t:.2f}°C" for t, p in zip(temp_vals[:min_len], pres_vals[:min_len])],
                        hovertemplate='%{text}<extra></extra>'
                    ))
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            continue
    
    fig.update_layout(
        title='Depth vs Temperature Profiles',
        xaxis_title='Temperature (°C)',
        yaxis_title='Depth (dbar)',
        yaxis=dict(autorange='reversed'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500
    )
    return fig

def create_depth_pressure_plot(data, key_suffix=""):
    """Create depth vs pressure profile plot (redundant but kept for consistency)"""
    if not data or 'results' not in data:
        return go.Figure()
    
    profile_data = [r for r in data['results'] if 'warning' not in r]
    if not profile_data:
        return go.Figure()
    
    fig = go.Figure()
    
    # Create a simple pressure distribution plot instead
    pressure_counts = [row.get('pressure_count', 0) for row in profile_data]
    float_ids = [str(row['float_id']) for row in profile_data]
    
    fig.add_trace(go.Bar(
        x=float_ids,
        y=pressure_counts,
        marker_color='#10b981',
        text=pressure_counts,
        textposition='auto',
    ))
    
    fig.update_layout(
        title='Pressure Measurements per Float',
        xaxis_title='Float ID',
        yaxis_title='Number of Pressure Measurements',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500
    )
    return fig

def create_time_series_plot(data, key_suffix=""):
    """Create time series plot"""
    if not data or 'results' not in data:
        return go.Figure()
    
    profile_data = [r for r in data['results'] if 'warning' not in r]
    if not profile_data:
        return go.Figure()
    
    df = pd.DataFrame(profile_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['temperature_count'],
        mode='lines+markers',
        name='Temperature Measurements',
        marker=dict(size=8, color='#60a5fa'),
        line=dict(width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['pressure_count'],
        mode='lines+markers',
        name='Pressure Measurements',
        marker=dict(size=8, color='#10b981'),
        line=dict(width=2)
    ))
    
    fig.update_layout(
        title='Measurements Over Time',
        xaxis_title='Date',
        yaxis_title='Number of Measurements',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500
    )
    return fig

def create_comparison_plot(data, key_suffix=""):
    """Create enhanced comparison plot of measurements by float"""
    if not data or 'results' not in data:
        return go.Figure()
    
    profile_data = [r for r in data['results'] if 'warning' not in r]
    if not profile_data:
        return go.Figure()
    
    df = pd.DataFrame(profile_data)
    
    fig = go.Figure()
    
    # Enhanced temperature bars
    fig.add_trace(go.Bar(
        x=df['float_id'].astype(str),
        y=df['temperature_count'],
        name='Temperature Measurements',
        marker=dict(
            color='rgba(0, 212, 170, 0.8)',
            line=dict(color='rgba(0, 212, 170, 1)', width=2),
            pattern=dict(shape="", size=8)
        ),
        text=df['temperature_count'],
        textposition='outside',
        textfont=dict(color='white', size=11),
        hovertemplate='<b>Float %{x}</b><br>Temperature: %{y} measurements<extra></extra>',
        offsetgroup=1
    ))
    
    # Enhanced pressure bars
    fig.add_trace(go.Bar(
        x=df['float_id'].astype(str),
        y=df['pressure_count'],
        name='Pressure Measurements',
        marker=dict(
            color='rgba(255, 107, 107, 0.8)',
            line=dict(color='rgba(255, 107, 107, 1)', width=2),
            pattern=dict(shape="x", size=8)
        ),
        text=df['pressure_count'],
        textposition='outside',
        textfont=dict(color='white', size=11),
        hovertemplate='<b>Float %{x}</b><br>Pressure: %{y} measurements<extra></extra>',
        offsetgroup=2
    ))
    
    # Add summary statistics
    avg_temp = df['temperature_count'].mean()
    avg_press = df['pressure_count'].mean()
    
    # Add average lines
    fig.add_hline(
        y=avg_temp, 
        line_dash="dash", 
        line_color="#00D4AA",
        annotation_text=f"Avg Temperature: {avg_temp:.1f}",
        annotation_position="top left",
        annotation_font_color="white"
    )
    
    fig.add_hline(
        y=avg_press, 
        line_dash="dash", 
        line_color="#FF6B6B",
        annotation_text=f"Avg Pressure: {avg_press:.1f}",
        annotation_position="bottom left",
        annotation_font_color="white"
    )
    
    fig.update_layout(
        title=dict(
            text='Measurement Comparison by Float',
            font=dict(size=20, color='white'),
            x=0.5
        ),
        xaxis_title='Float ID',
        yaxis_title='Number of Measurements',
        barmode='group',
        bargap=0.15,
        bargroupgap=0.1,
        plot_bgcolor='rgba(0,0,0,0.1)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=12),
        height=500,
        showlegend=True,
        legend=dict(
            bgcolor='rgba(255,255,255,0.1)',
            bordercolor='rgba(255,255,255,0.3)',
            borderwidth=1,
            font=dict(color='white'),
            orientation='h',
            x=0.5,
            y=1.02,
            xanchor='center'
        ),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.2)',
            zerolinecolor='rgba(255,255,255,0.3)',
            tickfont=dict(color='white'),
            showgrid=True
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.2)',
            zerolinecolor='rgba(255,255,255,0.3)',
            tickfont=dict(color='white'),
            showgrid=True
        )
    )
    return fig

# Export functions
def export_data_as_csv(data):
    if not data or 'results' not in data:
        return None

    results = [r for r in data['results'] if 'warning' not in r]
    if not results:
        return None
    df = pd.DataFrame(results)
    # Remove JSON columns if they exist
    for col in ['temperature_values', 'pressure_levels']:
        if col in df.columns:
            df = df.drop(col, axis=1)
    return df.to_csv(index=False).encode('utf-8')

def export_data_as_ascii(data):
    if not data or 'results' not in data:
        return None
    results = [r for r in data['results'] if 'warning' not in r]
    if not results:
        return None
    output = io.StringIO()
    output.write("Float ID,Date,Latitude,Longitude,Temperature Count,Pressure Count\n")
    for r in results:
        output.write(f"{r['float_id']},{r['date']},{r['latitude']},{r['longitude']},"
                     f"{r.get('temperature_count', 0)},{r.get('pressure_count', 0)}\n")
    return output.getvalue().encode('utf-8')

# Main function
def main():
    with st.sidebar:
        st.markdown("# 🐙 FloatChat")
        st.markdown("AI-Powered ARGO Data Explorer")
        st.markdown("---")

        st.markdown("### 📊 System Overview")
        stats_data = get_stats()
        if "error" not in stats_data:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats_data.get('count', 'N/A')}</div>
                <div class="metric-label">Total Profiles</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats_data.get('pressure_count', 'N/A')}</div>
                <div class="metric-label">With Pressure</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">Indian Ocean</div>
                <div class="metric-label">Primary Region</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">6 Months</div>
                <div class="metric-label">Data Range</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Could not load system stats.")

        st.markdown("### 🔍 Dashboard Filters")
        date_range = st.date_input("Date Range", [datetime(2025, 1, 1), datetime(2025, 8, 31)])
        region = st.selectbox("Region", ["All", "Indian Ocean", "Arabian Sea", "Bay of Bengal"])
        parameters = st.multiselect("Parameters", ["Temperature", "Pressure"], default=["Temperature", "Pressure"])

        st.markdown("---")
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    tab1, tab2 = st.tabs(["💬 Chatbot", "📊 Dashboard"])

    with tab1:
        st.markdown('<div class="main-chat-container">', unsafe_allow_html=True)

        if not st.session_state.chat_history:
            st.markdown("""
            <div class="welcome-container">
                <h1>🐙 FloatChat</h1>
                <p>Your conversational gateway to ARGO ocean data. Start by asking a question below.</p>
                <div class="example-prompts">
                    <div class="prompt-card"><strong>Find data</strong><p>Show temperature profiles near the equator.</p></div>
                    <div class="prompt-card"><strong>Compare</strong><p>Compare pressure in the Arabian Sea last month.</p></div>
                    <div class="prompt-card"><strong>Analyze</strong><p>Find floats with high temperature gradients.</p></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        for idx, message in enumerate(st.session_state.chat_history):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and "results" in message:
                    results = message["results"]
                    if "error" in results:
                        st.error(f"❌ Error: {results['error']}")
                    elif results.get('count', 0) > 0 and 'results' in results and results['results']:
                        st.markdown("---")
                        profile_data = [r for r in results['results'] if 'warning' not in r]
                        if profile_data:
                            tab_data, tab_temp, tab_press, tab_time, tab_map, tab_comp = st.tabs(["Data Table", "🌡️ Temperature", "📊 Pressure", "⏳ Time", "🗺️ Map", "📈 Compare"])
                            with tab_data:
                                display_df = pd.DataFrame(profile_data)
                                # Remove the JSON columns for display
                                for col in ['temperature_values', 'pressure_levels']:
                                    if col in display_df.columns:
                                        display_df = display_df.drop(col, axis=1)
                                st.dataframe(display_df, use_container_width=True, hide_index=True)
                                col1, col2 = st.columns(2)
                                with col1:
                                    csv_data = export_data_as_csv(results)
                                    if csv_data:
                                        st.download_button(label="📊 Download as CSV", data=csv_data, file_name=f"argo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", key=f"csv_chat_{idx}")
                                with col2:
                                    ascii_data = export_data_as_ascii(results)
                                    if ascii_data:
                                        st.download_button(label="📝 Download as ASCII", data=ascii_data, file_name=f"argo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain", key=f"ascii_chat_{idx}")
                            with tab_temp:
                                st.plotly_chart(create_depth_temperature_plot(results, f"chat_temp_{idx}"), use_container_width=True, key=f"temp_chart_chat_{idx}")
                            with tab_press:
                                st.plotly_chart(create_depth_pressure_plot(results, f"chat_press_{idx}"), use_container_width=True, key=f"press_chart_chat_{idx}")
                            with tab_time:
                                st.plotly_chart(create_time_series_plot(results, f"chat_time_{idx}"), use_container_width=True, key=f"time_chart_chat_{idx}")
                            with tab_map:
                                st.plotly_chart(create_float_trajectory_map(results, f"chat_map_{idx}"), use_container_width=True, key=f"map_chart_chat_{idx}")
                            with tab_comp:
                                st.plotly_chart(create_comparison_plot(results, f"chat_comp_{idx}"), use_container_width=True, key=f"comp_chart_chat_{idx}")

        st.markdown('</div>', unsafe_allow_html=True)

        if prompt := st.chat_input("Ask about ARGO data..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.spinner("🤔 Thinking..."):
                response = query_backend(prompt)
                assistant_message = {
                    "role": "assistant",
                    "results": response
                }
                if "error" in response:
                    assistant_message["content"] = f"Sorry, I encountered an error: {response['error']}"
                else:
                    count = response.get('count', 0)
                    assistant_message["content"] = f"✅ I found {count} ARGO profiles matching your query. Here are the results:" if count > 0 else "🤷‍♂️ I couldn't find any ARGO profiles matching your query. Please try rephrasing it."
                st.session_state.chat_history.append(assistant_message)
            st.rerun()

    with tab2:
        st.markdown("### 📊 ARGO Data Dashboard")
        filter_query = f"Show profiles in {region} from {date_range[0]} to {date_range[1]} with {', '.join(parameters)}"
        with st.spinner("Loading dashboard data..."):
            response = query_backend(filter_query)
        
        if "error" in response:
            st.error(f"❌ Error: {response['error']}")
        elif response.get('count', 0) > 0 and 'results' in response and response['results']:
            profile_data = [r for r in response['results'] if 'warning' not in r]
            if profile_data:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 🌍 Float Trajectories")
                    st.plotly_chart(create_float_trajectory_map(response, "dashboard_map"), use_container_width=True, key="dashboard_map_chart")
                with col2:
                    st.markdown("#### 📈 Measurement Counts")
                    st.plotly_chart(create_comparison_plot(response, "dashboard_comp"), use_container_width=True, key="dashboard_comp_chart")
                
                st.markdown("#### 📉 Depth Profiles")
                tab_temp, tab_press, tab_time = st.tabs(["🌡️ Temperature", "📊 Pressure", "⏳ Time"])
                with tab_temp:
                    st.plotly_chart(create_depth_temperature_plot(response, "dashboard_temp"), use_container_width=True, key="dashboard_temp_chart")
                with tab_press:
                    st.plotly_chart(create_depth_pressure_plot(response, "dashboard_press"), use_container_width=True, key="dashboard_press_chart")
                with tab_time:
                    st.plotly_chart(create_time_series_plot(response, "dashboard_time"), use_container_width=True, key="dashboard_time_chart")
                
                st.markdown("#### 📋 Data Table")
                display_df = pd.DataFrame(profile_data)
                # Remove the JSON columns for display
                for col in ['temperature_values', 'pressure_levels']:
                    if col in display_df.columns:
                        display_df = display_df.drop(col, axis=1)
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                col1, col2 = st.columns(2)
                with col1:
                    csv_data = export_data_as_csv(response)
                    if csv_data:
                        st.download_button(label="📊 Download as CSV", data=csv_data, file_name=f"argo_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", key="dashboard_csv")
                with col2:
                    ascii_data = export_data_as_ascii(response)
                    if ascii_data:
                        st.download_button(label="📝 Download as ASCII", data=ascii_data, file_name=f"argo_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain", key="dashboard_ascii")
        else:
            st.warning("No data available for the selected filters. Try adjusting the parameters.")

if __name__ == "__main__":
    main()