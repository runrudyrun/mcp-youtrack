"""MCP YouTrack server entry point."""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

import uvicorn
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-youtrack")


def main() -> None:
    """Run the MCP YouTrack server."""
    # Load environment variables from .env file
    load_dotenv()

    # Check if YOUTRACK_URL and YOUTRACK_TOKEN are set
    youtrack_url = os.getenv("YOUTRACK_URL")
    youtrack_token = os.getenv("YOUTRACK_TOKEN")

    if not youtrack_url or not youtrack_token:
        logger.error(
            "YOUTRACK_URL and YOUTRACK_TOKEN environment variables must be set"
        )
        sys.exit(1)

    logger.info(f"YouTrack client initialized with URL: {youtrack_url}")

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="MCP YouTrack server")
    parser.add_argument(
        "--interactive", action="store_true", help="Run in interactive mode"
    )
    parser.add_argument(
        "--direct", action="store_true", help="Use direct mode in interactive client"
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host to bind to"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to"
    )
    args = parser.parse_args()

    if args.interactive:
        # Run in interactive mode
        from .interactive import main as interactive_main
        
        # Pass the direct flag to the interactive client
        if args.direct:
            sys.argv.append("--direct")
            
        asyncio.run(interactive_main())
    else:
        # Run the MCP server
        from .mcp_server import app
        
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
