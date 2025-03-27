"""Tests for the MCP YouTrack server tools."""

import pytest
from unittest.mock import patch, MagicMock
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from mcp_youtrack.mcp_server import get_issues, comment_issue, update_field, IssueResponse, remove_issue_tags


class MockIssue(BaseModel):
    id: Optional[str] = "issue-123"
    id_readable: Optional[str] = "PROJ-123"
    summary: Optional[str] = "Test issue"
    description: Optional[str] = "Test description"
    wikified_description: Optional[str] = "<p>Test wikified description</p>"
    project: Optional[Dict[str, Any]] = {"id": "project-1", "name": "Test Project"}
    created: Optional[str] = "2023-01-01T12:00:00Z"
    updated: Optional[str] = "2023-01-02T12:00:00Z"
    reporter: Optional[Dict[str, Any]] = {"name": "Test User", "login": "testuser"}


class MockComment(BaseModel):
    id: Optional[str] = "comment-123"
    text: Optional[str] = "Test comment"
    created: Optional[str] = "2023-01-01T12:00:00Z"
    author: Optional[Dict[str, Any]] = {"name": "Test User", "login": "testuser"}


class MockField(BaseModel):
    id: Optional[str] = "field-123"
    name: Optional[str] = "Priority"
    value: Optional[Any] = "High"


class MockTag(BaseModel):
    id: Optional[str] = "tag-123"
    name: Optional[str] = "bug"


@pytest.fixture
def mock_youtrack_client():
    """Create a mock YouTrack client for testing."""
    with patch("mcp_youtrack.mcp_server.youtrack_client") as mock_client:
        yield mock_client


def test_get_issues_success(mock_youtrack_client):
    """Test successful retrieval of issues."""
    # Setup mock
    mock_issue = MagicMock()
    mock_issue.id = "issue-123"
    mock_issue.id_readable = "PROJ-123"
    mock_issue.summary = "Test issue"
    mock_issue.description = "Test description"
    mock_issue.wikified_description = "<p>Test wikified description</p>"
    mock_issue.project.id = "project-1"
    mock_issue.project.name = "Test Project"
    mock_issue.created = "2023-01-01T12:00:00Z"
    mock_issue.updated = "2023-01-02T12:00:00Z"
    mock_issue.reporter.name = "Test User"
    mock_issue.reporter.login = "testuser"
    
    mock_youtrack_client.get_issues.return_value = [mock_issue]
    
    # Execute
    result = get_issues("project: Test")
    
    # Verify
    assert len(result) == 1
    assert result[0].id == "issue-123"
    assert result[0].id_readable == "PROJ-123"
    assert result[0].summary == "Test issue"
    assert result[0].project["name"] == "Test Project"
    mock_youtrack_client.get_issues.assert_called_once_with(query="project: Test")


def test_get_issues_client_not_initialized(mock_youtrack_client):
    """Test get_issues when client is not initialized."""
    # Setup mock
    mock_youtrack_client.return_value = None
    
    # Execute
    result = get_issues("project: Test")
    
    # Verify
    assert result == []


def test_get_issues_exception(mock_youtrack_client):
    """Test get_issues when an exception occurs."""
    # Setup mock
    mock_youtrack_client.get_issues.side_effect = Exception("Test error")
    
    # Execute
    result = get_issues("project: Test")
    
    # Verify
    assert result == []


def test_comment_issue_success(mock_youtrack_client):
    """Test successful comment creation."""
    # Setup mock
    mock_comment = MagicMock()
    mock_comment.id = "comment-123"
    mock_comment.text = "Test comment"
    mock_comment.created = "2023-01-01T12:00:00Z"
    mock_comment.author.name = "Test User"
    mock_comment.author.login = "testuser"
    
    mock_youtrack_client.create_issue_comment.return_value = mock_comment
    
    # Execute
    result = comment_issue("issue-123", "Test comment")
    
    # Verify
    assert result["success"] is True
    assert result["comment_id"] == "comment-123"
    assert result["text"] == "Test comment"
    mock_youtrack_client.create_issue_comment.assert_called_once()


def test_comment_issue_client_not_initialized(mock_youtrack_client):
    """Test comment_issue when client is not initialized."""
    # Setup mock
    mock_youtrack_client.__bool__.return_value = False
    
    # Execute
    result = comment_issue("issue-123", "Test comment")
    
    # Verify
    assert result["success"] is False
    assert "error" in result


def test_comment_issue_exception(mock_youtrack_client):
    """Test comment_issue when an exception occurs."""
    # Setup mock
    mock_youtrack_client.create_issue_comment.side_effect = Exception("Test error")
    
    # Execute
    result = comment_issue("issue-123", "Test comment")
    
    # Verify
    assert result["success"] is False
    assert result["error"] == "Test error"


def test_update_field_success(mock_youtrack_client):
    """Test successful field update."""
    # Setup mocks
    mock_field = MagicMock()
    mock_field.id = "field-123"
    mock_field.name = "Priority"
    mock_field.value = "High"
    
    mock_youtrack_client.get_issue_custom_fields.return_value = [mock_field]
    mock_youtrack_client.update_issue_custom_field.return_value = mock_field
    
    # Execute
    result = update_field("issue-123", "field-123", "High")
    
    # Verify
    assert result["success"] is True
    assert result["field_id"] == "field-123"
    assert result["field_name"] == "Priority"
    mock_youtrack_client.update_issue_custom_field.assert_called_once()


def test_update_field_not_found(mock_youtrack_client):
    """Test update_field when field is not found."""
    # Setup mock
    mock_youtrack_client.get_issue_custom_fields.return_value = []
    
    # Execute
    result = update_field("issue-123", "field-123", "High")
    
    # Verify
    assert result["success"] is False
    assert "not found" in result["error"]


def test_update_field_client_not_initialized(mock_youtrack_client):
    """Test update_field when client is not initialized."""
    # Setup mock
    mock_youtrack_client.__bool__.return_value = False
    
    # Execute
    result = update_field("issue-123", "field-123", "High")
    
    # Verify
    assert result["success"] is False
    assert "error" in result


def test_update_field_exception(mock_youtrack_client):
    """Test update_field when an exception occurs."""
    # Setup mock
    mock_field = MagicMock()
    mock_field.id = "field-123"
    
    mock_youtrack_client.get_issue_custom_fields.return_value = [mock_field]
    mock_youtrack_client.update_issue_custom_field.side_effect = Exception("Test error")
    
    # Execute
    result = update_field("issue-123", "field-123", "High")
    
    # Verify
    assert result["success"] is False
    assert result["error"] == "Test error"


def test_remove_issue_tags_success(mock_youtrack_client):
    """Test successful tag removal."""
    # Setup mocks
    mock_tag1 = MagicMock()
    mock_tag1.id = "tag-123"
    mock_tag1.name = "bug"
    
    mock_tag2 = MagicMock()
    mock_tag2.id = "tag-456"
    mock_tag2.name = "feature"
    
    mock_issue = MagicMock()
    mock_issue.tags = [mock_tag1, mock_tag2]
    
    mock_youtrack_client.get_issue.return_value = mock_issue
    
    # Execute
    result = remove_issue_tags("issue-123", ["bug"])
    
    # Verify
    assert result["success"] is True
    assert result["issue_id"] == "issue-123"
    assert "bug" in result["removed_tags"]
    assert len(result["removed_tags"]) == 1
    mock_youtrack_client.remove_issue_tag.assert_called_once_with(issue_id="issue-123", tag_id="tag-123")


def test_remove_issue_tags_nonexistent_tag(mock_youtrack_client):
    """Test removing a tag that doesn't exist on the issue."""
    # Setup mocks
    mock_tag = MagicMock()
    mock_tag.id = "tag-123"
    mock_tag.name = "bug"
    
    mock_issue = MagicMock()
    mock_issue.tags = [mock_tag]
    
    mock_youtrack_client.get_issue.return_value = mock_issue
    
    # Execute
    result = remove_issue_tags("issue-123", ["feature"])
    
    # Verify
    assert result["success"] is True
    assert result["issue_id"] == "issue-123"
    assert len(result["removed_tags"]) == 0
    assert "feature" in result["skipped_tags"]
    mock_youtrack_client.remove_issue_tag.assert_not_called()


def test_remove_issue_tags_no_tags(mock_youtrack_client):
    """Test removing tags from an issue with no tags."""
    # Setup mocks
    mock_issue = MagicMock()
    mock_issue.tags = []
    
    mock_youtrack_client.get_issue.return_value = mock_issue
    
    # Execute
    result = remove_issue_tags("issue-123", ["bug"])
    
    # Verify
    assert result["success"] is True
    assert result["issue_id"] == "issue-123"
    assert len(result["removed_tags"]) == 0
    assert "bug" in result["skipped_tags"]
    mock_youtrack_client.remove_issue_tag.assert_not_called()


def test_remove_issue_tags_client_not_initialized(mock_youtrack_client):
    """Test remove_issue_tags when client is not initialized."""
    # Setup mock
    mock_youtrack_client.__bool__.return_value = False
    
    # Execute
    result = remove_issue_tags("issue-123", ["bug"])
    
    # Verify
    assert result["success"] is False
    assert "error" in result


def test_remove_issue_tags_exception(mock_youtrack_client):
    """Test remove_issue_tags when an exception occurs."""
    # Setup mock
    mock_youtrack_client.get_issue.side_effect = Exception("Test error")
    
    # Execute
    result = remove_issue_tags("issue-123", ["bug"])
    
    # Verify
    assert result["success"] is False
    assert result["error"] == "Test error"
