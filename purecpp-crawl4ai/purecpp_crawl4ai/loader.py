
"""Crawl4ai PureCPP loader module"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Iterable, Iterator, Optional, Union, List

import logging 

import json
from pathlib import Path

from purecpp_extract import BaseDataLoader 
from purecpp_libs import RAGDocument
from crawl4ai import AsyncWebCrawler, BrowserConfig

import asyncio


class Crawl4AILoader(BaseDataLoader):
    """Crawl4ai loader"""

    def __init__(self, url: str, browser_config: BrowserConfig):
        super().__init__(2)
        self._urls = url
        self._browser_config: BrowserConfig =  browser_config or BrowserConfig()
        self._crawler = AsyncWebCrawler(config=self._browser_config)
        
    async def load(self): 
        await self._crawler.start()
        results = await self._crawler.arun(self._urls)
        metadata = {"url": results.url}
        content = results.markdown

        await self._crawler.close()
        return [RAGDocument(page_content=content, metadata=metadata)]

