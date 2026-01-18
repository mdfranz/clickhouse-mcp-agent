#!/usr/bin/env python

import json
import logging
import os
import sys
import time

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
        self.model_name = model_name

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
                "Show both the query and the results",
            ),
        )
        logging.info("Pydantic AI Agent created.")
        self.usage_log_path = os.getenv("MCP_USAGE_LOG_PATH", "ch-agent-usage.jsonl")

    def run_query(self, query_string: str):
        logging.info(f"Running query: {query_string}")
        start_time = time.perf_counter()
        result = self.agent.run_sync(query_string)
        duration = time.perf_counter() - start_time
        logging.info(
            "Agent run complete in %.3f seconds. Result output: %s",
            duration,
            result.output,
        )
        logging.info("Agent run complete. Usage output: %s", result.usage())
        self._record_usage(query_string, duration, result.usage())
        return result, duration

    def _record_usage(self, query_string: str, duration: float, usage) -> None:
        usage_dict = self._usage_to_dict(usage)
        record = {
            "timestamp": time.time(),
            "model": self.model_name,
            "query": query_string,
            "duration_seconds": duration,
            "usage": usage_dict,
        }
        with open(self.usage_log_path, "a", encoding="utf-8") as f:
            json.dump(record, f)
            f.write("\n")

    @staticmethod
    def _usage_to_dict(usage) -> dict:
        if usage is None:
            return {}
        if isinstance(usage, dict):
            return usage
        for attr in ("model_dump", "dict"):
            fn = getattr(usage, attr, None)
            if callable(fn):
                try:
                    return fn()
                except Exception:
                    continue
        return {"usage_repr": repr(usage)}


def load_prompts_from_path(prompt_path: str):
    if os.path.isdir(prompt_path):
        prompts = []
        for filename in sorted(os.listdir(prompt_path)):
            file_path = os.path.join(prompt_path, filename)
            if not os.path.isfile(file_path):
                continue
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content:
                logging.warning("Prompt file %s is empty; skipping", file_path)
                continue
            prompts.append((filename, content))
        return prompts
    if os.path.isfile(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        return [(os.path.basename(prompt_path), content)] if content else []
    raise FileNotFoundError(f"Prompt path not found: {prompt_path}")


def run_prompts(clickhouse_agent_instance: ClickhouseAgent, prompt_path: str):
    is_file = os.path.isfile(prompt_path)
    is_dir = os.path.isdir(prompt_path)
    if not is_file and not is_dir:
        print(f"Prompt path not found: {prompt_path}", file=sys.stderr)
        sys.exit(1)

    if is_file and not is_dir:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read().strip()
        if not prompt_text:
            print(f"Prompt file {prompt_path} is empty", file=sys.stderr)
            sys.exit(1)
        prompts = [(os.path.basename(prompt_path), prompt_text)]
    else:
        try:
            prompts = load_prompts_from_path(prompt_path)
        except FileNotFoundError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)

        if not prompts:
            print(f"No prompts found in {prompt_path}", file=sys.stderr)
            sys.exit(1)

    for prompt_name, prompt_text in prompts:
        print(f"\nRunning prompt '{prompt_name}'")
        try:
            result, duration = clickhouse_agent_instance.run_query(prompt_text)
            print(f"Completed in {duration:.3f} seconds")
            print(result.output)
            print(result.usage())
        except Exception as e:
            logging.error("Error running prompt %s: %s", prompt_name, e)
            print(f"Error running prompt '{prompt_name}': {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ch-loop.py <model_name> [prompt_path]", file=sys.stderr)
        print("\t\t models: ollama:qwen3:14b gpt-5-mini gemini-2.5-pro")
        print("\nSee https://ai.pydantic.dev/models/overview/ for examples")
        sys.exit(1)

    model_name = sys.argv[1]
    prompt_path = sys.argv[2] if len(sys.argv) >= 3 else None

    if model_name.find("ollama") > -1:
        if "OLLAMA_BASE_URL" not in os.environ:
            print("Set OLLAMA_BASE_URL to http://1.2.3.4:11434/v1")
            sys.exit(1)

    clickhouse_agent_instance = ClickhouseAgent(model_name)

    if prompt_path:
        run_prompts(clickhouse_agent_instance, prompt_path)
        sys.exit(0)

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

            result, duration = clickhouse_agent_instance.run_query(user_query)
            print(f"\nCompleted in {duration:.3f} seconds")
            print(result.output)
            print(result.usage())
        except Exception as e:
            logging.error(f"An error occurred during query execution: {e}")
            print(f"An error occurred: {e}")
