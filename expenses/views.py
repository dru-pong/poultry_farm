from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from datetime import date, timedelta
from .models import ExpenseCategory, Expense
from .serializers import ExpenseCategorySerializer, ExpenseSerializer


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing expense categories.
    """
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing expenses.
    """
    queryset = Expense.objects.select_related('category', 'created_by').all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['date', 'category', 'payment_method', 'is_recurring']
    search_fields = ['description', 'notes', 'category__name']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date', '-created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get expense summary for a date range.
        Query params: start_date, end_date (optional, defaults to current month)
        """
        from django.utils import timezone
        
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            # Default to current month
            today = date.today()
            start_date = date(today.year, today.month, 1)
            # Get last day of month
            if today.month == 12:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
        else:
            start_date = date.fromisoformat(start_date)
            end_date = date.fromisoformat(end_date)
        
        # Filter expenses in date range
        expenses = Expense.objects.filter(date__range=[start_date, end_date])
        
        # Calculate totals
        total_expenses = expenses.count()
        total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Group by category
        category_breakdown = expenses.values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        summary = {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
            },
            'total_expenses': total_expenses,
            'total_amount': total_amount,
            'category_breakdown': list(category_breakdown),
        }
        
        return Response(summary)