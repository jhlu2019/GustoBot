from typing import Any, Dict, List, Optional, Tuple

import regex as re

from ..models import CypherValidationTask
from .regex_patterns import (
    get_node_label_pattern,
    get_node_pattern,
    get_node_variable_pattern,
    get_property_pattern,
    get_relationship_pattern,
    get_relationship_type_pattern,
    get_relationship_variable_pattern,
    get_variable_operator_property_pattern,
)


def extract_entities_for_validation(
    cypher_statement: str,
) -> Dict[str, List[CypherValidationTask]]:
    nodes = _extract_nodes_and_properties_from_cypher_statement(cypher_statement)
    rels = _extract_relationships_and_properties_from_cypher_statement(cypher_statement)

    return {"nodes": nodes, "relationships": rels}


def _extract_nodes_and_properties_from_cypher_statement(
    cypher_statement: str,
) -> List[CypherValidationTask]:
    """
    Extract Node and Property pairs from the Cypher statement.

    Parameters
    ----------
    cypher_statement : str
        The statement.

    Returns
    -------
    List[CypherValidationTask]
        A List of CypherValidationTasks with keys `labels`, `operator`, `property_name` and `property_value`.
    """
    tasks = list()

    nodes = re.findall(get_node_pattern(), cypher_statement)
    used_variables = set()
    # find all variable assignments and process match clauses
    for n in nodes:
        variables = re.findall(get_node_variable_pattern(), n)
        labels = _find_all_node_labels(n)

        k = _parse_element_from_regex_result(regex_result=variables)
        label = labels[0].strip() if len(labels) > 0 else None
        match_props = re.findall(get_property_pattern(), n)
        match_props = _parse_element_from_regex_result(regex_result=match_props)
        # process ids in the MATCH clause
        if match_props is not None:
            match_props_parsed: List[Dict[str, Any]] = (
                process_match_clause_property_ids(match_props)
            )
            [
                e.update({"labels_or_types": label, "operator": "="})
                for e in match_props_parsed
            ]
            tasks.extend(match_props_parsed)

        # find and process property filters based on variables
        if k is not None and k not in used_variables:
            filters: List[Dict[str, Any]] = _find_all_filters(
                variable=k, cypher_statement=cypher_statement
            )
            [e.update({"labels_or_types": label}) for e in filters]
            tasks.extend(filters)

        used_variables.add(k)

    # validate all found tasks
    validated_tasks = [CypherValidationTask.model_validate(task) for task in tasks]
    return validated_tasks


def _extract_relationships_and_properties_from_cypher_statement(
    cypher_statement: str,
) -> List[CypherValidationTask]:
    """
    Extract Relationship and Property pairs from the Cypher statement.

    Parameters
    ----------
    cypher_statement : str
        The statement.

    Returns
    -------
    List[CypherValidationTask]
        A List of CypherValidationTasks with keys `rel_types`, `operator`, `property_name` and `property_value`.
    """
    tasks = list()

    rels = re.findall(get_relationship_pattern(), cypher_statement)
    used_variables = set()

    # find all variable assignments and process match clauses
    for n in rels:
        variables = re.findall(get_relationship_variable_pattern(), n)
        rel_types = _find_all_relationship_types(n)

        rel_type = rel_types[0].strip() if len(rel_types) > 0 else None
        k = _parse_element_from_regex_result(regex_result=variables)

        match_props = re.findall(get_property_pattern(), n)
        match_props = _parse_element_from_regex_result(regex_result=match_props)
        # process ids in the MATCH clause
        if match_props is not None:
            match_props_parsed: List[Dict[str, Any]] = (
                process_match_clause_property_ids(match_props)
            )
            [
                e.update({"labels_or_types": rel_type, "operator": "="})
                for e in match_props_parsed
            ]
            tasks.extend(match_props_parsed)

        # find and process property filters based on variables
        if k is not None and k not in used_variables:
            filters: List[Dict[str, Any]] = _find_all_filters(
                variable=k, cypher_statement=cypher_statement
            )
            [e.update({"labels_or_types": rel_type}) for e in filters]
            tasks.extend(filters)
        used_variables.add(k)

    # validate all found tasks
    validated_tasks = [CypherValidationTask.model_validate(task) for task in tasks]

    return validated_tasks


def process_match_clause_property_ids(
    match_clause_section: str,
) -> List[Dict[str, Any]]:
    parts = match_clause_section.split(",")
    result = list()
    for part in parts:
        k_and_v = part.split(":")
        if len(k_and_v) == 2:
            k, v = k_and_v
        else:
            continue
        result.append(
            {
                "property_name": _process_prop_key(k),
                "property_value": _process_prop_val(v),
            }
        )
    return result


def _process_prop_key(prop: str) -> str:
    prop = prop.strip()
    return prop.strip("{")


def _process_prop_val(prop: str) -> str:
    prop = prop.strip()
    prop = prop.strip("}")
    prop = prop.replace('"', "")
    return prop.replace("'", "")


# def parse_labels_or_types(labels_str: Optional[str]) -> List[str]:
#     """Parse labels or types in cases with & / | and !."""

#     if labels_str is None:
#         return list()

#     if "&" in labels_str:
#         labels = [lbl.strip() for lbl in labels_str.split("&")]
#     elif "|" in labels_str:
#         labels = [lbl.strip() for lbl in labels_str.split("|")]
#     elif ":" in labels_str:
#         labels = [lbl.strip() for lbl in labels_str.split(":")]
#     else:
#         labels = [labels_str]

#     labels = [lbl for lbl in labels if not lbl.startswith("!")]

#     return labels


def _find_all_filters(variable: str, cypher_statement: str) -> List[Dict[str, Any]]:
    res: List[Tuple[str, str, Any]] = re.findall(
        get_variable_operator_property_pattern(variable=variable), cypher_statement
    )

    return [
        {
            "property_name": _process_prop_key(n[0]),
            "operator": n[1].strip(),
            "property_value": _process_prop_val(n[2]),
        }
        for n in res
    ]


def _find_all_node_labels(node: str) -> List[str]:
    return [n.strip() for n in re.findall(get_node_label_pattern(), node)]


def _find_all_relationship_types(relationship: str) -> List[str]:
    return [
        r.strip() for r in re.findall(get_relationship_type_pattern(), relationship)
    ]


def _parse_element_from_regex_result(regex_result: List[str]) -> Optional[str]:
    """The `regex_result` should be a single element list."""

    parsed = regex_result[0] if len(regex_result) > 0 else None
    if not parsed:
        return None
    else:
        return parsed
