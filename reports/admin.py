from django.contrib import admin

# Register your models here.
# reports/admin.py
"""
Django Admin Configuration for Reports App

⚠️ THIS FILE IS INTENTIONALLY EMPTY ⚠️

REASON:
The reports app contains NO database models. All reports are:
- Dynamically generated via API endpoints (ReportViewSet)
- Aggregated from other apps (sales, expenses, inventory)
- Consumed by frontend (Quasar) via REST API

AVAILABLE REPORT ENDPOINTS (use in frontend):
  GET /api/reports/dashboard_summary/?date=YYYY-MM-DD
  GET /api/reports/sales_report/?start_date=...&end_date=...
  GET /api/reports/profit_loss/?start_date=...&end_date=...
  GET /api/reports/inventory_status/

DO NOT:
- Attempt to register non-existent models here
- Create dummy models just for admin visibility
- Duplicate report logic in admin views

IF YOU NEED ADMIN ACCESS TO SOURCE DATA:
  → Manage Sales:     admin.site.register(Sale) in SALES app admin.py
  → Manage Expenses:  admin.site.register(Expense) in EXPENSES app admin.py
  → Manage Inventory: admin.site.register(IntakeLog) in INVENTORY app admin.py
"""