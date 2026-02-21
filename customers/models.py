from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class WholesaleCustomer(models.Model):
    """
    Wholesale customer profiles with contact information.
    """
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Wholesale Customer'
        verbose_name_plural = 'Wholesale Customers'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if not self.name.strip():
            raise ValidationError("Customer name cannot be empty")


class CustomerPriceOverride(models.Model):
    """
    Custom pricing overrides for specific customers.
    If price is null, system falls back to base wholesale price.
    """
    customer = models.ForeignKey(WholesaleCustomer, on_delete=models.CASCADE, related_name='price_overrides')
    egg_type = models.ForeignKey('inventory.EggType', on_delete=models.CASCADE, related_name='customer_overrides')
    price_per_crate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    effective_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-effective_date']
        verbose_name = 'Customer Price Override'
        verbose_name_plural = 'Customer Price Overrides'
        unique_together = ['customer', 'egg_type', 'effective_date']
    
    def __str__(self):
        price = self.price_per_crate if self.price_per_crate is not None else "Default"
        return f"{self.customer.name} - {self.egg_type.name}: ₵{price}"
    
    def clean(self):
        if self.price_per_crate is not None and self.price_per_crate < 0:
            raise ValidationError("Price cannot be negative")
