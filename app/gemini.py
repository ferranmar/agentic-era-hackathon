import json
import logging
from collections.abc import Callable
from typing import Any

from fastapi import WebSocket
from google.cloud import logging as google_cloud_logging
from google.genai import types
from google.genai.live import AsyncSession
from google.genai.types import LiveServerToolCall
from websockets.exceptions import ConnectionClosedError

logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
logging.basicConfig(level=logging.INFO)


class GeminiSession:
    """Manages bidirectional communication between a client and the Gemini model."""

    def __init__(
        self,
        session: AsyncSession,
        websocket: WebSocket,
        tool_functions: dict[str, Callable],
    ) -> None:
        """Initialize the Gemini session.

        Args:
            session: The Gemini session
            websocket: The client websocket connection
            user_id: Unique identifier for this client
            tool_functions: Dictionary of available tool functions
        """
        self.session = session
        self.websocket = websocket
        self.run_id = "n/a"
        self.user_id = "n/a"
        self.tool_functions = tool_functions

    async def receive_from_client(self) -> None:
        """Listen for and process messages from the client.

        Continuously receives messages and forwards audio data to Gemini.
        Handles connection errors gracefully.
        """
        while True:
            try:
                data = await self.websocket.receive_json()
                if isinstance(data, dict) and (
                    "realtimeInput" in data or "clientContent" in data
                ):
                    await self.session._ws.send(json.dumps(data))
                elif "setup" in data:
                    self.run_id = data["setup"]["run_id"]
                    self.user_id = data["setup"]["user_id"]
                    logger.log_struct(
                        {**data["setup"], "type": "setup"}, severity="INFO"
                    )
                else:
                    logging.warning(
                        f"Received unexpected input from client: {data}"
                    )
            except ConnectionClosedError as e:
                logging.warning(
                    f"Client {self.user_id} closed connection: {e}"
                )
                break
            except Exception as e:
                logging.error(
                    f"Error receiving from client {self.user_id}: {e!s}"
                )
                break

    def _get_func(self, action_label: str) -> Callable | None:
        """Get the tool function for a given action label."""
        return (
            None
            if action_label == ""
            else self.tool_functions.get(action_label)
        )

    async def _handle_tool_call(
        self, session: Any, tool_call: LiveServerToolCall
    ) -> None:
        """Process tool calls from Gemini and send back responses.

        Args:
            session: The Gemini session
            tool_call: Tool call request from Gemini
        """
        for fc in tool_call.function_calls:
            logging.debug(
                f"Calling tool function: {fc.name} with args: {fc.args}"
            )
            response = self._get_func(fc.name)(**fc.args)
            tool_response = types.LiveClientToolResponse(
                function_responses=[
                    types.FunctionResponse(
                        name=fc.name, id=fc.id, response=response
                    )
                ]
            )
            logging.debug(f"Tool response: {tool_response}")
            await session.send(input=tool_response)

    async def receive_from_gemini(self) -> None:
        """Listen for and process messages from Gemini.

        Continuously receives messages from Gemini, forwards them to the client,
        and handles any tool calls. Handles connection errors gracefully.
        """
        while result := await self.session._ws.recv(decode=False):
            await self.websocket.send_bytes(result)
            message = types.LiveServerMessage.model_validate(
                json.loads(result)
            )
            if message.tool_call:
                tool_call = LiveServerToolCall.model_validate(
                    message.tool_call
                )
                await self._handle_tool_call(self.session, tool_call)
