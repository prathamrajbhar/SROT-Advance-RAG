import asyncio
from typing import Any, Dict, List, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as rest_models
from core.config import get_settings

settings = get_settings()

_qdrant_clients: Dict[int, AsyncQdrantClient] = {}


def get_qdrant() -> AsyncQdrantClient:
    try:
        loop = asyncio.get_running_loop()
        loop_id = id(loop)
    except RuntimeError:
        loop_id = 0

    client = _qdrant_clients.get(loop_id)
    if client is None:
        client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            check_compatibility=False,
        )
        _qdrant_clients[loop_id] = client
    return client


def get_collection_name(project_id: str) -> str:
    clean_id = str(project_id).replace("-", "_")
    return f"proj_{clean_id}"


async def ensure_project_collection(
    project_id: str, vector_dim: int = 1024
) -> str:
    import asyncio
    client = get_qdrant()
    collection_name = get_collection_name(project_id)
    
    exists = await client.collection_exists(collection_name=collection_name)
    if exists:
        try:
            coll_info = await client.get_collection(collection_name=collection_name)
            current_dim = coll_info.config.params.vectors.size if hasattr(coll_info.config.params.vectors, "size") else None
            if current_dim and current_dim != vector_dim:
                await client.delete_collection(collection_name=collection_name)
                exists = False
        except Exception:
            pass

    if not exists:
        for attempt in range(4):
            try:
                await client.create_collection(
                    collection_name=collection_name,
                    vectors_config=rest_models.VectorParams(
                        size=vector_dim,
                        distance=rest_models.Distance.COSINE,
                    ),
                )
                break
            except Exception as e:
                # If another concurrent task created it, verify existence
                if await client.collection_exists(collection_name=collection_name):
                    break
                if attempt == 3:
                    raise
                await asyncio.sleep(0.5)
    return collection_name



async def delete_project_collection(project_id: str) -> None:
    client = get_qdrant()
    collection_name = get_collection_name(project_id)
    try:
        await client.delete_collection(collection_name=collection_name)
    except Exception:
        pass


async def upsert_chunks(
    project_id: str, points: List[rest_models.PointStruct]
) -> None:
    client = get_qdrant()
    collection_name = get_collection_name(project_id)
    await client.upsert(
        collection_name=collection_name,
        points=points,
    )


async def delete_document_points(project_id: str, document_id: str) -> None:
    client = get_qdrant()
    collection_name = get_collection_name(project_id)
    try:
        await client.delete(
            collection_name=collection_name,
            points_selector=rest_models.FilterSelector(
                filter=rest_models.Filter(
                    must=[
                        rest_models.FieldCondition(
                            key="document_id",
                            match=rest_models.MatchValue(value=str(document_id)),
                        )
                    ]
                )
            ),
        )
    except Exception:
        pass


async def search_vectors(
    project_id: str,
    query_vector: List[float],
    limit: int = 40,
    score_threshold: Optional[float] = None,
) -> List[rest_models.ScoredPoint]:
    client = get_qdrant()
    collection_name = get_collection_name(project_id)
    try:
        response = await client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=rest_models.Filter(
                must=[
                    rest_models.FieldCondition(
                        key="project_id",
                        match=rest_models.MatchValue(value=str(project_id)),
                    )
                ]
            ),
        )
        return response.points
    except Exception:
        return []
