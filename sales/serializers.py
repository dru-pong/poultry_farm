from rest_framework import serializers
from .models import Sale, SaleItem, CreditPayment
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
        if data.get('quantity', 0) < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
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

    # Credit fields (read-only computed)
    outstanding_balance = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total_credit_payments = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Sale
        fields = [
            'id', 'sale_type', 'customer', 'customer_id', 'customer_name',
            'sale_datetime', 'total_amount', 'amount_paid', 'payment_status',
            'outstanding_balance', 'total_credit_payments',
            'notes', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'items'
        ]
        read_only_fields = [
            'id', 'total_amount', 'payment_status',
            'outstanding_balance', 'total_credit_payments',
            'created_at', 'updated_at'
        ]

    def validate(self, data):
        sale_type = data.get('sale_type')
        customer = data.get('customer')

        if sale_type == 'wholesale' and not customer:
            raise serializers.ValidationError("Wholesale sales require a customer")
        if sale_type == 'retail' and customer:
            raise serializers.ValidationError("Retail sales should not have a customer assigned")

        items = data.get('items', [])
        if not items:
            raise serializers.ValidationError("At least one item is required for a sale")
        if not any(item.get('quantity', 0) > 0 for item in items):
            raise serializers.ValidationError("At least one item must have a positive quantity")

        # Validate amount_paid
        amount_paid = data.get('amount_paid', Decimal('0.00'))
        if amount_paid < 0:
            raise serializers.ValidationError("Amount paid cannot be negative")

        # Retail sales are always fully paid
        if sale_type == 'retail':
            data['amount_paid'] = Decimal('0.00')  # will be set to total after calculation

        return data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        amount_paid_input = validated_data.pop('amount_paid', None)

        # Calculate total amount
        total_amount = Decimal('0.00')
        for item_data in items_data:
            if item_data.get('quantity', 0) <= 0:
                continue
            from inventory.models import PriceTier
            sale_type = validated_data.get('sale_type', 'retail')
            tier = 'retail' if sale_type == 'retail' else 'wholesale_base'
            egg_type = item_data['egg_type']

            base_price = PriceTier.objects.filter(
                tier=tier, egg_type=egg_type,
                effective_date__lte=validated_data['sale_datetime'].date(),
                is_active=True
            ).order_by('-effective_date').first()

            price = item_data.get('price_per_crate')
            if price is None and base_price:
                price = base_price.price_per_crate
            elif price is None:
                price = Decimal('0.00')

            line_total = item_data['quantity'] * price
            total_amount += line_total
            item_data['line_total'] = line_total

        validated_data['total_amount'] = total_amount

        # Determine amount_paid and payment_status
        if validated_data.get('sale_type') == 'retail':
            validated_data['amount_paid'] = total_amount
            validated_data['payment_status'] = 'paid'
        else:
            ap = amount_paid_input if amount_paid_input is not None else Decimal('0.00')
            validated_data['amount_paid'] = ap
            if ap >= total_amount:
                validated_data['payment_status'] = 'paid'
            elif ap > 0:
                validated_data['payment_status'] = 'partial'
            else:
                validated_data['payment_status'] = 'unpaid'

        sale = Sale.objects.create(**validated_data)

        for item_data in items_data:
            if item_data.get('quantity', 0) <= 0:
                continue
            SaleItem.objects.create(sale=sale, **item_data)

        return sale

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        amount_paid_input = validated_data.pop('amount_paid', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if items_data is not None:
            total_amount = Decimal('0.00')
            for item_data in items_data:
                if item_data.get('quantity', 0) <= 0:
                    continue
                from inventory.models import PriceTier
                sale_type = validated_data.get('sale_type', instance.sale_type)
                tier = 'retail' if sale_type == 'retail' else 'wholesale_base'
                egg_type = item_data['egg_type']

                base_price = PriceTier.objects.filter(
                    tier=tier, egg_type=egg_type,
                    effective_date__lte=validated_data.get(
                        'sale_datetime', instance.sale_datetime
                    ).date(),
                    is_active=True
                ).order_by('-effective_date').first()

                price = item_data.get('price_per_crate')
                if price is None and base_price:
                    price = base_price.price_per_crate
                elif price is None:
                    price = Decimal('0.00')

                line_total = item_data['quantity'] * price
                total_amount += line_total
                item_data['line_total'] = line_total

            instance.total_amount = total_amount

        # Update amount_paid if provided
        if amount_paid_input is not None:
            instance.amount_paid = amount_paid_input

        # Recalculate payment status
        instance.recalculate_payment_status()
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                if item_data.get('quantity', 0) <= 0:
                    continue
                SaleItem.objects.create(sale=instance, **item_data)

        return instance


class CreditPaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.username', read_only=True)

    class Meta:
        model = CreditPayment
        fields = [
            'id', 'customer', 'customer_name', 'sale',
            'amount_paid', 'payment_date', 'notes',
            'recorded_by', 'recorded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'recorded_by', 'recorded_by_name', 'created_at']

    def validate(self, data):
        if data.get('amount_paid', 0) <= 0:
            raise serializers.ValidationError("Payment amount must be positive")

        # If a sale is specified, it must belong to the customer
        sale = data.get('sale')
        customer = data.get('customer')
        if sale and customer and sale.customer_id != customer.id:
            raise serializers.ValidationError("Sale does not belong to this customer")

        return data