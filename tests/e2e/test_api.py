"""E2E 测试 —— 完整 HTTP 请求链路验证。"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    from doggy.server.bootstrap import app, setup_app
    setup_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealthEndpoints:
    async def test_healthz(self, client):
        resp = await client.get("/v1/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    async def test_readyz(self, client):
        resp = await client.get("/v1/readyz")
        assert resp.status_code in (200, 503)


class TestAdminAPI:
    async def test_list_policies(self, client):
        resp = await client.get("/v1/admin/policies")
        assert resp.status_code == 200
        assert "policies" in resp.json()

    async def test_list_plugins(self, client):
        resp = await client.get("/v1/admin/plugins")
        assert resp.status_code == 200
        assert "plugins" in resp.json()

    async def test_service_health(self, client):
        resp = await client.get("/v1/admin/health/services")
        assert resp.status_code == 200
        data = resp.json()
        assert data["gateway"] == "healthy"


class TestMetrics:
    async def test_metrics_endpoint(self, client):
        resp = await client.get("/v1/metrics")
        assert resp.status_code == 200
        text = resp.text
        assert "doggy_requests_total" in text
        assert "doggy_active_connections" in text
