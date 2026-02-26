from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WholesaleCustomerViewSet

router = DefaultRouter()
router.register(r'customers', WholesaleCustomerViewSet, basename='customer')

app_name = 'customers'

urlpatterns = [
    path('', include(router.urls)),
]