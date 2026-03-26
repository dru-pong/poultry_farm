from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Flock, FlockEvent, EggProductionLog
from .serializers import FlockSerializer, FlockEventSerializer, EggProductionLogSerializer


class FlockViewSet(viewsets.ModelViewSet):
    queryset = Flock.objects.prefetch_related('events', 'egg_logs').all()
    serializer_class = FlockSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'breed']
    search_fields = ['name', 'breed', 'notes']
    ordering_fields = ['date_acquired', 'current_count', 'name']
    ordering = ['-date_acquired']

    @action(detail=True, methods=['get'], url_path='summary')
    def summary(self, request, pk=None):
        """Quick stats for a single flock."""
        flock = self.get_object()
        events = flock.events.all()
        total_deaths = sum(e.quantity for e in events if e.event_type in ('death', 'cull'))
        total_eggs = sum(log.total_crates() for log in flock.egg_logs.all())

        return Response({
            'flock_id': flock.id,
            'name': flock.name,
            'initial_count': flock.initial_count,
            'current_count': flock.current_count,
            'total_deaths': total_deaths,
            'mortality_rate': round((total_deaths / flock.initial_count) * 100, 2) if flock.initial_count else 0,
            'total_egg_crates': float(total_eggs),
        })


class FlockEventViewSet(viewsets.ModelViewSet):
    queryset = FlockEvent.objects.select_related('flock').all()
    serializer_class = FlockEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['flock', 'event_type', 'event_date']
    ordering_fields = ['event_date', 'created_at']
    ordering = ['-event_date']


class EggProductionLogViewSet(viewsets.ModelViewSet):
    queryset = EggProductionLog.objects.select_related('flock').all()
    serializer_class = EggProductionLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['flock', 'recorded_date']
    ordering_fields = ['recorded_date', 'created_at']
    ordering = ['-recorded_date']