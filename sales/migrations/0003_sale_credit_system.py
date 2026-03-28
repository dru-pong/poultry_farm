from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('customers', '0002_delete_customerpriceoverride'),
        ('sales', '0002_remove_sale_big_quantity_remove_sale_broken_quantity_and_more'),
    ]

    operations = [
        # --- Sale: add amount_paid ---
        migrations.AddField(
            model_name='sale',
            name='amount_paid',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='Amount paid upfront at time of sale. 0 = full credit.',
                max_digits=12,
            ),
        ),
        # --- Sale: add payment_status ---
        migrations.AddField(
            model_name='sale',
            name='payment_status',
            field=models.CharField(
                choices=[('paid', 'Paid'), ('partial', 'Partial'), ('unpaid', 'Unpaid')],
                default='paid',
                help_text='Auto-calculated: paid / partial / unpaid',
                max_length=10,
            ),
        ),
        # --- Sale: add index on payment_status ---
        migrations.AddIndex(
            model_name='sale',
            index=models.Index(fields=['payment_status'], name='sales_sale_payment_8e3f4a_idx'),
        ),
        # --- CreditPayment model ---
        migrations.CreateModel(
            name='CreditPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=12)),
                ('payment_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='credit_payments',
                    to='customers.wholesalecustomer',
                )),
                ('sale', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='credit_payments',
                    to='sales.sale',
                    help_text='Optional: tie this payment to a specific sale.',
                )),
                ('recorded_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Credit Payment',
                'verbose_name_plural': 'Credit Payments',
                'ordering': ['-payment_date'],
                'indexes': [
                    models.Index(fields=['customer', '-payment_date'], name='sales_credi_custome_a1b2c3_idx'),
                ],
            },
        ),
        # --- Backfill: mark all existing sales as 'paid' with amount_paid = total_amount ---
        migrations.RunSQL(
            sql="UPDATE sales_sale SET amount_paid = total_amount, payment_status = 'paid';",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
