# openai_tool_example.py
import json
import os
import argparse
import requests # Use requests for synchronous HTTP calls to Cabbage API
from openai import OpenAI # Use the official OpenAI library
from dotenv import load_dotenv

# Import the function to call your local Cabbage API server
from client_example import call_search_api

# --- Load Environment Variables ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY environment variable not set.")
    print("Please set it in your environment or in a .env file.")
    exit(1) # Exit if the key is missing

# --- OpenAI API Client ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Tool Definition for OpenAI ---
# Note: OpenAI uses a slightly different format than Mistral
cabbage_search_tool_definition = {
    "type": "function",
    "function": {
        "name": "cabbage_web_search",
        "description": "Performs a web search using the Cabbage engine for a given query and returns a concise summary of the findings. Use this for questions about recent events, specific facts, or topics requiring up-to-date information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The specific question or topic to search the web for.",
                }
            },
            "required": ["query"],
        },
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

    if api_response and api_response.get("summary"):
        result = api_response["summary"]
        print(f"Tool Success: Summary received (Length: {len(result)}).")
        # OpenAI expects tool results as strings
        return json.dumps({"summary": result})
    elif api_response and api_response.get("message"):
        result = f"Search completed, but no summary could be generated. API Message: {api_response['message']}"
        print(f"Tool Warning: {result}")
        return json.dumps({"message": result})
    else:
        error_message = "Error: Failed to get a valid response or summary from the Cabbage Search API."
        print(f"Tool Error: {error_message}")
        return json.dumps({"error": error_message})

# --- Main Interaction Logic ---
def run_openai_interaction(user_request: str, model="gpt-4o"): # Using gpt-4o as default
    """
    Handles the interaction with the OpenAI API using the official library.
    """
    # Define the system prompt
    system_prompt = """You are a helpful assistant. When you use tools to gather information, synthesize the results into a clear, comprehensive, and informative answer for the user. Do not just state that you used a tool; explain what you found in a user-friendly way."""

    # Start the conversation history
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_request}
    ]

    print(f"\n--- Sending Request to OpenAI ---")
    print(f"System Prompt: {system_prompt}")
    print(f"User Request: {user_request}")
    print(f"Model: {model}")
    print(f"Tools Available: {[tool['function']['name'] for tool in tools]}")

    try:
        # --- First API Call ---
        response1 = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto" # Let OpenAI decide when to use the tool
        )

        response1_message = response1.choices[0].message
        messages.append(response1_message) # Add assistant's response to history

        # Check if OpenAI decided to use a tool
        tool_calls = response1_message.tool_calls
        if tool_calls:
            print("\n--- OpenAI Responded with Tool Call(s) ---")
            available_functions = {
                "cabbage_web_search": execute_cabbage_search,
            }

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions.get(function_name)
                if not function_to_call:
                    print(f"Error: Unknown tool requested: {function_name}")
                    tool_result = json.dumps({"error": f"Unknown tool '{function_name}'."})
                else:
                    function_args = json.loads(tool_call.function.arguments)
                    print(f"Tool to Call: {function_name}")
                    print(f"Arguments: {function_args}")
                    tool_result = function_to_call(query=function_args.get("query"))

                # Append the tool's result message
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": tool_result, # Content must be a string
                    }
                )

            print("\n--- Sending Tool Result(s) Back to OpenAI ---")
            # --- Second API Call ---
            response2 = client.chat.completions.create(
                model=model,
                messages=messages
                # No tools needed here, just getting the final response
            )
            final_content = response2.choices[0].message.content
            print("\n--- Final Response from OpenAI (after tool use) ---")
            print(final_content)

        else:
            # OpenAI answered directly without using a tool
            final_content = response1_message.content
            print("\n--- OpenAI Responded Directly ---")
            print(final_content)

    except Exception as e:
        print(f"\n--- An Unexpected Error Occurred ---")
        print(f"Error during OpenAI API interaction: {type(e).__name__} - {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interact with OpenAI API using the Cabbage Search tool via the Cabbage API server.")
    parser.add_argument("query", help="The query/question to ask OpenAI.")
    parser.add_argument("-m", "--model", default="gpt-4o", help="OpenAI model to use (must support tool calling).")
    args = parser.parse_args()

    print("--- Starting OpenAI Interaction ---")
    print("NOTE: Make sure the Cabbage API server (cabbage/api_server.py) is running on http://127.0.0.1:8000")
    run_openai_interaction(args.query, model=args.model)
    print("\n--- Interaction Complete ---")