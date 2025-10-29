"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator

NUMBER_ENUM = {"INTEGER", "FLOAT"}


class Property(BaseModel):
    """
    Represents a filter condition based on a specific node property in a graph in a Cypher statement.
    """

    node_label: str = Field(
        description="The label of the node to which this property belongs."
    )
    property_key: str = Field(description="The key of the property being filtered.")
    property_value: str = Field(
        description="The value that the property is being matched against.",
        coerce_numbers_to_str=True,
    )


class ValidateCypherOutput(BaseModel):
    """
    Represents the validation result of a Cypher query's output,
    including any errors and applied filters.
    """

    errors: Optional[List[str]] = Field(
        description="A list of syntax or semantical errors in the Cypher statement. Always explain the discrepancy between schema and Cypher statement"
    )
    filters: Optional[List[Property]] = Field(
        description="A list of property-based filters applied in the Cypher statement."
    )


class BaseNeo4jStructuredSchemaProperty(BaseModel):
    property: str = Field(description="The property name.")
    type: str = Field(description="The Neo4j type of the property.")


class Neo4jStructuredSchemaPropertyString(BaseNeo4jStructuredSchemaProperty):
    values: List[str] = Field(
        description="A list of example values directly from the database."
    )
    distinct_count: Optional[int] = Field(
        description="The number of distinct values in the database.", default=None
    )

    @property
    def is_enum(self) -> bool:
        """Whether the object contains a valid enum."""
        if len(self.values) > 0 and self.distinct_count is not None:
            return len(self.values) == self.distinct_count
        else:
            return False

    @field_validator("type")
    def validate_prop_type(cls, v: str) -> str:
        assert v == "STRING", "Property type must be 'STRING'."
        return v

    def get_property_values_enum(self) -> Set[str]:
        """
        A set with the values of the property.
        If `distinct_count` != the number of items in `values` then an empty set will be returned.

        Returns
        -------
        Set[str]
            The enum.
        """

        if self.is_enum:
            return set(self.values)
        else:
            return set()


class Neo4jStructuredSchemaPropertyNumber(BaseNeo4jStructuredSchemaProperty):
    min: float = Field(
        description="The min value of the number.", default=float("-inf")
    )
    max: float = Field(description="The max value of the number.", default=float("inf"))
    distinct_count: Optional[int] = Field(
        description="The number of distinct values in the database.", default=None
    )

    @field_validator("type")
    def validate_prop_type(cls, v: str) -> str:
        assert v in NUMBER_ENUM, "Property type must be 'INTEGER' or 'FLOAT'."
        return v

    @property
    def is_enum(self) -> bool:
        """Whether the object contains a valid enum."""
        return False


class Neo4jStructuredSchemaPropertyList(BaseNeo4jStructuredSchemaProperty):
    min_size: int = Field(description="The minimum size of the list.")
    max_size: int = Field(description="The maximum size of the list.")

    @field_validator("type")
    def validate_prop_type(cls, v: str) -> str:
        assert v == "LIST", "Property type must be 'LIST'."
        return v

    @property
    def is_enum(self) -> bool:
        """Whether the object contains a valid enum."""
        return False


class Neo4jStructuredSchemaPropertyDateTime(BaseNeo4jStructuredSchemaProperty):
    min: str = Field(description="The earliest date.")
    max: str = Field(description="The most recent date.")

    @field_validator("type")
    def validate_prop_type(cls, v: str) -> str:
        assert v == "DATE_TIME", "Property type must be 'DATE_TIME'."
        return v

    @property
    def is_enum(self) -> bool:
        """Whether the object contains a valid enum."""
        return False


class Neo4jStructuredSchemaRelationship(BaseModel):
    start: str = Field(description="The start node label.")
    type: str = Field(description="The relationship type.")
    end: str = Field(description="The end node label.")


class Neo4jStructuredSchema(BaseModel):
    """
    The Structured Schema of a Neo4j Graph.
    The output from `Neo4jGraph(enhanced_schema=True).structured_schema` found in the `langchain_neo4j` Python library should map to this object.
    """

    node_props: Dict[
        str,
        List[
            Neo4jStructuredSchemaPropertyString
            | Neo4jStructuredSchemaPropertyNumber
            | Neo4jStructuredSchemaPropertyList
            | Neo4jStructuredSchemaPropertyDateTime
        ],
    ] = Field(
        description="A Python Dictionary with node labels as keys and a list of properties as values."
    )
    rel_props: Dict[
        str,
        List[
            Neo4jStructuredSchemaPropertyString
            | Neo4jStructuredSchemaPropertyNumber
            | Neo4jStructuredSchemaPropertyList
            | Neo4jStructuredSchemaPropertyDateTime
        ],
    ] = Field(
        description="A Python Dictionary with relationship types as keys and a list of properties as values."
    )
    relationships: List[Neo4jStructuredSchemaRelationship] = Field(
        description="A list of relationships."
    )
    metadata: Dict[str, Any] = Field(
        description="Metadata about the database.", default=dict()
    )

    def get_node_labels(self) -> List[str]:
        """
        A list of node labels in the database.

        Returns
        -------
        List[str]
            The node labels.
        """

        return list(self.node_props.keys())

    def get_relationship_types(self) -> List[str]:
        """
        A list of relationship types in the database.

        Returns
        -------
        List[str]
            The relationship types.
        """

        return [x.type for x in self.relationships]

    def get_node_properties_enum(self) -> Dict[str, Set[str]]:
        """
        A Python dictionary with node labels as keys and enums of property names as values.

        Returns
        -------
        Dict[str, Set[str]]
            The Python dictionary.
        """
        return {
            label: {p.property for p in prop_list}
            for label, prop_list in self.node_props.items()
        }

    def get_relationship_properties_enum(self) -> Dict[str, Set[str]]:
        """
        A Python dictionary with relationship types as keys and enums of property names as values.

        Returns
        -------
        Dict[str, Set[str]]
            The Python dictionary.
        """
        return {
            rel_type: {p.property for p in prop_list}
            for rel_type, prop_list in self.rel_props.items()
        }

    def get_node_property_values_enum(self) -> Dict[str, Dict[str, Set[str]]]:
        """
        A Python dictionary with node labels as parent keys, property names as child keys and a set of possible property values as the values.

        Returns
        -------
        Dict[str, Dict[str, Set[str]]]
            A dictionary like:
            {
            node_label_1: {
                prop_1: {val_1, val_2, val_3},
                ...
                },
            ...
            }
        """
        return {
            label: {
                p.property: p.get_property_values_enum()
                for p in prop_list
                if isinstance(p, Neo4jStructuredSchemaPropertyString) and p.is_enum
            }
            for label, prop_list in self.node_props.items()
        }

    def get_relationship_property_values_enum(self) -> Dict[str, Dict[str, Set[str]]]:
        """
        A Python dictionary with relationship types as parent keys, property names as child keys and a set of possible property values as the values.

        Returns
        -------
        Dict[str, Dict[str, Set[str]]]
            A dictionary like:
            {
            rel_type_1: {
                prop_1: {val_1, val_2, val_3},
                ...
                },
            ...
            }
        """

        return {
            rel_type: {
                p.property: p.get_property_values_enum()
                for p in prop_list
                if isinstance(p, Neo4jStructuredSchemaPropertyString) and p.is_enum
            }
            for rel_type, prop_list in self.node_props.items()
        }

    def get_node_property_values_range(
        self,
    ) -> Dict[str, Dict[str, Neo4jStructuredSchemaPropertyNumber]]:
        """
        A Python dictionary with node labels as parent keys, property names as child keys and `Neo4jStructuredSchemaPropertyNumber` objects as the values.

        Returns
        -------
        Dict[str, Dict[str, Neo4jStructuredSchemaPropertyNumber]]
            A dictionary like:
            {
            node_label_1: {
                prop_1: Neo4jStructuredSchemaPropertyNumber(...),
                ...
                },
            ...
            }
        """
        return {
            label: {
                p.property: p
                for p in prop_list
                if isinstance(p, Neo4jStructuredSchemaPropertyNumber)
            }
            for label, prop_list in self.node_props.items()
        }

    def get_relationship_property_values_range(
        self,
    ) -> Dict[str, Dict[str, Neo4jStructuredSchemaPropertyNumber]]:
        """
        A Python dictionary with relationship types as parent keys, property names as child keys and `Neo4jStructuredSchemaPropertyNumber` objects as the values.

        Returns
        -------
        Dict[str, Dict[str, Neo4jStructuredSchemaPropertyNumber]]
            A dictionary like:
            {
            rel_type_1: {
                prop_1: Neo4jStructuredSchemaPropertyNumber(...),
                ...
                },
            ...
            }
        """
        return {
            rel_type: {
                p.property: p
                for p in prop_list
                if isinstance(p, Neo4jStructuredSchemaPropertyNumber)
            }
            for rel_type, prop_list in self.node_props.items()
        }


class CypherValidationTask(BaseModel):
    labels_or_types: Optional[str] = Field(
        description="The extracted node labels or relationship types pattern. May be None if only a variable is provided.",
        examples=["NodeA", "NodeA&!NodeB", "REL_A|REL_B"],
        default=None,
    )
    operator: str = Field(description="The operator used to check the property value.")
    property_name: str = Field(
        description="The property name in the extracted node or relationship instance."
    )
    property_value: Any = Field(
        description="The property value declared in the extracted node or relationship instance."
    )
    property_type: Optional[str] = Field(
        description="The property type found in the schema. This may be assigned in a later step and is allowed to be None.",
        default=None,
    )

    @property
    def parsed_labels_or_types(self) -> List[str]:
        """Parse labels or types in cases with & / | and !."""

        if self.labels_or_types is None:
            return list()

        if "&" in self.labels_or_types:
            parsed = [lbl.strip() for lbl in self.labels_or_types.split("&")]
        elif "|" in self.labels_or_types:
            parsed = [lbl.strip() for lbl in self.labels_or_types.split("|")]
        elif ":" in self.labels_or_types:
            parsed = [lbl.strip() for lbl in self.labels_or_types.split(":")]
        else:
            parsed = [self.labels_or_types]

        parsed_final = [lbl for lbl in parsed if not lbl.startswith("!")]

        return parsed_final
