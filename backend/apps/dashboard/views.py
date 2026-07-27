from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from apps.documents.models import Document
from apps.detection.models import PlagiarismAnalysis


class DashboardStatsView(APIView):
    """Statistiques globales du tableau de bord."""

    def get(self, request):
        user = request.user
        base_docs = Document.objects.all() if user.is_admin else Document.objects.filter(owner=user)
        base_analyses = PlagiarismAnalysis.objects.all() if user.is_admin else PlagiarismAnalysis.objects.filter(initiated_by=user)

        total_documents = base_docs.count()
        total_analyses = base_analyses.count()
        completed_analyses = base_analyses.filter(status=PlagiarismAnalysis.Status.COMPLETED)

        avg_score = completed_analyses.aggregate(avg=Avg('overall_score'))['avg'] or 0
        high_risk_count = completed_analyses.filter(overall_score__gte=50).count()
        medium_risk_count = completed_analyses.filter(overall_score__gte=25, overall_score__lt=50).count()
        low_risk_count = completed_analyses.filter(overall_score__lt=25).count()

        # Activité récente (7 derniers jours)
        week_ago = timezone.now() - timedelta(days=7)
        recent_analyses = base_analyses.filter(created_at__gte=week_ago).count()
        recent_documents = base_docs.filter(uploaded_at__gte=week_ago).count()

        return Response({
            'total_documents': total_documents,
            'total_analyses': total_analyses,
            'average_score': round(avg_score, 1),
            'high_risk_count': high_risk_count,
            'medium_risk_count': medium_risk_count,
            'low_risk_count': low_risk_count,
            'recent_analyses': recent_analyses,
            'recent_documents': recent_documents,
            'detection_rate': {
                'direct': completed_analyses.filter(direct_copy_score__gt=0).count(),
                'paraphrase': completed_analyses.filter(paraphrase_score__gt=0).count(),
                'cross_lingual': completed_analyses.filter(cross_lingual_score__gt=0).count(),
                'structural': completed_analyses.filter(structural_score__gt=0).count(),
            }
        })


class AnalysisHistoryView(APIView):
    """Historique des analyses avec pagination."""

    def get(self, request):
        user = request.user
        base_analyses = PlagiarismAnalysis.objects.all() if user.is_admin else PlagiarismAnalysis.objects.filter(initiated_by=user)

        analyses = base_analyses.filter(
            status=PlagiarismAnalysis.Status.COMPLETED
        ).select_related('document').order_by('-completed_at')[:50]

        data = [{
            'id': str(a.id),
            'document_title': a.document.title,
            'overall_score': a.overall_score,
            'direct_copy_score': a.direct_copy_score,
            'paraphrase_score': a.paraphrase_score,
            'cross_lingual_score': a.cross_lingual_score,
            'structural_score': a.structural_score,
            'completed_at': a.completed_at,
            'processing_time': a.processing_time,
        } for a in analyses]

        return Response(data)


class ScoreDistributionView(APIView):
    """Distribution des scores pour le graphique."""

    def get(self, request):
        user = request.user
        base = PlagiarismAnalysis.objects.filter(status=PlagiarismAnalysis.Status.COMPLETED)
        if not user.is_admin:
            base = base.filter(initiated_by=user)

        ranges = [
            ('0-10%', 0, 10), ('10-20%', 10, 20), ('20-30%', 20, 30),
            ('30-40%', 30, 40), ('40-50%', 40, 50), ('50-60%', 50, 60),
            ('60-70%', 60, 70), ('70-80%', 70, 80), ('80-90%', 80, 90),
            ('90-100%', 90, 101),
        ]

        distribution = []
        for label, low, high in ranges:
            count = base.filter(overall_score__gte=low, overall_score__lt=high).count()
            distribution.append({'range': label, 'count': count})

        return Response(distribution)
