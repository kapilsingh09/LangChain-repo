from collections.abc import Mapping, Sequence
from typing import Any

from pymongo import AsyncMongoClient, UpdateOne

from src.config.config import MONGODB_DATABASE, MONGODB_URI


_client = AsyncMongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000,
)
_repositories = _client[MONGODB_DATABASE]["github_repositories"]


async def upsert_github_repositories(
    repositories: Sequence[Mapping[str, Any]],
) -> dict[str, int]:
    if not repositories:
        return {"inserted": 0, "updated": 0, "matched": 0}

    operations = []
    for repository in repositories:
        source_id = repository.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise ValueError("Each GitHub repository must have a source_id.")

        operations.append(
            UpdateOne(
                {"source_id": source_id},
                {"$set": dict(repository)},
                upsert=True,
            )
        )

    await _repositories.create_index("source_id", unique=True)
    result = await _repositories.bulk_write(operations, ordered=False)

    return {
        "inserted": result.upserted_count,
        "updated": result.modified_count,
        "matched": result.matched_count,
    }


async def remove_github_repository(source_id: str) -> bool:
    result = await _repositories.delete_one({"source_id": source_id})
    return result.deleted_count == 1
