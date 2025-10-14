from typing import Any, Dict, Generator, List, Set

import yaml
from tqdm import tqdm


def read_cypher_examples_from_yaml_file(
    file_path: str,
    header_key: str = "queries",
    question_key: str = "question",
    cypher_key: str = "cql",
) -> List[Dict[str, str]]:
    with open(file_path) as f:
        try:
            queries = yaml.safe_load(f)[header_key]
        except yaml.YAMLError as exc:
            print(exc)
    return [
        {
            "question": q[question_key],
            "cql": q[cypher_key],
        }
        for q in queries
    ]


def remove_preexisting_nodes_from_ingest_tasks(
    ingest_tasks: List[Dict[str, str]], existing_node_questions: Set[str]
) -> List[Dict[str, str]]:
    return [x for x in ingest_tasks if x.get("question") not in existing_node_questions]


def batch_data(data: List[Any], batch_size: int = 10) -> Generator[Any, Any, Any]:
    """Yield successive batches of size `batch_size` from the input list."""
    for i in tqdm(range(0, len(data), batch_size)):
        if i + batch_size < len(data):
            yield data[i : i + batch_size]
        else:
            yield data[i:]
