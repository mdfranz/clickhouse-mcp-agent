
# DuckDB Usage

## MCP Server

```
mfranz@asus-pn50:~/suricata$ uvx mcp-server-motherduck --db-path ./subset.db --transport sse --port 8000 --host 0.0.0.0
[motherduck] INFO - 🦆 MotherDuck MCP Server v0.8.0
[motherduck] INFO - Ready to execute SQL queries via DuckDB/MotherDuck
[motherduck] INFO - Query result limits: 1024 rows, 50,000 characters
[motherduck] INFO - Query timeout: disabled
[motherduck] INFO - Starting MotherDuck MCP Server
[motherduck] INFO - Database client initialized in `duckdb` mode
[motherduck] INFO - 🔌 Connecting to duckdb database
[motherduck] INFO - ✅ Successfully connected to duckdb database
[motherduck] INFO - Registering handlers
[motherduck] INFO - MCP server initialized in sse mode
[motherduck] INFO - 🦆 Connect to MotherDuck MCP Server at http://0.0.0.0:8000/sse
[uvicorn]    INFO - Started server process [1781512]
[uvicorn]    INFO - Waiting for application startup.
[uvicorn]    INFO - Application startup complete.
[uvicorn]    INFO - Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Client

Set `MCP_URL`

```
export MCP_URL=http://asus-pn50:8000/sse
```

```
./duckdb-loop.py gemini-3-flash-preview

DuckDB Query (or 'exit'/'quit'): find all the linux servers baed on DNS lookups to security.ubuntu.com

Based on DNS lookups to `security.ubuntu.com`, the following 25 IP addresses have been identified as Linux (Ubuntu) servers:

*   192.168.2.100
*   192.168.2.119
*   192.168.2.128
*   192.168.2.129
*   192.168.2.138
*   192.168.2.160
*   192.168.2.161
*   192.168.2.169
*   192.168.2.173
*   192.168.2.176
*   192.168.2.179
*   192.168.2.180
*   192.168.2.197
*   192.168.2.201
*   192.168.2.204
*   192.168.2.206
*   192.168.2.210
*   192.168.2.227
*   192.168.2.232
*   192.168.2.238
*   192.168.2.239
*   192.168.2.254
*   192.168.3.122
*   192.168.3.240
*   192.168.4.174
RunUsage(input_tokens=13602, cache_read_tokens=5994, output_tokens=1100, details={'thoughts_tokens': 461, 'text_prompt_tokens': 13602, 'cached_content_tokens': 5994, 'text_cache_tokens': 5994}, requests=7, tool_calls=6)
DuckDB Query (or 'exit'/'quit'): find the top 10 most common DNS queries from 192.168.2.100
```

The top 10 most common DNS queries from the IP address **192.168.2.100** are as follows:

| Query | Count |
| :--- | :--- |
| s3.us-east-1.amazonaws.com | 52,946 |
| cdn.fwupd.org | 960 |
| motd.ubuntu.com | 572 |
| archive.ubuntu.com | 256 |
| security.ubuntu.com | 240 |
| pkgs.tailscale.com | 238 |
| esm.ubuntu.com | 238 |
| repo.radeon.com | 238 |
| apt.vector.dev | 238 |
| _http._tcp.archive.ubuntu.com | 157 |
RunUsage(input_tokens=9047, cache_read_tokens=2012, output_tokens=844, details={'thoughts_tokens': 478, 'text_prompt_tokens': 9047, 'cached_content_tokens': 2012, 'text_cache_tokens': 2012}, requests=5, tool_calls=4) 
