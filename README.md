# Weather MCP

A Model Context Protocol (MCP) server that provides weather alerts from the National Weather Service (NWS) API, integrated with an interactive chat client powered by LangChain and Groq.

## Overview

This project implements an MCP server that exposes weather alert functionality, allowing AI agents to query active weather alerts for US states. The server uses FastMCP for easy tool definition and integrates with the National Weather Service API.

## Features

- 🌦️ **Weather Alerts**: Get active weather alerts for any US state
- 🤖 **MCP Integration**: Standard MCP server implementation using FastMCP
- 💬 **Interactive Chat Client**: Chat interface using LangChain and Groq LLM
- 🔧 **Token Management**: Built-in token usage optimization for Groq free tier (8000 TPM)
- 📊 **Tool Result Logging**: Detailed logging of tool calls and results
- 🧠 **Conversation Memory**: Optional conversation history with automatic clearing

## Project Structure

```
weather-mcp/
├── server/
│   ├── weather.py      # MCP server implementation
│   ├── weather.json    # MCP server configuration
│   └── client.py       # Interactive chat client
├── main.py             # Entry point
├── pyproject.toml      # Project dependencies
└── README.md          # This file
```

## Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Groq API key (get one at [console.groq.com](https://console.groq.com))

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd weather-mcp
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

## Configuration

The MCP server is configured in `server/weather.json`. Update the path in the `args` array if your project is located elsewhere:

```json
{
    "mcpServers": {
      "weather": {
        "command": "uv",
        "args": [
          "--directory",
          "/path/to/weather-mcp",
          "run",
          "server/weather.py"
        ]
      }
    }
}
```

## Usage

### Running the Chat Client

Start the interactive chat client:

```bash
uv run server/client.py
```

The client will:
- Initialize the MCP server connection
- Start an interactive chat session
- Automatically manage conversation history to stay within token limits
- Log tool calls and results for debugging

### Example Queries

Once the chat is running, you can ask questions like:

- "What are the weather alerts for California?"
- "Get weather alerts for NY"
- "Show me alerts for Texas, limit to 5"

### Commands

- `exit` or `quit`: End the conversation
- `clear`: Manually clear conversation history

## MCP Server API

### Tools

#### `get_alerts(state: str, max_alerts: int = 3) -> str`

Retrieves active weather alerts for a US state.

**Parameters:**
- `state`: Two-letter US state code (e.g., "CA", "NY", "TX")
- `max_alerts`: Maximum number of alerts to return (default: 3)

**Returns:**
Formatted string containing weather alert information including:
- Event type
- Affected area
- Severity level
- Description
- Instructions

**Example:**
```python
alerts = await get_alerts("CA", max_alerts=5)
```

## Token Usage Management

The project includes built-in token usage optimization for the Groq free tier (8000 tokens per minute limit):

- **Automatic History Clearing**: Conversation history is automatically cleared every 3 turns
- **Response Size Limits**: `max_tokens=1024` limits response size
- **Alert Truncation**: Long alert descriptions are truncated to save tokens
- **Configurable Limits**: Adjust `max_steps` and `MAX_TURNS_BEFORE_CLEAR` as needed

## Dependencies

- `langchain>=1.0.2` - LLM framework
- `langchain-core>=1.0.0` - Core LangChain components
- `langchain-groq>=1.0.0` - Groq LLM integration
- `mcp-use>=1.4.0` - MCP client utilities
- `mcp[cli]>=1.18.0` - MCP server framework
- `httpx` - HTTP client for API requests
- `python-dotenv` - Environment variable management

## Architecture

### MCP Server (`server/weather.py`)

- Uses FastMCP for easy tool definition
- Implements `get_alerts` tool that queries the NWS API
- Handles errors gracefully and truncates long responses
- Includes resource definitions for MCP protocol compliance

### Chat Client (`server/client.py`)

- Uses `MCPAgent` from `mcp_use` for agent orchestration
- Integrates with Groq LLM (llama-3.3-70b-versatile)
- Implements streaming for real-time responses
- Captures and logs tool calls and results
- Manages conversation memory with automatic clearing

## Error Handling

The client handles several error scenarios:

- **Token Limit Exceeded**: Provides helpful suggestions and auto-clears history
- **Recursion Limit**: Logs tool results even if recursion limit is reached
- **API Errors**: Gracefully handles NWS API failures
- **Network Issues**: Timeout handling for API requests

## Development

### Running the MCP Server Standalone

To test the MCP server directly:

```bash
uv run server/weather.py
```

### Debugging

The client includes extensive debug logging:
- Tool call logging with input parameters
- Tool result logging with full output
- Event streaming for agent execution
- Error messages with actionable suggestions

## Limitations

- **Free Tier Limits**: Groq free tier has 8000 TPM limit - history auto-clears to manage this
- **State Codes Only**: Currently supports US state codes only (not city names)
- **Alert Limit**: Default limit of 3 alerts to prevent token overflow
- **No Historical Data**: Only retrieves active alerts, not historical weather data

## Future Enhancements

- [ ] Support for city/zip code lookups
- [ ] Historical weather data
- [ ] Weather forecasts (not just alerts)
- [ ] Multi-state query support
- [ ] Customizable alert filtering
- [ ] Webhook support for real-time alerts

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Acknowledgments

- National Weather Service for providing the weather API
- FastMCP for simplifying MCP server development
- LangChain and Groq for LLM integration

