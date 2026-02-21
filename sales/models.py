from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal


class Sale(models.Model):
    """
    Record of egg sales (retail or wholesale).
    Quantities are tracked per egg type with automatic pricing.
    """
    SALE_TYPE_CHOICES = [
        ('retail', 'Retail (Single Sales)'),
        ('wholesale', 'Wholesale'),
    ]
    
    sale_type = models.CharField(max_length=20, choices=SALE_TYPE_CHOICES)
    customer = models.ForeignKey(
        'customers.WholesaleCustomer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales'
    )
    sale_datetime = models.DateTimeField(default=timezone.now)
    broken_quantity = models.IntegerField(default=0)
    small_quantity = models.IntegerField(default=0)
    medium_quantity = models.IntegerField(default=0)
    big_quantity = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-sale_datetime']
        verbose_name = 'Sale'
        verbose_name_plural = 'Sales'
        indexes = [
            models.Index(fields=['sale_datetime']),
            models.Index(fields=['sale_type']),
            models.Index(fields=['customer']),
        ]
    
    def __str__(self):
        customer_str = f" to {self.customer.name}" if self.customer else ""
        return f"{self.get_sale_type_display()} on {self.sale_datetime.date()}{customer_str} - ₵{self.total_amount}"
    
    def clean(self):
        # Validate quantities
        if any(q < 0 for q in [self.broken_quantity, self.small_quantity, self.medium_quantity, self.big_quantity]):
            raise ValidationError("Quantities cannot be negative")
        
        # Wholesale must have a customer
        if self.sale_type == 'wholesale' and not self.customer:
            raise ValidationError("Wholesale sales require a customer")
        
        # Retail should not have a customer
        if self.sale_type == 'retail' and self.customer:
            raise ValidationError("Retail sales should not have a customer assigned")
    
    def calculate_total(self):
        """
        Calculate total amount based on sale type and applicable prices.
        Returns Decimal total.
        """
        from inventory.models import EggType, PriceTier
        from customers.models import CustomerPriceOverride
        
        total = Decimal('0.00')
        
        # Get egg types
        try:
            broken = EggType.objects.get(name='Broken')
            small = EggType.objects.get(name='Small')
            medium = EggType.objects.get(name='Medium')
            big = EggType.objects.get(name='Big')
        except EggType.DoesNotExist:
            # Fallback if egg types not set up yet
            return Decimal('0.00')
        
        # Determine pricing tier
        if self.sale_type == 'retail':
            tier = 'retail'
        else:  # wholesale
            tier = 'wholesale_base'
        
        # Helper to get price for an egg type
        def get_price(egg_type, quantity):
            if quantity <= 0:
                return Decimal('0.00')
            
            price = Decimal('0.00')
            
            # For wholesale with customer, check for override first
            if self.sale_type == 'wholesale' and self.customer:
                override = CustomerPriceOverride.objects.filter(
                    customer=self.customer,
                    egg_type=egg_type,
                    effective_date__lte=self.sale_datetime.date()
                ).order_by('-effective_date').first()
                
                if override and override.price_per_crate is not None:
                    price = override.price_per_crate
                    return price * quantity
            
            # Fall back to base tier price
            base_price = PriceTier.objects.filter(
                tier=tier,
                egg_type=egg_type,
                effective_date__lte=self.sale_datetime.date(),
                is_active=True
            ).order_by('-effective_date').first()
            
            if base_price:
                price = base_price.price_per_crate
                return price * quantity
            
            return Decimal('0.00')
        
        # Calculate totals per egg type
        total += get_price(broken, self.broken_quantity)
        total += get_price(small, self.small_quantity)
        total += get_price(medium, self.medium_quantity)
        total += get_price(big, self.big_quantity)
        
        return total
    
    def save(self, *args, **kwargs):
        # Calculate total before saving
        self.total_amount = self.calculate_total()
        super().save(*args, **kwargs)