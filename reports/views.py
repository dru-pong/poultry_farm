from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from inventory.models import EggType
from sales.models import SaleItem


class ReportViewSet(viewsets.ViewSet):
    """
    ViewSet for aggregated reports and analytics.
    ALL QUANTITIES ARE IN CRATES (confirmed by Sales model).
    """
    permission_classes = [permissions.IsAuthenticated]

    def _parse_date(self, date_str, param_name):
        """Reusable date parsing with validation"""
        if not date_str:
            raise ValidationError(f"'{param_name}' is required")
        try:
            return date.fromisoformat(date_str)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid '{param_name}' format. Use YYYY-MM-DD")

    @action(detail=False, methods=['get'], url_path='dashboard-summary')
    def dashboard_summary(self, request):
        from sales.models import Sale
        from expenses.models import Expense

        report_date_str = request.query_params.get('date', date.today().isoformat())
        try:
            report_date = self._parse_date(report_date_str, 'date')
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        sales = Sale.objects.filter(sale_datetime__date=report_date)
        total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        total_sales_count = sales.count()

        expenses = Expense.objects.filter(date=report_date)
        total_expenses_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        total_expenses_count = expenses.count()  # Fixed ambiguous key name

        profit = total_revenue - total_expenses_amount
        profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else Decimal('0.00')

        return Response({
            'date': report_date.isoformat(),  # ISO string for JSON safety
            'revenue': str(total_revenue),
            'expenses': str(total_expenses_amount),  # Amount (not count)
            'profit': str(profit),
            'profit_margin': round(profit_margin, 2),  # FIXED: Removed leading space typo
            'total_sales': total_sales_count,
            'total_expenses_count': total_expenses_count,  # Explicit count key
        })
    
    @action(detail=False, methods=['get'], url_path='sales-trend')
    def sales_trend(self, request):
        """
        Daily sales revenue for last 7 days (used by dashboard chart).
        Optional: ?days=14 (max 30)
        """
        from sales.models import Sale
        from datetime import date, timedelta
        from django.db.models import Sum
        from decimal import Decimal

     # Get days parameter (default 7, clamp 1-30)
        try:
            days = int(request.query_params.get('days', 7))
            days = max(1, min(days, 30))
        except (ValueError, TypeError):
            days = 7

        today = date.today()
        start_date = today - timedelta(days=days - 1)
    
        # Aggregate revenue by date
        sales_data = Sale.objects.filter(
            sale_datetime__date__range=[start_date, today]
        ).values('sale_datetime__date').annotate(
            total=Sum('total_amount')
        ).order_by('sale_datetime__date')
    
     # Build complete date range (fill missing dates with 0)
        revenue_map = {
            item['sale_datetime__date'].isoformat(): str(item['total'] or Decimal('0.00'))
            for item in sales_data
        }
    
        categories = []
        values = []
        for i in range(days):
            d = (start_date + timedelta(days=i)).isoformat()
            categories.append(d)
            values.append(revenue_map.get(d, '0.00'))
    
        return Response({
        'categories': categories,  # ["2026-02-10", "2026-02-11", ...]
        'values': values,          # ["150.00", "200.50", ...]
        'days': days
    })

    @action(detail=False, methods=['get'], url_path='sales-report')
    def sales_report(self, request):
        from sales.models import Sale, SaleItem
        from inventory.models import EggType

        try:
            start_date = self._parse_date(request.query_params.get('start_date'), 'start_date')
            end_date = self._parse_date(request.query_params.get('end_date'), 'end_date')
            if start_date > end_date:
                return Response({'error': 'start_date cannot be after end_date'}, status=400)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        sales = Sale.objects.filter(sale_datetime__date__range=[start_date, end_date])
        total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

        retail_sales = sales.filter(sale_type='retail')
        wholesale_sales = sales.filter(sale_type='wholesale')

        # Get egg types
        try:
            broken_type = EggType.objects.get(name='Broken')
            small_type = EggType.objects.get(name='Small')
            medium_type = EggType.objects.get(name='Medium')
            big_type = EggType.objects.get(name='Big')
        except EggType.DoesNotExist:
            broken_type = small_type = medium_type = big_type = None

        # Calculate quantities using SaleItem relationships
        quantities = {
            'broken': 0,
            'small': 0,
            'medium': 0,
            'big': 0
        }

        if broken_type and small_type and medium_type and big_type:
            # Get all sale items within date range
            sale_items = SaleItem.objects.filter(sale__in=sales)
            
            # Calculate quantities by egg type
            quantities['broken'] = sale_items.filter(egg_type=broken_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
            quantities['small'] = sale_items.filter(egg_type=small_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
            quantities['medium'] = sale_items.filter(egg_type=medium_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
            quantities['big'] = sale_items.filter(egg_type=big_type).aggregate(Sum('quantity'))['quantity__sum'] or 0

        report = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_sales': sales.count(),
            'total_revenue': str(total_revenue),
            'retail_count': retail_sales.count(),
            'wholesale_count': wholesale_sales.count(),
            'retail_revenue': str(retail_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')),
            'wholesale_revenue': str(wholesale_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')),
            'quantities': quantities
        }
        return Response(report)

    @action(detail=False, methods=['get'], url_path='profit-loss')
    def profit_loss(self, request):
        from sales.models import Sale
        from expenses.models import Expense

        try:
            start_date = self._parse_date(request.query_params.get('start_date'), 'start_date')
            end_date = self._parse_date(request.query_params.get('end_date'), 'end_date')
            if start_date > end_date:
                return Response({'error': 'start_date cannot be after end_date'}, status=400)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        sales = Sale.objects.filter(sale_datetime__date__range=[start_date, end_date])
        expenses = Expense.objects.filter(date__range=[start_date, end_date])
        
        total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        net_profit = total_revenue - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0.00')

        pl_statement = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_revenue': str(total_revenue),
            'total_expenses': str(total_expenses),
            'net_profit': str(net_profit),
            'profit_margin': round(profit_margin, 2),
            'revenue_breakdown': {
                'retail': str(sales.filter(sale_type='retail').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')),
                'wholesale': str(sales.filter(sale_type='wholesale').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')),
            },
            'expense_breakdown': list(
                expenses.values('category__name').annotate(total=Sum('amount')).order_by('-total')
            ),
        }
        return Response(pl_statement)

    @action(detail=False, methods=['get'], url_path='inventory-status')
    def inventory_status(self, request):
        """
        Calculates CUMULATIVE stock in CRATES (all historical intake - all historical sales).
        Uses the new model structure with SaleItem relationships.
        """
        from inventory.models import IntakeLog
        from sales.models import Sale, SaleItem

        today = date.today()
        
        # SUM ALL intake logs up to today
        intake_logs = IntakeLog.objects.filter(recorded_date__lte=today)
        if not intake_logs.exists():
            return Response({
                'error': 'No intake records found. Please log inventory intake first.'
            }, status=404)

        # Total intake per egg type (in crates)
        total_broken_intake = intake_logs.aggregate(Sum('broken_crates'))['broken_crates__sum'] or 0
        total_small_intake = intake_logs.aggregate(Sum('small_crates'))['small_crates__sum'] or 0
        total_medium_intake = intake_logs.aggregate(Sum('medium_crates'))['medium_crates__sum'] or 0
        total_big_intake = intake_logs.aggregate(Sum('big_crates'))['big_crates__sum'] or 0

        # Get egg types
        try:
            broken_type = EggType.objects.get(name='Broken')
            small_type = EggType.objects.get(name='Small')
            medium_type = EggType.objects.get(name='Medium')
            big_type = EggType.objects.get(name='Big')
        except EggType.DoesNotExist:
            return Response({
                'error': 'Egg types not configured. Please set up egg types first.'
            }, status=404)

        # Total sales per egg type using the new relationship structure
        sales = Sale.objects.filter(sale_datetime__date__lte=today)
        sale_items = SaleItem.objects.filter(sale__in=sales)
        
        total_broken_sold = sale_items.filter(egg_type=broken_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_small_sold = sale_items.filter(egg_type=small_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_medium_sold = sale_items.filter(egg_type=medium_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_big_sold = sale_items.filter(egg_type=big_type).aggregate(Sum('quantity'))['quantity__sum'] or 0

        # Calculate available stock (in crates)
        broken_available = max(0, total_broken_intake - total_broken_sold)
        small_available = max(0, total_small_intake - total_small_sold)
        medium_available = max(0, total_medium_intake - total_medium_sold)
        big_available = max(0, total_big_intake - total_big_sold)
        total_available = broken_available + small_available + medium_available + big_available

        # Low stock alerts (threshold: 10 crates)
        low_stock_alerts = []
        threshold = 10
        for egg_type, available in [
            ('broken', broken_available),
            ('small', small_available),
            ('medium', medium_available),
            ('big', big_available)
        ]:
            if available < threshold:
                low_stock_alerts.append({
                    'egg_type': egg_type,
                    'available_crates': available,
                    'threshold_crates': threshold
                })

       
        status = {
            'broken_available': broken_available,
            'small_available': small_available,
            'medium_available': medium_available,
            'big_available': big_available,
            'total_available': total_available,
            'low_stock_alerts': low_stock_alerts,
            'calculation_date': today.isoformat(),
            'note': 'Stock calculated as: SUM(all intakes up to today) - SUM(all sales up to today)'
        }

        return Response(status)
    
    @action(detail=False, methods=['get'], url_path='expenses-report')
    def expenses_report(self, request):
        """
        Detailed report of expenses for a date range.
        Returns expenses broken down by category with detailed transaction history.
        """
        from expenses.models import Expense, ExpenseCategory
        
        try:
            # Parse date parameters
            start_date = self._parse_date(request.query_params.get('start_date'), 'start_date')
            end_date = self._parse_date(request.query_params.get('end_date'), 'end_date')
            
            # Validate date range
            if start_date > end_date:
                return Response({
                    'error': 'start_date cannot be after end_date'
                }, status=400)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        # Get all expenses in date range
        expenses = Expense.objects.filter(date__range=[start_date, end_date])
        
        # Total expenses
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        # Calculate number of days in range (add 1 to include both start and end dates)
        number_of_days = (end_date - start_date).days + 1
        
        # Calculate average expense per day
        average_per_day = total_expenses / number_of_days if number_of_days > 0 else Decimal('0.00')
        average_per_day = average_per_day.quantize(Decimal('0.01'))  # ← This ensures 2 decimal places

        # Categorized expenses
        category_breakdown = []
        categories = ExpenseCategory.objects.filter(is_active=True)
        
        for category in categories:
            category_expenses = expenses.filter(category=category)
            category_total = category_expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            
            if category_total > 0:
                category_breakdown.append({
                    'category': category.name,
                    'total': str(category_total),
                    'count': category_expenses.count(),
                    'items': [{
                        'id': expense.id,
                        'date': str(expense.date),
                        'description': expense.description,
                        'amount': str(expense.amount),
                        'notes': expense.notes or ''
                    } for expense in category_expenses]
                })
        
        # Daily expenses breakdown
        daily_expenses = {}
        current_date = start_date
        while current_date <= end_date:
            day_expenses = expenses.filter(date=current_date)
            day_total = day_expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            daily_expenses[str(current_date)] = str(day_total)
            current_date += timedelta(days=1)
        
        # Format response
        report = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_expenses': str(total_expenses),
            'average_expense_per_day': str(average_per_day),  # ← NEW: Added average
            'number_of_days': number_of_days,  # ← NEW: Added day count
            'category_breakdown': category_breakdown,
            'daily_expenses': daily_expenses,
            'expense_count': expenses.count()
        }
        
        return Response(report)
    @action(detail=False, methods=['get'], url_path='expenses-report/excel')
    def expenses_report_excel(self, request):
        """
        Export expenses report as Excel file.
        """
        from expenses.models import Expense, ExpenseCategory
        from .utils import create_expenses_excel_report
        from django.http import HttpResponse
        
        try:
            # Parse date parameters
            start_date = self._parse_date(request.query_params.get('start_date'), 'start_date')
            end_date = self._parse_date(request.query_params.get('end_date'), 'end_date')
            
            if start_date > end_date:
                return Response({
                    'error': 'start_date cannot be after end_date'
                }, status=400)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        # Get all expenses in date range
        expenses = Expense.objects.filter(date__range=[start_date, end_date])
        
        # Total expenses
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        # Calculate number of days in range
        number_of_days = (end_date - start_date).days + 1
        
        # Calculate average expense per day
        average_per_day = total_expenses / number_of_days if number_of_days > 0 else Decimal('0.00')
        average_per_day = average_per_day.quantize(Decimal('0.01'))
        
        # Categorized expenses
        category_breakdown = []
        categories = ExpenseCategory.objects.filter(is_active=True)
        
        for category in categories:
            category_expenses = expenses.filter(category=category)
            category_total = category_expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            
            if category_total > 0:
                category_breakdown.append({
                    'category': category.name,
                    'total': str(category_total),
                    'count': category_expenses.count(),
                    'items': [{
                        'id': expense.id,
                        'date': str(expense.date),
                        'description': expense.description,
                        'amount': str(expense.amount),
                        'notes': expense.notes or ''
                    } for expense in category_expenses]
                })
        
        # Daily expenses breakdown
        daily_expenses = {}
        current_date = start_date
        while current_date <= end_date:
            day_expenses = expenses.filter(date=current_date)
            day_total = day_expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            daily_expenses[str(current_date)] = str(day_total)
            current_date += timedelta(days=1)
        
        # Prepare report data
        report_data = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_expenses': str(total_expenses),
            'average_expense_per_day': str(average_per_day),
            'number_of_days': number_of_days,
            'category_breakdown': category_breakdown,
            'daily_expenses': daily_expenses,
            'expense_count': expenses.count()
        }
        
        # Create Excel workbook
        wb = create_expenses_excel_report(report_data)
        
        # Create HTTP response with Excel file
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=expenses_report_{start_date}_to_{end_date}.xlsx'
        
        wb.save(response)
        
        return response
    @action(detail=False, methods=['get'], url_path='sales-report/excel')
    def sales_report_excel(self, request):
        """
        Export sales report as comprehensive Excel file.
        Includes customer breakdown, daily sales, and all transactions.
        """
        from sales.models import Sale, SaleItem
        from inventory.models import EggType
        from customers.models import WholesaleCustomer
        from .utils import create_sales_excel_report
        from django.http import HttpResponse
        
        try:
            start_date = self._parse_date(request.query_params.get('start_date'), 'start_date')
            end_date = self._parse_date(request.query_params.get('end_date'), 'end_date')
            
            if start_date > end_date:
                return Response({'error': 'start_date cannot be after end_date'}, status=400)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        # Get all sales in date range
        sales = Sale.objects.filter(sale_datetime__date__range=[start_date, end_date])
        
        # Basic metrics
        total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        total_sales = sales.count()
        retail_sales = sales.filter(sale_type='retail')
        wholesale_sales = sales.filter(sale_type='wholesale')
        
        # Get egg types
        egg_types = {
            'Broken': EggType.objects.filter(name='Broken').first(),
            'Small': EggType.objects.filter(name='Small').first(),
            'Medium': EggType.objects.filter(name='Medium').first(),
            'Big': EggType.objects.filter(name='Big').first(),
        }
        
        # Get all sale items
        sale_items = SaleItem.objects.filter(sale__in=sales).select_related('egg_type', 'sale__customer')
        
        # Customer breakdown
        customer_breakdown = []
        customers = WholesaleCustomer.objects.filter(is_active=True)
        for customer in customers:
            customer_sales = sales.filter(customer=customer)
            if customer_sales.exists():
                customer_total = customer_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
                customer_breakdown.append({
                    'customer': customer.name,
                    'total': str(customer_total),
                    'transaction_count': customer_sales.count(),
                })
        
        # Daily sales breakdown
        daily_sales = {}
        current_date = start_date
        while current_date <= end_date:
            day_sales = sales.filter(sale_datetime__date=current_date)
            day_revenue = day_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
            daily_sales[str(current_date)] = {
                'count': day_sales.count(),
                'revenue': str(day_revenue),
            }
            current_date += timedelta(days=1)
        
        # Egg type breakdown
        egg_type_breakdown = []
        for egg_name, egg_type in egg_types.items():
            if egg_type:
                type_items = sale_items.filter(egg_type=egg_type)
                total_crates = type_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
                type_revenue = sum(item.line_total for item in type_items)
                egg_type_breakdown.append({
                    'egg_type': egg_name,
                    'total_crates': total_crates,
                    'revenue': str(type_revenue),
                })
        
        # Detailed transactions
        transactions = []
        for item in sale_items:
            transactions.append({
                'sale_datetime': item.sale.sale_datetime.isoformat(),
                'customer': item.sale.customer.name if item.sale.customer else 'Retail',
                'sale_type': item.sale.sale_type,
                'egg_type': item.egg_type.name,
                'quantity': item.quantity,
                'price_per_crate': str(item.price_per_crate or Decimal('0.00')),
                'line_total': str(item.line_total),
                'notes': item.sale.notes or '',
            })
        
        # Prepare report data
        report_data = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_sales': total_sales,
            'total_revenue': str(total_revenue),
            'retail_count': retail_sales.count(),
            'retail_revenue': str(retail_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')),
            'wholesale_count': wholesale_sales.count(),
            'wholesale_revenue': str(wholesale_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')),
            'quantities': {
                'broken': sale_items.filter(egg_type=egg_types.get('Broken')).aggregate(Sum('quantity'))['quantity__sum'] or 0,
                'small': sale_items.filter(egg_type=egg_types.get('Small')).aggregate(Sum('quantity'))['quantity__sum'] or 0,
                'medium': sale_items.filter(egg_type=egg_types.get('Medium')).aggregate(Sum('quantity'))['quantity__sum'] or 0,
                'big': sale_items.filter(egg_type=egg_types.get('Big')).aggregate(Sum('quantity'))['quantity__sum'] or 0,
            },
            'customer_breakdown': customer_breakdown,
            'daily_sales': daily_sales,
            'egg_type_breakdown': egg_type_breakdown,
            'transactions': transactions,
        }
        
        # Create Excel workbook
        wb = create_sales_excel_report(report_data)
        
        # Create HTTP response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=sales_report_{start_date}_to_{end_date}.xlsx'
        
        wb.save(response)
        
        return response


    @action(detail=False, methods=['get'], url_path='profit-loss/excel')
    def profit_loss_excel(self, request):
        """
        Export profit & loss report as Excel file.
        """
        from sales.models import Sale
        from expenses.models import Expense
        from .utils import create_profit_loss_excel_report
        from django.http import HttpResponse
        
        try:
            start_date = self._parse_date(request.query_params.get('start_date'), 'start_date')
            end_date = self._parse_date(request.query_params.get('end_date'), 'end_date')
            
            if start_date > end_date:
                return Response({'error': 'start_date cannot be after end_date'}, status=400)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        # Get sales and expenses
        sales = Sale.objects.filter(sale_datetime__date__range=[start_date, end_date])
        expenses = Expense.objects.filter(date__range=[start_date, end_date])
        
        # Calculate totals
        total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        net_profit = total_revenue - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0.00')
        
        # Revenue breakdown
        retail_sales = sales.filter(sale_type='retail')
        wholesale_sales = sales.filter(sale_type='wholesale')
        
        # Expense breakdown by category
        expense_breakdown = list(
            expenses.values('category__name').annotate(total=Sum('amount')).order_by('-total')
        )
        
        # Prepare report data
        report_data = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_revenue': str(total_revenue),
            'total_expenses': str(total_expenses),
            'net_profit': str(net_profit),
            'profit_margin': round(float(profit_margin), 2),
            'revenue_breakdown': {
                'retail': str(retail_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')),
                'wholesale': str(wholesale_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')),
            },
            'retail_count': retail_sales.count(),
            'wholesale_count': wholesale_sales.count(),
            'expense_breakdown': expense_breakdown,
        }
        
        # Create Excel workbook
        wb = create_profit_loss_excel_report(report_data)
        
        # Create HTTP response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=profit_loss_report_{start_date}_to_{end_date}.xlsx'
        
        wb.save(response)
        
        return response
    