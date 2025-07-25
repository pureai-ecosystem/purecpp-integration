import unittest
from unittest.mock import patch, AsyncMock, MagicMock

from purecpp_crawl4ai.loader import Crawl4AILoader, BrowserConfig
from purecpp_libs import RAGDocument

class TestCrawl4AILoader(unittest.IsolatedAsyncioTestCase):
    @patch('purecpp_crawl4ai.loader.AsyncWebCrawler')
    async def test_load_success(self, MockAsyncWebCrawler):
       # --- 1. Arrange ---
        
        # Define the mock data that the crawler will "return"
        test_url = "https://mock-example.com"
        mock_crawl_result = MagicMock()
        mock_crawl_result.url = test_url
        mock_crawl_result.markdown = "# Mock Page\n\nThis is test content."

        # Configure the AsyncWebCrawler mock
        # When AsyncWebCrawler() is called, it returns our mock instance
        mock_crawler_instance = MockAsyncWebCrawler.return_value
        
        # Make the async methods awaitable
        mock_crawler_instance.start = AsyncMock()
        mock_crawler_instance.close = AsyncMock()
        
        # Set the return value for the main crawling method
        mock_crawler_instance.arun = AsyncMock(return_value=mock_crawl_result)

        # Instantiate the loader with a dummy config
        browser_config = BrowserConfig()
        loader = Crawl4AILoader(url=test_url, browser_config=browser_config)

        # --- 2. Act ---
        
        # Run the loader's load method
        documents = await loader.load()

        # --- 3. Assert ---

        # Verify that the crawler was initialized with the correct config
        MockAsyncWebCrawler.assert_called_once_with(config=browser_config)

        # Verify that the crawler's lifecycle methods were called
        mock_crawler_instance.start.assert_awaited_once()
        mock_crawler_instance.arun.assert_awaited_once_with(test_url)
        mock_crawler_instance.close.assert_awaited_once()

        # Verify the structure and content of the output
        self.assertEqual(len(documents), 1)
        self.assertIsInstance(documents[0], RAGDocument)
        
        # Check the content of the returned RAGDocument
        doc = documents[0]
        self.assertEqual(doc.page_content, mock_crawl_result.markdown)
        self.assertEqual(doc.metadata, {"url": mock_crawl_result.url})
        
        print("\n✅ test_load_success passed!")

if __name__ == '__main__':
    unittest.main()
