from rest_framework import serializers
from .models import PlagiarismAnalysis, PlagiarismMatch


class PlagiarismMatchSerializer(serializers.ModelSerializer):
    match_type_display = serializers.CharField(source='get_match_type_display', read_only=True)

    class Meta:
        model = PlagiarismMatch
        fields = ['id', 'match_type', 'match_type_display', 'similarity_score',
                  'source_text', 'source_char_start', 'source_char_end',
                  'target_text', 'target_document_title']


class PlagiarismAnalysisListSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source='document.title', read_only=True)
    initiated_by_name = serializers.CharField(source='initiated_by.get_full_name', read_only=True)

    class Meta:
        model = PlagiarismAnalysis
        fields = ['id', 'document', 'document_title', 'status',
                  'overall_score', 'direct_copy_score', 'paraphrase_score',
                  'cross_lingual_score', 'structural_score',
                  'segments_analyzed', 'matches_found', 'processing_time',
                  'initiated_by_name', 'created_at', 'completed_at']


class PlagiarismAnalysisDetailSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source='document.title', read_only=True)
    matches = PlagiarismMatchSerializer(many=True, read_only=True)
    initiated_by_name = serializers.CharField(source='initiated_by.get_full_name', read_only=True)

    class Meta:
        model = PlagiarismAnalysis
        fields = ['id', 'document', 'document_title', 'status',
                  'overall_score', 'direct_copy_score', 'paraphrase_score',
                  'cross_lingual_score', 'structural_score',
                  'segments_analyzed', 'matches_found', 'processing_time',
                  'initiated_by_name', 'created_at', 'completed_at',
                  'matches', 'error_message']


class StartAnalysisSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    compare_with = serializers.UUIDField(required=False)
