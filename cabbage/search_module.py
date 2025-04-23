import logging
from duckduckgo_search import DDGS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def search_urls(query, num_results=5):
    """
    Performs a web search using DuckDuckGo and returns the top URLs.

    Args:
        query (str): The search query.
        num_results (int): The maximum number of search result URLs to return.

    Returns:
        list: A list of URLs found, or an empty list if an error occurs or no results.
    """
    logging.debug(f"Performing search for query: '{query}' (max {num_results} results)") # Changed to DEBUG
    urls = []
    try:
        # Use DDGS context manager for text search
        with DDGS() as ddgs:
            # Fetch results using ddgs.text() which returns a generator
            # Convert generator to list to get all results up to max_results
            results = list(ddgs.text(query, max_results=num_results))

        if results:
            urls = [result['href'] for result in results]
            logging.debug(f"Found {len(urls)} URLs: {urls}") # Changed to DEBUG
        else:
            logging.warning(f"No search results found for query: '{query}'")

    except Exception as e:
        logging.error(f"An error occurred during search: {e}")

    return urls

# Removed the __main__ block for library usage