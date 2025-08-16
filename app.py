# app.py
# This is a sample Streamlit app to demonstrate the basic structure.
# You will need to adapt this code to fit your specific FarmFinanceOptimizer logic.

import streamlit as st
import pandas as pd
import numpy as np

# --- App Title and Introduction ---
st.set_page_config(page_title="Farm Finance Optimizer", layout="wide")
st.title("🌾 Farm Finance Optimizer")
st.markdown("""
Welcome to the Farm Finance Optimizer! This tool helps you analyze different crop scenarios to
maximize your profitability. Use the sidebar on the left to input your data and see the results.
""")

# --- Sidebar Inputs ---
st.sidebar.header("Input Financial Data")
# Use a number input for financial values
total_land = st.sidebar.number_input(
    "Total available land (acres)",
    min_value=1.0,
    value=100.0,
    step=10.0,
    help="Enter the total acres of land you have available for planting."
)

# Use a text input for string values
farm_location = st.sidebar.text_input(
    "Farm Location",
    "Midwest, USA",
    help="Enter the general location of your farm."
)

# Use a checkbox for a yes/no option
is_organic = st.sidebar.checkbox(
    "Is a portion of your farm organic?",
    help="Check this if you plan to allocate some land for organic crops."
)

# Use a multi-select for choosing crops
crop_options = ["Corn", "Soybeans", "Wheat", "Barley"]
selected_crops = st.sidebar.multiselect(
    "Select Crops for Analysis",
    options=crop_options,
    default=["Corn", "Soybeans"],
    help="Choose the crops you want to include in the optimization."
)

st.sidebar.markdown("---")
st.sidebar.subheader("Crop Details")

# Create a dictionary to hold the input data for each selected crop
crop_data = {}
for crop in selected_crops:
    st.sidebar.markdown(f"**{crop}**")
    revenue_per_acre = st.sidebar.number_input(
        f"Revenue per acre for {crop} ($)",
        min_value=0.0,
        value=500.0,
        step=50.0
    )
    cost_per_acre = st.sidebar.number_input(
        f"Cost per acre for {crop} ($)",
        min_value=0.0,
        value=300.0,
        step=20.0
    )
    crop_data[crop] = {
        'Revenue per Acre': revenue_per_acre,
        'Cost per Acre': cost_per_acre,
    }

# --- Main Content: Display Results ---
st.header("Financial Analysis Results")

if not selected_crops:
    st.warning("Please select at least one crop to perform the analysis.")
else:
    # Convert crop data to a DataFrame for easier handling and display
    df_crop_data = pd.DataFrame.from_dict(crop_data, orient='index')

    # Calculate Profit per Acre and add it to the DataFrame
    df_crop_data['Profit per Acre'] = df_crop_data['Revenue per Acre'] - df_crop_data['Cost per Acre']

    # Display the input data in a table
    st.subheader("Input Data Summary")
    st.dataframe(df_crop_data)

    # Simple optimization logic:
    # Assuming the app optimizes by allocating all land to the most profitable crop.
    if not df_crop_data.empty:
        most_profitable_crop = df_crop_data['Profit per Acre'].idxmax()
        profit_per_acre = df_crop_data.loc[most_profitable_crop, 'Profit per Acre']
        max_profit = total_land * profit_per_acre

        st.subheader("Optimization Recommendation")
        st.info(
            f"Based on your inputs, the most profitable single crop is **{most_profitable_crop}** "
            f"with a profit of **${profit_per_acre:.2f} per acre**."
        )

        st.success(
            f"If you allocate all **{total_land:.0f} acres** to **{most_profitable_crop}**, "
            f"your potential total profit is **${max_profit:.2f}**."
        )

        st.balloons()

    # --- Data Visualization ---
    st.header("Visualizing Profitability")
    if not df_crop_data.empty:
        # Sort the data for a better-looking chart
        df_sorted = df_crop_data.sort_values('Profit per Acre', ascending=False)
        st.bar_chart(df_sorted[['Profit per Acre']])

    # --- Additional Info based on a condition ---
    if is_organic:
        st.markdown("---")
        st.subheader("Organic Farming Considerations")
        st.write("You selected that a portion of your farm is organic. This version of the app doesn't yet factor in the specific higher revenues or costs of organic crops, but you can enter those values manually above to see the difference.")
        st.write("Consider adding more complex optimization logic in the future to handle multiple crop allocations.")
