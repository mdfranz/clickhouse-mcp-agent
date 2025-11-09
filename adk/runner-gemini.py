#!/usr/bin/env python

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StreamableHTTPConnectionParams,
)
from google.genai import types

# Set up a logger for the application
logger = logging.getLogger("mcp_agent_app")


def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(log_level)

    # Prevent logging from propagating to the root logger
    logger.propagate = False

    # Configure file handler
    file_handler = logging.FileHandler("mcp_agent_app.log", mode="a")
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)  # Log everything to the file

    # Configure console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)

    # Add handlers to the logger
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)


# Configuration constants
APP_NAME = "mcp_agent_app"
USER_ID = "user"
DEFAULT_MODEL_ID = "gemini-2.0-flash-exp"
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")

# Available model configurations
AVAILABLE_MODELS = {
    "gemini-flash": "gemini-2.0-flash-exp",
    "gemini-pro": "gemini-2.5-pro",
    "gemini-pro-latest": "gemini-pro-latest",
    "gemini-flash-latest": "gemini-flash-latest",
}


class ClickHouseAgentRunner:
    """Manages the ClickHouse agent with configurable model support."""

    def __init__(self, model_id: str = DEFAULT_MODEL_ID, mcp_url: str = MCP_SERVER_URL):
        """Initialize the agent runner with specified model.

        Args:
            model_id: The model ID to use for the agent.
            mcp_url: The MCP server URL.
        """
        self.model_id = model_id
        self.mcp_url = mcp_url

        # Initialize MCP toolset
        self.tools = McpToolset(
            connection_params=StreamableHTTPConnectionParams(url=self.mcp_url)
        )

        # Configure ClickHouse agent
        self.agent = Agent(
            name="clickhouse_agent",
            tools=[self.tools],
            model=self.model_id,
            description="An agent that writes and executes ClickHouse queries via an MCP tool.",
            instruction="""
            You are a ClickHouse query expert.
            Use the provided tools to construct and execute ClickHouse queries based on the user's request.
            Provide clear explanations of the queries you construct and the results you obtain.
            """,
        )

        # Initialize runner
        self.runner = InMemoryRunner(
            agent=self.agent,
            app_name=APP_NAME,
        )

        logger.debug(f"Initialized ClickHouseAgentRunner with model: {self.model_id}")

    async def create_session(self) -> Session:
        """Creates a new asynchronous session.

        Returns:
            Session: The newly created session object.

        Raises:
            Exception: If session creation fails.
        """
        logger.debug("Creating new session...")
        try:
            session = await self.runner.session_service.create_session(
                app_name=APP_NAME, user_id=USER_ID
            )
            logger.debug(f"Session created successfully: {session.id}")
            return session
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise

    async def query_agent(self, prompt: str, session_id: str) -> None:
        """Queries the agent asynchronously and streams the response.

        Args:
            prompt: The user's query/prompt.
            session_id: The session ID to use for the query.

        Raises:
            Exception: If the query fails.
        """
        logger.debug(f"User query: {prompt}")
        logger.info(f"\n** User: {prompt}\n")

        try:
            response_stream = self.runner.run_async(
                new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
                user_id=USER_ID,
                session_id=session_id,
            )

            # Process streaming response
            async for message in response_stream:
                if message.content and message.content.parts:
                    for part in message.content.parts:
                        if part.text:
                            logger.info(f"** {message.author}: {part.text}\n")
                        # Handle other part types if needed
                        elif hasattr(part, "function_call"):
                            logger.debug(f"Function call: {part.function_call}")

        except Exception as e:
            logger.error(f"Error during agent query: {e}")
            raise
        finally:
            # Ensure proper cleanup of the stream
            try:
                await response_stream.aclose()
            except Exception as e:
                logger.warning(f"Error closing response stream: {e}")


def resolve_model_id(model_name: str) -> str:
    """Resolve a model name to its full model ID.

    Args:
        model_name: Short name or full model ID.

    Returns:
        The full model ID.
    """
    # If it's a key in AVAILABLE_MODELS, return the mapped value
    if model_name in AVAILABLE_MODELS:
        return AVAILABLE_MODELS[model_name]

    # If it looks like a full model ID (contains "gemini"), use it directly
    if "gemini" in model_name.lower():
        return model_name

    # Default fallback
    logger.warning(f"Unknown model '{model_name}', using default: {DEFAULT_MODEL_ID}")
    return DEFAULT_MODEL_ID


async def main(args: argparse.Namespace) -> None:
    """Main async function to run the agent.

    Args:
        args: Command line arguments.
    """
    try:
        # Resolve model ID
        model_id = resolve_model_id(args.model)
        logger.info(f"=== Using Model: {model_id} ===")
        logger.debug(f"MCP Server URL: {args.mcp_url}")

        # Create agent runner with specified model
        agent_runner = ClickHouseAgentRunner(model_id=model_id, mcp_url=args.mcp_url)

        # Create session
        session = await agent_runner.create_session()

        if args.prompt:
            # Single-shot mode
            await agent_runner.query_agent(args.prompt.strip(), session_id=session.id)
        else:
            # Interactive mode
            logger.info("Entering interactive mode. Type 'exit' or 'quit' to end.")
            while True:
                try:
                    user_prompt = input("User > ").strip()
                    if user_prompt.lower() in ["exit", "quit"]:
                        break
                    if not user_prompt:
                        continue
                    await agent_runner.query_agent(user_prompt, session_id=session.id)
                except (EOFError, KeyboardInterrupt):
                    break
            logger.info("\nExiting interactive mode.")

        logger.debug("Agent query completed successfully")

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="ClickHouse Agent Runner")
    parser.add_argument(
        "model",
        nargs="?",
        default="gemini-flash",
        help=(
            "Model name or ID to use (e.g., 'gemini-flash', 'gemini-pro'). "
            f"Default: {DEFAULT_MODEL_ID}"
        ),
    )
    parser.add_argument(
        "--mcp-url",
        default=MCP_SERVER_URL,
        help=f"MCP server URL. Default: {MCP_SERVER_URL}",
    )
    parser.add_argument(
        "--prompt",
        help="Run in non-interactive mode with a single prompt.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging for debugging.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
