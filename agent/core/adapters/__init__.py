"""External capability adapters used by Agent Core."""

from core.adapters.federated_adapter import FederatedAdapter
from core.adapters.model_adapter import AIService, ModelAdapter

__all__ = ["AIService", "FederatedAdapter", "ModelAdapter"]
