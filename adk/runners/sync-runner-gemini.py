from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)
from google.genai import types

APP_NAME = "ollama"
USER_ID = "user"
SESSION_ID = "session"
MODEL_ID = "gemini-2.5-pro"

tools = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url="http://localhost:8000/mcp")
)

dumb_agent = Agent(
    name="dumb",
    tools=[tools],
    model=MODEL_ID,
    description="Clickhouse Instructions",
    instruction="""
      Create the necessary clickhouse query using the Tools
    """,
)

runner = InMemoryRunner(
    agent=dumb_agent,
    app_name=APP_NAME,
)


def create_session():
    session = runner.session_service.create_session_sync(
        app_name=APP_NAME, user_id=USER_ID
    )
    return session


def query_agent(prompt: str, session_id: str):
    print("** User:", prompt)

    response = runner.run(
        new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
        user_id=USER_ID,
        session_id=session_id,
    )
    for message in response:
        if message.content.parts and message.content.parts[0].text:
            print(f"** {message.author}: {message.content.parts[0].text}\n")


if __name__ == "__main__":
    session = create_session()
    user_prompt = """ Using file('/tmp/mcp/data/**/*.log.gz', 'JSONEachRow') as a data source you will find JSON compressed files.                                                                                         ┃
    Find and count the different type of events based on event_type. Then find the number number of SSH logins based on the auth event_type. Lastly find the number of unique users that logged in via SSH
    """
    query_agent(user_prompt, session_id=session.id)
