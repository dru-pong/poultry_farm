from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class ExpenseCategory(models.Model):
    """
    Predefined categories for expense tracking.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Expense Category'
        verbose_name_plural = 'Expense Categories'
    
    def __str__(self):
        return self.name


class Expense(models.Model):
    """
    Record of business expenses with optional recurring support.
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('credit', 'Credit'),
        ('other', 'Other'),
    ]
    
    RECURRENCE_CHOICES = [
        (None, 'None'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    date = models.DateField(default=timezone.now)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    receipt_file = models.FileField(upload_to='expense_receipts/', blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, blank=True, null=True)
    recurrence_end_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.category.name} - ₵{self.amount} on {self.date}"
    
    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Amount must be greater than zero")
        
        if self.is_recurring and not self.recurrence_pattern:
            raise ValidationError("Recurring expenses must have a recurrence pattern")
        
        if self.recurrence_end_date and self.recurrence_end_date < self.date:
            raise ValidationError("Recurrence end date cannot be before expense date")
