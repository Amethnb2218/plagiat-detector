from django.db import models
from django.conf import settings
import uuid


class Document(models.Model):
    class Status(models.TextChoices):
        UPLOADED = 'uploaded', 'Téléversé'
        PROCESSING = 'processing', 'En traitement'
        PROCESSED = 'processed', 'Traité'
        ERROR = 'error', 'Erreur'

    class FileType(models.TextChoices):
        PDF = 'pdf', 'PDF'
        DOCX = 'docx', 'DOCX'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=500)
    file = models.FileField(upload_to='uploads/%Y/%m/')
    file_type = models.CharField(max_length=4, choices=FileType.choices)
    file_size = models.PositiveIntegerField(default=0)
    page_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.UPLOADED)
    author_name = models.CharField(max_length=255, blank=True)
    language = models.CharField(max_length=10, default='fr')
    raw_text = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title


class DocumentSegment(models.Model):
    class Level(models.TextChoices):
        CHAPTER = 'chapter', 'Chapitre'
        SECTION = 'section', 'Section'
        PARAGRAPH = 'paragraph', 'Paragraphe'
        SENTENCE = 'sentence', 'Phrase'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='segments')
    level = models.CharField(max_length=10, choices=Level.choices)
    position = models.PositiveIntegerField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    text = models.TextField()
    clean_text = models.TextField(blank=True)
    char_start = models.PositiveIntegerField(default=0)
    char_end = models.PositiveIntegerField(default=0)
    embedding = models.BinaryField(null=True, blank=True)
    embedding_model = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'document_segments'
        ordering = ['document', 'position']
        indexes = [
            models.Index(fields=['document', 'level']),
            models.Index(fields=['document', 'position']),
        ]

    def __str__(self):
        return f"{self.document.title} - {self.get_level_display()} #{self.position}"
