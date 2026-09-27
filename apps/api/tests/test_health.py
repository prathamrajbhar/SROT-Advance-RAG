from httpx import AsyncClient


async def test_health_reports_healthy_dependencies(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["services"]["postgres"]["status"] == "healthy"


async def test_readiness_probe_is_available_under_api_prefix(client: AsyncClient) -> None:
    response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


async def test_health_response_carries_a_trace_id(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.headers.get("X-Trace-Id")


async def test_openapi_schema_is_served(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "SROT"
    assert "/api/v1/health" in schema["paths"]
    assert "/api/v1/ready" in schema["paths"]
