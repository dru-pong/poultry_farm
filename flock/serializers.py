from rest_framework import serializers
from .models import Flock, FlockEvent, EggProductionLog


class FlockEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = FlockEvent
        fields = ['id', 'flock', 'event_type', 'event_type_display', 'quantity', 'event_date', 'notes', 'created_at']
        read_only_fields = ['created_at']

    def validate(self, data):
        flock = data.get('flock')
        event_type = data.get('event_type')
        quantity = data.get('quantity')
        decreasing = ('death', 'cull', 'transfer', 'sale')

        if event_type in decreasing and flock and quantity > flock.current_count:
            raise serializers.ValidationError(
                f"Cannot remove {quantity} birds — flock only has {flock.current_count}."
            )
        return data


class EggProductionLogSerializer(serializers.ModelSerializer):
    total_crates = serializers.SerializerMethodField()
    flock_name = serializers.CharField(source='flock.name', read_only=True)

    class Meta:
        model = EggProductionLog
        fields = [
            'id', 'flock', 'flock_name', 'recorded_date',
            'broken_crates', 'small_crates', 'medium_crates', 'big_crates',
            'total_crates', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_total_crates(self, obj):
        return obj.total_crates()


class FlockSerializer(serializers.ModelSerializer):
    events = FlockEventSerializer(many=True, read_only=True)
    egg_logs = EggProductionLogSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Flock
        fields = [
            'id', 'name', 'breed', 'date_acquired',
            'initial_count', 'current_count', 'status', 'status_display',
            'notes', 'events', 'egg_logs', 'created_at', 'updated_at',
        ]
        read_only_fields = ['current_count', 'created_at', 'updated_at']