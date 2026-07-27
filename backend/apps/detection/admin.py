from django.contrib import admin
from .models import PlagiarismAnalysis, PlagiarismMatch


@admin.register(PlagiarismAnalysis)
class PlagiarismAnalysisAdmin(admin.ModelAdmin):
    list_display = ['document', 'initiated_by', 'status', 'overall_score', 'created_at']
    list_filter = ['status']
    readonly_fields = ['id', 'created_at', 'completed_at']


@admin.register(PlagiarismMatch)
class PlagiarismMatchAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'match_type', 'similarity_score']
    list_filter = ['match_type']
