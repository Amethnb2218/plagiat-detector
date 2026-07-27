from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:analysis_id>/pdf/', views.GenerateReportPDFView.as_view(), name='report_pdf'),
]
