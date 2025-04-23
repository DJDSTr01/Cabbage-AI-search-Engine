<p align="center">
 <img src="github/assets/Cabbage.png" alt="Cabbage Logo">
</p>

# Cabbage: An Open-Source AI Search Engine

Cabbage is an open-source Python project designed to function as an AI-powered search engine. It performs web searches, scrapes content from results, extracts key information, and generates concise summaries. The goal is to provide a flexible and easily integrable search and summarization backend for various applications.

## Features

*   **Open-Source:** Freely available for use and modification.
*   **AI-Powered Summarization:** Uses Sumy (LSA) for initial summaries and can optionally leverage Mistral AI models (via API) for more refined, human-like summaries.
*   **Web Search:** Utilizes DuckDuckGo for retrieving search results.
*   **Content Scraping:** Employs Selenium and `webdriver-manager` for robust web scraping.
*   **Content Extraction:** Uses Trafilatura to isolate the main textual content from web pages.
*   **Configurable:** Allows customization of search depth, summary length, and the Mistral model used via `cabbage/config.json`.
*   **Easy Integration:** Designed to be used as a Python library by placing the `cabbage` folder in your project.
*   **Examples Provided:** Includes several examples in the `examples/` directory, demonstrating direct library usage, API calls, and LLM tool integration (Mistral, OpenAI, Anthropic).

## Setup

This guide explains how to set up and use the Cabbage library and scripts.

1.  **Get the Code:**
    *   **Option A: Clone the repository (Recommended if you have Git):**
        ```bash
        git clone https://github.com/DJDSTr01/Cabbage-AI-search-Engine.git
        cd Cabbage-AI-search-Engine # Or your repository directory name
        ```
    *   **Option B: Download:**
        Download and extract the source code ZIP file to a location on your computer.

2.  **Ensure Python is Installed:**
    You need Python 3.8 or higher. You can check your version with `python --version`.

3.  **Install Dependencies:**
    Navigate to the project's root directory (where the `requirements.txt` file is located) in your terminal or command prompt. It's highly recommended to use a Python virtual environment:
    ```bash
    # Create a virtual environment (optional but recommended)
    python -m venv venv

    # Activate the virtual environment
    # On Linux/macOS:
    source venv/bin/activate
    # On Windows:
    # venv\Scripts\activate

    # Install required libraries
    pip install -r requirements.txt
    ```
    This installs the core libraries needed for Cabbage (like Selenium, NLTK, Trafilatura, etc.).

4.  **Download NLTK Data:**
    The first time the Cabbage library runs, it needs specific data from the NLTK library. You can pre-download it:
    ```python
    # Run this in a Python interpreter or save as a script
    import nltk
    nltk.download('punkt')
    ```
    If you skip this, the library will attempt to download it automatically on first use, which might require internet access and write permissions.

## Configuration

1.  **API Keys / Environment Variables:**
    API keys for optional services (like Mistral for summarization, or OpenAI/Anthropic for examples) are managed using a `.env` file in the project root.
    *   **Create `.env`:** Copy the provided template file `.env.example` to a new file named `.env`.
        ```bash
        # Linux/macOS
        cp .env.example .env
        # Windows
        # copy .env.example .env
        ```
    *   **Edit `.env`:** Open the `.env` file and replace the placeholder values (like `your_mistral_api_key_here`) with your actual API keys.
    *   **Usage:**
        *   The `MISTRAL_API_KEY` is used by the core Cabbage library for optional enhanced summarization. If left blank, this step is skipped.
        *   Other keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) are needed only if you run the corresponding LLM tool examples in the `examples/` directory.

2.  **Configuration File (`cabbage/config.json`):**
    You can fine-tune Cabbage's behavior by editing the `cabbage/config.json` file:
    ```json
    
    {
      "search_results_count": 5,
      "summary_sentences_count": 50,
      "mistral_model": "mistral-large-latest",
      "mistral_max_tokens": 250
    }
    ```
    *   `search_results_count`: How many web search results to process.
    *   `summary_sentences_count`: Target length (in sentences) for the initial summary.
    *   `mistral_model`: Which Mistral model to use if the API key is provided.
    *   `mistral_max_tokens`: Maximum length for the Mistral-generated summary.

    If this file is missing or invalid, Cabbage will use built-in default values.

## Usage

There are two main ways to use Cabbage:

### 1. As a Python Library (Recommended for Integration)

This is the most flexible way to use Cabbage in your own Python projects.

*   **Ensure Importability:** Make sure Python can find the `cabbage` folder. You can either:
    *   Place the `cabbage` folder directly inside your project directory.
    *   Add the directory *containing* the `cabbage` folder to your projects directory
*   **Import and Use:** Import the `process_query` function from the `cabbage` package.

```python
# Example: your_project/my_search_script.py
import asyncio
from cabbage import process_query, load_config, DEFAULT_CONFIG

async def main():
    search_term = "What is the future of electric vehicles?"
    print(f"Searching for: {search_term}")

    # You can optionally load config or pass parameters directly
    config = load_config() # Loads from cabbage/config.json if found
    num_results = config.get("search_results_count", DEFAULT_CONFIG["search_results_count"])
    # ... other config parameters

    # Call the main function
    summary = await process_query(
        search_term,
        num_results=num_results,
        # You can override other config values here if needed
    )

    if summary:
        print("\n--- Summary ---")
        print(summary)
    else:
        print("Could not generate a summary.")

if __name__ == "__main__":
    # Make sure you have installed dependencies from requirements.txt
    # Make sure NLTK data ('punkt') is downloaded
    # Make sure .env file with MISTRAL_API_KEY exists if you want Mistral summary
    asyncio.run(main())
```

See `examples/library_usage_example.py` for a more detailed demonstration.

### 2. Running the Example Scripts

The `examples/` directory contains scripts showing various ways to interact with Cabbage.

*   **Dependencies:** Some examples require extra libraries not listed in the main `requirements.txt`.
    *   To run the API client or LLM tool examples, you'll likely need `requests` and potentially specific LLM libraries (`openai`, `anthropic`). Install them as needed:
        ```bash
        pip install requests openai anthropic
        ```
    *   The LLM examples also require their respective API keys (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) to be set in your `.env` file (see Configuration section above).

*   **Running:** Navigate to the project's root directory in your terminal and run the desired script using `python examples/<script_name.py>`.

    ```bash
    # Example: Run the direct library usage example
    python examples/library_usage_example.py

    # Example: Run the OpenAI tool example (requires API server running & dependencies)
    # 1. Start the API server: python cabbage/api_server.py
    # 2. Run the example: python examples/openai_tool_example.py "latest AI news"
    ```

    Refer to the comments within each example script for specific requirements and usage.

### 3. Using the Example API Server (Optional)

An optional, simple web server (`cabbage/api_server.py`) is provided to expose Cabbage's functionality over HTTP.

1.  **Install API Dependencies:**
    ```bash
    pip install fastapi uvicorn
    ```
2.  **Run the Server:**
    From the project root directory:
    ```bash
    python cabbage/api_server.py
    ```
    The server will start on `http://127.0.0.1:8000`.

3.  **Call the API:**
    You can use tools like `curl` or the provided `examples/client_example.py` script (requires `pip install requests`):
    ```bash
    # Using curl
    curl -X POST "http://127.0.0.1:8000/search?query=your%20search%20query"

    # Using the client example script
    python examples/client_example.py "your search query"
    ```

## Logging

The project uses Python's built-in `logging`. You can adjust logging levels within the scripts if needed for debugging.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
