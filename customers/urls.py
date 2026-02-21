from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WholesaleCustomerViewSet, CustomerPriceOverrideViewSet

router = DefaultRouter()
router.register(r'customers', WholesaleCustomerViewSet, basename='customer')
router.register(r'customer-price-overrides', CustomerPriceOverrideViewSet, basename='customer-price-override')

app_name = 'customers'

urlpatterns = [
    path('', include(router.urls)),
]