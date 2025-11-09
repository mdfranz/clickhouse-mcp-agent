from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)

tools = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url="http://localhost:8000/mcp")
)

root_agent = Agent(
    name="chdb_gemini",
    model="gemini-2.5-pro",
    tools=[tools],
    description="Clickhouse Instructions",
    instruction="""Create the necessary clickhouse query using the Tools to be able to query ClickHouse compressed JSON data""",
)
