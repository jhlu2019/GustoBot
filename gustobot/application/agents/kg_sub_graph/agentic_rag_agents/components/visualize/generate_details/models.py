from typing import Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class ChartDetailsOutput(BaseModel):
    title: str = Field(description="The chart title.")
    x_axis_key: str = Field(
        description="The key present in the data used to retrieve the x values."
    )
    y_axis_key: str = Field(
        description="The key present in the data used to retrieve the y values."
    )
    hue_key: str = Field(
        description="The key present in the data used to group bars, lines, points, etc"
    )
    chart_type: Literal["line", "bar", "scatter"] = Field(
        description="The type of chart to create with the data."
    )
    chart_description: str = Field(
        description="A description of what the chart is displaying."
    )

    @field_validator("x_axis_key", "y_axis_key", "hue_key")
    def validate_axis_keys(cls, v: str, info: ValidationInfo) -> str:
        """Validate the x or y axis key against the existing data."""

        if info.context is not None and info.context.get("keys") is not None:
            keys = info.context.get("keys")
            assert v in keys

        return v
