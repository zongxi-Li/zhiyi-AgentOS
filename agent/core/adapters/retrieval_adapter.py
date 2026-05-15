"""Public retrieval adapter facade for legal, education, and code search."""

from core.adapters.retrieval.chroma_client import chroma_client, chroma_legal_client
from core.adapters.retrieval.code_index_builder import build_code_index, code_index_builder, search_code
from core.adapters.retrieval.education_index_builder import education_index_builder
from core.adapters.retrieval.legal_index_builder import legal_index_builder

__all__ = [
    "build_code_index",
    "chroma_client",
    "chroma_legal_client",
    "code_index_builder",
    "education_index_builder",
    "legal_index_builder",
    "search_code",
]
