def get_cypher_query_node_graph_schema() -> str:
    # 以 "- CypherQuery" 开始的整个段落，直到 "Relationship properties" 或 "- " 为止
    return r"^(- \*\*CypherQuery\*\*[\s\S]+?)(^Relationship properties|- \*)"
