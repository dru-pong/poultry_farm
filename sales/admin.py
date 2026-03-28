from django.contrib import admin
from .models import Sale, SaleItem, CreditPayment


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['line_total']
    autocomplete_fields = ['egg_type']


class CreditPaymentInline(admin.TabularInline):
    model = CreditPayment
    extra = 0
    readonly_fields = ['created_at']
    autocomplete_fields = ['customer']
    fk_name = 'sale'


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = [
        'sale_datetime', 'sale_type', 'customer', 'total_amount',
        'amount_paid', 'payment_status', 'get_items_summary'
    ]
    list_filter = ['sale_type', 'payment_status', 'sale_datetime', 'customer']
    search_fields = ['notes', 'customer__name']
    date_hierarchy = 'sale_datetime'
    autocomplete_fields = ['customer']
    inlines = [SaleItemInline, CreditPaymentInline]

    def get_items_summary(self, obj):
        items = obj.items.all()
        if not items:
            return "No items"
        return ", ".join([f"{item.quantity}x {item.egg_type.name}" for item in items])
    get_items_summary.short_description = 'Items'

    fieldsets = (
        ('Basic Information', {
            'fields': ('sale_type', 'customer', 'sale_datetime', 'total_amount', 'notes')
        }),
        ('Payment', {
            'fields': ('amount_paid', 'payment_status')
        }),
    )

    readonly_fields = ['total_amount', 'payment_status']
    ordering = ['-sale_datetime']


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'egg_type', 'quantity', 'price_per_crate', 'line_total']
    list_filter = ['egg_type', 'sale__sale_datetime']
    search_fields = ['sale__notes']
    autocomplete_fields = ['sale', 'egg_type']
    readonly_fields = ['line_total']


@admin.register(CreditPayment)
class CreditPaymentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'amount_paid', 'payment_date', 'sale', 'recorded_by']
    list_filter = ['payment_date', 'customer']
    search_fields = ['customer__name', 'notes']
    autocomplete_fields = ['customer', 'sale']
    readonly_fields = ['created_at']
    ordering = ['-payment_date']