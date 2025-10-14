from typing import Any, Dict, List

from pydantic import BaseModel, Field


class visualization(BaseModel):
    """Generate, Validate and Correct a data visualization."""

    subquestion: str = Field(
        ..., description="The question that the visualization should address."
    )
    data: List[Dict[str, Any]] = Field(
        ..., description="The data available for the visualization."
    )
