from rest_framework import serializers
from .models import ExpenseCategory, Expense


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name', 'description', 'is_active', 'order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'date', 'category', 'category_name', 'description', 'amount',
            'payment_method', 'receipt_file', 'is_recurring', 'recurrence_pattern',
            'recurrence_end_date', 'notes', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    
    def validate(self, data):
        # Validate recurring expense requirements
        if data.get('is_recurring') and not data.get('recurrence_pattern'):
            raise serializers.ValidationError("Recurring expenses must have a recurrence pattern")
        
        # Validate recurrence end date
        if data.get('recurrence_end_date') and data.get('date') and data['recurrence_end_date'] < data['date']:
            raise serializers.ValidationError("Recurrence end date cannot be before expense date")
        
        return data