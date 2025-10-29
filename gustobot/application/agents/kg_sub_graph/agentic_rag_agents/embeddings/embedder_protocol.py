from typing import List, Protocol, runtime_checkable


@runtime_checkable
class EmbedderProtocol(Protocol):
    """An Embedder must follow this protocol to be used by the package."""

    def embed_query(self, text: str) -> List[float]: ...
