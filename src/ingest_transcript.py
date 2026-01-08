"""Entry point for the ingestion pipeline."""

import json, uuid
import click
from tqdm import tqdm
from loguru import logger

from db import _get_embedding_model
from db.utils import get_db, get_table
from config_utils import AppConfig


def connect_to_db_table(uri: str, table_name: str):
    """
    Connect to the LanceDB database and get the specified table.

    Args:
        uri (str): The URI for the LanceDB database.
        table_name (str): The name of the table to retrieve.

    Returns:
        lancedb.Table: The table from the database.
    """
    db = get_db(uri)
    return get_table(db, table_name)


def load_data_from_file(datapath: str):
    """
    Load data from a JSON file.

    Args:
        datapath (str): The path to the JSON file.

    Returns:
        list: The loaded data.
    """
    with open(datapath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def embed_data(data: list, embedding_model):
    """
    Embed the text data using the specified embedding model.

    Args:
        data (list): The list of data dictionaries containing 'text' keys.
        embedding_model: The embedding model to use for embedding the text.

    Returns:
        list: The data with embedded vectors added.
    """
    for d in tqdm(data):
        d["embedding"] = embedding_model.embed_query(d["text"])
    return data


def ingest_data(table, data: list):
    """
    Add the embedded data to the specified table.

    Args:
        table (lancedb.Table): The table to which data will be added.
        data (list): The list of data dictionaries with embedded vectors.

    Returns:
        None
    """
    table.add(data)


@click.command()
@click.option("--config", help="Path to the configuration file.", required=True)
def main(config: str):
    """
    Main function to run the ingestion pipeline.

    Args:
        config (str): Path to the config file.
    """
    table_name = "live"
    datapath = "data/2025_06_10-hit_radio_kesselbach_chunks.json"
    playlist_path = "data/2025_06_10_hit_radio_kesselbach_playlist.json"

    logger.info("Starting ingestion pipeline...")
    config: AppConfig = AppConfig.from_yaml(path=config)
    embedding_model = _get_embedding_model(
        embedding_model=config.embeddings.model, base_url=config.embeddings.base_url
    )

    # Connect to the LanceDB database and get the table
    table = connect_to_db_table(config.data.db_uri, table_name)

    # Load the live radio data
    logger.info("Loading data...")
    data = load_data_from_file(datapath)
    if playlist_path:
        logger.info("Loading playlist data...")
        playlist_data = load_data_from_file(playlist_path)
        # set an unique chunk_id for each item
        for item in playlist_data:
            item["chunk_id"] = str(uuid.uuid4())
        # merge playlist data into the main data
        data.extend(playlist_data)
    logger.info(f"Loaded {len(data)} chunks from {datapath}.")

    # Embed the data
    logger.info("Embedding data...")
    data = embed_data(data, embedding_model)
    logger.info("Embedding done.")

    # Add data to the table
    logger.info("Adding data to the table...")
    ingest_data(table, data)
    logger.info("Data added to the table.")
    logger.info("Ingestion done.")


if __name__ == "__main__":
    main()
