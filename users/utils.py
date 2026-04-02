"""
Utility functions for the finance backend.
Includes response formatting, validation helpers, and common functions.
"""

from django.http import JsonResponse
from django.core.exceptions import ValidationError
import json
from datetime import datetime


def success_response(data=None, message='Success', status_code=200):
    """
    Standard success response format.
    Returns a JSON response with status 'success'.

    Args:
        data: Response data (dict or list)
        message: Success message
        status_code: HTTP status code
    """
    response = {
        'status': 'success',
        'message': message,
    }
    if data is not None:
        response['data'] = data

    return JsonResponse(response, status=status_code)


def error_response(message, code='ERROR', errors=None, status_code=400):
    """
    Standard error response format.
    Returns a JSON response with status 'error'.

    Args:
        message: Error message
        code: Error code for programmatic identification
        errors: Detailed field errors (dict)
        status_code: HTTP status code
    """
    response = {
        'status': 'error',
        'message': message,
        'code': code,
    }
    if errors:
        response['errors'] = errors

    return JsonResponse(response, status=status_code)


def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present in data.

    Args:
        data: Dictionary to validate
        required_fields: List of field names that are required

    Returns:
        Tuple (is_valid, errors_dict)
    """
    errors = {}

    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            errors[field] = f'{field} is required'

    return len(errors) == 0, errors


def validate_decimal_field(value, field_name='amount', min_value=0, max_value=None):
    """
    Validate a decimal field.

    Args:
        value: Value to validate
        field_name: Name of the field
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Tuple (is_valid, error_message)
    """
    try:
        decimal_value = float(value)

        if decimal_value < min_value:
            return False, f'{field_name} must be at least {min_value}'

        if max_value is not None and decimal_value > max_value:
            return False, f'{field_name} must be at most {max_value}'

        return True, None

    except (ValueError, TypeError):
        return False, f'{field_name} must be a valid number'


def validate_date_field(value, field_name='date'):
    """
    Validate a date field.

    Args:
        value: Value to validate (string or date)
        field_name: Name of the field

    Returns:
        Tuple (is_valid, error_message, parsed_date)
    """
    if hasattr(value, 'date'):  # Already a date object
        return True, None, value.date()

    try:
        parsed_date = datetime.strptime(str(value), '%Y-%m-%d').date()
        return True, None, parsed_date
    except (ValueError, TypeError):
        return False, f'{field_name} must be in YYYY-MM-DD format', None


def validate_choice_field(value, choices, field_name='field'):
    """
    Validate that value is one of the allowed choices.

    Args:
        value: Value to validate
        choices: List of allowed values
        field_name: Name of the field

    Returns:
        Tuple (is_valid, error_message)
    """
    if value not in choices:
        return False, f'{field_name} must be one of: {", ".join(choices)}'

    return True, None


def paginate_queryset(queryset, page=1, page_size=20):
    """
    Paginate a queryset.

    Args:
        queryset: Django QuerySet
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Dict with paginated data and pagination info
    """
    page = max(1, int(page))
    page_size = min(100, max(1, int(page_size)))  # Cap at 100 per page

    total_count = queryset.count()
    total_pages = (total_count + page_size - 1) // page_size

    start = (page - 1) * page_size
    end = start + page_size

    items = list(queryset[start:end])

    return {
        'items': items,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1,
        }
    }


def serialize_financial_record(record):
    """Convert a FinancialRecord instance to a dictionary."""
    return {
        'id': record.id,
        'user_id': record.user.id,
        'user_name': record.user.get_full_name(),
        'amount': float(record.amount),
        'transaction_type': record.transaction_type,
        'category': record.category,
        'date': record.date.isoformat(),
        'description': record.description,
        'created_at': record.created_at.isoformat(),
        'updated_at': record.updated_at.isoformat(),
    }


def serialize_user(user):
    """Convert a User instance to a dictionary."""
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name(),
        'role': user.role.name,
        'status': user.status,
        'created_at': user.created_at.isoformat(),
        'updated_at': user.updated_at.isoformat(),
        'last_login': user.last_login.isoformat() if user.last_login else None,
    }
