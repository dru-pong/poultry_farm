from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import WholesaleCustomer, CustomerPriceOverride
from .serializers import WholesaleCustomerSerializer, CustomerPriceOverrideSerializer


class WholesaleCustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing wholesale customers.
    """
    queryset = WholesaleCustomer.objects.all()
    serializer_class = WholesaleCustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'contact_person', 'phone', 'email', 'address']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class CustomerPriceOverrideViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing customer-specific price overrides.
    """
    queryset = CustomerPriceOverride.objects.select_related('customer', 'egg_type').all()
    serializer_class = CustomerPriceOverrideSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'egg_type', 'effective_date']
    search_fields = ['customer__name', 'egg_type__name', 'notes']
    ordering_fields = ['effective_date', 'created_at']
    ordering = ['-effective_date']