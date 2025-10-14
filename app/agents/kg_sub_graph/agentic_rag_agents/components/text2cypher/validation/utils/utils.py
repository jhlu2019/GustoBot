from typing import List, Literal

from ..models import CypherValidationTask, Neo4jStructuredSchema

# from .cypher_extractors import parse_labels_or_types


def update_task_list_with_property_type(
    tasks: List[CypherValidationTask],
    structure_graph_schema: Neo4jStructuredSchema,
    node_or_rel: Literal["node", "rel"],
) -> List[CypherValidationTask]:
    """Assign property types to each entry in the task list."""

    if node_or_rel == "node":
        schema = structure_graph_schema.node_props
    else:
        schema = structure_graph_schema.rel_props

    # if node_or_rel == "node":
    #     label_or_type = "labels"
    # else:
    #     label_or_type = "rel_types"

    for task in tasks:
        # labels_or_types = parse_labels_or_types(task.get(label_or_type, None))
        labels_or_types = task.parsed_labels_or_types
        found_types = set()

        for lt in labels_or_types:
            name_type_map = {d.property: d.type for d in schema.get(lt, list())}
            found_types.add(name_type_map.get(task.property_name))

        if len(found_types) > 1:
            print(
                f"More than 1 type was found for {task.labels_or_types} and property {task.property_name}"
            )
        elif not len(found_types):
            print(
                f"No type was found for {task.labels_or_types} and property {task.property_name}"
            )

        if len(found_types) > 0:
            t = list(found_types)[0]
            task.property_type = t

    return tasks
