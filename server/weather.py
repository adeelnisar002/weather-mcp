from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
        
def format_alert(feature: dict, max_desc_length: int = 150) -> str:
    """Format an alert feature into a readable string with truncated descriptions."""
    props = feature["properties"]
    
    # Truncate long descriptions to save tokens
    description = props.get('description', 'No description available')
    if len(description) > max_desc_length:
        description = description[:max_desc_length] + "..."
    
    instruction = props.get('instruction', 'No specific instructions provided')
    if len(instruction) > max_desc_length:
        instruction = instruction[:max_desc_length] + "..."
    
    return f"""
        Event: {props.get('event', 'Unknown')}
        Area: {props.get('areaDesc', 'Unknown')}
        Severity: {props.get('severity', 'Unknown')}
        Description: {description}
        Instructions: {instruction}
        """

@mcp.tool()
async def get_alerts(state: str, max_alerts: int = 3) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
        max_alerts: Maximum number of alerts to return (default: 3) to stay within token limits and avoid recursion errors
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    # Limit the number of alerts to prevent token overflow
    features = data["features"][:max_alerts]
    alerts = [format_alert(feature) for feature in features]
    
    result = "\n---\n".join(alerts)
    
    # Add note if there are more alerts
    total_alerts = len(data["features"])
    if total_alerts > max_alerts:
        result += f"\n\nNote: Showing {max_alerts} of {total_alerts} total alerts. Ask for more specific information if needed."
    
    return result


@mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """Echo a message as a resource"""
    return f"Resource echo: {message}"

def main():
    # Initialize and run the server
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()