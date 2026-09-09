"""Request and response shapes for /chat.

The output guard validates the response against ChatResponse before anything
is returned, so this file is the contract that guard enforces.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """One turn from the user."""

    model_config = {"extra": "forbid"}

    message: str = Field(min_length=1, max_length=4000)
    # Which conversation this turn belongs to. Only Stage 1 uses it, and only
    # to demonstrate that in-process state does not survive a restart.
    session_id: str = Field(default="default", min_length=1, max_length=64)


class ChatResponse(BaseModel):
    """One answer, plus what is needed to find it in the trace."""

    model_config = {"extra": "forbid"}

    answer: str = Field(min_length=1)
    stage: int = Field(ge=1, le=3)
    # Returned so the UI can attach a thumbs up/down to this exact request.
    # Populated once Phoenix is wired in at step 4; None until then.
    trace_id: str | None = None


class FeedbackRequest(BaseModel):
    """A thumbs up or down on one earlier response."""

    model_config = {"extra": "forbid"}

    # The trace ID that /chat returned for the response being rated.
    trace_id: str = Field(min_length=32, max_length=32, pattern=r"^[0-9a-f]{32}$")
    helpful: bool
