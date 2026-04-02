from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
import json

from .models import User, Role
from .decorators import require_role, require_authentication
from .utils import (
    success_response, error_response, validate_required_fields,
    validate_choice_field, serialize_user, paginate_queryset
)


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

    # If content-type is not set correctly but body looks like JSON, still parse it.
    if raw_body.strip().startswith('{'):
        try:
            data = json.loads(raw_body)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    # Fallback for form-data or x-www-form-urlencoded
    return request.POST.dict()


@require_http_methods(["GET"])
@require_authentication
def get_current_user(request):
    """Get the current authenticated user's information."""
    user = request.current_user
    return success_response(serialize_user(user))


@require_http_methods(["GET"])
@require_role('admin')
def list_users(request):
    """List all users with optional filtering and pagination."""
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)
    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')

    queryset = User.objects.select_related('role')

    if role_filter:
        valid, error = validate_choice_field(
            role_filter,
            ['viewer', 'analyst', 'admin'],
            'role'
        )
        if not valid:
            return error_response(error, 'INVALID_ROLE', status_code=400)
        queryset = queryset.filter(role__name=role_filter)

    if status_filter:
        valid, error = validate_choice_field(
            status_filter,
            ['active', 'inactive'],
            'status'
        )
        if not valid:
            return error_response(error, 'INVALID_STATUS', status_code=400)
        queryset = queryset.filter(status=status_filter)

    paginated = paginate_queryset(queryset, page, page_size)
    serialized = [serialize_user(u) for u in paginated['items']]

    return success_response({
        'users': serialized,
        'pagination': paginated['pagination']
    })


@require_http_methods(["GET"])
@require_role('admin')
def get_user_detail(request, user_id):
    """Get details of a specific user."""
    try:
        user = User.objects.select_related('role').get(id=user_id)
        return success_response(serialize_user(user))
    except User.DoesNotExist:
        return error_response('User not found', 'USER_NOT_FOUND', status_code=404)


@require_http_methods(["POST"])
@csrf_exempt
@require_role('admin')
def create_user(request):
    """Create a new user. Admin only."""
    try:
        data = get_request_data(request)
        if data is None:
            return error_response(
                'Invalid JSON body',
                'INVALID_JSON',
                status_code=400
            )

        # Validate required fields
        required = ['username', 'email', 'role']
        is_valid, errors = validate_required_fields(data, required)
        if not is_valid:
            return error_response(
                'Missing required fields',
                'VALIDATION_ERROR',
                errors=errors,
                status_code=400
            )

        # Validate role
        valid, error = validate_choice_field(
            data['role'],
            ['viewer', 'analyst', 'admin'],
            'role'
        )
        if not valid:
            return error_response(error, 'INVALID_ROLE', status_code=400)

        try:
            role = Role.objects.get(name=data['role'])
        except Role.DoesNotExist:
            return error_response('Role not found', 'ROLE_NOT_FOUND', status_code=400)

        # Create user
        user = User.objects.create(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role=role,
            status=data.get('status', 'active')
        )

        return success_response(serialize_user(user), 'User created successfully', 201)

    except IntegrityError as e:
        if 'username' in str(e):
            return error_response(
                'Username already exists',
                'DUPLICATE_USERNAME',
                status_code=400
            )
        elif 'email' in str(e):
            return error_response(
                'Email already exists',
                'DUPLICATE_EMAIL',
                status_code=400
            )
        return error_response(
            'Database integrity error',
            'INTEGRITY_ERROR',
            status_code=400
        )
    except Exception as e:
        return error_response(str(e), 'SERVER_ERROR', status_code=500)


@require_http_methods(["PUT", "PATCH"])
@csrf_exempt
@require_role('admin')
def update_user(request, user_id):
    """Update a user. Admin only."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return error_response('User not found', 'USER_NOT_FOUND', status_code=404)

    try:
        data = get_request_data(request)
        if data is None:
            return error_response(
                'Invalid JSON body',
                'INVALID_JSON',
                status_code=400
            )

        # Update fields if provided
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            user.email = data['email']

        if 'status' in data:
            valid, error = validate_choice_field(
                data['status'],
                ['active', 'inactive'],
                'status'
            )
            if not valid:
                return error_response(error, 'INVALID_STATUS', status_code=400)
            user.status = data['status']

        if 'role' in data:
            valid, error = validate_choice_field(
                data['role'],
                ['viewer', 'analyst', 'admin'],
                'role'
            )
            if not valid:
                return error_response(error, 'INVALID_ROLE', status_code=400)
            try:
                user.role = Role.objects.get(name=data['role'])
            except Role.DoesNotExist:
                return error_response('Role not found', 'ROLE_NOT_FOUND', status_code=400)

        user.save()
        return success_response(serialize_user(user), 'User updated successfully')

    except IntegrityError as e:
        if 'email' in str(e):
            return error_response(
                'Email already exists',
                'DUPLICATE_EMAIL',
                status_code=400
            )
        return error_response(
            'Database integrity error',
            'INTEGRITY_ERROR',
            status_code=400
        )
    except Exception as e:
        return error_response(str(e), 'SERVER_ERROR', status_code=500)


@require_http_methods(["DELETE"])
@csrf_exempt
@require_role('admin')
def delete_user(request, user_id):
    """Delete a user. Admin only."""
    try:
        user = User.objects.get(id=user_id)
        username = user.username
        user.delete()
        return success_response({'deleted_user_id': user_id}, f'User {username} deleted successfully')
    except User.DoesNotExist:
        return error_response('User not found', 'USER_NOT_FOUND', status_code=404)
    except Exception as e:
        return error_response(str(e), 'SERVER_ERROR', status_code=500)


@require_http_methods(["GET"])
@require_role('admin')
def list_roles(request):
    """List all available roles."""
    roles = Role.objects.all()
    role_data = [
        {
            'name': role.name,
            'display_name': role.get_name_display(),
            'description': role.description,
        }
        for role in roles
    ]
    return success_response({'roles': role_data})
