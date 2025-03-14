"""Integration tests for the MCP YouTrack server tools."""

import pytest
from datetime import datetime, timedelta
import pytz
from typing import List

from mcp_youtrack.mcp_server import get_issues, IssueResponse


def test_fetch_an_issues_last_month():
    """Test fetching #AN issues created in the last month.
    
    This test verifies that the MCP server can successfully connect to YouTrack
    and retrieve #AN issues created in the last month.
    """
    # Calculate the date one month ago
    now = datetime.now(pytz.UTC)
    one_month_ago = now - timedelta(days=30)
    date_string = one_month_ago.strftime("%Y-%m-%d")
    
    # Construct the query to find #AN issues created in the last month
    query = f'project: Analytics created: {date_string} .. *'
    
    # Execute the query
    issues = get_issues(query)
    
    # Verify that we got a response
    assert isinstance(issues, list), "Expected a list of issues"
    
    # Log the number of issues found
    print(f"Found {len(issues)} Analytics issues created since {date_string}")
    
    # If we found issues, verify they have the expected structure
    if issues:
        for issue in issues:
            assert isinstance(issue, IssueResponse), "Expected IssueResponse object"
            assert issue.id, "Issue should have an ID"
            assert issue.id_readable, "Issue should have a readable ID"
            assert issue.summary, "Issue should have a summary"
            assert issue.id_readable.startswith("AN-"), f"Issue ID should start with AN-, got {issue.id_readable}"
            
            # Verify the creation date is within the last month
            if issue.created:
                created_date = datetime.fromisoformat(issue.created.replace('Z', '+00:00'))
                assert created_date >= one_month_ago, f"Issue {issue.id_readable} was created before the specified date range"
                assert created_date <= now, f"Issue {issue.id_readable} has a future creation date"


def test_fetch_an_issues_with_comments():
    """Test fetching #AN issues that have comments.
    
    This test verifies that the MCP server can successfully connect to YouTrack
    and retrieve #AN issues that have comments.
    """
    # Construct the query to find #AN issues with comments
    query = 'project: Analytics has: comments'
    
    # Execute the query
    issues = get_issues(query)
    
    # Verify that we got a response
    assert isinstance(issues, list), "Expected a list of issues"
    
    # Log the number of issues found
    print(f"Found {len(issues)} Analytics issues with comments")
    
    # If we found issues, verify they have the expected structure
    if issues:
        for issue in issues:
            assert isinstance(issue, IssueResponse), "Expected IssueResponse object"
            assert issue.id, "Issue should have an ID"
            assert issue.id_readable, "Issue should have a readable ID"
            assert issue.summary, "Issue should have a summary"
            assert issue.id_readable.startswith("AN-"), f"Issue ID should start with AN-, got {issue.id_readable}"


def test_fetch_an_issues_by_reporter():
    """Test fetching #AN issues created by a specific reporter.
    
    This test verifies that the MCP server can successfully connect to YouTrack
    and retrieve #AN issues created by a specific reporter.
    """
    # Construct the query to find #AN issues by reporter
    # Note: This assumes there's at least one issue with a reporter
    query = 'project: Analytics has: reporter'
    
    # Execute the query
    issues = get_issues(query)
    
    # Verify that we got a response
    assert isinstance(issues, list), "Expected a list of issues"
    
    # Log the number of issues found
    print(f"Found {len(issues)} Analytics issues with a reporter")
    
    # If we found issues with reporters, try to fetch issues by a specific reporter
    if issues and any(issue.reporter for issue in issues):
        # Get the first issue with a reporter
        issue_with_reporter = next((issue for issue in issues if issue.reporter), None)
        
        if issue_with_reporter and issue_with_reporter.reporter:
            reporter_login = issue_with_reporter.reporter.get('login')
            
            if reporter_login:
                # Fetch issues by this specific reporter
                reporter_query = f'project: Analytics reporter: {reporter_login}'
                reporter_issues = get_issues(reporter_query)
                
                # Verify the results
                assert isinstance(reporter_issues, list), "Expected a list of issues"
                print(f"Found {len(reporter_issues)} Analytics issues reported by {reporter_login}")
                
                # Verify all returned issues have the correct reporter
                for issue in reporter_issues:
                    assert issue.reporter, "Issue should have a reporter"
                    assert issue.reporter.get('login') == reporter_login, f"Issue reporter should be {reporter_login}"


def test_fetch_an_issues_with_tag_last_month():
    """Test fetching Analytics issues with a specific tag created in the last month.
    
    This test verifies that the MCP server can successfully connect to YouTrack
    and retrieve Analytics issues with a specific tag created in the last month.
    """
    # Calculate the date one month ago
    now = datetime.now(pytz.UTC)
    one_month_ago = now - timedelta(days=30)
    date_string = one_month_ago.strftime("%Y-%m-%d")
    
    # Try different tags that might be used in the Analytics project
    tags_to_try = ["#data", "#analytics", "#dashboard", "#report", "#metric"]
    
    for tag in tags_to_try:
        # Construct the query to find tagged issues created in the last month
        query = f'project: Analytics {tag} created: {date_string} .. *'
        
        # Execute the query
        issues = get_issues(query)
        
        # Verify that we got a response
        assert isinstance(issues, list), "Expected a list of issues"
        
        # Log the number of issues found
        print(f"Found {len(issues)} Analytics issues with tag {tag} created since {date_string}")
        
        # If we found issues, verify they have the expected structure and stop the loop
        if issues:
            for issue in issues:
                assert isinstance(issue, IssueResponse), "Expected IssueResponse object"
                assert issue.id, "Issue should have an ID"
                assert issue.id_readable, "Issue should have a readable ID"
                assert issue.summary, "Issue should have a summary"
                assert issue.id_readable.startswith("AN-"), f"Issue ID should start with AN-, got {issue.id_readable}"
                
                # Verify the creation date is within the last month
                if issue.created:
                    created_date = datetime.fromisoformat(issue.created.replace('Z', '+00:00'))
                    assert created_date >= one_month_ago, f"Issue {issue.id_readable} was created before the specified date range"
                    assert created_date <= now, f"Issue {issue.id_readable} has a future creation date"
            
            # If we found issues with this tag, no need to try other tags
            if issues:
                break
    
    # No assertion for finding issues, as there might not be any with these specific tags
    # The test is successful if the API calls work correctly
