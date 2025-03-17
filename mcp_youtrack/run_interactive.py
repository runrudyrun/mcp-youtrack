"""Interactive client runner for MCP YouTrack.

This module provides a standalone way to run the interactive client
without modifying the main.py entry point.
"""

import argparse
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-youtrack-interactive-runner")


async def main() -> None:
    """Run the MCP YouTrack interactive client."""
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
    parser = argparse.ArgumentParser(description="MCP YouTrack Interactive Client")
    parser.add_argument(
        "--direct", action="store_true", help="Use direct mode in interactive client"
    )
    args = parser.parse_args()

    try:
        # Import the interactive module
        from .interactive import main as interactive_main
        
        # Run the interactive client with the direct flag if specified
        if args.direct:
            sys.argv.append("--direct")
            
        await interactive_main()
    except ImportError as e:
        logger.error(f"Failed to import interactive module: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running interactive client: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
