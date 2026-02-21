from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import AuditLog
from .serializers import AuditLogSerializer

from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok", "message": "Backend is running!"})
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for audit logs.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['user', 'action', 'model']
    search_fields = ['details']
    ordering_fields = ['timestamp', 'id']
    ordering = ['-timestamp']
