#!/usr/bin/env python

import asyncio
import sys

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools


def resolve_model(model_name: str):
    if model_name == "claude":
        return Claude(id="claude-sonnet-4-20250514")
    if model_name == "gemini":
        return Gemini(id="gemini-2.5-pro")
    if "gpt" in model_name:
        return OpenAIChat(id=model_name)
    return Ollama(id=model_name)


async def main(model_name: str) -> None:
    async with MCPTools(
        transport="streamable-http",
        url="http://127.0.0.1:8000/mcp",
        timeout_seconds=60,
    ) as mcp_tools:
        agent = Agent(
            model=resolve_model(model_name),
            instructions="Excecute DuckDB SQL queries as needed to get the answer. You do not need to show the SQL",
            debug_mode=True,
            markdown=True,
            tools=[mcp_tools],
        )
        await agent.acli_app(markdown=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: duckdb_cli.py <model>")
        print("Example: duckdb_cli.py claude")
        print("Supported models: claude, gemini, gpt-*, ollama_model_name")
        sys.exit(1)

    selected_model = sys.argv[1]
    print(f"Selected {selected_model}")
    asyncio.run(main(selected_model))
