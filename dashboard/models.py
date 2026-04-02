from django.db import models
from django.db.models import Sum, Q
from users.models import User
from records.models import FinancialRecord


class DashboardCache(models.Model):
    """
    Cache for dashboard summaries to improve query performance.
    Stores aggregated financial data by user.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='dashboard_cache')
    total_income = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)
    total_expense = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)
    net_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)
    record_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dashboard Cache"
        verbose_name_plural = "Dashboard Caches"

    def __str__(self):
        return f"Dashboard Cache: {self.user.username}"

    @staticmethod
    def refresh_cache(user):
        """Recalculate and update cache for a specific user."""
        income = FinancialRecord.objects.filter(
            user=user,
            transaction_type='income',
            is_deleted=False
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        expense = FinancialRecord.objects.filter(
            user=user,
            transaction_type='expense',
            is_deleted=False
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        net_balance = income - expense
        record_count = FinancialRecord.objects.filter(
            user=user,
            is_deleted=False
        ).count()

        cache, created = DashboardCache.objects.update_or_create(
            user=user,
            defaults={
                'total_income': income,
                'total_expense': expense,
                'net_balance': net_balance,
                'record_count': record_count,
            }
        )
        return cache
