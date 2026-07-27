import re
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

from apps.documents.models import Document, DocumentSegment
from .extractor import TextExtractor, TextCleaner

ML_AVAILABLE = False
try:
    import numpy as np
    from .segmenter import HierarchicalSegmenter
    from .embeddings import EmbeddingGenerator, FAISSIndex
    ML_AVAILABLE = True
except ImportError:
    logger.warning("ML dependencies not installed. Running in light mode (text extraction only).")


def simple_sentence_split(text):
    """Segmentation basique quand SpaCy n'est pas disponible."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = []
    pos = 0
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if len(sent) >= 15:
            start = text.find(sent, pos)
            if start == -1:
                start = pos
            result.append({
                'position': len(result),
                'text': sent,
                'char_start': start,
                'char_end': start + len(sent),
            })
            pos = start + len(sent)
    return result


@shared_task(bind=True, max_retries=3, time_limit=600)
def process_document(self, document_id: str):
    """Pipeline de traitement d'un document: extraction, nettoyage, segmentation, embeddings."""
    try:
        doc = Document.objects.get(id=document_id)
        doc.status = Document.Status.PROCESSING
        doc.save(update_fields=['status'])

        # 1. Extraction de texte
        result = TextExtractor.extract(doc.file.path, doc.file_type)
        doc.raw_text = result['raw_text']
        doc.page_count = result['page_count']
        doc.metadata = result['metadata']
        doc.save(update_fields=['raw_text', 'page_count', 'metadata'])

        # 2. Nettoyage
        clean_text = TextCleaner.clean(doc.raw_text)

        # 3. Segmentation
        if ML_AVAILABLE:
            try:
                segmenter = HierarchicalSegmenter(language=doc.language)
                sentences = segmenter.get_flat_sentences(clean_text)
            except Exception:
                sentences = simple_sentence_split(clean_text)
        else:
            sentences = simple_sentence_split(clean_text)

        # 4. Création des segments en base
        segments_to_create = []
        for sent_data in sentences:
            segments_to_create.append(DocumentSegment(
                document=doc,
                level=DocumentSegment.Level.SENTENCE,
                position=sent_data['position'],
                text=sent_data['text'],
                clean_text=sent_data['text'],
                char_start=sent_data['char_start'],
                char_end=sent_data['char_end'],
                embedding_model='LaBSE' if ML_AVAILABLE else 'none',
            ))

        DocumentSegment.objects.filter(document=doc).delete()
        created_segments = DocumentSegment.objects.bulk_create(segments_to_create, batch_size=500)

        # 5. Génération des embeddings (si ML disponible)
        if ML_AVAILABLE and created_segments:
            try:
                texts = [s.text for s in created_segments]
                generator = EmbeddingGenerator(model_type='labse')
                embeddings = generator.encode(texts, batch_size=64)

                for segment, embedding in zip(created_segments, embeddings):
                    segment.embedding = embedding.tobytes()

                DocumentSegment.objects.bulk_update(created_segments, ['embedding'], batch_size=500)

                # 6. Index FAISS du document
                faiss_index = FAISSIndex(dimension=768)
                index_name = f"doc_{document_id}"
                faiss_index.create_index(embeddings, index_name)
            except Exception as e:
                logger.warning(f"Embedding generation failed: {e}. Document processed without embeddings.")

        doc.status = Document.Status.PROCESSED
        doc.processed_at = timezone.now()
        doc.save(update_fields=['status', 'processed_at'])

        return {'status': 'success', 'document_id': document_id, 'segments_count': len(created_segments)}

    except Exception as exc:
        doc = Document.objects.get(id=document_id)
        doc.status = Document.Status.ERROR
        doc.error_message = str(exc)
        doc.save(update_fields=['status', 'error_message'])
        raise self.retry(exc=exc, countdown=30)


@shared_task(time_limit=1800)
def rebuild_corpus_index():
    """Reconstruit l'index FAISS global."""
    if not ML_AVAILABLE:
        return {'status': 'skipped', 'reason': 'ML dependencies not installed'}

    from .embeddings import CorpusIndex

    segments = DocumentSegment.objects.filter(
        document__status=Document.Status.PROCESSED,
        level=DocumentSegment.Level.SENTENCE,
    ).values('id', 'text')

    segments_list = list(segments)
    if not segments_list:
        return {'status': 'empty', 'count': 0}

    corpus_index = CorpusIndex()
    corpus_index.build_from_segments([{'id': str(s['id']), 'text': s['text']} for s in segments_list])

    return {'status': 'success', 'indexed_segments': len(segments_list)}
