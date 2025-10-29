"""
This file contains Cypher validators that may be used in the Text2Cypher validation node.
"""

from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Union

from langchain_core.runnables.base import Runnable
from langchain_neo4j import Neo4jGraph
from langchain_neo4j.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema
from neo4j.exceptions import CypherSyntaxError

from ....components.text2cypher.validation.models import ValidateCypherOutput
from ....constants import WRITE_CLAUSES
from ...utils.utils import retrieve_and_parse_schema_from_graph_for_prompts
from .models import (
    CypherValidationTask,
    Neo4jStructuredSchema,
    Neo4jStructuredSchemaPropertyNumber,
)
from .utils.cypher_extractors import (
    extract_entities_for_validation,
)

# parse_labels_or_types,
from .utils.utils import update_task_list_with_property_type


def validate_cypher_query_syntax(graph: Neo4jGraph, cypher_statement: str) -> List[str]:
    """
    Validate the Cypher statement syntax by running an EXPLAIN query.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    List[str]
        If the statement contains invalid syntax, return an error message in a list
    """
    errors = list()
    try:
        graph.query(f"EXPLAIN {cypher_statement}")
    except CypherSyntaxError as e:
        errors.append(str(e.message))
    return errors


def correct_cypher_query_relationship_direction(
    graph: Neo4jGraph, cypher_statement: str
) -> str:
    """
    Correct Relationship directions in the Cypher statement with LangChain's `CypherQueryCorrector`.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    str
        The Cypher statement with corrected Relationship directions.
    """
    # Cypher query corrector is experimental
    corrector_schema = [
        Schema(el["start"], el["type"], el["end"])
        for el in graph.structured_schema.get("relationships", list())
    ]
    cypher_query_corrector = CypherQueryCorrector(corrector_schema)

    corrected_cypher: str = cypher_query_corrector(cypher_statement)

    return corrected_cypher


async def validate_cypher_query_with_llm(
    validate_cypher_chain: Runnable[Dict[str, Any], Any],
    question: str,
    graph: Neo4jGraph,
    cypher_statement: str,
) -> Dict[str, List[str]]:
    """
    Validate the Cypher statement with an LLM.
    Use declared LLM to find Node and Property pairs to validate.
    Validate Node and Property pairs against the Neo4j graph.

    Parameters
    ----------
    validate_cypher_chain : RunnableSerializable
        The LangChain LLM to perform processing.
    question : str
        The question associated with the Cypher statement.
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    Dict[str, List[str]]
        A Python dictionary with keys `errors` and `mapping_errors`, each with a list of found errors.
    """

    errors: List[str] = []
    mapping_errors: List[str] = []

    llm_output: ValidateCypherOutput = await validate_cypher_chain.ainvoke(
        {
            "question": question,
            "schema": retrieve_and_parse_schema_from_graph_for_prompts(graph),
            "cypher": cypher_statement,
        }
    )
    if llm_output.errors:
        errors.extend(llm_output.errors)
    if llm_output.filters:
        for filter in llm_output.filters:
            # Do mapping only for string values
            if (
                not [
                    prop
                    for prop in graph.structured_schema["node_props"][filter.node_label]
                    if prop["property"] == filter.property_key
                ][0]["type"]
                == "STRING"
            ):
                continue
            mapping = graph.query(
                f"MATCH (n:{filter.node_label}) WHERE toLower(n.`{filter.property_key}`) = toLower($value) RETURN 'yes' LIMIT 1",
                {"value": filter.property_value},
            )
            if not mapping:
                mapping_error = f"Missing value mapping for {filter.node_label} on property {filter.property_key} with value {filter.property_value}"
                mapping_errors.append(mapping_error)
    return {"errors": errors, "mapping_errors": mapping_errors}


def validate_cypher_query_with_schema(
    graph: Neo4jGraph, cypher_statement: str
) -> List[str]:
    """
    Validate the provided Cypher statement using the schema retrieved from the graph.
    This will ensure the existance of names nodes, relationships and properties.
    This will validate property values with enums and number ranges, if available.
    This method does not use an LLM.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher to be validated.

    Returns
    -------
    List[str]
        A list of any found errors.
    """

    schema: Neo4jStructuredSchema = Neo4jStructuredSchema.model_validate(
        graph.get_structured_schema
    )
    nodes_and_rels = extract_entities_for_validation(cypher_statement=cypher_statement)

    node_tasks = update_task_list_with_property_type(
        nodes_and_rels.get("nodes", list()), schema, "node"
    )
    rel_tasks = update_task_list_with_property_type(
        nodes_and_rels.get("relationships", list()), schema, "rel"
    )

    errors: List[str] = list()

    node_prop_name_enum_tasks = node_tasks
    node_prop_val_enum_tasks = [n for n in node_tasks if n.property_type == "STRING"]
    node_prop_val_range_tasks = [
        n
        for n in node_tasks
        if (n.property_type == "INTEGER" or n.property_type == "FLOAT")
    ]

    rel_prop_name_enum_tasks = rel_tasks
    rel_prop_val_enum_tasks = [n for n in rel_tasks if n.property_type == "STRING"]
    rel_prop_val_range_tasks = [
        n
        for n in rel_tasks
        if (n.property_type == "INTEGER" or n.property_type == "FLOAT")
    ]

    errors.extend(
        _validate_node_property_names_with_enum(schema, node_prop_name_enum_tasks)
    )
    errors.extend(
        _validate_node_property_values_with_enum(schema, node_prop_val_enum_tasks)
    )
    errors.extend(
        _validate_node_property_values_with_range(schema, node_prop_val_range_tasks)
    )

    errors.extend(
        _validate_relationship_property_names_with_enum(
            schema, rel_prop_name_enum_tasks
        )
    )
    errors.extend(
        _validate_relationship_property_values_with_enum(
            schema, rel_prop_val_enum_tasks
        )
    )
    errors.extend(
        _validate_relationship_property_values_with_range(
            schema, rel_prop_val_range_tasks
        )
    )

    return errors


def _validate_node_property_values_with_enum(
    structure_graph_schema: Neo4jStructuredSchema, tasks: List[CypherValidationTask]
) -> List[str]:
    prop_values_enum = structure_graph_schema.get_node_property_values_enum()

    errors = list()

    for t in tasks:
        labels = t.parsed_labels_or_types

        prop_val_validation_error = _validate_property_value_with_enum(
            enum_dict=prop_values_enum,
            labels_or_types=labels,
            node_or_rel="Node",
            property_name=t.property_name,
            property_value=t.property_value,
        )
        if prop_val_validation_error:
            errors.append(prop_val_validation_error)

    return errors


def _validate_node_property_names_with_enum(
    structure_graph_schema: Neo4jStructuredSchema, tasks: List[CypherValidationTask]
) -> List[str]:
    prop_enum = structure_graph_schema.get_node_properties_enum()

    errors = list()

    for t in tasks:
        labels = t.parsed_labels_or_types

        prop_validation_error = _validate_property_with_enum(
            enum_dict=prop_enum,
            labels_or_types=labels,
            node_or_rel="Node",
            property_name=t.property_name,
        )

        if prop_validation_error:
            errors.append(prop_validation_error)
    return errors


def _validate_relationship_property_names_with_enum(
    structure_graph_schema: Neo4jStructuredSchema, tasks: List[CypherValidationTask]
) -> List[str]:
    prop_enum = structure_graph_schema.get_relationship_properties_enum()

    errors = list()

    for t in tasks:
        rel_types = t.parsed_labels_or_types

        prop_validation_error = _validate_property_with_enum(
            enum_dict=prop_enum,
            labels_or_types=rel_types,
            node_or_rel="Relationship",
            property_name=t.property_name,
        )

        if prop_validation_error:
            errors.append(prop_validation_error)
    return errors


def _validate_relationship_property_values_with_enum(
    structure_graph_schema: Neo4jStructuredSchema, tasks: List[CypherValidationTask]
) -> List[str]:
    prop_values_enum = structure_graph_schema.get_relationship_property_values_enum()

    errors = list()

    for t in tasks:
        rel_types = t.parsed_labels_or_types
        prop_val_validation_error = _validate_property_value_with_enum(
            enum_dict=prop_values_enum,
            labels_or_types=rel_types,
            node_or_rel="Relationship",
            property_name=t.property_name,
            property_value=t.property_value,
        )
        if prop_val_validation_error:
            errors.append(prop_val_validation_error)

    return errors


def _validate_node_property_values_with_range(
    structure_graph_schema: Neo4jStructuredSchema,
    tasks: List[CypherValidationTask],
) -> List[str]:
    prop_values_range = structure_graph_schema.get_node_property_values_range()

    errors = list()

    for t in tasks:
        rel_types = t.parsed_labels_or_types
        prop_val_validation_error = _validate_property_value_with_range(
            enum_dict=prop_values_range,
            labels_or_types=rel_types,
            node_or_rel="Node",
            property_name=t.property_name,
            property_value=t.property_value,
        )
        if prop_val_validation_error:
            errors.append(prop_val_validation_error)

    return errors


def _validate_relationship_property_values_with_range(
    structure_graph_schema: Neo4jStructuredSchema,
    tasks: List[CypherValidationTask],
) -> List[str]:
    prop_values_range = structure_graph_schema.get_relationship_property_values_range()

    errors = list()

    for t in tasks:
        rel_types = t.parsed_labels_or_types
        prop_val_validation_error = _validate_property_value_with_range(
            enum_dict=prop_values_range,
            labels_or_types=rel_types,
            node_or_rel="Relationship",
            property_name=t.property_name,
            property_value=t.property_value,
        )
        if prop_val_validation_error:
            errors.append(prop_val_validation_error)

    return errors


def _validate_property_value_with_enum(
    enum_dict: Dict[str, Dict[str, Set[str]]],
    labels_or_types: List[str],
    property_name: str,
    node_or_rel: str,
    property_value: str,
    and_or: Optional[Literal["and", "or"]] = None,
) -> Optional[str]:
    """Validate that a property value is found in the enum generated from the graph schema."""

    assert node_or_rel in {
        "Node",
        "Relationship",
    }, f"Invalid `node_or_rel`: {node_or_rel}"

    if and_or is None and len(labels_or_types) > 1:
        raise ValueError(
            f"Invalid combination of `labels_or_types` and `and_or`: {labels_or_types} | {and_or}"
        )

    # track labels or types that are invalid
    # compare the number of invalid to the number tested to determine if valid
    invalid_labels_or_types = list()

    for lt in labels_or_types:
        props = enum_dict.get(lt)
        if props is None:
            # return None
            continue
        enum = props.get(property_name)
        if enum is None:
            # return None
            continue
        if property_value not in enum:
            invalid_labels_or_types.append(lt)

    if and_or is None and len(invalid_labels_or_types) > 0:  # single label or type
        return f"{node_or_rel} {labels_or_types} with property {property_name} = {property_value} not found in graph database."
    elif (
        and_or == "and"
        and 0 < len(invalid_labels_or_types)
        and len(invalid_labels_or_types) <= len(labels_or_types)
    ):
        return f"{node_or_rel}(s) {invalid_labels_or_types} with property {property_name} = {property_value} not found in graph database."
    elif and_or == "or" and len(invalid_labels_or_types) == len(labels_or_types):
        return f"None of {node_or_rel}s {labels_or_types} have property {property_name} = {property_value} in graph database."

    else:
        return None


def _validate_property_value_with_range(
    enum_dict: Dict[str, Dict[str, Neo4jStructuredSchemaPropertyNumber]],
    labels_or_types: List[str],
    property_name: str,
    node_or_rel: Literal["Node", "Relationship"],
    property_value: Union[int, float],
    and_or: Optional[Literal["and", "or"]] = None,
) -> Optional[str]:
    """Validate that a property value is found within the range generated from the graph schema."""

    assert node_or_rel in {
        "Node",
        "Relationship",
    }, f"Invalid `node_or_rel`: {node_or_rel}"

    # track labels or types that are invalid
    # compare the number of invalid to the number tested to determine to determine if valid
    invalid_labels_or_types: List[Tuple[str, Neo4jStructuredSchemaPropertyNumber]] = (
        list()
    )
    error_message_invalid_labels_or_types: List[str] = list()

    for lt in labels_or_types:
        props = enum_dict.get(lt)
        if props is None:
            # return None
            continue
        r = props.get(property_name)

        if r is None:
            # return None
            continue
        if float(property_value) < r.min or float(property_value) > r.max:
            invalid_labels_or_types.append((lt, r))

    for e in invalid_labels_or_types:
        if len(e) == 2:
            e_lt: str = e[0]  # the label or type
            e_prop: Neo4jStructuredSchemaPropertyNumber = e[1]
            error_message_invalid_labels_or_types.append(
                f"{e_lt} with property {e_prop.property} range {e_prop.min} to {e_prop.max}"
            )

    if and_or is None and len(invalid_labels_or_types) > 0:  # single label or type
        example_lt, example_prop = invalid_labels_or_types[0]
        return f"{node_or_rel} {example_lt} has property {property_name} = {property_value} which is out of range {example_prop.min} to {example_prop.max} in graph database."
    elif (
        and_or == "and"
        and 0 < len(invalid_labels_or_types)
        and len(invalid_labels_or_types) <= len(labels_or_types)
    ):
        return f"{node_or_rel}(s) {', '.join(error_message_invalid_labels_or_types)} have property {property_name} = {property_value} which is out of range in graph database."
    elif and_or == "or" and len(invalid_labels_or_types) == len(labels_or_types):
        return f"All of {node_or_rel}s {', '.join(error_message_invalid_labels_or_types)} have property {property_name} = {property_value} which is out of range in graph database."

    else:
        return None


def _validate_property_with_enum(
    enum_dict: Dict[str, Set[str]],
    labels_or_types: List[str],
    property_name: str,
    node_or_rel: Literal["Node", "Relationship"],
    and_or: Optional[Literal["and", "or"]] = None,
) -> Optional[str]:
    """Validate that a property name is found in the enum generated from the graph schema."""
    assert node_or_rel in {
        "Node",
        "Relationship",
    }, f"Invalid `node_or_rel`: {node_or_rel}"

    if and_or is None and len(labels_or_types) > 1:
        raise ValueError(
            f"Invalid combination of `labels_or_types` and `and_or`: {labels_or_types} | {and_or}"
        )

    # track labels or types that are invalid
    # compare the number of invalid to the number tested to determine to determine if valid
    invalid_labels_or_types = list()

    for lt in labels_or_types:
        enum = enum_dict.get(lt)

        if enum is None:
            # return None
            continue
        if property_name not in enum:
            invalid_labels_or_types.append(lt)

    if and_or is None and len(invalid_labels_or_types) > 0:  # single label or type
        return f"{node_or_rel} {labels_or_types} does not have the property {property_name} in the graph database."
    elif (
        and_or == "and"
        and 0 < len(invalid_labels_or_types)
        and len(invalid_labels_or_types) <= len(labels_or_types)
    ):
        return f"{node_or_rel}(s) {invalid_labels_or_types} do(es) not have the property {property_name} in the graph database."
    elif and_or == "or" and len(invalid_labels_or_types) == len(labels_or_types):
        return f"None of {node_or_rel}s {labels_or_types} have the property {property_name} in the graph database."

    else:
        return None


def validate_no_writes_in_cypher_query(cypher_statement: str) -> List[str]:
    """
    Validate whether the provided Cypher contains any write clauses.

    Parameters
    ----------
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    List[str]
        A list of any found errors.
    """
    errors: List[str] = list()

    for wc in WRITE_CLAUSES:
        if wc in cypher_statement.upper():
            errors.append(f"Cypher contains write clause: {wc}")

    return errors
