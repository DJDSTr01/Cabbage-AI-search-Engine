import argparse
import logging
import json # To potentially save structured data later
import trafilatura # Import the library
import nltk
import asyncio # Added for async operations
import aiohttp # Added for HTTP requests
# Sumy imports
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from dotenv import load_dotenv # Correct import
# Import functions from our other modules
# Import Hugging Face Transformers
import os # Added for environment variables
# Removed Mistral client import

# Import functions from our other modules
from search_module import search_urls
from scraper import scrape_website # Assuming scraper.py is in the same directory

# Load environment variables from .env file
load_dotenv()

# Logging configuration will be set after parsing args
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # This line should remain commented

# --- NLTK Data Download ---
# Ensure 'punkt' tokenizer data is available for Sumy
try:
    logging.debug("Ensuring NLTK 'punkt' and 'punkt_tab' data are available...")
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=False) # Remove quiet=True to see potential errors
    logging.debug("'punkt' and 'punkt_tab' download check complete.")
except Exception as e:
    # Log error but proceed; summarization might fail later
    logging.error(f"Error during NLTK 'punkt' download check: {e}")


# --- Configuration Loading ---
DEFAULT_CONFIG = {
    "search_results_count": 5,
    "summary_sentences_count": 50,
    "mistral_model": "mistral-small-latest", # Default Mistral model
    "mistral_max_tokens": 150 # Default max tokens for Mistral summary
}

# --- Mistral API Configuration ---
mistral_api_key = os.environ.get("MISTRAL_API_KEY")
mistral_api_url = "https://api.mistral.ai/v1/chat/completions"

if not mistral_api_key:
    logging.warning("MISTRAL_API_KEY environment variable not set. Mistral summarization will be skipped.")


import pathlib # Import pathlib

# Get the directory where main_processor.py resides
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()

def load_config(config_path=None):
    """Loads configuration from a JSON file relative to this script's directory."""
    if config_path is None:
        # Default to config.json in the same directory as this script
        config_path = SCRIPT_DIR / "config.json"
    else:
        # If a path is provided, resolve it (might be absolute or relative to CWD)
        config_path = pathlib.Path(config_path)

    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            # Ensure required keys are present, use defaults if not
            config = DEFAULT_CONFIG.copy()
            config.update(config_data)
            logging.info(f"Loaded configuration from {config_path}")
            return config
    except FileNotFoundError:
        logging.warning(f"Config file '{config_path}' not found. Using default settings.")
        return DEFAULT_CONFIG
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from '{config_path}'. Using default settings.")
        return DEFAULT_CONFIG
    except Exception as e:
        logging.error(f"Error loading config file '{config_path}': {e}. Using default settings.")
        return DEFAULT_CONFIG

# --- Constants ---
LANGUAGE = "english" # Language for summarization
# SENTENCES_COUNT removed, will be loaded from config

# --- Functions ---
def summarize_text(text, sentences_count):
    """Summarizes the given text using Sumy LSA."""
    if not text or not isinstance(text, str) or len(text.strip()) == 0:
        logging.warning("Cannot summarize empty or invalid text.")
        return ""

    logging.debug(f"Summarizing text ({len(text)} chars) to {sentences_count} sentences...") # Changed to DEBUG
    try:
        # Use the standard parser with the string and tokenizer
        parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))
        stemmer = Stemmer(LANGUAGE)
        summarizer = LsaSummarizer(stemmer)
        summarizer.stop_words = get_stop_words(LANGUAGE)

        summary_sentences = summarizer(parser.document, sentences_count)
        summary = " ".join(str(sentence) for sentence in summary_sentences)
        logging.debug(f"Generated first summary ({len(summary)} chars).") # Changed to DEBUG
        return summary
    except Exception as e:
        logging.error(f"Error during summarization: {e}")
        return "" # Return empty string on error

async def process_query(query, num_results, summary_sentences, mistral_model_name, mistral_max_tokens): # Made async, updated config params
    """
    Orchestrates the process: search, scrape, extract, summarize (x2).

    Args:
        query (str): The user's search query.
        num_results (int): The number of search results to process.
        summary_sentences (int): Number of sentences for the first summary.
        mistral_model_name (str): The Mistral model to use.
        mistral_max_tokens (int): Max tokens for the second (Mistral) summary.

    Returns:
        str: A summary of the combined content from the scraped URLs,
             or an empty string if the process fails at any critical step.
    """
    logging.debug(f"Starting processing for query: '{query}'") # Changed to DEBUG

    # 1. Search for URLs
    urls = search_urls(query, num_results=num_results)
    if not urls:
        logging.error("Search returned no URLs. Aborting process.")
        return {}

    # 2. Scrape HTML content for each URL
    scraped_data = {}
    logging.debug(f"Fetching content for {len(urls)} URLs...") # Changed to DEBUG
    for i, url in enumerate(urls):
        logging.debug(f"Fetching URL {i+1}/{len(urls)}: {url}") # Changed to DEBUG
        html_content = scrape_website(url) # Using the function from scraper.py
        scraped_data[url] = html_content
        if html_content:
            logging.debug(f"Successfully scraped: {url} ({len(html_content)} bytes)") # Changed to DEBUG
        else:
            logging.warning(f"Failed to scrape: {url}") # Kept WARNING

    # --- Placeholder for Future Steps ---

    # 3. Extract Main Content using Trafilatura
    extracted_texts = {}
    logging.debug("Extracting main content using Trafilatura...") # Changed to DEBUG
    for url, html_content in scraped_data.items():
        if html_content:
            # Use trafilatura to extract the main text content
            # include_comments=False, include_tables=False can be added for cleaner text
            extracted_text = trafilatura.extract(html_content, include_comments=False, include_tables=False)
            if extracted_text:
                extracted_texts[url] = extracted_text
                logging.debug(f"Successfully extracted content from: {url} ({len(extracted_text)} chars)") # Changed to DEBUG
            else:
                logging.warning(f"Trafilatura could not extract main content from: {url}") # Kept WARNING
                extracted_texts[url] = None # Mark as failed extraction
        else:
            extracted_texts[url] = None # Carry over the scraping failure

    # 3b. Deduplication (Requires Implementation)
    #    - Compare extracted_texts values to remove duplicates or near-duplicates
    #    - Techniques: Check for exact matches, use hashing (e.g., MinHash), or semantic similarity.
    logging.debug("[Placeholder] Next step: Deduplicate extracted content.") # Changed to DEBUG
    processed_content = extracted_texts # For now, pass all extracted texts

    # 4. Combine and Summarize Content
    # Combine all non-empty extracted texts into one large string
    combined_text = "\n\n".join(text for text in processed_content.values() if text and text.strip())

    if not combined_text:
        logging.warning("No valid text content extracted to summarize.")
        final_summary = ""
    else:
        logging.debug("Performing first summarization (LSA)...") # Changed to DEBUG
        first_summary = summarize_text(combined_text, sentences_count=summary_sentences)

        # 5. Second Summarization using Mistral API via aiohttp
        if first_summary and mistral_api_key: # Check if API key is available
            logging.debug(f"Performing second summarization using Mistral API (model: {mistral_model_name})...") # Changed to DEBUG
            try:
                # Construct the prompt (Revised again to ignore unclear parts, stick to text)
                system_prompt = f"""You are an expert summarizer tasked with refining an initial summary. The provided text is the result of a web search for the query "{query}" and has already been summarized once, but might contain incomplete sentences or unclear phrasing.

Your goal is to produce a final, comprehensive, and coherent summary that directly answers the query "{query}", based *only* on the information provided in the initial summary text.

- Ensure **all key information relevant to the query** from the provided text is included. Do not omit relevant details.
- If parts of the initial summary are too incomplete or unclear to be accurately represented, **ignore those specific parts**. Do not add information not present in the provided text.
- Focus on summarizing the clear and complete information relevant to the query, ensuring the final output is well-written and flows logically.
- Focus only on content relevant to "{query}" and ignore irrelevant details or sections.
"""
                user_prompt = f"""Initial Summary Text to Refine:
---
{first_summary}
---

Based on the query "{query}", provide the refined and comprehensive summary:""" # Slightly adjusted user prompt wording

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]

                headers = {
                    "Authorization": f"Bearer {mistral_api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                payload = {
                    "model": mistral_model_name,
                    "messages": messages,
                    "max_tokens": mistral_max_tokens
                }

                # Make the API call using aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(mistral_api_url, headers=headers, json=payload) as response:
                        response.raise_for_status() # Raise exception for bad status codes
                        json_response = await response.json()

                        if json_response.get('choices'):
                            final_summary = json_response['choices'][0]['message']['content'].strip()
                            logging.debug(f"Generated Mistral summary ({len(final_summary)} chars) using model {mistral_model_name} with max_tokens: {mistral_max_tokens}.") # Changed to DEBUG
                        else:
                            logging.warning("Mistral API returned no choices. Falling back to the first summary.") # Kept WARNING
                            final_summary = first_summary

            except aiohttp.ClientResponseError as e:
                 logging.error(f"Mistral API HTTP Error: {e.status} - {e.message}")
                 try:
                     error_body = await e.text()
                     logging.error(f"API Error Body: {error_body}")
                 except Exception:
                     pass # Ignore if reading body fails
                 logging.warning("Falling back to the first summary.")
                 final_summary = first_summary
            except Exception as e:
                logging.error(f"Error during Mistral API call: {type(e).__name__} - {e}")
                logging.warning("Falling back to the first summary.")
                final_summary = first_summary # Fallback to the first summary
        elif not first_summary:
            logging.warning("First summary was empty, skipping Mistral summarization.")
            final_summary = ""
        else: # mistral_api_key is None
             logging.warning("Mistral API key not set. Falling back to the first summary.")
             final_summary = first_summary
 
    logging.debug("Processing finished.") # Changed to DEBUG
    # Add a small delay to allow background tasks (like closing connections) to finish
    await asyncio.sleep(0.1)
    return final_summary # Return the final (potentially double) summary

# Removed the __main__ block for library usage