from django.contrib import admin
from .models import Flock, FlockEvent, EggProductionLog


class FlockEventInline(admin.TabularInline):
    model = FlockEvent
    extra = 0
    readonly_fields = ['created_at']
    fields = ['event_type', 'quantity', 'event_date', 'notes', 'created_at']


class EggProductionLogInline(admin.TabularInline):
    model = EggProductionLog
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['recorded_date', 'broken_crates', 'small_crates', 'medium_crates', 'big_crates', 'notes']


@admin.register(Flock)
class FlockAdmin(admin.ModelAdmin):
    list_display = ['name', 'breed', 'date_acquired', 'initial_count', 'current_count', 'status']
    list_filter = ['status', 'breed']
    search_fields = ['name', 'breed', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date_acquired'
    inlines = [FlockEventInline, EggProductionLogInline]


@admin.register(FlockEvent)
class FlockEventAdmin(admin.ModelAdmin):
    list_display = ['flock', 'event_type', 'quantity', 'event_date', 'created_at']
    list_filter = ['event_type', 'event_date']
    search_fields = ['flock__name', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'event_date'


@admin.register(EggProductionLog)
class EggProductionLogAdmin(admin.ModelAdmin):
    list_display = ['flock', 'recorded_date', 'broken_crates', 'small_crates', 'medium_crates', 'big_crates']
    list_filter = ['recorded_date', 'flock']
    search_fields = ['flock__name', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'recorded_date'