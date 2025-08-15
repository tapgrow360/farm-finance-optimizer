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
        return 0.0

def load_excel_data(file_path):
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        df = pd.read_excel(full_path, sheet_name='Sheet1')
        
        yield_value = None
        price_value = None
        for row in df.itertuples():
            if pd.isna(row[1]):
                continue
            if 'Yield' in str(row[1]):
                yield_value = parse_dollar_value(row[2])
            if 'Price' in str(row[1]):
                price_value = parse_dollar_value(row[2])
        
        cost_data = []
        category = None
        for row in df.itertuples():
            if pd.isna(row[1]):
                continue
            cost_name = str(row[1]).strip()
            if 'Direct costs' in cost_name:
                category = 'Direct Costs'
                continue
            if 'Overhead costs' in cost_name:
                category = 'Overhead Costs'
                continue
            if 'Revenue' in cost_name or 'Return over direct' in cost_name or 'Direct & overhead' in cost_name or 'Net return' in cost_name:
                continue
            cost_value = parse_dollar_value(row[2])
            if category:
                cost_data.append({
                    'Category': category,
                    'Cost_Item': cost_name,
                    'Cost_Value': cost_value
                })
        
        cost_df = pd.DataFrame(cost_data)
        crop_df = pd.DataFrame({
            'Crop': ['Soybeans'],
            'Yield': [yield_value],
            'Price': [price_value]
        })
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
        
        crop_name = lines[0].split(',')[0].strip()
        yield_value = None
        price_value = None
        for line in lines:
            parts = line.split(',')
            if parts[0].strip().lower() == 'yield':
                yield_value = float(parts[1].strip())
            if parts[0].strip().lower() == 'price':
                price_value = parse_dollar_value(parts[1].strip())
        
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
        
        cost_data = pd.DataFrame({
            'Category': ['Direct Costs'] * len(direct_costs) + ['Overhead Costs'] * len(overhead_costs),
            'Cost_Item': list(direct_costs.keys()) + list(overhead_costs.keys())
        })

        crop_df = pd.DataFrame({
            'Crop': [crop_name],
            'Yield': [yield_value],
            'Price': [price_value]
        })

        regional_data = []
        for name, value in direct_costs.items():
            regional_data.append({'Region': 'Midwest', 'Cost_Item': name, 'Cost_Value': value})
        for name, value in overhead_costs.items():
            regional_data.append({'Region': 'Midwest', 'Cost_Item': name, 'Cost_Value': value})
        
        regional_costs_df = pd.DataFrame(regional_data)
        
        additional_regions = ['Great Plains']
        for region in additional_regions:
            for name, value in direct_costs.items():
                modified_value = value * 0.95
                regional_data.append({'Region': region, 'Cost_Item': name, 'Cost_Value': modified_value})
            for name, value in overhead_costs.items():
                modified_value = value * 0.95
                regional_data.append({'Region': region, 'Cost_Item': name, 'Cost_Value': modified_value})
        
        regional_costs_df = pd.DataFrame(regional_data)
        
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
        st.error(f"Error loading CSV data: {e}")
        return create_fallback_data()

def create_fallback_data():
    # Your original fallback code

def load_wheat_data(file_path):
    # Your original load_wheat_data code with similar dynamic fixes if needed

def load_data(crop_type):
    # Your original load_data code
