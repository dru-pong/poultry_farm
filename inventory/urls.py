from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EggTypeViewSet, PriceTierViewSet, IntakeLogViewSet

router = DefaultRouter()
router.register(r'egg-types', EggTypeViewSet, basename='egg-type')
router.register(r'price-tiers', PriceTierViewSet, basename='price-tier')
router.register(r'intake-logs', IntakeLogViewSet, basename='intake-log')

app_name = 'inventory'

urlpatterns = [
    path('', include(router.urls)),
]