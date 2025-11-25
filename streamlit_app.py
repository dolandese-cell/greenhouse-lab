import streamlit as st
import pandas as pd
import time
import random
import altair as alt
import os

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

# Storage for saved runs (comparison lines)
if 'saved_runs' not in st.session_state:
    st.session_state.saved_runs = {}

# Initialize Particle Data (Fixed positions)
if 'particle_data' not in st.session_state:
    particles = []
    for _ in range(30):
        particles.append({
            'cx': random.randint(10, 290),
            'cy': random.randint(10, 140),
            'r': random.randint(3, 6),
            'dx': random.choice([-5, 5]),
            'dy': random.choice([-5, 5]),
            'delay': random.uniform(0, 1.0) 
        })
    st.session_state.particle_data = particles

# Physics Constants
GAS_PROPERTIES = {
    "Nitrogen (N2)":       {"Insulation": 1.0, "Color": "#1f77b4"}, 
    "Oxygen (O2)":         {"Insulation": 1.0, "Color": "#2ca02c"}, 
    "Carbon Dioxide (CO2)": {"Insulation": 4.0, "Color": "#ff7f0e"}, 
    "Methane (CH4)":       {"Insulation": 8.0, "Color": "#d62728"}  
}

AMBIENT_TEMP = 20.0 

# --- 4. Sidebar Controls & Auto-Reset ---
st.sidebar.header("🔬 Experiment Controls")

gas_name = st.sidebar.selectbox("Select Gas Type", list(GAS_PROPERTIES.keys()))
intensity = st.sidebar.slider("Light Intensity (Heating Power)", 1, 10, 5)
concentration = st.sidebar.slider("Gas Concentration (ppm)", 0, 1000, 500)
sim_speed = st.sidebar.slider("Simulation Speed", 1, 10, 5, help="Higher number = Faster animation")

# Button to clear comparison history
if st.sidebar.button("🗑️ Clear Graph History"):
    st.session_state.saved_runs = {}
    st.rerun()

# Auto-Reset Logic: Check if gas changed
if gas_name != st.session_state.selected_gas:
    # 1. Save the OLD run before switching, if it has data
    if len(st.session_state.history_time) > 10: # Only save if they actually ran it for a bit
        prev_gas = st.session_state.selected_gas
        st.session_state.saved_runs[prev_gas] = {
            "Time": st.session_state.history_time,
            "Temp": st.session_state.history_temp,
            "Color": GAS_PROPERTIES[prev_gas]["Color"]
        }
    
    # 2. Reset Everything for new gas
    st.session_state.is_running = False
    st.session_state.current_time = 0.0
    st.session_state.current_temp = AMBIENT_TEMP
    st.session_state.history_time = [0.0]
    st.session_state.history_temp = [AMBIENT_TEMP]
    st.session_state.selected_gas = gas_name
    
    # Regenerate particles
    st.session_state.particle_data = [] 
    for _ in range(30):
        st.session_state.particle_data.append({
            'cx': random.randint(10, 290),
            'cy': random.randint(10, 140),
            'r': random.randint(3, 6),
            'dx': random.choice([-5, 5]),
            'dy': random.choice([-5, 5]),
            'delay': random.uniform(0, 1.0)
        })
    st.rerun()

# --- 5. Helper Functions (Visuals) ---

def generate_particle_html(temp, color):
    speed_factor = max(0.0, min(1.0, (temp - 20) / 50.0)) 
    duration = 1.0 - (speed_factor * 0.8) 
    duration = max(0.1, duration) 
    
    particle_svgs = []
    for p in st.session_state.particle_data:
        # Unpack variables for cleaner f-string
        cx, cy, r = p['cx'], p['cy'], p['r']
        dx, dy, delay = p['dx'], p['dy'], p['delay']
        
        particle = (
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="0.7">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0,0; {dx},{dy}; 0,0" dur="{duration:.2f}s" '
            f'begin="-{delay:.2f}s" repeatCount="indefinite" />'
            f'</circle>'
        )
        particle_svgs.append(particle)
    
    svg_content = "".join(particle_svgs)
    
    return (
        f'<div class="particle-box">'
        f'<svg width="100%" height="150" viewBox="0 0 300 150" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="100%" height="100%" fill="#fafafa"/>'
        f'{svg_content}'
        f'<text x="10" y="140" font-family="Arial" font-size="12" fill="#555">Molecular Activity</text>'
        f'</svg>'
        f'</div>'
    )

def plot_comparison_chart(history_t, history_T, current_gas_name, current_color):
    """
    Builds a multi-line chart using Altair to show Current + Saved runs.
    """
    # 1. Prepare Current Data
    df_current = pd.DataFrame({
        "Time": history_t,
        "Temperature": history_T,
        "Gas": current_gas_name
    })
    
    # 2. Prepare Saved Data
    all_dfs = [df_current]
    
    # Define color scale domain and range
    domain = [current_gas_name]
    range_colors = [current_color]
    
    for saved_gas_name, data in st.session_state.saved_runs.items():
        # Don't plot the saved version of the current gas (avoid duplicates)
        if saved_gas_name != current_gas_name:
            df_saved = pd.DataFrame({
                "Time": data["Time"],
                "Temperature": data["Temp"],
                "Gas": saved_gas_name
            })
            all_dfs.append(df_saved)
            domain.append(saved_gas_name)
            range_colors.append(data["Color"])
            
    # Combine all data
    final_df = pd.concat(all_dfs)
    
    # 3. Create Altair Chart
    chart = alt.Chart(final_df).mark_line(strokeWidth=3).encode(
        x=alt.X('Time', title='Time (minutes)'),
        y=alt.Y('Temperature', title='Temperature (°C)', scale=alt.Scale(domain=[15, 65])),
        color=alt.Color('Gas', scale=alt.Scale(domain=domain, range=range_colors), legend=alt.Legend(title="Gases")),
        tooltip=['Gas', 'Time', 'Temperature']
    ).properties(
        height=350
    ).interactive()
    
    return chart

def update_ui(temp, t, history_t, history_T, gas_props, gas_name):
    # 1. Update Meters
    temp_placeholder.markdown(
        f'<div class="metric-container"><div class="big-font">{temp:.1f} °C</div></div>', 
        unsafe_allow_html=True
    )
    time_placeholder.markdown(
        f'<div class="metric-container"><div class="big-font">{t:.1f} m</div></div>', 
        unsafe_allow_html=True
    )
    
    # 2. Update Graph (Now using Altair for multi-line support)
    chart = plot_comparison_chart(history_t, history_T, gas_name, gas_props["Color"])
    chart_placeholder.altair_chart(chart, use_container_width=True)
    
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

# --- Image Upload / Display Section ---
# Only attempts to display if the file exists, to prevent crashing for users without the file
image_filename = "image_a015ba.jpg"
if os.path.exists(image_filename):
    st.write("") # Spacer
    st.image(image_filename, caption="Lab Setup", use_container_width=True)
else:
    # Optional: Display a placeholder or instructions if local file is missing
    st.info(f"Note: To see the lab setup image, ensure '{image_filename}' is in the same folder as this script.")

# --- 7. The Simulation Loop ---

# Physics Logic Setup
base_cooling = 1.5 
insulation_factor = 1.0 

props = GAS_PROPERTIES[gas_name]
if props["Insulation"] > 1.0:
    added_insulation = (props["Insulation"] - 1.0) * (concentration / 1000.0)
    insulation_factor = 1.0 + added_insulation

cooling_rate = base_cooling / insulation_factor

# Render initial state
update_ui(
    st.session_state.current_temp, 
    st.session_state.current_time, 
    st.session_state.history_time, 
    st.session_state.history_temp,
    props,
    gas_name
)

if st.session_state.is_running:
    while st.session_state.is_running and st.session_state.current_time < 20.0:
        
        # 1. Physics Step
        dt = 0.1 
        heat_gain = intensity * 1.5 
        temp_diff = st.session_state.current_temp - AMBIENT_TEMP
        heat_loss = temp_diff * cooling_rate
        
        net_change = (heat_gain - heat_loss) * dt
        
        st.session_state.current_temp += net_change
        st.session_state.current_time += dt
        
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
            props,
            gas_name
        )
        
        # 3. Speed Control
        time.sleep(0.5 / sim_speed)
        
    if st.session_state.current_time >= 20.0:
        st.session_state.is_running = False
        st.success("Simulation Complete!")
