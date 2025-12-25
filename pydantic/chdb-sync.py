#!/usr/bin/env python

import logging
import os
import sys

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from pydantic_ai.providers.ollama import OllamaProvider

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="agent.log",
)

logging.info("Starting agent...")


class ChdbAgent:
    def __init__(self, model_name: str):
        logging.info(f"Initializing ChdbAgent with model: {model_name}")

        self.server = MCPServerStreamableHTTP(
            os.getenv("MCP_URL", "http://localhost:8000/mcp")
        )
        logging.info("MCP Server initialized.")

        self.agent = Agent(
            model_name,
            toolsets=[self.server],
            instructions=(
                "Using file('./**/*.log.gz', 'JSONEachRow') as a data source you will find JSON compressed files for multiple events captured from Linux systems"
                "by creating ClickHouse SQL queries using the ClickHouse MCP Server. Only show me the results not the queries themselves."
            ),
        )
        logging.info("Pydantic AI Agent created.")

    def run_query(self, query_string: str):
        logging.info(f"Running query: {query_string}")
        result = self.agent.run_sync(query_string)
        logging.info(f"Agent run complete. Result output: {result.output}")
        logging.info(f"Agent run complete. Usage output: {result.usage()}")
        return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chdb-sync.py <model_name>", file=sys.stderr)
        print("\t\t models: ollama:qwen3:14b gpt-5-mini gemini-2.5-pro")
        print("\nSee https://ai.pydantic.dev/models/overview/ for examples")
        sys.exit(1)

    model_name = sys.argv[1]

    if model_name.find("ollama") > -1:
        if "OLLAMA_BASE_URL" not in os.environ:
            print("Set OLLAMA_BASE_URL to http://1.2.3.4:11434/v1")
            sys.exit(1)

    chdb_agent_instance = ChdbAgent(model_name)
    result = chdb_agent_instance.run_query(
        "Count the number of different types of events based on the the event_type field"
    )
    print(result.output)
    print(result.usage())

    result = chdb_agent_instance.run_query(
        "Now find the number number of SSH logins based on the auth event_type."
        "Lastly find the number of unique users that logged in via SSH and the source IPs they logged in from."
    )
    print(result.output)
    print(result.usage())
