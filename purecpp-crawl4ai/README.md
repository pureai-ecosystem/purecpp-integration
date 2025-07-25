# Crawl4AI Loader for PureCPP

This module provides a `Crawl4AILoader`, a data loader designed to integrate the `crawl4ai` web crawling library with the `purecpp_extract` data loading framework. It allows you to easily fetch web page content as Markdown and load it into `RAGDocument` objects, ready for use in Retrieval-Augmented Generation (RAG) pipelines.

## ✨ Features

* **Simple Web Content Extraction**: Leverages `crawl4ai` to fetch the content of a single URL.
* **Markdown Conversion**: Automatically converts the fetched HTML content into clean Markdown.
* **RAG-Ready Output**: Wraps the extracted content and metadata into `RAGDocument` objects, the standard format for the PureCPP ecosystem.
* **Asynchronous by Design**: Built with `asyncio` for efficient, non-blocking I/O operations.
* **Configurable**: Accepts a `BrowserConfig` object to customize the crawling behavior (e.g., setting user agents, handling cookies).

## ⚙️ Installation

Before using the loader, ensure you have Python 3.10+ and the necessary libraries installed.

1.  **Clone the repository** (if applicable) or ensure your project is set up.
2.  **Create and activate a virtual environment**:
    ```bash
    uv venv 
    source .venv/bin/activate
    uv sync
    ```

## 🚀 Usage

The loader is straightforward to use. Instantiate `Crawl4AILoader` with a target URL and a `BrowserConfig`, then call its `load` method.

For a complete, runnable script, please refer to the `loader.py` file in the project directory.

**Basic Usage Pattern:**

```python
import asyncio
from purecpp_crawl4ai.loader import Crawl4AILoader, BrowserConfig

async def run_loader():
    # 1. Configure the browser
    config = BrowserConfig()

    # 2. Instantiate the loader with a target URL
    loader = Crawl4AILoader("[https://www.example.com](https://www.example.com)", config)

    # 3. Load the content asynchronously
    documents = await loader.load()

    # 4. Use the resulting documents
    for doc in documents:
        print(f"Loaded content from: {doc.metadata['url']}")
        print(f"Snippet: {doc.page_content[:100]}...")

if __name__ == "__main__":
    asyncio.run(run_loader())
```

## Testing 
The project includes a test suite to ensure the loader functions correctly. The tests use unittest.mock to simulate the behavior of AsyncWebCrawler, allowing for fast and reliable testing without making actual network requests.

Ensure unittest is available (it's part of the Python standard library).

Navigate to the project's root directory in your terminal.

Run the tests using the following command:
```bash
python -m unittest test_loader.py
```
