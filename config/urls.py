"""
URL Configuration for Poultry AI project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
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

# ✅ Catch-all route for Quasar frontend (must be LAST)
# This serves index.html for any route not matched above, enabling Vue Router
urlpatterns += [
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]