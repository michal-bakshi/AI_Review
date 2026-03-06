"""Integration tests for FastAPI API routes using TestClient."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    """Provide a TestClient with the workflow dependency mocked out."""
    import main  # ensure app is importable

    return TestClient(main.app)


def test_health_check(client: TestClient) -> None:
    """GET /health should return 200 with status=healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch("app.api.routes.workflow")
def test_start_review_returns_thread_id(mock_workflow: MagicMock, client: TestClient) -> None:
    """POST /review/start should return thread_id, review_draft, and language."""
    mock_workflow.ainvoke = AsyncMock(
        return_value={"review_draft": "LGTM with minor issues", "language": "python"}
    )
    response = client.post("/review/start", json={"code": "def foo(): pass"})

    assert response.status_code == 200
    data = response.json()
    assert "thread_id" in data
    assert data["language"] == "python"
    assert "review_draft" in data


@patch("app.api.routes.workflow")
def test_start_review_rejects_empty_code(mock_workflow: MagicMock, client: TestClient) -> None:
    """POST /review/start should return 422 when code is an empty string."""
    response = client.post("/review/start", json={"code": ""})
    assert response.status_code == 422


@patch("app.api.routes.workflow")
def test_approve_review_returns_final_review(mock_workflow: MagicMock, client: TestClient) -> None:
    """POST /review/{id}/approve should return final_review on success."""
    mock_workflow.ainvoke = AsyncMock(
        return_value={"final_review": "Approved review text", "language": "python"}
    )
    response = client.post(
        "/review/some-thread-id/approve",
        json={"approved": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert "final_review" in data
    assert data["approved"] is True


@patch("app.api.routes.workflow")
def test_approve_review_with_feedback(mock_workflow: MagicMock, client: TestClient) -> None:
    """POST /review/{id}/approve with feedback should propagate feedback field."""
    mock_workflow.ainvoke = AsyncMock(
        return_value={"final_review": "Revised review", "language": "python"}
    )
    response = client.post(
        "/review/some-thread-id/approve",
        json={"approved": False, "feedback": "Please add more detail on line 3"},
    )
    assert response.status_code == 200
    assert response.json()["approved"] is False
