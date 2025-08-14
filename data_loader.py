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
        return 0.0  # Default to 0 if conversion fails, to avoid errors

def load_excel_data(file_path):
    """
    Load data from an Excel file containing soybeans data.
   
    Args:
        file_path (str): Path to the Excel file
    
    Returns:
        dict: A dictionary containing dataframes for different data categories
    """
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        df = pd.read_excel(full_path, sheet_name='Sheet1')
       
        # Extract basic information
        yield_value = df.iloc[0, 1] # Yield is in row 0, column 1
        price_value = df.iloc[1, 1] # Price is in row 1, column 1
       
        # Extract costs from the data
        cost_data = []
       
        # Map the Excel data to our cost structure
        cost_mapping = {
            'Rent': 5,
            'Seed': 6,
            'Chemical': 8,
            'Insurance': 9,
            'Fuel': 11,
            'Repairs': 12,
            'Interest': 13,
            'Depreciation': 17,
            'Utilities': 18,
            'Misc overhead': 19,
            'Labor': 20,
            'Management': 21
        }
       
        # Create cost entries
        for cost_name, row_idx in cost_mapping.items():
            if pd.notna(df.iloc[row_idx, 1]): # Check if value exists
                cost_value = df.iloc[row_idx, 1]
                # Determine category
                if cost_name in ['Rent', 'Seed', 'Chemical', 'Insurance', 'Fuel', 'Repairs', 'Interest']:
                    category = 'Direct Costs'
                else:
                    category = 'Overhead Costs'
                
                cost_data.append({
                    'Category': category,
                    'Cost_Item': cost_name,
                    'Cost_Value': cost_value
                })
       
        # Skip Fertilizer for soybeans (nitrogen-fixing crop doesn't need fertilizer)
       
        # Handle Drying (appears to be 0 or not specified)
        cost_data.append({
            'Category': 'Direct Costs',
            'Cost_Item': 'Drying',
            'Cost_Value': 0.0 # Not specified in the Excel, defaulting to 0
        })
       
        # Create DataFrame
        cost_df = pd.DataFrame(cost_data)
       
        # Create crop data DataFrame
        crop_df = pd.DataFrame({
            'Crop': ['Soybeans'],
            'Yield': [yield_value],
            'Price': [price_value]
        })
       
        # Create regional costs DataFrame with individual cost items
        regional_data = []
        for _, cost_row in cost_df.iterrows():
            cost_item = cost_row['Cost_Item']
            base_cost = cost_row['Cost_Value']
           
            # Add Midwest costs (base values)
            regional_data.append({
                'Region': 'Midwest',
                'Cost_Item': cost_item,
                'Cost_Value': base_cost
            })
           
            # Add Great Plains costs (5% lower)
            regional_data.append({
                'Region': 'Great Plains',
                'Cost_Item': cost_item,
                'Cost_Value': base_cost * 0.95
            })
       
        regional_df = pd.DataFrame(regional_data)
       
        # Create the result structure matching CSV data
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
    """
    Load data from a CSV file in the AgriCommand2 format.
   
    Args:
        file_path (str): Path to the CSV file
    
    Returns:
        dict: A dictionary containing dataframes for different data categories
    """
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        with open(full_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]  # Remove blank lines
        
        # Extract crop name from first non-blank line
        crop_name = lines[0].split(',')[0].strip()
        
        # Find lines for yield and price dynamically
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
            regional_costs.append({'Region': 'Midwest', 'Cost_Item': name, 'Cost_Value': value})
        for name, value in overhead_costs.items():
            regional_costs.append({'Region': 'Midwest', 'Cost_Item': name, 'Cost_Value': value})
        
        regional_costs_df = pd.DataFrame(regional_costs)
        
        additional_regions = ['Great Plains']
        for region in additional_regions:
            for name, value in direct_costs.items():
                modified_value = value * 0.95
                regional_costs.append({'Region': region, 'Cost_Item': name, 'Cost_Value': modified_value})
            for name, value in overhead_costs.items():
                modified_value = value * 0.95
                regional_costs.append({'Region': region, 'Cost_Item': name, 'Cost_Value': modified_value})
        
        regional_costs_df = pd.DataFrame(regional_costs)
        
        additional_crops = [
            {'Crop': 'Soybeans', 'Avg_Yield': 60, 'Current_Price': 13.50},
            {'Crop': 'Wheat', 'Avg_Yield': 75, 'Current_Price': 7.00}
        ]
        
        for crop in additional_crops:
            crop_df = pd.concat([crop_df, pd.DataFrame([crop])], ignore_index=True)
        
        return {
            'crop_data': crop_df,
            'cost_data': cost_data,
            'regional_costs': regional_costs_df
        }
        
    except Exception as e:
        st.error(f"Error loading CSV data: {str(e)}")
        return create_fallback_data()

# (The rest of the code remains the same: create_fallback_data, load_wheat_data, load_data)
