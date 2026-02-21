from django.contrib import admin
from .models import WholesaleCustomer, CustomerPriceOverride


@admin.register(WholesaleCustomer)
class WholesaleCustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email', 'is_active', 'created_at']
    list_editable = ['is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'phone', 'email', 'address']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'contact_person', 'is_active')
        }),
        ('Contact Details', {
            'fields': ('phone', 'email', 'address')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomerPriceOverride)
class CustomerPriceOverrideAdmin(admin.ModelAdmin):
    list_display = ['customer', 'egg_type', 'price_per_crate', 'effective_date', 'notes']
    list_filter = ['customer', 'egg_type', 'effective_date']
    search_fields = ['customer__name', 'egg_type__name', 'notes']
    ordering = ['-effective_date', 'customer', 'egg_type']
    date_hierarchy = 'effective_date'
    
    fieldsets = (
        ('Customer & Egg Type', {
            'fields': ('customer', 'egg_type')
        }),
        ('Pricing', {
            'fields': ('price_per_crate', 'effective_date', 'notes')
        }),
    )
