import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

try:
    from celery import shared_task
except ImportError:
    def shared_task(*args, **kwargs):
        def decorator(func):
            func.delay = lambda *a, **kw: func(*a, **kw)
            func.apply_async = lambda *a, **kw: func(*a.get('args', []), **kw)
            return func
        if args and callable(args[0]):
            return decorator(args[0])
        return decorator

from .models import PlagiarismAnalysis, PlagiarismMatch

DETECTOR_AVAILABLE = False
try:
    from .detector import PlagiarismPipeline
    DETECTOR_AVAILABLE = True
except ImportError:
    logger.warning("Detection pipeline not available (missing ML deps)")
from apps.documents.models import Document, DocumentSegment


@shared_task(bind=True, max_retries=2, time_limit=1800)
def run_plagiarism_analysis(self, analysis_id: str):
    """Lance l'analyse de plagiat complète pour un document."""
    try:
        analysis = PlagiarismAnalysis.objects.get(id=analysis_id)
        analysis.status = PlagiarismAnalysis.Status.RUNNING
        analysis.save(update_fields=['status'])

        pipeline = PlagiarismPipeline()
        result = pipeline.analyze_document(analysis.document)

        # Mise à jour des scores
        analysis.overall_score = result['overall_score']
        analysis.direct_copy_score = result['direct_copy_score']
        analysis.paraphrase_score = result['paraphrase_score']
        analysis.cross_lingual_score = result['cross_lingual_score']
        analysis.structural_score = result['structural_score']
        analysis.segments_analyzed = result['segments_analyzed']
        analysis.matches_found = result['matches_found']
        analysis.processing_time = result['processing_time']
        analysis.status = PlagiarismAnalysis.Status.COMPLETED
        analysis.completed_at = timezone.now()
        analysis.save()

        # Sauvegarde des matches
        _save_matches(analysis, result['matches'])

        return {'status': 'completed', 'analysis_id': analysis_id, 'score': result['overall_score']}

    except Exception as exc:
        analysis = PlagiarismAnalysis.objects.get(id=analysis_id)
        analysis.status = PlagiarismAnalysis.Status.FAILED
        analysis.error_message = str(exc)
        analysis.save(update_fields=['status', 'error_message'])
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=2, time_limit=3600)
def run_comparison_analysis(self, analysis_id: str, target_document_id: str):
    """Compare un document contre un autre document spécifique."""
    try:
        analysis = PlagiarismAnalysis.objects.get(id=analysis_id)
        target_doc = Document.objects.get(id=target_document_id)

        analysis.status = PlagiarismAnalysis.Status.RUNNING
        analysis.save(update_fields=['status'])

        pipeline = PlagiarismPipeline()
        result = pipeline.analyze_against_document(analysis.document, target_doc)

        analysis.overall_score = result['overall_score']
        analysis.direct_copy_score = result['direct_copy_score']
        analysis.paraphrase_score = result['paraphrase_score']
        analysis.cross_lingual_score = result['cross_lingual_score']
        analysis.structural_score = result['structural_score']
        analysis.segments_analyzed = result['segments_analyzed']
        analysis.matches_found = result['matches_found']
        analysis.processing_time = result['processing_time']
        analysis.status = PlagiarismAnalysis.Status.COMPLETED
        analysis.completed_at = timezone.now()
        analysis.save()

        _save_matches(analysis, result['matches'], target_doc)

        return {'status': 'completed', 'analysis_id': analysis_id, 'score': result['overall_score']}

    except Exception as exc:
        analysis = PlagiarismAnalysis.objects.get(id=analysis_id)
        analysis.status = PlagiarismAnalysis.Status.FAILED
        analysis.error_message = str(exc)
        analysis.save(update_fields=['status', 'error_message'])
        raise self.retry(exc=exc, countdown=60)


def _save_matches(analysis, matches, target_doc=None):
    """Sauvegarde les correspondances détectées."""
    match_objects = []
    for match in matches[:100]:  # Limiter à 100 résultats
        match_type_map = {
            'direct': PlagiarismMatch.MatchType.DIRECT,
            'paraphrase': PlagiarismMatch.MatchType.PARAPHRASE,
            'cross_lingual': PlagiarismMatch.MatchType.CROSS_LINGUAL,
            'structural': PlagiarismMatch.MatchType.STRUCTURAL,
        }

        match_objects.append(PlagiarismMatch(
            analysis=analysis,
            match_type=match_type_map.get(match['type'], PlagiarismMatch.MatchType.PARAPHRASE),
            similarity_score=match['similarity'],
            source_text=match.get('source_text', ''),
            target_text=match.get('target_text', ''),
            target_document_title=target_doc.title if target_doc else '',
        ))

    PlagiarismMatch.objects.filter(analysis=analysis).delete()
    PlagiarismMatch.objects.bulk_create(match_objects, batch_size=50)
