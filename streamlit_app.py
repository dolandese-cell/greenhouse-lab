import streamlit as st
import pandas as pd
import time
import random

# --- 1. Page Configuration ---
st.set_page_config(page_title="Greenhouse Gas Lab", layout="wide")

# --- 2. Styles for Big Meters & Layout ---
st.markdown("""
<style>
    .big-font {
        font-size:50px !important;
        font-weight: bold;
        color: #333;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #d6d6d6;
    }
    .label-font {
        font-size: 20px;
        color: #555;
    }
    .particle-box {
        border: 2px solid #333;
        border-radius: 5px;
        background-color: #fff;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Physics & State Management ---

# Initialize Session State variables
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'current_time' not in st.session_state:
    st.session_state.current_time = 0.0
if 'current_temp' not in st.session_state:
    st.session_state.current_temp = 20.0 
if 'history_time' not in st.session_state:
    st.session_state.history_time = [0.0]
if 'history_temp' not in st.session_state:
    st.session_state.history_temp = [20.0]
if 'selected_gas' not in st.session_state:
    st.session_state.selected_gas = "Nitrogen (N2)"

# Physics Constants
# Insulation: 1.0 = No Greenhouse Effect (Heat escapes easily)
# Higher Insulation = Heat is trapped
GAS_PROPERTIES = {
    "Nitrogen (N2)":       {"Insulation": 1.0, "Color": "#1f77b4", "Particles": 30}, 
    "Oxygen (O2)":         {"Insulation": 1.0, "Color": "#2ca02c", "Particles": 30}, 
    "Carbon Dioxide (CO2)": {"Insulation": 4.0, "Color": "#ff7f0e", "Particles": 50}, 
    "Methane (CH4)":       {"Insulation": 8.0, "Color": "#d62728", "Particles": 50}  
}

AMBIENT_TEMP = 20.0 

# --- 4. Sidebar Controls & Auto-Reset ---
st.sidebar.header("🔬 Experiment Controls")

gas_name = st.sidebar.selectbox("Select Gas Type", list(GAS_PROPERTIES.keys()))
intensity = st.sidebar.slider("Light Intensity (Heating Power)", 1, 10, 5)
concentration = st.sidebar.slider("Gas Concentration (ppm)", 0, 1000, 500)
sim_speed = st.sidebar.slider("Simulation Speed", 1, 10, 5, help="Higher number = Faster animation")

# Auto-Reset Logic: Check if gas changed
if gas_name != st.session_state.selected_gas:
    st.session_state.is_running = False
    st.session_state.current_time = 0.0
    st.session_state.current_temp = AMBIENT_TEMP
    st.session_state.history_time = [0.0]
    st.session_state.history_temp = [AMBIENT_TEMP]
    st.session_state.selected_gas = gas_name
    st.rerun()

# --- 5. Helper Functions (Visuals) ---

def generate_particle_html(temp, color):
    """Generates an SVG animation of vibrating particles."""
    # Speed is inversely proportional to temperature (Hotter = Faster vibration duration is lower)
    # Mapping 20C -> 1.0s, 60C -> 0.1s
    clamped_temp = max(20, min(100, temp))
    speed = 1.0 - ((clamped_temp - 20) / 100.0) 
    speed = max(0.1, speed)
    
    particles = []
    # Create random dots
    for _ in range(20):
        cx = random.randint(10, 290)
        cy = random.randint(10, 140)
        r = random.randint(3, 6)
        dx = random.choice([-5, 5])
        dy = random.choice([-5, 5])
        
        # We construct the string without indentation to avoid Markdown code-block parsing issues
        particle = (
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="0.7">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0,0; {dx},{dy}; 0,0" dur="{speed}s" repeatCount="indefinite" />'
            f'</circle>'
        )
        particles.append(particle)
    
    svg_content = "".join(particles)
    
    # Return a clean, flattened HTML string
    return (
        f'<div class="particle-box">'
        f'<svg width="100%" height="150" viewBox="0 0 300 150" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="100%" height="100%" fill="#fafafa"/>'
        f'{svg_content}'
        f'<text x="10" y="140" font-family="Arial" font-size="12" fill="#555">Molecular Activity</text>'
        f'</svg>'
        f'</div>'
    )

def update_ui(temp, t, history_t, history_T, gas_props):
    # 1. Update Meters
    temp_placeholder.markdown(
        f'<div class="metric-container"><div class="big-font">{temp:.1f} °C</div></div>', 
        unsafe_allow_html=True
    )
    time_placeholder.markdown(
        f'<div class="metric-container"><div class="big-font">{t:.1f} m</div></div>', 
        unsafe_allow_html=True
    )
    
    # 2. Update Graph
    chart_data = pd.DataFrame({"Time": history_t, "Temperature": history_T})
    chart_placeholder.line_chart(chart_data.set_index("Time"), color=gas_props["Color"])
    
    # 3. Update Particle Visual
    particle_html = generate_particle_html(temp, gas_props["Color"])
    particle_placeholder.markdown(particle_html, unsafe_allow_html=True)

# --- 6. Main UI Layout ---

st.title("🧪 Interactive Greenhouse Effect Lab")

# Top Row: Buttons
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
with col_btn1:
    if st.button("▶️ Play"):
        st.session_state.is_running = True
with col_btn2:
    if st.button("II Pause"):
        st.session_state.is_running = False
with col_btn3:
    if st.button("🔄 Reset"):
        st.session_state.is_running = False
        st.session_state.current_time = 0.0
        st.session_state.current_temp = AMBIENT_TEMP
        st.session_state.history_time = [0.0]
        st.session_state.history_temp = [AMBIENT_TEMP]
        st.rerun()

st.divider()

# Middle Row: Layout
# Left: Meters & Particles | Right: Graph
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown('<div class="label-font">Current Temperature</div>', unsafe_allow_html=True)
    temp_placeholder = st.empty()
    
    st.write("") 
    st.markdown('<div class="label-font">Elapsed Time (min)</div>', unsafe_allow_html=True)
    time_placeholder = st.empty()
    
    st.write("")
    st.markdown('<div class="label-font">Particle View</div>', unsafe_allow_html=True)
    particle_placeholder = st.empty()

with col_right:
    chart_placeholder = st.empty()

# --- 7. The Simulation Loop ---

# Physics Logic Setup
base_cooling = 1.5 # Increased cooling so N2/O2 don't heat up much
insulation_factor = 1.0 

props = GAS_PROPERTIES[gas_name]
if props["Insulation"] > 1.0:
    # Use concentration to scale the insulation
    added_insulation = (props["Insulation"] - 1.0) * (concentration / 1000.0)
    insulation_factor = 1.0 + added_insulation

cooling_rate = base_cooling / insulation_factor

# Render initial state
update_ui(
    st.session_state.current_temp, 
    st.session_state.current_time, 
    st.session_state.history_time, 
    st.session_state.history_temp,
    props
)

if st.session_state.is_running:
    while st.session_state.is_running and st.session_state.current_time < 20.0:
        
        # 1. Physics Step
        dt = 0.1 
        heat_gain = intensity * 1.5 # Adjusted heat gain
        temp_diff = st.session_state.current_temp - AMBIENT_TEMP
        heat_loss = temp_diff * cooling_rate
        
        net_change = (heat_gain - heat_loss) * dt
        
        st.session_state.current_temp += net_change
        st.session_state.current_time += dt
        
        # Ensure we don't drop below ambient
        if st.session_state.current_temp < AMBIENT_TEMP:
             st.session_state.current_temp = AMBIENT_TEMP
        
        st.session_state.history_time.append(st.session_state.current_time)
        st.session_state.history_temp.append(st.session_state.current_temp)
        
        # 2. Update UI
        update_ui(
            st.session_state.current_temp, 
            st.session_state.current_time, 
            st.session_state.history_time, 
            st.session_state.history_temp,
            props
        )
        
        # 3. Speed Control
        time.sleep(0.5 / sim_speed)
        
    if st.session_state.current_time >= 20.0:
        st.session_state.is_running = False
        st.success("Simulation Complete!")
