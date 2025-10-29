from typing import Optional

from pydantic import BaseModel, Field


class ValidateFinalAnswerResponse(BaseModel):
    valid: bool = Field(
        description="Whether the final answer sufficiently answers the provided question."
    )
    follow_up_question: Optional[str] = Field(
        description="A follow up question to ask that will gather the remaining information needed.",
        default=None,
    )
