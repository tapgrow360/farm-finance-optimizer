import pandas as pd
import os
import streamlit as st
import openpyxl

def parse_dollar_value(value):
    """Convert dollar string to float value."""
    if isinstance(value, str) and '$' in value:
        return float(value.replace('$', '').replace(',', '').strip())
    try:
        return float(value)
    except ValueError:
        return 0.0  # Default to 0 if conversion fails

def load_excel_data(file_path):
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        df = pd.read_excel(full_path, sheet_name='Sheet1')
        
        # Dynamic extraction for yield and price
        yield_value = None
        price_value = None
        for row in df.itertuples():
            if 'Yield' in str(row[1]):
                yield_value = row[2]
            if 'Price' in str(row[1]):
                price_value = row[2]
        
        if yield_value is None or price_value is None:
            raise ValueError("Could not find yield or price in Excel")
        
        # Dynamic extraction for costs
        cost_data = []
        category = None
        for row in df.itertuples():
            cost_name = str(row[1]).strip()
            if cost_name == 'Direct costs':
                category = 'Direct Costs'
                continue
            if cost_name == 'Overhead costs':
                category = 'Overhead Costs'
                continue
            if cost_name == '' or pd.isna(row[2]):
                continue
            cost_value = parse_dollar_value(row[2])
            cost_data.append({
                'Category': category,
                'Cost_Item': cost_name,
                'Cost_Value': cost_value
            })
        
        cost_df = pd.DataFrame(cost_data)
        
        # Create crop data DataFrame
        crop_df = pd.DataFrame({
            'Crop': ['Soybeans'],
            'Yield': [yield_value],
            'Price': [price_value]
        })
        
        # Create regional costs
        regional_data = []
        for _, cost_row in cost_df.iterrows():
            base_cost = cost_row['Cost_Value']
            regional_data.append({
                'Region': 'Midwest',
                'Cost_Item': cost_row['Cost_Item'],
                'Cost_Value': base_cost
            })
            regional_data.append({
                'Region': 'Great Plains',
                'Cost_Item': cost_row['Cost_Item'],
                'Cost_Value': base_cost * 0.95
            })
        
        regional_df = pd.DataFrame(regional_data)
        
        result = {
            'cost_data': cost_df,
            'crop_data': crop_df,
            'regional_costs': regional_df,
            'crop_name': 'Soybeans',
            'yield_value': yield_value,
            'price_value': price_value
        }
        return result
        
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return None

def load_csv_data(file_path):
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        with open(full_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        # Extract crop name, yield, price
        crop_name = lines[0].split(',')[0].strip()
        yield_value = None
        price_value = None
        for line in lines:
            parts = line.split(',')
            if parts[0].strip().lower() == 'yield':
                yield_value = float(parts[1].strip())
            if parts[0].strip().lower() == 'price':
                price_value = parse_dollar_value(parts[1].strip())
        
        if yield_value is None or price_value is None:
            raise ValueError("Could not find yield or price in CSV")
        
        # Extract costs dynamically
        direct_costs = {}
        overhead_costs = {}
        in_direct = False
        in_overhead = False
        for line in lines:
            parts = line.split(',')
            if len(parts) < 2 or not parts[0].strip():
                continue
            cost_name = parts[0].strip()
            if cost_name.lower() == 'direct costs':
                in_direct = True
                in_overhead = False
                continue
            if cost_name.lower() == 'overhead costs':
                in_direct = False
                in_overhead = True
                continue
            if cost_name.lower() == 'net return' or cost_name == '':
                break
            
            cost_value = parse_dollar_value(parts[1].strip())
            if in_direct:
                direct_costs[cost_name] = cost_value
            if in_overhead:
                overhead_costs[cost_name] = cost_value
        
        # Create crop data
        crop_df = pd.DataFrame({
            'Crop': [crop_name],
            'Yield': [yield_value],
            'Price': [price_value]
        })
        
        # Create cost categories
        cost_categories = []
        for name in direct_costs.keys():
            cost_categories.append({'Category': 'Direct Costs', 'Cost_Item': name})
        for name in overhead_costs.keys():
            cost_categories.append({'Category': 'Overhead Costs', 'Cost_Item': name})
        
        cost_data = pd.DataFrame(cost_categories)
        
        # Create regional cost data
        regional_costs = []
        for name, value in direct_costs.items():
            regional
