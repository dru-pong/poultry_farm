"""
URL Configuration for Poultry AI project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', obtain_auth_token, name='api_login'),  # ← Token login
    path('api/auth/logout/', lambda request: None, name='api_logout'),  # Simple logout

    path('api/', include('core.urls')),    

    # API endpoints for all apps
    path('api/core/', include('core.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/expenses/', include('expenses.urls')),
    path('api/customers/', include('customers.urls')),
    path('api/reports/', include('reports.urls')),
]



# ✅ Serve media files in development (Whitenoise handles static in production)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

