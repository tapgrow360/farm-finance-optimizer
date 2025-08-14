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
    """Load data from an Excel file containing soybeans data."""
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

        if yield_value is None or price_value is None:
            raise ValueError("Could not find yield or price in Excel")

        cost_data = []
        in_direct = False
        in_overhead = False
        for row in df.itertuples():
            if pd.isna(row[1]):
                continue
            cost_name = str(row[1]).strip()
            if cost_name == 'Direct costs':
                in_direct = True
                in_overhead = False
                continue
            if cost_name == 'Overhead costs':
                in_direct = False
                in_overhead = True
                continue
            if cost_name in ['Revenue', 'Return over direct', 'Direct & overhead', 'Net return']:
                continue
            cost_value = parse_dollar_value(row[2])
            category = 'Direct Costs' if in_direct else 'Overhead Costs' if in_overhead else None
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
    """Load data from a CSV file in the AgriCommand2 format."""
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

        if yield_value is None or price_value is None:
            raise ValueError("Could not find yield or price in CSV")

        direct_costs = {}
        overhead_costs = {}
        in_direct = False
        in_overhead = False
        for line in lines:
            parts = line.split(',')
            if len(parts) < 2:
                continue
            cost_name = parts[0].strip()
            if 'Direct costs' in cost_name:
                in_direct = True
                in_overhead = False
                continue
            if 'Overhead costs' in cost_name:
                in_direct = False
                in_overhead = True
                continue
            if 'Net return' in cost_name or 'Return over direct' in cost_name or 'Direct & overhead' in cost_name:
                continue
            cost_value = parse_dollar_value(parts[1])
            if in_direct:
                direct_costs[cost_name] = cost_value
            if in_overhead:
                overhead_costs[cost_name] = cost_value

        cost_data = []
        for name, value in direct_costs.items():
            cost_data.append({'Category': 'Direct Costs', 'Cost_Item': name, 'Cost_Value': value})
        for name, value in overhead_costs.items():
            cost_data.append({'Category': 'Overhead Costs', 'Cost_Item': name, 'Cost_Value': value})

        cost_df = pd.DataFrame(cost_data)

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
        st.error(f"Error loading CSV data: {str(e)}")
        return create_fallback_data()

def create_fallback_data():
    """Create sample data structure to use when CSV loading fails."""
    crop_data = pd.DataFrame({
        'Crop': ['Corn', 'Soybeans', 'Wheat'],
        'Yield': [180, 60, 75],
        'Price': [4.25, 13.50, 7.00]
    })

    cost_data = pd.DataFrame({
        'Category': ['Direct Costs'] * 9 + ['Overhead Costs'] * 5,
        'Cost_Item': ['Rent', 'Seed', 'Fertilizer', 'Chemical', 'Insurance', 'Drying', 'Fuel', 'Repairs', 'Interest', 'Depreciation', 'Utilities', 'Misc overhead', 'Labor', 'Management']
    })

    regional_rows = []
    regions = ['Midwest', 'Great Plains']
    for region in regions:
        for item in cost_data['Cost_Item']:
            base_cost = 50.0  # Sample value
            cost = base_cost if region == 'Midwest' else base_cost * 0.95
            regional_rows.append({
                'Region': region,
                'Cost_Item': item,
                'Cost_Value': cost
            })

    regional_costs = pd.DataFrame(regional_rows)

    return {
        'crop_data': crop_data,
        'cost_data': cost_data,
        'regional_costs': regional_costs
    }

def load_wheat_data(file_path):
    """Load wheat data from Excel file with specific data structure."""
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    try:
        df = pd.read_excel(full_path, header=None)

        yield_value = None
        price_value = None
        straw_revenue = None
        for row in df.itertuples():
            if 'Yield' in str(row[1]):
                yield_value = parse_dollar_value(row[2])
            if 'Price' in str(row[1]):
                price_value = parse_dollar_value(row[2])
            if 'Straw revenue' in str(row[1]):
                straw_revenue = parse_dollar_value(row[2])

        if yield_value is None or price_value is None:
            raise ValueError("Could not find yield or price in Excel")

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

        crop_df = pd.DataFrame({
            'Crop': ['Wheat'],
            'Yield': [yield_value],
            'Price': [price_value],
            'Straw_Revenue': [straw_revenue]
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
            'regional_costs': regional_df
        }
        return result

    except Exception as e:
        st.error(f"Error loading wheat data: {e}")
        return None

def load_data(crop_type):
    """Load data based on the selected crop type."""
    if crop_type == "Corn":
        return load_csv_data("attached_assets/AgriCommand2 Demo - Corn.csv")
    elif crop_type == "Soybeans":
        return load_excel_data("attached_assets/Beans.xlsx")
    elif crop_type == "Wheat":
        return load_wheat_data("attached_assets/Wheat_1753029874668.xlsx")
    else:
        return None
