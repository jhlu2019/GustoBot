from pydantic import BaseModel, Field


class text2cypher(BaseModel):
    """Generate, Validate, Correct and Execute a Cypher statement against Neo4j to retrieve relevant information."""

    subquestion: str = Field(
        ..., description="The question that the Cypher should address"
    )
