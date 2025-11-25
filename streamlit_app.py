import streamlit as st
import pandas as pd
import time

# --- 1. Page Configuration ---
st.set_page_config(page_title="Greenhouse Gas Lab", layout="wide")

# --- 2. Styles for Big Meters ---
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
</style>
""", unsafe_allow_html=True)

# --- 3. Physics & State Management ---

# Initialize Session State variables if they don't exist
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'current_time' not in st.session_state:
    st.session_state.current_time = 0.0
if 'current_temp' not in st.session_state:
    st.session_state.current_temp = 20.0 # Start at Room Temp
if 'history_time' not in st.session_state:
    st.session_state.history_time = [0.0]
if 'history_temp' not in st.session_state:
    st.session_state.history_temp = [20.0]

# Physics Constants
GAS_PROPERTIES = {
    "Nitrogen (N2)":       {"Insulation": 1.0, "Color": "#1f77b4"}, # Baseline (No extra heat trapping)
    "Oxygen (O2)":         {"Insulation": 1.0, "Color": "#2ca02c"}, # Baseline
    "Carbon Dioxide (CO2)": {"Insulation": 1.5, "Color": "#ff7f0e"}, # Traps heat
    "Methane (CH4)":       {"Insulation": 2.5, "Color": "#d62728"}  # Traps A LOT of heat
}

AMBIENT_TEMP = 20.0  # Room temperature

# --- 4. Sidebar Controls ---
st.sidebar.header("🔬 Experiment Controls")

gas_name = st.sidebar.selectbox("Select Gas Type", list(GAS_PROPERTIES.keys()))
intensity = st.sidebar.slider("Light Intensity (Heating Power)", 1, 10, 5)
concentration = st.sidebar.slider("Gas Concentration (ppm)", 0, 1000, 500)
sim_speed = st.sidebar.slider("Simulation Speed", 1, 10, 5, help="Higher number = Faster animation")

# --- 5. Main UI Layout ---

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

st.divider()

# Middle Row: Big Meters & Graph
col_left, col_right = st.columns([1, 2])

# Placeholders for live updates
with col_left:
    st.markdown('<div class="label-font">Current Temperature</div>', unsafe_allow_html=True)
    temp_placeholder = st.empty()
    
    st.write("") # Spacer
    
    st.markdown('<div class="label-font">Elapsed Time (min)</div>', unsafe_allow_html=True)
    time_placeholder = st.empty()

with col_right:
    chart_placeholder = st.empty()

# --- 6. Helper Function to Draw UI ---
def update_ui(temp, t, history_t, history_T, gas_color):
    # Update Big Temperature Meter
    temp_placeholder.markdown(
        f'<div class="metric-container"><div class="big-font">{temp:.1f} °C</div></div>', 
        unsafe_allow_html=True
    )
    
    # Update Time Meter
    time_placeholder.markdown(
        f'<div class="metric-container"><div class="big-font">{t:.1f} m</div></div>', 
        unsafe_allow_html=True
    )
    
    # Update Graph
    chart_data = pd.DataFrame({"Time": history_t, "Temperature": history_T})
    
    # We use Altair or standard Streamlit line chart
    # Setting a fixed Y-axis (15 to 60) so students see the rise clearly
    # Note: Streamlit line_chart auto-scales, so we construct a slight workaround 
    # or just let it auto-scale. For Simplicity, we rely on auto-scale but add a 'Limit' line?
    # No, let's keep it simple.
    chart_placeholder.line_chart(
        chart_data.set_index("Time"), 
        color=gas_color
    )

# --- 7. The Simulation Loop ---

# Calculate Physics Parameters based on Sliders
# Logic: Heat In - Heat Out = Change in Temp
# Heat In = Intensity
# Heat Out = (CurrentTemp - Ambient) * CoolingFactor
# Greenhouse gases DECREASE the CoolingFactor (trap heat)

base_cooling = 0.5 # How fast a normal bottle cools
# Insulation multiplier: 1.0 = Normal, 2.0 = Harder to cool
insulation_factor = 1.0 

props = GAS_PROPERTIES[gas_name]
if props["Insulation"] > 1.0:
    # Use concentration to scale the insulation
    # 0 ppm = 1.0 (no effect), 1000 ppm = Max effect defined in dictionary
    added_insulation = (props["Insulation"] - 1.0) * (concentration / 1000.0)
    insulation_factor = 1.0 + added_insulation

# Effective cooling rate (Lower = Hotter bottle)
cooling_rate = base_cooling / insulation_factor

# Render initial static state
update_ui(
    st.session_state.current_temp, 
    st.session_state.current_time, 
    st.session_state.history_time, 
    st.session_state.history_temp,
    props["Color"]
)

# If "Play" is active, run the loop
if st.session_state.is_running:
    
    # Loop Logic
    while st.session_state.is_running and st.session_state.current_time < 20.0: # Stop at 20 mins
        
        # 1. Physics Step
        dt = 0.1 # Simulation time step
        
        # Newton's Law of Heating/Cooling
        # Energy In (Lamp)
        heat_gain = intensity * 2.0 
        
        # Energy Out (Loss to room)
        temp_diff = st.session_state.current_temp - AMBIENT_TEMP
        heat_loss = temp_diff * cooling_rate
        
        # Net Change
        net_change = (heat_gain - heat_loss) * dt
        
        # Update State
        st.session_state.current_temp += net_change
        st.session_state.current_time += dt
        
        # Append to History
        st.session_state.history_time.append(st.session_state.current_time)
        st.session_state.history_temp.append(st.session_state.current_temp)
        
        # 2. Update UI
        update_ui(
            st.session_state.current_temp, 
            st.session_state.current_time, 
            st.session_state.history_time, 
            st.session_state.history_temp,
            props["Color"]
        )
        
        # 3. Speed Control
        # Sleep time decreases as speed slider increases
        sleep_time = 0.5 / sim_speed 
        time.sleep(sleep_time)
        
        # Check if we should stop (Streamlit re-runs script on interaction, 
        # but inside a loop we must rely on the loop finishing or external interrupt. 
        # A true 'Pause' button press during the loop triggers a script re-run, 
        # which will reset 'is_running' variable logic if we aren't careful, 
        # but since we set is_running via button earlier, the rerun stops the loop.)
        
    # If time is up
    if st.session_state.current_time >= 20.0:
        st.session_state.is_running = False
        st.success("Simulation Complete!")
