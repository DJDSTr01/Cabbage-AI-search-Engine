# library_usage_example.py
import asyncio
import logging

# Import directly from the cabbage package
# Assumes the 'cabbage' folder is in the same directory or accessible via PYTHONPATH
from cabbage import process_query, load_config, DEFAULT_CONFIG

# Configure basic logging for the example
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def run_cabbage_search(search_term: str):
    """
    Demonstrates calling the Cabbage library directly.
    """
    logging.info(f"--- Starting Cabbage Library Example for query: '{search_term}' ---")

    # Load configuration from cabbage/config.json
    # This step is optional; process_query will use defaults if config is not loaded
    # or if specific parameters are omitted in the call.
    try:
        config = load_config()
        logging.info(f"Loaded config: {config}")
        # Extract config values or use defaults
        num_results = config.get("search_results_count", DEFAULT_CONFIG["search_results_count"])
        summary_sentences = config.get("summary_sentences_count", DEFAULT_CONFIG["summary_sentences_count"])
        mistral_model = config.get("mistral_model", DEFAULT_CONFIG["mistral_model"])
        mistral_tokens = config.get("mistral_max_tokens", DEFAULT_CONFIG["mistral_max_tokens"])
    except Exception as e:
        logging.warning(f"Could not load config, using defaults. Error: {e}")
        num_results = DEFAULT_CONFIG["search_results_count"]
        summary_sentences = DEFAULT_CONFIG["summary_sentences_count"]
        mistral_model = DEFAULT_CONFIG["mistral_model"]
        mistral_tokens = DEFAULT_CONFIG["mistral_max_tokens"]

    logging.info(f"Using parameters: num_results={num_results}, summary_sentences={summary_sentences}, mistral_model='{mistral_model}', mistral_tokens={mistral_tokens}")

    # Ensure you have set the MISTRAL_API_KEY environment variable (e.g., in a .env file)
    # if you want to use the Mistral summarization step.
    # If the key is missing, Cabbage will fall back to the initial LSA summary.

    try:
        # Call the core processing function from the library
        summary = await process_query(
            search_term,
            num_results=num_results,
            summary_sentences=summary_sentences,
            mistral_model_name=mistral_model,
            mistral_max_tokens=mistral_tokens
        )

        if summary:
            print("\n" + "="*20 + " SUMMARY " + "="*20)
            print(summary)
            print("="*50)
        else:
            logging.warning("Failed to generate a summary.")

    except Exception as e:
        logging.error(f"An error occurred during Cabbage processing: {e}", exc_info=True)

    logging.info("--- Cabbage Library Example Complete ---")


if __name__ == "__main__":
    # Example query
    query = "What are the latest advancements in quantum computing?"

    # Run the async function
    asyncio.run(run_cabbage_search(query))