from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FlockViewSet, FlockEventViewSet, EggProductionLogViewSet

router = DefaultRouter()
router.register(r'flocks', FlockViewSet, basename='flock')
router.register(r'events', FlockEventViewSet, basename='flock-event')
router.register(r'egg-production', EggProductionLogViewSet, basename='egg-production')

app_name = 'flock'

urlpatterns = [
    path('', include(router.urls)),
]