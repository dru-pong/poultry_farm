from django.contrib import admin
from .models import EggType, PriceTier, IntakeLog


@admin.register(EggType)
class EggTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'order', 'created_at']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']


@admin.register(PriceTier)
class PriceTierAdmin(admin.ModelAdmin):
    list_display = ['tier', 'egg_type', 'price_per_crate', 'effective_date', 'is_active']
    list_editable = ['price_per_crate', 'is_active']
    list_filter = ['tier', 'egg_type', 'is_active', 'effective_date']
    search_fields = ['egg_type__name']
    ordering = ['-effective_date', 'tier', 'egg_type']
    date_hierarchy = 'effective_date'


@admin.register(IntakeLog)
class IntakeLogAdmin(admin.ModelAdmin):
    list_display = ['recorded_date', 'broken_crates', 'small_crates', 'medium_crates', 'big_crates', 'total_crates', 'created_by', 'created_at']
    list_filter = ['recorded_date', 'created_by']
    search_fields = ['notes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'recorded_date'
    ordering = ['-recorded_date']
    
    fieldsets = (
        ('Date & Quantities', {
            'fields': ('recorded_date', ('broken_crates', 'small_crates', 'medium_crates', 'big_crates'))
        }),
        ('Notes & Metadata', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at')
        }),
    )