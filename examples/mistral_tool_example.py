# mistral_tool_example.py
import json
import os
import argparse
import requests # Use requests for synchronous HTTP calls
from dotenv import load_dotenv

# Import the function to call your local API server
from client_example import call_search_api

# --- Load Environment Variables ---
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    print("ERROR: MISTRAL_API_KEY environment variable not set.")
    print("Please set it in your environment or in a .env file.")
    exit(1) # Exit if the key is missing

# --- Mistral API Configuration ---
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- Tool Definition for Mistral ---
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
    api_response = call_search_api(query) # Function from client_example.py

    if api_response and api_response.get("summary"):
        result = api_response["summary"]
        print(f"Tool Success: Summary received (Length: {len(result)}).")
        return result
    elif api_response and api_response.get("message"):
        result = f"Search completed, but no summary could be generated. API Message: {api_response['message']}"
        print(f"Tool Warning: {result}")
        return result
    else:
        error_message = "Error: Failed to get a valid response or summary from the Cabbage Search API."
        print(f"Tool Error: {error_message}")
        return error_message

# --- Function to Format Mistral Response ---
def format_mistral_response(content):
    """Formats the potentially structured response from Mistral into a readable string."""
    if isinstance(content, list):
        formatted_text = ""
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                formatted_text += item.get("text", "")
            # Optionally handle 'reference' types if needed, e.g., append [ref_id]
            elif isinstance(item, dict) and item.get("type") == "reference":
                 # Simple example: append reference IDs if they exist
                 ref_ids = item.get("reference_ids")
                 if ref_ids:
                     formatted_text += f" [References: {', '.join(map(str, ref_ids))}]"
        return formatted_text.strip() # Remove leading/trailing whitespace
    elif isinstance(content, str):
        return content # Return as is if it's already a string
    else:
        # Fallback for unexpected formats
        return str(content)

# --- Main Interaction Logic ---
def run_mistral_interaction_via_http(user_request: str, model="mistral-large-latest"):
    """
    Handles the interaction with the Mistral API via direct HTTP requests.
    """
    # Define the system prompt
    system_prompt = """You are a helpful assistant. When you use tools to gather information, synthesize the results into a clear, comprehensive, and informative answer for the user. Do not just state that you used a tool; explain what you found in a user-friendly way."""

    # Start the conversation history with the system prompt and the user request
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_request}
    ]

    print(f"\n--- Sending Request to Mistral ---")
    print(f"System Prompt: {system_prompt}")
    print(f"User Request: {user_request}")
    print(f"Model: {model}")
    print(f"Tools Available: {[tool['function']['name'] for tool in tools]}")

    try:
        # --- First API Call ---
        payload1 = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto"
        }
        print(f"Payload (1st call): {json.dumps(payload1, indent=2)}")
        response1 = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload1)
        response1.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        response1_data = response1.json()
        print(f"Response (1st call): {json.dumps(response1_data, indent=2)}")

        assistant_message = response1_data['choices'][0]['message']
        messages.append(assistant_message) # Add assistant's response to history

        # Check if Mistral decided to use a tool
        if assistant_message.get("tool_calls"):
            print("\n--- Mistral Responded with Tool Call ---")
            tool_call = assistant_message["tool_calls"][0] # Assuming one tool call
            function_name = tool_call['function']['name']
            function_args_str = tool_call['function']['arguments']
            function_args = json.loads(function_args_str)
            tool_call_id = tool_call['id']

            print(f"Tool to Call: {function_name}")
            print(f"Arguments: {function_args}")

            # Execute the correct local function
            if function_name == "cabbage_web_search":
                tool_result = execute_cabbage_search(query=function_args.get("query"))
            else:
                print(f"Error: Unknown tool requested: {function_name}")
                tool_result = f"Error: Unknown tool '{function_name}'."

            # Append the tool's result message
            tool_message = {
                "role": "tool",
                "name": function_name,
                "content": tool_result,
                "tool_call_id": tool_call_id
            }
            messages.append(tool_message)

            print("\n--- Sending Tool Result Back to Mistral ---")
            # --- Second API Call ---
            payload2 = {
                "model": model,
                "messages": messages
                # No tools needed here
            }
            print(f"Payload (2nd call): {json.dumps(payload2, indent=2)}")
            response2 = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload2)
            response2.raise_for_status()
            response2_data = response2.json()
            print(f"Raw Response (2nd call): {json.dumps(response2_data, indent=2)}") # Keep raw log

            raw_final_content = response2_data['choices'][0]['message']['content']
            final_output = format_mistral_response(raw_final_content) # Format the response

            print("\n--- Final Formatted Response from Mistral (after tool use) ---")
            print(final_output) # Print the formatted response

        else:
            # Mistral answered directly without using a tool
            raw_final_content = assistant_message['content']
            final_output = format_mistral_response(raw_final_content) # Format the response

            print("\n--- Mistral Responded Directly (Formatted) ---")
            print(final_output) # Print the formatted response

    except requests.exceptions.RequestException as e:
        print(f"\n--- HTTP Request Error ---")
        print(f"Error during Mistral API call: {e}")
        if e.response is not None:
            print(f"Response Status Code: {e.response.status_code}")
            try:
                print(f"Response Body: {e.response.text}")
            except Exception:
                print("Could not read response body.")
    except json.JSONDecodeError as e:
        print(f"\n--- JSON Parsing Error ---")
        print(f"Could not decode JSON response from Mistral API: {e}")
    except Exception as e:
        print(f"\n--- An Unexpected Error Occurred ---")
        print(f"Error during Mistral API interaction: {type(e).__name__} - {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interact with Mistral API via HTTP using the Cabbage Search tool.")
    parser.add_argument("query", help="The query/question to ask Mistral.")
    parser.add_argument("-m", "--model", default="mistral-large-latest", help="Mistral model to use (must support tool calling).")
    args = parser.parse_args()

    print("--- Starting Mistral Interaction via HTTP ---")
    print("NOTE: Make sure the Cabbage API server (api_server.py) is running on http://127.0.0.1:8000")
    run_mistral_interaction_via_http(args.query, model=args.model)
    print("\n--- Interaction Complete ---")