from django.urls import path
from . import views

urlpatterns = [
    # Current user info
    path('current/', views.get_current_user, name='current-user'),

    # User management (admin only)
    path('list/', views.list_users, name='list-users'),
    path('<int:user_id>/', views.get_user_detail, name='user-detail'),
    path('create/', views.create_user, name='create-user'),
    path('<int:user_id>/update/', views.update_user, name='update-user'),
    path('<int:user_id>/delete/', views.delete_user, name='delete-user'),

    # Roles
    path('roles/', views.list_roles, name='list-roles'),
]
