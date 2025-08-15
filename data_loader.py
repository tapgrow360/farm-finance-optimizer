import pandas as pd
import os
import streamlit as st
import openpyxl

def parse_dollar_value(value):
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
            lines = f.readlines()
        
        crop_name = lines[0].split(',')[0].strip()
        yield_value = None
        price_value = None
        for line in lines:
            parts = line.split(',')
            if len(parts) < 2:
                continue
            if 'Yield' in parts[0]:
                yield_value = parse_dollar_value(parts[1])
            if 'Price' in parts[0]:
                price_value = parse_dollar_value(parts[1])

        direct_costs = {}
        overhead_costs = {}
        in_direct = True  # Start in direct costs after revenue
        for line in lines:
            parts = line.split(',')
            if len(parts) < 2:
                continue
            cost_name = parts[0].strip()
            if 'Revenue' in cost_name:
                continue
            if 'Direct costs' in cost_name or 'Return over direct' in cost_name:
                in_direct = False
                in_overhead = True
                continue
            if 'Overhead costs' in cost_name or 'Direct & overhead' in cost_name or 'Net return' in cost_name:
                continue
            cost_value = parse_dollar_value(parts[1])
            if in_direct:
                direct_costs[cost_name] = cost_value
            else:
                overhead_costs[cost_name] = cost_value

        cost_df = pd.DataFrame([{'Category': 'Direct Costs', 'Cost_Item': k, 'Cost_Value': v} for k, v in direct_costs.items()] + [{'Category': 'Overhead Costs', 'Cost_Item': k, 'Cost_Value': v} for k, v in overhead_costs.items()])

        crop_df = pd.DataFrame({
            'Crop': [crop_name],
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
            'crop_name': crop_name,
            'yield_value': yield_value,
            'price_value': price_value
        }
        return result

    except Exception as e:
        st.error(f"Error loading CSV data: {e}")
        return None

# Add the other functions (load_wheat_data, load_data, etc.) as before, with similar dynamic fixes if needed.
