from rest_framework import serializers
from .models import WholesaleCustomer


class WholesaleCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WholesaleCustomer
        fields = ['id', 'name', 'contact_person', 'phone', 'email', 'address', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']