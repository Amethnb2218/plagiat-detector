from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PlagiarismAnalysis
from .serializers import (
    PlagiarismAnalysisListSerializer,
    PlagiarismAnalysisDetailSerializer,
    StartAnalysisSerializer,
)
from .tasks import run_plagiarism_analysis, run_comparison_analysis
from apps.documents.models import Document


class StartAnalysisView(APIView):
    """Lance une nouvelle analyse de plagiat."""

    def post(self, request):
        serializer = StartAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document_id = serializer.validated_data['document_id']
        compare_with = serializer.validated_data.get('compare_with')

        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        if document.status != Document.Status.PROCESSED:
            return Response(
                {"error": "Le document doit être traité avant l'analyse."},
                status=status.HTTP_400_BAD_REQUEST
            )

        analysis = PlagiarismAnalysis.objects.create(
            document=document,
            initiated_by=request.user,
        )

        if compare_with:
            run_comparison_analysis.delay(str(analysis.id), str(compare_with))
        else:
            run_plagiarism_analysis.delay(str(analysis.id))

        return Response(
            PlagiarismAnalysisListSerializer(analysis).data,
            status=status.HTTP_201_CREATED
        )


class AnalysisListView(generics.ListAPIView):
    serializer_class = PlagiarismAnalysisListSerializer

    def get_queryset(self):
        if self.request.user.is_admin:
            return PlagiarismAnalysis.objects.all()
        return PlagiarismAnalysis.objects.filter(initiated_by=self.request.user)


class AnalysisDetailView(generics.RetrieveAPIView):
    serializer_class = PlagiarismAnalysisDetailSerializer

    def get_queryset(self):
        if self.request.user.is_admin:
            return PlagiarismAnalysis.objects.all()
        return PlagiarismAnalysis.objects.filter(initiated_by=self.request.user)


class AnalysisStatusView(APIView):
    """Vérifie le statut d'une analyse (polling)."""

    def get(self, request, pk):
        try:
            analysis = PlagiarismAnalysis.objects.get(id=pk)
        except PlagiarismAnalysis.DoesNotExist:
            return Response({"error": "Analyse introuvable."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': str(analysis.id),
            'status': analysis.status,
            'overall_score': analysis.overall_score,
            'processing_time': analysis.processing_time,
            'completed_at': analysis.completed_at,
        })
