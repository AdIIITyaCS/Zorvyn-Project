"""
Access control decorators for role-based authorization.
These decorators enforce that only users with appropriate roles can access certain views.
"""

from functools import wraps
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


def get_user_from_request(request):
    """
    Extract user from request context.
    In a real application, this would validate JWT tokens or session data.
    For this demo, we assume user_id is passed via query or header.
    """
    # Try to get from query parameter or header
    user_id = request.GET.get('user_id') or request.headers.get('X-User-ID')

    if not user_id:
        return None

    from .models import User
    try:
        return User.objects.get(id=user_id, status='active')
    except User.DoesNotExist:
        return None


def require_role(*allowed_roles):
    """
    Decorator to require specific roles to access a view.

    Usage:
        @require_role('admin')
        def admin_view(request):
            ...

        @require_role('admin', 'analyst')
        def analyst_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = get_user_from_request(request)

            if not user:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }, status=401)

            if not user.is_active():
                return JsonResponse({
                    'status': 'error',
                    'message': 'User account is inactive',
                    'code': 'USER_INACTIVE'
                }, status=403)

            if user.role.name not in allowed_roles:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Access denied. Required role(s): {", ".join(allowed_roles)}',
                    'code': 'INSUFFICIENT_PERMISSIONS'
                }, status=403)

            # Attach user to request for use in the view
            request.current_user = user
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def require_authentication(view_func):
    """
    Decorator to require user authentication.
    Simply checks if a valid user is present.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = get_user_from_request(request)

        if not user:
            return JsonResponse({
                'status': 'error',
                'message': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }, status=401)

        if not user.is_active():
            return JsonResponse({
                'status': 'error',
                'message': 'User account is inactive',
                'code': 'USER_INACTIVE'
            }, status=403)

        request.current_user = user
        return view_func(request, *args, **kwargs)

    return wrapper


class RolePermissionMixin:
    """
    Mixin for class-based views to add role-based permission checking.
    Define required_roles in the view class.
    """
    required_roles = []

    def check_permissions(self, request):
        """Check if the user has required permissions."""
        user = get_user_from_request(request)

        if not user:
            return False, JsonResponse({
                'status': 'error',
                'message': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }, status=401)

        if not user.is_active():
            return False, JsonResponse({
                'status': 'error',
                'message': 'User account is inactive',
                'code': 'USER_INACTIVE'
            }, status=403)

        if self.required_roles and user.role.name not in self.required_roles:
            return False, JsonResponse({
                'status': 'error',
                'message': f'Access denied. Required role(s): {", ".join(self.required_roles)}',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }, status=403)

        request.current_user = user
        return True, None

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to check permissions first."""
        has_permission, error_response = self.check_permissions(request)

        if not has_permission:
            return error_response

        return super().dispatch(request, *args, **kwargs)
