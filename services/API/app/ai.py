import os
from sentence_transformers import SentenceTransformer, CrossEncoder
from typing import List

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CROSS_ENCODER_MODEL_NAME = os.getenv("CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

# Lazy init to avoid blocking startup due to heavy model downloads
_embedding_model = None
_cross_encoder = None


def _ensure_models():
    global _embedding_model, _cross_encoder
    if _embedding_model is None:
        try:
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        except Exception as e:
            # Fallback to a lightweight deterministic dummy embedding
            try:
                from loguru import logger
                logger.warning(f"Embedding model init failed: {e}; using dummy embedding")
            except Exception:
                pass

            class _DummyEmb:
                def encode(self, text: str, normalize_embeddings: bool = True):
                    import hashlib, random
                    seed = int.from_bytes(hashlib.md5(text.encode()).digest()[:4], "big")
                    rnd = random.Random(seed)
                    # Default dimension for MiniLM is 384
                    return [rnd.random() for _ in range(384)]

                def get_sentence_embedding_dimension(self) -> int:
                    return 384

            _embedding_model = _DummyEmb()

    if _cross_encoder is None:
        try:
            _cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL_NAME)
        except Exception as e:
            try:
                from loguru import logger
                logger.warning(f"Cross encoder init failed: {e}; using dummy scorer")
            except Exception:
                pass

            class _DummyCE:
                def predict(self, pairs):
                    # Return zero scores to keep behavior deterministic
                    return [0.0] * len(pairs)

            _cross_encoder = _DummyCE()


def get_text_embedding(text: str) -> List[float]:
    _ensure_models()
    return _embedding_model.encode(text, normalize_embeddings=True)


def get_embedding_dimension() -> int:
    _ensure_models()
    return _embedding_model.get_sentence_embedding_dimension()


def rerank_pairs(query: str, candidates: List[str]) -> List[float]:
    _ensure_models()
    pairs = [(query, c) for c in candidates]
    scores = _cross_encoder.predict(pairs)
    return scores.tolist() if hasattr(scores, 'tolist') else list(scores)