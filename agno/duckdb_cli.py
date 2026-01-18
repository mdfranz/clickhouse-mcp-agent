#!/usr/bin/env python

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def resolve_model(model_name: str):
    if model_name == "claude":
        return Claude(id="claude-sonnet-4-20250514")
    if model_name == "gemini":
        return Gemini(id="gemini-2.5-pro")
    if "gpt" in model_name:
        return OpenAIChat(id=model_name)
    return Ollama(id=model_name)


def init_sqlite_db() -> SqliteDb:
    """Mirror the cookbook example by persisting sessions to SQLite."""
    db_path = Path(os.getenv("DUCKDB_CLI_SQLITE_DB", "data/duckdb_cli.sqlite"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return SqliteDb(db_file=str(db_path))


async def main(model_name: str) -> None:
    sqlite_db = init_sqlite_db()

    mcp_url = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")
    logger.info(f"Connecting to MCP at {mcp_url}...")

    try:
        async with MCPTools(
            transport="streamable-http",
            url=mcp_url,
            timeout_seconds=60,
        ) as mcp_tools:
            agent = Agent(
                model=resolve_model(model_name),
                instructions="Execute DuckDB SQL queries as needed to get the answer. You do not need to show the SQL",
                debug_mode=False,
                markdown=False,
                tools=[mcp_tools],
                db=sqlite_db,
                add_history_to_context=True,
                add_datetime_to_context=True,
            )
            await agent.acli_app(markdown=False)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DuckDB CLI Agent")
    parser.add_argument(
        "model",
        help="Model to use (claude, gemini, gpt-*, ollama_model_name)",
        nargs="?",  # Make it optional to allow showing help easily, though logic requires it
        default=None,
    )

    args = parser.parse_args()

    if not args.model:
        parser.print_help()
        sys.exit(1)

    print(f"Selected {args.model}")
    asyncio.run(main(args.model))
