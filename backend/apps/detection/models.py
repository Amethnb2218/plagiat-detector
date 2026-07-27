from django.db import models
from django.conf import settings
import uuid


class PlagiarismAnalysis(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        RUNNING = 'running', 'En cours'
        COMPLETED = 'completed', 'Terminée'
        FAILED = 'failed', 'Échouée'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey('documents.Document', on_delete=models.CASCADE, related_name='analyses')
    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='analyses')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    # Scores
    overall_score = models.FloatField(default=0.0)
    direct_copy_score = models.FloatField(default=0.0)
    paraphrase_score = models.FloatField(default=0.0)
    cross_lingual_score = models.FloatField(default=0.0)
    structural_score = models.FloatField(default=0.0)

    # Metadata
    segments_analyzed = models.PositiveIntegerField(default=0)
    matches_found = models.PositiveIntegerField(default=0)
    processing_time = models.FloatField(default=0.0)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'plagiarism_analyses'
        ordering = ['-created_at']

    def __str__(self):
        return f"Analyse de {self.document.title} - {self.overall_score:.1f}%"


class PlagiarismMatch(models.Model):
    class MatchType(models.TextChoices):
        DIRECT = 'direct', 'Copie directe'
        PARAPHRASE = 'paraphrase', 'Paraphrase'
        CROSS_LINGUAL = 'cross_lingual', 'Cross-lingue'
        STRUCTURAL = 'structural', 'Structurelle'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(PlagiarismAnalysis, on_delete=models.CASCADE, related_name='matches')
    match_type = models.CharField(max_length=15, choices=MatchType.choices)
    similarity_score = models.FloatField()

    # Source (le segment analysé)
    source_segment = models.ForeignKey(
        'documents.DocumentSegment', on_delete=models.CASCADE,
        related_name='source_matches', null=True
    )
    source_text = models.TextField()
    source_char_start = models.PositiveIntegerField(default=0)
    source_char_end = models.PositiveIntegerField(default=0)

    # Target (le segment trouvé dans le corpus)
    target_segment = models.ForeignKey(
        'documents.DocumentSegment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='target_matches'
    )
    target_text = models.TextField()
    target_document_title = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'plagiarism_matches'
        ordering = ['-similarity_score']

    def __str__(self):
        return f"{self.get_match_type_display()} - {self.similarity_score:.2f}"
