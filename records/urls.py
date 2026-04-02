from django.urls import path
from . import views

urlpatterns = [
    # Record management
    path('list/', views.list_records, name='list-records'),
    path('<int:record_id>/', views.get_record_detail, name='record-detail'),
    path('create/', views.create_record, name='create-record'),
    path('<int:record_id>/update/', views.update_record, name='update-record'),
    path('<int:record_id>/delete/', views.delete_record, name='delete-record'),

    # Lookup data
    path('categories/', views.get_categories, name='categories'),
    path('types/', views.get_transaction_types, name='transaction-types'),
]
