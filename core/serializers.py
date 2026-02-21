from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'model', 'record_id', 'timestamp', 'details', 'ip_address']
        read_only_fields = ['id', 'timestamp']