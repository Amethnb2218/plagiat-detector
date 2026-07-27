import numpy as np
import faiss
import os
import threading
from typing import List, Optional
from pathlib import Path
from django.conf import settings


_model_lock = threading.Lock()
_labse_model = None
_sbert_model = None


def get_labse_model():
    """Singleton LaBSE model - chargé une seule fois par worker."""
    global _labse_model
    if _labse_model is None:
        with _model_lock:
            if _labse_model is None:
                from sentence_transformers import SentenceTransformer
                _labse_model = SentenceTransformer(settings.AI_MODELS['LABSE_MODEL'])
    return _labse_model


def get_sbert_model():
    """Singleton SBERT model pour le français."""
    global _sbert_model
    if _sbert_model is None:
        with _model_lock:
            if _sbert_model is None:
                from sentence_transformers import SentenceTransformer
                _sbert_model = SentenceTransformer(settings.AI_MODELS['SBERT_MODEL'])
    return _sbert_model


class EmbeddingGenerator:
    """Génération d'embeddings sémantiques avec LaBSE (cross-lingue) ou SBERT."""

    def __init__(self, model_type='labse'):
        self.model_type = model_type

    @property
    def model(self):
        if self.model_type == 'labse':
            return get_labse_model()
        return get_sbert_model()

    @property
    def dimension(self):
        return 768

    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embeddings.astype(np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        embedding = self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embedding[0].astype(np.float32)


class FAISSIndex:
    """Gestion de l'index FAISS pour la recherche de similarité."""

    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.index_dir = Path(settings.FAISS_INDEX_PATH)
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def create_index(self, embeddings: np.ndarray, index_name: str) -> faiss.Index:
        n_vectors = embeddings.shape[0]
        embeddings = np.ascontiguousarray(embeddings.astype(np.float32))
        faiss.normalize_L2(embeddings)

        if n_vectors < 1000:
            index = faiss.IndexFlatIP(self.dimension)
        else:
            nlist = min(int(np.sqrt(n_vectors)), 256)
            quantizer = faiss.IndexFlatIP(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist, faiss.METRIC_INNER_PRODUCT)
            index.train(embeddings)

        index.add(embeddings)
        index_path = self.index_dir / f"{index_name}.index"
        faiss.write_index(index, str(index_path))
        return index

    def load_index(self, index_name: str) -> Optional[faiss.Index]:
        index_path = self.index_dir / f"{index_name}.index"
        if not index_path.exists():
            return None
        return faiss.read_index(str(index_path))

    def search(self, index: faiss.Index, query_embeddings: np.ndarray, top_k: int = 10) -> tuple:
        query_embeddings = np.ascontiguousarray(query_embeddings.astype(np.float32))
        faiss.normalize_L2(query_embeddings)

        if hasattr(index, 'nprobe'):
            index.nprobe = 10

        distances, indices = index.search(query_embeddings, top_k)
        return distances, indices

    def add_to_index(self, index: faiss.Index, embeddings: np.ndarray, index_name: str):
        embeddings = np.ascontiguousarray(embeddings.astype(np.float32))
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
        index_path = self.index_dir / f"{index_name}.index"
        faiss.write_index(index, str(index_path))


class CorpusIndex:
    """Index global du corpus de référence pour la détection de plagiat."""

    INDEX_NAME = 'corpus_global'

    def __init__(self):
        self.embedding_gen = EmbeddingGenerator(model_type='labse')
        self.faiss_index = FAISSIndex(dimension=768)
        self._index = None
        self._segment_ids = []

    @property
    def index(self):
        if self._index is None:
            self._index = self.faiss_index.load_index(self.INDEX_NAME)
        return self._index

    def build_from_segments(self, segments_data: List[dict]):
        """Construit l'index à partir de segments avec leurs textes."""
        texts = [s['text'] for s in segments_data]
        self._segment_ids = [s['id'] for s in segments_data]

        embeddings = self.embedding_gen.encode(texts, batch_size=64)
        self._index = self.faiss_index.create_index(embeddings, self.INDEX_NAME)

        ids_path = self.faiss_index.index_dir / f"{self.INDEX_NAME}_ids.npy"
        np.save(str(ids_path), np.array(self._segment_ids, dtype=object))

    def search_similar(self, query_text: str, top_k: int = 10) -> List[dict]:
        if self.index is None:
            return []

        query_embedding = self.embedding_gen.encode_single(query_text).reshape(1, -1)
        distances, indices = self.faiss_index.search(self.index, query_embedding, top_k)

        ids_path = self.faiss_index.index_dir / f"{self.INDEX_NAME}_ids.npy"
        if ids_path.exists():
            segment_ids = np.load(str(ids_path), allow_pickle=True)
        else:
            segment_ids = np.array([])

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            result = {
                'index': int(idx),
                'similarity': float(dist),
            }
            if idx < len(segment_ids):
                result['segment_id'] = str(segment_ids[idx])
            results.append(result)

        return results
