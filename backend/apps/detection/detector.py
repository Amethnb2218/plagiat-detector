import numpy as np
import time
from typing import List, Dict, Tuple
from difflib import SequenceMatcher
import networkx as nx
from django.conf import settings

from apps.nlp_engine.embeddings import EmbeddingGenerator, FAISSIndex, CorpusIndex
from apps.documents.models import Document, DocumentSegment


class DirectCopyDetector:
    """Détection de copies directes par comparaison lexicale (n-grammes + SequenceMatcher)."""

    THRESHOLD = 0.90

    def detect(self, source_text: str, target_text: str) -> float:
        ratio = SequenceMatcher(None, source_text.lower(), target_text.lower()).ratio()
        return ratio

    def find_matches(self, source_sentences: List[str], target_sentences: List[str]) -> List[Dict]:
        matches = []
        for i, src in enumerate(source_sentences):
            for j, tgt in enumerate(target_sentences):
                score = self.detect(src, tgt)
                if score >= self.THRESHOLD:
                    matches.append({
                        'source_idx': i,
                        'target_idx': j,
                        'source_text': src,
                        'target_text': tgt,
                        'similarity': score,
                        'type': 'direct',
                    })
        return matches


class ParaphraseDetector:
    """Détection de paraphrases par similarité sémantique (LaBSE embeddings + cosine)."""

    THRESHOLD = 0.75
    HIGH_CONFIDENCE = 0.85

    def __init__(self):
        self.embedding_gen = EmbeddingGenerator(model_type='labse')
        self.faiss_manager = FAISSIndex(dimension=768)

    def detect_against_corpus(self, sentences: List[str], top_k: int = 5) -> List[Dict]:
        """Détecte les paraphrases en comparant contre le corpus indexé."""
        corpus_index = CorpusIndex()
        if corpus_index.index is None:
            return []

        matches = []
        embeddings = self.embedding_gen.encode(sentences, batch_size=64)

        distances, indices = self.faiss_manager.search(
            corpus_index.index, embeddings, top_k=top_k
        )

        for sent_idx, (dists, idxs) in enumerate(zip(distances, indices)):
            for dist, idx in zip(dists, idxs):
                if idx == -1:
                    continue
                if dist >= self.THRESHOLD:
                    matches.append({
                        'source_idx': sent_idx,
                        'source_text': sentences[sent_idx],
                        'corpus_idx': int(idx),
                        'similarity': float(dist),
                        'type': 'paraphrase' if dist < self.HIGH_CONFIDENCE else 'direct',
                    })

        return matches

    def detect_pairwise(self, source_sentences: List[str], target_sentences: List[str]) -> List[Dict]:
        """Comparaison directe entre deux documents."""
        src_embeddings = self.embedding_gen.encode(source_sentences, batch_size=64)
        tgt_embeddings = self.embedding_gen.encode(target_sentences, batch_size=64)

        similarities = np.dot(src_embeddings, tgt_embeddings.T)

        matches = []
        for i in range(len(source_sentences)):
            for j in range(len(target_sentences)):
                if similarities[i][j] >= self.THRESHOLD:
                    matches.append({
                        'source_idx': i,
                        'target_idx': j,
                        'source_text': source_sentences[i],
                        'target_text': target_sentences[j],
                        'similarity': float(similarities[i][j]),
                        'type': 'paraphrase',
                    })

        return matches


class CrossLingualDetector:
    """Détection cross-lingue via LaBSE (espace vectoriel partagé FR/EN)."""

    THRESHOLD = 0.72

    def __init__(self):
        self.embedding_gen = EmbeddingGenerator(model_type='labse')

    def detect(self, source_sentences: List[str], target_sentences: List[str],
               source_lang: str = 'fr', target_lang: str = 'en') -> List[Dict]:
        src_embeddings = self.embedding_gen.encode(source_sentences, batch_size=64)
        tgt_embeddings = self.embedding_gen.encode(target_sentences, batch_size=64)

        similarities = np.dot(src_embeddings, tgt_embeddings.T)

        matches = []
        for i in range(len(source_sentences)):
            best_j = np.argmax(similarities[i])
            if similarities[i][best_j] >= self.THRESHOLD:
                matches.append({
                    'source_idx': i,
                    'target_idx': int(best_j),
                    'source_text': source_sentences[i],
                    'target_text': target_sentences[int(best_j)],
                    'similarity': float(similarities[i][best_j]),
                    'source_lang': source_lang,
                    'target_lang': target_lang,
                    'type': 'cross_lingual',
                })

        return matches


class StructuralDetector:
    """Détection de plagiat structurel par analyse de graphe (NetworkX)."""

    THRESHOLD = 0.70

    def __init__(self):
        self.embedding_gen = EmbeddingGenerator(model_type='labse')

    def build_document_graph(self, segments: List[Dict]) -> nx.DiGraph:
        """Modélise un document comme un graphe dirigé de paragraphes."""
        G = nx.DiGraph()

        for i, segment in enumerate(segments):
            G.add_node(i, text=segment['text'], position=segment.get('position', i))

        for i in range(len(segments) - 1):
            G.add_edge(i, i + 1, relation='sequential')

        return G

    def detect_reorganization(self, source_graph: nx.DiGraph, target_graph: nx.DiGraph,
                              source_embeddings: np.ndarray, target_embeddings: np.ndarray) -> Dict:
        """Détecte si le document cible est une réorganisation du source."""
        similarities = np.dot(source_embeddings, target_embeddings.T)

        node_mapping = {}
        for i in range(len(source_embeddings)):
            best_j = np.argmax(similarities[i])
            if similarities[i][best_j] >= self.THRESHOLD:
                node_mapping[i] = int(best_j)

        if len(node_mapping) < 3:
            return {'is_reorganized': False, 'score': 0.0, 'mapping': {}}

        coverage = len(node_mapping) / max(source_graph.number_of_nodes(), 1)

        positions_source = [i for i in sorted(node_mapping.keys())]
        positions_target = [node_mapping[i] for i in positions_source]

        inversions = 0
        total_pairs = 0
        for i in range(len(positions_target)):
            for j in range(i + 1, len(positions_target)):
                total_pairs += 1
                if positions_target[i] > positions_target[j]:
                    inversions += 1

        inversion_ratio = inversions / max(total_pairs, 1)

        structural_score = coverage * inversion_ratio

        return {
            'is_reorganized': structural_score > 0.3,
            'score': structural_score,
            'coverage': coverage,
            'inversion_ratio': inversion_ratio,
            'mapping': node_mapping,
        }


class PlagiarismPipeline:
    """Pipeline complet de détection combinant toutes les méthodes."""

    def __init__(self):
        self.direct_detector = DirectCopyDetector()
        self.paraphrase_detector = ParaphraseDetector()
        self.cross_lingual_detector = CrossLingualDetector()
        self.structural_detector = StructuralDetector()
        self.weights = settings.PLAGIARISM_WEIGHTS

    def analyze_document(self, document: Document) -> Dict:
        """Exécute l'analyse complète d'un document."""
        start_time = time.time()

        segments = list(document.segments.filter(
            level=DocumentSegment.Level.SENTENCE
        ).values('id', 'text', 'position', 'char_start', 'char_end'))

        if not segments:
            return self._empty_result(start_time)

        sentences = [s['text'] for s in segments]

        # 1. Détection de paraphrases contre le corpus
        paraphrase_matches = self.paraphrase_detector.detect_against_corpus(sentences, top_k=5)

        # 2. Séparation copies directes vs paraphrases
        direct_matches = [m for m in paraphrase_matches if m['similarity'] >= 0.90]
        semantic_matches = [m for m in paraphrase_matches if 0.75 <= m['similarity'] < 0.90]

        # 3. Calcul des scores
        direct_score = self._compute_score(direct_matches, len(sentences))
        paraphrase_score = self._compute_score(semantic_matches, len(sentences))

        # 4. Score global pondéré
        overall_score = (
            self.weights['direct'] * direct_score +
            self.weights['semantic'] * paraphrase_score +
            self.weights['cross_lingual'] * 0 +
            self.weights['structural'] * 0
        ) * 100

        processing_time = time.time() - start_time

        return {
            'overall_score': min(overall_score, 100.0),
            'direct_copy_score': direct_score * 100,
            'paraphrase_score': paraphrase_score * 100,
            'cross_lingual_score': 0.0,
            'structural_score': 0.0,
            'matches': paraphrase_matches,
            'segments_analyzed': len(sentences),
            'matches_found': len(paraphrase_matches),
            'processing_time': processing_time,
        }

    def analyze_against_document(self, source_doc: Document, target_doc: Document) -> Dict:
        """Compare deux documents directement."""
        start_time = time.time()

        src_segments = list(source_doc.segments.filter(
            level=DocumentSegment.Level.SENTENCE
        ).values('id', 'text', 'position', 'char_start', 'char_end'))

        tgt_segments = list(target_doc.segments.filter(
            level=DocumentSegment.Level.SENTENCE
        ).values('id', 'text', 'position', 'char_start', 'char_end'))

        src_sentences = [s['text'] for s in src_segments]
        tgt_sentences = [s['text'] for s in tgt_segments]

        # 1. Copie directe
        direct_matches = self.direct_detector.find_matches(src_sentences, tgt_sentences)

        # 2. Paraphrase sémantique
        paraphrase_matches = self.paraphrase_detector.detect_pairwise(src_sentences, tgt_sentences)

        # 3. Cross-lingue
        cross_matches = []
        if source_doc.language != target_doc.language:
            cross_matches = self.cross_lingual_detector.detect(
                src_sentences, tgt_sentences,
                source_doc.language, target_doc.language
            )

        # 4. Analyse structurelle
        embedding_gen = EmbeddingGenerator(model_type='labse')
        src_embeddings = embedding_gen.encode(src_sentences)
        tgt_embeddings = embedding_gen.encode(tgt_sentences)

        src_graph = self.structural_detector.build_document_graph(src_segments)
        tgt_graph = self.structural_detector.build_document_graph(tgt_segments)
        structural_result = self.structural_detector.detect_reorganization(
            src_graph, tgt_graph, src_embeddings, tgt_embeddings
        )

        # 5. Calcul des scores
        direct_score = self._compute_score(direct_matches, len(src_sentences))
        paraphrase_score = self._compute_score(paraphrase_matches, len(src_sentences))
        cross_score = self._compute_score(cross_matches, len(src_sentences))
        structural_score = structural_result['score']

        overall_score = (
            self.weights['direct'] * direct_score +
            self.weights['semantic'] * paraphrase_score +
            self.weights['cross_lingual'] * cross_score +
            self.weights['structural'] * structural_score
        ) * 100

        all_matches = direct_matches + paraphrase_matches + cross_matches

        processing_time = time.time() - start_time

        return {
            'overall_score': min(overall_score, 100.0),
            'direct_copy_score': direct_score * 100,
            'paraphrase_score': paraphrase_score * 100,
            'cross_lingual_score': cross_score * 100,
            'structural_score': structural_score * 100,
            'matches': all_matches,
            'structural_details': structural_result,
            'segments_analyzed': len(src_sentences),
            'matches_found': len(all_matches),
            'processing_time': processing_time,
        }

    def _compute_score(self, matches: List[Dict], total_sentences: int) -> float:
        if not matches or total_sentences == 0:
            return 0.0
        unique_sources = set(m.get('source_idx', 0) for m in matches)
        return len(unique_sources) / total_sentences

    def _empty_result(self, start_time: float) -> Dict:
        return {
            'overall_score': 0.0,
            'direct_copy_score': 0.0,
            'paraphrase_score': 0.0,
            'cross_lingual_score': 0.0,
            'structural_score': 0.0,
            'matches': [],
            'segments_analyzed': 0,
            'matches_found': 0,
            'processing_time': time.time() - start_time,
        }
