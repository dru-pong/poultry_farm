from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Sale
from .serializers import SaleSerializer
from rest_framework.decorators import action
from rest_framework.response import Response


class SaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sales (retail and wholesale).
    Total amount is auto-calculated on save.
    """
    queryset = Sale.objects.select_related('customer', 'created_by').all()
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sale_type', 'customer', 'sale_datetime']
    search_fields = ['notes', 'customer__name']
    ordering_fields = ['sale_datetime', 'total_amount', 'created_at']
    ordering = ['-sale_datetime']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='daily-summary')
    def daily_summary(self, request):
        """
        Get daily sales summary (total revenue, count by type).
        """
        from django.db.models import Sum, Count, Q
        from decimal import Decimal
        from datetime import date
        
        today = date.today()
        sales_today = Sale.objects.filter(sale_datetime__date=today)
        
        summary = {
            'date': today,
            'total_sales': sales_today.count(),
            'total_revenue': sales_today.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'retail_count': sales_today.filter(sale_type='retail').count(),
            'wholesale_count': sales_today.filter(sale_type='wholesale').count(),
            'retail_revenue': sales_today.filter(sale_type='retail').aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'wholesale_revenue': sales_today.filter(sale_type='wholesale').aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        }
        
        return Response(summary)