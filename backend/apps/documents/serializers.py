from rest_framework import serializers
from .models import Document, DocumentSegment


class DocumentSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentSegment
        fields = ['id', 'level', 'position', 'text', 'clean_text', 'char_start', 'char_end']


class DocumentListSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    segment_count = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'title', 'file_type', 'file_size', 'page_count',
                  'status', 'author_name', 'language', 'owner_name',
                  'uploaded_at', 'processed_at', 'segment_count']

    def get_segment_count(self, obj):
        return obj.segments.count()


class DocumentDetailSerializer(serializers.ModelSerializer):
    segments = DocumentSegmentSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'title', 'file_type', 'file_size', 'page_count',
                  'status', 'author_name', 'language', 'raw_text', 'metadata',
                  'owner_name', 'uploaded_at', 'processed_at', 'segments', 'error_message']


class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = Document
        fields = ['title', 'file', 'author_name', 'language']

    def validate_file(self, value):
        allowed_types = ['application/pdf',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Seuls les fichiers PDF et DOCX sont acceptés.")
        if value.size > 52428800:  # 50MB
            raise serializers.ValidationError("La taille du fichier ne doit pas dépasser 50 Mo.")
        return value
