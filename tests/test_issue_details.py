"""Tests for the issue details functionality in the MCP YouTrack server."""

import pytest
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any, Optional

from mcp_youtrack.mcp_server import (
    get_issue_details, 
    get_issue_custom_fields,
    get_issue_comments,
    IssueDetailResponse,
    CustomFieldResponse,
    CommentResponse,
    IssueCustomFieldType
)


@pytest.fixture
def mock_youtrack_client():
    """Create a mock YouTrack client for testing."""
    with patch("mcp_youtrack.mcp_server.youtrack_client") as mock_client:
        yield mock_client


def test_get_issue_details_success(mock_youtrack_client):
    """Test successful retrieval of issue details."""
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
    mock_issue.resolved = "2023-01-03T12:00:00Z"
    mock_issue.reporter.name = "Test User"
    mock_issue.reporter.login = "testuser"
    mock_issue.updater.name = "Update User"
    mock_issue.updater.login = "updateuser"
    mock_issue.comments_count = 5
    
    # Mock custom fields
    mock_field = MagicMock()
    mock_field.id = "field-123"
    mock_field.name = "Priority"
    mock_field.type = IssueCustomFieldType.SINGLE_ENUM
    mock_field.value.name = "High"
    mock_field.value.id = "priority-high"
    mock_issue.custom_fields = [mock_field]
    
    # Mock tags
    mock_tag = MagicMock()
    mock_tag.name = "bug"
    mock_tag.id = "tag-bug"
    mock_issue.tags = [mock_tag]
    
    # Mock links
    mock_youtrack_client.get_issue_links.return_value = []
    
    mock_youtrack_client.get_issue.return_value = mock_issue
    
    # Execute
    result = get_issue_details("issue-123")
    
    # Verify
    assert result is not None
    assert result.id == "issue-123"
    assert result.id_readable == "PROJ-123"
    assert result.summary == "Test issue"
    assert result.description == "Test description"
    assert result.wikified_description == "<p>Test wikified description</p>"
    assert result.project["name"] == "Test Project"
    assert result.created == "2023-01-01T12:00:00Z"
    assert result.updated == "2023-01-02T12:00:00Z"
    assert result.resolved == "2023-01-03T12:00:00Z"
    assert result.reporter["name"] == "Test User"
    assert result.updater["name"] == "Update User"
    assert result.comments_count == 5
    assert len(result.tags) == 1
    assert result.tags[0]["name"] == "bug"
    assert len(result.custom_fields) == 1
    assert result.custom_fields[0]["name"] == "Priority"
    assert result.custom_fields[0]["value"]["name"] == "High"
    
    mock_youtrack_client.get_issue.assert_called_once_with(issue_id="issue-123")


def test_get_issue_details_client_not_initialized(mock_youtrack_client):
    """Test get_issue_details when client is not initialized."""
    # Setup mock
    mock_youtrack_client.__bool__.return_value = False
    
    # Execute
    result = get_issue_details("issue-123")
    
    # Verify
    assert result is None


def test_get_issue_details_not_found(mock_youtrack_client):
    """Test get_issue_details when issue is not found."""
    # Setup mock
    mock_youtrack_client.get_issue.return_value = None
    
    # Execute
    result = get_issue_details("issue-123")
    
    # Verify
    assert result is None


def test_get_issue_details_exception(mock_youtrack_client):
    """Test get_issue_details when an exception occurs."""
    # Setup mock
    mock_youtrack_client.get_issue.side_effect = Exception("Test error")
    
    # Execute
    result = get_issue_details("issue-123")
    
    # Verify
    assert result is None


def test_get_issue_custom_fields_success(mock_youtrack_client):
    """Test successful retrieval of issue custom fields."""
    # Setup mock
    mock_field1 = MagicMock()
    mock_field1.id = "field-123"
    mock_field1.name = "Priority"
    mock_field1.type = IssueCustomFieldType.SINGLE_ENUM
    mock_field1.value.name = "High"
    mock_field1.value.id = "priority-high"
    
    mock_field2 = MagicMock()
    mock_field2.id = "field-456"
    mock_field2.name = "Assignee"
    mock_field2.type = IssueCustomFieldType.SINGLE_USER
    mock_field2.value.name = "Test User"
    mock_field2.value.login = "testuser"
    
    # Patch the IssueCustomFieldType enum values
    with patch("mcp_youtrack.mcp_server.IssueCustomFieldType") as mock_field_type:
        mock_field_type.SINGLE_ENUM = "enum"
        mock_field_type.MULTI_ENUM = "enum[]"
        mock_field_type.SINGLE_USER = "user"
        mock_field_type.MULTI_USER = "user[]"
        mock_field_type.DATE = "date"
        mock_field_type.PERIOD = "period"
        
        mock_youtrack_client.get_issue_custom_fields.return_value = [mock_field1, mock_field2]
        
        # Execute
        result = get_issue_custom_fields("issue-123")
        
        # Verify
        assert len(result) == 2
        assert result[0].id == "field-123"
        assert result[0].name == "Priority"
        assert result[0].type == "enum"
        assert result[0].value["name"] == "High"
        assert result[1].id == "field-456"
        assert result[1].name == "Assignee"
        assert result[1].type == "user"
        assert result[1].value["name"] == "Test User"
        
        mock_youtrack_client.get_issue_custom_fields.assert_called_once_with(issue_id="issue-123")


def test_get_issue_custom_fields_client_not_initialized(mock_youtrack_client):
    """Test get_issue_custom_fields when client is not initialized."""
    # Setup mock
    mock_youtrack_client.__bool__.return_value = False
    
    # Execute
    result = get_issue_custom_fields("issue-123")
    
    # Verify
    assert result == []


def test_get_issue_custom_fields_not_found(mock_youtrack_client):
    """Test get_issue_custom_fields when no fields are found."""
    # Setup mock
    mock_youtrack_client.get_issue_custom_fields.return_value = []
    
    # Execute
    result = get_issue_custom_fields("issue-123")
    
    # Verify
    assert result == []


def test_get_issue_custom_fields_exception(mock_youtrack_client):
    """Test get_issue_custom_fields when an exception occurs."""
    # Setup mock
    mock_youtrack_client.get_issue_custom_fields.side_effect = Exception("Test error")
    
    # Execute
    result = get_issue_custom_fields("issue-123")
    
    # Verify
    assert result == []


def test_get_issue_comments_success(mock_youtrack_client):
    """Test successful retrieval of issue comments."""
    # Setup mock
    mock_comment1 = MagicMock()
    mock_comment1.id = "comment-123"
    mock_comment1.text = "Test comment 1"
    mock_comment1.text_preview = "Test comment 1 preview"
    mock_comment1.created = "2023-01-01T12:00:00Z"
    mock_comment1.updated = "2023-01-02T12:00:00Z"
    mock_comment1.author.name = "Test User"
    mock_comment1.author.login = "testuser"
    mock_comment1.deleted = False
    
    mock_comment2 = MagicMock()
    mock_comment2.id = "comment-456"
    mock_comment2.text = "Test comment 2"
    mock_comment2.text_preview = "Test comment 2 preview"
    mock_comment2.created = "2023-01-03T12:00:00Z"
    mock_comment2.author.name = "Another User"
    mock_comment2.author.login = "anotheruser"
    
    mock_youtrack_client.get_issue_comments.return_value = [mock_comment1, mock_comment2]
    
    # Execute
    result = get_issue_comments("issue-123")
    
    # Verify
    assert len(result) == 2
    assert result[0].id == "comment-123"
    assert result[0].text == "Test comment 1"
    assert result[0].text_preview == "Test comment 1 preview"
    assert result[0].created == "2023-01-01T12:00:00Z"
    assert result[0].updated == "2023-01-02T12:00:00Z"
    assert result[0].author["name"] == "Test User"
    assert result[0].deleted is False
    assert result[1].id == "comment-456"
    assert result[1].text == "Test comment 2"
    assert result[1].author["name"] == "Another User"
    
    mock_youtrack_client.get_issue_comments.assert_called_once_with(issue_id="issue-123")


def test_get_issue_comments_client_not_initialized(mock_youtrack_client):
    """Test get_issue_comments when client is not initialized."""
    # Setup mock
    mock_youtrack_client.__bool__.return_value = False
    
    # Execute
    result = get_issue_comments("issue-123")
    
    # Verify
    assert result == []


def test_get_issue_comments_not_found(mock_youtrack_client):
    """Test get_issue_comments when no comments are found."""
    # Setup mock
    mock_youtrack_client.get_issue_comments.return_value = []
    
    # Execute
    result = get_issue_comments("issue-123")
    
    # Verify
    assert result == []


def test_get_issue_comments_exception(mock_youtrack_client):
    """Test get_issue_comments when an exception occurs."""
    # Setup mock
    mock_youtrack_client.get_issue_comments.side_effect = Exception("Test error")
    
    # Execute
    result = get_issue_comments("issue-123")
    
    # Verify
    assert result == []
