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
