from django.contrib import admin
from .models import Document, DocumentSegment


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'file_type', 'status', 'page_count', 'uploaded_at']
    list_filter = ['status', 'file_type', 'language']
    search_fields = ['title', 'author_name']
    readonly_fields = ['id', 'uploaded_at', 'processed_at']


@admin.register(DocumentSegment)
class DocumentSegmentAdmin(admin.ModelAdmin):
    list_display = ['document', 'level', 'position']
    list_filter = ['level']
    search_fields = ['text']
