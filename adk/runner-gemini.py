import asyncio
import logging
import sys
from typing import Optional

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)
from google.genai import types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="mcp_agent_app.log",  # Log to a file named mcp_agent_app.log
    filemode="a",  # Append to the log file if it exists
)
logger = logging.getLogger(__name__)

# Configuration constants
APP_NAME = "mcp_agent_app"
USER_ID = "user"
MODEL_ID = "gemini-2.5-pro"
MCP_SERVER_URL = "http://localhost:8000/mcp"
# Initialize MCP toolset\\
tools = MCPToolset(connection_params=StreamableHTTPConnectionParams(url=MCP_SERVER_URL))

# Configure ClickHouse agent
clickhouse_agent = Agent(
    name="clickhouse_agent",
    tools=[tools],
    model=MODEL_ID,
    description="An agent that writes and executes ClickHouse queries via an MCP tool.",
    instruction="""
    You are a ClickHouse query expert.
    Use the provided tools to construct and execute ClickHouse queries based on the user's request.
    Provide clear explanations of the queries you construct and the results you obtain.
    """,
)

# Initialize runner
runner = InMemoryRunner(
    agent=clickhouse_agent,
    app_name=APP_NAME,
)


async def create_session() -> Session:
    """Creates a new asynchronous session.

    Returns:
        Session: The newly created session object.

    Raises:
        Exception: If session creation fails.
    """
    logger.info("Creating new session...")
    try:
        session = await runner.session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID
        )
        logger.info(f"Session created successfully: {session.id}")
        return session
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise


async def query_agent(prompt: str, session_id: str) -> None:
    """Queries the agent asynchronously and streams the response.

    Args:
        prompt: The user's query/prompt.
        session_id: The session ID to use for the query.

    Raises:
        Exception: If the query fails.
    """
    logger.info(f"User query: {prompt}")
    print(f"\n** User: {prompt}\n")

    try:
        response_stream = runner.run_async(
            new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
            user_id=USER_ID,
            session_id=session_id,
        )

        # Process streaming response
        async for message in response_stream:
            if message.content and message.content.parts:
                for part in message.content.parts:
                    if part.text:
                        print(f"** {message.author}: {part.text}\n")
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


async def main(custom_prompt: Optional[str] = None) -> None:
    """Main async function to run the agent.

    Args:
        custom_prompt: Optional custom prompt to use instead of default.
    """
    try:
        # Create session
        session = await create_session()

        # Use custom prompt or default
        user_prompt = (
            custom_prompt
            or """
        Using file('/tmp/mcp/data/**/*.log.gz', 'JSONEachRow') as a data source you will find JSON compressed files.
        Find and count the different types of events based on event_type.
        Then find the number of SSH logins based on the auth event_type.
        Lastly find the number of unique users that logged in via SSH.
        """
        )

        # Query the agent
        await query_agent(user_prompt.strip(), session_id=session.id)

        logger.info("Agent query completed successfully")

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
