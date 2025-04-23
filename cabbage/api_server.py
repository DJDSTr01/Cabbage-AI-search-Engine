# api_server.py
import uvicorn
from fastapi import FastAPI, HTTPException, Query
import logging
import asyncio
from main_processor import process_query, load_config, DEFAULT_CONFIG

# Configure logging (can be more sophisticated in production)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="Cabbage Search Engine API",
    description="An API to perform web searches, scrape content, and generate summaries.",
    version="0.1.0"
)

# Load configuration once at startup
config = load_config()
num_results = config.get("search_results_count", DEFAULT_CONFIG["search_results_count"])
summary_sentences = config.get("summary_sentences_count", DEFAULT_CONFIG["summary_sentences_count"])
mistral_model = config.get("mistral_model", DEFAULT_CONFIG["mistral_model"])
mistral_tokens = config.get("mistral_max_tokens", DEFAULT_CONFIG["mistral_max_tokens"])

@app.post("/search", summary="Perform a web search and get a summary")
async def perform_search(
    query: str = Query(..., description="The search query to process.")
):
    """
    Takes a search query, finds relevant web pages, scrapes their content,
    and returns a consolidated summary.
    """
    logging.info(f"Received API request for query: '{query}'")
    try:
        # Ensure the asyncio event loop is running or get the current one
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())

        # Call the existing processing logic
        final_summary = await process_query(
            query,
            num_results,
            summary_sentences,
            mistral_model,
            mistral_tokens
        )

        if final_summary:
            logging.info(f"Successfully processed query: '{query}'")
            return {"query": query, "summary": final_summary}
        else:
            logging.warning(f"Processing query '{query}' resulted in an empty summary.")
            # Return 200 OK but indicate no summary could be generated
            return {"query": query, "summary": None, "message": "Could not generate a summary for this query."}

    except Exception as e:
        logging.error(f"Error processing API request for query '{query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")

if __name__ == "__main__":
    # Run the server using uvicorn
    # Use reload=True for development to automatically reload on code changes
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)