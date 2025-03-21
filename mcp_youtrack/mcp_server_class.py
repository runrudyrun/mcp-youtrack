from uuid import UUID

import mcp.types as types
import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send
import logging

logger = logging.getLogger(__name__)
# YouTrack client configuration

class SSEServerTransport(SseServerTransport):
    async def handle_post_message(self, scope: Scope, receive: Receive, send: Send) -> None:
        logger.debug("Handling POST message")
        request = Request(scope, receive)

        session_id_param = request.query_params.get("session_id")
        if session_id_param is None:
            logger.warning("Received request without session_id")
            response = Response("session_id is required", status_code=400)
            return await response(scope, receive, send)

        try:
            session_id = UUID(hex=session_id_param)
            logger.debug(f"Parsed session ID: {session_id}")
        except ValueError:
            logger.warning(f"Received invalid session ID: {session_id_param}")
            response = Response("Invalid session ID", status_code=400)
            return await response(scope, receive, send)

        writer = self._read_stream_writers.get(session_id)
        if not writer:
            logger.warning(f"Could not find session for ID: {session_id}")
            response = Response("Could not find session", status_code=404)
            return await response(scope, receive, send)

        json = await request.json()
        logger.debug(f"Received JSON: {json}")

        if json["method"] == "tools/call":
            json["params"].setdefault("_meta", {})
            json["params"]["_meta"]["youtrack_url"] = request.headers.get(
                "x-youtrack-url"
            )
            json["params"]["_meta"]["youtrack_token"] = request.headers.get(
                "x-youtrack-token"
            )

        try:
            message = types.JSONRPCMessage.model_validate(json)
            logger.debug(f"Validated client message: {message}")
        except ValidationError as err:
            logger.error(f"Failed to parse message: {err}")
            response = Response("Could not parse message", status_code=400)
            await response(scope, receive, send)
            await writer.send(err)
            return

        logger.debug(f"Sending message to writer: {message}")
        response = Response("Accepted", status_code=202)
        await response(scope, receive, send)
        await writer.send(message)


class MCPServer(FastMCP):
    async def run_sse_async(self) -> None:
        """Run the server using SSE transport."""
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SSEServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await self._mcp_server.run(
                    streams[0],
                    streams[1],
                    self._mcp_server.create_initialization_options(),
                )

        starlette_app = Starlette(
            debug=self.settings.debug,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        config = uvicorn.Config(
            starlette_app,
            host=self.settings.host,
            port=self.settings.port,
            log_level=self.settings.log_level.lower(),
        )
        server = uvicorn.Server(config)
        await server.serve()
