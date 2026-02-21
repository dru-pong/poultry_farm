from django.contrib import admin
from django.contrib.auth.models import User, Group
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model', 'record_id']
    list_filter = ['action', 'model', 'timestamp']
    search_fields = ['user__username', 'model', 'details']
    readonly_fields = ['user', 'action', 'model', 'record_id', 'timestamp', 'details', 'ip_address']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
