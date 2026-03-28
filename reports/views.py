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
        if not date_str:
            raise ValidationError(f"'{param_name}' is required")
        try:
            return date.fromisoformat(date_str)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid '{param_name}' format. Use YYYY-MM-DD")

    # ─── DASHBOARD SUMMARY ──────────────────────────────────────────────

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
        total_expenses_count = expenses.count()

        profit = total_revenue - total_expenses_amount
        profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else Decimal('0.00')

        return Response({
            'date': report_date.isoformat(),
            'revenue': str(total_revenue),
            'expenses': str(total_expenses_amount),
            'profit': str(profit),
            'profit_margin': round(profit_margin, 2),
            'total_sales': total_sales_count,
            'total_expenses_count': total_expenses_count,
        })

    # ─── SALES TREND ────────────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='sales-trend')
    def sales_trend(self, request):
        from sales.models import Sale
        from django.db.models import Sum

        try:
            days = int(request.query_params.get('days', 7))
            days = max(1, min(days, 30))
        except (ValueError, TypeError):
            days = 7

        today = date.today()
        start_date = today - timedelta(days=days - 1)

        sales_data = Sale.objects.filter(
            sale_datetime__date__range=[start_date, today]
        ).values('sale_datetime__date').annotate(
            total=Sum('total_amount')
        ).order_by('sale_datetime__date')

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
            'categories': categories,
            'values': values,
            'days': days
        })

    # ─── SALES REPORT ───────────────────────────────────────────────────

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

        try:
            broken_type = EggType.objects.get(name='Broken')
            small_type = EggType.objects.get(name='Small')
            medium_type = EggType.objects.get(name='Medium')
            big_type = EggType.objects.get(name='Big')
        except EggType.DoesNotExist:
            broken_type = small_type = medium_type = big_type = None

        quantities = {'broken': 0, 'small': 0, 'medium': 0, 'big': 0}

        if broken_type and small_type and medium_type and big_type:
            sale_items = SaleItem.objects.filter(sale__in=sales)
            quantities['broken'] = sale_items.filter(egg_type=broken_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
            quantities['small'] = sale_items.filter(egg_type=small_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
            quantities['medium'] = sale_items.filter(egg_type=medium_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
            quantities['big'] = sale_items.filter(egg_type=big_type).aggregate(Sum('quantity'))['quantity__sum'] or 0

        report = {
            'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
            'total_sales': sales.count(),
            'total_revenue': str(total_revenue),
            'retail_count': retail_sales.count(),
            'wholesale_count': wholesale_sales.count(),
            'retail_revenue': str(retail_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')),
            'wholesale_revenue': str(wholesale_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')),
            'quantities': quantities
        }
        return Response(report)

    # ─── PROFIT & LOSS ──────────────────────────────────────────────────

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
            'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
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

    # ─── INVENTORY STATUS ───────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='inventory-status')
    def inventory_status(self, request):
        from inventory.models import IntakeLog
        from sales.models import Sale, SaleItem

        today = date.today()

        intake_logs = IntakeLog.objects.filter(recorded_date__lte=today)
        if not intake_logs.exists():
            return Response({'error': 'No intake records found.'}, status=404)

        total_broken_intake = intake_logs.aggregate(Sum('broken_crates'))['broken_crates__sum'] or 0
        total_small_intake = intake_logs.aggregate(Sum('small_crates'))['small_crates__sum'] or 0
        total_medium_intake = intake_logs.aggregate(Sum('medium_crates'))['medium_crates__sum'] or 0
        total_big_intake = intake_logs.aggregate(Sum('big_crates'))['big_crates__sum'] or 0

        try:
            broken_type = EggType.objects.get(name='Broken')
            small_type = EggType.objects.get(name='Small')
            medium_type = EggType.objects.get(name='Medium')
            big_type = EggType.objects.get(name='Big')
        except EggType.DoesNotExist:
            return Response({'error': 'Egg types not configured.'}, status=404)

        sales = Sale.objects.filter(sale_datetime__date__lte=today)
        sale_items = SaleItem.objects.filter(sale__in=sales)

        total_broken_sold = sale_items.filter(egg_type=broken_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_small_sold = sale_items.filter(egg_type=small_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_medium_sold = sale_items.filter(egg_type=medium_type).aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_big_sold = sale_items.filter(egg_type=big_type).aggregate(Sum('quantity'))['quantity__sum'] or 0

        broken_available = max(0, total_broken_intake - total_broken_sold)
        small_available = max(0, total_small_intake - total_small_sold)
        medium_available = max(0, total_medium_intake - total_medium_sold)
        big_available = max(0, total_big_intake - total_big_sold)
        total_available = broken_available + small_available + medium_available + big_available

        low_stock_alerts = []
        threshold = 10
        for egg_type, available in [
            ('broken', broken_available), ('small', small_available),
            ('medium', medium_available), ('big', big_available)
        ]:
            if available < threshold:
                low_stock_alerts.append({
                    'egg_type': egg_type,
                    'available_crates': available,
                    'threshold_crates': threshold
                })

        return Response({
            'broken_available': broken_available,
            'small_available': small_available,
            'medium_available': medium_available,
            'big_available': big_available,
            'total_available': total_available,
            'low_stock_alerts': low_stock_alerts,
            'calculation_date': today.isoformat(),
            'note': 'Stock calculated as: SUM(all intakes up to today) - SUM(all sales up to today)'
        })

    # ─── EXPENSES REPORT ────────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='expenses-report')
    def expenses_report(self, request):
        from expenses.models import Expense, ExpenseCategory

        try:
            start_date = self._parse_date(request.query_params.get('start_date'), 'start_date')
            end_date = self._parse_date(request.query_params.get('end_date'), 'end_date')
            if start_date > end_date:
                return Response({'error': 'start_date cannot be after end_date'}, status=400)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        expenses = Expense.objects.filter(date__range=[start_date, end_date])
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        number_of_days = (end_date - start_date).days + 1
        average_per_day = (total_expenses / number_of_days).quantize(Decimal('0.01')) if number_of_days > 0 else Decimal('0.00')

        category_breakdown = []
        categories = ExpenseCategory.objects.filter(is_active=True)
        for category in categories:
            cat_expenses = expenses.filter(category=category)
            cat_total = cat_expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            if cat_total > 0:
                category_breakdown.append({
                    'category': category.name,
                    'total': str(cat_total),
                    'count': cat_expenses.count(),
                    'items': [{
                        'id': e.id, 'date': str(e.date),
                        'description': e.description, 'amount': str(e.amount),
                        'notes': e.notes or ''
                    } for e in cat_expenses]
                })

        daily_expenses = {}
        current_date = start_date
        while current_date <= end_date:
            day_total = expenses.filter(date=current_date).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            daily_expenses[str(current_date)] = str(day_total)
            current_date += timedelta(days=1)

        return Response({
            'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
            'total_expenses': str(total_expenses),
            'average_expense_per_day': str(average_per_day),
            'number_of_days': number_of_days,
            'category_breakdown': category_breakdown,
            'daily_expenses': daily_expenses,
            'expense_count': expenses.count()
        })

    @action(detail=False, methods=['get'], url_path='expenses-report/excel')
    def expenses_report_excel(self, request):
        from expenses.models import Expense, ExpenseCategory
        from .utils import create_expenses_excel_report
        from django.http import HttpResponse

        try:
            start_date = self._parse_date(request.query_params.get('start_date'), 'start_date')
            end_date = self._parse_date(request.query_params.get('end_date'), 'end_date')
            if start_date > end_date:
                return Response({'error': 'start_date cannot be after end_date'}, status=400)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        expenses = Expense.objects.filter(date__range=[start_date, end_date])
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        number_of_days = (end_date - start_date).days + 1
        average_per_day = (total_expenses / number_of_days).quantize(Decimal('0.01')) if number_of_days > 0 else Decimal('0.00')

        category_breakdown = []
        categories = ExpenseCategory.objects.filter(is_active=True)
        for category in categories:
            cat_expenses = expenses.filter(category=category)
            cat_total = cat_expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            if cat_total > 0:
                category_breakdown.append({
                    'category': category.name,
                    'total': str(cat_total),
                    'count': cat_expenses.count(),
                    'items': [{
                        'id': e.id, 'date': str(e.date),
                        'description': e.description, 'amount': str(e.amount),
                        'notes': e.notes or ''
                    } for e in cat_expenses]
                })

        daily_expenses = {}
        current_date = start_date
        while current_date <= end_date:
            day_total = expenses.filter(date=current_date).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            daily_expenses[str(current_date)] = str(day_total)
            current_date += timedelta(days=1)

        report_data = {
            'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
            'total_expenses': str(total_expenses),
            'average_expense_per_day': str(average_per_day),
            'number_of_days': number_of_days,
            'category_breakdown': category_breakdown,
            'daily_expenses': daily_expenses,
            'expense_count': expenses.count()
        }

        wb = create_expenses_excel_report(report_data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=expenses_report_{start_date}_to_{end_date}.xlsx'
        wb.save(response)
        return response

    # ─── SALES REPORT EXCEL ─────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='sales-report/excel')
    def sales_report_excel(self, request):
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

        sales = Sale.objects.filter(sale_datetime__date__range=[start_date, end_date])
        total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        total_sales = sales.count()
        retail_sales = sales.filter(sale_type='retail')
        wholesale_sales = sales.filter(sale_type='wholesale')

        egg_types = {
            'Broken': EggType.objects.filter(name='Broken').first(),
            'Small': EggType.objects.filter(name='Small').first(),
            'Medium': EggType.objects.filter(name='Medium').first(),
            'Big': EggType.objects.filter(name='Big').first(),
        }

        sale_items = SaleItem.objects.filter(sale__in=sales).select_related('egg_type', 'sale__customer')

        customer_breakdown = []
        customers = WholesaleCustomer.objects.filter(is_active=True)
        for customer in customers:
            c_sales = sales.filter(customer=customer)
            if c_sales.exists():
                c_total = c_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
                customer_breakdown.append({
                    'customer': customer.name,
                    'total': str(c_total),
                    'transaction_count': c_sales.count(),
                })

        daily_sales = {}
        current_date = start_date
        while current_date <= end_date:
            day_sales = sales.filter(sale_datetime__date=current_date)
            day_revenue = day_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
            daily_sales[str(current_date)] = {'count': day_sales.count(), 'revenue': str(day_revenue)}
            current_date += timedelta(days=1)

        egg_type_breakdown = []
        for egg_name, egg_type in egg_types.items():
            if egg_type:
                type_items = sale_items.filter(egg_type=egg_type)
                total_crates = type_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
                type_revenue = sum(item.line_total for item in type_items)
                egg_type_breakdown.append({
                    'egg_type': egg_name, 'total_crates': total_crates, 'revenue': str(type_revenue),
                })

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

        report_data = {
            'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
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

        wb = create_sales_excel_report(report_data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=sales_report_{start_date}_to_{end_date}.xlsx'
        wb.save(response)
        return response

    # ─── PROFIT & LOSS EXCEL ────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='profit-loss/excel')
    def profit_loss_excel(self, request):
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

        sales = Sale.objects.filter(sale_datetime__date__range=[start_date, end_date])
        expenses = Expense.objects.filter(date__range=[start_date, end_date])

        total_revenue = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        net_profit = total_revenue - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0.00')

        retail_sales = sales.filter(sale_type='retail')
        wholesale_sales = sales.filter(sale_type='wholesale')

        expense_breakdown = list(
            expenses.values('category__name').annotate(total=Sum('amount')).order_by('-total')
        )

        report_data = {
            'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
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

        wb = create_profit_loss_excel_report(report_data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=profit_loss_report_{start_date}_to_{end_date}.xlsx'
        wb.save(response)
        return response

    # ─── CUSTOMER REPORT (JSON) ─────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='customer-report')
    def customer_report(self, request):
        """
        Per-customer breakdown: egg types, daily history (active days only),
        credit payment history, outstanding balance.

        Optimised: bulk-fetches all data in a handful of queries instead of
        N+1 per customer.
        """
        from sales.models import Sale, SaleItem, CreditPayment
        from customers.models import WholesaleCustomer
        from inventory.models import EggType
        from django.db.models import F
        from collections import defaultdict

        try:
            start_date = self._parse_date(request.query_params.get('start_date'), 'start_date')
            end_date = self._parse_date(request.query_params.get('end_date'), 'end_date')
            if start_date > end_date:
                return Response({'error': 'start_date cannot be after end_date'}, status=400)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        # ── 1. All-time balance aggregates (2 queries) ──────────────────
        alltime_sales_agg = (
            Sale.objects
            .filter(customer__isnull=False)
            .values('customer_id')
            .annotate(
                total_purchased=Sum('total_amount'),
                total_upfront=Sum('amount_paid'),
            )
        )
        alltime_map = {
            row['customer_id']: row for row in alltime_sales_agg
        }

        alltime_credit_agg = (
            CreditPayment.objects
            .values('customer_id')
            .annotate(total_credit=Sum('amount_paid'))
        )
        credit_alltime_map = {
            row['customer_id']: row['total_credit'] for row in alltime_credit_agg
        }

        # ── 2. In-range sales (1 query, prefetch items) ────────────────
        range_sales = list(
            Sale.objects
            .filter(
                customer__isnull=False,
                sale_datetime__date__range=[start_date, end_date],
            )
            .select_related('customer')
            .prefetch_related('items__egg_type')
            .order_by('customer_id', 'sale_datetime')
        )

        # Group sales by customer
        sales_by_customer = defaultdict(list)
        for sale in range_sales:
            sales_by_customer[sale.customer_id].append(sale)

        # ── 3. In-range credit payments (1 query) ──────────────────────
        range_credits = list(
            CreditPayment.objects
            .filter(payment_date__date__range=[start_date, end_date])
            .order_by('customer_id', 'payment_date')
        )
        credits_by_customer = defaultdict(list)
        for cp in range_credits:
            credits_by_customer[cp.customer_id].append(cp)

        # ── 4. Active egg types (1 query) ──────────────────────────────
        active_egg_types = list(EggType.objects.filter(is_active=True).order_by('order'))

        # ── 5. Build response per customer ──────────────────────────────
        # Only include customers that have sales in the range
        customer_ids_with_sales = set(sales_by_customer.keys())
        customers_qs = (
            WholesaleCustomer.objects
            .filter(is_active=True, id__in=customer_ids_with_sales)
            .order_by('name')
        )

        customers_data = []
        for customer in customers_qs:
            cid = customer.id
            c_sales = sales_by_customer.get(cid, [])

            # All-time balance
            at = alltime_map.get(cid, {})
            total_purchased_alltime = at.get('total_purchased') or Decimal('0.00')
            total_upfront_alltime = at.get('total_upfront') or Decimal('0.00')
            total_credit_alltime = credit_alltime_map.get(cid) or Decimal('0.00')
            outstanding_balance = total_purchased_alltime - total_upfront_alltime - total_credit_alltime

            # In-range totals
            range_total = sum(s.total_amount for s in c_sales)
            range_paid = sum(s.amount_paid for s in c_sales)

            # Egg type breakdown (from prefetched items)
            egg_qty = defaultdict(int)
            egg_rev = defaultdict(Decimal)
            for sale in c_sales:
                for item in sale.items.all():  # already prefetched
                    egg_qty[item.egg_type_id] += item.quantity
                    egg_rev[item.egg_type_id] += item.line_total

            egg_breakdown = []
            for et in active_egg_types:
                qty = egg_qty.get(et.id, 0)
                if qty > 0:
                    egg_breakdown.append({
                        'egg_type': et.name,
                        'crates': qty,
                        'revenue': str(egg_rev.get(et.id, Decimal('0.00'))),
                    })

            # Daily purchase history
            running_balance = Decimal('0.00')
            daily_history = []
            for sale in c_sales:
                sale_balance = sale.total_amount - sale.amount_paid
                running_balance += sale_balance

                items_detail = [{
                    'egg_type': item.egg_type.name,
                    'crates': item.quantity,
                    'price_per_crate': str(item.price_per_crate or Decimal('0.00')),
                    'line_total': str(item.line_total),
                } for item in sale.items.all()]

                daily_history.append({
                    'date': sale.sale_datetime.date().isoformat(),
                    'sale_id': sale.id,
                    'items': items_detail,
                    'sale_total': str(sale.total_amount),
                    'amount_paid': str(sale.amount_paid),
                    'payment_status': sale.payment_status,
                    'running_balance': str(running_balance),
                })

            # Credit payment history
            credit_history = [{
                'id': cp.id,
                'date': cp.payment_date.date().isoformat(),
                'amount': str(cp.amount_paid),
                'sale_id': cp.sale_id,
                'notes': cp.notes,
            } for cp in credits_by_customer.get(cid, [])]

            customers_data.append({
                'customer_id': cid,
                'customer_name': customer.name,
                'phone': customer.phone,
                'summary': {
                    'total_purchased_in_range': str(range_total),
                    'total_paid_in_range': str(range_paid),
                    'transaction_count': len(c_sales),
                    'outstanding_balance_alltime': str(outstanding_balance),
                },
                'egg_breakdown': egg_breakdown,
                'daily_history': daily_history,
                'credit_payments': credit_history,
            })

        # Sort by outstanding balance descending
        customers_data.sort(
            key=lambda x: Decimal(x['summary']['outstanding_balance_alltime']),
            reverse=True
        )

        return Response({
            'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
            'customer_count': len(customers_data),
            'customers': customers_data,
        })

    # ─── CUSTOMER REPORT EXCEL ──────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='customer-report/excel')
    def customer_report_excel(self, request):
        """Export customer report as Excel — reuses the optimised JSON logic."""
        from .utils import create_customer_excel_report
        from django.http import HttpResponse

        # Reuse the JSON endpoint to build report_data
        json_response = self.customer_report(request)
        if json_response.status_code != 200:
            return json_response

        report_data = json_response.data

        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
        except Exception:
            start_date = 'report'
            end_date = 'report'

        wb = create_customer_excel_report(report_data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=customer_report_{start_date}_to_{end_date}.xlsx'
        wb.save(response)
        return response