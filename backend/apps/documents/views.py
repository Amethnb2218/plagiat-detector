from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from .models import Document
from .serializers import DocumentListSerializer, DocumentDetailSerializer, DocumentUploadSerializer
from apps.nlp_engine.tasks import process_document


class DocumentUploadView(generics.CreateAPIView):
    serializer_class = DocumentUploadSerializer
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        file = serializer.validated_data['file']
        file_type = 'pdf' if file.content_type == 'application/pdf' else 'docx'
        doc = serializer.save(
            owner=self.request.user,
            file_type=file_type,
            file_size=file.size,
        )
        process_document.delay(str(doc.id))


class DocumentListView(generics.ListAPIView):
    serializer_class = DocumentListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'file_type', 'language']

    def get_queryset(self):
        if self.request.user.is_admin:
            return Document.objects.all()
        return Document.objects.filter(owner=self.request.user)


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = DocumentDetailSerializer

    def get_queryset(self):
        if self.request.user.is_admin:
            return Document.objects.all()
        return Document.objects.filter(owner=self.request.user)
