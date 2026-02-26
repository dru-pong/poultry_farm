from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, Color
from openpyxl.utils import get_column_letter
from datetime import datetime
from decimal import Decimal


def create_expenses_excel_report(report_data, filename='expenses_report.xlsx'):
    """
    Create an Excel file from expenses report data.
    """
    wb = Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Create summary sheet
    summary_ws = wb.create_sheet('Summary')
    _create_summary_sheet(summary_ws, report_data)
    
    # Create category breakdown sheet
    category_ws = wb.create_sheet('By Category')
    _create_category_sheet(category_ws, report_data)
    
    # Create daily expenses sheet
    daily_ws = wb.create_sheet('Daily Expenses')
    _create_daily_sheet(daily_ws, report_data)
    
    # Create detailed transactions sheet
    detail_ws = wb.create_sheet('All Transactions')
    _create_detail_sheet(detail_ws, report_data)
    
    # Auto-adjust column widths
    _adjust_column_widths(summary_ws)
    _adjust_column_widths(category_ws)
    _adjust_column_widths(daily_ws)
    _adjust_column_widths(detail_ws)
    
    return wb


def _create_summary_sheet(ws, data):
    """Create summary sheet with key metrics."""
    # Title
    ws['A1'] = 'POULTRY FARM - EXPENSE REPORT'
    ws['A1'].font = Font(bold=True, size=16, color='1F4E79')
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Period
    ws['A3'] = 'Report Period:'
    ws['B3'] = f"{data['period']['start_date']} to {data['period']['end_date']}"
    
    # Metrics
    ws['A5'] = 'Metric'
    ws['B5'] = 'Value'
    
    metrics = [
        ('Total Expenses', data['total_expenses']),
        ('Average per Day', data['average_expense_per_day']),
        ('Number of Days', data['number_of_days']),
        ('Total Transactions', data['expense_count']),
    ]
    
    for i, (label, value) in enumerate(metrics, start=6):
        ws[f'A{i}'] = label
        ws[f'B{i}'] = f'₵{value}' if 'Expense' in label or 'per Day' in label else value
    
    # Style headers
    for cell in ['A5', 'B5']:
        ws[cell].font = Font(bold=True)
        ws[cell].fill = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')


def _create_category_sheet(ws, data):
    """Create category breakdown sheet."""
    # Title
    ws['A1'] = 'EXPENSES BY CATEGORY'
    ws['A1'].font = Font(bold=True, size=14)
    
    # Headers
    headers = ['Category', 'Total Amount', 'Transaction Count', 'Percentage']
    for col, header in enumerate(headers, start=1):
        ws.cell(row=3, column=col, value=header)
        ws.cell(row=3, column=col).font = Font(bold=True)
        ws.cell(row=3, column=col).fill = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')
    
    # Data
    total = float(data['total_expenses'])
    for i, category in enumerate(data['category_breakdown'], start=4):
        ws.cell(row=i, column=1, value=category['category'])
        ws.cell(row=i, column=2, value=f"₵{category['total']}")
        ws.cell(row=i, column=3, value=category['count'])
        percentage = (float(category['total']) / total * 100) if total > 0 else 0
        ws.cell(row=i, column=4, value=f"{percentage:.1f}%")


def _create_daily_sheet(ws, data):
    """Create daily expenses sheet."""
    # Title
    ws['A1'] = 'DAILY EXPENSES'
    ws['A1'].font = Font(bold=True, size=14)
    
    # Headers
    headers = ['Date', 'Amount']
    for col, header in enumerate(headers, start=1):
        ws.cell(row=3, column=col, value=header)
        ws.cell(row=3, column=col).font = Font(bold=True)
        ws.cell(row=3, column=col).fill = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')
    
    # Data
    for i, (date, amount) in enumerate(data['daily_expenses'].items(), start=4):
        ws.cell(row=i, column=1, value=date)
        ws.cell(row=i, column=2, value=f"₵{amount}")


def _create_detail_sheet(ws, data):
    """Create detailed transactions sheet."""
    # Title
    ws['A1'] = 'ALL EXPENSE TRANSACTIONS'
    ws['A1'].font = Font(bold=True, size=14)
    
    # Headers
    headers = ['Date', 'Category', 'Description', 'Amount', 'Notes']
    for col, header in enumerate(headers, start=1):
        ws.cell(row=3, column=col, value=header)
        ws.cell(row=3, column=col).font = Font(bold=True)
        ws.cell(row=3, column=col).fill = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')
    
    # Data
    row = 4
    for category in data['category_breakdown']:
        for item in category['items']:
            ws.cell(row=row, column=1, value=item['date'])
            ws.cell(row=row, column=2, value=category['category'])
            ws.cell(row=row, column=3, value=item['description'])
            ws.cell(row=row, column=4, value=f"₵{item['amount']}")
            ws.cell(row=row, column=5, value=item['notes'])
            row += 1


def _adjust_column_widths(ws):
    """Auto-adjust column widths for better readability."""
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
        
def create_sales_excel_report(report_data, filename='sales_report.xlsx'):
    """
    Create a comprehensive Excel file from sales report data.
    Includes multiple sheets for detailed analysis.
    """
    wb = Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Create summary sheet
    summary_ws = wb.create_sheet('Summary')
    _create_sales_summary_sheet(summary_ws, report_data)
    
    # Create sales by customer sheet
    customer_ws = wb.create_sheet('By Customer')
    _create_sales_by_customer_sheet(customer_ws, report_data)
    
    # Create daily sales sheet
    daily_ws = wb.create_sheet('Daily Sales')
    _create_sales_daily_sheet(daily_ws, report_data)
    
    # Create detailed transactions sheet
    detail_ws = wb.create_sheet('All Transactions')
    _create_sales_detail_sheet(detail_ws, report_data)
    
    # Create egg type breakdown sheet
    eggtype_ws = wb.create_sheet('By Egg Type')
    _create_sales_by_eggtype_sheet(eggtype_ws, report_data)
    
    # Auto-adjust column widths
    for ws in wb.worksheets:
        _adjust_column_widths(ws)
    
    return wb


def _create_sales_summary_sheet(ws, data):
    """Create summary sheet with key sales metrics."""
    # Title
    ws['A1'] = 'POULTRY FARM - SALES REPORT'
    ws['A1'].font = Font(bold=True, size=16, color='1F4E79')
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Period
    ws['A3'] = 'Report Period:'
    ws['B3'] = f"{data['period']['start_date']} to {data['period']['end_date']}"
    
    # Metrics
    ws['A5'] = 'Metric'
    ws['B5'] = 'Value'
    
    metrics = [
        ('Total Sales', data['total_sales']),
        ('Total Revenue', f"₵{data['total_revenue']}"),
        ('Retail Transactions', data['retail_count']),
        ('Retail Revenue', f"₵{data['retail_revenue']}"),
        ('Wholesale Transactions', data['wholesale_count']),
        ('Wholesale Revenue', f"₵{data['wholesale_revenue']}"),
    ]
    
    for i, (label, value) in enumerate(metrics, start=6):
        ws[f'A{i}'] = label
        ws[f'B{i}'] = value
    
    # Style headers
    for cell in ['A5', 'B5']:
        ws[cell].font = Font(bold=True)
        ws[cell].fill = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')
    
    # Quantity breakdown
    ws['A15'] = 'Quantity Breakdown (Crates)'
    ws['A15'].font = Font(bold=True, size=14)
    
    ws['A17'] = 'Egg Type'
    ws['B17'] = 'Quantity'
    
    quantities = data.get('quantities', {})
    egg_types = [('Broken', quantities.get('broken', 0)),
                 ('Small', quantities.get('small', 0)),
                 ('Medium', quantities.get('medium', 0)),
                 ('Big', quantities.get('big', 0))]
    
    for i, (egg_type, qty) in enumerate(egg_types, start=18):
        ws[f'A{i}'] = egg_type
        ws[f'B{i}'] = qty
        ws[f'B{i}'].font = Font(bold=True)


def _create_sales_by_customer_sheet(ws, data):
    """Create sales breakdown by customer sheet."""
    # Title
    ws['A1'] = 'SALES BY CUSTOMER'
    ws['A1'].font = Font(bold=True, size=14)
    
    # Headers
    headers = ['Customer', 'Total Purchases', 'Transaction Count', 'Avg per Transaction', 'Percentage']
    for col, header in enumerate(headers, start=1):
        ws.cell(row=3, column=col, value=header)
        ws.cell(row=3, column=col).font = Font(bold=True)
        ws.cell(row=3, column=col).fill = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')
    
    # Data from customer_breakdown
    total = float(data['total_revenue'])
    for i, customer in enumerate(data.get('customer_breakdown', []), start=4):
        ws.cell(row=i, column=1, value=customer['customer'])
        ws.cell(row=i, column=2, value=f"₵{customer['total']}")
        ws.cell(row=i, column=3, value=customer['transaction_count'])
        avg = float(customer['total']) / customer['transaction_count'] if customer['transaction_count'] > 0 else 0
        ws.cell(row=i, column=4, value=f"₵{avg:.2f}")
        percentage = (float(customer['total']) / total * 100) if total > 0 else 0
        ws.cell(row=i, column=5, value=f"{percentage:.1f}%")


def _create_sales_daily_sheet(ws, data):
    """Create daily sales sheet."""
    # Title
    ws['A1'] = 'DAILY SALES'
    ws['A1'].font = Font(bold=True, size=14)
    
    # Headers
    headers = ['Date', 'Sales Count', 'Revenue']
    for col, header in enumerate(headers, start=1):
        ws.cell(row=3, column=col, value=header)
        ws.cell(row=3, column=col).font = Font(bold=True)
        ws.cell(row=3, column=col).fill = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')
    
    # Data from daily_sales
    for i, (date, sales_data) in enumerate(data.get('daily_sales', {}).items(), start=4):
        ws.cell(row=i, column=1, value=date)
        ws.cell(row=i, column=2, value=sales_data.get('count', 0))
        ws.cell(row=i, column=3, value=f"₵{sales_data.get('revenue', '0.00')}")


def _create_sales_detail_sheet(ws, data):
    """Create detailed transactions sheet with all sale items."""
    # Title
    ws['A1'] = 'ALL SALES TRANSACTIONS'
    ws['A1'].font = Font(bold=True, size=14)
    
    # Headers
    headers = ['Date', 'Time', 'Customer', 'Sale Type', 'Egg Type', 'Quantity', 'Price/Crate', 'Line Total', 'Notes']
    for col, header in enumerate(headers, start=1):
        ws.cell(row=3, column=col, value=header)
        ws.cell(row=3, column=col).font = Font(bold=True)
        ws.cell(row=3, column=col).fill = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')
        ws.cell(row=3, column=col).alignment = Alignment(wrap_text=True)
    
    # Data from transactions
    row = 4
    for transaction in data.get('transactions', []):
        # Parse datetime for separate date and time columns
        sale_datetime = transaction.get('sale_datetime', '')
        date_part = sale_datetime.split('T')[0] if 'T' in sale_datetime else sale_datetime.split(' ')[0]
        time_part = sale_datetime.split('T')[1][:5] if 'T' in sale_datetime else ''
        
        ws.cell(row=row, column=1, value=date_part)
        ws.cell(row=row, column=2, value=time_part)
        ws.cell(row=row, column=3, value=transaction.get('customer', 'Retail'))
        ws.cell(row=row, column=4, value=transaction.get('sale_type', '').title())
        ws.cell(row=row, column=5, value=transaction.get('egg_type', ''))
        ws.cell(row=row, column=6, value=transaction.get('quantity', 0))
        ws.cell(row=row, column=7, value=f"₵{transaction.get('price_per_crate', '0.00')}")
        ws.cell(row=row, column=8, value=f"₵{transaction.get('line_total', '0.00')}")
        ws.cell(row=row, column=9, value=transaction.get('notes', ''))
        row += 1


def _create_sales_by_eggtype_sheet(ws, data):
    """Create sales breakdown by egg type sheet."""
    # Title
    ws['A1'] = 'SALES BY EGG TYPE'
    ws['A1'].font = Font(bold=True, size=14)
    
    # Headers
    headers = ['Egg Type', 'Total Crates Sold', 'Revenue', 'Percentage of Total']
    for col, header in enumerate(headers, start=1):
        ws.cell(row=3, column=col, value=header)
        ws.cell(row=3, column=col).font = Font(bold=True)
        ws.cell(row=3, column=col).fill = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')
    
    # Data from egg_type_breakdown
    total_revenue = float(data['total_revenue'])
    for i, egg_type in enumerate(data.get('egg_type_breakdown', []), start=4):
        ws.cell(row=i, column=1, value=egg_type['egg_type'])
        ws.cell(row=i, column=2, value=egg_type['total_crates'])
        ws.cell(row=i, column=3, value=f"₵{egg_type['revenue']}")
        percentage = (float(egg_type['revenue']) / total_revenue * 100) if total_revenue > 0 else 0
        ws.cell(row=i, column=4, value=f"{percentage:.1f}%")


def create_profit_loss_excel_report(report_data, filename='profit_loss_report.xlsx'):
    """
    Create a comprehensive Excel file from profit & loss report data.
    """
    wb = Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Create summary sheet
    summary_ws = wb.create_sheet('P&L Summary')
    _create_pl_summary_sheet(summary_ws, report_data)
    
    # Create revenue breakdown sheet
    revenue_ws = wb.create_sheet('Revenue Breakdown')
    _create_pl_revenue_sheet(revenue_ws, report_data)
    
    # Create expense breakdown sheet
    expense_ws = wb.create_sheet('Expense Breakdown')
    _create_pl_expense_sheet(expense_ws, report_data)
    
    # Auto-adjust column widths
    for ws in wb.worksheets:
        _adjust_column_widths(ws)
    
    return wb


def _create_pl_summary_sheet(ws, data):
    """Create P&L summary sheet."""
    # Title
    ws['A1'] = 'POULTRY FARM - PROFIT & LOSS STATEMENT'
    ws['A1'].font = Font(bold=True, size=16, color='1F4E79')
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Period
    ws['A3'] = 'Report Period:'
    ws['B3'] = f"{data['period']['start_date']} to {data['period']['end_date']}"
    
    # REVENUE SECTION
    ws['A5'] = 'REVENUE'
    ws['A5'].font = Font(bold=True, size=14, color='006400')
    
    ws['A7'] = 'Retail Sales'
    ws['B7'] = f"₵{data.get('revenue_breakdown', {}).get('retail', '0.00')}"
    
    ws['A8'] = 'Wholesale Sales'
    ws['B8'] = f"₵{data.get('revenue_breakdown', {}).get('wholesale', '0.00')}"
    
    ws['A10'] = 'TOTAL REVENUE'
    ws['B10'] = f"₵{data.get('total_revenue', '0.00')}"
    ws['B10'].font = Font(bold=True)
    
    # EXPENSES SECTION
    ws['A12'] = 'EXPENSES'
    ws['A12'].font = Font(bold=True, size=14, color='8B0000')
    
    ws['A14'] = 'Total Expenses'
    ws['B14'] = f"₵{data.get('total_expenses', '0.00')}"
    
    # NET PROFIT SECTION
    ws['A17'] = 'NET PROFIT'
    ws['A17'].font = Font(bold=True, size=14)
    
    net_profit = float(data.get('net_profit', 0))
    ws['B17'] = f"₵{data.get('net_profit', '0.00')}"
    ws['B17'].font = Font(bold=True, size=14, color='006400' if net_profit >= 0 else '8B0000')
    
    ws['A18'] = 'Profit Margin'
    ws['B18'] = f"{data.get('profit_margin', 0)}%"
    
    # Style headers
    for cell in ['A5', 'A12', 'A17']:
        ws[cell].fill = PatternFill(start_color='E8E8E8', end_color='E8E8E8', fill_type='solid')


def _create_pl_revenue_sheet(ws, data):
    """Create revenue breakdown sheet."""
    # Title
    ws['A1'] = 'REVENUE BREAKDOWN'
    ws['A1'].font = Font(bold=True, size=14)
    
    # Headers
    headers = ['Sale Type', 'Transaction Count', 'Total Revenue', 'Percentage']
    for col, header in enumerate(headers, start=1):
        ws.cell(row=3, column=col, value=header)
        ws.cell(row=3, column=col).font = Font(bold=True)
        ws.cell(row=3, column=col).fill = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')
    
    total = float(data.get('total_revenue', 0))
    revenue_data = data.get('revenue_breakdown', {})
    
    retail_count = data.get('retail_count', 0)
    wholesale_count = data.get('wholesale_count', 0)
    
    # Retail row
    ws.cell(row=4, column=1, value='Retail')
    ws.cell(row=4, column=2, value=retail_count)
    ws.cell(row=4, column=3, value=f"₵{revenue_data.get('retail', '0.00')}")
    retail_pct = (float(revenue_data.get('retail', 0)) / total * 100) if total > 0 else 0
    ws.cell(row=4, column=4, value=f"{retail_pct:.1f}%")
    
    # Wholesale row
    ws.cell(row=5, column=1, value='Wholesale')
    ws.cell(row=5, column=2, value=wholesale_count)
    ws.cell(row=5, column=3, value=f"₵{revenue_data.get('wholesale', '0.00')}")
    wholesale_pct = (float(revenue_data.get('wholesale', 0)) / total * 100) if total > 0 else 0
    ws.cell(row=5, column=4, value=f"{wholesale_pct:.1f}%")


def _create_pl_expense_sheet(ws, data):
    """Create expense breakdown sheet."""
    # Title
    ws['A1'] = 'EXPENSE BREAKDOWN'
    ws['A1'].font = Font(bold=True, size=14)
    
    # Headers
    headers = ['Category', 'Total Amount', 'Percentage']
    for col, header in enumerate(headers, start=1):
        ws.cell(row=3, column=col, value=header)
        ws.cell(row=3, column=col).font = Font(bold=True)
        ws.cell(row=3, column=col).fill = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')
    
    total = float(data.get('total_expenses', 0))
    
    for i, expense in enumerate(data.get('expense_breakdown', []), start=4):
        category = expense.get('category__name', 'Unknown')
        amount = expense.get('total', 0)
        ws.cell(row=i, column=1, value=category)
        ws.cell(row=i, column=2, value=f"₵{amount}")
        percentage = (float(amount) / total * 100) if total > 0 else 0
        ws.cell(row=i, column=3, value=f"{percentage:.1f}%")


def _adjust_column_widths(ws):
    """Auto-adjust column widths for better readability."""
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width