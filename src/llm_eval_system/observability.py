from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from .config import Settings


@dataclass
class TraceHandle:
    id: str
    generation: Any | None = None


class Observability:
    """Langfuse adapter that degrades safely when credentials are absent."""

    def __init__(self, settings: Settings):
        self.client = None
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            from langfuse import Langfuse

            self.client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )

    @contextmanager
    def generation(
        self, *, name: str, user_id: str, session_id: str, metadata: dict[str, Any], input: Any
    ) -> Iterator[TraceHandle]:
        import uuid

        trace_id = uuid.uuid4().hex
        if self.client is None:
            yield TraceHandle(trace_id)
            return

        from langfuse import propagate_attributes

        with (
            self.client.start_as_current_observation(
                as_type="generation",
                name=name,
                input=input,
                metadata=metadata,
                trace_context={"trace_id": trace_id},
            ) as generation,
            propagate_attributes(user_id=user_id, session_id=session_id, metadata=metadata),
        ):
            try:
                yield TraceHandle(generation.trace_id, generation)
            except Exception as exc:
                generation.update(level="ERROR", status_message=str(exc))
                raise

    def end(self, handle: TraceHandle, *, output: str, model: str) -> None:
        if handle.generation is not None:
            handle.generation.update(output=output, model=model)

    def score(self, trace_id: str, name: str, value: float, comment: str | None = None) -> None:
        if self.client is not None:
            self.client.create_score(trace_id=trace_id, name=name, value=value, comment=comment)
