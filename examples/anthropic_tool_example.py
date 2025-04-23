# anthropic_tool_example.py
import json
import os
import argparse
import requests # Use requests for synchronous HTTP calls to Cabbage API
from anthropic import Anthropic # Use the official Anthropic library
from dotenv import load_dotenv

# Import the function to call your local Cabbage API server
from client_example import call_search_api

# --- Load Environment Variables ---
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
    print("Please set it in your environment or in a .env file.")
    exit(1) # Exit if the key is missing

# --- Anthropic API Client ---
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# --- Tool Definition for Anthropic ---
# Anthropic uses a specific format for tool definition
cabbage_search_tool_definition = {
    "name": "cabbage_web_search",
    "description": "Performs a web search using the Cabbage engine for a given query and returns a concise summary of the findings. Use this for questions about recent events, specific facts, or topics requiring up-to-date information.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The specific question or topic to search the web for.",
            }
        },
        "required": ["query"],
    }
}

# Available tools list for the API payload
tools = [cabbage_search_tool_definition]

# --- Function to Execute Local Tool ---
def execute_cabbage_search(query: str):
    """Calls the local Cabbage Search API."""
    print(f"\n--- Executing Tool: cabbage_web_search ---")
    print(f"Query: {query}")
    # Assuming client_example.call_search_api handles the request and returns a dict
    api_response = call_search_api(query)

    # Anthropic expects tool results as a dictionary (which will be JSON serialized)
    if api_response and api_response.get("summary"):
        result = {"summary": api_response["summary"]}
        print(f"Tool Success: Summary received (Length: {len(api_response['summary'])}).")
        return result
    elif api_response and api_response.get("message"):
        result_msg = f"Search completed, but no summary could be generated. API Message: {api_response['message']}"
        result = {"message": result_msg}
        print(f"Tool Warning: {result_msg}")
        return result
    else:
        error_message = "Error: Failed to get a valid response or summary from the Cabbage Search API."
        result = {"error": error_message}
        print(f"Tool Error: {error_message}")
        return result

# --- Main Interaction Logic ---
def run_anthropic_interaction(user_request: str, model="claude-3-opus-20240229"): # Using Opus as default
    """
    Handles the interaction with the Anthropic API using the official library.
    """
    # Define the system prompt (Anthropic uses 'system' parameter)
    system_prompt = """You are a helpful assistant. When you use tools to gather information, synthesize the results into a clear, comprehensive, and informative answer for the user. Do not just state that you used a tool; explain what you found in a user-friendly way. When presenting the result from the cabbage_web_search tool, format it nicely for the user."""

    # Start the conversation history (user role only initially for Anthropic)
    messages = [
        {"role": "user", "content": user_request}
    ]

    print(f"\n--- Sending Request to Anthropic ---")
    print(f"System Prompt: {system_prompt}")
    print(f"User Request: {user_request}")
    print(f"Model: {model}")
    print(f"Tools Available: {[tool['name'] for tool in tools]}")

    try:
        # --- First API Call ---
        response1 = client.messages.create(
            model=model,
            system=system_prompt,
            messages=messages,
            tools=tools,
            # tool_choice={"type": "auto"} # Default is auto
        )

        # Add the user message and assistant's initial response to messages list for context
        messages.append({"role": "assistant", "content": response1.content})

        # Check if Claude decided to use a tool
        tool_use_block = next((block for block in response1.content if block.type == "tool_use"), None)

        if tool_use_block:
            print("\n--- Anthropic Responded with Tool Call ---")
            tool_name = tool_use_block.name
            tool_input = tool_use_block.input
            tool_call_id = tool_use_block.id

            print(f"Tool to Call: {tool_name}")
            print(f"Arguments: {tool_input}")

            # Execute the correct local function
            if tool_name == "cabbage_web_search":
                tool_result_dict = execute_cabbage_search(query=tool_input.get("query"))
            else:
                print(f"Error: Unknown tool requested: {tool_name}")
                tool_result_dict = {"error": f"Unknown tool '{tool_name}'."}

            # Append the tool use result message
            # Role is 'user' for tool results in Anthropic's API
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_call_id,
                        "content": json.dumps(tool_result_dict), # Content should be a JSON string or list of blocks
                        # Can also use "is_error": True if needed
                    }
                ]
            })

            print("\n--- Sending Tool Result Back to Anthropic ---")
            # --- Second API Call ---
            response2 = client.messages.create(
                model=model,
                system=system_prompt,
                messages=messages,
                # No tools needed here, just getting the final response
            )

            # Extract text content from the response blocks
            final_content_blocks = [block.text for block in response2.content if block.type == 'text']
            final_content = "\n".join(final_content_blocks)

            print("\n--- Final Response from Anthropic (after tool use) ---")
            print(final_content)

        else:
            # Claude answered directly without using a tool
            # Extract text content from the response blocks
            final_content_blocks = [block.text for block in response1.content if block.type == 'text']
            final_content = "\n".join(final_content_blocks)
            print("\n--- Anthropic Responded Directly ---")
            print(final_content)

    except Exception as e:
        print(f"\n--- An Unexpected Error Occurred ---")
        print(f"Error during Anthropic API interaction: {type(e).__name__} - {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interact with Anthropic API using the Cabbage Search tool via the Cabbage API server.")
    parser.add_argument("query", help="The query/question to ask Anthropic.")
    parser.add_argument("-m", "--model", default="claude-3-opus-20240229", help="Anthropic model to use (must support tool use).")
    args = parser.parse_args()

    print("--- Starting Anthropic Interaction ---")
    print("NOTE: Make sure the Cabbage API server (cabbage/api_server.py) is running on http://127.0.0.1:8000")
    run_anthropic_interaction(args.query, model=args.model)
    print("\n--- Interaction Complete ---")