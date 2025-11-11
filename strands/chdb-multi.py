#!/usr/bin/env python


import logging
import os
import sys

from mcp.client.streamable_http import streamablehttp_client
from strands.models.gemini import GeminiModel
from strands.models.ollama import OllamaModel
from strands.models.openai import OpenAIModel
from strands.tools.mcp import MCPClient

from strands import Agent

instructions = """
Using file('/tmp/mcp/data/**/*.log.gz', 'JSONEachRow') as a data source you will find JSON compressed files for multiple events captured from Linux systems
by creating ClickHouse SQL queries using the ClickHouse MCP Server. Only show me the results not the queries themselves.
"""

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="chdb-multi.log",
    filemode="w",
)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: foo.py <model>")
        sys.exit(-1)

    raw_model = sys.argv[1]
    logging.debug(f"Using model: {raw_model}")

    if raw_model.find("gemini") > -1:
        agent_model = GeminiModel(
            client_args={"api_key": os.environ["GOOGLE_API_KEY"]}, model_id=raw_model
        )
    elif raw_model.find("gpt") > -1:
        agent_model = OpenAIModel(
            client_args={"api_key": os.environ["OPENAI_API_KEY"]}, model_id=raw_model
        )
    else:
        # Assume Ollama
        agent_model = OllamaModel(
            host=f"http://{os.environ['OLLAMA_HOST']}",
            model_id=raw_model,
            streaming=False,
        )

    mcp_url = os.getenv("MCP_URL", "http://localhost:8000/mcp")
    streamable_http_mcp_client = MCPClient(lambda: streamablehttp_client(mcp_url))

    # Manual approach
    try:
        with streamable_http_mcp_client:
            tools = streamable_http_mcp_client.list_tools_sync()
            agent = Agent(tools=tools, system_prompt=instructions, model=agent_model)

            logging.debug("Running first query...")
            result = agent(
                "Count the number of different types of events based on the the event_type field"
            )
            print(result)
            logging.debug(f"First result: {result}")

            logging.debug("Running second query...")
            result = agent(
                "Now find the number number of SSH logins based on the auth event_type."
                "Lastly find the number of unique users that logged in via SSH and the source IPs they logged in from."
            )
            print(result)
            logging.debug(f"Second result: {result}")
    except Exception as e:
        print(f"Failed to connect to MCP server at {mcp_url}: {e}", file=sys.stderr)
        logging.error(f"Failed to connect to MCP server at {mcp_url}: {e}")
        sys.exit(1)
