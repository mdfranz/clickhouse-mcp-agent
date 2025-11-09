import logging
import sys

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

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
        self.server = MCPServerStreamableHTTP("http://localhost:8000/mcp")
        logging.info("MCP Server initialized.")

        self.agent = Agent(
            model_name,
            toolsets=[self.server],
            instructions=(
                "Using file('/tmp/mcp/data/**/*.log.gz', 'JSONEachRow') as a data source you"
                " will find JSON compressed files for multiple events captured from Linux systems"
                " by creating ClickHouse SQL queries using the ClickHouse MCP Server. Only show me the results not the queries themselves."
            ),
        )
        logging.info("Pydantic AI Agent created.")

    def run_query(self, query_string: str):
        logging.info(f"Running query: {query_string}")
        result = self.agent.run_sync(query_string)
        logging.info(f"Agent run complete. Result output: {result.output}")
        return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chdb-sync.py <model_name>", file=sys.stderr)
        sys.exit(1)

    model_name = sys.argv[1]
    chdb_agent_instance = ChdbAgent(model_name)
    result = chdb_agent_instance.run_query(
        "Count the number of different types of events based on the the event_type field"
    )
    print(result.output)
    print(result.usage())
