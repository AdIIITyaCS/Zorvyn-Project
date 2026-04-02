from django.contrib import admin
from .models import FinancialRecord


@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'transaction_type',
                    'category', 'date', 'created_at')
    list_filter = ('transaction_type', 'category', 'date', 'is_deleted')
    search_fields = ('user__username', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User & Amount', {
            'fields': ('user', 'amount')
        }),
        ('Transaction Details', {
            'fields': ('transaction_type', 'category', 'date', 'description')
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
