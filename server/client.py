import asyncio
import os
import sys
import types

# Monkey-patch for langchain.globals compatibility with langchain 1.0+
# In langchain 1.0+, globals was moved to langchain_core.globals
# This must happen BEFORE importing mcp_use
try:
    from langchain_core.globals import set_debug as _set_debug
    import langchain
    # Create a proper module object for langchain.globals
    globals_module = types.ModuleType('globals')
    globals_module.set_debug = _set_debug
    langchain.globals = globals_module
    # Also add it to sys.modules so imports work correctly
    sys.modules['langchain.globals'] = globals_module
except ImportError:
    pass  # If langchain_core is not available, let the original import fail

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableConfig

from mcp_use import MCPAgent, MCPClient

async def run_memory_chat():
    """Run a chat using MCPAgent's built-in conversation memory."""
    # Load environment variables for API keys
    load_dotenv()
    os.environ["GROQ_API_KEY"]=os.getenv("GROQ_API_KEY")
    
    # Set LangGraph recursion limit via environment variable
    # This helps prevent recursion limit errors when processing tool results
    os.environ.setdefault("LANGGRAPH_RECURSION_LIMIT", "10")

    # Config file path - change this to your config file
    config_file = "server/weather.json"

    print("Initializing chat...")

    # Create MCP client and agent with memory enabled
    client = MCPClient.from_config_file(config_file)
    # Configure LLM with token limits to stay within Groq free tier (8000 TPM)
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,  # Limit response size to reduce token usage
        temperature=0.7,
    )

    # Create agent with memory_enabled=True
    # Balanced max_steps: enough for tool calls but not too many to avoid recursion limit
    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=5,  # Increased to 3 to help avoid recursion limit (was 2)
        memory_enabled=False,  # Enable built-in conversation memory
    )

    print("\n===== Interactive MCP Chat =====")
    print("Type 'exit' or 'quit' to end the conversation")
    print("Type 'clear' to clear conversation history (recommended if you hit token limits)")
    print("Note: Groq free tier has 8000 TPM limit - history auto-clears every 3 turns")
    print("==================================\n")

    # Track turns to auto-clear history and prevent token overflow
    turn_count = 0
    MAX_TURNS_BEFORE_CLEAR = 3  # Clear history after 3 turns to manage token usage

    try:
        # Main chat loop
        while True:
            # Get user input
            user_input = input("\nYou: ")

            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                print("Ending conversation...")
                break

            # Check for clear history command
            if user_input.lower() == "clear":
                agent.clear_conversation_history()
                turn_count = 0  # Reset counter
                print("Conversation history cleared.")
                continue

            # Auto-clear history periodically to prevent token overflow
            turn_count += 1
            if turn_count >= MAX_TURNS_BEFORE_CLEAR:
                agent.clear_conversation_history()
                turn_count = 0
                print("(History auto-cleared to manage token usage)")

            # Get response from agent
            print("\nAssistant: ", end="", flush=True)

            try:
                # Use stream_events to capture tool results for logging
                # Note: MCPAgent doesn't expose config parameter, so we can't set recursion_limit directly
                # We'll capture tool results and handle recursion errors gracefully
                
                tool_results = []
                final_response_parts = []
                tool_result_captured = False
                
                print("\n[DEBUG] Starting agent execution with tool result logging...")
                
                try:
                    # Stream events to capture tool calls and results
                    async for event in agent.stream_events(user_input):
                        event_type = event.get("event", "")
                        event_name = event.get("name", "")
                        event_data = event.get("data", {})
                        
                        # Capture tool calls
                        if event_type == "on_tool_start":
                            tool_name = event_name
                            tool_input = event_data.get("input", {})
                            print(f"\n[TOOL CALL] {tool_name}")
                            print(f"[TOOL INPUT] {tool_input}")
                        
                        # Capture tool results - THIS IS THE KEY PART
                        elif event_type == "on_tool_end":
                            tool_name = event_name
                            tool_output = event_data.get("output", "")
                            tool_output_str = str(tool_output)
                            
                            print(f"\n[TOOL RESULT - {tool_name}]")
                            print("=" * 80)
                            if len(tool_output_str) > 3000:
                                print(f"{tool_output_str[:3000]}...")
                                print(f"\n[TRUNCATED - Full length: {len(tool_output_str)} characters]")
                            else:
                                print(tool_output_str)
                            print("=" * 80)
                            
                            tool_results.append({
                                "name": tool_name,
                                "output": tool_output_str
                            })
                            tool_result_captured = True
                        
                        # Capture final response chunks
                        elif event_type == "on_chain_stream":
                            chunk = event_data.get("chunk", {})
                            if isinstance(chunk, dict) and "content" in chunk:
                                content = str(chunk["content"])
                                final_response_parts.append(content)
                                print(content, end="", flush=True)
                        
                        # Capture final response
                        elif event_type == "on_chain_end" and event_name == "Agent":
                            final_output = event_data.get("output", "")
                            if final_output and not final_response_parts:
                                final_response_parts.append(str(final_output))
                    
                    # If we collected response parts, join them
                    if final_response_parts:
                        response = "".join(final_response_parts)
                        if response.strip():
                            print()  # New line after streaming
                        else:
                            # Fallback if no response collected
                            response = await agent.run(user_input)
                            print(response)
                    else:
                        # Fallback to regular run if streaming didn't work
                        print("\n[DEBUG] No response from stream_events, falling back to agent.run()...")
                        response = await agent.run(user_input)
                        print(response)
                        
                except Exception as stream_error:
                    error_msg = str(stream_error)
                    # If we hit recursion limit but captured tool result, provide a helpful response
                    if "recursion_limit" in error_msg.lower() and tool_result_captured and tool_results:
                        print(f"\n[WARNING] Recursion limit reached, but tool result was captured.")
                        print(f"[INFO] Tool '{tool_results[0]['name']}' returned {len(tool_results[0]['output'])} characters")
                        print("\n[FALLBACK] Attempting to get response with regular run()...")
                        try:
                            response = await agent.run(user_input)
                            print(response)
                        except Exception as run_error:
                            # If run() also fails, at least we have the tool result logged
                            print(f"\n[ERROR] Both stream_events and run() failed: {run_error}")
                            print(f"[INFO] Tool result was successfully captured above. The agent may need more processing steps.")
                            raise
                    else:
                        # Re-raise if it's a different error or we didn't capture tool result
                        raise

            except Exception as e:
                error_msg = str(e)
                print(f"\nError: {error_msg}")
                
                # Check if it's a token limit error
                if "413" in error_msg or "rate_limit" in error_msg.lower() or "too large" in error_msg.lower():
                    print("\n⚠️  Token limit exceeded! Try:")
                    print("  1. Type 'clear' to clear conversation history")
                    print("  2. Ask shorter questions")
                    print("  3. Reduce max_steps in the agent configuration")
                    print("  4. Consider upgrading your Groq tier at https://console.groq.com/settings/billing")
                
                # Check if it's a recursion limit error
                elif "recursion_limit" in error_msg.lower() or "recursion limit" in error_msg.lower():
                    print("\n⚠️  Recursion limit reached! The agent may need more steps to process the response.")
                    print("   The recursion_limit has been set to 10. If this persists, the tool result may be too large.")

    finally:
        # Clean up
        if client and client.sessions:
            await client.close_all_sessions()


if __name__ == "__main__":
    asyncio.run(run_memory_chat())