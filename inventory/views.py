from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import EggType, PriceTier, IntakeLog
from .serializers import EggTypeSerializer, PriceTierSerializer, IntakeLogSerializer
from django.utils import timezone  # Added import for timezone


class EggTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing egg types.
    """
    queryset = EggType.objects.all()
    serializer_class = EggTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']


class PriceTierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing price tiers (retail & wholesale).
    """
    queryset = PriceTier.objects.select_related('egg_type').all()
    serializer_class = PriceTierSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tier', 'egg_type', 'is_active', 'effective_date']
    search_fields = ['egg_type__name']
    ordering_fields = ['effective_date', 'tier', 'price_per_crate']
    ordering = ['-effective_date']
    
    @action(detail=False, methods=['get'], url_path='current-prices')
    def current_prices(self, request):
        """
        Get current prices for all egg types based on sale type.
        Usage: /api/inventory/price-tiers/current-prices/?sale_type=retail
        """
        sale_type = request.query_params.get('sale_type', 'retail')
        
        # Determine the tier based on sale type
        if sale_type == 'retail':
            tier = 'retail'
        else:  # wholesale
            tier = 'wholesale_base'
        
        # Get the most recent active price for each egg type
        current_prices = []
        egg_types = EggType.objects.filter(is_active=True)
        
        for egg_type in egg_types:
            current_price = PriceTier.objects.filter(
                egg_type=egg_type,
                tier=tier,
                is_active=True,
                effective_date__lte=timezone.now().date()
            ).order_by('-effective_date').first()
            
            current_prices.append({
                'egg_type_id': egg_type.id,
                'egg_type_name': egg_type.name,
                'price_per_crate': float(current_price.price_per_crate) if current_price else 0.0
            })
        
        return Response(current_prices)


class IntakeLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing daily intake logs.
    """
    queryset = IntakeLog.objects.select_related('created_by').all()
    serializer_class = IntakeLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['recorded_date']
    search_fields = ['notes']
    ordering_fields = ['recorded_date', 'created_at']
    ordering = ['-recorded_date']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)