import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import base64
from utils import (
    calculate_profit_per_acre, 
    identify_optimization_areas,
    generate_pdf_report,
    generate_excel_report
)
from data_loader import load_csv_data, load_excel_data, load_wheat_data

# Page configuration
st.set_page_config(
    page_title="TapGrow 360 | Agricultural Financial Analysis",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add meta tags for better mobile experience
st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
""", unsafe_allow_html=True)

# Apply custom CSS for a cleaner, sharper interface
try:
    with open('.streamlit/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except Exception as e:
    st.error(f"Could not load CSS: {e}")
    # Apply some emergency inline CSS for extreme mobile optimization
    st.markdown("""
    <style>
    /* Emergency mobile CSS */
    @media screen and (max-width: 375px) {
        .main .block-container {
            padding: 0.3rem !important;
            max-width: 95% !important;
        }
        h1, h2, h3, h4, h5, h6 {
            font-size: 80% !important;
            margin: 0.2rem 0 !important;
        }
        p, div {
            font-size: 70% !important;
        }
        [data-testid="stSidebar"] {
            width: 150px !important;
        }
        .logo-container img {
            max-width: 60% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Removed the INPUTS button as requested
# Always keep the sidebar expanded
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = 'expanded'

# Display responsive logo - using HTML for better mobile responsiveness
# First add the responsive logo styles
st.markdown("""
<style>
/* Ultra-responsive logo for tiny screens */
@media screen and (max-width: 375px) {
    .logo-container img {
        max-width: 70% !important;
        width: 180px !important;
        height: auto !important;
        transform: scale(0.6) !important;
        transform-origin: center top !important;
        margin-top: -55px !important;  /* Pushed even higher */
        margin-bottom: -60px !important; /* Further increased negative margin to remove gap */
    }
    .logo-container {
        padding: 0 !important;
        margin: -15px auto -40px auto !important;  /* Increased negative bottom margin */
        height: 40px !important;
        overflow: hidden !important;
        top: -20px !important;  /* Added negative top positioning */
    }
    .intro-text {
        font-size: 11px !important;
        padding: 8px !important;
        margin-top: -10px !important; /* Made negative to pull text up */
    }
    /* Target the element container after logo container */
    .element-container:has(> div.logo-container) + div.element-container {
        margin-top: -40px !important;
    }
}

/* Ultra-ultra tiny screens */
@media screen and (max-width: 320px) {
    .logo-container img {
        transform: scale(0.45) !important;
        margin-top: -70px !important;  /* Pushed even more extreme up */
        margin-bottom: -70px !important; /* Even more extreme negative bottom margin */
    }
    .logo-container {
        height: 30px !important;
        margin: -25px auto -50px auto !important;  /* Further increased extreme negative bottom margin */
        top: -30px !important; /* Pushed higher with position */
    }
    .intro-text {
        font-size: 10px !important;
        padding: 5px !important;
        margin-top: -15px !important; /* Made even more negative to pull text up */
    }
    /* Target the element container after logo container on tiny screens */
    .element-container:has(> div.logo-container) + div.element-container {
        margin-top: -50px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Render the original logo with enhanced CSS for crispness
logo_base64 = base64.b64encode(open("./attached_assets/Original Logo_1754603028196.png", "rb").read()).decode().png", "rb").read()).decode()
st.markdown(f"""
<div class="logo-container" style="text-align: center; margin: -50px auto -80px auto; padding-top: 0; position: relative; top: -40px;">
    <img src="data:image/png;base64,{logo_base64}" 
         style="max-width: 95%; width: min(80vw, 600px); height: auto; margin: 0 auto; transform: translateY(-25px); 
                image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges; 
                filter: contrast(1.1) brightness(1.05) saturate(1.1);" 
         alt="TapGrow 360 Logo">
</div>
""", unsafe_allow_html=True)

# Add style to further reduce gaps between all top elements
st.markdown("""
<style>
/* Remove gap between logo and intro text */
.element-container:has(> div.logo-container) + div.element-container {
    margin-top: -30px !important;
}

/* Remove gap between intro text and financial summary heading */
.element-container:has(> div.intro-text) + div.element-container {
    margin-top: -15px !important;
}

/* Make all Streamlit headings have less padding */
.stMarkdown h3 {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="intro-text" style="margin: -10px 0 30px 0; padding: 15px; background-color: #f9f9f9; border-radius: 5px; border-left: 5px solid #1a5ebe;">
    <div style="font-size: 18px; font-weight: 500; line-height: 1.3;">
    This tool helps farmers optimize financial efficiency by analyzing operational costs and identifying 
    potential input reductions without impacting profitability. Explore different regions, crops, and cost 
    scenarios to maximize your farm's profitability.
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar for navigation and inputs
# Add small logo in sidebar
small_logo_base64 = base64.b64encode(open("attached_assets/Transparent Logo_1754605512600.png", "rb").read()).decode()
st.sidebar.markdown(f"""
<div style="text-align: center; margin-bottom: 10px;">
    <img src="data:image/png;base64,{small_logo_base64}" 
         style="max-width: 90%; height: auto; object-fit: contain;" 
         alt="TapGrow 360 Small Logo">
</div>
""", unsafe_allow_html=True)

st.sidebar.title("Crop Inputs")

# Load data from local files
@st.cache_data(ttl=600)  # Cache data for 10 minutes
def load_data(crop_type="Corn"):
    try:
        if crop_type == "Corn":
            csv_path = "attached_assets/AgriCommand2 Demo - Corn.csv"
            if os.path.exists(csv_path):
                return load_csv_data(csv_path)
            else:
                st.error(f"CSV file not found at path: {csv_path}")
                return None
        elif crop_type == "Soybeans":
            excel_path = "attached_assets/Beans.xlsx"
            if os.path.exists(excel_path):
                return load_excel_data(excel_path)
            else:
                st.error(f"Excel file not found at path: {excel_path}")
                return None
        elif crop_type == "Wheat":
            wheat_path = "attached_assets/Wheat_1753029874668.xlsx"
            if os.path.exists(wheat_path):
                return load_wheat_data(wheat_path)
            else:
                st.error(f"Wheat file not found at path: {wheat_path}")
                return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Add crop selection
selected_crop = st.sidebar.selectbox(
    "Select Crop",
    ["Corn", "Soybeans", "Wheat"],
    index=0,
    help="Choose the crop type for your analysis"
)

# Load the data based on selected crop
with st.spinner("Loading farm data..."):
    sheet_data = load_data(selected_crop)

if sheet_data is None:
    st.error("Failed to load data. Please check if the CSV file exists and is accessible.")
    st.stop()

# Extract the necessary dataframes from the loaded data
crop_data = sheet_data.get('crop_data', pd.DataFrame())
cost_data = sheet_data.get('cost_data', pd.DataFrame())
regional_costs = sheet_data.get('regional_costs', pd.DataFrame())

# Check if data is available
if crop_data.empty or cost_data.empty or regional_costs.empty:
    st.error("Some required data is missing from the CSV file.")
    st.stop()

# Select region
available_regions = regional_costs['Region'].unique().tolist()
selected_region = st.sidebar.selectbox("Select Region", available_regions)

# Filter regional costs based on selected region
region_costs = regional_costs[regional_costs['Region'] == selected_region]

# Use the crop already selected from the main dropdown

# Get details for the selected crop
if not crop_data.empty and 'Crop' in crop_data.columns:
    crop_match = crop_data[crop_data['Crop'] == selected_crop]
    if not crop_match.empty:
        crop_details = crop_match.iloc[0]
    else:
        # Use the first row if no exact match found
        crop_details = crop_data.iloc[0]
else:
    # Fallback to default values
    crop_details = pd.Series({'Yield': 50.0, 'Price': 5.0})

# User inputs for crop specifics
st.sidebar.subheader("Inputs")
yield_per_acre = st.sidebar.number_input(
    "Expected Yield (per acre)",
    min_value=0.0,
    value=float(crop_details.get('Yield', 50.0)),
    step=1.0 if selected_crop in ["Soybeans", "Wheat"] else 10.0,
    format="%.1f"
)

current_price = st.sidebar.number_input(
    "Current Price ($ per unit)",
    min_value=0.0,
    value=float(crop_details.get('Price', 5.0)),
    step=0.01,
    format="%.2f"
)

# Add straw revenue input for wheat
straw_revenue_input = 0.0
if selected_crop == "Wheat":
    straw_revenue_input = st.sidebar.number_input(
        "Straw Revenue ($ per acre)",
        min_value=0.0,
        value=float(crop_details.get('Straw_Revenue', 55.0)),
        step=1.0,
        format="%.2f",
        help="Additional revenue from selling wheat straw"
    )

total_acres = st.sidebar.number_input(
    "Total Acres",
    min_value=1,
    value=1,
    step=1
)

# Operational costs customization
st.sidebar.subheader("Analysis Mode")
analysis_mode = st.sidebar.radio(
    "Choose analysis mode",
    ["Single Scenario", "Compare Scenarios"],
    help="Use Single Scenario for a standard analysis, or Compare Scenarios to test different combinations of inputs"
)

st.sidebar.subheader("Customize Operational Costs")
show_cost_customization = st.sidebar.checkbox("Customize Costs", value=False)

# Get cost categories from the data
cost_categories = cost_data['Category'].unique().tolist()
custom_costs = {}

# Function to collect input values for a scenario
def collect_scenario_inputs(scenario_label=""):
    scenario_inputs = {}
    
    # Get region and crop selections
    if scenario_label:
        st.sidebar.markdown(f"#### {scenario_label}")
    
    # If we're in comparison mode and this is scenario 2+, allow different selections
    if analysis_mode == "Compare Scenarios" and scenario_label:
        scenario_region = st.sidebar.selectbox(f"Region {scenario_label}", available_regions, key=f"region_{scenario_label}")
        available_crops = crop_data['Crop'].unique().tolist() if not crop_data.empty else [selected_crop]
        scenario_crop = st.sidebar.selectbox(f"Crop {scenario_label}", available_crops, key=f"crop_{scenario_label}")
        
        # Get region-specific costs
        scenario_region_costs = regional_costs[regional_costs['Region'] == scenario_region]
        scenario_crop_details = crop_data[crop_data['Crop'] == scenario_crop].iloc[0]
        
        # Get yield and price inputs
        scenario_yield = st.sidebar.number_input(
            f"Expected Yield {scenario_label} (per acre)",
            min_value=0.0,
            value=float(scenario_crop_details.get('Avg_Yield', 50.0)),
            step=10.0,
            format="%.1f",
            key=f"yield_{scenario_label}"
        )
        
        scenario_price = st.sidebar.number_input(
            f"Current Price {scenario_label} ($ per unit)",
            min_value=0.0,
            value=float(scenario_crop_details.get('Current_Price', 5.0)),
            step=0.01,
            format="%.2f",
            key=f"price_{scenario_label}"
        )
    else:
        # Use the main selections for the first scenario or single scenario mode
        scenario_region = selected_region
        scenario_crop = selected_crop
        scenario_region_costs = region_costs
        
        # Use the main yield and price inputs
        scenario_yield = yield_per_acre
        scenario_price = current_price
    
    # Store basic scenario data
    scenario_inputs["region"] = scenario_region
    scenario_inputs["crop"] = scenario_crop
    scenario_inputs["yield_per_acre"] = scenario_yield
    scenario_inputs["price_per_unit"] = scenario_price
    
    # Get cost customizations for this scenario
    scenario_costs = {}
    
    # If customizing costs and in comparison mode with multiple scenarios, show cost inputs for each
    if show_cost_customization and analysis_mode == "Compare Scenarios" and scenario_label:
        st.sidebar.markdown(f"##### Costs for {scenario_label}")
        
        for category in cost_categories:
            category_costs = cost_data[cost_data['Category'] == category]
            with st.sidebar.expander(f"{category} - {scenario_label}"):
                for _, row in category_costs.iterrows():
                    cost_item = row['Cost_Item'] if 'Cost_Item' in row else row['Item']
                    try:
                        if 'Cost_Item' in scenario_region_costs.columns:
                            cost_match = scenario_region_costs[scenario_region_costs['Cost_Item'] == cost_item]
                        elif 'Item' in scenario_region_costs.columns:
                            cost_match = scenario_region_costs[scenario_region_costs['Item'] == cost_item]
                        else:
                            cost_match = None
                        
                        if cost_match is not None and not cost_match.empty and 'Cost_Value' in cost_match.columns:
                            default_cost = cost_match['Cost_Value'].iloc[0]
                        else:
                            default_cost = 0.0
                    except:
                        default_cost = 0.0
                    
                    scenario_costs[cost_item] = st.sidebar.number_input(
                        f"{cost_item} ($ per acre)",
                        min_value=0.0,
                        value=float(default_cost),
                        step=0.1,
                        format="%.2f",
                        key=f"{cost_item}_{scenario_label}"
                    )
    elif show_cost_customization and (scenario_label == "" or analysis_mode == "Single Scenario"):
        # Show cost customization for single scenario mode or the first scenario
        for category in cost_categories:
            category_costs = cost_data[cost_data['Category'] == category]
            st.sidebar.markdown(f"**{category}**")
            
            for _, row in category_costs.iterrows():
                cost_item = row['Cost_Item'] if 'Cost_Item' in row else row['Item']
                try:
                    if 'Cost_Item' in scenario_region_costs.columns:
                        cost_match = scenario_region_costs[scenario_region_costs['Cost_Item'] == cost_item]
                    elif 'Item' in scenario_region_costs.columns:
                        cost_match = scenario_region_costs[scenario_region_costs['Item'] == cost_item]
                    else:
                        cost_match = None
                    
                    if cost_match is not None and not cost_match.empty and 'Cost_Value' in cost_match.columns:
                        default_cost = cost_match['Cost_Value'].iloc[0]
                    else:
                        default_cost = 0.0
                except:
                    default_cost = 0.0
                
                scenario_costs[cost_item] = st.sidebar.number_input(
                    f"{cost_item} ($ per acre)",
                    min_value=0.0,
                    value=float(default_cost),
                    step=0.1,
                    format="%.2f",
                    key=f"{cost_item}_{scenario_label}"
                )
    else:
        # Use default regional costs
        for _, row in cost_data.iterrows():
            # Handle both column formats (corn uses 'Item', soybeans uses 'Cost_Item')
            cost_item = row['Cost_Item'] if 'Cost_Item' in row else row['Item']
            try:
                if 'Cost_Item' in scenario_region_costs.columns:
                    cost_match = scenario_region_costs[scenario_region_costs['Cost_Item'] == cost_item]
                elif 'Item' in scenario_region_costs.columns:
                    cost_match = scenario_region_costs[scenario_region_costs['Item'] == cost_item]
                else:
                    cost_match = None
                
                if cost_match is not None and not cost_match.empty and 'Cost_Value' in cost_match.columns:
                    default_cost = cost_match['Cost_Value'].iloc[0]
                else:
                    default_cost = 0.0
            except:
                default_cost = 0.0
            scenario_costs[cost_item] = default_cost
    
    scenario_inputs["costs"] = scenario_costs
    return scenario_inputs

# For single scenario mode, use the traditional input collection
if analysis_mode == "Single Scenario":
    # Collect inputs for the single scenario
    scenario_data = collect_scenario_inputs()
    custom_costs = scenario_data["costs"]
else:
    # For comparison mode, collect data for multiple scenarios
    st.sidebar.markdown("### Scenario 1 (Baseline)")
    scenario1_data = collect_scenario_inputs("Scenario 1")
    
    st.sidebar.markdown("### Scenario 2")
    scenario2_data = collect_scenario_inputs("Scenario 2")
    
    # Option for a third scenario
    add_third_scenario = st.sidebar.checkbox("Add a third scenario")
    scenario3_data = None
    if add_third_scenario:
        st.sidebar.markdown("### Scenario 3")
        scenario3_data = collect_scenario_inputs("Scenario 3")
    
    # For the main calculations and visualizations, use Scenario 1 as the baseline
    custom_costs = scenario1_data["costs"]
    selected_region = scenario1_data["region"]
    selected_crop = scenario1_data["crop"]
    yield_per_acre = scenario1_data["yield_per_acre"]
    current_price = scenario1_data["price_per_unit"]

# Main calculation
total_cost_per_acre = sum(custom_costs.values())
revenue_per_acre = yield_per_acre * current_price

# Add straw revenue for wheat
if selected_crop == "Wheat":
    revenue_per_acre += straw_revenue_input
    
profit_per_acre = revenue_per_acre - total_cost_per_acre

total_cost = total_cost_per_acre * total_acres
total_revenue = revenue_per_acre * total_acres
total_profit = profit_per_acre * total_acres

# Display financial summary with minimal gap
st.markdown("<h3 style='font-size: 20px; margin-top: -5px; margin-bottom: 0;'>FINANCIAL SUMMARY</h3>", unsafe_allow_html=True)

# Add custom CSS for financial summary boxes
st.markdown("""
<style>
/* Custom styling for financial metrics */
[data-testid="stMetricValue"] {
    font-size: 1.25rem !important; /* Larger font for numbers */
    display: inline-block;
    margin-top: 0;
    color: #1a5ebe; /* Match our blue theme */
    font-weight: 500;
}

/* Reduce space between heading and metrics */
[data-testid="stVerticalBlock"] > div:has(> [data-testid="stMetric"]) {
    margin-top: -10px;
    padding-top: 0;
}

/* Increase font size for metric labels */
[data-testid="stMetricLabel"] {
    margin-bottom: -5px;
    font-size: 1.05rem !important;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# Create responsive columns for the key metrics - using 1:1:1 for desktop, but will stack on mobile with CSS
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Revenue per Acre", f"${revenue_per_acre:,.2f}")
    # Show breakdown for wheat with straw revenue
    if selected_crop == "Wheat" and straw_revenue_input > 0:
        grain_revenue = yield_per_acre * current_price
        st.markdown(f"<p style='font-size: 0.8rem; color: #666; margin-top: -10px; margin-bottom: 10px;'>Grain: ${grain_revenue:,.2f}<br>Straw: ${straw_revenue_input:,.2f}</p>", unsafe_allow_html=True)
    st.metric("Total Revenue", f"${total_revenue:,.2f}")
with col2:
    st.metric("Cost per Acre", f"${total_cost_per_acre:,.2f}")
    st.metric("Total Cost", f"${total_cost:,.2f}")
with col3:
    st.metric("Profit per Acre", f"${profit_per_acre:,.2f}")
    st.metric("Total Profit", f"${total_profit:,.2f}")

# Detailed cost breakdown
# Add minimal divider with reduced space from financial summary
st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px;'>", unsafe_allow_html=True)
st.markdown("<h3 style='font-size: 18px; margin-top: 0;'>COST BREAKDOWN</h3>", unsafe_allow_html=True)

# Organize costs by category
categorized_costs = {}
for _, row in cost_data.iterrows():
    category = row['Category']
    item = row['Cost_Item'] if 'Cost_Item' in row else row['Item']
    if category not in categorized_costs:
        categorized_costs[category] = {}
    categorized_costs[category][item] = custom_costs.get(item, 0.0)

# Calculate category totals
category_totals = {category: sum(items.values()) for category, items in categorized_costs.items()}

# Create a pie chart for direct costs only
direct_cost_items = []
direct_cost_values = []

# Get only direct costs
if 'Direct Costs' in categorized_costs:
    direct_costs = categorized_costs['Direct Costs']
    for item, value in direct_costs.items():
        direct_cost_items.append(item)
        direct_cost_values.append(value)
    
    # Create a pie chart for direct costs
    # Using a custom vibrant color palette
    vibrant_colors = ['#FF4136', '#0074D9', '#2ECC40', '#FFDC00', '#FF851B', '#B10DC9', '#F012BE', '#01FF70', '#39CCCC', '#85144b']
    
    fig_direct_costs = px.pie(
        names=direct_cost_items,
        values=direct_cost_values,
        title="Individual Direct Costs ($ per Acre)",
        color_discrete_sequence=vibrant_colors, # Using custom vibrant colors
        hole=0.3  # Creates a donut chart for better visibility
    )
    
    # Customize layout
    fig_direct_costs.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hoverinfo='label+value+percent',
        textfont=dict(size=14, color='black'), # Make text larger and black
        insidetextfont=dict(color='black')     # Ensure inside text is black
    )
    
    # Add custom hover template to show dollar values
    fig_direct_costs.update_traces(
        hovertemplate='<b>%{label}</b><br>$%{value:.2f} per acre<br>%{percent}'
    )
    
    # Remove borders between pie segments
    fig_direct_costs.update_traces(
        marker=dict(line=dict(color='white', width=0))
    )
    
    # Make chart more mobile-responsive
    fig_direct_costs.update_layout(
        uniformtext_minsize=14,
        uniformtext_mode='hide',
        margin=dict(l=0, r=0, t=30, b=0),  # Tighter margins for mobile
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="bottom",
            y=-0.2,          # Position below chart
            xanchor="center",
            x=0.5,           # Center the legend
            font=dict(size=10)  # Smaller legend text
        ),
        height=250,           # Even smaller height for better mobile view
        title_font=dict(size=12)  # Smaller title font
    )
    
    # Extra adjustments for tiny screens
    st.markdown("""
    <style>
    /* Ultra-small screen adjustments for pie chart */
    @media screen and (max-width: 375px) {
        div[data-testid="stPlotlyChart"] .js-plotly-plot {
            transform: scale(0.85);
            transform-origin: top center;
            height: 220px !important;
            margin-bottom: -50px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Set the chart to be responsive (auto-adjust to container width)
    st.plotly_chart(fig_direct_costs, use_container_width=True)
else:
    st.write("No direct costs data available.")

# Create a bar chart for detailed cost breakdown
cost_items = []
cost_values = []
cost_categories_list = []

for category, items in categorized_costs.items():
    for item, value in items.items():
        cost_items.append(item)
        cost_values.append(value)
        cost_categories_list.append(category)

cost_df = pd.DataFrame({
    'Item': cost_items,
    'Cost': cost_values,
    'Category': cost_categories_list
})

# Sort by cost value descending
cost_df = cost_df.sort_values('Cost', ascending=False)

fig_bar = px.bar(
    cost_df,
    x='Item',
    y='Cost',
    color='Category',
    title="Detailed Cost Breakdown ($ per Acre)",
    labels={'Item': 'Cost Item', 'Cost': 'Cost per Acre ($)'}
)

# Make chart more mobile-responsive
fig_bar.update_layout(
    margin=dict(l=0, r=0, t=30, b=0),  # Tighter margins for mobile
    legend=dict(
        orientation="h",      # Horizontal legend
        yanchor="bottom",
        y=-0.25,             # Position below chart
        xanchor="center",
        x=0.5,              # Center the legend
        font=dict(size=9)    # Smaller legend text
    ),
    xaxis=dict(
        tickangle=-45,       # Angle the labels to prevent overlap
        tickfont=dict(size=8)  # Smaller font size for labels
    ),
    height=300,             # Smaller height for mobile views
    title_font=dict(size=12)  # Smaller title font
)

# Extra adjustments for tiny screens
st.markdown("""
<style>
/* Ultra-small screen adjustments for second chart */
@media screen and (max-width: 375px) {
    /* Apply to the second plotly chart */
    div[data-testid="stPlotlyChart"]:nth-of-type(2) .js-plotly-plot {
        transform: scale(0.8);
        transform-origin: top center;
        height: 250px !important;
        margin-bottom: -50px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Set the chart to be responsive (auto-adjust to container width)
st.plotly_chart(fig_bar, use_container_width=True)

# Calculate optimization data but don't display general optimization section
optimization_results = identify_optimization_areas(custom_costs, category_totals, profit_per_acre)

# Create dedicated sections for each of the top 4 direct costs
# Add a less prominent divider with minimal spacing
st.markdown("<hr style='margin-top: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
st.markdown("<h3 style='font-size: 18px; margin-top: 0;'>DIRECT COST REDUCTION ANALYSIS</h3>", unsafe_allow_html=True)
st.write("Direct costs account for 76 percent of total input costs. Analyze how reductions in these key costs affect your profit.")

# Define the key direct cost items we want to analyze 
if selected_crop == "Soybeans":
    key_direct_costs = ["Rent", "Seed", "Chemical", "Insurance"]
elif selected_crop == "Wheat":
    key_direct_costs = ["Rent", "Fertilizer", "Seed", "Chemical"]
else:  # Corn
    key_direct_costs = ["Rent", "Fertilizer", "Seed", "Chemical"]

# Process each direct cost item individually
for cost_item in key_direct_costs:
    # Only process if this cost item exists in the data
    if cost_item in custom_costs:
        current_cost = custom_costs[cost_item]
        
        # Create a dedicated section for this cost item
        st.markdown(f"<div class='scenario-subheader'>{cost_item} Cost Reduction Analysis</div>", unsafe_allow_html=True)
        st.markdown(f"<p style='margin-bottom:2px;'>Current {cost_item} cost: <strong>${current_cost:.2f}</strong> per acre</p>", unsafe_allow_html=True)
        
        # Create reduction data specific to this cost item
        reduction_percentages = [1, 5, 10, 15, 20]
        item_reduction_data = []
        
        for pct in reduction_percentages:
            # Calculate the reduced cost of this specific input
            new_item_cost = current_cost * (1 - pct/100)
            
            # Calculate savings on this specific input
            item_savings = current_cost - new_item_cost
            
            # Calculate new farm-wide costs and profits
            new_farm_total_cost = total_cost_per_acre - item_savings
            new_farm_profit = revenue_per_acre - new_farm_total_cost
            profit_increase = new_farm_profit - profit_per_acre
            profit_increase_total = profit_increase * total_acres
            
            # Only include the reduction percentage, new cost (with wrapped heading), and total profit increase
            item_reduction_data.append({
                'Reduction %': pct,
                f'New\n{cost_item}\nCost': new_item_cost,  # Line breaks for better wrapping
                'Total\nProfit\nIncrease': profit_increase_total  # Line breaks here too
            })
        
        # Create a DataFrame for this specific cost item
        item_df = pd.DataFrame(item_reduction_data)
        
        # Format numeric columns with thousands separators
        format_dict = {
            f'New\n{cost_item}\nCost': '${:,.2f}',  # Match the new column name with line breaks
            'Total\nProfit\nIncrease': '${:,.2f}'   # Match the new column name with line breaks
        }
        
        # Apply formatting to DataFrame
        item_df_formatted = item_df.copy()
        for col, fmt in format_dict.items():
            item_df_formatted[col] = item_df_formatted[col].apply(lambda x: fmt.format(x))
        
        # Special CSS to match table width to graph width and hide index column
        st.markdown("""
        <style>
        /* Table matching graph width exactly */
        div[data-testid="stDataFrame"] {
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: auto !important;
        }
        
        /* Tiny narrow table on mobile */
        @media screen and (max-width: 375px) {
            /* Hide the index column (first column) */
            div[data-testid="stDataFrame"] table th:first-child,
            div[data-testid="stDataFrame"] table td:first-child {
                display: none !important;
                width: 0 !important;
                padding: 0 !important;
                margin: 0 !important;
                max-width: 0 !important;
            }
            
            div[data-testid="stDataFrame"] table {
                font-size: 6px !important;
                padding: 0 !important;
                margin: 0 !important;
            }
            
            div[data-testid="stDataFrame"] th,
            div[data-testid="stDataFrame"] td {
                padding: 1px !important;
                white-space: normal !important;
                word-break: break-all !important;
                max-width: 55px !important;
            }
            
            div[data-testid="stDataFrame"] {
                transform: scale(0.85) !important;
                transform-origin: top left !important;
                margin-bottom: -20px !important;
                width: 105% !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Use dataframe with modified display options
        # Set the index to False to avoid showing row numbers
        st.dataframe(item_df_formatted, use_container_width=True, hide_index=True)
        
        # Create bar chart specifically for this cost item
        unformatted_profit_increases = [profit_increase for pct, price, profit_increase in [
            (item['Reduction %'], 
             item[f'New\n{cost_item}\nCost'], 
             item['Total\nProfit\nIncrease'] / total_acres) # Convert back to per-acre for chart
            for item in item_reduction_data
        ]]
        
        fig = px.bar(
            item_reduction_data, 
            x='Reduction %', 
            y=unformatted_profit_increases,
            title=f"Impact of {cost_item} Cost Reduction on Profit per Acre",
            labels={'x': 'Reduction Percentage', 'y': 'Profit Increase ($/acre)'}
        )
        
        # Set specific chart titles for Seed and Chemical, use generic title for others
        title_text = ""
        if cost_item == "Seed":
            title_text = "<b>Impact of Seed Reduction on Profit per Acre</b>"
        elif cost_item == "Chemical":
            title_text = "<b>Impact of Chemical Reduction on Profit per Acre</b>"
        else:
            title_text = f"<b>Impact of {cost_item} Cost Reduction on Profit per Acre</b>"
            
        fig.update_layout(
            title={
                'text': title_text,
                'font': {'size': 18, 'color': '#1a5ebe', 'family': 'Arial, sans-serif'},
                'xanchor': 'left',
                'x': 0,
            }
        )
        
        # Customize the chart
        fig.update_layout(
            xaxis_title="Reduction Percentage (%)",
            yaxis_title="Profit Increase ($/acre)",
            yaxis_tickprefix="$",
            yaxis_tickformat=",.2f",
            margin=dict(l=5, r=5, t=50, b=5),  # Increased top margin for title
            height=270,  # Taller for larger text
            bargap=0.1,  # Reduce the gap between bars
            title_font=dict(size=14),  # Larger title size
            font=dict(size=14)  # Even larger font size for axis labels
        )
        
        # Add value labels on top of bars
        fig.update_traces(
            texttemplate='$%{y:.2f}',
            textposition='outside',
            textfont=dict(size=14)  # Larger text size for values
        )
        
        # Add more adjustments for tiny screens
        st.markdown("""
        <style>
        /* Ultra-small screen adjustments for reduction analysis charts */
        @media screen and (max-width: 375px) {
            /* Target the reduction charts (they come after the second plotly chart) */
            div[data-testid="stPlotlyChart"]:nth-of-type(n+3) .js-plotly-plot {
                transform: scale(0.8);
                transform-origin: top center;
                height: 180px !important;
                margin-bottom: -40px !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Set the chart to be responsive
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"{cost_item} cost not found in your current selections.")

# Scenario Comparison Section (only shown when in Compare Scenarios mode)
if analysis_mode == "Compare Scenarios":
    # Add divider for better visual separation
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 18px;'>SCENARIO COMPARISON</h3>", unsafe_allow_html=True)
    st.write("Compare financial outcomes across different scenarios to identify the most profitable approach.")
    
    # Helper function to calculate financial metrics for a scenario
    def calculate_scenario_metrics(scenario_data):
        s_yield = scenario_data["yield_per_acre"]
        s_price = scenario_data["price_per_unit"]
        s_costs = scenario_data["costs"]
        s_total_costs = sum(s_costs.values())
        
        s_revenue = s_yield * s_price
        s_profit = s_revenue - s_total_costs
        
        # Organize costs by category
        s_categorized_costs = {}
        for _, row in cost_data.iterrows():
            category = row['Category']
            item = row['Cost_Item'] if 'Cost_Item' in row else row['Item']
            if category not in s_categorized_costs:
                s_categorized_costs[category] = {}
            s_categorized_costs[category][item] = s_costs.get(item, 0.0)
        
        # Calculate category totals
        s_category_totals = {category: sum(items.values()) for category, items in s_categorized_costs.items()}
        
        return {
            "region": scenario_data["region"],
            "crop": scenario_data["crop"],
            "yield": s_yield,
            "price": s_price,
            "revenue": s_revenue,
            "total_costs": s_total_costs,
            "profit": s_profit,
            "category_costs": s_category_totals
        }
    
    # Calculate metrics for all scenarios
    scenario1_metrics = calculate_scenario_metrics(scenario1_data)
    scenario2_metrics = calculate_scenario_metrics(scenario2_data)
    scenario3_metrics = calculate_scenario_metrics(scenario3_data) if scenario3_data else None
    
    # Create comparison table for key metrics
    comparison_data = {
        "Metric": ["Region", "Crop", "Yield (per acre)", "Price ($ per unit)", 
                   "Revenue ($/acre)", "Total Costs ($/acre)", "Profit ($/acre)"],
        "Scenario 1": [
            scenario1_metrics["region"],
            scenario1_metrics["crop"],
            f"{scenario1_metrics['yield']:.1f}",
            f"${scenario1_metrics['price']:.2f}",
            f"${scenario1_metrics['revenue']:.2f}",
            f"${scenario1_metrics['total_costs']:.2f}",
            f"${scenario1_metrics['profit']:.2f}"
        ],
        "Scenario 2": [
            scenario2_metrics["region"],
            scenario2_metrics["crop"],
            f"{scenario2_metrics['yield']:.1f}",
            f"${scenario2_metrics['price']:.2f}",
            f"${scenario2_metrics['revenue']:.2f}",
            f"${scenario2_metrics['total_costs']:.2f}",
            f"${scenario2_metrics['profit']:.2f}"
        ]
    }
    
    # Add scenario 3 if it exists
    if scenario3_metrics:
        comparison_data["Scenario 3"] = [
            scenario3_metrics["region"],
            scenario3_metrics["crop"],
            f"{scenario3_metrics['yield']:.1f}",
            f"${scenario3_metrics['price']:.2f}",
            f"${scenario3_metrics['revenue']:.2f}",
            f"${scenario3_metrics['total_costs']:.2f}",
            f"${scenario3_metrics['profit']:.2f}"
        ]
    
    # Display the comparison with mobile-first approach
    st.markdown("<div class='scenario-subheader'>Key Metrics Comparison</div>", unsafe_allow_html=True)
    
    # Hide standard table on mobile and show cards instead
    st.markdown("""
    <style>
    /* DESKTOP-ONLY: Show the standard Streamlit table only on desktop */
    @media screen and (max-width: 375px) {
        div.scenario-table div[data-testid="stTable"] {
            display: none !important;
        }
        .mobile-comparison-cards {
            display: block !important;
        }
    }
    
    /* MOBILE-ONLY: Hide the mobile cards on desktop */
    @media screen and (min-width: 376px) {
        .mobile-comparison-cards {
            display: none !important;
        }
    }
    
    /* Ultra-minimal cards for tiny screens */
    .mobile-comparison-cards {
        width: 100%;
        font-size: 6px;
        margin-bottom: 5px;
    }
    
    .mobile-metric-card {
        background-color: #f9f9f9;
        border-left: 2px solid #1a5ebe;
        margin-bottom: 2px;
        padding: 1px;
    }
    
    .mobile-metric-title {
        font-weight: bold;
        margin: 0;
        font-size: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 50px;
    }
    
    .mobile-scenario-values {
        display: flex;
        justify-content: flex-start;
    }
    
    .mobile-scenario-value {
        margin: 0;
        padding: 0 1px;
        max-width: 20px;
        flex: 0 0 auto;
        text-align: left;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .mobile-scenario-label {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Wrap standard table in div for targeting with CSS
    st.markdown("<div class='scenario-table'>", unsafe_allow_html=True)
    
    # Abbreviate metric names for smaller screens
    mobile_comparison_data = comparison_data.copy()
    for i, metric in enumerate(mobile_comparison_data["Metric"]):
        if "Revenue per Acre" in metric:
            mobile_comparison_data["Metric"][i] = "Rev/Acre"
        elif "Total Revenue" in metric:
            mobile_comparison_data["Metric"][i] = "Tot Rev"
        elif "Cost per Acre" in metric:
            mobile_comparison_data["Metric"][i] = "Cost/Acre"
        elif "Total Cost" in metric:
            mobile_comparison_data["Metric"][i] = "Tot Cost"
        elif "Profit per Acre" in metric:
            mobile_comparison_data["Metric"][i] = "Prof/Acre"
        elif "Total Profit" in metric:
            mobile_comparison_data["Metric"][i] = "Tot Prof"
        elif "Yield (per acre)" in metric:
            mobile_comparison_data["Metric"][i] = "Yield"
        elif "Price ($ per unit)" in metric:
            mobile_comparison_data["Metric"][i] = "Price"
            
    # Standard table for desktop
    comparison_df = pd.DataFrame(mobile_comparison_data)
    st.table(comparison_df.set_index("Metric"))
    
    # Close the div wrapper
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Create series of cards for mobile instead of table
    mobile_cards_html = "<div class='mobile-comparison-cards'>"
    
    # Add cards for each metric
    for i, metric in enumerate(mobile_comparison_data["Metric"]):
        mobile_cards_html += f"""
        <div class="mobile-metric-card">
            <div class="mobile-metric-title">{metric}</div>
            <div class="mobile-scenario-values">
        """
        
        # Scenario 1 value
        mobile_cards_html += f"""
                <div class="mobile-scenario-value">
                    <div class="mobile-scenario-label">Scenario 1</div>
                    {comparison_data['Scenario 1'][i]}
                </div>
        """
        
        # Scenario 2 value
        mobile_cards_html += f"""
                <div class="mobile-scenario-value">
                    <div class="mobile-scenario-label">Scenario 2</div>
                    {comparison_data['Scenario 2'][i]}
                </div>
        """
        
        # Scenario 3 value if it exists
        if "Scenario 3" in comparison_data:
            mobile_cards_html += f"""
                <div class="mobile-scenario-value">
                    <div class="mobile-scenario-label">Scenario 3</div>
                    {comparison_data['Scenario 3'][i]}
                </div>
            """
        
        mobile_cards_html += """
            </div>
        </div>
        """
    
    mobile_cards_html += "</div>"
    
    # Display the custom mobile cards
    st.markdown(mobile_cards_html, unsafe_allow_html=True)
    
    # Create a bar chart comparing profits across scenarios
    profit_comparison = {
        "Scenario": ["Scenario 1", "Scenario 2"] + (["Scenario 3"] if scenario3_metrics else []),
        "Profit ($/acre)": [
            scenario1_metrics["profit"],
            scenario2_metrics["profit"]
        ] + ([scenario3_metrics["profit"]] if scenario3_metrics else [])
    }
    
    profit_df = pd.DataFrame(profit_comparison)
    
    # Create a bar chart for profit comparison
    fig_profit = px.bar(
        profit_df,
        x="Scenario",
        y="Profit ($/acre)",
        title="Profit Comparison Across Scenarios",
        color="Scenario",
        text_auto=True
    )
    
    # Format the text to show dollar values
    fig_profit.update_traces(
        texttemplate='$%{y:.2f}',
        textposition='outside',
        textfont=dict(size=10)  # Smaller text for mobile
    )
    
    # Make chart more mobile-responsive
    fig_profit.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),  # Ultra-tight margins for mobile
        height=250,  # Smaller height for mobile views
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="bottom",
            y=-0.25,         # Position below chart
            xanchor="center",
            x=0.5,          # Center the legend
            font=dict(size=9)  # Smaller legend text
        ),
        title_font=dict(size=10),  # Smaller title
        font=dict(size=8)  # Smaller fonts everywhere
    )
    
    # Add more adjustments for tiny screens
    st.markdown("""
    <style>
    /* Ultra-small screen adjustments for scenario comparison chart */
    @media screen and (max-width: 375px) {
        /* Target the scenario comparison chart */
        div[data-testid="stPlotlyChart"]:nth-last-of-type(1) .js-plotly-plot {
            transform: scale(0.8);
            transform-origin: top center;
            height: 180px !important;
            margin-bottom: -30px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Set the chart to be responsive
    st.plotly_chart(fig_profit, use_container_width=True)
    
    # Removed cost category radar chart as requested
    
    # Add analysis of the differences
    st.markdown("<div class='scenario-subheader'>Scenario Analysis</div>", unsafe_allow_html=True)
    
    # Find the most profitable scenario
    profit_values = [
        ("Scenario 1", scenario1_metrics["profit"]),
        ("Scenario 2", scenario2_metrics["profit"])
    ]
    
    if scenario3_metrics:
        profit_values.append(("Scenario 3", scenario3_metrics["profit"]))
    
    most_profitable = max(profit_values, key=lambda x: x[1])
    
    # Add responsive heading styles for very small screens
    st.markdown("""
    <style>
    /* Ultra-small screen adjustments for scenario analysis headings */
    @media screen and (max-width: 375px) {
        h3 {
            font-size: 14px !important;
            margin: 5px 0 2px 0 !important;
        }
        p {
            font-size: 12px !important;
            margin: 2px 0 !important;
            line-height: 1.2 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Use markdown for heading to allow for CSS styling
    st.markdown(f"### Most Profitable: {most_profitable[0]}")
    st.write(f"The most profitable scenario is **{most_profitable[0]}** with a profit of **${most_profitable[1]:.2f}** per acre.")
    
    # Compare with the baseline (Scenario 1)
    if most_profitable[0] != "Scenario 1":
        profit_diff = most_profitable[1] - scenario1_metrics["profit"]
        profit_pct = (profit_diff / scenario1_metrics["profit"]) * 100 if scenario1_metrics["profit"] != 0 else float('inf')
        
        st.write(f"This represents an increase of **${profit_diff:.2f}** per acre (**{profit_pct:.1f}%**) compared to the baseline scenario.")
    
    # Key factors that make the most profitable scenario better
    if most_profitable[0] == "Scenario 2":
        better_scenario = scenario2_metrics
        baseline = scenario1_metrics
    elif most_profitable[0] == "Scenario 3":
        better_scenario = scenario3_metrics
        baseline = scenario1_metrics
    else:
        # If Scenario 1 is the most profitable, compare it with Scenario 2
        better_scenario = scenario1_metrics
        baseline = scenario2_metrics
    
    st.markdown("### Key Differences")
    
    # Revenue difference
    revenue_diff = better_scenario["revenue"] - baseline["revenue"]
    # Cost difference
    cost_diff = better_scenario["total_costs"] - baseline["total_costs"]
    # Price and yield differences
    price_diff = better_scenario["price"] - baseline["price"]
    yield_diff = better_scenario["yield"] - baseline["yield"]
    
    # Combine all differences into a single markdown string for better styling
    st.markdown(f"""
    <div style="font-size: 0.9em;">
    - <strong>Revenue</strong>: ${better_scenario['revenue']:.2f} vs ${baseline['revenue']:.2f} (Difference: ${revenue_diff:.2f})
    - <strong>Total Costs</strong>: ${better_scenario['total_costs']:.2f} vs ${baseline['total_costs']:.2f} (Difference: ${cost_diff:.2f})
    - <strong>Price</strong>: ${better_scenario['price']:.2f} vs ${baseline['price']:.2f} (Difference: ${price_diff:.2f})
    - <strong>Yield</strong>: {better_scenario['yield']:.1f} vs {baseline['yield']:.1f} (Difference: {yield_diff:.1f})
    </div>
    """, unsafe_allow_html=True)

# Download report option
# Just add a divider with minimal spacing
st.markdown("<hr style='margin-top: 20px; margin-bottom: 10px;'>", unsafe_allow_html=True)
# Add section heading in the same style as FINANCIAL TERMS EXPLAINED
st.markdown("<h3 style='font-size: 18px;'>REPORTS</h3>", unsafe_allow_html=True)
# Compact download message
st.markdown("<p style='margin: 0; padding: 0;'>Generate a detailed report of this analysis:</p>", unsafe_allow_html=True)

# Generate report data
if analysis_mode == "Single Scenario":
    # Single scenario report
    report_data = {
        'Region': selected_region,
        'Crop': selected_crop,
        'Yield per Acre': yield_per_acre,
        'Price per Unit': current_price,
        'Total Acres': total_acres,
        'Revenue per Acre': revenue_per_acre,
        'Cost per Acre': total_cost_per_acre,
        'Profit per Acre': profit_per_acre,
        'Total Revenue': total_revenue,
        'Total Cost': total_cost,
        'Total Profit': total_profit,
        'Cost Breakdown': custom_costs,
        'Optimization Suggestions': optimization_results
    }

    report_csv = pd.DataFrame({
        'Metric': [
            'Region', 'Crop', 'Yield per Acre', 'Price per Unit', 'Total Acres',
            'Revenue per Acre ($)', 'Cost per Acre ($)', 'Profit per Acre ($)',
            'Total Revenue ($)', 'Total Cost ($)', 'Total Profit ($)'
        ],
        'Value': [
            selected_region, selected_crop, yield_per_acre, current_price, total_acres,
            f"${revenue_per_acre:,.2f}", f"${total_cost_per_acre:,.2f}", f"${profit_per_acre:,.2f}",
            f"${total_revenue:,.2f}", f"${total_cost:,.2f}", f"${total_profit:,.2f}"
        ]
    })
else:
    # Multi-scenario comparison report
    report_data = {
        'Mode': 'Scenario Comparison',
        'Total Acres': total_acres,
        'Baseline': {
            'Region': scenario1_metrics["region"],
            'Crop': scenario1_metrics["crop"],
            'Yield per Acre': scenario1_metrics["yield"],
            'Price per Unit': scenario1_metrics["price"],
            'Revenue per Acre': scenario1_metrics["revenue"],
            'Cost per Acre': scenario1_metrics["total_costs"], 
            'Profit per Acre': scenario1_metrics["profit"],
            'Total Revenue': scenario1_metrics["revenue"] * total_acres,
            'Total Cost': scenario1_metrics["total_costs"] * total_acres,
            'Total Profit': scenario1_metrics["profit"] * total_acres,
            'Cost Breakdown': scenario1_data["costs"]
        },
        'Scenario 2': {
            'Region': scenario2_metrics["region"],
            'Crop': scenario2_metrics["crop"],
            'Yield per Acre': scenario2_metrics["yield"],
            'Price per Unit': scenario2_metrics["price"],
            'Revenue per Acre': scenario2_metrics["revenue"],
            'Cost per Acre': scenario2_metrics["total_costs"],
            'Profit per Acre': scenario2_metrics["profit"],
            'Total Revenue': scenario2_metrics["revenue"] * total_acres,
            'Total Cost': scenario2_metrics["total_costs"] * total_acres,
            'Total Profit': scenario2_metrics["profit"] * total_acres,
            'Cost Breakdown': scenario2_data["costs"]
        }
    }
    
    # Add scenario 3 if it exists
    if scenario3_metrics:
        report_data['Scenario 3'] = {
            'Region': scenario3_metrics["region"],
            'Crop': scenario3_metrics["crop"],
            'Yield per Acre': scenario3_metrics["yield"],
            'Price per Unit': scenario3_metrics["price"],
            'Revenue per Acre': scenario3_metrics["revenue"],
            'Cost per Acre': scenario3_metrics["total_costs"],
            'Profit per Acre': scenario3_metrics["profit"],
            'Total Revenue': scenario3_metrics["revenue"] * total_acres,
            'Total Cost': scenario3_metrics["total_costs"] * total_acres,
            'Total Profit': scenario3_metrics["profit"] * total_acres,
            'Cost Breakdown': scenario3_data["costs"]
        }
    
    # Create comparison table for CSV export
    report_csv = pd.DataFrame({
        'Metric': [
            'Region', 'Crop', 'Yield per Acre', 'Price per Unit',
            'Revenue per Acre ($)', 'Cost per Acre ($)', 'Profit per Acre ($)',
            'Total Revenue ($)', 'Total Cost ($)', 'Total Profit ($)'
        ],
        'Scenario 1': [
            scenario1_metrics["region"], 
            scenario1_metrics["crop"],
            f"{scenario1_metrics['yield']:.1f}",
            f"${scenario1_metrics['price']:.2f}",
            f"${scenario1_metrics['revenue']:.2f}",
            f"${scenario1_metrics['total_costs']:.2f}",
            f"${scenario1_metrics['profit']:.2f}",
            f"${scenario1_metrics['revenue'] * total_acres:.2f}",
            f"${scenario1_metrics['total_costs'] * total_acres:.2f}",
            f"${scenario1_metrics['profit'] * total_acres:.2f}"
        ],
        'Scenario 2': [
            scenario2_metrics["region"],
            scenario2_metrics["crop"],
            f"{scenario2_metrics['yield']:.1f}",
            f"${scenario2_metrics['price']:.2f}",
            f"${scenario2_metrics['revenue']:.2f}",
            f"${scenario2_metrics['total_costs']:.2f}",
            f"${scenario2_metrics['profit']:.2f}",
            f"${scenario2_metrics['revenue'] * total_acres:.2f}",
            f"${scenario2_metrics['total_costs'] * total_acres:.2f}",
            f"${scenario2_metrics['profit'] * total_acres:.2f}"
        ]
    })
    
    # Add scenario 3 if it exists
    if scenario3_metrics:
        report_csv['Scenario 3'] = [
            scenario3_metrics["region"],
            scenario3_metrics["crop"],
            f"{scenario3_metrics['yield']:.1f}",
            f"${scenario3_metrics['price']:.2f}",
            f"${scenario3_metrics['revenue']:.2f}",
            f"${scenario3_metrics['total_costs']:.2f}",
            f"${scenario3_metrics['profit']:.2f}",
            f"${scenario3_metrics['revenue'] * total_acres:.2f}",
            f"${scenario3_metrics['total_costs'] * total_acres:.2f}",
            f"${scenario3_metrics['profit'] * total_acres:.2f}"
        ]

# Add cost breakdown to the report
if analysis_mode == "Single Scenario":
    # For single scenario mode, add costs to the single column
    for item, cost in custom_costs.items():
        new_row = pd.DataFrame({'Metric': [f'Cost: {item} ($/acre)'], 'Value': [f"${cost:,.2f}"]})
        report_csv = pd.concat([report_csv, new_row], ignore_index=True)
else:
    # For comparison mode, add cost breakdowns for all scenarios
    # First, collect all cost items across all scenarios
    all_cost_items = set()
    for scenario_data in [scenario1_data, scenario2_data]:
        all_cost_items.update(scenario_data["costs"].keys())
    if scenario3_data:
        all_cost_items.update(scenario3_data["costs"].keys())
    
    # Now add each cost item for all scenarios
    for item in sorted(all_cost_items):
        cost_data = {
            'Metric': f'Cost: {item} ($/acre)',
            'Scenario 1': f"${scenario1_data['costs'].get(item, 0):,.2f}",
            'Scenario 2': f"${scenario2_data['costs'].get(item, 0):,.2f}"
        }
        
        if scenario3_data:
            cost_data['Scenario 3'] = f"${scenario3_data['costs'].get(item, 0):,.2f}"
        
        new_row = pd.DataFrame([cost_data])
        report_csv = pd.concat([report_csv, new_row], ignore_index=True)

# Convert report to CSV
csv = report_csv.to_csv(index=False)

# Remove duplicate reports heading (we have the main REPORTS heading above)

if analysis_mode == "Single Scenario":
    # For single scenario mode, show all three report options
    # On small screens, these will automatically stack
    # Use a single column on very small screens like iPhone
    smallest_screen = True  # Assume smallest screen for maximum compatibility
    
    if smallest_screen:
        # CSV Button - Full width for very small screens
        st.download_button(
            label="Download CSV Report",
            data=csv,
            file_name="TapGrow_360_analysis.csv",
            mime="text/csv",
            key="csv_download",
            use_container_width=True
        )
        
        # PDF Button
        try:
            pdf_bytes = generate_pdf_report(report_data)
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name="TapGrow_360_analysis.pdf",
                mime="application/pdf",
                key="pdf_download",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
        
        # Excel Button
        try:
            excel_bytes = generate_excel_report(report_data)
            st.download_button(
                label="Download Excel Report",
                data=excel_bytes,
                file_name="TapGrow_360_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="excel_download",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error generating Excel: {e}")
    else:
        # For larger screens, use columns
        dl_col1, dl_col2, dl_col3 = st.columns(3)
        with dl_col1:
            st.download_button(
                label="Download CSV Report",
                data=csv,
                file_name="TapGrow_360_analysis.csv",
                mime="text/csv",
                key="csv_download"
            )
        with dl_col2:
            try:
                pdf_bytes = generate_pdf_report(report_data)
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name="TapGrow_360_analysis.pdf",
                    mime="application/pdf",
                    key="pdf_download"
                )
            except Exception as e:
                st.error(f"Error generating PDF: {e}")
        with dl_col3:
            try:
                excel_bytes = generate_excel_report(report_data)
                st.download_button(
                    label="Download Excel Report",
                    data=excel_bytes,
                    file_name="TapGrow_360_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="excel_download"
                )
            except Exception as e:
                st.error(f"Error generating Excel: {e}")
else:
    # For comparison mode, only show CSV and Excel options as requested
    # Always use the stacked approach for smallest screens
    # CSV Button
    st.download_button(
        label="Download CSV Report",
        data=csv,
        file_name="TapGrow_360_comparison.csv",
        mime="text/csv",
        key="csv_download",
        use_container_width=True
    )
    
    # Excel Button
    try:
        excel_bytes = generate_excel_report(report_data)
        st.download_button(
            label="Download Excel Report",
            data=excel_bytes,
            file_name="TapGrow_360_comparison.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="excel_download",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error generating Excel: {e}")

# Footer with explanations
# Add divider for better visual separation
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<h3 style='font-size: 18px;'>FINANCIAL TERMS EXPLAINED</h3>", unsafe_allow_html=True)
with st.expander("Click to expand definitions"):
    st.markdown("""
    **Revenue per Acre**: The total income generated per acre of land, calculated as (Yield × Price).
    
    **Cost per Acre**: The total expenses required to produce crops on one acre of land.
    
    **Profit per Acre**: The net income per acre after subtracting costs from revenue.
    
    **Total Revenue**: Revenue per acre multiplied by total acres farmed.
    
    **Total Cost**: Cost per acre multiplied by total acres farmed.
    
    **Total Profit**: Profit per acre multiplied by total acres farmed.
    
    **Cost Categories**:
    - **Seed**: Costs for purchasing seeds or planting materials.
    - **Fertilizer**: Costs for nutrients applied to the soil.
    - **Chemicals**: Includes herbicides, pesticides, fungicides, etc.
    - **Insurance**: Crop insurance premiums.
    - **Equipment**: Costs related to machinery usage, maintenance, and depreciation.
    - **Labor**: Wages paid for farm work.
    - **Land**: Rental costs or opportunity costs of land ownership.
    - **Other**: Miscellaneous expenses not falling into other categories.
    """)
