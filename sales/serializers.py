from rest_framework import serializers
from .models import Sale


class SaleSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'sale_type', 'customer', 'customer_name', 'sale_datetime',
            'broken_quantity', 'small_quantity', 'medium_quantity', 'big_quantity',
            'total_amount', 'notes', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_amount', 'created_at', 'updated_at']
    
    def validate(self, data):
        # Validate quantities are not negative
        quantity_fields = ['broken_quantity', 'small_quantity', 'medium_quantity', 'big_quantity']
        for field in quantity_fields:
            if field in data and data[field] < 0:
                raise serializers.ValidationError({field: "Quantity cannot be negative"})
        
        # Validate wholesale sales have a customer
        if data.get('sale_type') == 'wholesale' and not data.get('customer'):
            raise serializers.ValidationError("Wholesale sales require a customer")
        
        # Validate retail sales don't have a customer
        if data.get('sale_type') == 'retail' and data.get('customer'):
            raise serializers.ValidationError("Retail sales should not have a customer assigned")
        
        return data