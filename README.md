![ADK](clickhouse-adk.png)

# What is this

This is testing [ClickHouse MCP Server](https://github.com/ClickHouse/mcp-clickhouse) with both [Agno](https://docs.agno.com/introduction) and [Google ADK](https://google.github.io/adk-docs/)


# Example Prompt

- Using file('/tmp/mcp/data/**/*.log.gz', 'JSONEachRow') as a data source you will find JSON compressed files for multiple events captured from Linux systems.
- Find and count the different type of events based on event_type. 
- Then find the number number of SSH logins based on the auth event_type. 
- Lastly find the number of unique users that logged in via SSH and the source IPs they logged in as.


# Running a standalone MCP server

Set environment variables

```
export CLICKHOUSE_ENABLED=false
export CHDB_DATA_PATH=data
export CHDB_ENABLED=true
export CLICKHOUSE_MCP_SERVER_TRANSPORT=http
```

```
uv run --with mcp-clickhouse mcp-clickhouse
```

# References
- https://github.com/ClickHouse/mcp-clickhouse
- https://clickhouse.com/blog/integrating-clickhouse-mcp
- https://www.youtube.com/watch?v=rvkOpKhPWvQ
