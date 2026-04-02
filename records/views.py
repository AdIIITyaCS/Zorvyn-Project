from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum
from datetime import datetime
from decimal import Decimal
import json

from .models import FinancialRecord
from users.decorators import require_authentication, require_role
from users.utils import (
    success_response, error_response, validate_required_fields,
    validate_decimal_field, validate_date_field, validate_choice_field,
    paginate_queryset, serialize_financial_record
)
from dashboard.models import DashboardCache


def get_request_data(request):
    """Return request data from JSON body or form-data."""
    content_type = request.content_type or ''
    raw_body = request.body.decode('utf-8') if request.body else ''

    if 'application/json' in content_type:
        try:
            raw_body = raw_body or '{}'
            data = json.loads(raw_body)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    # If body looks like JSON, parse it even if header is missing.
    if raw_body.strip().startswith('{'):
        try:
            data = json.loads(raw_body)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    # Fallback for form-data or x-www-form-urlencoded
    return request.POST.dict()


def get_user_records_queryset(user):
    """Get financial records for a specific user, excluding soft-deleted."""
    return FinancialRecord.objects.filter(user=user, is_deleted=False)


@require_http_methods(["GET"])
@require_authentication
def list_records(request):
    """List financial records for the current user or all users (if admin)."""
    user = request.current_user
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)

    # Admins can view all records, others can only view their own
    if user.role.name == 'admin':
        queryset = FinancialRecord.objects.filter(is_deleted=False)
        if 'user_id' in request.GET:
            queryset = queryset.filter(user_id=request.GET['user_id'])
    else:
        queryset = get_user_records_queryset(user)

    # Apply filters
    if 'transaction_type' in request.GET:
        valid, error = validate_choice_field(
            request.GET['transaction_type'],
            ['income', 'expense'],
            'transaction_type'
        )
        if not valid:
            return error_response(error, 'INVALID_TYPE', status_code=400)
        queryset = queryset.filter(
            transaction_type=request.GET['transaction_type'])

    if 'category' in request.GET:
        queryset = queryset.filter(category=request.GET['category'])

    if 'start_date' in request.GET:
        valid, error, parsed_date = validate_date_field(
            request.GET['start_date'],
            'start_date'
        )
        if not valid:
            return error_response(error, 'INVALID_DATE', status_code=400)
        queryset = queryset.filter(date__gte=parsed_date)

    if 'end_date' in request.GET:
        valid, error, parsed_date = validate_date_field(
            request.GET['end_date'],
            'end_date'
        )
        if not valid:
            return error_response(error, 'INVALID_DATE', status_code=400)
        queryset = queryset.filter(date__lte=parsed_date)

    # Order by date (newest first)
    queryset = queryset.order_by('-date', '-created_at')

    paginated = paginate_queryset(queryset, page, page_size)
    serialized = [serialize_financial_record(r) for r in paginated['items']]

    return success_response({
        'records': serialized,
        'pagination': paginated['pagination']
    })


@require_http_methods(["GET"])
@require_authentication
def get_record_detail(request, record_id):
    """Get details of a specific record."""
    user = request.current_user

    try:
        record = FinancialRecord.objects.get(id=record_id, is_deleted=False)

        # Check permissions: only admin or record owner can view
        if user.role.name != 'admin' and record.user_id != user.id:
            return error_response(
                'You do not have permission to view this record',
                'PERMISSION_DENIED',
                status_code=403
            )

        return success_response(serialize_financial_record(record))
    except FinancialRecord.DoesNotExist:
        return error_response('Record not found', 'RECORD_NOT_FOUND', status_code=404)


@require_http_methods(["POST"])
@csrf_exempt
@require_authentication
def create_record(request):
    """Create a new financial record."""
    user = request.current_user

    # Only admin and analyst can create records
    if user.role.name == 'viewer':
        return error_response(
            'Viewers cannot create financial records',
            'PERMISSION_DENIED',
            status_code=403
        )

    try:
        data = get_request_data(request)
        if data is None:
            return error_response(
                'Invalid JSON body',
                'INVALID_JSON',
                status_code=400
            )

        # Validate required fields
        required = ['amount', 'transaction_type', 'category', 'date']
        is_valid, errors = validate_required_fields(data, required)
        if not is_valid:
            return error_response(
                'Missing required fields',
                'VALIDATION_ERROR',
                errors=errors,
                status_code=400
            )

        # Validate amount
        valid, error = validate_decimal_field(
            data['amount'], 'amount', min_value=0.01)
        if not valid:
            return error_response(error, 'INVALID_AMOUNT', status_code=400)

        # Validate transaction type
        valid, error = validate_choice_field(
            data['transaction_type'],
            ['income', 'expense'],
            'transaction_type'
        )
        if not valid:
            return error_response(error, 'INVALID_TYPE', status_code=400)

        # Validate category
        category_choices = [choice[0]
                            for choice in FinancialRecord.CATEGORY_CHOICES]
        valid, error = validate_choice_field(
            data['category'],
            category_choices,
            'category'
        )
        if not valid:
            return error_response(error, 'INVALID_CATEGORY', status_code=400)

        # Validate date
        valid, error, parsed_date = validate_date_field(data['date'], 'date')
        if not valid:
            return error_response(error, 'INVALID_DATE', status_code=400)

        # Create record
        record = FinancialRecord.objects.create(
            user=user,
            amount=Decimal(str(data['amount'])),
            transaction_type=data['transaction_type'],
            category=data['category'],
            date=parsed_date,
            description=data.get('description', '')
        )

        # Refresh dashboard cache
        DashboardCache.refresh_cache(user)

        return success_response(serialize_financial_record(record), 'Record created successfully', 201)

    except Exception as e:
        return error_response(str(e), 'SERVER_ERROR', status_code=500)


@require_http_methods(["PUT", "PATCH"])
@csrf_exempt
@require_authentication
def update_record(request, record_id):
    """Update a financial record."""
    user = request.current_user

    try:
        record = FinancialRecord.objects.get(id=record_id, is_deleted=False)

        # Check permissions: only admin or record owner can update
        if user.role.name == 'viewer':
            return error_response(
                'Viewers cannot update records',
                'PERMISSION_DENIED',
                status_code=403
            )

        if user.role.name != 'admin' and record.user_id != user.id:
            return error_response(
                'You do not have permission to update this record',
                'PERMISSION_DENIED',
                status_code=403
            )

        data = get_request_data(request)
        if data is None:
            return error_response(
                'Invalid JSON body',
                'INVALID_JSON',
                status_code=400
            )

        # Update fields if provided
        if 'amount' in data:
            valid, error = validate_decimal_field(
                data['amount'], 'amount', min_value=0.01)
            if not valid:
                return error_response(error, 'INVALID_AMOUNT', status_code=400)
            record.amount = Decimal(str(data['amount']))

        if 'transaction_type' in data:
            valid, error = validate_choice_field(
                data['transaction_type'],
                ['income', 'expense'],
                'transaction_type'
            )
            if not valid:
                return error_response(error, 'INVALID_TYPE', status_code=400)
            record.transaction_type = data['transaction_type']

        if 'category' in data:
            category_choices = [choice[0]
                                for choice in FinancialRecord.CATEGORY_CHOICES]
            valid, error = validate_choice_field(
                data['category'],
                category_choices,
                'category'
            )
            if not valid:
                return error_response(error, 'INVALID_CATEGORY', status_code=400)
            record.category = data['category']

        if 'date' in data:
            valid, error, parsed_date = validate_date_field(
                data['date'], 'date')
            if not valid:
                return error_response(error, 'INVALID_DATE', status_code=400)
            record.date = parsed_date

        if 'description' in data:
            record.description = data['description']

        record.save()

        # Refresh dashboard cache
        DashboardCache.refresh_cache(user)

        return success_response(serialize_financial_record(record), 'Record updated successfully')

    except FinancialRecord.DoesNotExist:
        return error_response('Record not found', 'RECORD_NOT_FOUND', status_code=404)
    except Exception as e:
        return error_response(str(e), 'SERVER_ERROR', status_code=500)


@require_http_methods(["DELETE"])
@csrf_exempt
@require_authentication
def delete_record(request, record_id):
    """Soft delete a financial record."""
    user = request.current_user

    try:
        record = FinancialRecord.objects.get(id=record_id, is_deleted=False)

        # Check permissions
        if user.role.name == 'viewer':
            return error_response(
                'Viewers cannot delete records',
                'PERMISSION_DENIED',
                status_code=403
            )

        if user.role.name != 'admin' and record.user_id != user.id:
            return error_response(
                'You do not have permission to delete this record',
                'PERMISSION_DENIED',
                status_code=403
            )

        # Soft delete
        record.is_deleted = True
        record.save()

        # Refresh dashboard cache
        DashboardCache.refresh_cache(user)

        return success_response({'deleted_record_id': record_id}, 'Record deleted successfully')

    except FinancialRecord.DoesNotExist:
        return error_response('Record not found', 'RECORD_NOT_FOUND', status_code=404)
    except Exception as e:
        return error_response(str(e), 'SERVER_ERROR', status_code=500)


@require_http_methods(["GET"])
@require_authentication
def get_categories(request):
    """Get available transaction categories."""
    categories = [
        {
            'value': choice[0],
            'label': choice[1]
        }
        for choice in FinancialRecord.CATEGORY_CHOICES
    ]
    return success_response({'categories': categories})


@require_http_methods(["GET"])
@require_authentication
def get_transaction_types(request):
    """Get available transaction types."""
    types = [
        {
            'value': choice[0],
            'label': choice[1]
        }
        for choice in FinancialRecord.TRANSACTION_TYPE_CHOICES
    ]
    return success_response({'transaction_types': types})
