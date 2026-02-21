from rest_framework import serializers

# ===== NESTED SERIALIZERS FOR STRUCTURED RESPONSES =====
class PeriodSerializer(serializers.Serializer):
    """Reusable period structure (ISO date strings)"""
    start_date = serializers.CharField(help_text="ISO format: YYYY-MM-DD")
    end_date = serializers.CharField(help_text="ISO format: YYYY-MM-DD")

class QuantitiesSerializer(serializers.Serializer):
    """Egg type quantities in CRATES"""
    broken = serializers.IntegerField(min_value=0)
    small = serializers.IntegerField(min_value=0)
    medium = serializers.IntegerField(min_value=0)
    big = serializers.IntegerField(min_value=0)

class RevenueBreakdownSerializer(serializers.Serializer):
    """Revenue split by sale type (stringified decimals)"""
    retail = serializers.CharField(help_text="Decimal string (e.g., '1500.00')")
    wholesale = serializers.CharField(help_text="Decimal string (e.g., '3500.00')")

class ExpenseBreakdownItemSerializer(serializers.Serializer):
    """Single expense category entry"""
    category__name = serializers.CharField(source='name', help_text="Category name")
    total = serializers.CharField(help_text="Decimal string of total amount")

class LowStockAlertSerializer(serializers.Serializer):
    """Low stock alert with crate context"""
    egg_type = serializers.ChoiceField(choices=['broken', 'small', 'medium', 'big'])
    available_crates = serializers.IntegerField(min_value=0)
    threshold_crates = serializers.IntegerField(min_value=1)


# ===== MAIN REPORT SERIALIZERS =====
class DashboardSummarySerializer(serializers.Serializer):
    """
    Matches /reports/dashboard_summary/ response structure.
    ALL monetary values are STRINGIFIED decimals. Date is ISO string.
    """
    date = serializers.CharField(help_text="Report date (ISO format)")
    revenue = serializers.CharField(help_text="Total revenue as decimal string")
    expenses = serializers.CharField(help_text="Total expenses amount as decimal string")
    profit = serializers.CharField(help_text="Net profit as decimal string")
    profit_margin = serializers.FloatField(help_text="Percentage rounded to 2 decimals")
    total_sales = serializers.IntegerField(min_value=0)
    total_expenses_count = serializers.IntegerField(
        min_value=0,
        help_text="Count of expense records (NOT monetary total)"
    )

class SalesReportSerializer(serializers.Serializer):
    """
    Matches /reports/sales_report/ response structure.
    Quantities are in CRATES (confirmed by Sales model).
    """
    period = PeriodSerializer()
    total_sales = serializers.IntegerField(min_value=0)
    total_revenue = serializers.CharField(help_text="Decimal string")
    retail_count = serializers.IntegerField(min_value=0)
    wholesale_count = serializers.IntegerField(min_value=0)
    retail_revenue = serializers.CharField(help_text="Decimal string")
    wholesale_revenue = serializers.CharField(help_text="Decimal string")
    quantities = QuantitiesSerializer(help_text="Quantities sold in CRATES")

class ProfitLossSerializer(serializers.Serializer):
    """
    Matches /reports/profit_loss/ response structure.
    CRITICAL: expense_breakdown items MUST have 'total' as stringified decimal.
    """
    period = PeriodSerializer()
    total_revenue = serializers.CharField(help_text="Decimal string")
    total_expenses = serializers.CharField(help_text="Decimal string")
    net_profit = serializers.CharField(help_text="Decimal string")
    profit_margin = serializers.FloatField(help_text="Percentage rounded to 2 decimals")
    revenue_breakdown = RevenueBreakdownSerializer()
    expense_breakdown = ExpenseBreakdownItemSerializer(many=True, help_text="List of category totals")

class InventoryStatusSerializer(serializers.Serializer):
    """
    Matches /reports/inventory_status/ response structure.
    ALL values represent PHYSICAL CRATES (confirmed by business logic).
    """
    unit = serializers.CharField(default='crates', read_only=True, help_text="ALL values are in crates")
    broken_available = serializers.IntegerField(min_value=0, help_text="Available broken crates")
    small_available = serializers.IntegerField(min_value=0, help_text="Available small crates")
    medium_available = serializers.IntegerField(min_value=0, help_text="Available medium crates")
    big_available = serializers.IntegerField(min_value=0, help_text="Available big crates")
    total_available = serializers.IntegerField(min_value=0, help_text="Sum of all available crates")
    low_stock_alerts = LowStockAlertSerializer(many=True, help_text="Alerts where available < threshold")
    calculation_date = serializers.CharField(help_text="ISO date of calculation")
    note = serializers.CharField(
        default="Stock = SUM(all intake crates) - SUM(all sales crates). Values represent physical crates.",
        read_only=True
    )


# ===== UNUSED (Preserved for potential future use) =====
class ExpenseReportSerializer(serializers.Serializer):
    """
    NOT USED in current ReportViewSet actions.
    Preserved in case needed for other endpoints.
    """
    date = serializers.DateField()
    total_expenses = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    category_breakdown = serializers.ListField()