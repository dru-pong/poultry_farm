from django.contrib import admin
from .models import Sale


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_datetime', 'sale_type', 'customer', 'broken_quantity', 'small_quantity', 'medium_quantity', 'big_quantity', 'total_amount', 'created_by']
    list_filter = ['sale_type', 'sale_datetime', 'customer', 'created_by']
    search_fields = ['notes', 'customer__name']
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    date_hierarchy = 'sale_datetime'
    ordering = ['-sale_datetime']
    
    fieldsets = (
        ('Sale Information', {
            'fields': ('sale_type', 'customer', 'sale_datetime', 'total_amount')
        }),
        ('Quantities', {
            'fields': (('broken_quantity', 'small_quantity'), ('medium_quantity', 'big_quantity'))
        }),
        ('Notes & Metadata', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Allow editing quantities but keep total_amount auto-calculated
        if obj:
            return ['total_amount', 'created_at', 'updated_at']
        return ['total_amount', 'created_at', 'updated_at']