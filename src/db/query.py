"""This module contains the code to query data from the vector database."""

import pyarrow as pa
from typing import Dict, List
from langchain.schema.runnable import RunnableLambda

from db import _get_embedding_model
from db.utils import get_db, get_table
from config_utils import AppConfig


def get_retriever(config: AppConfig, table_name: str = "live") -> RunnableLambda:
    """
    Create a retriever for the database usable with Langchain.
    """
    # Connect to the LanceDB database
    db = get_db(config.data.db_uri)
    # Get the table
    table = get_table(db, table_name)

    def _my_retrieval(input: Dict) -> List[Dict]:
        result = query_db(
            embedding_model=config.embeddings.model,
            embedding_base_url=config.embeddings.base_url,
            table=table,
            query=input["semantic_query"],
            starttime=input["starttime"],
            endtime=input["endtime"],
            num_results=input["num_results"],
        )
        return result

    retriever = RunnableLambda(_my_retrieval)
    return retriever


def query_website_db(
    db_uri: str,
    embedding_model: str,
    embedding_base_url: str,
    query: str,
    type: str,
    top_n: int = 1,
) -> List[Dict]:
    """
    Query the database table for the top N results based on the query string.

    Args:
        db_uri (str): The URI of the LanceDB database.
        embedding_model (str): The embedding model to use for the query.
        embedding_base_url (str): The base URL for the embedding model service.
        query (str): The query string.
        type (str): The type of the page to query.
        top_n (int): The number of top results to return.

    Returns:
        List[Dict]: A list of dictionaries containing the top N results.
    """
    table = get_table(get_db(db_uri), "website")
    # Convert the query string to an embedding (use a prompt for usage with mixedbread)
    embedding_model = _get_embedding_model(embedding_model, embedding_base_url)
    query_embed = embedding_model.embed_query(
        f"{query}"  # Represent this sentence for searching relevant passages:
    )

    # Perform the query
    result = (
        table.search(query_embed)
        .where(f"type == '{type}'")
        .select(
            ["title", "summary", "full_text", "url", "schedule", "date", "team_members"]
        )
        .limit(top_n)
        .to_list()
    )
    return result


def query_db(
    embedding_model: str,
    embedding_base_url: str,
    table: pa.table,
    query: str,
    starttime: str = None,
    endtime: str = None,
    num_results: int = 5,
):
    """
    Query the database table for the top N results based on the query string.

    Args:
        embedding_model (str): The embedding model to use for the query.
        embedding_base_url (str): The base URL for the embedding model service.
        table (pa.Table): The database table to query.
        query (str): The query string.
        starttime (str): The start time for the query (optional).
        endtime (str): The end time for the query (optional).
        num_results (int): The number of top results to return.

    Returns:
        List[Dict]: A list of dictionaries containing the top N results.
    """
    # Convert the query string to an embedding (use a prompt for usage with mixedbread)
    embedding_model = _get_embedding_model(embedding_model, embedding_base_url)
    query_embed = embedding_model.embed_query(
        f"{query}"  # Represent this sentence for searching relevant passages:
    )

    # When starttime and endtime are the same search only for endtime
    if starttime == endtime:
        endtime = None
    # Perform the query
    if starttime and endtime:
        result = (
            table.search(query_embed)
            .where(f"starttime >= '{starttime}' AND endtime <= '{endtime}'")
            .select(["text", "chunk_id", "starttime", "endtime"])
            .limit(num_results)
            .to_list()
        )
    elif starttime:
        result = (
            table.search(query_embed)
            .where(f"starttime >= '{starttime}'")
            .select(["text", "chunk_id", "starttime", "endtime"])
            .limit(num_results)
            .to_list()
        )
    elif endtime:
        result = (
            table.search(query_embed)
            .where(f"endtime <= '{endtime}'")
            .select(["text", "chunk_id", "starttime", "endtime"])
            .limit(num_results)
            .to_list()
        )
    # if no time range is specified, return the top N results
    else:
        result = (
            table.search(query_embed)
            .select(["text", "chunk_id", "starttime", "endtime"])
            .limit(num_results)
            .to_list()
        )
    return result
