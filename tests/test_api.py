import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import Mock

from main import app
from api.routes import get_feedback_service
from domain.models import Inbox, InboxView, User, Message
from service.feedback_service import InboxNotFoundException

client = TestClient(app)

mock_service = Mock()
app.dependency_overrides[get_feedback_service] = lambda: mock_service

@pytest.fixture
def sample_inbox():
    """Helper to create a real Domain Inbox."""
    return Inbox(
        id="inbox_123",
        topic="Do you like tests?",
        owner_signature="owner#tripcode",
        requires_signature=True,
        expires_at=datetime.now() + timedelta(hours=24)
    )

def test_read_inbox_as_owner(sample_inbox):
    # Setup: Service returns an Owner View (with messages)
    view = InboxView(
        inbox=sample_inbox, 
        messages=[Message(body="Hello!", timestamp=datetime.now(), signature="user#sig")]
    )
    mock_service.read_inbox.return_value = view
    mock_service.get_user_from_username_and_secret.return_value = User("admin", "secret")

    # Act
    response = client.get("/inboxes/inbox_123", headers={"x-username": "admin", "x-secret": "secret"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "Do you like tests?"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["body"] == "Hello!"

def test_read_inbox_as_public(sample_inbox):
    # Setup: Service returns a Public View (messages=None)
    view = InboxView(inbox=sample_inbox, messages=None)
    mock_service.read_inbox.return_value = view
    mock_service.get_user_from_username_and_secret.return_value = User(None, None)

    # Act
    response = client.get("/inboxes/inbox_123")

    # Assert
    assert response.status_code == 200
    data = response.json()
    # Pydantic should have used InboxPublicRead, so 'messages' should not be in the keys
    assert "messages" not in data
    assert data["topic"] == "Do you like tests?"

def test_create_inbox_success(sample_inbox):
    # Setup: Service returns the created inbox
    mock_service.create_inbox.return_value = InboxView(inbox=sample_inbox, messages=[])
    mock_service.get_user_from_username_and_secret.return_value = User("owner", "pass")

    # Act
    payload = {
        "topic": "New Inbox",
        "username": "owner",
        "secret": "pass",
        "requires_signature": True,
        "expires_in_hours": 12
    }
    response = client.post("/inboxes", json=payload)

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == "inbox_123"

def test_read_inbox_not_found():
    # Setup: Service raises our custom exception
    mock_service.read_inbox.side_effect = InboxNotFoundException()
    mock_service.get_user_from_username_and_secret.return_value = User(None, None)

    # Act
    response = client.get("/inboxes/non_existent")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Inbox not found"