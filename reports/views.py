from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError


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
        from sales.models import Sale

        try:
            start_date = self._parse_date(request.query_params.get('start_date'), 'start_date')
            end_date = self._parse_date(request.query_params.get('end_date'), 'end_date')
            if start_date > end_date:
                return Response({'error': 'start_date cannot be after end_date'}, status=400)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        sales = Sale.objects.filter(sale_datetime__date__range=[start_date, end_date])
        total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

        retail_sales = sales.filter(sale_type='retail')  # FIXED: Removed space typo 'retai l'
        wholesale_sales = sales.filter(sale_type='wholesale')

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
            'quantities': {
                'broken': sales.aggregate(Sum('broken_quantity'))['broken_quantity__sum'] or 0,
                'small': sales.aggregate(Sum('small_quantity'))['small_quantity__sum'] or 0,
                'medium': sales.aggregate(Sum('medium_quantity'))['medium_quantity__sum'] or 0,
                'big': sales.aggregate(Sum('big_quantity'))['big_quantity__sum'] or 0,
            }
        }
        return Response(report)

    @action(detail=False, methods=['get'], url_path='profit-loss')
    def profit_loss(self, request):
        from sales.models import Sale
        from expenses.models import Expense

        try:
            start_date = self._parse_date(request.query_params.get('start_date'), 'start_date')
            end_date = self._parse_date(request.query_params.get('end_date'), 'end_date')  # FIXED: 'en d_date' typo
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
        FIXED: Calculates CUMULATIVE stock in CRATES (all historical intake - all historical sales).
        CONFIRMED: Both IntakeLog.*_crates and Sale.*_quantity represent CRATES.
        """
        from inventory.models import IntakeLog
        from sales.models import Sale

        today = date.today()
        
        # SUM ALL intake logs up to today (critical fix for multiple deliveries)
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

        # Total sales per egg type (in crates - CONFIRMED by Sales model)
        sales = Sale.objects.filter(sale_datetime__date__lte=today)
        total_broken_sold = sales.aggregate(Sum('broken_quantity'))['broken_quantity__sum'] or 0
        total_small_sold = sales.aggregate(Sum('small_quantity'))['small_quantity__sum'] or 0
        total_medium_sold = sales.aggregate(Sum('medium_quantity'))['medium_quantity__sum'] or 0
        total_big_sold = sales.aggregate(Sum('big_quantity'))['big_quantity__sum'] or 0

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