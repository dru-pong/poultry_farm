from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import EggType, PriceTier, IntakeLog
from .serializers import EggTypeSerializer, PriceTierSerializer, IntakeLogSerializer


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