import logging
from pathlib import Path

import pandas as pd



from graphrag.utils.api import (
    get_embedding_store,
    load_search_prompt,
)

from graphrag.config.load_config import load_config
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.embeddings import (
    community_full_content_embedding,
    entity_description_embedding,
    text_unit_text_embedding,
)

from graphrag.config.resolve_path import resolve_paths

from graphrag.index.create_pipeline_config import create_pipeline_config
from graphrag.query.factory import get_local_search_engine, get_basic_search_engine, get_global_search_engine, \
    get_drift_search_engine
from graphrag.query.indexer_adapters import read_indexer_entities, read_indexer_communities, read_indexer_reports, \
    read_indexer_text_units, read_indexer_relationships, read_indexer_covariates, read_indexer_report_embeddings
from graphrag.storage.factory import StorageFactory
from graphrag.utils.storage import load_table_from_storage, storage_has_table

from webserver.configs import settings

logger = logging.getLogger(__name__)


async def load_context(root: Path, data_dir: Path | None = None):
    config = load_config(root, Path("settings.yaml"))
    config.storage.base_dir = str(data_dir) if data_dir else config.storage.base_dir
    resolve_paths(config)

    dataframe_dict = await resolve_output_files(
        config=config,
        output_list=[
            "create_final_nodes",
            "create_final_community_reports",
            "create_final_text_units",
            "create_final_relationships",
            "create_final_entities",
            "create_final_communities",
        ],
        optional_list=[
            "create_final_covariates",
        ],
    )
    return config, dataframe_dict


async def resolve_output_files(config: GraphRagConfig, output_list: list[str], optional_list: list[str] | None = None,
                               ) -> dict[str, pd.DataFrame]:
    """Read indexing output files to a dataframe dict."""
    dataframe_dict = {}
    pipeline_config = create_pipeline_config(config)
    storage_config = pipeline_config.storage.model_dump()  # type: ignore

    
    storage_obj = StorageFactory().create_storage(
        storage_type=storage_config["type"], kwargs=storage_config
    )
    for name in output_list:
        df_value = await load_table_from_storage(name=name, storage=storage_obj)
        dataframe_dict[name] = df_value

    # for optional output files, set the dict entry to None instead of erroring out if it does not exist
    if optional_list:
        for optional_file in optional_list:
            file_exists = await storage_has_table(optional_file, storage_obj)
            if file_exists:
                df_value = await load_table_from_storage(name=optional_file, storage=storage_obj)
                dataframe_dict[optional_file] = df_value
            else:
                dataframe_dict[optional_file] = None

    return dataframe_dict


async def load_local_search_engine(config: GraphRagConfig, data: dict[str, pd.DataFrame]):
    vector_store_args = config.embeddings.vector_store
    logger.info(f"Vector Store Args: {vector_store_args}")  # type: ignore # noqa

    description_embedding_store = get_embedding_store(
        config_args=vector_store_args,  # type: ignore
        embedding_name=entity_description_embedding,
    )

    final_nodes = data["create_final_nodes"]
    final_entities = data['create_final_entities']
    community_level = settings.community_level
    final_covariates = data['create_final_covariates'] if data.get('create_final_covariates') is not None else []
    final_text_units: pd.DataFrame = data["create_final_text_units"]
    final_relationships: pd.DataFrame = data["create_final_relationships"]
    final_community_reports: pd.DataFrame = data["create_final_community_reports"]

    entities_ = read_indexer_entities(final_nodes, final_entities, community_level)
    covariates_ = read_indexer_covariates(final_covariates) if final_covariates else []
    prompt = load_search_prompt(config.root_dir, config.local_search.prompt)

    search_engine = get_local_search_engine(
        config=config,
        reports=read_indexer_reports(final_community_reports, final_nodes, community_level),
        text_units=read_indexer_text_units(final_text_units),
        entities=entities_,
        relationships=read_indexer_relationships(final_relationships),
        covariates={"claims": covariates_},
        description_embedding_store=description_embedding_store,  # type: ignore
        response_type=settings.response_type,
        system_prompt=prompt,
    )
    return search_engine


async def load_global_search_engine(config: GraphRagConfig, data: dict[str, pd.DataFrame]):
    final_nodes = data["create_final_nodes"]
    final_entities = data['create_final_entities']
    community_level = settings.community_level
    final_community_reports: pd.DataFrame = data["create_final_community_reports"]
    final_communities: pd.DataFrame = data["create_final_communities"]

    communities_ = read_indexer_communities(final_communities, final_nodes, final_community_reports)
    reports = read_indexer_reports(
        final_community_reports,
        final_nodes,
        community_level=community_level,
        dynamic_community_selection=settings.dynamic_community_selection,
    )
    entities_ = read_indexer_entities(final_nodes, final_entities, community_level=community_level)
    map_prompt = _load_search_prompt(config.root_dir, config.global_search.map_prompt)
    reduce_prompt = _load_search_prompt(
        config.root_dir, config.global_search.reduce_prompt
    )
    knowledge_prompt = _load_search_prompt(
        config.root_dir, config.global_search.knowledge_prompt
    )

    search_engine = get_global_search_engine(
        config,
        reports=reports,
        entities=entities_,
        communities=communities_,
        response_type="Multiple Paragraphs",
        dynamic_community_selection=settings.dynamic_community_selection,
        map_system_prompt=map_prompt,
        reduce_system_prompt=reduce_prompt,
        general_knowledge_inclusion_prompt=knowledge_prompt,
    )
    return search_engine


async def load_drift_search_engine(config: GraphRagConfig, data: dict[str, pd.DataFrame]):
    vector_store_args = config.embeddings.vector_store
    logger.info(f"Vector Store Args: {vector_store_args}")  # type: ignore # noqa

    description_embedding_store = _get_embedding_store(
        config_args=vector_store_args,  # type: ignore
        embedding_name=entity_description_embedding,
    )

    full_content_embedding_store = _get_embedding_store(
        config_args=vector_store_args,  # type: ignore
        embedding_name=community_full_content_embedding,
    )

    final_nodes = data["create_final_nodes"]
    final_entities = data['create_final_entities']
    community_level = settings.community_level
    final_text_units: pd.DataFrame = data["create_final_text_units"]
    final_relationships: pd.DataFrame = data["create_final_relationships"]
    final_community_reports: pd.DataFrame = data["create_final_community_reports"]

    entities_ = read_indexer_entities(final_nodes, final_entities, community_level)
    reports = read_indexer_reports(final_community_reports, final_nodes, community_level)
    read_indexer_report_embeddings(reports, full_content_embedding_store)
    prompt = _load_search_prompt(config.root_dir, config.drift_search.prompt)
    search_engine = get_drift_search_engine(
        config=config,
        reports=reports,
        text_units=read_indexer_text_units(final_text_units),
        entities=entities_,
        relationships=read_indexer_relationships(final_relationships),
        description_embedding_store=description_embedding_store,  # type: ignore
        local_system_prompt=prompt,
    )

    return search_engine


async def load_basic_search_engine(config: GraphRagConfig, data: dict[str, pd.DataFrame]):
    vector_store_args = config.embeddings.vector_store
    logger.info(f"Vector Store Args: {vector_store_args}")  # type: ignore # noqa

    description_embedding_store = _get_embedding_store(
        config_args=vector_store_args,  # type: ignore
        embedding_name=text_unit_text_embedding,
    )

    final_text_units: pd.DataFrame = data["create_final_text_units"]

    prompt = _load_search_prompt(config.root_dir, config.basic_search.prompt)

    search_engine = get_basic_search_engine(
        config=config,
        text_units=read_indexer_text_units(final_text_units),
        text_unit_embeddings=description_embedding_store,
        system_prompt=prompt,
    )

    return search_engine
