from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.StartAnalysisView.as_view(), name='start_analysis'),
    path('', views.AnalysisListView.as_view(), name='analysis_list'),
    path('<uuid:pk>/', views.AnalysisDetailView.as_view(), name='analysis_detail'),
    path('<uuid:pk>/status/', views.AnalysisStatusView.as_view(), name='analysis_status'),
]
