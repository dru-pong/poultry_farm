from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet
from . import views
router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

app_name = 'core'

urlpatterns = [
    path('', include(router.urls)),
    path('health-check/', views.health_check, name='health_check'),
]