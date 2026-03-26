from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Flock(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('retired', 'Retired'),
        ('sold', 'Sold'),
    ]

    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100, blank=True)
    date_acquired = models.DateField(default=timezone.now)
    initial_count = models.PositiveIntegerField()
    current_count = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_acquired']

    def __str__(self):
        return f"{self.name} ({self.current_count} birds)"

    def clean(self):
        if self.current_count > self.initial_count:
            raise ValidationError("Current count cannot exceed initial count.")


class FlockEvent(models.Model):
    EVENT_CHOICES = [
        ('purchase', 'Purchase'),
        ('death', 'Death'),
        ('cull', 'Cull'),
        ('transfer', 'Transfer'),
        ('sale', 'Sale'),
    ]

    flock = models.ForeignKey(Flock, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    quantity = models.PositiveIntegerField()
    event_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-event_date']

    def __str__(self):
        return f"{self.flock.name} — {self.get_event_type_display()} x{self.quantity} on {self.event_date}"

    def clean(self):
        decreasing = ('death', 'cull', 'transfer', 'sale')
        if self.event_type in decreasing and self.quantity > self.flock.current_count:
            raise ValidationError(
                f"Cannot remove {self.quantity} birds — flock only has {self.flock.current_count}."
            )


class EggProductionLog(models.Model):
    flock = models.ForeignKey(Flock, on_delete=models.CASCADE, related_name='egg_logs')
    recorded_date = models.DateField(default=timezone.now)
    broken_crates = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    small_crates = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    medium_crates = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    big_crates = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-recorded_date']
        unique_together = ['flock', 'recorded_date']

    def __str__(self):
        return f"{self.flock.name} eggs — {self.recorded_date}"

    def total_crates(self):
        return self.broken_crates + self.small_crates + self.medium_crates + self.big_crates

    def clean(self):
        for field in ('broken_crates', 'small_crates', 'medium_crates', 'big_crates'):
            if getattr(self, field) < 0:
                raise ValidationError("Crate quantities cannot be negative.")