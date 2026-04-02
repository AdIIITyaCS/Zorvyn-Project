from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from decimal import Decimal

from .models import DashboardCache
from records.models import FinancialRecord
from users.decorators import require_authentication, require_role
from users.utils import success_response, error_response, validate_date_field


@require_http_methods(["GET"])
@require_authentication
def get_summary(request):
    """Get financial summary for the current user."""
    user = request.current_user

    try:
        # Get or refresh cache
        cache, created = DashboardCache.objects.get_or_create(user=user)
        if created:
            DashboardCache.refresh_cache(user)
            cache.refresh_from_db()

        summary = {
            'user_id': user.id,
            'user_name': user.get_full_name(),
            'total_income': float(cache.total_income),
            'total_expense': float(cache.total_expense),
            'net_balance': float(cache.net_balance),
            'record_count': cache.record_count,
            'last_updated': cache.last_updated.isoformat(),
        }

        return success_response(summary)

    except Exception as e:
        return error_response(str(e), 'SERVER_ERROR', status_code=500)


@require_http_methods(["GET"])
@require_authentication
def get_category_breakdown(request):
    """Get income and expense breakdown by category for current user."""
    user = request.current_user

    try:
        records = FinancialRecord.objects.filter(
            user=user,
            is_deleted=False
        )

        # Income breakdown
        income_by_category = records.filter(
            transaction_type='income'
        ).values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        # Expense breakdown
        expense_by_category = records.filter(
            transaction_type='expense'
        ).values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        breakdown = {
            'income_by_category': [
                {
                    'category': item['category'],
                    'total': float(item['total']),
                    'count': item['count']
                }
                for item in income_by_category
            ],
            'expense_by_category': [
                {
                    'category': item['category'],
                    'total': float(item['total']),
                    'count': item['count']
                }
                for item in expense_by_category
            ],
        }

        return success_response(breakdown)

    except Exception as e:
        return error_response(str(e), 'SERVER_ERROR', status_code=500)


@require_http_methods(["GET"])
@require_authentication
def get_monthly_trend(request):
    """Get monthly income and expense trends for current user."""
    user = request.current_user
    start_month = request.GET.get('start_month')  # Format: YYYY-MM
    end_month = request.GET.get('end_month')      # Format: YYYY-MM

    try:
        records = FinancialRecord.objects.filter(
            user=user,
            is_deleted=False
        )

        # Extract year-month and aggregate
        monthly_data = {}
        for record in records:
            month_key = record.date.strftime('%Y-%m')

            if start_month and month_key < start_month:
                continue
            if end_month and month_key > end_month:
                continue

            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'month': month_key,
                    'income': 0,
                    'expense': 0,
                    'net': 0,
                }

            if record.transaction_type == 'income':
                monthly_data[month_key]['income'] += float(record.amount)
            else:
                monthly_data[month_key]['expense'] += float(record.amount)

        # Calculate net balance
        for month_key in monthly_data:
            monthly_data[month_key]['net'] = (
                monthly_data[month_key]['income'] -
                monthly_data[month_key]['expense']
            )

        # Sort by month
        trend = sorted(monthly_data.values(), key=lambda x: x['month'])

        return success_response({'monthly_trend': trend})

    except Exception as e:
        return error_response(str(e), 'SERVER_ERROR', status_code=500)


@require_http_methods(["GET"])
@require_authentication
def get_recent_activity(request):
    """Get recent financial records for current user."""
    user = request.current_user
    limit = min(int(request.GET.get('limit', 10)), 50)

    try:
        records = FinancialRecord.objects.filter(
            user=user,
            is_deleted=False
        ).order_by('-date', '-created_at')[:limit]

        activity = [
            {
                'id': record.id,
                'type': record.transaction_type,
                'amount': float(record.amount),
                'category': record.category,
                'date': record.date.isoformat(),
                'description': record.description,
            }
            for record in records
        ]

        return success_response({'recent_activity': activity})

    except Exception as e:
        return error_response(str(e), 'SERVER_ERROR', status_code=500)


@require_http_methods(["GET"])
@require_authentication
def get_period_summary(request):
    """Get summary for a specific period."""
    user = request.current_user
    # 'day', 'week', 'month', 'year'
    period_type = request.GET.get('period', 'month')

    try:
        today = datetime.now().date()

        # Determine date range
        if period_type == 'day':
            start_date = today
        elif period_type == 'week':
            start_date = today - timedelta(days=7)
        elif period_type == 'month':
            start_date = today - timedelta(days=30)
        elif period_type == 'year':
            start_date = today - timedelta(days=365)
        else:
            return error_response('Invalid period type', 'INVALID_PERIOD', status_code=400)

        records = FinancialRecord.objects.filter(
            user=user,
            is_deleted=False,
            date__gte=start_date
        )

        income = records.filter(transaction_type='income').aggregate(
            Sum('amount'))['amount__sum'] or 0
        expense = records.filter(transaction_type='expense').aggregate(
            Sum('amount'))['amount__sum'] or 0

        summary = {
            'period': period_type,
            'start_date': start_date.isoformat(),
            'end_date': today.isoformat(),
            'total_income': float(income),
            'total_expense': float(expense),
            'net_balance': float(income - expense),
            'record_count': records.count(),
        }

        return success_response(summary)

    except Exception as e:
        return error_response(str(e), 'SERVER_ERROR', status_code=500)


@require_http_methods(["GET"])
@require_role('admin')
def get_all_users_summary(request):
    """Get summary for all users. Admin only."""
    try:
        caches = DashboardCache.objects.select_related('user').all()

        total_income = 0
        total_expense = 0
        total_users = 0
        total_records = 0

        user_summaries = []

        for cache in caches:
            total_income += cache.total_income
            total_expense += cache.total_expense
            total_users += 1
            total_records += cache.record_count

            user_summaries.append({
                'user_id': cache.user.id,
                'username': cache.user.username,
                'role': cache.user.role.name,
                'total_income': float(cache.total_income),
                'total_expense': float(cache.total_expense),
                'net_balance': float(cache.net_balance),
                'record_count': cache.record_count,
            })

        system_summary = {
            'total_users': total_users,
            'total_records': total_records,
            'system_income': float(total_income),
            'system_expense': float(total_expense),
            'system_net': float(total_income - total_expense),
            'user_summaries': user_summaries,
        }

        return success_response(system_summary)

    except Exception as e:
        return error_response(str(e), 'SERVER_ERROR', status_code=500)
