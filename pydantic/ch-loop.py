#!/usr/bin/env python

import logging
import os
import sys

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

# See the settings to run the MCP server

"""
    export CLICKHOUSE_HOST=localhost
    export CLICKHOUSE_PORT=8123
    export CLICKHOUSE_USER=default
    export CLICKHOUSE_PASSWORD=secret_password
    export CLICKHOUSE_MCP_SERVER_TRANSPORT=http
    export CLICKHOUSE_MCP_BIND_PORT=8989
    export CLICKHOUSE_SECURE=false

    uv run --with mcp-clickhouse mcp-clickhouse
"""



# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="ch-agent.log",
)

logging.info("Starting agent...")


class ClickhouseAgent:
    def __init__(self, model_name: str):
        logging.info(f"Initializing ClickhouseAgent with model: {model_name}")

        self.server = MCPServerStreamableHTTP(
            os.getenv("MCP_URL", "http://localhost:8989/mcp")
        )
        logging.info("MCP Server initialized.")

        self.agent = Agent(
            model_name,
            toolsets=[self.server],
            retries=5,
            instructions=(
                "Query the table specified in the prompt looking for security events by creating ClickHouse SQL queries using the ClickHouse MCP Server.",
                "Show both the query and the results"
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
        print("Usage: python ch-loop.py <model_name>", file=sys.stderr)
        print("\t\t models: ollama:qwen3:14b gpt-5-mini gemini-2.5-pro")
        print("\nSee https://ai.pydantic.dev/models/overview/ for examples")
        sys.exit(1)

    model_name = sys.argv[1]

    if model_name.find("ollama") > -1:
        if "OLLAMA_BASE_URL" not in os.environ:
            print("Set OLLAMA_BASE_URL to http://1.2.3.4:11434/v1")
            sys.exit(1)

    clickhouse_agent_instance = ClickhouseAgent(model_name)

    print("Enter your queries. Type 'exit' or 'quit' to end the session.")
    while True:
        try:
            user_query = input("ClickHouse Query (or 'exit'/'quit'): ")
            if user_query.lower() in ["exit", "quit"]:
                print("Exiting session.")
                break
            if not user_query.strip():
                print("Query cannot be empty. Please enter a query.")
                continue

            result = clickhouse_agent_instance.run_query(user_query)
            print("\n" + result.output)
            print(result.usage())
        except Exception as e:
            logging.error(f"An error occurred during query execution: {e}")
            print(f"An error occurred: {e}")
