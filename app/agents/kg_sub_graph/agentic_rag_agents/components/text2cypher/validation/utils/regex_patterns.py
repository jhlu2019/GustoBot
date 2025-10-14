"""
This code is sourced from https://github.com/langchain-ai/langchain-neo4j/blob/main/libs/neo4j/langchain_neo4j/chains/graph_qa/cypher_utils.py
"""

import regex as re


def get_property_pattern() -> re.Pattern:
    """Should be run on an entire captured Node or Relationship pattern."""
    return re.compile(r"\{.+?\}")


def get_node_variable_pattern() -> re.Pattern:
    """Should be run on an entire captured Node pattern."""
    return re.compile(r"^\(([a-zA-Z\_\d]*)(?:[\s]{0,1}[:\{])")


def get_relationship_variable_pattern() -> re.Pattern:
    """Should be run on an entire captured Relationship pattern."""
    return re.compile(r"^([\w\d]*):?")


def get_relationship_pattern() -> re.Pattern:
    """Capture a Relationship without direction."""
    return re.compile(r"-\[([\w\:\{\s\"\'\}\,\|\&]+)\]-")


def get_node_pattern() -> re.Pattern:
    """Capture a Node."""
    return re.compile(r"(\([\w\:\{\s\"\'\}\,\|\&]+\))")


def get_node_label_pattern() -> re.Pattern:
    """Should be run on an entire captured Node pattern."""
    return re.compile(r"\([^:\{]*:\`?([a-zA-Z\_\d\s\|\&]*)\`?[\s\_\{\)]")


def get_variable_operator_property_pattern(variable: str) -> re.Pattern:
    """
    Should be run on an entire Cypher Statement. The variable parameter must be gathered in a prior step.

    Parameters
    ----------
    variable : str
        The variable of interest.

    Returns
    -------
    re.Pattern
        The regex pattern.
    """
    return (
        re.escape(variable)
        + r"\.(?P<property_name>[^\s]*)\s(?P<operator>contains|CONTAINS|[><=]{0,2}|starts with|STARTS WITH|ends with|ENDS WITH)\s\"?\'?(?P<property_value>[\w\s]+\"|[\d]+)\"?\'?"
    )


def get_path_pattern() -> re.Pattern:
    return re.compile(
        r"(\([^\,\(\)]*?(\{.+\})?[^\,\(\)]*?\))(<?-)(\[.*?\])?(->?)(\([^\,\(\)]*?(\{.+\})?[^\,\(\)]*?\))"
    )


def get_node_relationship_node_pattern() -> re.Pattern:
    return re.compile(
        r"(\()+(?P<left_node>[^()]*?)\)(?P<relation>.*?)\((?P<right_node>[^()]*?)(\))+"
    )


def get_relationship_type_pattern() -> re.Pattern:
    return re.compile(r":([\w\|\&\:]+?)[\]\s\{]+")
