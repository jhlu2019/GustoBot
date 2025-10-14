from typing import Optional

from pydantic import BaseModel, Field

from .text2cypher.state import CypherOutputState
from .visualize.state import VisualizationOutputState


class Task(BaseModel):
    question: str = Field(..., description="The question to be addressed.")
    parent_task: str = Field(
        ..., description="The parent task this task is derived from."
    )
    requires_visualization: bool = Field(
        default=False,
        description="Whether this task requires a visual to be returned.",
    )
    data: Optional[CypherOutputState] = Field(
        default=None, description="The Cypher query result details."
    )
    visualization: Optional[VisualizationOutputState] = Field(
        default=None, description="The visualization details."
    )

    @property
    def is_complete(self) -> bool:
        viz_bool = (self.requires_visualization and self.visualization is not None) or (
            not self.requires_visualization and self.visualization is None
        )
        return viz_bool and self.data is not None
