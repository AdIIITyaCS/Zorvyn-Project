from django.urls import path
from . import views

urlpatterns = [
    # Dashboard summaries
    path('summary/', views.get_summary, name='dashboard-summary'),
    path('category-breakdown/', views.get_category_breakdown,
         name='category-breakdown'),
    path('monthly-trend/', views.get_monthly_trend, name='monthly-trend'),
    path('recent-activity/', views.get_recent_activity, name='recent-activity'),
    path('period-summary/', views.get_period_summary, name='period-summary'),

    # Admin dashboards
    path('all-users-summary/', views.get_all_users_summary,
         name='all-users-summary'),
]
