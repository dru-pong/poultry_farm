from django.contrib import admin
from .models import ExpenseCategory, Expense


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'order', 'created_at']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['date', 'category', 'description', 'amount', 'payment_method', 'created_by']
    list_filter = ['date', 'category', 'payment_method', 'is_recurring']
    search_fields = ['description', 'notes', 'category__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('date', 'category', 'description', 'amount')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'receipt_file')
        }),
        ('Recurring Settings', {
            'fields': ('is_recurring', 'recurrence_pattern', 'recurrence_end_date'),
            'classes': ('collapse',)
        }),
        ('Notes & Metadata', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at')
        }),
    )