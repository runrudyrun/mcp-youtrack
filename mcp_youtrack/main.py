"""Entry point for MCP YouTrack server.

This module provides a simple command-line interface for starting the MCP server
that interacts with YouTrack.
"""

from .mcp_server import mcp


def main():
    """Run the MCP YouTrack server."""
    mcp.run()


if __name__ == "__main__":
    main()
