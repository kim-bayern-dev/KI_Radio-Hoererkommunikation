import lancedb
import pyarrow as pa


def create_db(uri: str):
    """
    Creates a LanceDB database at the specified URI.

    This function initializes a LanceDB database at the given URI.
    If the database already exists, it will not overwrite it.
    """
    try:
        db = lancedb.connect(uri)
        return db
    except lancedb.LanceDBError as e:
        raise ConnectionError(
            f"Failed to create or connect to the database at {uri}: {e}"
        )
    except Exception as e:
        raise RuntimeError(
            f"An unexpected error occurred while creating or connecting to the database: {e}"
        )


def create_table(db, table_name: str, schema: pa.Schema):
    """
    Creates a table in the LanceDB database.

    This function creates a table with the specified name and schema in the connected LanceDB database.
    If the table already exists, it will not overwrite it.
    """
    try:
        table = db.create_table(table_name, schema=schema, mode="overwrite")
        return table
    except lancedb.LanceDBError as e:
        raise ValueError(f"Failed to create table {table_name}: {e}")
    except Exception as e:
        raise RuntimeError(
            f"An unexpected error occurred while creating the table: {e}"
        )


def get_db(uri: str):
    """
    Returns the database connection.

    This function connects to the LanceDB database at the specified URI.
    """
    try:
        db = lancedb.connect(uri)
        return db
    except lancedb.LanceDBError as e:
        raise ConnectionError(f"Failed to connect to the database at {uri}: {e}")
    except Exception as e:
        raise RuntimeError(
            f"An unexpected error occurred while connecting to the database: {e}"
        )


def get_table(db, table_name: str) -> pa.Table:
    """
    Returns the table from the database.

    This function retrieves the specified table from the connected LanceDB database.
    """
    table = db.open_table(table_name)
    if table is None:
        raise ValueError(f"Table {table_name} not found in the database.")
    return table
