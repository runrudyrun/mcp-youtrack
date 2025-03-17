#!/usr/bin/env python3
"""
Helper script to run the MCP YouTrack interactive client.
"""

import asyncio
import sys

from mcp_youtrack.run_interactive import main

if __name__ == "__main__":
    asyncio.run(main())
