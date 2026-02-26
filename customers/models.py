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