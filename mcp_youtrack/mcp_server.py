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
from youtrack_sdk.entities import IssueComment, Issue, Tag

# Define custom field types to match the SDK
class IssueCustomFieldType:
    """Custom field types for YouTrack issues."""
    SINGLE_ENUM = "enum"
    MULTI_ENUM = "enum[]"
    SINGLE_BUILD = "build"
    MULTI_BUILD = "build[]"
    STATE = "state"
    SINGLE_VERSION = "version"
    MULTI_VERSION = "version[]"
    SINGLE_OWNED = "ownedField"
    MULTI_OWNED = "ownedField[]"
    SINGLE_USER = "user"
    MULTI_USER = "user[]"
    SINGLE_GROUP = "group"
    MULTI_GROUP = "group[]"
    SIMPLE = "simple"
    DATE = "date"
    PERIOD = "period"
    TEXT = "text"

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
    wikified_description: Optional[str] = None
    project: Optional[Dict[str, Any]] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    reporter: Optional[Dict[str, Any]] = None
    custom_fields: Optional[List[Dict[str, Any]]] = None


@mcp.tool()
def get_issues(query: str, limit: int = 5) -> List[IssueResponse]:
    """Get YouTrack issues based on a search query.
    
    Args:
        query: YouTrack search query string
        limit: Maximum number of issues to return (default: 5)
        
    Returns:
        List[IssueResponse]: List of issues matching the query
    """
    logger.info(f"Searching for issues with query: {query}, limit: {limit}")
    
    if not youtrack_client:
        logger.error("YouTrack client not initialized")
        return []
    
    try:
        issues = youtrack_client.get_issues(query=query)
        logger.info(f"Found {len(issues)} issues")
        
        # Convert to response model
        result = []
        for issue in issues[:limit]:
            # Process custom fields if available
            custom_fields_data = None
            if hasattr(issue, 'custom_fields') and issue.custom_fields:
                custom_fields_data = []
                for field in issue.custom_fields:
                    field_data = {
                        "id": field.id,
                        "name": field.name,
                        "type": getattr(field, 'type', None),
                        "value": getattr(field, 'value', None)
                    }
                    custom_fields_data.append(field_data)
            
            issue_data = IssueResponse(
                id=issue.id or "",
                id_readable=issue.id_readable or "",
                summary=issue.summary or "",
                description=issue.description,
                wikified_description=getattr(issue, 'wikified_description', None),
                project={"id": issue.project.id, "name": issue.project.name} if issue.project else None,
                created=str(issue.created) if issue.created else None,
                updated=str(issue.updated) if issue.updated else None,
                reporter={"name": issue.reporter.name, "login": issue.reporter.login} if issue.reporter else None,
                custom_fields=custom_fields_data
            )
            result.append(issue_data)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching issues: {e}")
        return []


class IssueDetailResponse(BaseModel):
    id: str
    id_readable: str
    summary: str
    description: Optional[str] = None
    wikified_description: Optional[str] = None
    project: Optional[Dict[str, Any]] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    resolved: Optional[str] = None
    reporter: Optional[Dict[str, Any]] = None
    updater: Optional[Dict[str, Any]] = None
    comments_count: Optional[int] = None
    tags: Optional[List[Dict[str, Any]]] = None
    custom_fields: Optional[List[Dict[str, Any]]] = None
    links: Optional[List[Dict[str, Any]]] = None


@mcp.tool()
def get_issue_details(issue_id: str) -> Optional[IssueDetailResponse]:
    """Get detailed information about a specific YouTrack issue.
    
    Args:
        issue_id: ID of the issue to fetch
        
    Returns:
        IssueDetailResponse: Detailed information about the issue
    """
    logger.info(f"Fetching details for issue {issue_id}")
    
    if not youtrack_client:
        logger.error("YouTrack client not initialized")
        return None
    
    try:
        # Get the issue with all details
        issue = youtrack_client.get_issue(issue_id=issue_id)
        
        if not issue:
            logger.warning(f"Issue {issue_id} not found")
            return None
        
        # Process custom fields
        custom_fields_data = None
        if hasattr(issue, 'custom_fields') and issue.custom_fields:
            custom_fields_data = []
            for field in issue.custom_fields:
                field_data = {
                    "id": field.id,
                    "name": field.name,
                    "type": getattr(field, 'type', None),
                }
                
                # Handle different field types
                if hasattr(field, 'value'):
                    if field.type in [IssueCustomFieldType.SINGLE_ENUM, IssueCustomFieldType.MULTI_ENUM]:
                        if isinstance(field.value, list):
                            field_data["value"] = [{"name": item.name, "id": item.id} for item in field.value if hasattr(item, 'name')]
                        elif hasattr(field.value, 'name'):
                            field_data["value"] = {"name": field.value.name, "id": field.value.id}
                        else:
                            field_data["value"] = str(field.value)
                    elif field.type in [IssueCustomFieldType.SINGLE_USER, IssueCustomFieldType.MULTI_USER]:
                        if isinstance(field.value, list):
                            field_data["value"] = [{"name": user.name, "login": user.login} for user in field.value if hasattr(user, 'name')]
                        elif hasattr(field.value, 'name'):
                            field_data["value"] = {"name": field.value.name, "login": field.value.login}
                        else:
                            field_data["value"] = str(field.value)
                    else:
                        field_data["value"] = str(field.value)
                
                custom_fields_data.append(field_data)
        
        # Get issue links
        links_data = None
        try:
            links = youtrack_client.get_issue_links(issue_id=issue_id)
            if links:
                links_data = []
                for link in links:
                    link_data = {
                        "type": {"name": link.type.name, "id": link.type.id} if hasattr(link, 'type') and link.type else None,
                        "direction": getattr(link, 'direction', None),
                        "issues": []
                    }
                    
                    if hasattr(link, 'issues') and link.issues:
                        for linked_issue in link.issues:
                            link_data["issues"].append({
                                "id": linked_issue.id,
                                "id_readable": linked_issue.id_readable,
                                "summary": linked_issue.summary
                            })
                    
                    links_data.append(link_data)
        except Exception as e:
            logger.warning(f"Error fetching issue links: {e}")
        
        # Process tags
        tags_data = None
        if hasattr(issue, 'tags') and issue.tags:
            tags_data = []
            for tag in issue.tags:
                tag_data = {
                    "name": tag.name,
                    "id": tag.id
                }
                tags_data.append(tag_data)
        
        # Create response
        response = IssueDetailResponse(
            id=issue.id or "",
            id_readable=issue.id_readable or "",
            summary=issue.summary or "",
            description=issue.description,
            wikified_description=getattr(issue, 'wikified_description', None),
            project={"id": issue.project.id, "name": issue.project.name} if issue.project else None,
            created=str(issue.created) if issue.created else None,
            updated=str(issue.updated) if issue.updated else None,
            resolved=str(issue.resolved) if hasattr(issue, 'resolved') and issue.resolved else None,
            reporter={"name": issue.reporter.name, "login": issue.reporter.login} if issue.reporter else None,
            updater={"name": issue.updater.name, "login": issue.updater.login} if hasattr(issue, 'updater') and issue.updater else None,
            comments_count=issue.comments_count if hasattr(issue, 'comments_count') else None,
            tags=tags_data,
            custom_fields=custom_fields_data,
            links=links_data
        )
        
        return response
    except Exception as e:
        logger.error(f"Error fetching issue details: {e}")
        return None


class CustomFieldResponse(BaseModel):
    id: str
    name: str
    type: Optional[str] = None
    value: Optional[Any] = None


@mcp.tool()
def get_issue_custom_fields(issue_id: str) -> List[CustomFieldResponse]:
    """Get custom fields for a specific YouTrack issue.
    
    Args:
        issue_id: ID of the issue to fetch custom fields for
        
    Returns:
        List[CustomFieldResponse]: List of custom fields for the issue
    """
    logger.info(f"Fetching custom fields for issue {issue_id}")
    
    if not youtrack_client:
        logger.error("YouTrack client not initialized")
        return []
    
    try:
        # Get the custom fields for the issue
        custom_fields = youtrack_client.get_issue_custom_fields(issue_id=issue_id)
        
        if not custom_fields:
            logger.warning(f"No custom fields found for issue {issue_id}")
            return []
        
        # Convert to response model
        result = []
        for field in custom_fields:
            field_value = None
            
            # Handle different field types
            if hasattr(field, 'value') and field.value is not None:
                if field.type in [IssueCustomFieldType.SINGLE_ENUM, IssueCustomFieldType.MULTI_ENUM]:
                    if isinstance(field.value, list):
                        field_value = [{"name": item.name, "id": item.id} for item in field.value if hasattr(item, 'name')]
                    elif hasattr(field.value, 'name'):
                        field_value = {"name": field.value.name, "id": field.value.id}
                    else:
                        field_value = str(field.value)
                elif field.type in [IssueCustomFieldType.SINGLE_USER, IssueCustomFieldType.MULTI_USER]:
                    if isinstance(field.value, list):
                        field_value = [{"name": user.name, "login": user.login} for user in field.value if hasattr(user, 'name')]
                    elif hasattr(field.value, 'name'):
                        field_value = {"name": field.value.name, "login": field.value.login}
                    else:
                        field_value = str(field.value)
                elif field.type == IssueCustomFieldType.DATE:
                    field_value = str(field.value)
                elif field.type == IssueCustomFieldType.PERIOD:
                    field_value = str(field.value)
                else:
                    field_value = str(field.value)
            
            field_data = CustomFieldResponse(
                id=field.id,
                name=field.name,
                type=field.type if hasattr(field, 'type') else None,
                value=field_value
            )
            result.append(field_data)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching custom fields: {e}")
        return []


class CommentResponse(BaseModel):
    issue_id: str
    id: str
    text: str
    text_preview: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    author: Optional[Dict[str, Any]] = None
    deleted: Optional[bool] = None


@mcp.tool()
def get_issue_comments(issue_id: str) -> List[CommentResponse]:
    """Get comments for a specific YouTrack issue.
    
    Args:
        issue_id: ID of the issue to fetch comments for
        
    Returns:
        List[CommentResponse]: List of comments for the issue
    """
    logger.info(f"Fetching comments for issue {issue_id}")
    
    if not youtrack_client:
        logger.error("YouTrack client not initialized")
        return []
    
    try:
        # Get the comments for the issue
        comments = youtrack_client.get_issue_comments(issue_id=issue_id)
        
        if not comments:
            logger.warning(f"No comments found for issue {issue_id}")
            return []
        
        # Convert to response model
        result = []
        for comment in comments:
            comment_data = CommentResponse(
                issue_id=issue_id or "",
                id=comment.id or "",
                text=comment.text or "",
                text_preview=getattr(comment, 'text_preview', None),
                created=str(comment.created) if comment.created else None,
                updated=str(comment.updated) if hasattr(comment, 'updated') and comment.updated else None,
                author={"name": comment.author.name, "login": comment.author.login} if comment.author else None,
                deleted=comment.deleted if hasattr(comment, 'deleted') else None
            )
            result.append(comment_data)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching comments: {e}")
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
        
        logger.info(f"Found field: {target_field}")
        
        # Create a new field instance with the updated value
        field_type = type(target_field)
        
        # Handle different field types appropriately
        if field_type.__name__ == "StateIssueCustomField":
            from youtrack_sdk.entities import StateBundleElement
            # For state fields, we need to create a StateBundleElement with the name
            if isinstance(field_value, str):
                # Create a new StateBundleElement with the provided name
                new_value = StateBundleElement(name=field_value)
            else:
                new_value = field_value
            
            # Create a new field instance with the same ID but updated value
            updated_field = field_type(id=target_field.id, name=target_field.name, value=new_value)
        elif field_type.__name__ in ["SingleEnumIssueCustomField", "MultiEnumIssueCustomField"]:
            from youtrack_sdk.entities import EnumBundleElement
            # For enum fields, we need to create an EnumBundleElement with the name
            if isinstance(field_value, str):
                # Create a new EnumBundleElement with the provided name
                new_value = EnumBundleElement(name=field_value)
                # For multi-enum fields, wrap in a list
                if field_type.__name__ == "MultiEnumIssueCustomField":
                    new_value = [new_value]
            else:
                new_value = field_value
            
            # Create a new field instance with the same ID but updated value
            updated_field = field_type(id=target_field.id, name=target_field.name, value=new_value)
        else:
            # For other field types, create a new instance with the same properties
            # but with the updated value
            updated_field = field_type(
                id=target_field.id,
                name=target_field.name,
                value=field_value
            )
        
        logger.info(f"Sending update with field: {updated_field}")
        
        # Send the update to YouTrack
        result = youtrack_client.update_issue_custom_field(
            issue_id=issue_id,
            field=updated_field
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


class SetIssueTagsRequest(BaseModel):
    issue_id: str = Field(..., description="ID of the issue to set tags for")
    tags: List[str] = Field(..., description="List of tag names to add to the issue")


@mcp.tool()
def set_issue_tags(issue_id: str, tags: List[str]) -> Dict[str, Any]:
    """Set tags for a specific YouTrack issue.
    
    Args:
        issue_id: ID of the issue to set tags for
        tags: List of tag names to add to the issue
        
    Returns:
        Dict: Information about the operation result
    """
    logger.info(f"Setting tags {tags} for issue {issue_id}")
    
    if not youtrack_client:
        logger.error("YouTrack client not initialized")
        return {"success": False, "error": "YouTrack client not initialized"}
    
    try:
        # Get existing tags to avoid duplicates
        issue = youtrack_client.get_issue(issue_id=issue_id)
        existing_tags = set()
        
        if hasattr(issue, 'tags') and issue.tags:
            existing_tags = {tag.name for tag in issue.tags if hasattr(tag, 'name') and tag.name}
        
        # Get all available tags from YouTrack
        all_tags = youtrack_client.get_tags()
        all_tags_dict = {tag.name: tag for tag in all_tags if hasattr(tag, 'name') and tag.name}
        
        # Track added tags
        added_tags = []
        
        # Add each tag that doesn't already exist on the issue
        for tag_name in tags:
            if tag_name in existing_tags:
                logger.info(f"Tag '{tag_name}' already exists on issue {issue_id}")
                continue
                
            # Check if the tag exists in YouTrack
            if tag_name in all_tags_dict:
                tag = all_tags_dict[tag_name]
            else:
                # If the tag doesn't exist in the system, we can't add it
                logger.warning(f"Tag '{tag_name}' doesn't exist in YouTrack")
                continue
                
            # Add the tag to the issue
            tag_entity = Tag(id=tag.id, name=tag.name)
            youtrack_client.add_issue_tag(issue_id=issue_id, tag=tag_entity)
            added_tags.append(tag_name)
            logger.info(f"Added tag '{tag_name}' to issue {issue_id}")
        
        return {
            "success": True,
            "issue_id": issue_id,
            "added_tags": added_tags,
            "skipped_tags": [tag for tag in tags if tag not in added_tags]
        }
    except Exception as e:
        logger.error(f"Error setting tags: {e}")
        return {"success": False, "error": str(e)}
