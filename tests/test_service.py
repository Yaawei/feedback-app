from unittest.mock import Mock
import pytest
from domain.models import User, Inbox
from service.feedback_service import FeedbackService, InboxNotFoundException


# 1. Setup Fixture
@pytest.fixture
def mock_repo():
    return Mock()  # Valid because Python assumes it has the methods we call


@pytest.fixture
def service(mock_repo):
    return FeedbackService(mock_repo)


# 2. Test Cases
def test_create_inbox_calls_save(service, mock_repo):
    user = User(username="test", secret="secret")

    # Act
    service.create_inbox("Topic", user, True, 24)

    # Assert
    mock_repo.save_new.assert_called_once()
    saved_inbox = mock_repo.save_new.call_args[0][0]
    assert saved_inbox.topic == "Topic"


def test_read_missing_inbox_raises_error(service, mock_repo):
    # Setup the mock to return None when get_by_id is called
    mock_repo.get_by_id.return_value = None
    user = User("anon", None)

    # Assert
    with pytest.raises(InboxNotFoundException):
        service.read_inbox("missing_id", user)