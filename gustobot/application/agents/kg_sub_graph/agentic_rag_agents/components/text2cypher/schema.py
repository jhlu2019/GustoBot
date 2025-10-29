from pydantic import BaseModel, Field


class text2cypher(BaseModel):
    """The default data retrieval tool. Use an LLM to generate a new Cypher query that satisfies the task."""

    task: str = Field(..., description="The task the Cypher query must answer.")


def get_text2cypher_schema() -> type[text2cypher]:
    """Get the schema for a text2cypher tool. This may be passed to a tool selection LLM as context."""
    return text2cypher
