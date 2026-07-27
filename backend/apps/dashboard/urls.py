from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.DashboardStatsView.as_view(), name='dashboard_stats'),
    path('history/', views.AnalysisHistoryView.as_view(), name='analysis_history'),
    path('distribution/', views.ScoreDistributionView.as_view(), name='score_distribution'),
]
