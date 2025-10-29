from typing import Literal
from pydantic import BaseModel, Field


class GuardrailsOutput(BaseModel):
    decision: Literal["end", "planner"] = Field(
        description="Decision on whether the question is related to the graph contents."
    )
