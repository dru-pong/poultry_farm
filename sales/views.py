from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Sale
from .serializers import SaleSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from datetime import date


class SaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sales (retail and wholesale).
    Total amount is auto-calculated on save.
    """
    queryset = Sale.objects.select_related('customer', 'created_by').prefetch_related('items__egg_type').all()
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sale_type', 'customer', 'sale_datetime']
    search_fields = ['notes', 'customer__name']
    ordering_fields = ['sale_datetime', 'total_amount', 'created_at']
    ordering = ['-sale_datetime']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Ensure update operations properly handle nested items"""
        serializer.save()
    
    @action(detail=False, methods=['get'], url_path='daily-summary')
    def daily_summary(self, request):
        """
        Get daily sales summary (total revenue, count by type).
        """
        today = date.today()
        sales_today = Sale.objects.filter(sale_datetime__date=today)
        
        # Use database aggregation for better performance
        summary_data = sales_today.aggregate(
            total_sales=Count('id'),
            total_revenue=Sum('total_amount'),
            retail_count=Count('id', filter=Q(sale_type='retail')),
            wholesale_count=Count('id', filter=Q(sale_type='wholesale')),
            retail_revenue=Sum('total_amount', filter=Q(sale_type='retail')),
            wholesale_revenue=Sum('total_amount', filter=Q(sale_type='wholesale'))
        )
        
        # Handle None values from aggregation
        summary = {
            'date': today,
            'total_sales': summary_data['total_sales'] or 0,
            'total_revenue': float(summary_data['total_revenue'] or 0),
            'retail_count': summary_data['retail_count'] or 0,
            'wholesale_count': summary_data['wholesale_count'] or 0,
            'retail_revenue': float(summary_data['retail_revenue'] or 0),
            'wholesale_revenue': float(summary_data['wholesale_revenue'] or 0),
        }
        
        return Response(summary)