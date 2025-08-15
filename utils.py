import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
import streamlit as st
import os
import io
import datetime
import jinja2
from reportlab.pdfgen import canvas
import xlsxwriter
# Existing imports...
from reportlab.pdfgen import canvas  # Example
import xlsxwriter  # Example
from weasyprint import HTML  # New line
def create_fallback_data():
    """Create sample data structure to use when Google Sheets access fails.
    This provides representative data for the application to function."""
    # Add your fallback code here if needed
    pass
    
    "Returns:"
        dict: A dictionary containing sample dataframes for different categories
    """
    # Sample crop data
    crop_data = pd.DataFrame({
        'Crop': ['Corn', 'Soybeans', 'Wheat', 'Cotton', 'Rice'],
        'Avg_Yield': [180, 60, 70, 1000, 7500],
        'Current_Price': [5.20, 13.50, 7.00, 0.85, 0.18]
    })
    
    # Sample cost categories
    cost_data = pd.DataFrame({
        'Category': ['Seed', 'Seed', 'Fertilizer', 'Fertilizer', 'Chemicals', 
                    'Chemicals', 'Equipment', 'Labor', 'Land', 'Insurance'],
        'Item': ['Crop Seed', 'Treatment', 'Nitrogen', 'Phosphorus', 'Herbicide', 
                'Pesticide', 'Machinery', 'Hired Labor', 'Rent', 'Crop Insurance']
    })
    
    # Sample regional cost data
    regions = ['Midwest', 'Northeast', 'South', 'West']
    cost_items = cost_data['Item'].tolist()
    
    regional_rows = []
    for region in regions:
        for item in cost_items:
            # Generate a reasonable cost based on the item
            if 'Seed' in item:
                cost = 80.0 + (10 * (regions.index(region) + 1))
            elif 'Fertilizer' in item or 'Nitrogen' in item or 'Phosphorus' in item:
                cost = 60.0 + (8 * (regions.index(region) + 1))
            elif 'Chemical' in item or 'Herbicide' in item or 'Pesticide' in item:
                cost = 40.0 + (5 * (regions.index(region) + 1))
            elif 'Equipment' in item or 'Machinery' in item:
                cost = 70.0 + (10 * (regions.index(region) + 1))
            elif 'Labor' in item:
                cost = 50.0 + (15 * (regions.index(region) + 1))
            elif 'Land' in item or 'Rent' in item:
                cost = 200.0 + (50 * (regions.index(region) + 1))
            elif 'Insurance' in item:
                cost = 30.0 + (5 * (regions.index(region) + 1))
            else:
                cost = 25.0 + (5 * (regions.index(region) + 1))
            
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

def fetch_sheet_data(sheet_id):
    """
    Fetch data from a Google Sheet using the sheet ID.
    
    This function will try different authentication methods:
    print("1. First, try to use Streamlit's secrets mechanism")
    2. If that fails, try to use local credentials (for development)
    3. If all fails, use public access (if the sheet is public)
    
    Args:
        sheet_id (str): The ID of the Google Sheet
        
    Returns:
        dict: A dictionary containing dataframes for different sheets
    """
    try:
        # Try using Streamlit's secrets mechanism
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            gc = gspread.authorize(credentials)
        else:
            # Try to access the sheet directly (for public sheets or fallback)
            try:
                # Try service account first (for development environment)
                gc = gspread.service_account()
            except Exception as service_account_error:
                st.warning("Using anonymous access - some features may be limited. For full functionality, please set up Google API credentials.")
                # For public sheets or anonymous access
                gc = gspread.Client(None)
            
        # Open the spreadsheet - attempt public access
        try:
            sheet = gc.open_by_key(sheet_id)
            # Get all worksheets
            worksheets = sheet.worksheets()
        except Exception as sheet_error:
            st.error(f"Unable to access the Google Sheet: {str(sheet_error)}")
            # Use fallback data structure since we can't access the real sheet
            return create_fallback_data()
        
        data_dict = {}
        
        # Process each worksheet
        for worksheet in worksheets:
            # Get the title and data
            title = worksheet.title.lower().replace(" ", "_")
            data = worksheet.get_all_records()
            
            # Convert to DataFrame
            if data:
                df = pd.DataFrame(data)
                data_dict[title] = df
        
        # Process the main data tabs we need
        
        # 1. Create crop_data from appropriate tab
        if 'crop_info' in data_dict:
            data_dict['crop_data'] = data_dict['crop_info']
        elif 'crops' in data_dict:
            data_dict['crop_data'] = data_dict['crops']
        
        # 2. Create cost_data from appropriate tab
        if 'cost_categories' in data_dict:
            data_dict['cost_data'] = data_dict['cost_categories']
        elif 'costs' in data_dict:
            data_dict['cost_data'] = data_dict['costs']
        
        # 3. Create regional_costs from appropriate tab
        if 'regional_costs' in data_dict:
            pass  # Already named correctly
        elif 'regional_data' in data_dict:
            data_dict['regional_costs'] = data_dict['regional_data']
        
        # Ensure we have the minimum required datasets
        required_keys = ['crop_data', 'cost_data', 'regional_costs']
        missing_keys = [key for key in required_keys if key not in data_dict]
        
        if missing_keys:
            # If we're missing some data, try to create synthetic versions based on what we have
            if 'crop_data' not in data_dict and len(data_dict) > 0:
                # Create a simple crop data from any available sheet
                sample_df = next(iter(data_dict.values()))
                data_dict['crop_data'] = pd.DataFrame({
                    'Crop': ['Corn', 'Soybeans', 'Wheat'],
                    'Avg_Yield': [180, 60, 70],
                    'Current_Price': [5.20, 13.50, 7.00]
                })
            
            if 'cost_data' not in data_dict:
                # Create a simple cost category structure
                data_dict['cost_data'] = pd.DataFrame({
                    'Category': ['Seed', 'Seed', 'Fertilizer', 'Fertilizer', 'Chemicals', 
                                'Equipment', 'Labor', 'Land', 'Insurance'],
                    'Item': ['Corn Seed', 'Treatment', 'Nitrogen', 'Phosphorus', 'Herbicide', 
                            'Machinery', 'Hired Labor', 'Rent', 'Crop Insurance']
                })
            
            if 'regional_costs' not in data_dict:
                # Create simple regional cost data
                cost_items = data_dict['cost_data']['Item'].tolist() if 'cost_data' in data_dict else [
                    'Corn Seed', 'Treatment', 'Nitrogen', 'Phosphorus', 'Herbicide', 
                    'Machinery', 'Hired Labor', 'Rent', 'Crop Insurance'
                ]
                
                regions = ['Midwest', 'Northeast', 'South', 'West']
                rows = []
                
                for region in regions:
                    for item in cost_items:
                        # Generate a reasonable cost based on the item
                        if 'Seed' in item:
                            cost = 80.0 + (10 * (regions.index(region) + 1))
                        elif 'Fertilizer' in item or 'Nitrogen' in item or 'Phosphorus' in item:
                            cost = 60.0 + (8 * (regions.index(region) + 1))
                        elif 'Chemical' in item or 'Herbicide' in item:
                            cost = 40.0 + (5 * (regions.index(region) + 1))
                        elif 'Equipment' in item or 'Machinery' in item:
                            cost = 70.0 + (10 * (regions.index(region) + 1))
                        elif 'Labor' in item:
                            cost = 50.0 + (15 * (regions.index(region) + 1))
                        elif 'Land' in item or 'Rent' in item:
                            cost = 200.0 + (50 * (regions.index(region) + 1))
                        elif 'Insurance' in item:
                            cost = 30.0 + (5 * (regions.index(region) + 1))
                        else:
                            cost = 25.0 + (5 * (regions.index(region) + 1))
                        
                        rows.append({
                            'Region': region,
                            'Cost_Item': item,
                            'Cost_Value': cost
                        })
                
                data_dict['regional_costs'] = pd.DataFrame(rows)
            
        return data_dict
        
    except Exception as e:
        # If all else fails, raise the exception
        raise Exception(f"Failed to fetch Google Sheet data: {str(e)}")


def calculate_profit_per_acre(yield_per_acre, price_per_unit, costs_per_acre):
    """
    Calculate the profit per acre based on yield, price, and costs.
    
    Args:
        yield_per_acre (float): Yield per acre in units
        price_per_unit (float): Price per unit in dollars
        costs_per_acre (float): Total costs per acre in dollars
        
    Returns:
        float: Profit per acre in dollars
    """
    revenue_per_acre = yield_per_acre * price_per_unit
    profit_per_acre = revenue_per_acre - costs_per_acre
    return profit_per_acre


def identify_optimization_areas(custom_costs, category_totals, current_profit):
    """
    Identify areas where input reductions can potentially be made.
    
    Args:
        custom_costs (dict): Dictionary of cost items and their values
        category_totals (dict): Dictionary of category totals
        current_profit (float): Current profit per acre
        
    Returns:
        dict: Dictionary with optimization suggestions by category
    """
    optimization_areas = {}
    
    # Filter out Overhead Costs from the categories
    filtered_categories = {category: total for category, total in category_totals.items() 
                          if category != "Overhead Costs"}
    
    # Calculate the total of filtered costs (excluding overhead costs)
    filtered_total = sum(filtered_categories.values())
    
    # Sort categories by cost (highest first)
    sorted_categories = sorted(filtered_categories.items(), key=lambda x: x[1], reverse=True)
    
    # Analyze top cost categories
    for category, total in sorted_categories[:3]:  # Focus on top 3 categories
        percentage_of_total = total / filtered_total * 100 if filtered_total > 0 else 0
        
  optimization_areas["Fertilizer"] = {
    "description": f"""
   optimization_areas["Fertilizer"] = {
    "description": "Fertilizer costs account for {:.1f}% of your total input costs. Consider soil testing to optimize application rates and potentially reduce costs without impacting yield. Precision application technologies can also help reduce waste and improve efficiency.".format(percentage_of_total)
}
    Consider soil testing to optimize application rates and potentially reduce costs
    without impacting yield. Precision application technologies can also help
    reduce waste and improve efficiency.
    """
}             if category == "Fertilizer":
            optimization_areas["Fertilizer"] = {
                "description": f"""
                "description": f"Fertilizer costs account for {percentage_of_total:.1f}% of your total input costs."
                Consider soil testing to optimize application rates and potentially reduce costs
                without impacting yield. Precision application technologies can also help
                reduce waste and improve efficiency.
                """
            }
        elif category == "Seed":
            optimization_areas["Seed"] = {
                "description": f"Seed costs represent {percentage_of_total:.1f}% of your total input costs."
                Seed costs represent {percentage_of_total:.1f}% of your total input costs.
                Evaluate if premium seed varieties are delivering adequate yield increases
                to justify their cost. Consider conducting small test plots to compare
                performance of different varieties at different price points.
                """
            }
        elif category == "Chemicals":
            optimization_areas["Chemicals"] = {
                "description": f"""
                Chemical costs account for {percentage_of_total:.1f}% of your total input costs.
                Integrated Pest Management (IPM) strategies can potentially reduce chemical
                applications. Scout fields regularly to apply treatments only when necessary
                rather than on a fixed schedule.
                """
            }
        elif category == "Equipment":
            optimization_areas["Equipment"] = {
                "description": f"""
                Equipment costs represent {percentage_of_total:.1f}% of your total input costs.
                Consider equipment sharing arrangements with neighboring farms, custom hiring
                for specialized equipment, or evaluating if older equipment can be maintained
                rather than replaced.
                """
            }
        elif category == "Land":
            optimization_areas["Land"] = {
                "description": f"""
                Land costs account for {percentage_of_total:.1f}% of your total input costs.
                While often difficult to reduce, consider negotiating longer-term leases for
                potentially lower rates or exploring alternative lease arrangements like
                crop-share instead of cash rent.
                """
            }
        else:
            optimization_areas[category] = {
                "description": f"""
                {category} costs account for {percentage_of_total:.1f}% of your total input costs.
                As one of your largest expense categories, even small percentage reductions
                here could significantly impact overall profitability.
                """
            }
    
    # Add a general profitability suggestion
    if current_profit < 0:
        optimization_areas["Overall Profitability"] = {
            "description": """
            Your operation is currently showing a loss. Consider:
            1. Negotiating better prices through forward contracts or co-ops
            2. Temporarily reducing acreage of least profitable crops
            3. Exploring alternative markets or value-added opportunities
            4. Consulting with an agricultural financial advisor
            """
        }
    elif current_profit < 50:  # Low profit margin
        optimization_areas["Overall Profitability"] = {
            "description": """
            Your profit margins are relatively thin. Consider:
            1. Focusing cost reduction efforts on your largest direct expense categories
            2. Evaluating crop insurance options to protect against downside risk
            3. Exploring marketing strategies to capture price premiums
            """
        }
    
    return optimization_areas


def generate_pdf(data):
    with open('templates/report_template.html', 'r') as f:
        template = Template(f.read())
    html_content = template.render(crop_name=data['crop_name'], yield_value=data['yield_value'], price_value=data['price_value'], direct_costs=data['direct_costs'], overhead_costs=data['overhead_costs'], net_return=data['net_return'])
    HTML(string=html_content).write_pdf('media/report.pdf')
    """
    Generate a PDF report based on the analysis data.
    from jinja2 import Template
    Args:
        report_data (dict): Dictionary containing the analysis data
        
    Returns:
        bytes: PDF file as bytes
    """
    # Setup Jinja2 environment
    template_loader = jinja2.FileSystemLoader(searchpath="templates")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("report_template.html")
    
    # Check if report data is in the old format (wrapped in 'TapGrow 360 Analysis Report')
    if 'TapGrow 360 Analysis Report' in report_data:
        report_data = report_data['TapGrow 360 Analysis Report']
    
    # Format numbers for display
    formatted_data = {
        'today_date': datetime.datetime.now().strftime("%B %d, %Y"),
        'region': report_data['Region'],
        'crop': report_data['Crop'],
        'total_acres': f"{report_data['Total Acres']:,}",
        'yield_per_acre': f"{report_data['Yield per Acre']:,}",
        'price_per_unit': f"{report_data['Price per Unit']:,.2f}",
        'revenue_per_acre': f"{report_data['Revenue per Acre']:,.2f}",
        'cost_per_acre': f"{report_data['Cost per Acre']:,.2f}",
        'profit_per_acre': f"{report_data['Profit per Acre']:,.2f}",
        'total_profit': f"{report_data['Total Profit']:,.2f}",
        'costs': {k: f"{v:,.2f}" for k, v in report_data['Cost Breakdown'].items()},
        'optimization': report_data['Optimization Suggestions']
    }
    
    # Render the HTML template with the data
    html_str = template.render(**formatted_data)
    
    # Convert HTML to PDF using WeasyPrint
    pdf_bytes = io.BytesIO()
    HTML(string=html_str).write_pdf(pdf_bytes)
    pdf_bytes.seek(0)
    
    return pdf_bytes.getvalue()


def generate_excel_report(report_data):
    """
    Generate an Excel report based on the analysis data.
    
    Args:
        report_data (dict): Dictionary containing the analysis data
        
    Returns:
        bytes: Excel file as bytes
    """
    # Create an in-memory Excel file
    output = io.BytesIO()
    
    # Create a workbook
    workbook = xlsxwriter.Workbook(output)
    
    # Add formatting
    title_format = workbook.add_format({
        'bold': True, 
        'font_size': 14, 
        'align': 'center',
        'bg_color': '#000000',
        'font_color': 'white'
    })
    
    header_format = workbook.add_format({
        'bold': True, 
        'font_size': 12, 
        'align': 'center',
        'bg_color': '#f2f2f2',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'align': 'left',
        'border': 1
    })
    
    number_format = workbook.add_format({
        'align': 'right',
        'border': 1,
        'num_format': '$#,##0.00'
    })
    
    # Generate timestamp
    timestamp = datetime.datetime.now().strftime("%B %d, %Y")
    
    # Check if this is a scenario comparison report or a single-scenario report
    is_comparison = False
    if isinstance(report_data, dict):
        if 'Mode' in report_data:  # This is a comparison report
            is_comparison = True
        elif 'Baseline' in report_data:  # Alternative way to detect comparison
            is_comparison = True
    
    if is_comparison:
        # ===== SCENARIO COMPARISON REPORT =====
        summary_sheet = workbook.add_worksheet("Comparison")
        costs_sheet = workbook.add_worksheet("Cost Breakdown")
        
        # No logo layout
        summary_sheet.merge_range('A1:D1', 'TapGrow 360 Scenario Comparison', title_format)
        summary_sheet.merge_range('A2:D2', f'Generated on {timestamp}', cell_format)
        
        # Standard starting row for data
        data_start_row = 4
        
        # Headers for the summary table
        summary_sheet.write(data_start_row, 0, 'Metric', header_format)
        summary_sheet.write(data_start_row, 1, 'Scenario 1', header_format)
        summary_sheet.write(data_start_row, 2, 'Scenario 2', header_format)
        
        # Check if there's a Scenario 3
        has_scenario3 = False
        if 'Scenario 3' in report_data:
            has_scenario3 = True
            summary_sheet.write(data_start_row, 3, 'Scenario 3', header_format)
        
        # Define metrics to display
        metrics = [
            'Region', 'Crop', 'Yield per Acre', 'Price per Unit',
            'Revenue per Acre', 'Cost per Acre', 'Profit per Acre',
            'Total Revenue', 'Total Cost', 'Total Profit'
        ]
        
        # Fill in the summary data
        row = data_start_row + 1
        for metric in metrics:
            summary_sheet.write(row, 0, metric, cell_format)
            
            # Get values for each scenario
            scenario1_value = None
            scenario2_value = None
            scenario3_value = None
            
            if metric == 'Region':
                scenario1_value = report_data['Baseline']['Region']
                scenario2_value = report_data['Scenario 2']['Region']
                if has_scenario3:
                    scenario3_value = report_data['Scenario 3']['Region']
            elif metric == 'Crop':
                scenario1_value = report_data['Baseline']['Crop']
                scenario2_value = report_data['Scenario 2']['Crop']
                if has_scenario3:
                    scenario3_value = report_data['Scenario 3']['Crop']
            elif metric == 'Yield per Acre':
                scenario1_value = report_data['Baseline']['Yield per Acre']
                scenario2_value = report_data['Scenario 2']['Yield per Acre']
                if has_scenario3:
                    scenario3_value = report_data['Scenario 3']['Yield per Acre']
            elif metric == 'Price per Unit':
                scenario1_value = report_data['Baseline']['Price per Unit']
                scenario2_value = report_data['Scenario 2']['Price per Unit']
                if has_scenario3:
                    scenario3_value = report_data['Scenario 3']['Price per Unit']
            elif metric == 'Revenue per Acre':
                scenario1_value = report_data['Baseline']['Revenue per Acre']
                scenario2_value = report_data['Scenario 2']['Revenue per Acre']
                if has_scenario3:
                    scenario3_value = report_data['Scenario 3']['Revenue per Acre']
            elif metric == 'Cost per Acre':
                scenario1_value = report_data['Baseline']['Cost per Acre']
                scenario2_value = report_data['Scenario 2']['Cost per Acre']
                if has_scenario3:
                    scenario3_value = report_data['Scenario 3']['Cost per Acre']
            elif metric == 'Profit per Acre':
                scenario1_value = report_data['Baseline']['Profit per Acre']
                scenario2_value = report_data['Scenario 2']['Profit per Acre']
                if has_scenario3:
                    scenario3_value = report_data['Scenario 3']['Profit per Acre']
            elif metric == 'Total Revenue':
                scenario1_value = report_data['Baseline']['Total Revenue']
                scenario2_value = report_data['Scenario 2']['Total Revenue']
                if has_scenario3:
                    scenario3_value = report_data['Scenario 3']['Total Revenue']
            elif metric == 'Total Cost':
                scenario1_value = report_data['Baseline']['Total Cost']
                scenario2_value = report_data['Scenario 2']['Total Cost']
                if has_scenario3:
                    scenario3_value = report_data['Scenario 3']['Total Cost']
            elif metric == 'Total Profit':
                scenario1_value = report_data['Baseline']['Total Profit']
                scenario2_value = report_data['Scenario 2']['Total Profit']
                if has_scenario3:
                    scenario3_value = report_data['Scenario 3']['Total Profit']
            
            # Write values with appropriate formatting
            is_currency = 'Price' in metric or 'Revenue' in metric or 'Cost' in metric or 'Profit' in metric
            
            if is_currency and isinstance(scenario1_value, (int, float)):
                summary_sheet.write(row, 1, scenario1_value, number_format)
            else:
                summary_sheet.write(row, 1, scenario1_value, cell_format)
                
            if is_currency and isinstance(scenario2_value, (int, float)):
                summary_sheet.write(row, 2, scenario2_value, number_format)
            else:
                summary_sheet.write(row, 2, scenario2_value, cell_format)
                
            if has_scenario3:
                if is_currency and isinstance(scenario3_value, (int, float)):
                    summary_sheet.write(row, 3, scenario3_value, number_format)
                else:
                    summary_sheet.write(row, 3, scenario3_value, cell_format)
            
            row += 1
        
        # Auto-fit columns
        summary_sheet.set_column('A:A', 20)
        summary_sheet.set_column('B:B', 15)
        summary_sheet.set_column('C:C', 15)
        if has_scenario3:
            summary_sheet.set_column('D:D', 15)
        
        # Cost breakdown sheet
        costs_sheet.merge_range('A1:D1', 'Cost Breakdown per Acre', title_format)
        costs_sheet.write(3, 0, 'Cost Item', header_format)
        costs_sheet.write(3, 1, 'Scenario 1', header_format)
        costs_sheet.write(3, 2, 'Scenario 2', header_format)
        if has_scenario3:
            costs_sheet.write(3, 3, 'Scenario 3', header_format)
        
        # Collect all cost items
        all_cost_items = set()
        all_cost_items.update(report_data['Baseline']['Cost Breakdown'].keys())
        all_cost_items.update(report_data['Scenario 2']['Cost Breakdown'].keys())
        if has_scenario3:
            all_cost_items.update(report_data['Scenario 3']['Cost Breakdown'].keys())
        
        # Write cost items
        row = 4
        for item in sorted(all_cost_items):
            costs_sheet.write(row, 0, item, cell_format)
            costs_sheet.write(row, 1, report_data['Baseline']['Cost Breakdown'].get(item, 0), number_format)
            costs_sheet.write(row, 2, report_data['Scenario 2']['Cost Breakdown'].get(item, 0), number_format)
            if has_scenario3:
                costs_sheet.write(row, 3, report_data['Scenario 3']['Cost Breakdown'].get(item, 0), number_format)
            row += 1
        
        # Auto-fit columns
        costs_sheet.set_column('A:A', 25)
        costs_sheet.set_column('B:B', 15)
        costs_sheet.set_column('C:C', 15)
        if has_scenario3:
            costs_sheet.set_column('D:D', 15)
    
    else:
        # ===== SINGLE SCENARIO REPORT =====
        summary_sheet = workbook.add_worksheet("Summary")
        costs_sheet = workbook.add_worksheet("Cost Breakdown")
        optimization_sheet = workbook.add_worksheet("Optimization")
        
        # No logo layout
        summary_sheet.merge_range('A1:B1', 'TapGrow 360 Analysis Report', title_format)
        summary_sheet.merge_range('A2:B2', f'Generated on {timestamp}', cell_format)
        # Standard starting row for data
        data_start_row = 4
        
        summary_data = [
            ['Region', report_data['Region']],
            ['Crop', report_data['Crop']],
            ['Total Acres', report_data['Total Acres']],
            ['Yield per Acre', report_data['Yield per Acre']],
            ['Price per Unit', report_data['Price per Unit']],
            ['Revenue per Acre', report_data['Revenue per Acre']],
            ['Cost per Acre', report_data['Cost per Acre']],
            ['Profit per Acre', report_data['Profit per Acre']],
            ['Total Revenue', report_data['Total Revenue']],
            ['Total Cost', report_data['Total Cost']],
            ['Total Profit', report_data['Total Profit']]
        ]
        
        summary_sheet.write(data_start_row, 0, 'Metric', header_format)
        summary_sheet.write(data_start_row, 1, 'Value', header_format)
        
        row = data_start_row + 1
        for item in summary_data:
            summary_sheet.write(row, 0, item[0], cell_format)
            
            # Format numbers with dollar signs and thousands separators
            if isinstance(item[1], (int, float)) and ('Price' in item[0] or 'Revenue' in item[0] or 'Cost' in item[0] or 'Profit' in item[0]):
                summary_sheet.write(row, 1, item[1], number_format)
            else:
                summary_sheet.write(row, 1, item[1], cell_format)
            
            row += 1
        
        # Auto-fit columns
        summary_sheet.set_column('A:A', 20)
        summary_sheet.set_column('B:B', 15)
        
        # Cost breakdown sheet
        costs_sheet.merge_range('A1:B1', 'Cost Breakdown per Acre', title_format)
        costs_sheet.write('A3', 'Cost Item', header_format)
        costs_sheet.write('B3', 'Cost ($/acre)', header_format)
        
        row = 3
        for item, cost in report_data['Cost Breakdown'].items():
            costs_sheet.write(row, 0, item, cell_format)
            costs_sheet.write(row, 1, cost, number_format)
            row += 1
        
        # Auto-fit columns
        costs_sheet.set_column('A:A', 25)
        costs_sheet.set_column('B:B', 18)
        
        # Optimization sheet
        optimization_sheet.merge_range('A1:B1', 'Optimization Suggestions', title_format)
        optimization_sheet.write('A3', 'Category', header_format)
        optimization_sheet.write('B3', 'Recommendation', header_format)
        
        row = 3
        for category, details in report_data['Optimization Suggestions'].items():
            optimization_sheet.write(row, 0, category, cell_format)
            # Clean up the text and remove extra whitespace
            description = ' '.join(details['description'].split())
            optimization_sheet.write(row, 1, description, cell_format)
            row += 1
        
        # Auto-fit columns
        optimization_sheet.set_column('A:A', 20)
        optimization_sheet.set_column('B:B', 80)
    
    # Close the workbook
    workbook.close()
    
    # Get the bytes value
    output.seek(0)
    return output.getvalue()
