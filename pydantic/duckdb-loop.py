#!/usr/bin/env python

import logging
import os
import sys

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from pydantic_ai.mcp import MCPServerSSE
from pydantic_ai.providers.ollama import OllamaProvider

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="agent.log",
)

logging.info("Starting agent...")


class DuckDBAgent:
    def __init__(self, model_name: str):
        logging.info(f"Initializing DuckDBAgent with model: {model_name}")

        self.server = MCPServerSSE(
            os.getenv("MCP_URL", "http://127.0.0.1:8000/sse"),max_retries=5
        )
        logging.info("MCP Server initialized.")

        self.agent = Agent(
            model_name,
            toolsets=[self.server],
            retries=5,
            instructions=(
                "You are a data analyst. You will be asked to analyze data from a DuckDB database."
                " You can use the MotherDuck MCP Server to execute SQL queries."
                " Only show me the results not the queries themselves."
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
        print("Usage: python duckdb-sync.py <model_name>", file=sys.stderr)
        print("\t\t models: ollama:qwen3:14b gpt-5-mini gemini-2.5-pro")
        print("\nSee https://ai.pydantic.dev/models/overview/ for examples")
        sys.exit(1)

    model_name = sys.argv[1]

    if model_name.find("ollama") > -1:
        if "OLLAMA_BASE_URL" not in os.environ:
            print("Set OLLAMA_BASE_URL to http://1.2.3.4:11434/v1")
            sys.exit(1)

    duckdb_agent_instance = DuckDBAgent(model_name)

    print("Enter your queries. Type 'exit' or 'quit' to end the session.")
    while True:
        try:
            user_query = input("DuckDB Query (or 'exit'/'quit'): ")
            if user_query.lower() in ["exit", "quit"]:
                print("Exiting session.")
                break
            if not user_query.strip():
                print("Query cannot be empty. Please enter a query.")
                continue

            result = duckdb_agent_instance.run_query(user_query)
            print("\n" + result.output)
            print(result.usage())
        except Exception as e:
            logging.error(f"An error occurred during query execution: {e}")
            print(f"An error occurred: {e}")



