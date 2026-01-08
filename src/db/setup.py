"""Script to create the database and tables."""

from utils import get_db
from schema import Chunk


def setup_database(uri: str = "data/sample-lancedb"):
    """
    Set up the LanceDB database and create the 'live' table with the specified schema.

    Args:
        uri (str): The URI for the LanceDB database.
    """
    print(f"Setting up database at {uri}...")
    # Connect to the LanceDB database
    db = get_db(uri)

    # Create the table with the specified schema
    table = db.create_table("live", schema=Chunk, mode="overwrite")
    print(f"Created table 'live' in database at {uri}")


if __name__ == "__main__":
    setup_database()
