# client_example.py
import requests
import json
import argparse

# Define the API endpoint URL
API_URL = "http://127.0.0.1:8000/search"

def call_search_api(query: str):
    """
    Calls the Cabbage Search Engine API to get a summary for the given query.

    Args:
        query (str): The search query.

    Returns:
        dict: The JSON response from the API containing the query and summary,
              or None if the API call fails.
    """
    print(f"Sending query to Cabbage Search API: '{query}'")
    try:
        # The API expects the query as a query parameter in a POST request
        # Although POST usually has a body, FastAPI allows query params for POST
        # Alternatively, you could change the API to accept a JSON body
        response = requests.post(API_URL, params={"query": query})
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        result = response.json()
        print("Received response from API.")
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error calling Cabbage Search API: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON response from API. Response text: {response.text}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Example client for the Cabbage Search Engine API.")
    parser.add_argument("query", help="The search query to send to the API.")
    args = parser.parse_args()

    search_result = call_search_api(args.query)

    if search_result:
        print("\n--- API Response ---")
        # Pretty print the JSON response
        print(json.dumps(search_result, indent=2))
        if search_result.get("summary"):
            print("\n--- Summary ---")
            print(search_result["summary"])
        elif "message" in search_result:
            print(f"\nAPI Message: {search_result['message']}")
    else:
        print("\nFailed to get a result from the API.")