import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import io
import base64
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="FloatChat - ARGO Data Explorer",
    page_icon="🐙",
    layout="wide",
    initial_sidebar_state="expanded"  # Keep sidebar expanded by default
)

# Custom CSS for the new chatbot UI
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

# -------------------------------------------------------------------
# --- BACKEND AND PLOTTING FUNCTIONS (UNCHANGED) ---
# -------------------------------------------------------------------

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

def create_depth_temperature_plot(data):
    """Create depth vs temperature visualization"""
    if not data or 'results' not in data:
        return go.Figure()

    fig = go.Figure()

    # Placeholder for actual depth-temperature data
    fig.add_trace(go.Scatter(
        x=[15, 20, 25, 22, 18, 16, 14],
        y=[0, 50, 100, 200, 500, 1000, 2000],
        mode='lines+markers',
        name='Temperature Profile',
        line=dict(color='#60a5fa', width=3),
        marker=dict(size=8, color='#3b82f6')
    ))

    fig.update_layout(
        title='Depth vs Temperature Profile',
        xaxis_title='Temperature (°C)',
        yaxis_title='Depth (m)',
        yaxis=dict(autorange='reversed'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500
    )
    return fig

def create_depth_salinity_plot(data):
    """Create depth vs salinity visualization"""
    if not data or 'results' not in data:
        return go.Figure()
    
    fig = go.Figure()
    
    # Placeholder for actual depth-salinity data
    fig.add_trace(go.Scatter(
        x=[34.5, 34.7, 34.9, 35.1, 35.0, 34.8, 34.6],
        y=[0, 50, 100, 200, 500, 1000, 2000],
        mode='lines+markers',
        name='Salinity Profile',
        line=dict(color='#10b981', width=3),
        marker=dict(size=8, color='#059669')
    ))
    
    fig.update_layout(
        title='Depth vs Salinity Profile',
        xaxis_title='Salinity (PSU)',
        yaxis_title='Depth (m)',
        yaxis=dict(autorange='reversed'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500
    )
    return fig

def create_float_trajectory_map(data):
    """Create float trajectory map"""
    if not data or 'results' not in data:
        return go.Figure()

    results = data['results']
    if not results or isinstance(results[0], dict) and 'warning' in results[0]:
        return go.Figure()

    lats = [r.get('latitude', 0) for r in results if 'latitude' in r]
    lons = [r.get('longitude', 0) for r in results if 'longitude' in r]
    float_ids = [r.get('float_id', 'Unknown') for r in results if 'float_id' in r]

    if not lats or not lons:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode='markers',
        marker=dict(size=10, color='#3b82f6'),
        text=[f"Float ID: {fid}" for fid in float_ids],
        name='ARGO Floats'
    ))

    fig.update_layout(
        mapbox=dict(
            style='carto-darkmatter',
            center=dict(lat=sum(lats)/len(lats), lon=sum(lons)/len(lons)),
            zoom=3
        ),
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    return fig

def create_comparison_plot(data):
    """Create float comparison visualization"""
    if not data or 'results' not in data:
        return go.Figure()

    results = data['results']
    if not results or isinstance(results[0], dict) and 'warning' in results[0]:
        return go.Figure()

    float_ids = [str(r.get('float_id', 'Unknown')) for r in results[:10]] # Limit to 10 floats
    temp_counts = [r.get('temperature_count', 0) for r in results[:10]]
    sal_counts = [r.get('salinity_count', 0) for r in results[:10]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Temperature Measurements',
        x=float_ids,
        y=temp_counts,
        marker_color='#60a5fa'
    ))
    fig.add_trace(go.Bar(
        name='Salinity Measurements',
        x=float_ids,
        y=sal_counts,
        marker_color='#10b981'
    ))
    
    fig.update_layout(
        title='Measurement Counts by Float',
        xaxis_title='Float ID',
        yaxis_title='Number of Measurements',
        barmode='group',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500
    )
    return fig

def export_data_as_csv(data):
    """Convert data to CSV for download"""
    if not data or 'results' not in data:
        return None

    results = data['results']
    if not results or isinstance(results[0], dict) and 'warning' in results[0]:
        return None
    
    df = pd.DataFrame(results)
    return df.to_csv(index=False).encode('utf-8')

# -------------------------------------------------------------------
# --- UI AND APPLICATION LOGIC ---
# -------------------------------------------------------------------

def main():
    # --- Sidebar ---
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
                <div class="metric-value">{stats_data.get('salinity_count', 'N/A')}</div>
                <div class="metric-label">With Salinity</div>
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

        st.markdown("---")
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    # --- Main Chat Interface ---
    st.markdown('<div class="main-chat-container">', unsafe_allow_html=True)

    # Welcome screen for new chat
    if not st.session_state.chat_history:
        st.markdown("""
        <div class="welcome-container">
            <h1>🐙 FloatChat</h1>
            <p>Your conversational gateway to ARGO ocean data. Start by asking a question below.</p>
            <div class="example-prompts">
                <div class="prompt-card"><strong>Find data</strong><p>Show temperature profiles near the equator.</p></div>
                <div class="prompt-card"><strong>Compare</strong><p>Compare salinity in the Arabian Sea last month.</p></div>
                <div class="prompt-card"><strong>Analyze</strong><p>Find floats with high temperature gradients.</p></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # If the message is from the assistant and has results, display them
            if message["role"] == "assistant" and "results" in message:
                results = message["results"]
                if "error" in results:
                    st.error(f"❌ Error: {results['error']}")
                elif results.get('count', 0) > 0 and 'results' in results and results['results']:
                    st.markdown("---")
                    
                    profile_data = [r for r in results['results'] if 'warning' not in r]
                    if profile_data:
                        # Visualizations in tabs
                        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Data Table", "🌡️ Temp", "🧂 Salinity", "🗺️ Map", "📊 Compare"])
                        
                        with tab1:
                            st.dataframe(pd.DataFrame(profile_data), use_container_width=True, hide_index=True)
                            
                            # Export buttons
                            csv_data = export_data_as_csv(results)
                            if csv_data:
                                st.download_button(
                                    label="📊 Download as CSV",
                                    data=csv_data,
                                    file_name=f"argo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                        
                        with tab2:
                            st.plotly_chart(create_depth_temperature_plot(results), use_container_width=True)
                        with tab3:
                            st.plotly_chart(create_depth_salinity_plot(results), use_container_width=True)
                        with tab4:
                             st.plotly_chart(create_float_trajectory_map(results), use_container_width=True)
                        with tab5:
                            st.plotly_chart(create_comparison_plot(results), use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # --- Chat Input (Fixed at the bottom) ---
    if prompt := st.chat_input("Ask about ARGO data..."):
        # Add user message to history and display it
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Process the query and get the assistant's response
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
        
        # Rerun to display the new messages
        st.rerun()

if __name__ == "__main__":
    main()