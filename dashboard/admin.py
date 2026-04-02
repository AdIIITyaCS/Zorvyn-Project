from django.contrib import admin
from .models import DashboardCache


@admin.register(DashboardCache)
class DashboardCacheAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_income', 'total_expense',
                    'net_balance', 'record_count', 'last_updated')
    readonly_fields = ('last_updated', 'total_income',
                       'total_expense', 'net_balance', 'record_count')
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Summary Data', {
            'fields': ('total_income', 'total_expense', 'net_balance')
        }),
        ('Statistics', {
            'fields': ('record_count',)
        }),
        ('Update Info', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )
