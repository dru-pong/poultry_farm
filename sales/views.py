from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from datetime import date
from decimal import Decimal

from .models import Sale, CreditPayment
from .serializers import SaleSerializer, CreditPaymentSerializer


class SaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sales (retail and wholesale).
    Total amount is auto-calculated on save.
    """
    queryset = (
        Sale.objects
        .select_related('customer', 'created_by')
        .prefetch_related('items__egg_type', 'credit_payments')
        .all()
    )
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sale_type', 'customer', 'sale_datetime', 'payment_status']
    search_fields = ['notes', 'customer__name']
    ordering_fields = ['sale_datetime', 'total_amount', 'created_at']
    ordering = ['-sale_datetime']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'], url_path='daily-summary')
    def daily_summary(self, request):
        today = date.today()
        sales_today = Sale.objects.filter(sale_datetime__date=today)

        summary_data = sales_today.aggregate(
            total_sales=Count('id'),
            total_revenue=Sum('total_amount'),
            retail_count=Count('id', filter=Q(sale_type='retail')),
            wholesale_count=Count('id', filter=Q(sale_type='wholesale')),
            retail_revenue=Sum('total_amount', filter=Q(sale_type='retail')),
            wholesale_revenue=Sum('total_amount', filter=Q(sale_type='wholesale'))
        )

        summary = {
            'date': today,
            'total_sales': summary_data['total_sales'] or 0,
            'total_revenue': float(summary_data['total_revenue'] or 0),
            'retail_count': summary_data['retail_count'] or 0,
            'wholesale_count': summary_data['wholesale_count'] or 0,
            'retail_revenue': float(summary_data['retail_revenue'] or 0),
            'wholesale_revenue': float(summary_data['wholesale_revenue'] or 0),
        }
        return Response(summary)

    @action(detail=False, methods=['get'], url_path='customer-balance')
    def customer_balance(self, request):
        """
        GET /api/sales/sales/customer-balance/?customer_id=<id>
        Returns total purchased, total paid (upfront + credit), outstanding balance.
        """
        from customers.models import WholesaleCustomer

        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response({'error': 'customer_id is required'}, status=400)

        try:
            customer = WholesaleCustomer.objects.get(pk=customer_id)
        except WholesaleCustomer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=404)

        sales = Sale.objects.filter(customer=customer)
        total_purchased = sales.aggregate(t=Sum('total_amount'))['t'] or Decimal('0.00')
        total_upfront = sales.aggregate(t=Sum('amount_paid'))['t'] or Decimal('0.00')
        total_credit_paid = CreditPayment.objects.filter(
            customer=customer
        ).aggregate(t=Sum('amount_paid'))['t'] or Decimal('0.00')

        total_paid = total_upfront + total_credit_paid
        outstanding = total_purchased - total_paid

        return Response({
            'customer_id': customer.id,
            'customer_name': customer.name,
            'total_purchased': str(total_purchased),
            'total_upfront_paid': str(total_upfront),
            'total_credit_payments': str(total_credit_paid),
            'total_paid': str(total_paid),
            'outstanding_balance': str(outstanding),
        })


class CreditPaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for recording and listing credit payments.
    POST to record a payment, GET to list all / filter by customer.
    """
    queryset = (
        CreditPayment.objects
        .select_related('customer', 'sale', 'recorded_by')
        .all()
    )
    serializer_class = CreditPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['customer']
    ordering_fields = ['payment_date', 'amount_paid']
    ordering = ['-payment_date']

    def perform_create(self, serializer):
        cp = serializer.save(recorded_by=self.request.user)

        # If tied to a specific sale, update that sale's payment status
        if cp.sale:
            cp.sale.recalculate_payment_status()
            cp.sale.save(update_fields=['payment_status'])

        # Also update any unpaid/partial sales for this customer (oldest first)
        unpaid_sales = (
            Sale.objects
            .filter(customer=cp.customer, payment_status__in=['unpaid', 'partial'])
            .order_by('sale_datetime')
        )
        for sale in unpaid_sales:
            sale.recalculate_payment_status()
            sale.save(update_fields=['payment_status'])