"""Entry point for the ingestion pipeline."""

import json
import click
from tqdm import tqdm
from loguru import logger
from typing import List, Tuple

from db import _get_embedding_model
from db.schema import Page
from db.utils import get_db
from config_utils import AppConfig


def load_data_from_file(datapath: str) -> Tuple[List[dict], List[dict], List[dict]]:
    """
    Load data from a JSON file.

    Args:
        datapath (str): The path to the JSON file.

    Returns:
        tuple: A tuple containing the team, sendungen, and aktionen data.
    """
    with open(datapath, "r", encoding="utf-8") as f:
        data = json.load(f)

    team = data.pop("team")
    sendungen = data.pop("sendungen")
    aktionen = data.pop("aktionen")
    return team, sendungen, aktionen


def embed_data(
    team: List[dict],
    sendungen: List[dict],
    aktionen: List[dict],
    embedding_model,
    n_chars: int = 1500,
) -> Tuple[List[dict], List[dict], List[dict]]:
    """
    Embed the text data using the specified embedding model.

    Args:
        team (list): The list of team dictionaries.
        sendungen (list): The list of sendungen dictionaries.
        aktionen (list): The list of aktionen dictionaries.
        embedding_model: The embedding model to use for embedding the text.
        n_chars (int): The number of characters to consider for embedding.

    Returns:
        tuple: A tuple containing the embedded team, sendungen, and aktionen data.
    """
    for d in tqdm(team):
        d["embedding"] = embedding_model.embed_query(d["summary"][:n_chars])
        d["title"] = d["name"]
        del d["name"]
        d["schedule"] = ""
        d["team_members"] = []
        d["date"] = ""
        d["type"] = "team"

    for d in tqdm(sendungen):
        d["embedding"] = embedding_model.embed_query(d["summary"][:n_chars])
        d["date"] = ""
        d["team_members"] = [] if not d.get("team_members") else d["team_members"]
        d["schedule"] = d.get("schedule", "")
        d["type"] = "sendungen"

    for d in tqdm(aktionen):
        d["embedding"] = embedding_model.embed_query(d["summary"][:n_chars])
        d["schedule"] = ""
        d["team_members"] = [] if not d.get("team_members") else d["team_members"]
        d["date"] = "" if not d.get("date") else d["date"]
        d["type"] = "aktionen"

    return team, sendungen, aktionen


def ingest_data(team: List[dict], sendungen: List[dict], aktionen: List[dict], table):
    """
    Add the embedded data to the specified table.

    Args:
        team (list): The list of team dictionaries with embedded vectors.
        sendungen (list): The list of sendungen dictionaries with embedded vectors.
        aktionen (list): The list of aktionen dictionaries with embedded vectors.
        table (lancedb.Table): The table to which data will be added.
    """
    logger.info("Adding team data to the table...")
    table.add(team)
    logger.info("Team data added.")

    logger.info("Adding sendungen data to the table...")
    table.add(sendungen)
    logger.info("Sendungen data added.")

    logger.info("Adding aktionen data to the table...")
    table.add(aktionen)
    logger.info("Aktionen data added.")


@click.command()
@click.option("--config", help="Path to the configuration file.", required=True)
def main(config: str):
    """
    Main function to run the ingestion pipeline.

    Args:
        config (str): Path to the config file.
    """
    datapath = "data/2025-06-10-hit_radio_kesselbach_website.json"
    n_chars = 1500

    logger.info("Starting ingestion pipeline...")
    config: AppConfig = AppConfig.from_yaml(path=config)
    embedding_model = _get_embedding_model(
        embedding_model=config.embeddings.model, base_url=config.embeddings.base_url
    )

    # Connect to the LanceDB database and get the table
    db = get_db(config.data.db_uri)
    table = db.create_table("website", schema=Page, mode="overwrite")
    logger.info(f"Created table 'website' in database at {config.data.db_uri}")

    # Load the data from the JSON file
    team, sendungen, aktionen = load_data_from_file(datapath)

    # Embed the data
    logger.info("Embedding data...")
    team, sendungen, aktionen = embed_data(
        team, sendungen, aktionen, embedding_model, n_chars
    )
    logger.info("Embedding done.")

    # Add data to the table
    ingest_data(team, sendungen, aktionen, table)
    logger.info("Ingestion done.")


if __name__ == "__main__":
    main()
