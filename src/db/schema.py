"""The schema for the database."""

from lancedb.pydantic import Vector, LanceModel, List


class Chunk(LanceModel):
    chunk_id: str
    text: str
    summary: str = ""
    # starttime and endtime are in the format "%Y-%m-%d, %H:%M:%S"
    starttime: str
    endtime: str
    source_chunk_ids: List[str] = []
    embedding: Vector(dim=768)  # 384


class Page(LanceModel):
    url: str
    type: str  # one of team, sendungen, aktionen
    schedule: str = ""
    team_members: List[str] = []
    date: str = ""
    title: str
    summary: str = ""
    full_text: str = ""
    embedding: Vector(dim=768)  # 384
