from typing import List

from pydantic import BaseModel, Field

from ...components.models import Task


class PlannerOutput(BaseModel):
    tasks: List[Task] = Field(
        default=[],
        description="A list of tasks that must be complete to satisfy the input question.",
    )
