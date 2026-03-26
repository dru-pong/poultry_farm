from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from .models import FlockEvent, EggProductionLog


@receiver(post_save, sender=FlockEvent)
def update_flock_count_on_save(sender, instance, **kwargs):
    """Adjust flock current_count whenever a FlockEvent is saved."""
    flock = instance.flock
    increasing = ('purchase',)
    decreasing = ('death', 'cull', 'transfer', 'sale')

    if instance.event_type in increasing:
        flock.current_count += instance.quantity
    elif instance.event_type in decreasing:
        flock.current_count = max(0, flock.current_count - instance.quantity)

    flock.save(update_fields=['current_count', 'updated_at'])


@receiver(post_delete, sender=FlockEvent)
def update_flock_count_on_delete(sender, instance, **kwargs):
    """Reverse the count adjustment when a FlockEvent is deleted."""
    flock = instance.flock
    increasing = ('purchase',)
    decreasing = ('death', 'cull', 'transfer', 'sale')

    if instance.event_type in increasing:
        flock.current_count = max(0, flock.current_count - instance.quantity)
    elif instance.event_type in decreasing:
        flock.current_count += instance.quantity

    flock.save(update_fields=['current_count', 'updated_at'])


def _sync_intake_log(recorded_date):
    """
    Aggregate all EggProductionLogs for a given date and write
    the totals into IntakeLog. Creates the IntakeLog if it doesn't exist.
    """
    from inventory.models import IntakeLog

    totals = EggProductionLog.objects.filter(recorded_date=recorded_date).aggregate(
        broken=Sum('broken_crates'),
        small=Sum('small_crates'),
        medium=Sum('medium_crates'),
        big=Sum('big_crates'),
    )

    IntakeLog.objects.update_or_create(
        recorded_date=recorded_date,
        defaults={
            'broken_crates': int(totals['broken'] or 0),
            'small_crates': int(totals['small'] or 0),
            'medium_crates': int(totals['medium'] or 0),
            'big_crates': int(totals['big'] or 0),
        }
    )


@receiver(post_save, sender=EggProductionLog)
def sync_intake_on_save(sender, instance, **kwargs):
    _sync_intake_log(instance.recorded_date)


@receiver(post_delete, sender=EggProductionLog)
def sync_intake_on_delete(sender, instance, **kwargs):
    _sync_intake_log(instance.recorded_date)