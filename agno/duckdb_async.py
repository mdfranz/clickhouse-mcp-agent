#!/usr/bin/env python

import asyncio
import sys
import time

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools

#
# Assumptions
# uv run --with mcp-clickhouse mcp-clickhouse
# export CLICKHOUSE_ENABLED=false
# export CHDB_DATA_PATH=data
# export CHDB_ENABLED=true
# export CLICKHOUSE_MCP_SERVER_TRANSPORT=http
#


async def main(data_question, model):
    async with MCPTools(
        transport="sse",
        url="http://127.0.0.1:8989/sse",
        timeout_seconds=60,
    ) as mcp_tools:
        if model == "claude":
            my_model = Claude(id="claude-sonnet-4-20250514")
        elif model == "gemini":
            my_model = Gemini(id="gemini-2.5-pro")
        elif model.find("gpt") > -1:
            my_model = OpenAIChat(id=model)
        else:
            my_model = Ollama(id=model)

        agent = Agent(
            model=my_model,
            debug_mode=True,
            markdown=True,
            tools=[mcp_tools],
        )
        await agent.aprint_response(data_question, stream=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: foo.py <model>")
        print("Example: foo.py claude")
        print("Supported models: claude, gemini, gpt-*, ollama_model_name")
        sys.exit(1)
    model = sys.argv[1]
    print(f"Selected {model}")
    time.sleep(3)

    while True:
        prompt = input("Enter your data question (or type 'quit' or 'exit' to stop): ")
        if prompt.lower() in ["quit", "exit"]:
            print("Exiting.")
            break
        print("-" * 50) # Separator for readability
        asyncio.run(main(prompt, model))
        print("-" * 50) # Separator for readability
