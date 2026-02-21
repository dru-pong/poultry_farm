from rest_framework import serializers
from .models import WholesaleCustomer, CustomerPriceOverride


class WholesaleCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WholesaleCustomer
        fields = ['id', 'name', 'contact_person', 'phone', 'email', 'address', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerPriceOverrideSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    egg_type_name = serializers.CharField(source='egg_type.name', read_only=True)
    
    class Meta:
        model = CustomerPriceOverride
        fields = ['id', 'customer', 'customer_name', 'egg_type', 'egg_type_name', 'price_per_crate', 'effective_date', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_price_per_crate(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value