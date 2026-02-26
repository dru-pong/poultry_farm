from rest_framework import serializers
from .models import Sale, SaleItem
from inventory.serializers import EggTypeSerializer
from customers.serializers import WholesaleCustomerSerializer
from django.db import transaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class SaleItemSerializer(serializers.ModelSerializer):
    egg_type = EggTypeSerializer(read_only=True)
    egg_type_id = serializers.PrimaryKeyRelatedField(
        queryset=EggTypeSerializer.Meta.model.objects.all(),
        source='egg_type',
        write_only=True
    )
    
    class Meta:
        model = SaleItem
        fields = [
            'id', 'egg_type', 'egg_type_id', 
            'quantity', 'price_per_crate', 'line_total'
        ]
        read_only_fields = ['line_total']
    
    def validate(self, data):
        # Ensure quantity is not negative
        if data.get('quantity', 0) < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        
        # Ensure price_per_crate is not negative if provided
        if data.get('price_per_crate') is not None and data['price_per_crate'] < 0:
            raise serializers.ValidationError("Price per crate cannot be negative")
        
        return data


class SaleSerializer(serializers.ModelSerializer):
    customer = WholesaleCustomerSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=WholesaleCustomerSerializer.Meta.model.objects.filter(is_active=True),
        source='customer',
        write_only=True,
        required=False,
        allow_null=True
    )
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    items = SaleItemSerializer(many=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'sale_type', 'customer', 'customer_id', 'customer_name', 
            'sale_datetime', 'total_amount', 'notes', 'created_by', 
            'created_by_name', 'created_at', 'updated_at', 'items'
        ]
        read_only_fields = ['id', 'total_amount', 'created_at', 'updated_at']
    
    def validate(self, data):
        # Validate wholesale sales have a customer
        if data.get('sale_type') == 'wholesale' and not data.get('customer'):
            raise serializers.ValidationError("Wholesale sales require a customer")
        
        # Validate retail sales don't have a customer
        if data.get('sale_type') == 'retail' and data.get('customer'):
            raise serializers.ValidationError("Retail sales should not have a customer assigned")
        
        # Validate items exist
        items = data.get('items', [])
        if not items:
            raise serializers.ValidationError("At least one item is required for a sale")
        
        # Validate at least one item has a positive quantity
        if not any(item.get('quantity', 0) > 0 for item in items):
            raise serializers.ValidationError("At least one item must have a positive quantity")
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Calculate total amount BEFORE creating the Sale
        total_amount = Decimal('0.00')
        for item_data in items_data:
            # Skip items with zero quantity
            if item_data.get('quantity', 0) <= 0:
                continue
                
            # Get price tier
            from inventory.models import PriceTier
            sale_type = validated_data.get('sale_type', 'retail')
            tier = 'retail' if sale_type == 'retail' else 'wholesale_base'
            
            # Get egg type from item_data
            egg_type = item_data['egg_type']
            
            # Get current price tier
            base_price = PriceTier.objects.filter(
                tier=tier,
                egg_type=egg_type,
                effective_date__lte=validated_data['sale_datetime'].date(),
                is_active=True
            ).order_by('-effective_date').first()
            
            # Calculate price
            price = item_data.get('price_per_crate')
            if price is None and base_price:
                price = base_price.price_per_crate
            elif price is None:
                price = Decimal('0.00')
            
            # Calculate line total
            line_total = item_data['quantity'] * price
            
            # Add to total amount
            total_amount += line_total
            
            # Add to item data for later creation
            item_data['line_total'] = line_total
        
        # Set the total_amount in validated_data
        validated_data['total_amount'] = total_amount
        
        # Now create the Sale with the pre-calculated total
        sale = Sale.objects.create(**validated_data)
        
        # Create sale items
        for item_data in items_data:
            # Skip items with zero quantity
            if item_data.get('quantity', 0) <= 0:
                continue
                
            SaleItem.objects.create(sale=sale, **item_data)
        
        return sale
    
    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # Update sale fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # If items are provided, recalculate total
        if items_data is not None:
            total_amount = Decimal('0.00')
            for item_data in items_data:
                # Skip items with zero quantity
                if item_data.get('quantity', 0) <= 0:
                    continue
                    
                # Get price tier
                from inventory.models import PriceTier
                sale_type = validated_data.get('sale_type', instance.sale_type)
                tier = 'retail' if sale_type == 'retail' else 'wholesale_base'
                
                # Get egg type from item_data
                egg_type = item_data['egg_type']
                
                # Get current price tier
                base_price = PriceTier.objects.filter(
                    tier=tier,
                    egg_type=egg_type,
                    effective_date__lte=validated_data.get('sale_datetime', instance.sale_datetime).date(),
                    is_active=True
                ).order_by('-effective_date').first()
                
                # Calculate price
                price = item_data.get('price_per_crate')
                if price is None and base_price:
                    price = base_price.price_per_crate
                elif price is None:
                    price = Decimal('0.00')
                
                # Calculate line total
                line_total = item_data['quantity'] * price
                
                # Add to total amount
                total_amount += line_total
                
                # Add to item data
                item_data['line_total'] = line_total
            
            # Set the total_amount
            instance.total_amount = total_amount
        
        instance.save()
        
        # Update sale items if provided
        if items_data is not None:
            # Delete existing items
            instance.items.all().delete()
            
            # Create new items
            for item_data in items_data:
                # Skip items with zero quantity
                if item_data.get('quantity', 0) <= 0:
                    continue
                    
                SaleItem.objects.create(sale=instance, **item_data)
        
        return instance