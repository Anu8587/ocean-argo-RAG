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
    page_title="🐙 FloatChat - ARGO Data Explorer",
    page_icon="🐙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for glassmorphism and modern styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling */
    .stApp {
        background: linear-gradient(135deg, #0c1445 0%, #1e3a8a 50%, #3b82f6 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Chat message styling */
    .chat-message {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 15px;
        margin: 10px 0;
        animation: messageSlideIn 0.3s ease-out;
    }
    
    @keyframes messageSlideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .user-message {
        background: rgba(59, 130, 246, 0.2);
        margin-left: 20px;
    }
    
    .assistant-message {
        background: rgba(16, 185, 129, 0.2);
        margin-right: 20px;
    }
    
    /* Glassmorphism containers */
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
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
    }
    
    /* Table styling */
    .dataframe {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        overflow: hidden;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px;
        color: white;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(59, 130, 246, 0.3);
    }
    
    /* Text color */
    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p {
        color: white !important;
    }
    
    /* Metric styling */
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 20px;
        text-align: center;
        margin: 10px 0;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #60a5fa;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.8);
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_results' not in st.session_state:
    st.session_state.current_results = None

# Backend API configuration
BACKEND_URL = "http://localhost:5000"

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
    # In real implementation, you'd process the temperature_values and pressure_levels
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
    
    # Extract coordinates from results
    results = data['results']
    if not results or isinstance(results[0], dict) and 'warning' in results[0]:
        return go.Figure()
    
    lats = [r.get('latitude', 0) for r in results if 'latitude' in r]
    lons = [r.get('longitude', 0) for r in results if 'longitude' in r]
    float_ids = [r.get('float_id', 'Unknown') for r in results if 'float_id' in r]
    
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
            style='open-street-map',
            center=dict(lat=sum(lats)/len(lats) if lats else 0, 
                       lon=sum(lons)/len(lons) if lons else 0),
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
    
    float_ids = [str(r.get('float_id', 'Unknown')) for r in results[:10]]  # Limit to 10 floats
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
    return df.to_csv(index=False)

def export_data_as_netcdf(data):
    """Placeholder for NetCDF export"""
    # This would require xarray and actual NetCDF data structure
    # For now, return a placeholder message
    return "NetCDF export functionality coming soon!"

# Main application layout
def main():
    # Sidebar
    with st.sidebar:
        st.markdown("# 🐙 FloatChat")
        
        # Argo Map button (placeholder)
        if st.button("🗺️ Argo Map", help="View global ARGO float map"):
            st.info("Interactive map feature coming soon!")
        
        st.markdown("---")
        
        # Chat input
        st.markdown("### Ask about ARGO data:")
        user_input = st.text_area(
            "Enter your query...",
            placeholder="e.g., Show me temperature profiles in the Indian Ocean from last month",
            height=100,
            key="chat_input"
        )
        
        query_btn = st.button("🔍 Query", use_container_width=True)
        
        if query_btn and user_input.strip():
            # Add user message to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            
            # Query backend
            with st.spinner("🤔 Processing your query..."):
                response = query_backend(user_input)
            
            # Add assistant response to chat history
            if "error" in response:
                assistant_msg = f"❌ Error: {response['error']}"
            else:
                count = response.get('count', 0)
                assistant_msg = f"✅ Found {count} ARGO profiles matching your query."
                st.session_state.current_results = response
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": assistant_msg,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            
            st.experimental_rerun()
        
        st.markdown("---")
        
        # Chat history
        st.markdown("### Chat History")
        chat_container = st.container()
        
        with chat_container:
            for i, message in enumerate(reversed(st.session_state.chat_history[-10:])):  # Show last 10 messages
                role_emoji = "🧑" if message["role"] == "user" else "🤖"
                role_class = "user-message" if message["role"] == "user" else "assistant-message"
                
                st.markdown(f"""
                <div class="chat-message {role_class}">
                    <strong>{role_emoji} {message["role"].title()}</strong> <small>({message["timestamp"]})</small><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", help="Clear chat history"):
            st.session_state.chat_history = []
            st.session_state.current_results = None
            st.experimental_rerun()
    
    # Main content area
    st.markdown("# 🌊 ARGO Float Data Explorer")
    
    # Show statistics on load
    if not st.session_state.current_results:
        st.markdown("## 📊 System Overview")
        
        # Get stats from backend
        stats_data = get_stats()
        
        if "error" not in stats_data:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{stats_data.get('count', 0)}</div>
                    <div class="metric-label">Total Profiles</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{stats_data.get('salinity_count', 0)}</div>
                    <div class="metric-label">With Salinity</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">Indian Ocean</div>
                    <div class="metric-label">Primary Region</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">6 Months</div>
                    <div class="metric-label">Data Range</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Welcome message
        st.markdown("""
        <div class="glass-container">
            <h3>🚀 Getting Started</h3>
            <p>Welcome to FloatChat! Use natural language to explore ARGO float data:</p>
            <ul>
                <li><strong>"Show me temperature profiles near the equator"</strong></li>
                <li><strong>"Compare salinity in the Arabian Sea last month"</strong></li>
                <li><strong>"Find floats with high temperature gradients"</strong></li>
                <li><strong>"What are the latest measurements from float 12345?"</strong></li>
            </ul>
            <p>Start by typing your question in the sidebar! 👈</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show results if available
    if st.session_state.current_results:
        results = st.session_state.current_results
        
        st.markdown("## 🔍 Query Results")
        
        # Results summary
        count = results.get('count', 0)
        query = results.get('query', 'Your query')
        
        st.markdown(f"""
        <div class="glass-container">
            <h4>📋 Query Summary</h4>
            <p><strong>Query:</strong> {query}</p>
            <p><strong>Results:</strong> {count} ARGO profiles found</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Data table
        if 'results' in results and results['results']:
            result_data = results['results']
            
            # Filter out warning messages
            profile_data = [r for r in result_data if 'warning' not in r]
            warnings = [r['warning'] for r in result_data if 'warning' in r]
            
            if profile_data:
                st.markdown("### 📊 Profile Data")
                
                # Convert to DataFrame
                df = pd.DataFrame(profile_data)
                
                # Display table with glassmorphism styling
                st.markdown('<div class="glass-container">', unsafe_allow_html=True)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Export buttons
                st.markdown("### 💾 Export Data")
                col1, col2 = st.columns(2)
                
                with col1:
                    csv_data = export_data_as_csv(results)
                    if csv_data:
                        st.download_button(
                            label="📊 Download CSV",
                            data=csv_data,
                            file_name=f"argo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                
                with col2:
                    # Placeholder for NetCDF export
                    if st.button("🌐 Download NetCDF", use_container_width=True):
                        st.info("NetCDF export functionality coming soon!")
                
                # Visualizations in tabs
                st.markdown("### 📈 Data Visualizations")
                
                tab1, tab2, tab3, tab4 = st.tabs(["🌡️ Temperature", "🧂 Salinity", "🗺️ Map", "📊 Comparisons"])
                
                with tab1:
                    st.markdown("#### Depth vs Temperature Profile")
                    fig_temp = create_depth_temperature_plot(results)
                    st.plotly_chart(fig_temp, use_container_width=True)
                
                with tab2:
                    st.markdown("#### Depth vs Salinity Profile")
                    fig_sal = create_depth_salinity_plot(results)
                    st.plotly_chart(fig_sal, use_container_width=True)
                
                with tab3:
                    st.markdown("#### Float Locations")
                    fig_map = create_float_trajectory_map(results)
                    st.plotly_chart(fig_map, use_container_width=True)
                
                with tab4:
                    st.markdown("#### Float Comparisons")
                    fig_comp = create_comparison_plot(results)
                    st.plotly_chart(fig_comp, use_container_width=True)
            
            # Show warnings if any
            if warnings:
                for warning in warnings:
                    st.warning(f"⚠️ {warning}")
        
        else:
            st.markdown("""
            <div class="glass-container">
                <h4>🔍 No Results Found</h4>
                <p>No ARGO profiles matched your query. Try:</p>
                <ul>
                    <li>Broadening your search criteria</li>
                    <li>Checking different time periods</li>
                    <li>Using different geographic regions</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

# Footer
def show_footer():
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: rgba(255, 255, 255, 0.7); margin-top: 50px;">
        <p>🐙 FloatChat - AI-Powered ARGO Data Explorer | Built with Streamlit & LLaMA</p>
        <p><small>Democratizing access to oceanographic data through natural language interaction</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    show_footer()