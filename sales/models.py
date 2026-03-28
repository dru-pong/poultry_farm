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

    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('unpaid', 'Unpaid'),
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
    amount_paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        help_text="Amount paid upfront at time of sale. 0 = full credit."
    )
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default='paid',
        help_text="Auto-calculated: paid / partial / unpaid"
    )
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
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        customer_str = f" to {self.customer.name}" if self.customer else ""
        return f"{self.get_sale_type_display()} on {self.sale_datetime.date()}{customer_str} - ₵{self.total_amount}"

    def clean(self):
        if self.sale_type == 'wholesale' and not self.customer:
            raise ValidationError("Wholesale sales require a customer")
        if self.sale_type == 'retail' and self.customer:
            raise ValidationError("Retail sales should not have a customer assigned")
        if self.amount_paid < 0:
            raise ValidationError("Amount paid cannot be negative")

    @property
    def total_credit_payments(self):
        """Sum of all CreditPayment records against this sale."""
        return self.credit_payments.aggregate(
            total=models.Sum('amount_paid')
        )['total'] or Decimal('0.00')

    @property
    def outstanding_balance(self):
        """What's still owed: total - upfront - credit payments."""
        return self.total_amount - self.amount_paid - self.total_credit_payments

    def recalculate_payment_status(self):
        """Recalculate and persist payment_status based on current balances."""
        balance = self.outstanding_balance
        if balance <= 0:
            self.payment_status = 'paid'
        elif self.amount_paid + self.total_credit_payments > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'unpaid'

    def calculate_total_from_items(self, items_data):
        from inventory.models import PriceTier

        total = Decimal('0.00')
        tier = 'retail' if self.sale_type == 'retail' else 'wholesale_base'

        for item_data in items_data:
            if item_data.get('price_per_crate') is not None:
                price = item_data['price_per_crate']
            else:
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
        total = Decimal('0.00')
        if self.pk:
            for item in self.items.all():
                total += item.line_total
        return total

    def save(self, *args, **kwargs):
        if self.pk:
            self.total_amount = self.calculate_total()
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
        from inventory.models import PriceTier

        if self.price_per_crate is not None:
            return self.quantity * self.price_per_crate

        sale = self.sale
        tier = 'retail' if sale.sale_type == 'retail' else 'wholesale_base'

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
        self.line_total = self.calculate_line_total()
        super().save(*args, **kwargs)


class CreditPayment(models.Model):
    """
    Records a payment against a customer's outstanding credit balance.
    Can optionally target a specific sale, or apply to the customer's oldest debts.
    """
    customer = models.ForeignKey(
        'customers.WholesaleCustomer',
        on_delete=models.CASCADE,
        related_name='credit_payments'
    )
    sale = models.ForeignKey(
        Sale,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_payments',
        help_text="Optional: tie this payment to a specific sale."
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Credit Payment'
        verbose_name_plural = 'Credit Payments'
        indexes = [
            models.Index(fields=['customer', '-payment_date']),
        ]

    def __str__(self):
        return f"₵{self.amount_paid} from {self.customer.name} on {self.payment_date.date()}"

    def clean(self):
        if self.amount_paid <= 0:
            raise ValidationError("Payment amount must be positive")