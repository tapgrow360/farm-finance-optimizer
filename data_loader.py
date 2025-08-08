import pandas as pd
import os
import streamlit as st
import openpyxl

def parse_dollar_value(value):
    """Convert dollar string to float value."""
    if isinstance(value, str) and '$' in value:
        return float(value.replace('$', '').replace(',', '').strip())
    return value

def load_excel_data(file_path):
    """
    Load data from an Excel file containing soybeans data.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        dict: A dictionary containing dataframes for different data categories
    """
    try:
        df = pd.read_excel(file_path, sheet_name='Sheet1')
        
        # Extract basic information
        yield_value = df.iloc[0, 1]  # Yield is in row 0, column 1
        price_value = df.iloc[1, 1]  # Price is in row 1, column 1
        
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
            if pd.notna(df.iloc[row_idx, 1]):  # Check if value exists
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
            'Cost_Value': 0.0  # Not specified in the Excel, defaulting to 0
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
    # First, read the raw data
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Parse the crop name
        crop_name = lines[0].split(',')[0].strip()
        
        # Extract yield and price information - set corn yield to 185
        yield_value = 185.0 if 'corn' in crop_name.lower() else float(lines[1].split(',')[1].strip())
        price_value = parse_dollar_value(lines[2].split(',')[1].strip())
        
        # Extract cost categories
        direct_costs = {}
        overhead_costs = {}
        
        # Process direct costs
        direct_cost_lines = lines[6:16]  # Rent through Interest
        for line in direct_cost_lines:
            parts = line.split(',')
            if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
                cost_name = parts[0].strip()
                # Skip total rows (they will be calculated from individual costs)
                if cost_name.lower() == "direct costs":
                    continue
                cost_value = parse_dollar_value(parts[1].strip())
                direct_costs[cost_name] = cost_value
                
        # Process overhead costs
        overhead_cost_lines = lines[18:24]  # Depreciation through Management
        for line in overhead_cost_lines:
            parts = line.split(',')
            if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
                cost_name = parts[0].strip()
                # Skip total rows (they will be calculated from individual costs)
                if cost_name.lower() == "overhead costs":
                    continue
                cost_value = parse_dollar_value(parts[1].strip())
                overhead_costs[cost_name] = cost_value
        
        # Create crop data with updated yield default for corn
        default_yield = 185.0 if crop_name == 'Corn' else yield_value
        crop_data = pd.DataFrame({
            'Crop': [crop_name],
            'Yield': [default_yield],
            'Price': [price_value]
        })
        
        # Create cost category data
        cost_categories = []
        for name in direct_costs.keys():
            cost_categories.append({'Category': 'Direct Costs', 'Cost_Item': name})
        for name in overhead_costs.keys():
            cost_categories.append({'Category': 'Overhead Costs', 'Cost_Item': name})
        
        cost_data = pd.DataFrame(cost_categories)
        
        # Create regional cost data (using actual values from CSV)
        regional_costs = []
        for name, value in direct_costs.items():
            regional_costs.append({
                'Region': 'Midwest',
                'Cost_Item': name,
                'Cost_Value': value
            })
        for name, value in overhead_costs.items():
            regional_costs.append({
                'Region': 'Midwest',
                'Cost_Item': name,
                'Cost_Value': value
            })
        
        regional_costs_df = pd.DataFrame(regional_costs)
        
        # Additional regions can be synthetic, with variations based on the original data
        additional_regions = ['Great Plains']
        for region in additional_regions:
            for name, value in direct_costs.items():
                # Great Plains region has a 5% lower cost structure
                modified_value = value * 0.95  # 5% lower
                    
                regional_costs.append({
                    'Region': region,
                    'Cost_Item': name,
                    'Cost_Value': modified_value
                })
            
            for name, value in overhead_costs.items():
                # Great Plains region has a 5% lower cost structure
                modified_value = value * 0.95  # 5% lower
                    
                regional_costs.append({
                    'Region': region,
                    'Cost_Item': name,
                    'Cost_Value': modified_value
                })
        
        regional_costs_df = pd.DataFrame(regional_costs)
        
        # Add additional crops with variations for a more useful application
        additional_crops = [
            {
                'Crop': 'Soybeans',
                'Avg_Yield': 60,
                'Current_Price': 13.50
            },
            {
                'Crop': 'Wheat',
                'Avg_Yield': 75,
                'Current_Price': 7.00
            }
        ]
        
        for crop in additional_crops:
            crop_data = pd.concat([crop_data, pd.DataFrame([crop])], ignore_index=True)
        
        return {
            'crop_data': crop_data,
            'cost_data': cost_data,
            'regional_costs': regional_costs_df
        }
        
    except Exception as e:
        st.error(f"Error loading CSV data: {str(e)}")
        return create_fallback_data()

def create_fallback_data():
    """
    Create sample data structure to use when CSV loading fails.
    
    Returns:
        dict: A dictionary containing sample dataframes for different categories
    """
    # Sample crop data
    crop_data = pd.DataFrame({
        'Crop': ['Corn', 'Soybeans', 'Wheat'],
        'Avg_Yield': [180, 60, 75],
        'Current_Price': [4.25, 13.50, 7.00]
    })
    
    # Sample cost categories
    cost_data = pd.DataFrame({
        'Category': ['Direct Costs', 'Direct Costs', 'Direct Costs', 'Direct Costs', 
                    'Direct Costs', 'Direct Costs', 'Direct Costs', 'Direct Costs', 
                    'Direct Costs', 'Overhead Costs', 'Overhead Costs', 'Overhead Costs',
                    'Overhead Costs', 'Overhead Costs'],
        'Item': ['Rent', 'Seed', 'Fertilizer', 'Chemical', 'Insurance',
                'Drying', 'Fuel', 'Repairs', 'Interest',
                'Depreciation', 'Utilities', 'Misc overhead', 'Labor', 'Management']
    })
    
    # Sample regional cost data
    regions = ['Midwest', 'Great Plains']
    cost_items = cost_data['Item'].tolist()
    
    regional_rows = []
    for region in regions:
        for item in cost_items:
            # Generate a reasonable cost based on the item
            if item == 'Rent':
                base_cost = 190.0
            elif item == 'Seed':
                base_cost = 118.0
            elif item == 'Fertilizer':
                base_cost = 152.64
            elif item == 'Chemical':
                base_cost = 50.41
            elif item == 'Insurance':
                base_cost = 16.20
            elif item == 'Depreciation':
                base_cost = 75.0
            elif item == 'Labor':
                base_cost = 10.0
            elif item == 'Management':
                base_cost = 50.0
            elif item == 'Drying':
                base_cost = 10.0
            elif item == 'Fuel':
                base_cost = 20.0
            elif item == 'Repairs':
                base_cost = 30.0
            elif item == 'Interest':
                base_cost = 12.0
            elif item == 'Utilities':
                base_cost = 20.0
            elif item == 'Misc overhead':
                base_cost = 27.0
            else:
                base_cost = 25.0
            
            # Apply regional variations
            if region == 'Great Plains':
                cost = base_cost * 0.95  # 5% lower for Great Plains
            else:  # Midwest
                cost = base_cost
                
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
    """
    Load wheat data from Excel file with specific data structure.
    
    Args:
        file_path (str): Path to the wheat Excel file
        
    Returns:
        dict: A dictionary containing dataframes for different data categories
    """
    try:
        # Read the Excel file
        df = pd.read_excel(file_path, header=None)
        
        # Extract yield and price information
        yield_value = df.iloc[1, 1]  # Row 1, column 1
        price_value = df.iloc[2, 1]  # Row 2, column 1
        straw_revenue = df.iloc[3, 1]  # Row 3, column 1 - Straw revenue
        
        # Define the cost mapping for wheat
        cost_mapping = {
            'Rent': 6,
            'Seed': 7,
            'Fertilizer': 8,
            'Chemical': 9,
            'Insurance': 10,
            'Fuel': 12,
            'Repairs': 13,
            'Interest': 14,
            'Depreciation': 18,
            'Utilities': 19,
            'Misc overhead': 20,
            'Labor': 21,
            'Management': 22
        }
        
        # Create cost entries
        cost_data = []
        for cost_name, row_idx in cost_mapping.items():
            if pd.notna(df.iloc[row_idx, 1]):  # Check if value exists
                cost_value = df.iloc[row_idx, 1]
                # Determine category
                if cost_name in ['Rent', 'Seed', 'Fertilizer', 'Chemical', 'Insurance', 'Fuel', 'Repairs', 'Interest']:
                    category = 'Direct Costs'
                else:
                    category = 'Overhead Costs'
                
                cost_data.append({
                    'Category': category,
                    'Cost_Item': cost_name,
                    'Cost_Value': cost_value
                })
        
        # Create DataFrames
        cost_df = pd.DataFrame(cost_data)
        
        # Create crop data DataFrame
        crop_df = pd.DataFrame({
            'Crop': ['Wheat'],
            'Yield': [yield_value],
            'Price': [price_value],
            'Straw_Revenue': [straw_revenue]
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
        
        # Create the result structure
        result = {
            'crop_data': crop_df,
            'cost_data': cost_df,
            'regional_costs': regional_df
        }
        
        return result
        
    except Exception as e:
        print(f"Error loading wheat data: {e}")
        return None

def load_data(crop_type):
    """
    Load data based on the selected crop type.
    
    Args:
        crop_type (str): Type of crop ('Corn', 'Soybeans', or 'Wheat')
        
    Returns:
        dict: A dictionary containing dataframes for different data categories
    """
    if crop_type == "Corn":
        return load_csv_data("attached_assets/AgriCommand2 Demo - Corn.csv")
    elif crop_type == "Soybeans":
        return load_excel_data("attached_assets/Beans.xlsx")
    elif crop_type == "Wheat":
        return load_wheat_data("attached_assets/Wheat_1753029874668.xlsx")
    else:
        return None