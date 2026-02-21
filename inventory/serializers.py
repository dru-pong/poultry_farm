from rest_framework import serializers
from .models import EggType, PriceTier, IntakeLog


class EggTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EggType
        fields = ['id', 'name', 'description', 'is_active', 'order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PriceTierSerializer(serializers.ModelSerializer):
    egg_type_name = serializers.CharField(source='egg_type.name', read_only=True)
    
    class Meta:
        model = PriceTier
        fields = ['id', 'tier', 'egg_type', 'egg_type_name', 'price_per_crate', 'effective_date', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class IntakeLogSerializer(serializers.ModelSerializer):
    total_crates = serializers.SerializerMethodField()
    
    class Meta:
        model = IntakeLog
        fields = ['id', 'recorded_date', 'broken_crates', 'small_crates', 'medium_crates', 'big_crates', 'total_crates', 'notes', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_crates(self, obj):
        return obj.total_crates()
    
    def validate(self, data):
        # Custom validation for crate quantities
        fields_to_check = ['broken_crates', 'small_crates', 'medium_crates', 'big_crates']
        for field in fields_to_check:
            if field in data and data[field] < 0:
                raise serializers.ValidationError({field: "Quantity cannot be negative"})
        return data