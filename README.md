# MCP YouTrack

A Model Context Protocol (MCP) server for interacting with YouTrack issue tracking system.

# Demo

### Example: add to Windsurf mcp_config.json
```json
{
  "mcpServers": {
    "mcp-youtrack": {
      "command": "{PATH_TO_MCP_YOUTRACK}/mcp-youtrack/.venv/bin/mcp-youtrack",
      "args": [
        "run",
        "--with",
        "mcp-youtrack",
        "--python",
        "3.13",
        "mcp-youtrack"
      ]
    }
  }
}
```

## Overview

This repository provides a Model Context Protocol (MCP) server for YouTrack integration. It uses the youtrack-sdk to interact with the YouTrack API and provides tools for common operations like querying issues, adding comments, and updating issue fields.

The server is designed to be:
- **Efficient**: Optimized for common YouTrack operations
- **Flexible**: Easy to extend with additional YouTrack functionality
- **Secure**: Handles authentication and error handling
- **Type-safe**: Uses pydantic for data validation

## Getting Started

### Prerequisites

- Python 3.13 or later
- uv (for dependency management)
- A YouTrack instance with API access

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/mcp-youtrack.git
cd mcp-youtrack
```

2. Install dependencies:
```bash
uv lock
```

3. Set up environment variables:
```bash
# Create a .env file
echo "YOUTRACK_URL=https://your-youtrack-instance.com" > .env
echo "YOUTRACK_TOKEN=your-permanent-token" >> .env
```

4. Run the server:
```bash
uv run mcp-youtrack
```

## Architecture

The MCP YouTrack server follows a simple architecture:

- `mcp_youtrack/`: Main package
  - `__init__.py`: Package definition
  - `main.py`: Entry point
  - `mock_env.py`: Configuration management
  - `mcp_server.py`: MCP server implementation with tool definitions

### YouTrack Tools

The server provides the following tools for interacting with YouTrack:

- `get_issues(query: str)`: Get issues matching a search query
- `comment_issue(issue_id: str, text: str)`: Add a comment to an issue
- `update_field(issue_id: str, field_id: str, field_value: Any)`: Update a field of an issue

## Extending the Server

To add more YouTrack functionality to the server:

### 1. Add New Tools

Add new tools to the MCP server to extend its functionality:

```python
@mcp.tool()
def create_issue(summary: str, description: str = None, project_id: str = None):
    # Implement issue creation
    # ...
    return {"result": "Issue created successfully", "issue_id": new_issue.id}
```

### 2. Update Tests

Make sure to add tests for any new functionality:

```python
def test_create_issue_success(mock_youtrack_client):
    # Setup mock
    # ...
    
    # Execute
    result = create_issue("Test issue", "Description", "TEST")
    
    # Verify
    assert result["result"] == "Issue created successfully"
    # ...
```

## Testing

The server includes comprehensive tests. Run tests with:

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.
