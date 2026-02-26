from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import WholesaleCustomer
from .serializers import WholesaleCustomerSerializer


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