"""MCP YouTrack Server implementation.

This module defines a Model Context Protocol (MCP) server with tools that interact with
YouTrack API using the youtrack-sdk.
"""

import logging
import concurrent.futures
import atexit
import os
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from youtrack_sdk.client import Client
from youtrack_sdk.entities import IssueComment, IssueCustomFieldType

MCP_SERVER_NAME = "mcp-youtrack"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(MCP_SERVER_NAME)

QUERY_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=10)
atexit.register(lambda: QUERY_EXECUTOR.shutdown(wait=True))
SELECT_QUERY_TIMEOUT_SECS = 30

load_dotenv()

# YouTrack client configuration
YOUTRACK_URL = os.getenv("YOUTRACK_URL")
YOUTRACK_TOKEN = os.getenv("YOUTRACK_TOKEN")

# Initialize YouTrack client
youtrack_client = None
if YOUTRACK_URL and YOUTRACK_TOKEN:
    try:
        youtrack_client = Client(base_url=YOUTRACK_URL, token=YOUTRACK_TOKEN)
        logger.info(f"YouTrack client initialized with URL: {YOUTRACK_URL}")
    except Exception as e:
        logger.error(f"Failed to initialize YouTrack client: {e}")
else:
    logger.warning("YouTrack URL or token not provided. Set YOUTRACK_URL and YOUTRACK_TOKEN environment variables.")

deps = [
    "python-dotenv",
    "uvicorn",
    "pydantic>=2.0.0",
    "youtrack-sdk",
]

mcp = FastMCP(MCP_SERVER_NAME, dependencies=deps)


class IssueResponse(BaseModel):
    id: str
    id_readable: str
    summary: str
    description: Optional[str] = None
    project: Optional[Dict[str, Any]] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    reporter: Optional[Dict[str, Any]] = None


@mcp.tool()
def get_issues(query: str) -> List[IssueResponse]:
    """Get YouTrack issues based on a search query.
    
    Args:
        query: YouTrack search query string
        
    Returns:
        List[IssueResponse]: List of issues matching the query
    """
    logger.info(f"Searching for issues with query: {query}")
    
    if not youtrack_client:
        logger.error("YouTrack client not initialized")
        return []
    
    try:
        issues = youtrack_client.get_issues(query=query)
        logger.info(f"Found {len(issues)} issues")
        
        # Convert to response model
        result = []
        for issue in issues:
            issue_data = IssueResponse(
                id=issue.id or "",
                id_readable=issue.id_readable or "",
                summary=issue.summary or "",
                description=issue.description,
                project={"id": issue.project.id, "name": issue.project.name} if issue.project else None,
                created=str(issue.created) if issue.created else None,
                updated=str(issue.updated) if issue.updated else None,
                reporter={"name": issue.reporter.name, "login": issue.reporter.login} if issue.reporter else None
            )
            result.append(issue_data)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching issues: {e}")
        return []


class CommentIssueRequest(BaseModel):
    issue_id: str = Field(..., description="ID of the issue to comment on")
    text: str = Field(..., description="Comment text")


@mcp.tool()
def comment_issue(issue_id: str, text: str) -> Dict[str, Any]:
    """Create a comment on a YouTrack issue.
    
    Args:
        issue_id: ID of the issue to comment on
        text: Comment text
        
    Returns:
        Dict: Information about the created comment
    """
    logger.info(f"Adding comment to issue {issue_id}")
    
    if not youtrack_client:
        logger.error("YouTrack client not initialized")
        return {"success": False, "error": "YouTrack client not initialized"}
    
    try:
        comment = IssueComment(text=text)
        result = youtrack_client.create_issue_comment(issue_id=issue_id, comment=comment)
        
        return {
            "success": True,
            "comment_id": result.id,
            "text": result.text,
            "created": str(result.created) if result.created else None,
            "author": {"name": result.author.name, "login": result.author.login} if result.author else None
        }
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        return {"success": False, "error": str(e)}


class UpdateFieldRequest(BaseModel):
    issue_id: str = Field(..., description="ID of the issue to update")
    field_id: str = Field(..., description="ID of the custom field to update")
    field_value: Any = Field(..., description="New value for the field")


@mcp.tool()
def update_field(issue_id: str, field_id: str, field_value: Any) -> Dict[str, Any]:
    """Update a field of a YouTrack issue.
    
    Args:
        issue_id: ID of the issue to update
        field_id: ID of the custom field to update
        field_value: New value for the field
        
    Returns:
        Dict: Information about the update operation
    """
    logger.info(f"Updating field {field_id} for issue {issue_id}")
    
    if not youtrack_client:
        logger.error("YouTrack client not initialized")
        return {"success": False, "error": "YouTrack client not initialized"}
    
    try:
        # Get the issue's custom fields
        custom_fields = youtrack_client.get_issue_custom_fields(issue_id=issue_id)
        
        # Find the target field
        target_field = None
        for field in custom_fields:
            if field.id == field_id or field.name == field_id:
                target_field = field
                break
        
        if not target_field:
            return {"success": False, "error": f"Field {field_id} not found"}
        
        # Update the field value
        target_field.value = field_value
        
        # Send the update to YouTrack
        result = youtrack_client.update_issue_custom_field(
            issue_id=issue_id,
            field=target_field
        )
        
        return {
            "success": True,
            "field_id": result.id,
            "field_name": result.name,
            "updated_value": str(result.value) if result.value else None
        }
    except Exception as e:
        logger.error(f"Error updating field: {e}")
        return {"success": False, "error": str(e)}
