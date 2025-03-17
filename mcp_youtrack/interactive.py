"""Interactive query interface for MCP YouTrack.

This module provides an interactive command-line interface for querying
the YouTrack API through the MCP server tools.
"""

import asyncio
import json
import logging
import os
import sys
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-youtrack-interactive")


class CommandInfo(BaseModel):
    """Information about a command."""
    name: str
    description: str
    usage: str
    example: str


class InteractiveClient:
    """Interactive client for MCP YouTrack."""

    def __init__(self, direct_mode: bool = False):
        """Initialize the interactive client.
        
        Args:
            direct_mode: If True, use the MCP server directly instead of subprocess
        """
        self.session = None
        self.direct_mode = direct_mode
        self.mcp_server = None
        self.commands: Dict[str, CommandInfo] = {
            "help": CommandInfo(
                name="help",
                description="Show help information",
                usage="help [command]",
                example="help issues"
            ),
            "issues": CommandInfo(
                name="issues",
                description="Search for issues using YouTrack query syntax",
                usage="issues <query>",
                example="issues project: DEMO #Unresolved"
            ),
            "issue": CommandInfo(
                name="issue",
                description="Get detailed information about a specific issue",
                usage="issue <issue_id>",
                example="issue DEMO-123"
            ),
            "fields": CommandInfo(
                name="fields",
                description="Get custom fields for a specific issue",
                usage="fields <issue_id>",
                example="fields DEMO-123"
            ),
            "comments": CommandInfo(
                name="comments",
                description="Get comments for a specific issue",
                usage="comments <issue_id>",
                example="comments DEMO-123"
            ),
            "comment": CommandInfo(
                name="comment",
                description="Add a comment to an issue",
                usage="comment <issue_id> <text>",
                example="comment DEMO-123 \"This is a comment\""
            ),
            "update": CommandInfo(
                name="update",
                description="Update a field of an issue",
                usage="update <issue_id> <field_id> <field_value>",
                example="update DEMO-123 State \"In Progress\""
            ),
            "quit": CommandInfo(
                name="quit",
                description="Exit the interactive client",
                usage="quit",
                example="quit"
            ),
        }

    async def connect(self) -> bool:
        """Connect to the MCP server.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if self.direct_mode:
            try:
                # Import the MCP server directly
                from .mcp_server import (
                    get_issues, 
                    get_issue_details, 
                    get_issue_custom_fields, 
                    get_issue_comments, 
                    comment_issue, 
                    update_field
                )
                
                # Store the functions for later use
                self.mcp_server = {
                    "get_issues": get_issues,
                    "get_issue_details": get_issue_details,
                    "get_issue_custom_fields": get_issue_custom_fields,
                    "get_issue_comments": get_issue_comments,
                    "comment_issue": comment_issue,
                    "update_field": update_field
                }
                
                logger.info("Connected to MCP YouTrack server (direct mode)")
                return True
            except ImportError as e:
                logger.error(f"Failed to import MCP server functions: {e}")
                return False
        else:
            # Since we can't directly use the mcp-client library in this version,
            # we'll use the mcp-youtrack command-line tool directly
            logger.info("Connected to MCP YouTrack server (subprocess mode)")
            return True

    async def close(self) -> None:
        """Close the connection to the MCP server."""
        logger.info("Disconnected from MCP YouTrack server")

    def _format_output(self, data: Any) -> str:
        """Format output data as pretty JSON.
        
        Args:
            data: Data to format
            
        Returns:
            str: Formatted data as pretty JSON
        """
        return json.dumps(data, indent=2, default=str)

    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool using the mcp-youtrack command-line tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Any: Tool response
        """
        if self.direct_mode and self.mcp_server:
            # Call the tool directly
            try:
                if tool_name not in self.mcp_server:
                    logger.error(f"Unknown tool: {tool_name}")
                    raise Exception(f"Unknown tool: {tool_name}")
                
                # Call the function directly
                result = self.mcp_server[tool_name](**arguments)
                
                # Convert pydantic models to dict
                if hasattr(result, "model_dump"):
                    return result.model_dump()
                elif hasattr(result, "dict"):
                    return result.dict()
                
                return result
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                raise Exception(f"Error calling tool {tool_name}: {e}")
        else:
            # Convert arguments to JSON
            args_json = json.dumps(arguments)
            
            # Call the tool using the mcp-youtrack command-line tool
            cmd = [
                sys.executable, "-m", "mcp.client.stdio", 
                "--server", "mcp-youtrack", 
                "--tool", tool_name, 
                "--args", args_json
            ]
            
            try:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    check=False  # Don't raise an exception on non-zero exit code
                )
                
                if result.returncode != 0:
                    logger.error(f"Error calling tool {tool_name}: {result.stderr}")
                    raise Exception(f"Error calling tool {tool_name}: {result.stderr}")
                
                # Check if stdout is empty
                if not result.stdout.strip():
                    logger.warning(f"Empty response from tool {tool_name}")
                    return None
                
                try:
                    # Parse the JSON response
                    return json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing response from tool {tool_name}: {e}")
                    logger.error(f"Response was: {result.stdout}")
                    # Try to return the raw output if JSON parsing fails
                    return {"raw_output": result.stdout}
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                raise Exception(f"Error calling tool {tool_name}: {e}")

    async def process_command(self, command: str) -> Tuple[bool, str]:
        """Process a command.
        
        Args:
            command: Command to process
            
        Returns:
            Tuple[bool, str]: (continue_loop, response)
        """
        if not command:
            return True, "Please enter a command. Type 'help' for available commands."

        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "quit":
            return False, "Exiting interactive client..."

        if cmd == "help":
            return True, self._process_help(args)

        try:
            if cmd == "issues":
                return await self._process_issues(args)
            elif cmd == "issue":
                return await self._process_issue(args)
            elif cmd == "fields":
                return await self._process_fields(args)
            elif cmd == "comments":
                return await self._process_comments(args)
            elif cmd == "comment":
                return await self._process_comment(args)
            elif cmd == "update":
                return await self._process_update(args)
            else:
                return True, f"Unknown command: {cmd}. Type 'help' for available commands."
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return True, f"Error: {str(e)}"

    def _process_help(self, args: str) -> str:
        """Process help command.
        
        Args:
            args: Command arguments
            
        Returns:
            str: Help information
        """
        if not args:
            # General help
            help_text = "Available commands:\n\n"
            for cmd_info in self.commands.values():
                help_text += f"{cmd_info.name}: {cmd_info.description}\n"
            help_text += "\nType 'help <command>' for more information about a specific command."
            return help_text
        
        # Command-specific help
        cmd = args.lower()
        if cmd in self.commands:
            cmd_info = self.commands[cmd]
            return (
                f"Command: {cmd_info.name}\n"
                f"Description: {cmd_info.description}\n"
                f"Usage: {cmd_info.usage}\n"
                f"Example: {cmd_info.example}"
            )
        else:
            return f"Unknown command: {cmd}. Type 'help' for available commands."

    async def _process_issues(self, query: str) -> Tuple[bool, str]:
        """Process issues command.
        
        Args:
            query: YouTrack search query
            
        Returns:
            Tuple[bool, str]: (continue_loop, response)
        """
        if not query:
            return True, "Please provide a search query. Example: issues project: DEMO #Unresolved"
        
        try:
            response = self._call_tool(
                tool_name="get_issues", 
                arguments={"query": query}
            )
            
            if not response:
                return True, "No issues found."
            
            return True, self._format_output(response)
        except Exception as e:
            return True, f"Error: {str(e)}"

    async def _process_issue(self, issue_id: str) -> Tuple[bool, str]:
        """Process issue command.
        
        Args:
            issue_id: ID of the issue to fetch
            
        Returns:
            Tuple[bool, str]: (continue_loop, response)
        """
        if not issue_id:
            return True, "Please provide an issue ID. Example: issue DEMO-123"
        
        try:
            response = self._call_tool(
                tool_name="get_issue_details", 
                arguments={"issue_id": issue_id}
            )
            
            if not response:
                return True, f"Issue {issue_id} not found."
            
            return True, self._format_output(response)
        except Exception as e:
            return True, f"Error: {str(e)}"

    async def _process_fields(self, issue_id: str) -> Tuple[bool, str]:
        """Process fields command.
        
        Args:
            issue_id: ID of the issue to fetch fields for
            
        Returns:
            Tuple[bool, str]: (continue_loop, response)
        """
        if not issue_id:
            return True, "Please provide an issue ID. Example: fields DEMO-123"
        
        try:
            response = self._call_tool(
                tool_name="get_issue_custom_fields", 
                arguments={"issue_id": issue_id}
            )
            
            if not response:
                return True, f"No custom fields found for issue {issue_id}."
            
            return True, self._format_output(response)
        except Exception as e:
            return True, f"Error: {str(e)}"

    async def _process_comments(self, issue_id: str) -> Tuple[bool, str]:
        """Process comments command.
        
        Args:
            issue_id: ID of the issue to fetch comments for
            
        Returns:
            Tuple[bool, str]: (continue_loop, response)
        """
        if not issue_id:
            return True, "Please provide an issue ID. Example: comments DEMO-123"
        
        try:
            response = self._call_tool(
                tool_name="get_issue_comments", 
                arguments={"issue_id": issue_id}
            )
            
            if not response:
                return True, f"No comments found for issue {issue_id}."
            
            return True, self._format_output(response)
        except Exception as e:
            return True, f"Error: {str(e)}"

    async def _process_comment(self, args: str) -> Tuple[bool, str]:
        """Process comment command.
        
        Args:
            args: Command arguments (issue_id and text)
            
        Returns:
            Tuple[bool, str]: (continue_loop, response)
        """
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            return True, "Please provide an issue ID and comment text. Example: comment DEMO-123 \"This is a comment\""
        
        issue_id, text = parts
        
        try:
            response = self._call_tool(
                tool_name="comment_issue", 
                arguments={"issue_id": issue_id, "text": text}
            )
            
            return True, self._format_output(response)
        except Exception as e:
            return True, f"Error: {str(e)}"

    async def _process_update(self, args: str) -> Tuple[bool, str]:
        """Process update command.
        
        Args:
            args: Command arguments (issue_id, field_id, and field_value)
            
        Returns:
            Tuple[bool, str]: (continue_loop, response)
        """
        parts = args.split(maxsplit=2)
        if len(parts) < 3:
            return True, "Please provide an issue ID, field ID, and field value. Example: update DEMO-123 State \"In Progress\""
        
        issue_id, field_id, field_value = parts
        
        try:
            response = self._call_tool(
                tool_name="update_field", 
                arguments={
                    "issue_id": issue_id, 
                    "field_id": field_id, 
                    "field_value": field_value
                }
            )
            
            return True, self._format_output(response)
        except Exception as e:
            return True, f"Error: {str(e)}"

    async def run(self) -> None:
        """Run the interactive client."""
        print("\n=== MCP YouTrack Interactive Client ===")
        print("Type 'help' for available commands or 'quit' to exit.")
        
        if not await self.connect():
            print("Failed to connect to MCP YouTrack server. Exiting...")
            return
        
        try:
            while True:
                try:
                    command = input("\n> ").strip()
                    continue_loop, response = await self.process_command(command)
                    print(f"\n{response}")
                    
                    if not continue_loop:
                        break
                except KeyboardInterrupt:
                    print("\nKeyboard interrupt detected. Exiting...")
                    break
                except EOFError:
                    print("\nEOF detected. Exiting...")
                    break
                except Exception as e:
                    print(f"\nError: {str(e)}")
        finally:
            await self.close()


async def main() -> None:
    """Run the interactive client."""
    # Check if direct mode is requested
    direct_mode = "--direct" in sys.argv
    
    if direct_mode:
        print("Running in direct mode (using MCP server directly)")
    else:
        print("Running in subprocess mode (using MCP client)")
    
    client = InteractiveClient(direct_mode=direct_mode)
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
