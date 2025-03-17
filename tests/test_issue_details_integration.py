"""Integration tests for the issue details functionality in the MCP YouTrack server."""

import pytest
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Any, Optional

from mcp_youtrack.mcp_server import (
    get_issues,
    get_issue_details,
    get_issue_custom_fields,
    get_issue_comments,
    IssueResponse,
    IssueDetailResponse,
    CustomFieldResponse,
    CommentResponse
)


def test_fetch_issue_details():
    """Test fetching details for a specific issue.
    
    This test verifies that the MCP server can successfully connect to YouTrack
    and retrieve detailed information about a specific issue.
    """
    # First, get a list of issues to find a valid issue ID
    query = 'project: Analytics'
    issues = get_issues(query)
    
    # Verify that we got a response
    assert isinstance(issues, list), "Expected a list of issues"
    
    # Log the number of issues found
    print(f"Found {len(issues)} Analytics issues")
    
    # If we found issues, get details for the first one
    if issues:
        issue = issues[0]
        issue_id = issue.id
        
        # Get issue details
        details = get_issue_details(issue_id)
        
        # Verify that we got a response
        assert details is not None, f"Failed to get details for issue {issue_id}"
        assert isinstance(details, IssueDetailResponse), "Expected IssueDetailResponse object"
        
        # Verify the issue details
        assert details.id == issue_id, "Issue ID should match"
        assert details.summary, "Issue should have a summary"
        
        # Log the issue details
        print(f"Successfully fetched details for issue {details.id_readable}: {details.summary}")
        
        # Verify custom fields if available
        if details.custom_fields:
            print(f"Issue has {len(details.custom_fields)} custom fields")
            for field in details.custom_fields:
                assert field.get("id"), "Custom field should have an ID"
                assert field.get("name"), "Custom field should have a name"
                print(f"  - {field.get('name')}: {field.get('value')}")
        
        # Verify tags if available
        if details.tags:
            print(f"Issue has {len(details.tags)} tags")
            for tag in details.tags:
                assert tag.get("name"), "Tag should have a name"
                print(f"  - {tag.get('name')}")


def test_fetch_issue_custom_fields():
    """Test fetching custom fields for a specific issue.
    
    This test verifies that the MCP server can successfully connect to YouTrack
    and retrieve custom fields for a specific issue.
    """
    # First, get a list of issues to find a valid issue ID
    query = 'project: Analytics'
    issues = get_issues(query)
    
    # Verify that we got a response
    assert isinstance(issues, list), "Expected a list of issues"
    
    # If we found issues, get custom fields for the first one
    if issues:
        issue = issues[0]
        issue_id = issue.id
        
        # Get custom fields
        custom_fields = get_issue_custom_fields(issue_id)
        
        # Verify that we got a response
        assert isinstance(custom_fields, list), "Expected a list of custom fields"
        
        # Log the number of custom fields found
        print(f"Found {len(custom_fields)} custom fields for issue {issue.id_readable}")
        
        # If we found custom fields, verify they have the expected structure
        if custom_fields:
            for field in custom_fields:
                assert isinstance(field, CustomFieldResponse), "Expected CustomFieldResponse object"
                assert field.id, "Custom field should have an ID"
                assert field.name, "Custom field should have a name"
                
                # Log the custom field
                print(f"  - {field.name}: {field.value}")


def test_fetch_issue_comments():
    """Test fetching comments for a specific issue.
    
    This test verifies that the MCP server can successfully connect to YouTrack
    and retrieve comments for a specific issue.
    """
    # First, get a list of issues with comments
    query = 'project: Analytics has: comments'
    issues = get_issues(query)
    
    # Verify that we got a response
    assert isinstance(issues, list), "Expected a list of issues"
    
    # Log the number of issues found
    print(f"Found {len(issues)} Analytics issues with comments")
    
    # If we found issues with comments, get comments for the first one
    if issues:
        issue = issues[0]
        issue_id = issue.id
        
        # Get comments
        comments = get_issue_comments(issue_id)
        
        # Verify that we got a response
        assert isinstance(comments, list), "Expected a list of comments"
        
        # Log the number of comments found
        print(f"Found {len(comments)} comments for issue {issue.id_readable}")
        
        # If we found comments, verify they have the expected structure
        if comments:
            for comment in comments:
                assert isinstance(comment, CommentResponse), "Expected CommentResponse object"
                assert comment.id, "Comment should have an ID"
                assert comment.text, "Comment should have text"
                
                # Log the comment
                print(f"  - Comment by {comment.author.get('name') if comment.author else 'Unknown'}: {comment.text[:50]}...")
