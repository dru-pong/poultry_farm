from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class EggType(models.Model):
    """
    Predefined egg types with configurable names and active status.
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Egg Type'
        verbose_name_plural = 'Egg Types'
    
    def __str__(self):
        return self.name


class PriceTier(models.Model):
    """
    Pricing tiers for different sales channels.
    """
    TIER_CHOICES = [
        ('retail', 'Retail (Single Sales)'),
        ('wholesale_base', 'Base Wholesale'),
    ]
    
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    egg_type = models.ForeignKey(EggType, on_delete=models.CASCADE, related_name='prices')
    price_per_crate = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-effective_date', 'tier']
        verbose_name = 'Price Tier'
        verbose_name_plural = 'Price Tiers'
        unique_together = ['tier', 'egg_type', 'effective_date']
    
    def __str__(self):
        return f"{self.get_tier_display()} - {self.egg_type.name}: ₵{self.price_per_crate}"
    
    def clean(self):
        if self.price_per_crate < 0:
            raise ValidationError("Price cannot be negative")


class IntakeLog(models.Model):
    """
    Daily record of egg crates brought in.
    Only one intake record allowed per day.
    """
    recorded_date = models.DateField(unique=True, default=timezone.now)
    broken_crates = models.IntegerField(default=0)
    small_crates = models.IntegerField(default=0)
    medium_crates = models.IntegerField(default=0)
    big_crates = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-recorded_date']
        verbose_name = 'Intake Log'
        verbose_name_plural = 'Intake Logs'
        indexes = [
            models.Index(fields=['recorded_date']),
        ]
    
    def __str__(self):
        return f"Intake {self.recorded_date}"
    
    def clean(self):
        if self.broken_crates < 0 or self.small_crates < 0 or self.medium_crates < 0 or self.big_crates < 0:
            raise ValidationError("Crate quantities cannot be negative")
    
    def total_crates(self):
        return self.broken_crates + self.small_crates + self.medium_crates + self.big_crates