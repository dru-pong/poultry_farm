from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal


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
        # Wholesale must have a customer
        if self.sale_type == 'wholesale' and not self.customer:
            raise ValidationError("Wholesale sales require a customer")
        
        # Retail should not have a customer
        if self.sale_type == 'retail' and self.customer:
            raise ValidationError("Retail sales should not have a customer assigned")
    
    def calculate_total_from_items(self, items_data):
        """
        Calculate total amount based on provided items data (for new sales).
        Returns Decimal total.
        """
        from inventory.models import PriceTier
        
        total = Decimal('0.00')
        
        # Determine pricing tier
        if self.sale_type == 'retail':
            tier = 'retail'
        else:  # wholesale
            tier = 'wholesale_base'
        
        for item_data in items_data:
            # Use overridden price if provided
            if item_data.get('price_per_crate') is not None:
                price = item_data['price_per_crate']
            else:
                # Fall back to base tier price
                base_price = PriceTier.objects.filter(
                    tier=tier,
                    egg_type=item_data['egg_type'],
                    effective_date__lte=self.sale_datetime.date(),
                    is_active=True
                ).order_by('-effective_date').first()
                
                price = base_price.price_per_crate if base_price else Decimal('0.00')
            
            total += item_data['quantity'] * price
        
        return total
    
    def calculate_total(self):
        """
        Calculate total amount based on existing sale items (for saved sales).
        Returns Decimal total.
        """
        total = Decimal('0.00')
        # Only try to access related items if the sale is already saved
        if self.pk:
            for item in self.items.all():
                total += item.line_total
        return total
    
    def save(self, *args, **kwargs):
        # Only calculate total from DB if already saved
        if self.pk:
            self.total_amount = self.calculate_total()
        # For new objects, total_amount should already be set
        super().save(*args, **kwargs)


class SaleItem(models.Model):
    """
    Individual item within a sale, tracking quantity and price.
    """
    sale = models.ForeignKey(
        Sale, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    egg_type = models.ForeignKey(
        'inventory.EggType',
        on_delete=models.PROTECT
    )
    quantity = models.IntegerField(default=0)
    price_per_crate = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True
    )
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False,
        default=0
    )
    
    class Meta:
        verbose_name = 'Sale Item'
        verbose_name_plural = 'Sale Items'
        indexes = [
            models.Index(fields=['sale', 'egg_type']),
        ]
    
    def __str__(self):
        return f"{self.quantity} crates of {self.egg_type.name} in Sale #{self.sale.id}"
    
    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Quantity cannot be negative")
        if self.price_per_crate is not None and self.price_per_crate < 0:
            raise ValidationError("Price per crate cannot be negative")
    
    def calculate_line_total(self):
        """
        Calculate line total based on quantity and price.
        If price_per_crate is None, it will use the current price tier.
        Returns Decimal total.
        """
        from inventory.models import PriceTier
        
        # Use overridden price if provided
        if self.price_per_crate is not None:
            return self.quantity * self.price_per_crate
        
        # Otherwise, determine price based on sale type
        sale = self.sale
        if sale.sale_type == 'retail':
            tier = 'retail'
        else:  # wholesale
            tier = 'wholesale_base'
        
        # Fall back to base tier price
        base_price = PriceTier.objects.filter(
            tier=tier,
            egg_type=self.egg_type,
            effective_date__lte=sale.sale_datetime.date(),
            is_active=True
        ).order_by('-effective_date').first()
        
        if base_price:
            return self.quantity * base_price.price_per_crate
        
        return Decimal('0.00')
    
    def save(self, *args, **kwargs):
        # Calculate line total before saving
        self.line_total = self.calculate_line_total()
        super().save(*args, **kwargs)