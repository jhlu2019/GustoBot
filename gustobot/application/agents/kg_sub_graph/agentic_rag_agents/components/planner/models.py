from pydantic import BaseModel, Field

from ...components.models import Task


class PlannerOutput(BaseModel):
    tasks: list[Task] = Field(
        default_factory=list,
        description="A list of tasks that must be complete to satisfy the input question.",
    )
