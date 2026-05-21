"""External capability adapters used by Agent Core."""

from agentos.adapters.federated_adapter import FederatedAdapter
from agentos.adapters.model_adapter import AIService, ModelAdapter

__all__ = ["AIService", "FederatedAdapter", "ModelAdapter"]
