from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SaleViewSet, CreditPaymentViewSet

router = DefaultRouter()
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'credit-payments', CreditPaymentViewSet, basename='credit-payment')

app_name = 'sales'

urlpatterns = [
    path('', include(router.urls)),
]