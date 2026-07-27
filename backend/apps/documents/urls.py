from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('', views.DocumentListView.as_view(), name='document_list'),
    path('<uuid:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
]
