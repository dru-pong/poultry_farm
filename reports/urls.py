# reports/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet

router = DefaultRouter()
router.register(r'', ReportViewSet, basename='report')  # ✅ CRITICAL: Changed from r'reports' to r''

app_name = 'reports'
urlpatterns = [
    path('', include(router.urls)),  # Routes now live directly under /api/reports/
]