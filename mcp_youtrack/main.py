"""
Entry point for MCP YouTrack server.
"""

from .mcp_server import mcp


def main():
    """Run the MCP YouTrack server."""
    mcp.run()


if __name__ == "__main__":
    main()
