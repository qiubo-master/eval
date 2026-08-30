from typing import Literal

from pydantic import BaseModel, Field


Scenario = Literal["customer_service", "operations_agent"]


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=20_000)
    scenario: Scenario = "customer_service"
    contexts: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    variant: Literal["A", "B"]
    trace_id: str
    model: str


class FeedbackRequest(BaseModel):
    trace_id: str
    user_id: str
    thumbs_up: bool | None = None
    resolved: bool | None = None
    csat: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2_000)

