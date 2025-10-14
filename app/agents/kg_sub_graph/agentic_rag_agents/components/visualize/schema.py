from pydantic import BaseModel, Field


class visualize(BaseModel):
    """Generate a chart to visualize the retrieved data."""

    task: str = Field(..., description="The question the Cypher query must answer.")
    # we do not specify the `records` field because we do not want the LLM providing records information. This will be manually included.
